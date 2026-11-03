"""Kern der Demo: Vereinigung und Partition von Matroiden auf höchstens 16 Elementen (Bitmasken): k disjunkte unabhängige Mengen, Partitionsverfahren, Rangformel, kantendisjunkte Spannbäume und Arboricity.

Vereinigung M1 ∨ … ∨ Mk: unabhängig ist, was sich in I1 ∪ … ∪ Ik mit Ij unabhängig in Mj zerlegen lässt. Rang: r(X) = min über Y ⊆ X von |X ∖ Y| + Σ rj(Y).
Graphen: k kantendisjunkte Spannbäume genau dann, wenn jede Partition P der Knoten mindestens k (|P| − 1) Kanten zwischen den Klassen hat (Tutte, Nash-Williams); alle Kanten auf k Wälder genau dann,
wenn jede Knotenmenge U höchstens k (|U| − 1) Kanten in sich hat (Nash-Williams). Reduktion auf den Schnitt (k = 2): Grundmenge E × {1, 2}.

Unten die Grundlagen aus Stück 7 (Tabellen, Paar, Austauschgraph, Schnittverfahren, alle kleinen Matroide)."""

import itertools
from dataclasses import dataclass, field
from functools import cached_property

import numpy as np


def popcount(x: int) -> int:
    return bin(x).count("1")


def elements(mask: int, m: int) -> list[int]:
    return [e for e in range(m) if mask >> e & 1]


