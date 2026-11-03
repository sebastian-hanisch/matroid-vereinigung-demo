"""Eigenschaftstests (Schicht „Eigenschaften“): Invarianten auf Zufallsmatroiden mit festem Seed."""

import random

import numpy as np

import mvg_algorithm as A
from mvg_algorithm import partition_steps, rank_table

SEED = 20261112


def _random_matroid(rng, n):
    kind = rng.choice(["uniform", "partition", "graphic", "gf2"])
    if kind == "uniform":
        k = rng.randint(0, n)
        return np.array([bin(mask).count("1") <= k for mask in range(1 << n)])
    if kind == "partition":
        return A.partition_table(n, [rng.randint(0, 2) for _ in range(n)], {c: rng.randint(1, 2) for c in range(3)})
    if kind == "graphic":
        v = rng.randint(2, 5)
        return A.graphic_table(v, [(rng.randrange(v), rng.randrange(v)) for _ in range(n)])
    vec = [rng.getrandbits(3) for _ in range(n)]

    def indep(mask):
        basis = []
        for e in range(n):
            if mask >> e & 1:
                x = vec[e]
                for b in basis:
                    x = min(x, x ^ b)
                if not x:
                    return False
                basis.append(x)
        return True

    return np.array([indep(mask) for mask in range(1 << n)])


def _cases(count=50):
    rng = random.Random(SEED)
    out = []
    for _ in range(count):
        n = rng.randint(2, 6)
        k = rng.randint(1, 3)
        out.append((n, [_random_matroid(rng, n) for _ in range(k)]))
    return out


def test_verfahren_findet_den_rang_der_vereinigung_und_das_zertifikat_passt():
    for n, tables in _cases():
        ranks = [rank_table(t, n) for t in tables]
        run = partition_steps(n, tables)
        size = sum(1 for o in run["owner"] if o >= 0)
        assert size == A.union_rank(ranks, n)["value"] == int(rank_table(A.union_table(tables, n), n)[(1 << n) - 1])
        assert A.certificate_value(ranks, n, run["reach"]) == size


def test_die_zerlegung_besteht_aus_unabhaengigen_teilen_ohne_ueberschneidung():
    for n, tables in _cases():
        run = partition_steps(n, tables)
        for j, t in enumerate(tables):
            assert t[sum(1 << e for e in range(n) if run["owner"][e] == j)]


def test_jede_runde_bringt_genau_ein_element_mehr_unter_und_wege_wechseln_den_platz():
    for n, tables in _cases():
        run = partition_steps(n, tables)
        sizes = [r["size"] for r in run["rounds"]]
        assert sizes == list(range(len(sizes)))
        for r in run["rounds"][:-1]:
            assert r["owner"][r["path"][0]] == -1 and all(r["owner"][v] >= 0 for v in r["path"][1:])      # nur der erste ist noch nicht untergebracht


def test_die_vereinigung_ist_ein_matroid_und_der_rang_waechst_hoechstens_um_den_rang_des_summanden():
    for n, tables in _cases(25):
        union = A.System("u", n, A.union_table(tables, n).tolist())
        assert union.exchange_scan()[1] == 0
        base = A.union_table(tables[:-1], n) if len(tables) > 1 else None
        if base is not None:
            full = (1 << n) - 1
            assert 0 <= int(rank_table(A.union_table(tables, n), n)[full]) - int(rank_table(base, n)[full]) <= int(rank_table(tables[-1], n)[full])


def test_reihenfolge_der_matroide_und_umbenennen_aendern_den_rang_nicht():
    rng = random.Random(SEED + 1)
    for n, tables in _cases(25):
        size = sum(1 for o in partition_steps(n, tables)["owner"] if o >= 0)
        assert size == sum(1 for o in partition_steps(n, list(reversed(tables)))["owner"] if o >= 0)
        perm = list(range(n))
        rng.shuffle(perm)
        moved = []
        for t in tables:
            new = np.zeros(1 << n, dtype=bool)
            for mask in range(1 << n):
                new[sum(1 << perm[e] for e in range(n) if mask >> e & 1)] = t[mask]
            moved.append(new)
        assert size == sum(1 for o in partition_steps(n, moved)["owner"] if o >= 0)


def test_uniforme_matroide_addieren_ihre_raenge_bis_zur_grundmenge():
    n = 5
    for r1 in range(n + 1):
        for r2 in range(n + 1):
            t1 = np.array([bin(x).count("1") <= r1 for x in range(1 << n)])
            t2 = np.array([bin(x).count("1") <= r2 for x in range(1 << n)])
            assert sum(1 for o in partition_steps(n, [t1, t2])["owner"] if o >= 0) == min(n, r1 + r2)


def test_die_vereinigung_mit_einem_freien_matroid_ist_das_freie_matroid():
    for n, tables in _cases(20):
        free = np.ones(1 << n, dtype=bool)
        assert all(o >= 0 for o in partition_steps(n, tables + [free])["owner"])


def test_schwache_dualitaet_jede_zerlegbare_menge_ist_hoechstens_so_gross_wie_jede_schranke():
    for n, tables in _cases(25):
        ranks = [rank_table(t, n) for t in tables]
        union = A.union_table(tables, n)
        best = max(bin(x).count("1") for x in range(1 << n) if union[x])
        for y in range(1 << n):
            assert best <= (n - bin(y).count("1")) + sum(int(r[y]) for r in ranks)
