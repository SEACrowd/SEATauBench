"""Tests for the translation pipeline.

Unit tests run without external dependencies. Integration tests (marked
``integration``) require domain source files present in the repo. API tests
(marked ``translation_api``) require an API-key environment variable.

Run subsets::

    pytest tests/test_translation_pipeline.py                         # all non-API
    pytest tests/test_translation_pipeline.py -m "not translation_api"
    pytest tests/test_translation_pipeline.py -m translation_api      # needs Vertex ADC
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tau2.data_model.simulation import TextRunConfig
from translation import language as language_utils
from translation import paths as path_utils
from translation.config import (
    FIXED_PROTECTED_TERMS,
    get_domain_contextual_protected_terms,
)
from translation.extractors import (
    _extract_db_json,
    _extract_python,
    apply_toml_updates,
    build_schema_artifact,
    discover_domain_files,
    extract_files,
)
from translation.language import translated_asset_path
from translation.loader import (
    load_docstrings_json,
    localized_toolkit,
    patch_toolkit_docstrings,
    restore_toolkit_docstrings,
)
from translation.models import (
    DomainFile,
    PipelineConfig,
    Segment,
    SourceSpan,
    TranslationRequest,
)
from translation.paths import (
    PROJECT_ROOT,
    resolve_project_path,
    to_project_relative_path,
)
from translation.pipeline import (
    _build_translation_map,
    _extract_literal_map_from_schema_artifact,
    _reconstruct_tool_docstring,
    _validate_vertex_environment,
    _write_outputs,
    run_pipeline,
)
from translation.protect import (
    mask_protected_tokens,
    mask_segment_protected_tokens,
    unmask_protected_tokens,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DOMAINS_ROOT = _REPO_ROOT / "src" / "tau2" / "domains"
_LANGUAGES_JSON = _REPO_ROOT / "config" / "languages.json"

_RETAIL_TOOLS_PY = _SRC_DOMAINS_ROOT / "retail" / "tools.py"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fake_toolkit(docstrings: dict[str, str]) -> type:
    """Return a throwaway class with callable attributes for each docstring key."""

    class MockMethod:
        __doc__ = "original"

        def __call__(self) -> None: ...

    cls = type("FakeToolKit", (), {})
    for name in docstrings:
        setattr(cls, name, MockMethod())
    return cls


# ---------------------------------------------------------------------------
# Extraction (discovery / filtering)
# ---------------------------------------------------------------------------


def test_discover_domain_files_filters_components_and_skips_voice_split(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data" / "tau2" / "domains"
    src_root = tmp_path / "src" / "tau2" / "domains"
    domain = "retail"
    data_dir = data_root / domain
    src_dir = src_root / domain
    data_dir.mkdir(parents=True)
    src_dir.mkdir(parents=True)

    for filename in (
        "tasks.json",
        "tasks_full.json",
        "tasks_small.json",
        "tasks_voice.json",
        "split_tasks.json",
        "db.toml",
        "policy.md",
    ):
        (data_dir / filename).write_text("[]\n", encoding="utf-8")
    (src_dir / "tools.py").write_text('def x():\n    """doc"""\n', encoding="utf-8")

    task_files = discover_domain_files(
        domain=domain,
        data_domains_root=data_root,
        src_domains_root=src_root,
        components=("tasks",),
    )
    assert {file.path.name for file in task_files} == {
        "tasks.json",
        "tasks_full.json",
        "tasks_small.json",
    }


def test_validate_vertex_environment_rejects_noncanonical_model() -> None:
    with pytest.raises(RuntimeError, match="Translation must use the Vertex AI route"):
        _validate_vertex_environment("openai/gpt-5.4-mini")


def test_discover_domain_files_skips_telecom_non_primary_task_files(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data" / "tau2" / "domains"
    src_root = tmp_path / "src" / "tau2" / "domains"
    domain = "telecom"
    data_dir = data_root / domain
    src_dir = src_root / domain
    data_dir.mkdir(parents=True)
    src_dir.mkdir(parents=True)

    for filename in (
        "tasks.json",
        "tasks_full.json",
        "tasks_small.json",
        "tasks_voice.json",
        "split_tasks.json",
    ):
        (data_dir / filename).write_text("[]\n", encoding="utf-8")

    task_files = discover_domain_files(
        domain=domain,
        data_domains_root=data_root,
        src_domains_root=src_root,
        components=("tasks",),
    )
    assert {file.path.name for file in task_files} == {"tasks.json"}


def test_discover_domain_files_includes_all_domain_markdown_files(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data" / "tau2" / "domains"
    src_root = tmp_path / "src" / "tau2" / "domains"
    domain = "telecom"
    data_dir = data_root / domain
    src_dir = src_root / domain
    data_dir.mkdir(parents=True)
    src_dir.mkdir(parents=True)

    for filename in (
        "main_policy.md",
        "main_policy_solo.md",
        "tech_support_manual.md",
        "tech_support_workflow.md",
        "tech_support_workflow_solo.md",
        "faq.md",
    ):
        (data_dir / filename).write_text("# Policy\n", encoding="utf-8")

    policy_files = discover_domain_files(
        domain=domain,
        data_domains_root=data_root,
        src_domains_root=src_root,
        components=("policy",),
    )
    assert {file.path.name for file in policy_files} == {
        "main_policy.md",
        "main_policy_solo.md",
        "tech_support_manual.md",
        "tech_support_workflow.md",
        "tech_support_workflow_solo.md",
        "faq.md",
    }


def test_discover_domain_files_includes_schema_python_files(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data" / "tau2" / "domains"
    src_root = tmp_path / "src" / "tau2" / "domains"
    domain = "retail"
    (data_root / domain).mkdir(parents=True)
    src_dir = src_root / domain
    src_dir.mkdir(parents=True)
    for filename in ("data_model.py", "user_data_model.py"):
        (src_dir / filename).write_text(
            "from pydantic import BaseModel\n", encoding="utf-8"
        )

    schema_files = discover_domain_files(
        domain=domain,
        data_domains_root=data_root,
        src_domains_root=src_root,
        components=("schema",),
    )

    assert {file.path.name for file in schema_files} == {
        "data_model.py",
        "user_data_model.py",
    }


def test_extract_python_returns_named_segments(tmp_path: Path) -> None:
    """_extract_python returns structured docstring segments keyed by part."""
    tools_file = tmp_path / "tools.py"
    tools_file.write_text(
        "def cancel_order(order_id: str):\n"
        '    """Cancel a pending order.\n\n'
        "    Args:\n"
        "        order_id: The order id.\n\n"
        "    Returns:\n"
        "        str: The cancellation status.\n"
        '    """\n'
        "    ...\n"
        'def _private():\n    """Private helper."""\n    ...\n',
        encoding="utf-8",
    )
    df = DomainFile(
        domain="test", path=tools_file, relative_path=tools_file, kind="python"
    )
    result = _extract_python(df)

    names = {s.name for s in result.segments if s.name}
    assert "cancel_order" in names
    assert "_private" in names  # extracted but filtered by caller
    public = [s for s in result.segments if s.name == "cancel_order"]
    assert any(s.python_doc_key == "short" for s in public)
    assert any(s.python_doc_key == "param:order_id" for s in public)
    assert any(s.python_doc_key == "returns" for s in public)


