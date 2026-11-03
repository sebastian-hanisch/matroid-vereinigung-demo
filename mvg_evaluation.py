"""Kennzahlen, Experimente und Verdikte. Alle sichtbaren Zahlen kommen aus diesen Funktionen."""

import statistics
from dataclasses import dataclass
from functools import lru_cache

import mvg_constants as C
from mvg_algorithm import (
    arboricity_by_algorithm,
    certificate_value,
    components,
    elements,
    nash_williams,
    partition_steps,
    popcount,
    rank_table,
    reduction_row,
    set_partitions,
    small_union_row,
    trees_by_algorithm,
    tutte_min,
    union_rank,
)
from mvg_systems import color_table, edge_colors, forest_table, get_net


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma."""
    return f"{x:.{digits}f}".replace(".", ",")


def prozent(x: float, digits: int = 1) -> str:
    return de(100.0 * x, digits)


def zahl(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner."""
    return f"{n:,}".replace(",", " ")


def elemente(k: int) -> str:
    return "1 Element" if k == 1 else f"{k} Elemente"


def spannbaeume(k: int) -> str:
    return "1 Spannbaum" if k == 1 else f"{k} kantendisjunkte Spannbäume"


def waelder(k: int) -> str:
    return "1 Wald" if k == 1 else f"{k} Wälder"


def leitungen(k: int) -> str:
    return "1 Leitung" if k == 1 else f"{k} Leitungen"


def mengen(k: int) -> str:
    return "1 Menge" if k == 1 else f"{k} Mengen"


def uebrig(k: int) -> str:
    return "1 bleibt" if k == 1 else f"{k} bleiben"


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED
    graph: str = "plan"
    task: str = "waelder"
    k: int = C.DEFAULT_K
    c: int = C.DEFAULT_C


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    nodes: int                  # Zahl der Standorte
    m: int                      # Zahl der Leitungen
    labels: tuple
    matroids: tuple             # Namen der beteiligten Matroide (k Wälder oder Wald und Farbregel)
    k: int                      # Zahl der Matroide
    size: int                   # untergebrachte Leitungen
    complete: bool              # alle Leitungen untergebracht
    spanning: bool | None       # alle Wälder sind Spannbäume (nur bei Wäldern)
    formula: int                # Rang der Vereinigung nach der Formel (Minimum über alle Y)
    certificate: int            # |E ∖ R| + Σ rj(R) zur erreichbaren Menge R


def net_of(s: Settings):
    return get_net(s.graph, s.n, s.seed)


def tables_of(s: Settings):
    ft = forest_table(s.graph, s.n, s.seed)
    if s.task == "farben":
        return [ft, color_table(net_of(s), s.seed, s.c)]
    return [ft] * s.k


def names_of(s: Settings) -> tuple:
    if s.task == "farben":
        return ("Wald", "Farbregel")
    return tuple(f"Wald {j + 1}" for j in range(s.k))


@lru_cache(maxsize=32)
def run_view(s: Settings) -> dict:
    net = net_of(s)
    return partition_steps(len(net.edges), tables_of(s))


@lru_cache(maxsize=32)
def ranks_of(s: Settings) -> tuple:
    m = len(net_of(s).edges)
    return tuple(rank_table(t, m) for t in tables_of(s))


@lru_cache(maxsize=32)
def formula_of(s: Settings) -> dict:
    return union_rank(ranks_of(s), len(net_of(s).edges))


def analyse(s: Settings) -> Analysis:
    net = net_of(s)
    m = len(net.edges)
    run = run_view(s)
    owner = run["owner"]
    k = len(tables_of(s))
    size = sum(1 for o in owner if o >= 0)
    spanning = None
    if s.task == "waelder":
        spanning = all(sum(1 for o in owner if o == j) == net.n - 1 for j in range(k))
    return Analysis(s, net.n, m, net.labels, names_of(s), k, size, size == m, spanning, formula_of(s)["value"], certificate_value(ranks_of(s), m, run["reach"]))


def into(a: Analysis, j: int) -> str:
    """„in den Wald“, „in die Farbregel“ oder „in Wald 2“."""
    if a.settings.task == "farben":
        return ("in den Wald", "in die Farbregel")[j]
    return f"in {a.matroids[j]}"