class System:
    """Unabhängigkeitssystem auf m Elementen; ok[mask] sagt, ob die Menge `mask` zulässig ist."""

    def __init__(self, name: str, m: int, ok):
        if not 1 <= m <= 16:
            raise ValueError(f"m = {m} außerhalb von 1 bis 16")
        if len(ok) != 1 << m or not ok[0]:
            raise ValueError("ok braucht 2**m Einträge, und die leere Menge muss zulässig sein")
        self.name, self.m, self.ok = name, m, list(ok)
        self.full = (1 << m) - 1
        self.ind = [mask for mask in range(1 << m) if self.ok[mask]]
        self.ind_array = np.array(self.ind, dtype=np.int64)
        self.sizes = np.array([popcount(i) for i in self.ind], dtype=np.int64)
        self._ranks()

    # --- Grundbegriffe ------------------------------------------------------------------------------------------------------------------

    def check_down_closed(self) -> bool:
        """Mit jeder zulässigen Menge sind alle Mengen ohne ein Element zulässig (genügt für alle Teilmengen)."""
        return all(self.ok[mask & ~(1 << e)] for mask in self.ind for e in range(self.m) if mask >> e & 1)

    def can_add(self, mask: int, e: int) -> bool:
        return not mask >> e & 1 and self.ok[mask | 1 << e]

    def addable(self, mask: int) -> int:
        """Maske aller Elemente, die zu `mask` passen."""
        out = 0
        for e in range(self.m):
            if self.can_add(mask, e):
                out |= 1 << e
        return out

    def is_maximal(self, mask: int) -> bool:
        return self.ok[mask] and self.addable(mask) == 0

    def _ranks(self):
        m, ok = self.m, self.ok
        ur = [0] * (1 << m)
        for mask in range(1, 1 << m):
            ur[mask] = popcount(mask) if ok[mask] else max(ur[mask & ~(1 << e)] for e in range(m) if mask >> e & 1)
        self.ur = ur
        lr = [0] * (1 << m)
        for i in sorted(self.ind, key=popcount):
            free = self.full & ~i & ~self.addable(i)
            s = free
            while True:
                f = i | s
                if f and lr[f] == 0:
                    lr[f] = popcount(i)
                if s == 0:
                    break
                s = (s - 1) & free
        self.lr = lr
        best = None
        for f in range(1, 1 << m):
            if ur[f] > 0:
                q = lr[f] / ur[f]
                if best is None or q < best[0] - 1e-15:
                    best = (q, f)
        self.q = best[0] if best else 1.0

    # --- Rang, Basen, Kreise, Abschluss, Flache -------------------------------------------------------------------------------------------

    @property
    def rank(self) -> int:
        """Rang der ganzen Grundmenge: Größe der größten zulässigen Menge."""
        return self.ur[self.full]

    def rank_of(self, f: int) -> int:
        return self.ur[f]

    @cached_property
    def bases(self) -> list[int]:
        """Maximale zulässige Mengen (bei einem Matroid alle gleich groß)."""
        return [i for i in self.ind if self.is_maximal(i)]

    @cached_property
    def circuits(self) -> list[int]:
        """Minimale unzulässige Mengen."""
        out = []
        for c in range(1, 1 << self.m):
            if not self.ok[c] and all(self.ok[c & ~(1 << e)] for e in range(self.m) if c >> e & 1):
                out.append(c)
        return out

    def closure(self, f: int) -> int:
        """cl(F) = F plus alle e, deren Hinzunahme den Rang nicht erhöht."""
        r = self.ur[f]
        out = f
        for e in range(self.m):
            if not f >> e & 1 and self.ur[f | 1 << e] == r:
                out |= 1 << e
        return out

    @cached_property
    def closures(self) -> list[int]:
        return [self.closure(f) for f in range(1 << self.m)]

    @cached_property
    def flats(self) -> list[int]:
        return [f for f in range(1 << self.m) if self.closures[f] == f]

    def flats_by_rank(self) -> dict[int, int]:
        out: dict[int, int] = {}
        for f in self.flats:
            out[self.ur[f]] = out.get(self.ur[f], 0) + 1
        return dict(sorted(out.items()))

    def circuits_in(self, mask: int) -> list[int]:
        """Alle Kreise, die in `mask` enthalten sind."""
        return [c for c in self.circuits if c & ~mask == 0]

    def fundamental_circuit(self, base: int, e: int):
        """Der Kreis in B + e, wenn es genau einen gibt (bei einem Matroid immer), sonst None."""
        inside = self.circuits_in(base | 1 << e)
        return inside[0] if len(inside) == 1 else None

    def swap_is_basis(self, base: int, f: int, e: int) -> bool:
        """Ist B − f + e wieder eine Basis (maximale zulässige Menge)?"""
        new = (base & ~(1 << f)) | 1 << e
        return self.is_maximal(new)

    def maximal_sizes(self) -> dict[int, int]:
        sizes: dict[int, int] = {}
        for i in self.bases:
            sizes[popcount(i)] = sizes.get(popcount(i), 0) + 1
        return dict(sorted(sizes.items()))

    # --- Austauschprobe (Stück 3) -------------------------------------------------------------------------------------------------------

    def exchange_scan(self, weak: bool = False) -> tuple[int, int]:
        """(Zahl der Paare (I1, I2) mit |I1| < |I2|, Zahl der Paare ohne Austauschpartner); je I1 ein Maskenvergleich über alle I2."""
        pairs = viol = 0
        for i1, s1 in zip(self.ind, self.sizes):
            bigger = self.sizes == s1 + 1 if weak else self.sizes > s1
            count = int(bigger.sum())
            if not count:
                continue
            pairs += count
            viol += int(((self.ind_array[bigger] & ~i1 & self.addable(i1)) == 0).sum())
        return pairs, viol

    @cached_property
    def is_matroid(self) -> bool:
        return self.exchange_scan()[1] == 0


# --- Tabellen: Rang, Partitionsmatroid, graphisches Matroid ----------------------------------------------------------------------------------


_PC = None


def pc_table() -> np.ndarray:
    """Elementzahl aller Masken bis 2^16."""
    global _PC
    if _PC is None:
        _PC = np.array([bin(i).count("1") for i in range(1 << 16)], dtype=np.int16)
    return _PC


def rank_table(ok: np.ndarray, m: int) -> np.ndarray:
    """Rang jeder Teilmenge: Größe der größten unabhängigen Teilmenge (Schichten nach Elementzahl, mit numpy)."""
    pc = pc_table()[: 1 << m]
    ur = np.zeros(1 << m, dtype=np.int16)
    idx = np.arange(1 << m)
    for k in range(1, m + 1):
        layer = idx[pc == k]
        best = np.zeros(len(layer), dtype=np.int16)
        for e in range(m):
            has = (layer >> e & 1) == 1
            sub = ur[layer[has] & ~(1 << e)]
            best[has] = np.maximum(best[has], sub)
        ur[layer] = np.where(ok[layer], k, best)
    return ur