def test_extract_files_limits_tool_python_to_decorated_methods(tmp_path: Path) -> None:
    tools_file = tmp_path / "tools.py"
    tools_file.write_text(
        "from tau2.environment.toolkit import ToolType, is_discoverable_tool, is_tool\n"
        "\n"
        "class DemoTools:\n"
        '    """Demo tools."""\n'
        "\n"
        "    @is_tool(ToolType.READ)\n"
        "    def ping(self):\n"
        '        """Ping the service."""\n'
        "        ...\n"
        "\n"
        "    def helper(self):\n"
        '        """Internal helper."""\n'
        "        ...\n"
        "\n"
        "    @is_discoverable_tool(ToolType.WRITE)\n"
        "    def unlock(self):\n"
        '        """Unlock a hidden tool."""\n'
        "        ...\n"
        "\n"
        "    def assert_state(self):\n"
        '        """Assertion helper."""\n'
        "        ...\n",
        encoding="utf-8",
    )
    df = DomainFile(
        domain="test", path=tools_file, relative_path=tools_file, kind="python"
    )

    result = extract_files([df])

    extracted_names = {segment.name for segment in result.segments}
    assert extracted_names == {"ping", "unlock"}


def test_get_domain_contextual_protected_terms_includes_airline_runtime_literals() -> (
    None
):
    airline_terms = get_domain_contextual_protected_terms("airline")

    assert "available" in airline_terms["status"]
    assert "on time" in airline_terms["status"]
    assert "flying" in airline_terms["status"]
    assert "landed" in airline_terms["status"]
    assert "delayed" in airline_terms["status"]
    assert "round_trip" in airline_terms["flight_type"]
    assert "one_way" in airline_terms["flight_type"]
    assert "basic_economy" in airline_terms["cabin"]
    assert "credit_card" in airline_terms["payment_source"]


def test_build_schema_artifact_extracts_descriptions_and_value_sets(
    tmp_path: Path,
) -> None:
    schema_file = tmp_path / "data_model.py"
    schema_file.write_text(
        "from enum import Enum\n"
        "from typing import Literal, Optional\n"
        "from pydantic import BaseModel, Field\n\n"
        'OrderStatus = Literal["pending", "cancelled"]\n\n'
        "class SimStatus(str, Enum):\n"
        '    ACTIVE = "active"\n'
        '    MISSING = "missing"\n\n'
        "class Order(BaseModel):\n"
        '    """Represents an order."""\n'
        "    status: OrderStatus = Field(description=\"Status of the order. Should be 'pending' or 'cancelled'.\")\n"
        '    sim_status: Optional[Literal["active"]] = Field(description="SIM status.")\n',
        encoding="utf-8",
    )
    df = DomainFile(
        domain="retail",
        path=schema_file,
        relative_path=schema_file,
        kind="python",
    )

    artifact, result = build_schema_artifact(df)

    assert artifact["models"]["Order"]["description"] == "Represents an order."
    assert artifact["models"]["Order"]["fields"]["status"]["value_set"] == "OrderStatus"
    assert artifact["models"]["Order"]["fields"]["sim_status"]["value_set"] == (
        "Order.sim_status"
    )
    assert artifact["value_sets"]["OrderStatus"]["values"][0]["canonical"] == "pending"
    assert artifact["value_sets"]["SimStatus"]["values"][0]["canonical"] == "active"
    assert "pending" in result.protected_terms
    assert "cancelled" in result.protected_terms
    assert any(
        segment.address == ("value_sets", "OrderStatus", "values", "0", "localized")
        and segment.translate_runtime_labels
        for segment in result.segments
    )
    assert any(
        segment.address == ("models", "Order", "fields", "status", "description")
        and not segment.translate_runtime_labels
        for segment in result.segments
    )


def test_extract_literal_map_from_schema_artifact_adds_human_readable_aliases() -> None:
    artifact = {
        "value_sets": {
            "CabinClass": {
                "values": [
                    {"canonical": "basic_economy", "localized": "phổ thông cơ bản"},
                    {"canonical": "round_trip", "localized": "khứ hồi"},
                ]
            },
            "PaymentSource": {
                "values": [
                    {"canonical": "credit_card", "localized": "thẻ tín dụng"},
                ]
            },
        }
    }

    literal_map = _extract_literal_map_from_schema_artifact(artifact)

    assert literal_map["basic_economy"] == "phổ thông cơ bản"
    assert literal_map["basic economy"] == "phổ thông cơ bản"
    assert literal_map["Basic Economy"] == "phổ thông cơ bản"
    assert literal_map["round trip"] == "khứ hồi"
    assert literal_map["credit card"] == "thẻ tín dụng"


