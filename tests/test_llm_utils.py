import pytest

from tau2.data_model.message import (
    AssistantMessage,
    Message,
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from tau2.environment.tool import Tool, as_tool
from tau2.utils import llm_utils
from tau2.utils.llm_utils import generate, get_response_cost


class _FakeUsage:
    def __init__(self, cost: float | None = None):
        self.cost = cost


class _FakeResponse:
    def __init__(self, model: str, usage: _FakeUsage | None = None):
        self.model = model
        self._usage = usage

    def get(self, key: str):
        if key == "usage":
            return self._usage
        return None


def test_get_response_cost_uses_provider_reported_usage_cost() -> None:
    response = _FakeResponse(
        model="qwen/qwen3-235b-a22b-07-25",
        usage=_FakeUsage(cost=0.00012047607),
    )

    assert get_response_cost(response) == 0.00012047607


def test_get_response_cost_uses_requested_model_for_litellm_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def fake_completion_cost(**kwargs):
        calls.append(kwargs)
        return 0.42

    monkeypatch.setattr(llm_utils, "completion_cost", fake_completion_cost)
    response = _FakeResponse(
        model="qwen/qwen3-235b-a22b-07-25",
        usage=_FakeUsage(cost=None),
    )

    assert (
        get_response_cost(
            response,
            model="openrouter/qwen/qwen3-235b-a22b-2507",
        )
        == 0.42
    )
    assert calls == [
        {
            "completion_response": response,
            "model": "openrouter/qwen/qwen3-235b-a22b-2507",
        }
    ]


@pytest.fixture
def model() -> str:
    return "gpt-4o-mini"


@pytest.fixture
def messages() -> list[Message]:
    messages = [
        SystemMessage(role="system", content="You are a helpful assistant."),
        UserMessage(role="user", content="What is the capital of the moon?"),
    ]
    return messages


@pytest.fixture
def tool() -> Tool:
    def calculate_square(x: int) -> int:
        """Calculate the square of a number.
            Args:
            x (int): The number to calculate the square of.
        Returns:
            int: The square of the number.
        """
        return x * x

    return as_tool(calculate_square)


@pytest.fixture
def tool_call_messages() -> list[Message]:
    messages = [
        SystemMessage(role="system", content="You are a helpful assistant."),
        UserMessage(
            role="user",
            content="What is the square of 5? Just give me the number, no explanation.",
        ),
    ]
    return messages


def test_generate_no_tool_call(model: str, messages: list[Message]):
    response = generate(model, messages)
    assert isinstance(response, AssistantMessage)
    assert response.content is not None


def test_generate_tool_call(model: str, tool_call_messages: list[Message], tool: Tool):
    response = generate(model, tool_call_messages, tools=[tool])
    assert isinstance(response, AssistantMessage)
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "calculate_square"
    assert response.tool_calls[0].arguments == {"x": 5}
    follow_up_messages = [
        response,
        ToolMessage(role="tool", id=response.tool_calls[0].id, content="25"),
    ]
    response = generate(
        model,
        tool_call_messages + follow_up_messages,
        tools=[tool],
    )
    assert isinstance(response, AssistantMessage)
    assert response.tool_calls is None
    assert response.content == "25"
