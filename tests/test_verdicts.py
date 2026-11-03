"""Verdikte (reine Funktionen in mvg_evaluation.py) an handgesetzten Werten: jeder Zweig, jede Zahl im Text (DEMO-PLAYBOOK §4)."""

from dataclasses import replace

import mvg_constants as C
import mvg_evaluation as ev


def _preset(name):
    s = ev.Settings(**C.PRESETS[name])
    return s, ev.analyse(s), ev.run_view(s)


# --- Hauptansicht ------------------------------------------------------------------------------------------------------------------------


def test_round_verdict_without_swap_names_the_element_and_the_forest():
    s, a, run = _preset("Standardfall (Voreinstellung)")
    assert ev.verdict_round(a, run, 0) == ("info", "Runde 1: 0 Leitungen sind untergebracht. A–B passt ohne Tausch in Wald 1. Danach sind es 1.")


def test_round_verdict_with_a_path_names_the_swaps():
    s, a, run = _preset("Standardfall (Voreinstellung)")
    kind, text = ev.verdict_round(a, run, 10)
    assert kind == "info" and "Der kürzeste Weg hat 2 Elemente: C–G → A–C." in text and "C–G nimmt den Platz von A–C; zuletzt kommt A–C in Wald 2." in text and text.endswith("Danach sind es 11.")


def test_round_verdict_at_the_end_gives_the_certificate_and_checks_it():
    s, a, run = _preset("Standardfall (Voreinstellung)")
    kind, text = ev.verdict_round(a, run, 11)
    assert kind == "success" and text.startswith("Runde 12: Von der Leitung {D–G} führt **kein Weg** mehr")
    assert "Untergebracht sind **11** von 12 Leitungen" in text and "= 3 + 8 = **11**" in text and "Minimum über alle Y (11)" in text
    assert ev.verdict_round(replace(a, certificate=10), run, 11)[0] == "error"
    assert ev.verdict_round(replace(a, formula=12), run, 11)[0] == "error"


def test_round_verdict_when_everything_is_placed_has_the_empty_certificate():
    s, a, run = _preset("Zwei Spannbäume")
    kind, text = ev.verdict_round(a, run, len(run["rounds"]) - 1)
    assert kind == "success" and "**Alle 10 Leitungen**" in text and "Y = ∅" in text and "= 10 + 0" in text


def test_round_verdict_for_two_unplaced_names_both_and_the_matroid_words_follow_the_task():
    s, a, run = _preset("Wald und Farbregel")
    kind, text = ev.verdict_round(a, run, len(run["rounds"]) - 1)
    assert kind == "success" and "Von den 2 Leitungen {C–G, F–G}" in text and "= 1 + 9 = **10**" in text
    assert "zuletzt kommt A–D in die Farbregel" in ev.verdict_round(a, run, 9)[1]
    assert "passt ohne Tausch in den Wald" in ev.verdict_round(a, run, 0)[1]


def test_final_verdict_names_trees_and_cover():
    assert ev.verdict_final(_preset("Standardfall (Voreinstellung)")[1]) == (
        "info", "Bei 7 Standorten und 12 Leitungen: 2 kantendisjunkte Spannbäume **gibt es nicht**; nicht alle Leitungen passen auf 2 Wälder (untergebracht: 11 von 12).")
    assert ev.verdict_final(_preset("Zwei Spannbäume")[1])[0] == "success"
    assert ev.verdict_final(_preset("K5: drei Wälder")[1]) == ("info", "Bei 5 Standorten und 10 Leitungen: 3 kantendisjunkte Spannbäume **gibt es nicht**; alle Leitungen passen auf 3 Wälder.")
    assert "höchstens einer Leitung je Farbe; 2 bleiben übrig" in ev.verdict_final(_preset("Wald und Farbregel")[1])[1]
    s, a, run = _preset("K4: zwei Bäume")
    assert ev.verdict_final(replace(a, k=1, complete=False, spanning=False))[1].startswith("Bei 4 Standorten und 6 Leitungen: 1 Spannbaum **gibt es nicht**")


def test_round_rows_and_groups():
    s, a, run = _preset("Standardfall (Voreinstellung)")
    rows = ev.round_rows(a, run, 10)
    assert len(rows) == 12 and rows[8]["im Weg"] == "1" and rows[1]["im Weg"] == "2" and sum(r["im Weg"] != "–" for r in rows) == 2
    assert sum(r["untergebracht in"] == "–" for r in rows) == 2
    g = ev.round_groups(a, run, 10)
    assert [x[0] for x in g["groups"]] == ["Wald 1", "Wald 2"] and g["unassigned"] == [8, 9] and g["halo"] == [8, 1]


# --- Experimente ---------------------------------------------------------------------------------------------------------------------------


def test_trees_verdict_gives_the_failing_partition_and_catches_a_mismatch():
    s, a, run = _preset("Standardfall (Voreinstellung)")
    tv = ev.trees_view(s)
    kind, text = ev.verdict_trees(a, tv)
    assert kind == "info" and "höchstens **1 Spannbaum**" in text and "alle 876 Partitionen der 7 Standorte" in text
    assert "Partition mit 3 Klassen" in text and "nur **3** Leitungen" in text and "2 · (3 − 1) = **4**" in text
    assert ev.verdict_trees(a, {**tv, "alg": 2})[0] == "error"
    assert ev.verdict_trees(a, {**tv, "cert": {**tv["cert"], "violated": False}})[0] == "error"
    assert [r["alle Spannbäume"] for r in ev.trees_rows(tv)] == ["ja", "nein"]