def test_build_translation_map_deduplicates_only_telecom_tasks() -> None:
    class FakeTranslator:
        def __init__(self) -> None:
            self.request_ids: list[str] = []

        def translate_batch(
            self,
            requests: list,
            source_language: str,
            target_language: str,
            protected_terms: set[str] | None = None,
            translate_runtime_labels: bool = False,
        ) -> dict[str, str]:
            self.request_ids.extend(req.segment_id for req in requests)
            return {req.segment_id: f"VI::{req.text}" for req in requests}

    telecom_path = Path("data/tau2/domains/telecom/tasks.json")
    retail_path = Path("data/tau2/domains/retail/tasks.json")
    segments = [
        Segment(
            segment_id="telecom_1",
            domain="telecom",
            file_path=telecom_path,
            relative_path=telecom_path,
            kind="json",
            address=("0", "description", "purpose"),
            text="Repeated text",
        ),
        Segment(
            segment_id="telecom_2",
            domain="telecom",
            file_path=telecom_path,
            relative_path=telecom_path,
            kind="json",
            address=("1", "description", "purpose"),
            text="Repeated text",
        ),
        Segment(
            segment_id="telecom_3",
            domain="telecom",
            file_path=telecom_path,
            relative_path=telecom_path,
            kind="json",
            address=("2", "ticket"),
            text="Repeated text",
        ),
        Segment(
            segment_id="retail_1",
            domain="retail",
            file_path=retail_path,
            relative_path=retail_path,
            kind="json",
            address=("0", "description", "purpose"),
            text="Repeated text",
        ),
    ]

    translator = FakeTranslator()
    translated = _build_translation_map(
        segments=segments,
        protected_terms=set(),
        source_language="English",
        target_language="Vietnamese",
        translator=translator,
        batch_size=16,
    )

    assert set(translated) == {"telecom_1", "telecom_2", "telecom_3", "retail_1"}
    # telecom_1 and telecom_2 share address pattern+text, so only three requests total.
    assert len(translator.request_ids) == 3


def test_build_translation_map_splits_literal_label_segments_from_protected_prose() -> (
    None
):
    class FakeTranslator:
        def __init__(self) -> None:
            self.calls: list[tuple[bool, set[str], list[str]]] = []

        def translate_batch(
            self,
            requests: list,
            source_language: str,
            target_language: str,
            protected_terms: set[str] | None = None,
            translate_runtime_labels: bool = False,
        ) -> dict[str, str]:
            self.calls.append(
                (
                    translate_runtime_labels,
                    protected_terms or set(),
                    [req.segment_id for req in requests],
                )
            )
            if translate_runtime_labels:
                return {req.segment_id: "dang cho" for req in requests}
            return {req.segment_id: f"VI::{req.text}" for req in requests}

    path = Path("src/tau2/domains/retail/data_model.py")
    segments = [
        Segment(
            segment_id="desc",
            domain="retail",
            file_path=path,
            relative_path=path,
            kind="python",
            address=("models", "Order", "fields", "status", "description"),
            text="Status should be 'pending'.",
        ),
        Segment(
            segment_id="literal",
            domain="retail",
            file_path=path,
            relative_path=path,
            kind="python",
            address=("value_sets", "OrderStatus", "values", "0", "localized"),
            text="pending",
            translate_runtime_labels=True,
        ),
    ]

    translator = FakeTranslator()
    translated = _build_translation_map(
        segments=segments,
        protected_terms={"pending"},
        source_language="English",
        target_language="Vietnamese",
        translator=translator,
        batch_size=16,
    )

    assert translated["desc"] == "VI::Status should be 'pending'."
    assert translated["literal"] == "dang cho"
    assert len(translator.calls) == 2
    assert translator.calls[0][0] is False
    assert translator.calls[0][1] == {"pending"}
    assert translator.calls[1][0] is True
    assert translator.calls[1][1] == set()


def test_build_translation_map_localizes_tool_literals_from_schema_map() -> None:
    class FakeTranslator:
        def __init__(self) -> None:
            self.calls: list[TranslationRequest] = []

        def translate_batch(
            self,
            requests: list[TranslationRequest],
            source_language: str,
            target_language: str,
            protected_terms: set[str] | None = None,
            translate_runtime_labels: bool = False,
        ) -> dict[str, str]:
            self.calls.extend(requests)
            return {req.segment_id: f"VI::{req.text}" for req in requests}

    path = Path("src/tau2/domains/retail/tools.py")
    segment = Segment(
        segment_id="tool_desc",
        domain="retail",
        file_path=path,
        relative_path=path,
        kind="python",
        address=SourceSpan(0, 10),
        text="Cancel a pending order. The status becomes cancelled.",
        name="cancel_order",
        python_doc_key="short",
    )

    translator = FakeTranslator()
    translated = _build_translation_map(
        segments=[segment],
        protected_terms={"pending", "cancelled"},
        source_language="English",
        target_language="Vietnamese",
        translator=translator,
        batch_size=16,
        domain_literal_maps={
            "retail": {
                "pending": "đang chờ xử lý",
                "cancelled": "đã hủy",
            }
        },
    )

    assert translator.calls[0].literal_map == {
        "pending": "đang chờ xử lý",
        "cancelled": "đã hủy",
    }
    assert (
        translator.calls[0].text
        == "Cancel a __PH_0__ order. The status becomes __PH_1__."
    )
    assert translated["tool_desc"] == (
        "VI::Cancel a đang chờ xử lý order. The status becomes đã hủy."
    )


def test_build_translation_map_preserves_tool_doc_keywords() -> None:
    class FakeTranslator:
        def __init__(self) -> None:
            self.calls: list[TranslationRequest] = []

        def translate_batch(
            self,
            requests: list[TranslationRequest],
            source_language: str,
            target_language: str,
            protected_terms: set[str] | None = None,
            translate_runtime_labels: bool = False,
        ) -> dict[str, str]:
            self.calls.extend(requests)
            return {req.segment_id: f"VI::{req.text}" for req in requests}

    path = Path("src/tau2/domains/telecom/tools.py")
    segment = Segment(
        segment_id="tool_long_desc",
        domain="telecom",
        file_path=path,
        relative_path=path,
        kind="python",
        address=SourceSpan(0, 10),
        text=(
            "Checks: The line must be active.\n"
            "Logic: Update the line status.\n"
            "Warning: Verify the bill status first."
        ),
        name="suspend_line",
        python_doc_key="long",
    )

    translator = FakeTranslator()
    translated = _build_translation_map(
        segments=[segment],
        protected_terms=set(),
        source_language="English",
        target_language="Vietnamese",
        translator=translator,
        batch_size=16,
    )

    assert translator.calls[0].text == (
        "__PH_0__: The line must be active.\n"
        "__PH_1__: Update the line status.\n"
        "__PH_2__: Verify the bill status first."
    )
    assert translated["tool_long_desc"] == (
        "VI::Checks: The line must be active.\n"
        "Logic: Update the line status.\n"
        "Warning: Verify the bill status first."
    )


