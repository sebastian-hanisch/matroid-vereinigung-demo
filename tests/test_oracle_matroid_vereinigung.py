"""Orakel (anderer Rechenweg als die Demo): Wälder mit `networkx.is_forest` und Aufzählung, Spannbäume durch Aufzählung disjunkter Bäume,
Überdeckung durch Verzweigen über Wälder, Wald ∨ Farbregel durch „bester Wald plus Zahl der übrigen Farben“. Die Demo rechnet dagegen mit dem Partitionsverfahren
und mit Formeln über alle Partitionen beziehungsweise Knotenmengen."""

from functools import lru_cache

import pytest

import mvg_algorithm as A
import mvg_evaluation as ev
from mvg_systems import edge_colors, get_net

nx = pytest.importorskip("networkx")


def _forest_masks(n, edges):
    """Alle Kantenmengen, die ein Wald sind (networkx)."""
    m = len(edges)
    out = []
    for mask in range(1 << m):
        g = nx.Graph()
        g.add_nodes_from(range(n))
        g.add_edges_from(edges[e] for e in range(m) if mask >> e & 1)
        if nx.is_forest(g):
            out.append(mask)
    return out


def _bf_trees(n, edges):
    """Größte Zahl paarweise kantendisjunkter Spannbäume: Bäume = Wälder mit n − 1 Kanten (dann zusammenhängend), dann Suche nach disjunkten."""
    trees = [mask for mask in _forest_masks(n, edges) if bin(mask).count("1") == n - 1]

    def best(available, start):
        top = 0
        for i in range(start, len(trees)):
            if trees[i] & ~available == 0:
                top = max(top, 1 + best(available & ~trees[i], i + 1))
        return top

    return best((1 << len(edges)) - 1, 0)


def _bf_arboricity(n, edges):
    forests = _forest_masks(n, edges)
    m = len(edges)

    @lru_cache(maxsize=None)
    def covers(mask, k):
        if mask == 0:
            return True
        if k == 0:
            return False
        low = mask & -mask
        return any(f & low and f & ~mask == 0 and covers(mask & ~f, k - 1) for f in forests)

    k = 1
    while not covers((1 << m) - 1, k):
        k += 1
    return k


def _bf_union_max(n, edges, k):
    """Größte Menge, die sich in k Wälder zerlegen lässt (Verzweigen über Wälder, die die kleinste ungenutzte Kante enthalten oder weglassen)."""
    forests = _forest_masks(n, edges)
    m = len(edges)

    @lru_cache(maxsize=None)
    def best(mask, k):
        if mask == 0 or k == 0:
            return 0
        top = 0
        for f in forests:
            if f & ~mask == 0 and f:
                top = max(top, bin(f).count("1") + best(mask & ~f, k - 1))
        return top

    return best((1 << m) - 1, k)


def _graphs():
    cases = [("k4", 0, 0), ("k5", 0, 0), ("k33", 0, 0)]
    cases += [("plan", 6, s) for s in range(6)] + [("plan", 7, s) for s in range(3)]
    for graph, n, seed in cases:
        net = get_net(graph, n, seed)
        yield graph, n, seed, net.n, list(net.edges)


def test_zahl_der_kantendisjunkten_spannbaeume_und_arboricity_gegen_aufzaehlung():
    for graph, n, seed, nodes, edges in _graphs():
        tv = ev.trees_view(ev.Settings(n, seed, graph))
        av = ev.arb_view(ev.Settings(n, seed, graph))
        assert tv["alg"] == tv["tutte"]["tau"] == _bf_trees(nodes, edges), (graph, n, seed)
        assert av["alg"] == av["nw"]["arboricity"] == _bf_arboricity(nodes, edges), (graph, n, seed)


def test_groesste_zerlegbare_menge_gegen_aufzaehlung_fuer_k_1_bis_3():
    for graph, n, seed, nodes, edges in _graphs():
        if len(edges) > 10:
            continue
        for k in (1, 2, 3):
            run = ev.run_view(ev.Settings(n, seed, graph, "waelder", k))
            size = sum(1 for o in run["owner"] if o >= 0)
            assert size == _bf_union_max(nodes, edges, k), (graph, n, seed, k)


def test_wald_und_farbregel_gegen_besten_wald_plus_zahl_der_uebrigen_farben():
    """Eine Menge ist in Wald ∨ Farbregel genau dann unabhängig, wenn sie in einen Wald A und eine Menge mit lauter verschiedenen Farben zerfällt: größte Größe = max über Wälder A von |A| + Zahl der Farben der übrigen Kanten."""
    for graph, n, seed, nodes, edges in _graphs():
        if len(edges) > 12:
            continue
        forests = _forest_masks(nodes, edges)
        net = get_net(graph, n, seed)
        for c in (2, 4, 6):
            colors = edge_colors(net, seed, c)
            best = max(bin(f).count("1") + len({colors[e] for e in range(len(edges)) if not f >> e & 1}) for f in forests)
            a = ev.analyse(ev.Settings(n, seed, graph, "farben", 2, c))
            assert a.size == a.formula == best, (graph, n, seed, c)


def test_cayley_gegenprobe_fuer_die_zahl_der_spannbaeume_des_k5():
    """K5 hat 125 Spannbäume (Cayley, n^(n−2)); zwei kantendisjunkte passen in die 10 Kanten (2 · 4 = 8 ≤ 10), drei nicht (12 > 10)."""
    edges = list(get_net("k5", 0, 0).edges)
    trees = [mask for mask in _forest_masks(5, edges) if bin(mask).count("1") == 4]
    assert len(trees) == 125
    assert _bf_trees(5, edges) == 2


def test_bekannte_werte_fuer_vollstaendige_und_bipartite_graphen():
    """K_n: ⌊n/2⌋ kantendisjunkte Spannbäume und Arboricity ⌈n/2⌉ (Nash-Williams); K3,3: 1 und 2."""
    known = {"k4": (2, 2), "k5": (2, 3), "k6": (3, 3), "k33": (1, 2)}
    for graph, (trees, arb) in known.items():
        tv, av = ev.trees_view(ev.Settings(0, 0, graph)), ev.arb_view(ev.Settings(0, 0, graph))
        assert (tv["alg"], av["alg"]) == (trees, arb), graph
    assert nx.is_forest(nx.path_graph(4)) and not nx.is_forest(nx.cycle_graph(4))     # das Orakel selbst an Handbeispielen
    assert A.tutte_min(4, list(get_net("k4", 0, 0).edges))["tau"] == 2
