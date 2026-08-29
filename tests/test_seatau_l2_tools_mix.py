import pytest

from paths import TAU2_DOMAINS_SRC
from seatau.l2_tools_mix import load_mixed_docstrings, load_tool_mix_config
from seatau.l2_tools_mix import partition as partition_module
from tau2.domains.retail.environment import get_environment

MIXED_CONFIGS = [
    "2lang_uniform_en-th",
    "3lang_uniform_en-th-vi",
    "4lang_uniform_en-th-vi-id",
    "5lang_uniform_en-th-vi-id-zh",
]


def _retail_tool_names() -> list[str]:
    return sorted(get_environment().tools.get_tools().keys())


def _retail_partition(config_name: str):
    config = load_tool_mix_config(config_name)
    return load_mixed_docstrings(
        domain="retail",
        tool_names=_retail_tool_names(),
        config=config,
        src_tools_path=TAU2_DOMAINS_SRC / "retail" / "tools.py",
    )


def test_load_five_language_tool_mix_config_uses_nested_progressive() -> None:
    config = load_tool_mix_config("5lang_uniform_en-th-vi-id-zh")

    assert config.partitioning.group_mode is False
    assert config.partitioning.partition_strategy == "nested_progressive"
    assert config.partitioning.tools_per_added_language == 3


def test_retail_five_language_tool_mix_has_full_docstring_coverage() -> None:
    docs, partition = _retail_partition("5lang_uniform_en-th-vi-id-zh")
    tool_names = set(_retail_tool_names())

    assert len(tool_names) == 16
    assert set(docs) == tool_names
    assert partition.summary.by_language == {
        "en": 4,
        "th": 3,
        "vi": 3,
        "id": 3,
        "zh": 3,
    }


def test_load_mixed_docstrings_fails_when_assigned_docs_are_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool_names = _retail_tool_names()

    def fake_load_docstrings_for_lang(*args: object) -> dict[str, str]:
        lang = args[1]
        if lang == "en":
            return {tool: f"English doc for {tool}" for tool in tool_names}
        return {}

    monkeypatch.setattr(
        partition_module,
        "_load_docstrings_for_lang",
        fake_load_docstrings_for_lang,
    )

    with pytest.raises(ValueError, match="Missing tool-mix docstrings"):
        load_mixed_docstrings(
            domain="retail",
            tool_names=tool_names,
            config=load_tool_mix_config("2lang_uniform_en-th"),
            src_tools_path=TAU2_DOMAINS_SRC / "retail" / "tools.py",
        )


def test_retail_progressive_configs_add_three_tools_per_language() -> None:
    expected_by_config = {
        "2lang_uniform_en-th": {"en": 13, "th": 3},
        "3lang_uniform_en-th-vi": {"en": 10, "th": 3, "vi": 3},
        "4lang_uniform_en-th-vi-id": {"en": 7, "th": 3, "vi": 3, "id": 3},
        "5lang_uniform_en-th-vi-id-zh": {
            "en": 4,
            "th": 3,
            "vi": 3,
            "id": 3,
            "zh": 3,
        },
    }

    for config_name, expected in expected_by_config.items():
        _docs, partition = _retail_partition(config_name)
        assert partition.summary.by_language == expected


def test_retail_default_tool_mix_configs_are_nested_progressive() -> None:
    partitions = [
        (load_tool_mix_config(config_name), _retail_partition(config_name)[1])
        for config_name in MIXED_CONFIGS
    ]

    for (previous_config, previous), (current_config, current) in zip(
        partitions, partitions[1:]
    ):
        previous_assignments = previous.tool_assignments
        current_assignments = current.tool_assignments
        new_languages = set(current_config.languages.codes) - set(
            previous_config.languages.codes
        )

        for tool, previous_assignment in previous_assignments.items():
            current_lang = current_assignments[tool].lang
            if previous_assignment.lang != "en":
                assert current_lang == previous_assignment.lang
            elif current_lang != previous_assignment.lang:
                assert current_lang in new_languages