def test_build_translation_map_localizes_db_prose_literals_from_schema_map() -> None:
    class FakeTranslator:
        def __init__(self) -> None:
            self.calls: list[TranslationRequest] = []

        def translate_batch(
            self,
            requests: list[TranslationRequest],
            source_language: str,
            target_language: str,
            protected_terms: set[str] | None = None,
            translate_runtime_labels: bool = False,
        ) -> dict[str, str]:
            self.calls.extend(requests)
            return {req.segment_id: f"VI::{req.text}" for req in requests}

    path = Path("data/tau2/domains/retail/db.json")
    segment = Segment(
        segment_id="db_note",
        domain="retail",
        file_path=path,
        relative_path=path,
        kind="json",
        address=("orders", "1001", "note"),
        text="Tell the customer the order is pending until it becomes cancelled.",
    )

    translator = FakeTranslator()
    translated = _build_translation_map(
        segments=[segment],
        protected_terms={"pending", "cancelled"},
        source_language="English",
        target_language="Vietnamese",
        translator=translator,
        batch_size=16,
        domain_literal_maps={
            "retail": {
                "pending": "đang chờ xử lý",
                "cancelled": "đã hủy",
            }
        },
    )

    assert translator.calls[0].literal_map == {
        "pending": "đang chờ xử lý",
        "cancelled": "đã hủy",
    }
    assert translated["db_note"] == (
        "VI::Tell the customer the order is đang chờ xử lý until it becomes đã hủy."
    )


def test_build_translation_map_retries_single_request_when_placeholder_is_dropped() -> (
    None
):
    class FakeTranslator:
        def __init__(self) -> None:
            self.call_sizes: list[int] = []

        def translate_batch(
            self,
            requests: list[TranslationRequest],
            source_language: str,
            target_language: str,
            protected_terms: set[str] | None = None,
            translate_runtime_labels: bool = False,
        ) -> dict[str, str]:
            self.call_sizes.append(len(requests))
            if len(requests) > 1:
                return {
                    requests[0].segment_id: "VI::Use __PH_0__ or __PH_1__.",
                    requests[1].segment_id: "VI::Use __PH_0__ only.",
                }
            return {requests[0].segment_id: "VI::Use __PH_0__ or __PH_1__."}

    path = Path("src/tau2/domains/airline/tools.py")
    segments = [
        Segment(
            segment_id="seg_1",
            domain="airline",
            file_path=path,
            relative_path=path,
            kind="python",
            address=SourceSpan(0, 10),
            text="Use gift card or credit card.",
            name="book",
            python_doc_key="short",
        ),
        Segment(
            segment_id="seg_2",
            domain="airline",
            file_path=path,
            relative_path=path,
            kind="python",
            address=SourceSpan(10, 20),
            text="Use gift card or credit card.",
            name="change",
            python_doc_key="short",
        ),
    ]

    translator = FakeTranslator()
    translated = _build_translation_map(
        segments=segments,
        protected_terms=set(),
        source_language="English",
        target_language="Vietnamese",
        translator=translator,
        batch_size=16,
        domain_literal_maps={
            "airline": {
                "gift card": "thẻ quà tặng",
                "credit card": "thẻ tín dụng",
            }
        },
    )

    assert translated["seg_1"] == "VI::Use thẻ quà tặng or thẻ tín dụng."
    assert translated["seg_2"] == "VI::Use thẻ quà tặng or thẻ tín dụng."
    assert translator.call_sizes == [2, 1]


def test_build_translation_map_falls_back_to_localized_source_text_after_repeat_placeholder_loss() -> (
    None
):
    class FakeTranslator:
        def __init__(self) -> None:
            self.request_texts: list[str] = []

        def translate_batch(
            self,
            requests: list[TranslationRequest],
            source_language: str,
            target_language: str,
            protected_terms: set[str] | None = None,
            translate_runtime_labels: bool = False,
        ) -> dict[str, str]:
            self.request_texts.extend(request.text for request in requests)
            request = requests[0]
            if "__PH_" in request.text:
                return {request.segment_id: "ZH::使用 __PH_0__ 方法 ID。"}
            return {request.segment_id: "ZH::使用礼品卡或信用卡方法 ID。"}

    path = Path("src/tau2/domains/airline/tools.py")
    segment = Segment(
        segment_id="seg_1",
        domain="airline",
        file_path=path,
        relative_path=path,
        kind="python",
        address=SourceSpan(0, 10),
        text="Use gift card or credit card method ID.",
        name="book",
        python_doc_key="short",
    )

    translator = FakeTranslator()
    translated = _build_translation_map(
        segments=[segment],
        protected_terms=set(),
        source_language="English",
        target_language="Chinese (Simplified)",
        translator=translator,
        batch_size=16,
        domain_literal_maps={
            "airline": {
                "gift card": "礼品卡",
                "credit card": "信用卡",
            }
        },
    )

    assert translated["seg_1"] == "ZH::使用礼品卡或信用卡方法 ID。"
    assert translator.request_texts == [
        "Use __PH_0__ or __PH_1__ method ID.",
        "Use __PH_0__ or __PH_1__ method ID.",
        "Use 礼品卡 or 信用卡 method ID.",
    ]


@pytest.mark.skipif(not _RETAIL_TOOLS_PY.exists(), reason="retail tools.py not found")
def test_extract_retail_public_docstrings() -> None:
    """At least 3 public retail tool docstrings are extracted."""
    df = DomainFile(
        domain="retail",
        path=_RETAIL_TOOLS_PY,
        relative_path=_RETAIL_TOOLS_PY,
        kind="python",
    )
    result = _extract_python(df)
    named = {
        s.name: s.text
        for s in result.segments
        if s.name and not s.name.startswith("_") and s.name[0].islower()
    }
    assert len(named) >= 3


# ---------------------------------------------------------------------------
# TOML patching
# ---------------------------------------------------------------------------


def test_apply_toml_updates_translates_text_leaves() -> None:
    source = """
[product]
title = "Original title"
description = "Original description"
status = "pending"
"""
    segments = [
        Segment(
            segment_id="title",
            domain="retail",
            file_path=Path("db.toml"),
            relative_path=Path("db.toml"),
            kind="toml",
            address=("product", "title"),
            text="Original title",
        ),
        Segment(
            segment_id="description",
            domain="retail",
            file_path=Path("db.toml"),
            relative_path=Path("db.toml"),
            kind="toml",
            address=("product", "description"),
            text="Original description",
        ),
    ]

    updated = apply_toml_updates(
        source,
        segments,
        {"title": "Judul", "description": "Deskripsi"},
    )

    assert 'title = "Judul"' in updated
    assert 'description = "Deskripsi"' in updated
    assert 'status = "pending"' in updated