def partition_table(m: int, classes, caps=None) -> np.ndarray:
    """Partitionsmatroid: je Klasse höchstens caps[klasse] Elemente (Standard 1)."""
    caps = caps or {}
    pc = pc_table()[: 1 << m]
    idx = np.arange(1 << m)
    ok = np.ones(1 << m, dtype=bool)
    for cls in set(classes):
        mask = sum(1 << e for e in range(m) if classes[e] == cls)
        ok &= pc[idx & mask] <= caps.get(cls, 1)
    return ok


def graphic_table(v: int, edges) -> np.ndarray:
    """Graphisches Matroid der Kantenliste auf v Knoten (Schleifen sind nie unabhängig)."""
    m = len(edges)
    ok = np.zeros(1 << m, dtype=bool)
    for mask in range(1 << m):
        parent = list(range(v))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        good = True
        for e in range(m):
            if mask >> e & 1:
                a, b = find(edges[e][0]), find(edges[e][1])
                if a == b:
                    good = False
                    break
                parent[a] = b
        ok[mask] = good
    return ok


@dataclass
class Pair:
    """Zwei Matroide auf derselben Grundmenge mit m Elementen (ok1[mask], ok2[mask]: ist die Menge in M1 bzw. M2 unabhängig?)."""
    key: str
    m: int
    ok1: np.ndarray
    ok2: np.ndarray
    labels: tuple
    kind: str                       # "kanten" (Leitungen des Plans) oder "boegen" (festes Beispiel)
    inst: object = None
    colors: tuple = ()
    extra: dict = field(default_factory=dict)

    @cached_property
    def common(self) -> np.ndarray:
        return self.ok1 & self.ok2

    @cached_property
    def full(self) -> int:
        return (1 << self.m) - 1

    @cached_property
    def ur1(self) -> np.ndarray:
        return rank_table(self.ok1, self.m)

    @cached_property
    def ur2(self) -> np.ndarray:
        return rank_table(self.ok2, self.m)

    @cached_property
    def opt(self) -> int:
        return int(pc_table()[np.nonzero(self.common)[0]].max())

    @cached_property
    def opt_set(self) -> int:
        """Die erste gemeinsame Menge (nach Maske) mit der Größe des Optimums."""
        idx = np.nonzero(self.common)[0]
        return int(idx[pc_table()[idx] == self.opt][0])

    @cached_property
    def maximal(self) -> np.ndarray:
        """Alle maximalen gemeinsamen Mengen (kein Element passt in beiden Matroiden dazu), als Masken."""
        idx = np.arange(1 << self.m)
        maximal = self.common.copy()
        for e in range(self.m):
            bit = 1 << e
            has = (idx & bit) == 0
            grow = np.zeros(1 << self.m, dtype=bool)
            grow[has] = self.common[idx[has] | bit]
            maximal &= ~grow
        return np.nonzero(maximal)[0]

    @cached_property
    def worst_set(self) -> int:
        """Die erste maximale gemeinsame Menge (nach Maske) mit den wenigsten Elementen."""
        sizes = pc_table()[self.maximal]
        return int(self.maximal[int(sizes.argmin())])

    @cached_property
    def n_common(self) -> int:
        return int(self.common.sum())


# --- Greedy ------------------------------------------------------------------------------------------------------------------------------


def greedy_common(pair: Pair, order) -> int:
    """Elemente in der Reihenfolge `order` hinzufügen, solange die Menge in beiden Matroiden unabhängig bleibt."""
    cur = 0
    for e in order:
        if pair.common[cur | 1 << e]:
            cur |= 1 << e
    return cur


def random_greedy(pair: Pair, trials: int, seed: int) -> dict:
    """Greedy bei zufälligen Reihenfolgen: Größen der gefundenen Mengen gegen das Optimum."""
    rng = np.random.default_rng(seed)
    sizes = []
    for _ in range(trials):
        sizes.append(popcount(greedy_common(pair, [int(x) for x in rng.permutation(pair.m)])))
    return {"trials": trials, "sizes": sizes}


def maximal_sizes(pair: Pair) -> dict[int, int]:
    sizes = pc_table()[pair.maximal]
    return {int(k): int((sizes == k).sum()) for k in sorted(set(sizes.tolist()))}


