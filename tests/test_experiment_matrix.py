from seatau.experiment_matrix import get_scenario_preset, list_all_scenarios


def test_tool_scenarios_have_distinct_localization_modes() -> None:
    single = get_scenario_preset("l2_tools")
    mixed = get_scenario_preset("l2_tools_mix")

    assert single.lang_components == ("tools",)
    assert single.tool_mix is False
    assert mixed.lang_components == ("tool_mix",)
    assert mixed.tool_mix is True


def test_auxiliary_scenarios_are_opt_in_for_primary_matrix_consumers() -> None:
    assert "l2_tools_mix" not in list_all_scenarios()
    assert "l2_tools_mix" in list_all_scenarios(include_auxiliary=True)
