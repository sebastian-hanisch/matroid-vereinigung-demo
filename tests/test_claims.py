"""Jede Zahl der README („Befunde“) wird hier mit den Funktionen der App nachgerechnet (DEMO-PLAYBOOK §4)."""

from pathlib import Path

import pytest

import mvg_algorithm as A
import mvg_constants as C
import mvg_evaluation as ev
from mvg_systems import get_net

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")

EXAMPLES = {   # Name in der README -> (Preset, Leitungen, untergebracht, Orakelaufrufe, Spannbäume, Arboricity); None = steht als „–“ in der README
    "Plan 7/8, zwei Wälder": ("Standardfall (Voreinstellung)", 12, 11, 105, 1, 3),
    "Plan 6/3 („Zwei Spannbäume“), zwei Wälder": ("Zwei Spannbäume", 10, 10, 35, 2, 2),
    "K4, zwei Wälder": ("K4: zwei Bäume", 6, 6, 15, 2, 2),
    "K5, drei Wälder": ("K5: drei Wälder", 10, 10, 29, 2, 3),
    "Plan 7/8, Wald ∨ Farbregel mit 4 Farben": ("Wald und Farbregel", 12, 10, 116, None, None),
}


def test_the_example_table():
    for name, (preset, m, size, calls, trees, arb) in EXAMPLES.items():
        s = ev.Settings(**C.PRESETS[preset])
        a = ev.analyse(s)
        assert (a.m, a.size, ev.run_view(s)["calls"]) == (m, size, calls), name
        gs = ev.Settings(s.n, s.seed, s.graph)
        if trees is not None:
            assert (ev.trees_view(gs)["alg"], ev.arb_view(gs)["alg"]) == (trees, arb), name
        assert a.size == a.formula == a.certificate, name
        cells = f"| {name} | {m} | {size} | {calls} | {trees if trees is not None else '–'} | {arb if arb is not None else '–'} |"
        assert cells in README, name


def test_fixed_graphs():
    expected = {"k4": (2, 2), "k5": (2, 3), "k6": (3, 3), "k33": (1, 2)}
    for graph, (trees, arb) in expected.items():
        s = ev.Settings(0, 0, graph)
        assert (ev.trees_view(s)["alg"], ev.arb_view(s)["alg"]) == (trees, arb), graph
    assert "K4: 2 / 2; K5: 2 / 3; K6: 3 / 3; K3,3: 1 / 2" in README


def test_certificate_numbers_on_the_plan_and_on_k5():
    s = ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"])
    cert = ev.trees_view(s)["cert"]
    assert (cert["k"], cert["classes"], cert["cross"]) == (2, 3, 3) and cert["k"] * (cert["classes"] - 1) == 4
    dense = ev.arb_view(s)["cert"]
    assert (dense["k"], len(dense["nodes"]), len(dense["edges"])) == (2, 5, 9) and dense["k"] * (len(dense["nodes"]) - 1) == 8
    for fact in ("Es gibt nur **1** Spannbaum", "Partition mit **3** Klassen", "nur **3** Leitungen", "wären **4** nötig", "Die Arboricity ist **3**", "mit **5** Standorten hat **9** Leitungen", "höchstens **8** auf"):
        assert fact in README, fact
    k5 = ev.trees_view(ev.Settings(**C.PRESETS["K5: drei Wälder"]))["cert"]
    assert (k5["k"], k5["classes"], k5["cross"]) == (3, 5, 10) and k5["k"] * (k5["classes"] - 1) == 12
    assert "5 Einzelklassen: **10** Leitungen dazwischen, gebraucht **12**" in README