def names(a: Analysis, mask: int) -> str:
    return ", ".join(a.labels[e] for e in elements(mask, a.m))


def setstr(a: Analysis, mask: int) -> str:
    return "{" + names(a, mask) + "}" if mask else "∅"


def seq(a: Analysis, path) -> str:
    return " → ".join(a.labels[v] for v in path)


# --- Hauptansicht: Partition-Lauf --------------------------------------------------------------------------------------------------------------


def round_groups(a: Analysis, run: dict, index: int) -> dict:
    """Bild der Runde: Leitungen je Matroid gefärbt, nicht untergebrachte rot gestrichelt, der Weg als Halo."""
    rd = run["rounds"][index]
    owner = rd["owner"]
    groups = [(a.matroids[j], [e for e in range(a.m) if owner[e] == j], C.FOREST_COLORS[j % len(C.FOREST_COLORS)]) for j in range(a.k)]
    unassigned = [e for e in range(a.m) if owner[e] < 0]
    halo = list(rd["path"]) if rd["path"] else []
    return {"groups": groups, "unassigned": unassigned, "halo": halo}


def reach_classes(a: Analysis, run: dict) -> list[int]:
    """Klassenindex je Standort: Zusammenhangskomponenten der Leitungen in der erreichbaren Menge R (Tutte-Partition bzw. Knotenmengen der Verdichtung)."""
    net_edges = net_of(a.settings).edges
    return components(a.nodes, [net_edges[e] for e in range(a.m) if run["reach"] >> e & 1])


def round_rows(a: Analysis, run: dict, index: int) -> list[dict]:
    rd = run["rounds"][index]
    pos = {v: i + 1 for i, v in enumerate(rd["path"] or [])}
    return [{"Leitung": a.labels[e], "untergebracht in": a.matroids[rd["owner"][e]] if rd["owner"][e] >= 0 else "–", "im Weg": str(pos[e]) if e in pos else "–"} for e in range(a.m)]


def verdict_round(a: Analysis, run: dict, index: int) -> tuple[str, str]:
    rd = run["rounds"][index]
    if rd["path"] is not None:
        path = rd["path"]
        target = into(a, rd["target"])
        first = a.labels[path[0]]
        if len(path) == 1:
            move = f"{first} passt ohne Tausch {target}."
        else:
            steps = "; ".join(f"{a.labels[path[i]]} nimmt den Platz von {a.labels[path[i + 1]]}" for i in range(len(path) - 1))
            move = f"Der kürzeste Weg hat {elemente(len(path))}: {seq(a, path)}. {steps}; zuletzt kommt {a.labels[path[-1]]} {target}."
        return "info", f"Runde {index + 1}: {rd['size']} Leitungen sind untergebracht. {move} Danach sind es {rd['size'] + 1}."
    unassigned = [e for e in range(a.m) if rd["owner"][e] < 0]
    if not unassigned:
        return "success", f"Runde {index + 1}: **Alle {a.m} Leitungen** sind untergebracht; es gibt nichts mehr zu tun (Zertifikat: Y = ∅, |E ∖ Y| + Σ r_j(Y) = {a.m} + 0)."
    reach = run["reach"]
    if a.certificate != a.size or a.formula != a.size:
        return "error", "Zertifikat oder Rangformel stimmen nicht mit der Zahl der untergebrachten Leitungen überein. Das darf nicht sein: Rechenfehler."
    return "success", (
        f"Runde {index + 1}: Von {'der Leitung' if len(unassigned) == 1 else f'den {len(unassigned)} Leitungen'} {{{names(a, sum(1 << e for e in unassigned))}}} führt **kein Weg** mehr zu einer Senke. Untergebracht sind **{a.size}** von {a.m} Leitungen, mehr geht nicht: "
        f"Mit Y = {{{names(a, reach)}}} ist |E ∖ Y| + Σ r_j(Y) = {popcount(((1 << a.m) - 1) & ~reach)} + {a.certificate - popcount(((1 << a.m) - 1) & ~reach)} = **{a.certificate}**, "
        f"und das ist nach der Rangformel das Minimum über alle Y ({a.formula})."
    )


