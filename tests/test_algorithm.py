"""Kern: Partitionsverfahren, Rangformel, Zertifikat, Tutte und Nash-Williams, Reduktion; jeweils an Handbeispielen (conftest.py)."""

import numpy as np
import pytest

import mvg_algorithm as A
from mvg_algorithm import partition_steps, rank_table


def _ranks(tables, m):
    return [rank_table(t, m) for t in tables]


def test_dreieck_zwei_waelder_bringen_alle_drei_kanten_unter(dreieck):
    n, edges, table = dreieck
    run = partition_steps(3, [table, table])
    assert sum(1 for o in run["owner"] if o >= 0) == 3 and run["reach"] == 0
    for j in (0, 1):
        assert table[sum(1 << e for e in range(3) if run["owner"][e] == j)]
    assert A.union_rank(_ranks([table, table], 3), 3)["value"] == 3


def test_dreieck_ein_wald_bringt_zwei_kanten_unter_und_das_zertifikat_stimmt(dreieck):
    n, edges, table = dreieck
    run = partition_steps(3, [table])
    assert sum(1 for o in run["owner"] if o >= 0) == 2
    assert run["reach"] == 0b111                       # von der letzten Kante aus sind alle drei erreichbar
    assert A.certificate_value(_ranks([table], 3), 3, run["reach"]) == 2     # |E ∖ R| = 0, r(R) = 2


def test_dreieck_tutte_und_nash_williams(dreieck):
    n, edges, table = dreieck
    t = A.tutte_min(n, edges)
    assert t["tau"] == 1 and t["classes"] == 3 and t["cross"] == 3        # drei Einzelklassen: 3 Kanten, gebraucht 2 · 2 = 4 für zwei Bäume
    nw = A.nash_williams(n, edges)
    assert nw["arboricity"] == 2 and nw["size"] == 3 and nw["inside"] == 3
    assert A.trees_by_algorithm(table, 3, n) == 1 and A.arboricity_by_algorithm(table, 3) == 2


def test_vierzyklus_mit_diagonale(vierzyklus_mit_diagonale):
    n, edges, table = vierzyklus_mit_diagonale
    assert A.tutte_min(n, edges)["tau"] == 1 and A.nash_williams(n, edges)["arboricity"] == 2
    assert A.trees_by_algorithm(table, 5, n) == 1 and A.arboricity_by_algorithm(table, 5) == 2
    run = partition_steps(5, [table, table])
    assert all(o >= 0 for o in run["owner"])


def test_farben_beispiel_wald_und_farbregel(farben_beispiel):
    n, edges, colors, forest, color = farben_beispiel
    run = partition_steps(3, [forest, color])
    assert sum(1 for o in run["owner"] if o >= 0) == 3
    wald = [e for e in range(3) if run["owner"][e] == 0]
    farbe = [e for e in range(3) if run["owner"][e] == 1]
    assert forest[sum(1 << e for e in wald)] and color[sum(1 << e for e in farbe)]
    assert len({colors[e] for e in farbe}) == len(farbe)       # lauter verschiedene Farben


def test_ein_element_ohne_matroid_das_es_aufnimmt_hat_zertifikat_mit_menge_r():
    zero = np.array([True, False])                             # Nullmatroid: das einzige Element ist eine Schlinge
    run = partition_steps(1, [zero])
    assert run["owner"] == (-1,) and run["reach"] == 1
    assert A.certificate_value([rank_table(zero, 1)], 1, run["reach"]) == 0


def test_runden_zaehlen_die_untergebrachten_elemente_hoch(dreieck):
    n, edges, table = dreieck
    run = partition_steps(3, [table, table])
    assert [r["size"] for r in run["rounds"]] == [0, 1, 2, 3]
    assert run["rounds"][-1]["path"] is None and all(r["path"] for r in run["rounds"][:-1])


def test_allowed_blendet_elemente_aus(dreieck):
    n, edges, table = dreieck
    run = partition_steps(3, [table], allowed=0b011)          # nur a und b: ein Pfad, passt in einen Wald
    assert run["owner"][2] == -1 and run["owner"][0] == 0 and run["owner"][1] == 0
    assert partition_steps(3, [table], allowed=0)["rounds"][0]["path"] is None


def test_components_und_set_partitions():
    assert A.components(5, [(0, 1), (3, 4)]) == [0, 0, 1, 2, 2]
    assert sum(1 for _ in A.set_partitions(5)) == 52 and sum(1 for _ in A.set_partitions(9)) == 21147   # Bellsche Zahlen


def test_union_table_von_zwei_freien_matroiden_mit_rang_1_hat_rang_2():
    n = 4
    ok = np.array([bin(x).count("1") <= 1 for x in range(1 << n)])
    table = A.union_table([ok, ok], n)
    assert A.rank_table(table, n)[(1 << n) - 1] == 2 and table.sum() == 1 + 4 + 6


def test_reduktion_auf_den_schnitt_liefert_denselben_rang_wie_das_direkte_verfahren():
    row = A.reduction_row(3, 50, 1)           # bis 4 Elemente werden alle Paare geprüft, die Stichprobe gilt erst ab 5
    assert row["agree"] == row["pairs"] == 256 and row["calls_reduction"] > row["calls_direct"]
    assert A.reduction_row(5, 7, 1)["pairs"] == 7


def test_die_kleinen_paare_bis_3_elemente_erfuellen_alle_vier_aussagen():
    for n in (1, 2, 3):
        row = A.small_union_row(n, 100, 1)
        assert row["formula"] == row["matroid"] == row["alg"] == row["cert"] == row["pairs"], row