def test_wald_und_farbregel():
    default = ev.mix_view(ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]))
    assert (default["a"].size, sum(1 for o in default["owner"] if o == 0), sum(1 for o in default["owner"] if o == 1), default["formula"]["count"], 2 ** default["a"].m) == (11, 6, 5, 4, 4096)
    four = ev.mix_view(ev.Settings(**C.PRESETS["Wald und Farbregel"]))
    assert (four["a"].size, sum(1 for o in four["owner"] if o == 0), sum(1 for o in four["owner"] if o == 1), four["formula"]["count"]) == (10, 6, 4, 2)
    assert "**11** von 12 Leitungen (6 im Wald, 5 in der Farbregel), das Minimum über alle 4 096 Mengen Y wird bei **4** Mengen angenommen; mit 4 Farben: **10** (6 + 4), bei **2** Mengen" in README


def test_all_small_pairs_and_the_reduction():
    rows, red = ev.small_rows(), ev.reduction_rows()
    assert [r["pairs"] for r in rows] == [4, 25, 256, 4624, 2500] and sum(r["pairs"] for r in rows) == 7409
    assert all(r["formula"] == r["matroid"] == r["alg"] == r["cert"] == r["pairs"] for r in rows)
    assert [q["pairs"] for q in red] == [4, 25, 256, 4624, 600] and sum(q["pairs"] for q in red) == 5509 and all(q["agree"] == q["pairs"] for q in red)
    per_pair = [(ev.de(q["calls_direct"] / q["pairs"]), ev.de(q["calls_reduction"] / q["pairs"])) for q in red]
    assert per_pair == [("1,5", "4,2"), ("3,7", "12,7"), ("6,7", "26,5"), ("10,3", "47,4"), ("14,4", "76,4")]
    assert ev.de(red[-1]["calls_reduction"] / red[-1]["calls_direct"]) == "5,3"
    for text in ("zusammen **7 409**", "bei **allen 7 409**", "zusammen **5 509**", "bei **allen 5 509**", "1 Element: 1,5 / 4,2; 2: 3,7 / 12,7; 3: 6,7 / 26,5; 4: 10,3 / 47,4; 5: 14,4 / 76,4", "**5,3-Fache**"):
        assert text in README, text
    assert "4, 25, 256, 4 624 und 2 500 bei 5 Elementen" in README and "4, 25, 256, 4 624 und 600 Paare" in README


def test_the_series():
    rows = ev.plan_series()
    assert [(r["n"], r["two_trees"], r["arb2"], r["arb3"]) for r in rows] == [(6, 10, 10, 10), (7, 5, 5, 15), (8, 1, 1, 19)]
    assert [ev.de(r["calls"], 0) for r in rows] == ["43", "72", "109"]
    assert "bei 6 Standorten **10**, bei 7 **5**, bei 8 **1** der 20 Pläne" in README and "Orakelaufrufe im Mittel: 43, 72, 109" in README


def test_the_triangle_by_hand(dreieck):
    n, edges, table = dreieck
    assert A.rank_table(table, 3)[7] == 2
    assert sum(1 for o in A.partition_steps(3, [table, table])["owner"] if o >= 0) == 3
    assert A.tutte_min(n, edges)["tau"] == 1 and A.nash_williams(n, edges)["arboricity"] == 2
    assert "Ein Wald nimmt 2 der 3 Kanten auf, zwei Wälder alle 3 (Arboricity 2); zwei Spannbäume bräuchten 4 Kanten, es gibt nur 3 (1 Spannbaum)" in README


def test_the_two_trees_seed_is_the_first_plan_with_six_standorte_and_two_spanning_trees():
    assert C.TWO_TREE_SEED == 3
    trees = [ev.trees_view(ev.Settings(6, seed))["alg"] for seed in range(4)]
    assert trees == [1, 1, 1, 2]


def test_plan_sizes_in_the_readme():
    assert [len(get_net("plan", n, 8).edges) for n in (6, 7, 8, 9)] == [10, 12, 14, 16]
    assert ev.bell(9) == 21147 and "(bei 9 Standorten 21 147)" in README
    assert "Höchstens 16 Leitungen" in README


@pytest.mark.parametrize("graph, edges", [("k4", 6), ("k5", 10), ("k6", 15), ("k33", 9)])
def test_fixed_graph_edge_counts(graph, edges):
    assert len(get_net(graph, 0, 0).edges) == edges