def verdict_final(a: Analysis) -> tuple[str, str]:
    s = a.settings
    if s.task == "farben":
        if a.complete:
            return "success", f"Alle {a.m} Leitungen lassen sich auf einen Wald und eine Farbregel-Menge verteilen."
        return "info", f"Von {a.m} Leitungen passen {a.size} in einen Wald und eine Menge mit höchstens einer Leitung je Farbe; {uebrig(a.m - a.size)} übrig."
    parts = []
    parts.append(f"{spannbaeume(a.k)} **gibt es**" if a.spanning else f"{spannbaeume(a.k)} **gibt es nicht**")
    parts.append("alle Leitungen passen auf " + f"{a.k} Wälder" if a.complete else f"nicht alle Leitungen passen auf {a.k} Wälder (untergebracht: {a.size} von {a.m})")
    return ("success" if a.spanning else "info"), f"Bei {a.nodes} Standorten und {a.m} Leitungen: " + "; ".join(parts) + "."


# --- Experiment 1: kantendisjunkte Spannbäume ---------------------------------------------------------------------------------------------------


@lru_cache(maxsize=32)
def trees_view(s: Settings) -> dict:
    net = net_of(s)
    m, n = len(net.edges), net.n
    table = forest_table(s.graph, s.n, s.seed)
    tutte = tutte_min(n, net.edges)
    alg = trees_by_algorithm(table, m, n)
    rows = []
    for k in range(1, tutte["tau"] + 2):
        run = partition_steps(m, [table] * k)
        sizes = [sum(1 for o in run["owner"] if o == j) for j in range(k)]
        rows.append({"k": k, "sizes": sizes, "spanning": all(x == n - 1 for x in sizes), "reach": run["reach"], "size": sum(sizes), "need": k * (n - 1)})
    fail = rows[-1]
    part = components(n, [net.edges[e] for e in range(m) if fail["reach"] >> e & 1]) if not fail["spanning"] else None
    cert = None
    if part is not None:
        classes = max(part) + 1
        cross = sum(1 for a, b in net.edges if part[a] != part[b])
        cert = {"partition": part, "classes": classes, "cross": cross, "k": fail["k"], "violated": classes >= 2 and cross < fail["k"] * (classes - 1)}
    return {"tutte": tutte, "alg": alg, "rows": rows, "cert": cert}