# --- Austauschgraph und Verfahren ----------------------------------------------------------------------------------------------------


def exchange_graph(pair: Pair, cur: int) -> dict:
    """Der vollständige Austauschgraph zu I = cur: Quellen, Senken, Pfeile (von, nach, welches Matroid)."""
    m = pair.m
    out = [e for e in range(m) if not cur >> e & 1]
    inn = [e for e in range(m) if cur >> e & 1]
    x1 = [x for x in out if pair.ok1[cur | 1 << x]]
    x2 = [x for x in out if pair.ok2[cur | 1 << x]]
    arcs = []
    for y in inn:
        for x in out:
            swap = (cur & ~(1 << y)) | 1 << x
            if pair.ok1[swap]:
                arcs.append((y, x, 1))
            if pair.ok2[swap]:
                arcs.append((x, y, 2))
    return {"out": out, "inn": inn, "x1": x1, "x2": x2, "arcs": arcs}


def bfs_path(sources, is_sink, neighbors):
    """Kürzester Weg von einer Quelle zu einer Senke; (Weg oder None, besuchte Menge)."""
    parent = {s: None for s in sources}
    queue = list(sources)
    head = 0
    while head < len(queue):
        v = queue[head]
        head += 1
        if is_sink(v):
            path = []
            while v is not None:
                path.append(v)
                v = parent[v]
            return path[::-1], set(parent)
        for w in neighbors(v):
            if w not in parent:
                parent[w] = v
                queue.append(w)
    return None, set(parent)


def greedy_start(pair: Pair) -> int:
    return greedy_common(pair, range(pair.m))


START_NAMES = {"leer": "leere Menge", "greedy": "Greedy nach Nummer", "schlecht": "schlechteste maximale Menge"}


def steps(pair: Pair, start: str = "leer") -> list[dict]:
    """Der Lauf Runde für Runde mit dem vollständigen Austauschgraphen: je Runde die Menge I, Quellen, Senken, Pfeile und der kürzeste Weg (am Ende: keiner, dafür die erreichbare Menge R).
    start: "leer" (I = ∅), "greedy" (Greedy in der Reihenfolge der Nummern) oder "schlecht" (die kleinste maximale gemeinsame Menge, der schlechteste Fall für Greedy)."""
    cur = {"leer": 0, "greedy": greedy_start(pair), "schlecht": pair.worst_set}[start]
    rounds = []
    while True:
        g = exchange_graph(pair, cur)
        adj: dict[int, list[int]] = {v: [] for v in range(pair.m)}
        for a, b, _ in g["arcs"]:
            adj[a].append(b)
        sinks = set(g["x2"])
        path, seen = bfs_path(g["x1"], lambda v: v in sinks, lambda v: adj[v])
        rounds.append({"set": cur, **g, "path": path, "reach": sum(1 << v for v in seen) if path is None else None})
        if path is None:
            return rounds
        for v in path:
            cur ^= 1 << v


class Oracle:
    """Zählt jede Frage „ist die Menge unabhängig?“."""

    def __init__(self, ok):
        self.ok, self.calls = ok, 0

    def __call__(self, mask):
        self.calls += 1
        return self.ok[mask]


VARIANTS = ("naiv", "faul", "faul+greedy")


def intersect(pair: Pair, variant: str) -> dict:
    """Drei Varianten des Verfahrens, mit gezählten Orakelaufrufen. naiv: ganzer Austauschgraph je Runde; faul: Pfeile erst beim Besuch; faul+greedy: dazu Start mit Greedy."""
    m = pair.m
    o1, o2 = Oracle(pair.ok1.tolist()), Oracle(pair.ok2.tolist())
    cur = 0
    start = 0
    if variant == "faul+greedy":
        for e in range(m):
            if o1(cur | 1 << e) and o2(cur | 1 << e):
                cur |= 1 << e
        start = popcount(cur)
    lengths = []
    while True:
        out = [e for e in range(m) if not cur >> e & 1]
        inn = [e for e in range(m) if cur >> e & 1]
        x1 = [x for x in out if o1(cur | 1 << x)]
        if variant == "naiv":
            x2 = {x for x in out if o2(cur | 1 << x)}
            adj: dict[int, list[int]] = {v: [] for v in range(m)}
            for y in inn:
                for x in out:
                    swap = (cur & ~(1 << y)) | 1 << x
                    if o1(swap):
                        adj[y].append(x)
                    if o2(swap):
                        adj[x].append(y)
            path, seen = bfs_path(x1, lambda v: v in x2, lambda v: adj[v])
        else:
            def is_sink(v):
                return not cur >> v & 1 and o2(cur | 1 << v)

            def neighbors(v):
                if cur >> v & 1:
                    return [x for x in out if o1((cur & ~(1 << v)) | 1 << x)]
                return [y for y in inn if o2((cur & ~(1 << y)) | 1 << v)]

            path, seen = bfs_path(x1, is_sink, neighbors)
        if path is None:
            return {"set": cur, "calls": o1.calls + o2.calls, "rounds": len(lengths), "lengths": lengths, "reach": sum(1 << v for v in seen), "start": start}
        for v in path:
            cur ^= 1 << v
        lengths.append(len(path))


