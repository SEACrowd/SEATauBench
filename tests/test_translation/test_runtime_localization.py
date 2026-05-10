import json
from typing import Literal

from pydantic import BaseModel, Field

from tau2.data_model.message import AssistantMessage, ToolCall, ToolMessage
from tau2.data_model.tasks import (
    Action,
    EvaluationCriteria,
    RewardType,
    Task,
    UserScenario,
)
from tau2.environment.environment import Environment
from tau2.environment.tool import as_tool
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool
from tau2.evaluator.evaluator_env import EnvironmentEvaluator
from translation.runtime_localization import (
    LocalizedToolProxy,
    SchemaRuntimeLocalizer,
    patch_environment_with_schema_localizer,
)

SOURCE_ARTIFACT = {
    "kind": "schema",
    "source_file": "src/tau2/domains/mock/data_model.py",
    "models": {
        "OrderQuery": {
            "fields": {
                "status": {
                    "annotation": "TaskStatus",
                    "description": "Status of the task",
                    "value_set": "TaskStatus",
                }
            }
        }
    },
    "value_sets": {
        "TaskStatus": {
            "kind": "literal",
            "values": [
                {"canonical": "pending", "localized": "pending"},
                {"canonical": "completed", "localized": "completed"},
            ],
        }
    },
}

LOCALIZED_ARTIFACT = {
    "kind": "schema",
    "source_file": "src/tau2/domains/mock/data_model.py",
    "models": {
        "OrderQuery": {
            "fields": {
                "status": {
                    "annotation": "TaskStatus",
                    "description": "Status tugas",
                    "value_set": "TaskStatus",
                }
            }
        }
    },
    "value_sets": {
        "TaskStatus": {
            "kind": "literal",
            "values": [
                {
                    "canonical": "pending",
                    "localized": "menunggu",
                    "aliases": ["tertunda"],
                },
                {"canonical": "completed", "localized": "selesai"},
            ],
        }
    },
}


def _build_localizer() -> SchemaRuntimeLocalizer:
    return SchemaRuntimeLocalizer.from_artifact_pairs(
        [SOURCE_ARTIFACT],
        [LOCALIZED_ARTIFACT],
    )


class OrderQuery(BaseModel):
    status: Literal["pending", "completed"] = Field(description="Status of the task")


class DemoDB(BaseModel):
    status: str | None = None


def lookup_order(query: OrderQuery) -> str:
    """
    Look up an order.

    Args:
        query: The query to run.
    """
    return query.status


class DemoTools(ToolKitBase):
    def __init__(self) -> None:
        super().__init__(db=DemoDB())
        self.last_status = None

    @is_tool(ToolType.WRITE)
    def set_status(self, status: Literal["pending", "completed"]) -> dict:
        """
        Set task status.

        Args:
            status: Status of the task.
        """
        self.last_status = status
        self.db.status = status
        return {"status": status}


def test_localize_tool_schema_rewrites_schema_literals_and_descriptions() -> None:
    tool = LocalizedToolProxy(as_tool(lookup_order), _build_localizer())

    schema = tool.openai_schema["function"]["parameters"]
    order_query = schema["$defs"]["OrderQuery"]

    assert order_query["properties"]["status"]["description"] == "Status tugas"
    assert order_query["properties"]["status"]["enum"] == ["menunggu", "selesai"]


def test_normalize_tool_arguments_maps_localized_literals_back_to_canonical() -> None:
    tool = as_tool(lookup_order)
    localizer = _build_localizer()

    normalized = localizer.normalize_tool_arguments(
        {"query": {"status": "tertunda"}},
        tool.params.model_json_schema(),
    )

    assert normalized == {"query": {"status": "pending"}}


def test_environment_normalizes_localized_inputs_and_localizes_outputs() -> None:
    localizer = _build_localizer()
    toolkit = DemoTools()
    env = Environment(domain_name="mock", policy="POLICY", tools=toolkit)
    patch_environment_with_schema_localizer(
        env,
        localizer,
        localize_tools=True,
        localize_outputs=True,
    )

    response = env.get_response(
        ToolCall(
            id="1",
            name="set_status",
            arguments={"status": "tertunda"},
            requestor="assistant",
        )
    )

    assert toolkit.last_status == "pending"
    assert json.loads(response.content) == {"status": "menunggu"}
    localized_tool = env.get_tools()[0]
    assert localized_tool.openai_schema["function"]["parameters"]["properties"][
        "status"
    ]["enum"] == ["menunggu", "selesai"]


def test_replay_compare_accepts_historical_literal_aliases() -> None:
    localizer = _build_localizer()
    toolkit = DemoTools()
    env = Environment(domain_name="mock", policy="POLICY", tools=toolkit)
    patch_environment_with_schema_localizer(
        env,
        localizer,
        localize_tools=True,
        localize_outputs=True,
    )

    history = [
        AssistantMessage.text(
            "",
            tool_calls=[
                ToolCall(
                    id="1",
                    name="set_status",
                    arguments={"status": "tertunda"},
                    requestor="assistant",
                )
            ],
        ),
        ToolMessage(
            id="1",
            role="tool",
            requestor="assistant",
            content='{"status": "tertunda"}',
            error=False,
        ),
    ]

    env.set_state(
        initialization_data=None,
        initialization_actions=None,
        message_history=history,
    )

    assert toolkit.last_status == "pending"


def test_environment_evaluator_configures_replay_env_for_localized_outputs() -> None:
    localizer = _build_localizer()
    task = Task(
        id="task-1",
        user_scenario=UserScenario(instructions="test"),
        evaluation_criteria=EvaluationCriteria(
            actions=[
                Action(
                    action_id="set_status_1",
                    name="set_status",
                    arguments={"status": "pending"},
                    requestor="assistant",
                )
            ],
            reward_basis=[RewardType.DB],
        ),
    )
    history = [
        AssistantMessage.text(
            "",
            tool_calls=[
                ToolCall(
                    id="1",
                    name="set_status",
                    arguments={"status": "tertunda"},
                    requestor="assistant",
                )
            ],
        ),
        ToolMessage(
            id="1",
            role="tool",
            requestor="assistant",
            content='{"status": "tertunda"}',
            error=False,
        ),
    ]

    def build_env(**kwargs) -> Environment:
        return Environment(
            domain_name="mock",
            policy="POLICY",
            tools=DemoTools(),
            **kwargs,
        )

    reward_info = EnvironmentEvaluator.calculate_reward(
        environment_constructor=build_env,
        task=task,
        full_trajectory=history,
        environment_configurer=lambda env: patch_environment_with_schema_localizer(
            env,
            localizer,
            localize_tools=True,
            localize_outputs=True,
        ),
    )

    assert reward_info.reward == 1.0
