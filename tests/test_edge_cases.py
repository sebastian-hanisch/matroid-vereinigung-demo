"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): kleinste Fälle, nicht zusammenhängende Graphen schon im Kern,
Schlingen, leere Auswahl, Reglergrenzen und jeder Zweig der Spielwiese."""

import numpy as np
import pytest

import mvg_algorithm as A
import mvg_constants as C
import mvg_evaluation as ev
from mvg_systems import forest_table


def test_two_nodes_one_edge_is_one_tree_and_arboricity_one():
    edges = [(0, 1)]
    table = A.graphic_table(2, edges)
    assert A.tutte_min(2, edges)["tau"] == 1 and A.nash_williams(2, edges)["arboricity"] == 1
    assert A.trees_by_algorithm(table, 1, 2) == 1 and A.arboricity_by_algorithm(table, 1) == 1


def test_disconnected_graph_has_no_spanning_tree():
    edges = [(0, 1), (2, 3)]
    table = A.graphic_table(4, edges)
    assert A.tutte_min(4, edges)["tau"] == 0 and A.trees_by_algorithm(table, 2, 4) == 0
    assert A.arboricity_by_algorithm(table, 2) == 1 == A.nash_williams(4, edges)["arboricity"]


def test_loop_never_fits_into_a_forest_and_the_algorithm_reports_it_as_unplaced():
    edges = [(0, 0), (0, 1)]                                    # Schlinge und Kante
    table = A.graphic_table(2, edges)
    run = A.partition_steps(2, [table, table])
    assert run["owner"][0] == -1 and run["owner"][1] in (0, 1) and run["reach"] == 1
    assert A.certificate_value([A.rank_table(table, 2)] * 2, 2, run["reach"]) == 1


def test_empty_ground_set():
    run = A.partition_steps(0, [np.array([True])])
    assert run["owner"] == () and run["reach"] == 0 and len(run["rounds"]) == 1 and run["rounds"][0]["path"] is None
    assert A.union_rank([np.array([0])], 0)["value"] == 0


def test_play_view_with_an_empty_selection_and_with_every_single_edge():
    s = ev.Settings()
    assert ev.play_view(s, 0)["placed"] == 0 and ev.play_view(s, 0)["complete"] and ev.play_view(s, 0)["dense"] is None
    for e in range(12):
        v = ev.play_view(s, 1 << e)
        assert v["complete"] and v["placed"] == 1 and v["owner"][e] in (0, 1)


def test_play_view_places_exactly_the_selected_edges_and_nothing_else():
    s = ev.Settings()
    mask = 0b101010101010
    v = ev.play_view(s, mask)
    assert v["total"] == 6 and 0 < v["placed"] <= 6
    assert all(v["owner"][e] == -1 for e in range(12) if not mask >> e & 1)                 # nicht gewählte Leitungen bleiben draußen
    assert all(mask >> e & 1 for e in range(12) if v["owner"][e] >= 0)


def test_play_view_with_k4_on_the_dense_subgraph_names_the_node_set_and_ignores_unselected_edges():
    s = ev.Settings(0, 0, "k4", "waelder", 1)
    v = ev.play_view(s, (1 << 6) - 1)                              # alle 6 Kanten in einen Wald: nur 3 passen
    assert not v["complete"] and v["placed"] == 3 and len(v["dense"]["nodes"]) == 4 and len(v["dense"]["edges"]) == 6


def test_every_regler_corner_gives_consistent_numbers():
    for n in (C.N_MIN, C.N_MAX):
        for k in (C.K_MIN, C.K_MAX):
            for task in C.TASKS:
                s = ev.Settings(n, 8, "plan", task, k, C.C_MAX)
                a = ev.analyse(s)
                assert a.size == a.formula == a.certificate <= a.m, (n, k, task)


def test_four_forests_on_k4_leave_nothing_over_and_have_no_certificate_set():
    s = ev.Settings(0, 0, "k4", "waelder", 4)
    a = ev.analyse(s)
    run = ev.run_view(s)
    assert a.complete and run["reach"] == 0 and a.spanning is False        # 6 Kanten verteilen sich auf 4 Wälder, keiner ist ein Spannbaum


def test_fixed_graphs_ignore_the_plan_settings():
    for graph in ("k4", "k5", "k6", "k33"):
        assert ev.net_of(ev.Settings(6, 1, graph)).edges == ev.net_of(ev.Settings(9, 999, graph)).edges
        assert np.array_equal(forest_table(graph, 6, 1), forest_table(graph, 9, 999))


def test_unknown_graph_is_an_error():
    with pytest.raises(ValueError):
        ev.net_of(ev.Settings(7, 8, "kreis"))


def test_color_rule_with_one_color_per_edge_is_free_and_with_one_color_overall_holds_one_edge():
    from mvg_systems import color_table, get_net
    net = get_net("k4", 0, 0)
    free = A.partition_table(6, list(range(6)))
    assert free.all()                                             # jede Kante eine eigene Farbe: alles erlaubt
    one = A.partition_table(6, [0] * 6)
    assert A.rank_table(one, 6)[63] == 1
    assert color_table(net, 5, 2).shape == (64,)


def test_reduction_row_and_small_row_are_deterministic():
    assert A.small_union_row(2, 100, 1) == A.small_union_row(2, 100, 1) and A.reduction_row(2, 100, 1) == A.reduction_row(2, 100, 1)