def trees_rows(view: dict) -> list[dict]:
    return [{"Zahl der Wälder k": r["k"], "Leitungen je Wald": " + ".join(str(x) for x in r["sizes"]), "gebraucht je Spannbaum": r["need"] // r["k"], "alle Spannbäume": "ja" if r["spanning"] else "nein"} for r in view["rows"]]


def verdict_trees(a: Analysis, view: dict) -> tuple[str, str]:
    t, alg, cert = view["tutte"], view["alg"], view["cert"]
    if t["tau"] != alg:
        return "error", "Das Partitionsverfahren und die Formel von Tutte und Nash-Williams stimmen nicht überein. Das darf nicht sein: Rechenfehler."
    head = f"Es lassen sich höchstens **{spannbaeume(alg)}** packen (Partitionsverfahren **und** Minimum über alle {zahl(bell(a.nodes) - 1)} Partitionen der {a.nodes} Standorte in mindestens zwei Klassen: gleich). "
    if cert is None:
        return "success", head + "Mehr Wälder als Leitungen erlauben, gibt es hier nicht."
    if not cert["violated"]:
        return "error", "Die Partition aus der erreichbaren Menge verletzt die Bedingung von Tutte nicht. Das darf nicht sein: Rechenfehler."
    return "info", head + (
        f"Für k = {cert['k']} scheitert es an einer Partition mit {cert['classes']} Klassen: Zwischen den Klassen liegen nur **{cert['cross']}** Leitungen, gebraucht würden {cert['k']} · ({cert['classes']} − 1) = **{cert['k'] * (cert['classes'] - 1)}** "
        f"(die Klassen sind die Zusammenhangskomponenten der erreichbaren Menge)."
    )


@lru_cache(maxsize=16)
def bell(n: int) -> int:
    """Zahl der Partitionen einer n-elementigen Menge (Bellsche Zahl)."""
    return sum(1 for _ in set_partitions(n))


# --- Experiment 2: Arboricity -------------------------------------------------------------------------------------------------------------------


@lru_cache(maxsize=32)
def arb_view(s: Settings) -> dict:
    net = net_of(s)
    m, n = len(net.edges), net.n
    table = forest_table(s.graph, s.n, s.seed)
    nw = nash_williams(n, net.edges)
    alg = arboricity_by_algorithm(table, m)
    rows = []
    for k in range(1, alg + 1):
        run = partition_steps(m, [table] * k)
        rows.append({"k": k, "size": sum(1 for o in run["owner"] if o >= 0), "reach": run["reach"], "complete": all(o >= 0 for o in run["owner"])})
    cert = None
    if alg >= 2:
        fail = rows[-2]
        part = components(n, [net.edges[e] for e in range(m) if fail["reach"] >> e & 1])
        best = None
        for c in sorted(set(part)):
            nodes = [v for v in range(n) if part[v] == c]
            inside = [e for e, (u, w) in enumerate(net.edges) if part[u] == c and part[w] == c]
            excess = len(inside) - fail["k"] * (len(nodes) - 1)
            if best is None or excess > best["excess"]:
                best = {"nodes": nodes, "edges": inside, "excess": excess, "k": fail["k"]}
        cert = best
    return {"nw": nw, "alg": alg, "rows": rows, "cert": cert}


def arb_rows(a: Analysis, view: dict) -> list[dict]:
    return [{"Zahl der Wälder k": r["k"], "untergebrachte Leitungen": f"{r['size']} von {a.m}", "alle Leitungen untergebracht": "ja" if r["complete"] else "nein"} for r in view["rows"]]


def verdict_arb(a: Analysis, view: dict) -> tuple[str, str]:
    nw, alg, cert = view["nw"], view["alg"], view["cert"]
    if nw["arboricity"] != alg:
        return "error", "Das Partitionsverfahren und die Formel von Nash-Williams stimmen nicht überein. Das darf nicht sein: Rechenfehler."
    head = f"Die Leitungen lassen sich auf **{alg}** Wälder verteilen, auf weniger nicht (Partitionsverfahren **und** Maximum über alle {zahl(2 ** a.nodes - a.nodes - 1)} Knotenmengen: gleich). "
    if cert is None:
        return "success", head + "Ein Wald genügt: Das Netz hat keinen Kreis."
    if cert["excess"] <= 0:
        return "error", "Die Knotenmenge aus der erreichbaren Menge ist nicht zu dicht. Das darf nicht sein: Rechenfehler."
    lab = ", ".join(a.labels[e] for e in cert["edges"])
    return "info", head + (
        f"Auf {waelder(cert['k'])} passt es nicht, weil eine Knotenmenge mit {len(cert['nodes'])} Standorten **{len(cert['edges'])}** Leitungen in sich hat, aber in {waelder(cert['k'])} passen dort höchstens "
        f"{cert['k']} · ({len(cert['nodes'])} − 1) = **{cert['k'] * (len(cert['nodes']) - 1)}** ({lab})."
    )


# --- Experiment 3: Wald ∨ Farbregel ---------------------------------------------------------------------------------------------------------------


def mix_settings(s: Settings) -> Settings:
    return Settings(s.n, s.seed, s.graph, "farben", 2, s.c)


def mix_view(s: Settings) -> dict:
    ms = mix_settings(s)
    a = analyse(ms)
    run = run_view(ms)
    return {"a": a, "owner": run["owner"], "reach": run["reach"], "formula": formula_of(ms), "colors": edge_colors(net_of(ms), ms.seed, ms.c)}


def mix_groups(view: dict) -> dict:
    a, owner = view["a"], view["owner"]
    groups = [(a.matroids[j], [e for e in range(a.m) if owner[e] == j], C.FOREST_COLORS[j]) for j in range(2)]
    return {"groups": groups, "unassigned": [e for e in range(a.m) if owner[e] < 0], "halo": []}


def verdict_mix(view: dict) -> tuple[str, str]:
    a, f = view["a"], view["formula"]
    if f["value"] != a.size or a.certificate != a.size:
        return "error", "Rangformel oder Zertifikat stimmen nicht mit der Zahl der untergebrachten Leitungen überein. Das darf nicht sein: Rechenfehler."
    wald = sum(1 for o in view["owner"] if o == 0)
    farben = sum(1 for o in view["owner"] if o == 1)
    return "success", (
        f"Von {a.m} Leitungen kommen **{a.size}** in einen Wald ({wald}) und eine Menge mit höchstens einer Leitung je Farbe ({farben}); {uebrig(a.m - a.size)} übrig. "
        f"Das ist der Rang der Vereinigung: Das Minimum über alle {zahl(2 ** a.m)} Mengen Y von |E ∖ Y| + r_Wald(Y) + r_Farbe(Y) ist {f['value']} und wird bei {mengen(f['count'])} angenommen; "
        f"das Verfahren findet eine davon (sein Y hat {leitungen(popcount(view['reach']))})."
    )


# --- Experiment 4: alle kleinen Paare und die Reduktion --------------------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def small_rows() -> tuple:
    return tuple(small_union_row(n, C.PAIR_SAMPLE, C.PLAY_SEED) for n in range(1, C.ENUM_MAX_N + 1))


@lru_cache(maxsize=1)
def reduction_rows() -> tuple:
    return tuple(reduction_row(n, C.REDUCTION_SAMPLE, C.PLAY_SEED) for n in range(1, C.ENUM_MAX_N + 1))


def small_table(rows, red) -> list[dict]:
    out = []
    for r, q in zip(rows, red):
        out.append({
            "Elemente n": r["n"], "Paare": zahl(r["pairs"]), "Rangformel gilt": zahl(r["formula"]), "Vereinigung ist ein Matroid": zahl(r["matroid"]), "Verfahren = Rang": zahl(r["alg"]),
            "Zertifikat stimmt": zahl(r["cert"]), "Reduktion = Rang": f"{zahl(q['agree'])} von {zahl(q['pairs'])}",
            "Orakelaufrufe direkt": de(q["calls_direct"] / q["pairs"]), "über den Schnitt": de(q["calls_reduction"] / q["pairs"]),
        })
    return out


def verdict_small(rows, red) -> tuple[str, str]:
    pairs = sum(r["pairs"] for r in rows)
    bad = sum(r["pairs"] - r[key] for r in rows for key in ("formula", "matroid", "alg", "cert")) + sum(q["pairs"] - q["agree"] for q in red)
    if bad:
        return "error", f"Bei {bad} Prüfungen gilt eine Aussage nicht. Das darf nicht sein: Rechenfehler."
    last = red[-1]
    factor = last["calls_reduction"] / last["calls_direct"]
    return "success", (
        f"Bei allen {zahl(pairs)} geprüften Paaren von Matroiden mit höchstens {rows[-1]['n']} Elementen: Die Rangformel gilt, die Vereinigung ist ein Matroid, das Partitionsverfahren findet den Rang, und das Zertifikat stimmt "
        f"(**0 Abweichungen**). Die Reduktion auf den Schnitt liefert bei allen {zahl(sum(q['pairs'] for q in red))} geprüften Paaren dieselbe Zahl, braucht aber bei {last['n']} Elementen im Mittel "
        f"**{de(factor)}-mal** so viele Orakelaufrufe wie das direkte Verfahren."
    )


# --- Spielwiese -------------------------------------------------------------------------------------------------------------------------------------


def play_view(s: Settings, mask: int) -> dict:
    """Lässt sich die Leitungsmenge `mask` auf k Wälder verteilen? Ja: die Zerlegung; nein: die zu dichte Knotenmenge."""
    net = net_of(s)
    m, n = len(net.edges), net.n
    table = forest_table(s.graph, s.n, s.seed)
    run = partition_steps(m, [table] * s.k, mask)
    owner = run["owner"]
    placed = sum(1 for e in range(m) if owner[e] >= 0)
    total = popcount(mask)
    out = {"mask": mask, "k": s.k, "owner": owner, "placed": placed, "total": total, "complete": placed == total, "dense": None}
    if mask and not out["complete"]:
        part = components(n, [net.edges[e] for e in range(m) if run["reach"] >> e & 1])
        best = None
        for c in sorted(set(part)):
            nodes = [v for v in range(n) if part[v] == c]
            inside = [e for e in range(m) if mask >> e & 1 and part[net.edges[e][0]] == c and part[net.edges[e][1]] == c]
            excess = len(inside) - s.k * (len(nodes) - 1)
            if best is None or excess > best["excess"]:
                best = {"nodes": nodes, "edges": inside, "excess": excess}
        out["dense"] = best
    return out


def verdict_play(a: Analysis, v: dict) -> tuple[str, str]:
    total, k = v["total"], v["k"]
    if not total:
        return "info", "Wählen Sie mindestens eine Leitung."
    if v["complete"]:
        subject = "Die gewählte Leitung lässt" if total == 1 else f"Die {total} gewählten Leitungen lassen"
        return "success", f"{subject} sich auf {waelder(k)} verteilen (Zerlegung im Bild)."
    d = v["dense"]
    if d is None or d["excess"] <= 0:
        return "error", "Keine zu dichte Knotenmenge gefunden. Das darf nicht sein: Rechenfehler."
    return "warning", (
        f"Die {total} gewählten Leitungen lassen sich **nicht** auf {waelder(k)} verteilen (untergebracht: {v['placed']}). Eine Knotenmenge mit {len(d['nodes'])} Standorten hat {len(d['edges'])} der gewählten Leitungen in sich, "
        f"in {waelder(k)} passen dort aber höchstens {k} · ({len(d['nodes'])} − 1) = {k * (len(d['nodes']) - 1)}."
    )


# --- Messreihe über Pläne (auf Abruf) --------------------------------------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def plan_series() -> tuple:
    """Pläne mit 6 bis 8 Standorten, 20 Seeds: Zahl der kantendisjunkten Spannbäume und Arboricity (Partitionsverfahren)."""
    rows = []
    for n in C.SERIES_N:
        taus, arbs, calls = [], [], []
        for seed in range(C.SERIES_SEEDS):
            net = get_net("plan", n, seed)
            table = forest_table("plan", n, seed)
            m = len(net.edges)
            taus.append(trees_by_algorithm(table, m, net.n))
            arbs.append(arboricity_by_algorithm(table, m))
            calls.append(partition_steps(m, [table, table])["calls"])
        rows.append({"n": n, "m": 2 * n - 2, "two_trees": sum(1 for t in taus if t >= 2), "arb2": sum(1 for a in arbs if a == 2), "arb3": sum(1 for a in arbs if a == 3), "plans": len(taus), "calls": statistics.mean(calls)})
    return tuple(rows)


def series_table(rows) -> list[dict]:
    return [{"Standorte": r["n"], "Leitungen": r["m"], "Pläne": r["plans"], "zwei Spannbäume": r["two_trees"], "Arboricity 2": r["arb2"], "Arboricity 3": r["arb3"], "Orakelaufrufe bei k = 2 im Mittel": de(r["calls"], 0)} for r in rows]


def verdict_series(rows) -> tuple[str, str]:
    consistent = all(r["two_trees"] == r["arb2"] and r["two_trees"] + r["arb3"] == r["plans"] for r in rows)
    if not consistent:
        return "warning", "Auf manchen Plänen ist die Arboricity 2 ohne zwei Spannbäume oder größer als 3: Die Pläne sind anders gebaut als erwartet."
    shares = ", ".join(f"{prozent(r['two_trees'] / r['plans'], 0)} %" for r in rows)
    return "info", (
        f"Bei Plänen mit 6, 7, 8 Standorten haben {shares} zwei kantendisjunkte Spannbäume; die Arboricity ist bei diesen Plänen genau bei den Plänen mit zwei Spannbäumen 2, sonst 3. Bei 2n − 2 Leitungen heißt „zwei Spannbäume“: "
        f"alle Leitungen bilden zwei Bäume."
    )
