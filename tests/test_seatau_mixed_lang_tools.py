from seatau.constants import get_domain_src_path
from seatau.mixed_lang_tools import load_mixed_docstrings, load_mixed_tools_config
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
    config = load_mixed_tools_config(config_name)
    return load_mixed_docstrings(
        domain="retail",
        tool_names=_retail_tool_names(),
        config=config,
        src_tools_path=get_domain_src_path("retail") / "tools.py",
    )


def test_load_five_language_mixed_tools_config_uses_nested_progressive() -> None:
    config = load_mixed_tools_config("5lang_uniform_en-th-vi-id-zh")

    assert config.partitioning.group_mode is False
    assert config.partitioning.partition_strategy == "nested_progressive"
    assert config.partitioning.tools_per_added_language == 3


def test_retail_five_language_mixed_tools_has_full_docstring_coverage() -> None:
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


def test_retail_default_mixed_configs_are_nested_progressive() -> None:
    partitions = [
        (load_mixed_tools_config(config_name), _retail_partition(config_name)[1])
        for config_name in MIXED_CONFIGS
    ]

    for (previous_config, previous), (current_config, current) in zip(
        partitions, partitions[1:]
    ):
        previous_assignments = previous.tool_assignments
        current_assignments = current.tool_assignments
        new_languages = (
            set(current_config.languages.codes) - set(previous_config.languages.codes)
        )

        for tool, previous_assignment in previous_assignments.items():
            current_lang = current_assignments[tool].lang
            if previous_assignment.lang != "en":
                assert current_lang == previous_assignment.lang
            elif current_lang != previous_assignment.lang:
                assert current_lang in new_languages