def test_write_outputs_copies_db_file_with_no_segments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("translation.pipeline.to_project_relative_path", lambda p: p)

    data_root = tmp_path / "data" / "tau2" / "domains"
    domain = "telecom"
    data_dir = data_root / domain
    data_dir.mkdir(parents=True)

    db_path = data_dir / "db.toml"
    user_db_path = data_dir / "user_db.toml"
    db_path.write_text('[plans]\ntitle = "Original title"\n', encoding="utf-8")
    user_db_path.write_text(
        '[device]\nnetwork_mode_preference = "4g_5g_preferred"\n',
        encoding="utf-8",
    )

    db_segment = Segment(
        segment_id="db_title",
        domain=domain,
        file_path=db_path,
        relative_path=db_path,
        kind="toml",
        address=("plans", "title"),
        text="Original title",
    )

    config = PipelineConfig(
        domains=[domain],
        target_language="Indonesian",
        lang_id="id",
        data_domains_root=data_root,
        src_domains_root=tmp_path / "src" / "tau2" / "domains",
    )

    written, manifest_updates = _write_outputs(
        segments=[db_segment],
        translated={"db_title": "Judul"},
        data_domains_root=data_root,
        lang_id="id",
        config=config,
        all_files=[
            DomainFile(domain=domain, path=db_path, relative_path=db_path, kind="toml"),
            DomainFile(
                domain=domain,
                path=user_db_path,
                relative_path=user_db_path,
                kind="toml",
            ),
        ],
    )

    out_dir = data_root / domain / "id"
    out_db = out_dir / "db.toml"
    out_user_db = out_dir / "user_db.toml"
    assert out_db in written
    assert out_user_db in written
    assert 'title = "Judul"' in out_db.read_text(encoding="utf-8")
    assert out_user_db.read_text(encoding="utf-8") == user_db_path.read_text(
        encoding="utf-8"
    )

    manifest_assets = next(iter(manifest_updates.values()))
    assert "db.toml" in manifest_assets
    assert "user_db.toml" in manifest_assets


def test_write_outputs_writes_schema_artifact_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("translation.pipeline.to_project_relative_path", lambda p: p)

    data_root = tmp_path / "data" / "tau2" / "domains"
    src_root = tmp_path / "src" / "tau2" / "domains"
    domain = "retail"
    src_dir = src_root / domain
    src_dir.mkdir(parents=True)
    schema_path = src_dir / "data_model.py"
    schema_path.write_text(
        "from typing import Literal\n"
        "from pydantic import BaseModel, Field\n\n"
        'OrderStatus = Literal["pending", "cancelled"]\n\n'
        "class Order(BaseModel):\n"
        '    """Represents an order."""\n'
        '    status: OrderStatus = Field(description="Status of the order.")\n',
        encoding="utf-8",
    )

    df = DomainFile(
        domain=domain,
        path=schema_path,
        relative_path=schema_path,
        kind="python",
    )
    _, extraction = build_schema_artifact(df)
    translated = {
        segment.segment_id: {
            ("models", "Order", "description"): "Merepresentasikan pesanan.",
            ("models", "Order", "fields", "status", "description"): "Status pesanan.",
            ("value_sets", "OrderStatus", "values", "0", "localized"): "menunggu",
            ("value_sets", "OrderStatus", "values", "1", "localized"): "dibatalkan",
        }.get(segment.address, segment.text)
        for segment in extraction.segments
    }

    config = PipelineConfig(
        domains=[domain],
        target_language="Indonesian",
        lang_id="id",
        components=("schema",),
        data_domains_root=data_root,
        src_domains_root=src_root,
    )

    written, manifest_updates = _write_outputs(
        segments=extraction.segments,
        translated=translated,
        data_domains_root=data_root,
        lang_id="id",
        config=config,
        all_files=[df],
    )

    out_path = data_root / domain / "id" / "data_model.json"
    assert out_path in written
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["models"]["Order"]["description"] == "Merepresentasikan pesanan."
    assert payload["models"]["Order"]["fields"]["status"]["description"] == (
        "Status pesanan."
    )
    assert payload["value_sets"]["OrderStatus"]["values"][0] == {
        "canonical": "pending",
        "localized": "menunggu",
    }
    assert payload["value_sets"]["OrderStatus"]["values"][1] == {
        "canonical": "cancelled",
        "localized": "dibatalkan",
    }

    manifest_assets = next(iter(manifest_updates.values()))
    assert manifest_assets["data_model.json"]["component"] == "schema"


