"""AppTest: Hauptansicht, Experimente, Spielwiese, Permalink und PDF (DEMO-PLAYBOOK §3, §5)."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import mvg_constants as C
import mvg_evaluation as ev
from mvg_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
PLAY = "plan_7_8_waelder_2_6"


def _app(params=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    for key, value in (params or {}).items():
        at.query_params[key] = value
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return [m.value for m in list(at.success) + list(at.info) + list(at.warning) + list(at.error)]


def _click_preset(at, name):
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]


def test_default_shows_the_last_round_with_the_certificate_and_the_metrics():
    at = _app()
    assert [m.value for m in at.metric][:4] == ["12", "11", "11", "11"]
    texts = _texts(at)
    assert any("Runde 12: Von der Leitung {D–G} führt **kein Weg** mehr zu einer Senke" in t and "= 3 + 8 = **11**" in t for t in texts)
    assert any("2 kantendisjunkte Spannbäume **gibt es nicht**" in t for t in texts)


def test_round_slider_walks_through_the_rounds():
    at = _app()
    at.slider(key=f"round_{PLAY}").set_value(1).run()
    assert not at.exception and any(t.startswith("Runde 1: 0 Leitungen sind untergebracht. A–B passt ohne Tausch in Wald 1") for t in _texts(at))
    at.slider(key=f"round_{PLAY}").set_value(11).run()
    assert not at.exception and any("Der kürzeste Weg hat 2 Elemente: C–G → A–C" in t for t in _texts(at))


def test_main_verdict_matches_each_preset():
    expected = {
        "Standardfall (Voreinstellung)": "Von der Leitung {D–G} führt **kein Weg** mehr",
        "Zwei Spannbäume": "**Alle 10 Leitungen** sind untergebracht",
        "K4: zwei Bäume": "**Alle 6 Leitungen** sind untergebracht",
        "K5: drei Wälder": "**Alle 10 Leitungen** sind untergebracht",
        "Wald und Farbregel": "Von den 2 Leitungen {C–G, F–G} führt **kein Weg** mehr",
    }
    at = _app()
    for name, needle in expected.items():
        _click_preset(at, name)
        assert any(needle in t for t in _texts(at)), name


def test_experiment_one_and_two_follow_the_net():
    at = _app()
    texts = _texts(at)
    assert any("höchstens **1 Spannbaum**" in t and "alle 876 Partitionen" in t for t in texts)
    assert any("auf **3** Wälder verteilen" in t and "alle 120 Knotenmengen" in t for t in texts)
    _click_preset(at, "K5: drei Wälder")
    texts = _texts(at)
    assert any("höchstens **2 kantendisjunkte Spannbäume**" in t and "5 Klassen" in t for t in texts)
    assert any("auf **3** Wälder verteilen" in t and "mit 5 Standorten **10** Leitungen" in t for t in texts)


def test_experiment_three_follows_the_color_slider():
    at = _app()
    assert any("kommen **11** in einen Wald (6)" in t and "wird bei 4 Mengen angenommen" in t for t in _texts(at))
    at.sidebar.slider(key="c_slider").set_value(4).run()
    assert not at.exception and any("kommen **10** in einen Wald (6)" in t and "wird bei 2 Mengen angenommen" in t for t in _texts(at))


def test_experiment_four_and_the_series_on_demand():
    at = _app()
    assert not any("7 409" in t for t in _texts(at)) and not any("50 %, 25 %, 5 %" in t for t in _texts(at))
    at.button(key="small_run").click().run()
    assert not at.exception and any("Bei allen 7 409 geprüften Paaren" in t and "**5,3-mal**" in t for t in _texts(at))
    at.button(key="series_run").click().run()
    assert not at.exception and any("50 %, 25 %, 5 %" in t for t in _texts(at))
    _click_preset(at, "K4: zwei Bäume")
    assert any("7 409" in t for t in _texts(at)) and any("50 %, 25 %, 5 %" in t for t in _texts(at))      # die Ergebnisse bleiben nach anderen Änderungen


def test_every_net_and_task_runs_without_exception_and_has_a_verdict():
    at = _app()
    for graph in C.GRAPHS:
        for task in C.TASKS:
            at.sidebar.selectbox(key="graph_select").set_value(graph).run()
            at.sidebar.selectbox(key="task_select").set_value(task).run()
            assert not at.exception, (graph, task, [str(e) for e in at.exception])
            texts = _texts(at)
            assert any(t.startswith("Runde ") for t in texts) and any("Spannb" in t for t in texts) and any("Mengen Y" in t for t in texts), (graph, task)


def test_k_slider_changes_the_number_of_forests():
    at = _app()
    at.sidebar.slider(key="k_slider").set_value(3).run()
    assert not at.exception and any("alle Leitungen passen auf 3 Wälder" in t for t in _texts(at)) and at.metric[1].value == "12"


def test_playground_branches():
    at = _app()
    assert any("lassen sich **nicht** auf 2 Wälder verteilen (untergebracht: 11)" in t for t in _texts(at))
    at.multiselect(key=f"play_{PLAY}").set_value([0, 1, 2]).run()
    assert not at.exception and any("Die 3 gewählten Leitungen lassen sich auf 2 Wälder verteilen" in t for t in _texts(at))
    at.multiselect(key=f"play_{PLAY}").set_value([]).run()
    assert not at.exception and any(t == "Wählen Sie mindestens eine Leitung." for t in _texts(at))


def test_permalink_loads_valid_values_and_ignores_invalid_choices():
    at = _app(dict(n="8", seed="3", graph="k5", task="farben", k="4", c="3"))
    assert at.sidebar.slider(key="n_slider").value == 8 and at.sidebar.number_input(key="seed_input").value == 3
    assert at.sidebar.selectbox(key="graph_select").value == "k5" and at.sidebar.selectbox(key="task_select").value == "farben"
    assert at.sidebar.slider(key="k_slider").value == 4 and at.sidebar.slider(key="c_slider").value == 3
    bad = _app(dict(n="99", seed="-4", graph="gibtsnicht", task="nichts", k="99", c="99"))
    assert bad.sidebar.slider(key="n_slider").value == C.N_MAX and bad.sidebar.number_input(key="seed_input").value == 0
    assert bad.sidebar.selectbox(key="graph_select").value == "plan" and bad.sidebar.selectbox(key="task_select").value == "waelder"
    assert bad.sidebar.slider(key="k_slider").value == C.K_MAX and bad.sidebar.slider(key="c_slider").value == C.C_MAX


def test_address_line_mirrors_the_settings():
    at = _app(dict(graph="k33"))
    assert str(at.query_params["graph"]) in ("k33", "['k33']")


def test_pdf_button_makes_a_download():
    at = _app()
    at.button(key="pdf_make").click().run()
    assert not at.exception and "pdf_made" in at.session_state and at.session_state["pdf_made"][1][:4] == b"%PDF"


def test_pdf_builds_for_every_net_and_task():
    for graph in C.GRAPHS:
        for task in C.TASKS:
            s = ev.Settings(n=6, seed=2, graph=graph, task=task, k=3, c=4)
            assert build_pdf(ev.analyse(s), s)[:4] == b"%PDF", (graph, task)


def test_extreme_plan_sizes_do_not_raise():
    for n in (C.N_MIN, C.N_MAX):
        for task in C.TASKS:
            at = _app(dict(n=str(n), task=task))
            assert not at.exception, (n, task)
