"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und jedes Preset zeigt den Effekt, den sein Hilfetext verspricht."""

import mvg_constants as C
import mvg_evaluation as ev
import mvg_presets as P


def _settings(name):
    return ev.Settings(**C.PRESETS[name])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds_and_choices():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and 0 <= preset["seed"] <= C.SEED_MAX and preset["graph"] in C.GRAPHS and preset["task"] in C.TASKS
        assert C.K_MIN <= preset["k"] <= C.K_MAX and C.C_MIN <= preset["c"] <= C.C_MAX


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()
    defaults = ev.Settings()
    assert [P.SETTING_SPECS[key].default for key in ("n_slider", "seed_input", "graph_select", "task_select", "k_slider", "c_slider")] == [defaults.n, defaults.seed, defaults.graph, defaults.task, defaults.k, defaults.c]


def test_setting_specs_cover_every_preset_key_and_have_valid_defaults():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    for spec in P.SETTING_SPECS.values():
        assert spec.choices is None or (spec.default in spec.choices and spec.lo in spec.choices and spec.hi in spec.choices)


def test_no_single_regler_change_of_the_default_lands_on_another_preset():
    """Das Layout setzt jeden Regler auf seinen Höchstwert (oder Tiefstwert): das darf kein Preset treffen, sonst bliebe ein Preset markiert."""
    default = dict(C.PRESETS["Standardfall (Voreinstellung)"])
    for state_key, spec in P.SETTING_SPECS.items():
        key = next(k for k, v in P.PRESET_KEYS.items() if v == state_key)
        for value in (spec.hi, spec.lo):
            if value == default[key]:
                continue                                  # das Layout setzt dann den anderen Wert
            variant = {**default, key: value}
            assert all(variant != preset for preset in C.PRESETS.values()), (state_key, value)


def test_two_trees_preset_has_two_edge_disjoint_spanning_trees_that_use_all_edges():
    s = _settings("Zwei Spannbäume")
    a = ev.analyse(s)
    assert (a.nodes, a.m, a.spanning, a.complete) == (6, 10, True, True)
    assert ev.trees_view(s)["alg"] == 2


def test_k4_preset_two_trees_use_all_six_edges():
    a = ev.analyse(_settings("K4: zwei Bäume"))
    assert (a.nodes, a.m, a.spanning, a.complete) == (4, 6, True, True)


def test_k5_preset_needs_three_forests_but_has_only_two_trees():
    s = _settings("K5: drei Wälder")
    a = ev.analyse(s)
    assert (a.m, a.complete, a.spanning) == (10, True, False)
    assert ev.trees_view(s)["alg"] == 2 and ev.arb_view(s)["alg"] == 3


def test_default_help_numbers_hold():
    s = _settings("Standardfall (Voreinstellung)")
    a = ev.analyse(s)
    assert (a.nodes, a.m, a.size) == (7, 12, 11) and ev.trees_view(s)["alg"] == 1 and ev.trees_view(s)["cert"]["classes"] == 3


def test_color_preset_uses_a_forest_and_the_color_rule():
    s = _settings("Wald und Farbregel")
    a = ev.analyse(s)
    assert a.matroids == ("Wald", "Farbregel") and (a.m, a.size) == (12, 10) and s.c == 4