def test_trees_verdict_for_two_trees_names_k_equals_three_as_the_failing_case():
    s, a, run = _preset("Zwei Spannbäume")
    kind, text = ev.verdict_trees(a, ev.trees_view(s))
    assert "höchstens **2 kantendisjunkte Spannbäume**" in text and "Für k = 3 scheitert es an einer Partition mit 6 Klassen" in text and "nur **10** Leitungen" in text and "3 · (6 − 1) = **15**" in text


def test_arboricity_verdict_gives_the_dense_node_set():
    s, a, run = _preset("Standardfall (Voreinstellung)")
    av = ev.arb_view(s)
    kind, text = ev.verdict_arb(a, av)
    assert kind == "info" and "auf **3** Wälder verteilen, auf weniger nicht" in text and "alle 120 Knotenmengen" in text
    assert "Auf 2 Wälder passt es nicht" in text and "mit 5 Standorten **9** Leitungen" in text and "in 2 Wälder passen dort höchstens 2 · (5 − 1) = **8**" in text
    assert ev.verdict_arb(a, {**av, "alg": 2})[0] == "error"
    assert ev.verdict_arb(a, {**av, "cert": {**av["cert"], "excess": 0}})[0] == "error"
    assert [r["alle Leitungen untergebracht"] for r in ev.arb_rows(a, av)] == ["nein", "nein", "ja"]


def test_arboricity_verdict_for_one_forest_and_for_a_tree():
    s = ev.Settings(0, 0, "k4")
    a = ev.analyse(replace(s, k=1))
    av = ev.arb_view(s)
    assert "Auf 1 Wald passt es nicht" in ev.verdict_arb(a, av)[1]


def test_mix_verdict_counts_forest_and_color_part_and_the_minimizers():
    s, a, run = _preset("Standardfall (Voreinstellung)")
    mv = ev.mix_view(s)
    kind, text = ev.verdict_mix(mv)
    assert kind == "success" and "kommen **11** in einen Wald (6) und eine Menge mit höchstens einer Leitung je Farbe (5); 1 bleibt übrig" in text
    assert "alle 4 096 Mengen Y" in text and "ist 11 und wird bei 4 Mengen angenommen" in text and "sein Y hat 10 Leitungen" in text
    assert ev.verdict_mix({**mv, "formula": {**mv["formula"], "value": 12}})[0] == "error"
    k4 = ev.mix_view(ev.Settings(**{**C.PRESETS["K4: zwei Bäume"], "task": "farben"}))
    assert "wird bei 1 Menge angenommen" in ev.verdict_mix(k4)[1] and "ist 6 und" in ev.verdict_mix(k4)[1]


def test_small_verdict_all_hold_and_a_deviation_is_an_error():
    rows, red = ev.small_rows(), ev.reduction_rows()
    kind, text = ev.verdict_small(rows, red)
    assert kind == "success" and "Bei allen 7 409 geprüften Paaren" in text and "bei allen 5 509 geprüften Paaren" in text and "**5,3-mal**" in text and "(**0 Abweichungen**)" in text
    broken = [dict(rows[0], formula=rows[0]["pairs"] - 1)] + list(rows[1:])
    assert ev.verdict_small(broken, red)[0] == "error" and "Bei 1 Prüfungen" in ev.verdict_small(broken, red)[1]
    assert ev.small_table(rows, red)[-1]["Reduktion = Rang"] == "600 von 600"


def test_series_verdict_and_table():
    rows = ev.plan_series()
    kind, text = ev.verdict_series(rows)
    assert kind == "info" and "50 %, 25 %, 5 %" in text
    assert [(r["Standorte"], r["Leitungen"], r["zwei Spannbäume"], r["Arboricity 2"], r["Arboricity 3"]) for r in ev.series_table(rows)] == [(6, 10, 10, 10, 10), (7, 12, 5, 5, 15), (8, 14, 1, 1, 19)]
    odd = [dict(rows[0], two_trees=3)] + list(rows[1:])
    assert ev.verdict_series(odd)[0] == "warning"


# --- Spielwiese ----------------------------------------------------------------------------------------------------------------------------


def test_play_verdict_all_branches():
    s, a, run = _preset("Standardfall (Voreinstellung)")
    assert ev.verdict_play(a, ev.play_view(s, 0)) == ("info", "Wählen Sie mindestens eine Leitung.")
    assert ev.verdict_play(a, ev.play_view(s, 1)) == ("success", "Die gewählte Leitung lässt sich auf 2 Wälder verteilen (Zerlegung im Bild).")
    assert ev.verdict_play(a, ev.play_view(s, 0b111))[1].startswith("Die 3 gewählten Leitungen lassen sich auf 2 Wälder verteilen")
    kind, text = ev.verdict_play(a, ev.play_view(s, (1 << a.m) - 1))
    assert kind == "warning" and "untergebracht: 11" in text and "Knotenmenge mit 5 Standorten hat 9 der gewählten Leitungen" in text and "in 2 Wälder passen dort aber höchstens 2 · (5 − 1) = 8" in text
    assert ev.verdict_play(a, {**ev.play_view(s, (1 << a.m) - 1), "dense": None})[0] == "error"