def certificate(pair: Pair, reach: int) -> tuple[int, int, int]:
    """(r1(E ∖ R), r2(R), Summe) zur erreichbaren Menge R am Ende des Verfahrens."""
    a, b = int(pair.ur1[pair.full ^ reach]), int(pair.ur2[reach])
    return a, b, a + b


def min_max(pair: Pair) -> dict:
    """Minimum über alle A von r1(A) + r2(E ∖ A) und die Menge der Minimierer (Masken, nach Größe und Maske geordnet)."""
    idx = np.arange(1 << pair.m)
    total = pair.ur1[idx] + pair.ur2[pair.full ^ idx]
    value = int(total.min())
    mins = np.nonzero(total == value)[0]
    order = sorted(mins.tolist(), key=lambda x: (popcount(x), x))
    return {"value": value, "count": len(order), "first": order[:8]}


def intersection_is_matroid(pair: Pair, limit: int = 12):
    """Ist die Familie der gemeinsamen unabhängigen Mengen selbst ein Matroid? Nur bis `limit` Elemente gerechnet (sonst None)."""
    if pair.m > limit:
        return None
    return System("schnitt", pair.m, pair.common.tolist()).exchange_scan()[1] == 0


# --- alle Paare kleiner Matroide ------------------------------------------------------------------------------------------------------------


def all_systems(n: int) -> list[tuple[bool, ...]]:
    """Alle nach unten abgeschlossenen Familien auf n Elementen mit leerer Menge, jeweils als Tupel ok[mask]."""
    masks = sorted(range(1 << n), key=lambda x: (popcount(x), x))
    out: list[tuple[bool, ...]] = []
    family = [False] * (1 << n)

    def rec(i):
        if i == len(masks):
            if family[0]:
                out.append(tuple(family))
            return
        mask = masks[i]
        allowed = mask == 0 or all(family[mask & ~(1 << e)] for e in range(n) if mask >> e & 1)
        family[mask] = False
        rec(i + 1)
        if allowed:
            family[mask] = True
            rec(i + 1)
            family[mask] = False

    rec(0)
    return out