def test_run_pipeline_db_only_copies_db_when_no_segments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("translation.pipeline.to_project_relative_path", lambda p: p)
    monkeypatch.setattr(
        "translation.pipeline._validate_vertex_environment", lambda _: None
    )

    data_root = tmp_path / "data" / "tau2" / "domains"
    domain = "airline"
    data_dir = data_root / domain
    data_dir.mkdir(parents=True)

    db_path = data_dir / "db.json"
    db_path.write_text(
        json.dumps(
            {
                "users": {
                    "alice_1": {
                        "id": "alice_1",
                        "status": "gold",
                    }
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    config = PipelineConfig(
        domains=[domain],
        target_language="Vietnamese",
        lang_id="vi",
        components=("db",),
        data_domains_root=data_root,
        src_domains_root=tmp_path / "src" / "tau2" / "domains",
    )

    result = run_pipeline(config)

    out_db = data_root / domain / "vi" / "db.json"
    manifest_path = data_root / domain / "vi" / "translation_manifest.json"
    assert result == 0
    assert out_db.exists()
    assert out_db.read_text(encoding="utf-8") == db_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "db.json" in manifest.get("assets", {})


def test_run_pipeline_schema_prose_reuses_translated_literal_labels(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("translation.pipeline.to_project_relative_path", lambda p: p)
    monkeypatch.setattr(
        "translation.pipeline._validate_vertex_environment", lambda _: None
    )

    data_root = tmp_path / "data" / "tau2" / "domains"
    src_root = tmp_path / "src" / "tau2" / "domains"
    domain = "retail"
    data_dir = data_root / domain
    src_dir = src_root / domain
    data_dir.mkdir(parents=True)
    src_dir.mkdir(parents=True)

    schema_path = src_dir / "data_model.py"
    schema_path.write_text(
        "from typing import Literal\n"
        "from pydantic import BaseModel, Field\n\n"
        'OrderStatus = Literal["pending", "cancelled"]\n\n'
        "class Order(BaseModel):\n"
        '    """Represents an order whose status may be pending or cancelled."""\n'
        '    status: OrderStatus = Field(description="Status should be pending before it becomes cancelled.")\n',
        encoding="utf-8",
    )

    class FakeTranslator:
        def __init__(
            self,
            model: str,
            timeout_s: int = 0,
            retries: int = 0,
        ) -> None:
            self.calls: list[tuple[bool, list[TranslationRequest]]] = []

        def translate_batch(
            self,
            requests: list[TranslationRequest],
            source_language: str,
            target_language: str,
            protected_terms: set[str] | None = None,
            translate_runtime_labels: bool = False,
        ) -> dict[str, str]:
            self.calls.append((translate_runtime_labels, requests))
            if translate_runtime_labels:
                replacements = {
                    "pending": "đang chờ xử lý",
                    "cancelled": "đã hủy",
                }
                return {
                    req.segment_id: replacements.get(req.text, f"LABEL::{req.text}")
                    for req in requests
                }
            return {req.segment_id: f"VI::{req.text}" for req in requests}

    fake_translator = FakeTranslator(model="")
    monkeypatch.setattr(
        "translation.pipeline.LiteLLMTranslator", lambda **_: fake_translator
    )

    config = PipelineConfig(
        domains=[domain],
        target_language="Vietnamese",
        lang_id="vi",
        components=("schema",),
        data_domains_root=data_root,
        src_domains_root=src_root,
    )

    result = run_pipeline(config)

    out_path = data_root / domain / "vi" / "data_model.json"
    payload = json.loads(out_path.read_text(encoding="utf-8"))

    assert result == 0
    assert payload["value_sets"]["OrderStatus"]["values"] == [
        {"canonical": "pending", "localized": "đang chờ xử lý"},
        {"canonical": "cancelled", "localized": "đã hủy"},
    ]
    assert payload["models"]["Order"]["description"] == (
        "VI::Represents an order whose status may be đang chờ xử lý or đã hủy."
    )
    assert payload["models"]["Order"]["fields"]["status"]["description"] == (
        "VI::Status should be đang chờ xử lý before it becomes đã hủy."
    )


# ---------------------------------------------------------------------------
# Write / load roundtrip
# ---------------------------------------------------------------------------


def test_write_and_load_roundtrip(tmp_path: Path) -> None:
    """tools.json round-trips exactly; translated_asset_path resolves correctly."""
    doc_map = {"cancel_order": "Hủy đơn hàng đang chờ xử lý."}
    lang_code = "th"
    domain = "retail"

    dst = tmp_path / domain / lang_code / "tools.json"
    dst.parent.mkdir(parents=True)
    dst.write_text(
        json.dumps(doc_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    loaded = load_docstrings_json(dst)
    assert loaded == doc_map

    expected = translated_asset_path(tmp_path, lang_code, domain, "tools.json")
    assert expected == dst


# ---------------------------------------------------------------------------
# Docstring injection
# ---------------------------------------------------------------------------


def test_patch_restore_injection() -> None:
    """patch_toolkit_docstrings / restore_toolkit_docstrings round-trip correctly."""
    docs = {"cancel_order": "Hủy đơn hàng.", "get_order": "Lấy đơn hàng."}
    cls = _make_fake_toolkit(docs)

    originals = patch_toolkit_docstrings(cls, docs)
    for name, doc in docs.items():
        assert getattr(cls, name).__doc__ == doc

    restore_toolkit_docstrings(cls, originals)
    for name in docs:
        assert getattr(cls, name).__doc__ == "original"


def test_localized_toolkit_context_manager() -> None:
    """localized_toolkit restores original docstrings on exit."""
    docs = {"cancel_order": "Hủy đơn hàng.", "get_order": "Lấy đơn hàng."}
    cls = _make_fake_toolkit(docs)

    with localized_toolkit(cls, docs) as patched:
        for name, doc in docs.items():
            assert getattr(patched, name).__doc__ == doc

    for name in docs:
        assert getattr(cls, name).__doc__ == "original"


def test_reconstruct_tool_docstring_preserves_structure_and_multiline() -> None:
    source = (
        "Cancel a pending order.\n\n"
        "Handle cancellation with validation.\n\n"
        "Args:\n"
        "    order_id: The order id.\n"
        "        Must be active.\n\n"
        "Returns:\n"
        "    Order: The updated order.\n"
    )
    rebuilt = _reconstruct_tool_docstring(
        source,
        {
            "short": "Huy don hang dang cho xu ly.",
            "long": "Xu ly huy voi xac thuc.",
            "param:order_id": "Ma don hang.\nPhai con hieu luc.",
            "returns": "Don hang da cap nhat.",
        },
    )

    assert rebuilt.startswith("Huy don hang dang cho xu ly.")
    assert "Xu ly huy voi xac thuc." in rebuilt
    assert "Args:" in rebuilt
    assert "Returns:" in rebuilt
    assert "order_id: Ma don hang." in rebuilt
    assert "Phai con hieu luc." in rebuilt
    assert "Order: Don hang da cap nhat." in rebuilt


def test_mask_protected_tokens_preserves_retail_canonical_terms() -> None:
    text = (
        "The order stays pending, may become exchange requested, and the reason "
        "must be ordered by mistake."
    )

    masked = mask_protected_tokens(text, FIXED_PROTECTED_TERMS)

    assert "__PH_0__" in masked.text
    assert "pending" not in masked.text
    assert "exchange requested" not in masked.text
    assert "ordered by mistake" not in masked.text

    restored = unmask_protected_tokens(masked.text, masked)
    assert restored == text


def test_unmask_protected_tokens_accepts_exact_token_passthrough() -> None:
    text = "A pending order can become cancelled."
    masked = mask_protected_tokens(text, FIXED_PROTECTED_TERMS)

    translated_like_model = masked.text.replace("__PH_1__", "cancelled")

    restored = unmask_protected_tokens(translated_like_model, masked)
    assert restored == text


def test_mask_segment_protected_tokens_masks_contextual_airline_literals_in_policy() -> (
    None
):
    text = (
        "You want the cheapest economy options.\n"
        "If the status is **available**, the flight can be booked.\n"
        "Cabin classes are **economy** and **business**."
    )
    segment = Segment(
        segment_id="policy",
        domain="airline",
        file_path=Path("policy.md"),
        relative_path=Path("policy.md"),
        kind="markdown",
        address="full",
        text=text,
    )

    masked = mask_segment_protected_tokens(segment, protected_terms=set())

    assert "You want the cheapest economy options." in masked.text
    assert "**__PH_0__**" in masked.text
    assert "**__PH_1__**" in masked.text
    assert "**__PH_2__**" in masked.text
    assert masked.placeholders == ["available", "economy", "business"]


def test_mask_segment_protected_tokens_masks_contextual_airline_literals_by_path() -> (
    None
):
    segment = Segment(
        segment_id="status",
        domain="airline",
        file_path=Path("db.json"),
        relative_path=Path("db.json"),
        kind="json",
        address=("flights", "HAT001", "dates", "2024-05-16", "status"),
        text="available",
    )

    masked = mask_segment_protected_tokens(segment, protected_terms=set())

    assert masked.text == "__PH_0__"
    assert masked.placeholders == ["available"]


def test_mask_protected_tokens_does_not_fragment_embedded_numeric_substrings() -> None:
    text = "Agent updates reservation OBUT9V return flights to HAT290 and HAT175."

    masked = mask_protected_tokens(text, {"9", "29", "0", "17", "5"})

    assert masked.text == text
    assert masked.placeholders == []


def test_extract_db_json_skips_numeric_only_canonical_values(tmp_path: Path) -> None:
    db_file = tmp_path / "db.json"
    db_file.write_text(
        json.dumps(
            {
                "records": {
                    "27": {
                        "id": "27",
                        "status": "pending",
                        "name": "Sample item",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    extraction = _extract_db_json(
        DomainFile(
            domain="test",
            path=db_file,
            relative_path=db_file,
            kind="json",
        )
    )

    assert "27" not in extraction.protected_terms
    assert "pending" in extraction.protected_terms


def test_extract_db_json_translates_airline_address_fields_only(tmp_path: Path) -> None:
    db_file = tmp_path / "db.json"
    db_file.write_text(
        json.dumps(
            {
                "users": {
                    "john_smith_1": {
                        "user_id": "john_smith_1",
                        "name": {
                            "first_name": "John",
                            "last_name": "Smith",
                        },
                        "address": {
                            "address1": "181 Park Avenue",
                            "address2": "Suite 200",
                            "city": "Austin",
                            "country": "USA",
                            "state": "TX",
                            "zip": "78750",
                        },
                        "membership": "gold",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    extraction = _extract_db_json(
        DomainFile(
            domain="airline",
            path=db_file,
            relative_path=db_file,
            kind="json",
        )
    )

    extracted_paths = {segment.address for segment in extraction.segments}
    assert ("users", "john_smith_1", "address", "address1") in extracted_paths
    assert ("users", "john_smith_1", "address", "address2") in extracted_paths
    assert ("users", "john_smith_1", "address", "city") in extracted_paths
    assert ("users", "john_smith_1", "name", "first_name") not in extracted_paths
    assert ("users", "john_smith_1", "membership") not in extracted_paths


def test_extract_db_json_keeps_airline_address_keys_domain_scoped(
    tmp_path: Path,
) -> None:
    db_file = tmp_path / "db.json"
    db_file.write_text(
        json.dumps(
            {
                "profile": {
                    "address1": "181 Park Avenue",
                    "address2": "Suite 200",
                    "city": "Austin",
                    "name": "Retail profile",
                }
            }
        ),
        encoding="utf-8",
    )

    extraction = _extract_db_json(
        DomainFile(
            domain="retail",
            path=db_file,
            relative_path=db_file,
            kind="json",
        )
    )

    extracted_paths = {segment.address for segment in extraction.segments}
    assert ("profile", "name") in extracted_paths
    assert ("profile", "address1") not in extracted_paths
    assert ("profile", "address2") not in extracted_paths
    assert ("profile", "city") not in extracted_paths


# ---------------------------------------------------------------------------
# Stale / missing translation warnings
# ---------------------------------------------------------------------------


def test_get_stale_translation_warnings_reports_changed_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "data"
    domain_root = data_dir / "tau2" / "domains" / "retail"
    translated_root = domain_root / "th"
    translated_root.mkdir(parents=True)

    source_file = tmp_path / "src" / "tau2" / "domains" / "retail" / "tools.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text('"""before"""', encoding="utf-8")

    translated_file = translated_root / "tools.json"
    translated_file.write_text('{"tool":"doc"}\n', encoding="utf-8")
    manifest_path = translated_root / language_utils.TRANSLATION_MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(
            {
                "assets": {
                    "tools.json": {
                        "source_files": [
                            {
                                "path": str(source_file),
                                "sha256": "stale",
                            }
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(language_utils, "DATA_DIR", data_dir)

    warnings = language_utils.get_stale_translation_warnings(
        "retail", "th", ["tools.json"]
    )

    assert len(warnings) == 1
    assert "rerun translation" in warnings[0].lower()


def test_get_stale_translation_warnings_resolves_relative_source_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_project_root = tmp_path / "repo"
    source_file = fake_project_root / "src" / "tau2" / "domains" / "retail" / "tools.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text('"""before"""', encoding="utf-8")

    data_dir = fake_project_root / "data"
    translated_root = data_dir / "tau2" / "domains" / "retail" / "th"
    translated_root.mkdir(parents=True)
    (translated_root / "tools.json").write_text('{"tool":"doc"}\n', encoding="utf-8")
    manifest_path = translated_root / language_utils.TRANSLATION_MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(
            {
                "assets": {
                    "tools.json": {
                        "source_files": [
                            {
                                "path": "src/tau2/domains/retail/tools.py",
                                "sha256": "stale",
                            }
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(path_utils, "PROJECT_ROOT", fake_project_root)
    monkeypatch.setattr(language_utils, "DATA_DIR", data_dir)

    warnings = language_utils.get_stale_translation_warnings(
        "retail", "th", ["tools.json"]
    )

    assert len(warnings) == 1
    assert "rerun translation" in warnings[0].lower()


def test_manifest_source_paths_are_project_relative() -> None:
    source_file = PROJECT_ROOT / "src" / "translation" / "language.py"
    rel = to_project_relative_path(source_file)
    assert rel.as_posix() == "src/translation/language.py"
    assert resolve_project_path(rel) == source_file.resolve()


def test_missing_translation_component_warnings_report_enabled_missing_assets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "data"
    translated_root = data_dir / "tau2" / "domains" / "retail" / "vi"
    translated_root.mkdir(parents=True)

    (translated_root / "tools.json").write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(language_utils, "DATA_DIR", data_dir)

    warnings = language_utils.get_missing_translation_component_warnings(
        "retail",
        "vi",
        ["tools", "policy", "db", "tasks"],
    )

    assert len(warnings) == 3
    assert any("policy" in w for w in warnings)
    assert any("db" in w for w in warnings)
    assert any("tasks" in w for w in warnings)


# ---------------------------------------------------------------------------
# Language component resolution (TextRunConfig)
# ---------------------------------------------------------------------------


def test_resolve_language_components_defaults_to_all() -> None:
    assert language_utils.resolve_language_components(None) == set(
        language_utils.DEFAULT_LANGUAGE_COMPONENTS
    )


def test_effective_lang_components_require_lang_id() -> None:
    no_lang = TextRunConfig(lang_components=["user_system", "agent_system"])
    assert no_lang.effective_lang_components == set()

    with_lang = TextRunConfig(
        lang_id="vi", lang_components=["user_system", "agent_system"]
    )
    assert with_lang.effective_lang_components == {"user_system", "agent_system"}


def test_effective_lang_components_default_to_all_when_lang_id_is_set() -> None:
    with_lang = TextRunConfig(lang_id="vi")
    assert with_lang.effective_lang_components == set(
        language_utils.DEFAULT_LANGUAGE_COMPONENTS
    )


def test_effective_lang_components_respects_explicit_subset() -> None:
    with_lang = TextRunConfig(
        lang_id="vi",
        lang_components=["agent_system", "greeting"],
    )
    assert with_lang.effective_lang_components == {
        "agent_system",
        "greeting",
    }


def test_effective_lang_components_can_be_empty_with_lang_id() -> None:
    with_lang = TextRunConfig(
        lang_id="vi",
        lang_components=[],
    )
    assert with_lang.effective_lang_components == set()


def test_resolve_language_components_supports_context_and_all_aliases() -> None:
    assert language_utils.resolve_language_components(["context", "user_system"]) == {
        "user_system",
        "policy",
        "db",
        "tasks",
    }
    assert language_utils.resolve_language_components(["all"]) == set(
        language_utils.DEFAULT_LANGUAGE_COMPONENTS
    )


# ---------------------------------------------------------------------------
# End-to-end dry-run (no API call needed)
# ---------------------------------------------------------------------------


def test_e2e_dry_run(tmp_path: Path) -> None:
    """Full pipeline dry-run: extract → fake-translate → write/load → inject."""
    tools_file = tmp_path / "tools.py"
    tools_file.write_text(
        'def cancel_order():\n    """Cancel a pending order."""\n    ...\n'
        'def get_order():\n    """Get order details."""\n    ...\n',
        encoding="utf-8",
    )
    df = DomainFile(
        domain="retail", path=tools_file, relative_path=tools_file, kind="python"
    )
    result = _extract_python(df)
    named = {
        s.name: s.text
        for s in result.segments
        if s.name and not s.name.startswith("_") and s.name[0].islower()
    }
    assert named, "No public docstrings extracted"

    lang_code = "th"
    doc_map = {name: f"[TH] {text[:60]}" for name, text in named.items()}

    dst = tmp_path / "retail" / lang_code / "tools.json"
    dst.parent.mkdir(parents=True)
    dst.write_text(
        json.dumps(doc_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    loaded = load_docstrings_json(dst)
    assert loaded == doc_map

    cls = _make_fake_toolkit(loaded)
    originals = patch_toolkit_docstrings(cls, loaded)
    for name, doc in loaded.items():
        assert getattr(cls, name).__doc__ == doc
    restore_toolkit_docstrings(cls, originals)
    for name in loaded:
        assert getattr(cls, name).__doc__ == "original"


# ---------------------------------------------------------------------------
# End-to-end with real Vertex API (skipped unless Vertex env is set)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _RETAIL_TOOLS_PY.exists(), reason="retail tools.py not found")
@pytest.mark.skipif(
    not (os.getenv("VERTEXAI_PROJECT") and os.getenv("VERTEXAI_LOCATION")),
    reason="VERTEXAI_PROJECT and VERTEXAI_LOCATION not set",
)
@pytest.mark.translation_api
def test_e2e_with_vertex_api(tmp_path: Path) -> None:
    """Full pipeline with Vertex API: extract 3 docstrings → translate → write/load → inject."""
    from translation.litellm_translator import LiteLLMTranslator
    from translation.models import TranslationRequest

    df = DomainFile(
        domain="retail",
        path=_RETAIL_TOOLS_PY,
        relative_path=_RETAIL_TOOLS_PY,
        kind="python",
    )
    result = _extract_python(df)
    named = {
        s.name: s.text
        for s in result.segments
        if s.name and not s.name.startswith("_") and s.name[0].islower()
    }
    subset = dict(list(named.items())[:3])

    lang_code = "th"
    lang_data = json.loads(_LANGUAGES_JSON.read_text(encoding="utf-8"))
    target_language = lang_data[lang_code]["display_name"]

    translator = LiteLLMTranslator(
        model="vertex_ai/gemini-3.1-flash-lite-preview",
    )
    requests = [
        TranslationRequest(segment_id=name, text=text) for name, text in subset.items()
    ]
    doc_map = translator.translate_batch(
        requests=requests,
        source_language="English",
        target_language=target_language,
    )
    assert len(doc_map) == len(subset)

    dst = tmp_path / "retail" / lang_code / "tools.json"
    dst.parent.mkdir(parents=True)
    dst.write_text(
        json.dumps(doc_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    loaded = load_docstrings_json(dst)
    assert loaded == doc_map

    cls = _make_fake_toolkit(loaded)
    with localized_toolkit(cls, loaded):
        for name, doc in loaded.items():
            assert getattr(cls, name).__doc__ == doc
    for name in loaded:
        assert getattr(cls, name).__doc__ == "original"