def small_matroids(n: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Alle Matroide auf n Elementen als (Tabelle der unabhängigen Mengen, Rangtabelle)."""
    out = []
    for ok in all_systems(n):
        s = System("x", n, list(ok))
        if s.exchange_scan()[1] == 0:
            out.append((np.array(s.ok, dtype=bool), np.array(s.ur, dtype=np.int16)))
    return out


def small_pairs_row(n: int, sample: int, seed: int) -> dict:
    """Alle Paare von Matroiden auf n Elementen: Greedy-Faktor (schlechteste maximale Menge gegen Optimum), Min-Max-Formel, und das Verfahren (alle Paare bis 4 Elemente, sonst eine Stichprobe)."""
    mats = small_matroids(n)
    pc = pc_table()[: 1 << n]
    idx = np.arange(1 << n)
    full = (1 << n) - 1
    comp = full ^ idx
    row = {"n": n, "matroids": len(mats), "pairs": 0, "fail": 0, "worst": 1.0, "half": 0, "below_half": 0, "minmax": 0, "checked": 0, "alg_ok": 0, "cert_ok": 0, "rounds": []}
    grow_index = [(idx & (1 << e)) == 0 for e in range(n)]
    for ok1, ur1 in mats:
        for ok2, ur2 in mats:
            common = ok1 & ok2
            opt = int(pc[common].max())
            maximal = common.copy()
            for e in range(n):
                grow = np.zeros(1 << n, dtype=bool)
                grow[grow_index[e]] = common[idx[grow_index[e]] | (1 << e)]
                maximal &= ~grow
            lo = int(pc[maximal].min())
            row["pairs"] += 1
            row["fail"] += lo < opt
            ratio = lo / opt if opt else 1.0
            row["worst"] = min(row["worst"], ratio)
            row["below_half"] += ratio < 0.5 - 1e-12
            row["half"] += abs(ratio - 0.5) < 1e-12
            row["minmax"] += int((ur1[idx] + ur2[comp]).min()) == opt
    pool = [(a, b) for a in mats for b in mats]
    if len(pool) > sample:
        rng = np.random.default_rng(seed + n)
        pool = [pool[i] for i in rng.choice(len(pool), size=sample, replace=False)]
    for (ok1, ur1), (ok2, ur2) in pool:
        pair = Pair("klein", n, ok1, ok2, tuple(str(i) for i in range(n)), "kanten")
        pair.__dict__["ur1"], pair.__dict__["ur2"] = ur1, ur2
        r = intersect(pair, "faul")
        row["checked"] += 1
        row["alg_ok"] += popcount(r["set"]) == pair.opt
        row["cert_ok"] += certificate(pair, r["reach"])[2] == popcount(r["set"])
        row["rounds"].append(r["rounds"])
    return row


# --- Vereinigung: Partitionsverfahren -----------------------------------------------------------------------------------------------------------


def partition_steps(m: int, tables, allowed: int | None = None) -> dict:
    """Partitionsverfahren für k = len(tables) Matroide auf m Elementen (tables[j][mask]: ist die Menge in Mj unabhängig?). Elemente außerhalb von `allowed` werden ignoriert.

    Je Runde: Austauschgraph auf den Elementen mit Pfeil x → y, wenn y in der Menge Ij liegt und Ij − y + x in Mj unabhängig ist (x nicht in Ij); Quellen sind die noch nicht untergebrachten Elemente,
    eine Senke ist ein Element x, das ohne Tausch in ein Mj passt (x nicht in Ij). Ein kürzester Weg von einer Quelle zu einer Senke: Jedes Element des Wegs übernimmt den Platz seines Nachfolgers,
    das letzte kommt in das Matroid, in das es passt. Am Ende (kein Weg mehr): R = von den nicht untergebrachten Elementen aus erreichbar; dann ist |E ∖ R| + Σ rj(R) = Zahl der untergebrachten Elemente.
    Rückgabe: {"rounds": [{"owner", "path", "target", "size"}, ...], "owner", "reach", "calls", "lengths"}; owner[e] = j oder −1."""
    k = len(tables)
    allowed = (1 << m) - 1 if allowed is None else allowed
    calls = [0]

    def ok(j, mask):
        calls[0] += 1
        return bool(tables[j][mask])

    owner = [-1] * m
    rounds = []
    lengths = []
    while True:
        sets = [sum(1 << e for e in range(m) if owner[e] == j) for j in range(k)]
        unassigned = [e for e in range(m) if allowed >> e & 1 and owner[e] < 0]
        size = sum(1 for e in range(m) if owner[e] >= 0)
        parent = {x: None for x in unassigned}
        queue = list(unassigned)
        head = 0
        found = target = None
        while head < len(queue):
            x = queue[head]
            head += 1
            for j in range(k):
                if owner[x] != j and ok(j, sets[j] | 1 << x):
                    found, target = x, j
                    break
            if found is not None:
                break
            for j in range(k):
                if owner[x] == j:
                    continue
                for y in range(m):
                    if owner[y] == j and y not in parent and ok(j, (sets[j] & ~(1 << y)) | 1 << x):
                        parent[y] = x
                        queue.append(y)
        if found is None:
            reach = sum(1 << v for v in parent)
            rounds.append({"owner": tuple(owner), "path": None, "target": None, "size": size})
            return {"rounds": rounds, "owner": tuple(owner), "reach": reach, "calls": calls[0], "lengths": lengths}
        path = []
        v = found
        while v is not None:
            path.append(v)
            v = parent[v]
        path.reverse()
        rounds.append({"owner": tuple(owner), "path": path, "target": target, "size": size})
        lengths.append(len(path))
        new_owner = list(owner)
        for i in range(len(path) - 1):
            new_owner[path[i]] = owner[path[i + 1]]
        new_owner[path[-1]] = target
        owner = new_owner


def union_rank(ranks, m: int) -> dict:
    """Rang der Vereinigung nach der Formel: Minimum über alle Y ⊆ E von |E ∖ Y| + Σ rj(Y); dazu die Zahl der Minimierer und die ersten (nach Größe und Maske)."""
    idx = np.arange(1 << m)
    total = (m - pc_table()[: 1 << m]).astype(np.int64)
    for r in ranks:
        total = total + r[idx]
    value = int(total.min())
    mins = np.nonzero(total == value)[0].tolist()
    mins.sort(key=lambda x: (popcount(x), x))
    return {"value": value, "count": len(mins), "first": mins[:8]}


def certificate_value(ranks, m: int, reach: int) -> int:
    """|E ∖ R| + Σ rj(R) zur erreichbaren Menge R."""
    return popcount(((1 << m) - 1) & ~reach) + sum(int(r[reach]) for r in ranks)


def union_table(oks, n: int) -> np.ndarray:
    """Vereinigung als Tabelle: unabhängig, wenn zerlegbar in I1 ∪ … ∪ Ik (Aufzählung über alle Zerlegungen; nur für kleine n)."""
    table = np.array(oks[0], dtype=bool)
    for ok in oks[1:]:
        new = np.zeros(1 << n, dtype=bool)
        for mask in range(1 << n):
            sub = mask
            while True:
                if table[sub] and ok[mask ^ sub]:
                    new[mask] = True
                    break
                if sub == 0:
                    break
                sub = (sub - 1) & mask
        table = new
    return table


# --- Graphen: Tutte/Nash-Williams, Arboricity -------------------------------------------------------------------------------------------------------


def components(n: int, edge_list) -> list[int]:
    """Klassenindex (ab 0) je Knoten: Zusammenhangskomponenten des Graphen mit den Kanten edge_list."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edge_list:
        parent[find(a)] = find(b)
    roots = sorted({find(v) for v in range(n)})
    return [roots.index(find(v)) for v in range(n)]


def set_partitions(n: int):
    """Alle Partitionen von {0, …, n − 1} als Klassenindex je Knoten (restricted growth strings)."""
    def rec(i, cur, mx):
        if i == n:
            yield tuple(cur)
            return
        for c in range(mx + 2):
            cur.append(c)
            yield from rec(i + 1, cur, max(mx, c))
            cur.pop()
    yield from rec(0, [], -1)


def tutte_min(n: int, edges) -> dict:
    """Zahl der kantendisjunkten Spannbäume nach Tutte/Nash-Williams: das Minimum über alle Partitionen mit mindestens 2 Klassen von ⌊Kanten zwischen den Klassen / (Klassen − 1)⌋;
    dazu die Partition mit dem kleinsten Verhältnis (die engste Stelle) und ihre Zahlen."""
    best = None
    for part in set_partitions(n):
        classes = max(part) + 1
        if classes < 2:
            continue
        cross = sum(1 for a, b in edges if part[a] != part[b])
        ratio = cross / (classes - 1)
        if best is None or ratio < best[0]:
            best = (ratio, part, cross, classes)
    ratio, part, cross, classes = best
    return {"tau": int(ratio), "partition": part, "cross": cross, "classes": classes, "ratio": ratio}


def nash_williams(n: int, edges) -> dict:
    """Arboricity nach Nash-Williams: das Maximum über alle Knotenmengen U mit mindestens 2 Knoten von ⌈Kanten in U / (|U| − 1)⌉; dazu die dichteste Knotenmenge."""
    best = None
    for sub in range(1, 1 << n):
        size = popcount(sub)
        if size < 2:
            continue
        inside = sum(1 for a, b in edges if sub >> a & 1 and sub >> b & 1)
        ratio = inside / (size - 1)
        if best is None or ratio > best[0] + 1e-12:
            best = (ratio, sub, inside, size)
    ratio, sub, inside, size = best
    return {"arboricity": max(1, -(-inside // (size - 1))), "subset": sub, "inside": inside, "size": size, "ratio": ratio}


def forest_run(table, m: int, k: int, allowed: int | None = None) -> dict:
    return partition_steps(m, [table] * k, allowed)


def trees_by_algorithm(table, m: int, n: int) -> int:
    """Größte Zahl k, für die sich k kantendisjunkte Spannbäume finden lassen (Partitionsverfahren)."""
    k = 0
    while (k + 1) * (n - 1) <= m:
        run = forest_run(table, m, k + 1)
        sizes = [sum(1 for o in run["owner"] if o == j) for j in range(k + 1)]
        if not all(s == n - 1 for s in sizes):
            break
        k += 1
    return k


def arboricity_by_algorithm(table, m: int) -> int:
    """Kleinste Zahl k, für die sich alle Kanten auf k Wälder verteilen lassen (Partitionsverfahren)."""
    k = 1
    while True:
        run = forest_run(table, m, k)
        if all(o >= 0 for o in run["owner"]):
            return k
        k += 1


# --- alle kleinen Paare: Rangformel, Matroid, Verfahren, Zertifikat, Reduktion auf den Schnitt ------------------------------------------------------------------


def small_union_row(n: int, sample: int, seed: int) -> dict:
    """Vereinigung zweier Matroide auf n Elementen (bei n = 5 eine Stichprobe): Rangformel (für jede Teilmenge X), Vereinigung ist ein Matroid, Verfahren = Rang, Zertifikat."""
    rng = np.random.default_rng(seed + n)
    mats = small_matroids(n)
    pairs = [(a, b) for a in mats for b in mats]
    if n >= 5 and len(pairs) > sample:
        pairs = [pairs[i] for i in rng.choice(len(pairs), size=sample, replace=False)]
    full = (1 << n) - 1
    row = {"n": n, "pairs": len(pairs), "formula": 0, "matroid": 0, "alg": 0, "cert": 0}
    idx = np.arange(1 << n)
    subsets = [np.array([y for y in range(1 << n) if y & ~x == 0]) for x in range(1 << n)]
    for (ok1, ur1), (ok2, ur2) in pairs:
        table = union_table([ok1, ok2], n)
        ur = rank_table(table, n)
        row["formula"] += all(int(min(popcount(x & ~y) + int(ur1[y]) + int(ur2[y]) for y in subsets[x])) == int(ur[x]) for x in range(1 << n))
        row["matroid"] += System("u", n, table.tolist()).exchange_scan()[1] == 0
        run = partition_steps(n, [ok1, ok2])
        size = sum(1 for o in run["owner"] if o >= 0)
        row["alg"] += size == int(ur[full])
        row["cert"] += certificate_value([ur1, ur2], n, run["reach"]) == size
    return row


def reduction_row(n: int, sample: int, seed: int) -> dict:
    """Reduktion auf den Schnitt (k = 2): Grundmenge E × {1, 2}; M_A: Kopie 1 in M1, Kopie 2 in M2; M_B: jedes Element in höchstens einer Kopie. Größte gemeinsame Menge = Rang der Vereinigung?"""
    rng = np.random.default_rng(seed + 100 + n)
    mats = small_matroids(n)
    pairs = [(a, b) for a in mats for b in mats]
    if n >= 5 and len(pairs) > sample:
        pairs = [pairs[i] for i in rng.choice(len(pairs), size=sample, replace=False)]
    row = {"n": n, "pairs": len(pairs), "agree": 0, "calls_direct": 0, "calls_reduction": 0}
    for (ok1, ur1), (ok2, ur2) in pairs:
        union = union_table([ok1, ok2], n)
        opt_union = int(pc_table()[np.nonzero(union)[0]].max())
        m2 = 2 * n
        idx = np.arange(1 << m2)
        low, high = idx & ((1 << n) - 1), idx >> n
        pair = Pair("red", m2, ok1[low] & ok2[high], (low & high) == 0, tuple(str(i) for i in range(m2)), "kanten")
        r = intersect(pair, "faul")
        row["agree"] += popcount(r["set"]) == opt_union == pair.opt
        row["calls_reduction"] += r["calls"]
        row["calls_direct"] += partition_steps(n, [ok1, ok2])["calls"]
    return row
