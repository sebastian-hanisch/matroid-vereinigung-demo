"""Matroid-Vereinigung - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 9 der Reihe „Matroide und Submodularität“ (Bereich Kombinatorik). Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import mvg_constants as C
from mvg_evaluation import (
    Settings,
    analyse,
    arb_rows,
    arb_view,
    leitungen,
    mix_groups,
    mix_view,
    net_of,
    plan_series,
    play_view,
    reach_classes,
    reduction_rows,
    round_groups,
    round_rows,
    run_view,
    series_table,
    small_rows,
    small_table,
    trees_rows,
    trees_view,
    uebrig,
    verdict_arb,
    verdict_final,
    verdict_mix,
    verdict_play,
    verdict_round,
    verdict_series,
    verdict_small,
    verdict_trees,
)
from mvg_layout import dunkles_design, kopf_css
from mvg_pdf_export import build_pdf
from mvg_presets import bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sidebar_presets, sync_query_params
from mvg_systems import edge_colors
from mvg_visualization import build_graph

st.set_page_config(page_title="Matroid-Vereinigung – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Tabellen der Matroide aufbauen …")
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _run(settings):
    return run_view(settings)


@st.cache_data(show_spinner="Alle Partitionen der Standorte durchgehen …")
def _trees(settings):
    return trees_view(settings)


@st.cache_data(show_spinner="Alle Knotenmengen durchgehen …")
def _arb(settings):
    return arb_view(settings)


@st.cache_data(show_spinner="Alle Mengen Y durchgehen …")
def _mix(settings):
    return mix_view(settings)


@st.cache_data(show_spinner="Pläne mit 6 bis 8 Standorten durchrechnen (einige Sekunden) …")
def _series():
    return plan_series()


@st.cache_data(show_spinner="Alle Paare von Matroiden bis 5 Elemente prüfen und auf den Schnitt zurückführen (einige Sekunden) …")
def _small():
    return small_rows(), reduction_rows()


@st.cache_data(show_spinner=False)
def _play(settings, mask):
    return play_view(settings, mask)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in mvg_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 Matroid-Vereinigung – disjunkte Strukturen packen")
st.markdown(
    """
Bisher war es ein Matroid, dann zwei auf einmal (Schnitt). Hier werden Matroide **vereinigt**: Eine Menge ist unabhängig, wenn sie sich in **k Teile zerlegen** lässt, von denen der erste in M1, der zweite in M2 und so weiter unabhängig ist. Anders als der Schnitt ist die **Vereinigung wieder ein Matroid**, mit einer Formel für den Rang. Auf dem Leitungsnetz heißt das: **k kantendisjunkte Spannbäume** (Satz von Tutte und Nash-Williams) und die kleinste Zahl von **Wäldern**, die alle Leitungen überdecken (die **Arboricity**, Satz von Nash-Williams). Gerechnet wird mit dem **Partitionsverfahren**: ein kürzester Weg im Austauschgraphen bringt eine weitere Leitung unter, und wenn keiner mehr da ist, zeigt die erreichbare Menge ein **Zertifikat**. Man kann die Vereinigung auch auf den Schnitt aus Stück 7 zurückführen, das kostet aber mehr Orakelaufrufe.

Dies ist das **neunte Stück** der Reihe „Matroide und Submodularität“. Weiter unten: vier Experimente (🔬), eine **Spielwiese**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So hängt es zusammen", expanded=True):
    st.markdown(
        """
1. **Vereinigung:** I ist unabhängig in M1 ∨ … ∨ Mk, wenn I = I1 ∪ … ∪ Ik mit Ij unabhängig in Mj. **Rang:** r(X) = Minimum über alle Y ⊆ X von |X ∖ Y| + r1(Y) + … + rk(Y).
2. **Graphen:** Mit k Exemplaren des Waldmatroids ist eine Zerlegung ein Packen von k kantendisjunkten Wäldern. k Spannbäume gibt es genau dann, wenn jede Partition der Standorte in P Klassen mindestens k · (P − 1) Leitungen zwischen den Klassen hat. Alle Leitungen passen auf k Wälder genau dann, wenn jede Knotenmenge U höchstens k · (|U| − 1) Leitungen in sich hat.
3. **Partitionsverfahren:** Austauschgraph auf den Leitungen: Pfeil x → y, wenn y im Teil Ij liegt und Ij − y + x in Mj unabhängig ist. **Quellen:** noch nicht untergebrachte Leitungen. **Senken:** Leitungen, die ohne Tausch in ein Mj passen. Auf einem kürzesten Weg übernimmt jede Leitung den Platz ihres Nachfolgers, die letzte kommt in das Mj, in das sie passt.
4. **Zertifikat:** Gibt es keinen Weg mehr, sei R die von den Quellen aus erreichbare Menge. Dann ist |E ∖ R| + r1(R) + … + rk(R) so groß wie die Zahl der untergebrachten Leitungen, und das ist nach der Rangformel auch die kleinste mögliche Zahl. Bei Wäldern sind die Zusammenhangskomponenten von R die Partition von Tutte (bei Spannbäumen) beziehungsweise zeigen die zu dichte Knotenmenge (bei der Überdeckung).
5. **Reduktion auf den Schnitt:** Zwei Kopien der Grundmenge, M_A (Kopie 1 in M1, Kopie 2 in M2) und M_B (jede Leitung in höchstens einer Kopie): Die größte gemeinsame Menge hat die Größe des Rangs der Vereinigung (Experiment 4).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Netz**")
    graph = st.selectbox("Netz", C.GRAPHS, key="graph_select", format_func=C.GRAPH_NAMES.get,
                         help="Das Leitungsnetz aus den früheren Stücken (Plan, hängt von Standorten und Seed ab) oder ein festes Netz: K4, K5, K6 und K3,3.")
    n = st.slider("Standorte (mit Depot A, nur Plan)", *bounds("n_slider"), key="n_slider", help="Wie viele Standorte der Plan hat. Bis 9 (16 mögliche Leitungen). Die festen Netze hängen nicht davon ab.")
    seed = st.number_input("Zufalls-Seed (Plan und Farben)", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Plan generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Aufgabe**")
    task = st.selectbox("Vereinigung von", C.TASKS, key="task_select", format_func=C.TASK_NAMES.get,
                        help="k Exemplare des Waldmatroids (kantendisjunkte Wälder) oder zwei verschiedene Matroide: ein Wald und eine Farbregel.")
    k = st.slider("Zahl der Wälder k", *bounds("k_slider"), key="k_slider", help="Nur bei „k Wälder“: Wie viele Wälder gepackt werden.")
    c = st.slider("Kabelfarben (Farbregel)", *bounds("c_slider"), key="c_slider", help="Nur bei „Wald ∨ Farbregel“ und in Experiment 3: Wie viele Farben die Leitungen haben; je Farbe höchstens eine Leitung in der Farbregel-Menge.")

sync_query_params({"n_slider": int(n), "seed_input": int(seed), "graph_select": graph, "task_select": task, "k_slider": int(k), "c_slider": int(c)})

settings = Settings(int(n), int(seed), graph, task, int(k), int(c))
a = _analysis(settings)
net = net_of(settings)
run = _run(settings)
rounds = run["rounds"]
play_id = f"{graph}_{settings.n}_{settings.seed}_{task}_{settings.k}_{settings.c}"
graph_only = Settings(settings.n, settings.seed, graph)   # Experimente 1 und 2 hängen nur vom Netz ab

# --- Partitionslauf ------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Partitionslauf")
st.caption((f"{C.GRAPH_NAMES[graph]}: {a.nodes} Standorte, {leitungen(a.m)}" if graph == "plan" else C.GRAPH_NAMES[graph]) + f". Aufgabe: {C.TASK_NAMES[task]}" + (f", k = {a.k}." if task == "waelder" else f", {settings.c} Farben."))
mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("Leitungen", a.m)
mc2.metric("Untergebracht", a.size, delta="alle" if a.complete else f"{uebrig(a.m - a.size)} übrig", delta_color="off")
mc3.metric("Rang nach der Formel", a.formula, help="Minimum über alle Mengen Y von |E ∖ Y| + Summe der Ränge von Y.")
mc4.metric("Wert des Zertifikats", a.certificate, help="|E ∖ R| + Summe der Ränge von R, R = von den nicht untergebrachten Leitungen aus erreichbar.")
r_idx = 0
if len(rounds) > 1:
    r_idx = st.slider("Runde", 1, len(rounds), len(rounds), key=f"round_{play_id}", help="Welche Runde des Verfahrens angezeigt wird (zuletzt: das Ergebnis).") - 1
rd = rounds[r_idx]
groups = round_groups(a, run, r_idx)
path_text = {v: str(i + 1) for i, v in enumerate(rd["path"] or [])}
final_round = rd["path"] is None
node_class = reach_classes(a, run) if final_round and not a.complete and task == "waelder" else None
col_a, col_b = st.columns(2)
with col_a:
    st.plotly_chart(build_graph(net, groups["groups"], groups["unassigned"], groups["halo"], edge_text=path_text, node_class=node_class), width="stretch", key="map_round")
    st.caption(
        "Dicke Linien: die Teile I1, I2, … (je eine Farbe), rot gestrichelt: noch nicht untergebracht, orange unterlegt: der Verbesserungsweg (Zahlen: Reihenfolge)."
        + (" Standortfarben: die Zusammenhangskomponenten der erreichbaren Menge R." if node_class is not None else "")
    )
with col_b:
    st.markdown("**Die Leitungen in dieser Runde**")
    st.dataframe(round_rows(a, run, r_idx), hide_index=True, width="stretch")

if st.button("📄 PDF des aktuellen Beispiels erstellen", key="pdf_make"):
    st.session_state["pdf_made"] = (settings, build_pdf(a, settings))
made = st.session_state.get("pdf_made")
if made and made[0] == settings:
    st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="matroid-vereinigung.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viele disjunkte Strukturen passen in ein Netz?")
kind_v, text_v = verdict_round(a, run, r_idx)
getattr(st, kind_v)(text_v)
if final_round:
    kind_v, text_v = verdict_final(a)
    getattr(st, kind_v)(text_v)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Kantendisjunkte Spannbäume packen")
st.caption("Für k = 1, 2, … so viele Wälder packen, wie das Partitionsverfahren findet: Sind alle k Wälder Spannbäume? Dazu die Formel von Tutte und Nash-Williams (Minimum über alle Partitionen der Standorte).")
tv = _trees(graph_only)
st.dataframe(trees_rows(tv), hide_index=True, width="stretch")
if tv["cert"] is not None:
    t1, t2 = st.columns(2)
    with t1:
        part = tv["cert"]["partition"]
        crossing = [e for e, (u, w) in enumerate(net.edges) if part[u] != part[w]]
        inside = [e for e in range(len(net.edges)) if e not in crossing]
        st.plotly_chart(build_graph(net, [("zwischen den Klassen", crossing, C.COLOR_UNASSIGNED), ("innerhalb der Klassen", inside, C.COLOR_OTHER)], node_class=part, height=330), width="stretch", key="map_tutte")
        st.caption("Die Partition, an der es scheitert (Standortfarben = Klassen); rot: die Leitungen zwischen den Klassen.")
    with t2:
        st.markdown(
            f"**Die Zahlen der Partition:** {tv['cert']['classes']} Klassen, {tv['cert']['cross']} Leitungen dazwischen; "
            f"für {tv['cert']['k']} Spannbäume wären {tv['cert']['k'] * (tv['cert']['classes'] - 1)} nötig."
        )
kind_v, text_v = verdict_trees(a, tv)
getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 2: Arboricity")
st.caption("Alle Leitungen auf k Wälder verteilen: die kleinste mögliche Zahl k. Dazu die Formel von Nash-Williams (Maximum über alle Knotenmengen).")
av = _arb(graph_only)
st.dataframe(arb_rows(a, av), hide_index=True, width="stretch")
if av["cert"] is not None:
    cert = av["cert"]
    inside_nodes = set(cert["nodes"])
    st.plotly_chart(build_graph(net, [("in der zu dichten Knotenmenge", cert["edges"], C.COLOR_UNASSIGNED)], node_class=[1 if v in inside_nodes else 0 for v in range(net.n)], height=330), width="stretch", key="map_arb")
    st.caption(f"Die zu dichte Knotenmenge für k = {cert['k']} (orange gefärbte Standorte, rote Leitungen).")
kind_v, text_v = verdict_arb(a, av)
getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 3: Wald ∨ Farbregel")
st.caption("Zwei verschiedene Matroide: ein Wald und die Farbregel (höchstens eine Leitung je Farbe). Der Rang der Vereinigung ist das Minimum über alle Mengen Y; das Verfahren findet ein Y, das es erreicht.")
mv = _mix(Settings(settings.n, settings.seed, graph, "farben", 2, settings.c))
mg = mix_groups(mv)
colors = edge_colors(net, settings.seed, settings.c)
st.plotly_chart(build_graph(net, mg["groups"], mg["unassigned"], edge_text={e: f"F{colors[e] + 1}" for e in range(len(net.edges))}, height=330), width="stretch", key="map_mix")
st.caption("Beschriftung: die Kabelfarbe der Leitung (F1, F2, …).")
kind_v, text_v = verdict_mix(mv)
getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 4: Alle kleinen Paare und die Reduktion auf den Schnitt")
st.caption("Alle Paare von Matroiden auf 1 bis 5 Elementen (bei 5 eine Stichprobe): Rangformel, Vereinigung ist ein Matroid, Verfahren = Rang, Zertifikat, und die Reduktion auf den Schnitt mit ihren Orakelaufrufen.")
if st.button("📊 Alle Paare bis 5 Elemente prüfen", key="small_run"):
    st.session_state["small_done"] = True
if st.session_state.get("small_done"):
    rows, red = _small()
    st.dataframe(small_table(rows, red), hide_index=True, width="stretch")
    kind_v, text_v = verdict_small(rows, red)
    getattr(st, kind_v)(text_v)

st.subheader("🔬 Messreihe: Pläne mit 6 bis 8 Standorten")
st.caption("20 Pläne je Größe (Seeds 0 bis 19): Wie oft gibt es zwei kantendisjunkte Spannbäume, und welche Arboricity haben die Pläne?")
if st.button("📊 Messreihe über 20 Pläne je Größe", key="series_run"):
    st.session_state["series_done"] = True
if st.session_state.get("series_done"):
    srows = _series()
    st.dataframe(series_table(srows), hide_index=True, width="stretch")
    kind_v, text_v = verdict_series(srows)
    getattr(st, kind_v)(text_v)

st.markdown("---")

# --- Spielwiese ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🛠️ Spielwiese: Eine eigene Leitungsmenge zerlegen")
st.caption("Wählen Sie Leitungen. Die App prüft mit dem Partitionsverfahren (k Wälder, k wie in der Seitenleiste), ob sie sich auf k Wälder verteilen lassen; wenn nicht, zeigt sie die zu dichte Knotenmenge.")
sel = st.multiselect("Leitungen", list(range(a.m)), default=list(range(a.m)), key=f"play_{play_id}", format_func=lambda x: a.labels[x])
pv = _play(settings, sum(1 << x for x in sel))
kind_v, text_v = verdict_play(a, pv)
getattr(st, kind_v)(text_v)
if sel:
    owner = pv["owner"]
    pgroups = [(f"Wald {j + 1}", [e for e in sel if owner[e] == j], C.FOREST_COLORS[j % len(C.FOREST_COLORS)]) for j in range(settings.k)]
    punassigned = [e for e in sel if owner[e] < 0]
    dense = pv["dense"]
    pclass = [1 if v in set(dense["nodes"]) else 0 for v in range(net.n)] if dense is not None and not pv["complete"] else None
    st.plotly_chart(build_graph(net, pgroups, punassigned, node_class=pclass, height=330), width="stretch", key="map_play")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist (wer setzt an) |
|---|---|
| **Matroide mit Orakel, kleine Grundmenge** | Optimum, Rangformel und Zertifikat werden aus Tabellen aller Teilmengen berechnet (höchstens 16 Leitungen); die Orakelaufrufe zählen Fragen an Tabellen, nicht Rechenzeit. Bei großen Netzen genügt ein Orakel für „ist die Menge ein Wald?“. **(nicht in dieser Reihe)** |
| **Ungewichtet** | Hier zählt jede Leitung gleich. Mit Kosten braucht man den gewichteten Schnitt aus Stück 8; die Reduktion auf die Grundmenge E × {1, …, k} bleibt dieselbe, dieses Stück rechnet sie nicht mit Kosten durch. **(nicht in dieser Reihe)** |
| **Ungerichtet** | Gerichtete Leitungen (Arboreszenzen, kantendisjunkte Wege) brauchen einen Schnitt statt einer Vereinigung (Stück 7). **(Stück 7)** |
| **Matroide als Eingabe** | Die Vereinigung ist ein Matroid, aber ihr Orakel ist teuer: jede Frage „ist I unabhängig?“ ist selbst ein Lauf des Partitionsverfahrens. **(nicht in dieser Reihe)** |
| **Das Beispiel ist klein und zufällig** | Anteile und Aufrufe gelten für den gezeigten Plan und die Seeds der Messreihe (0 bis 19), nicht allgemein. **(nicht allgemein)** |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben** Matroide $M_1 = (E, \mathcal{I}_1), \dots, M_k = (E, \mathcal{I}_k)$ mit Rangfunktionen $r_1, \dots, r_k$. Die **Vereinigung** $M_1 \vee \dots \vee M_k$ hat die unabhängigen Mengen $\{I_1 \cup \dots \cup I_k : I_j \in \mathcal{I}_j\}$.

| Symbol | Bedeutung |
|---|---|
| $r(X)$ | Rang der Vereinigung für $X \subseteq E$ |
| $D$ | Austauschgraph zur Zerlegung $(I_1, \dots, I_k)$ auf $E$ |
| $(x, y)$ | Pfeil für $y \in I_j$, $x \notin I_j$ mit $I_j - y + x \in \mathcal{I}_j$ |
| $R$ | die von den nicht untergebrachten Elementen aus erreichbaren Elemente |

**Rangformel.** Die Vereinigung ist ein Matroid mit
$$r(X) = \min_{Y \subseteq X} \Big( \lvert X \setminus Y \rvert + \sum_{j=1}^{k} r_j(Y) \Big).$$

**Partitionsverfahren.** Ein kürzester Weg von einem nicht untergebrachten Element zu einem Element, das ohne Tausch in ein $M_j$ passt, vergrößert die Zahl der untergebrachten Elemente um 1. Gibt es keinen Weg mehr, gilt für $R$: $\lvert E \setminus R \rvert + \sum_j r_j(R)$ ist gleich der Zahl der untergebrachten Elemente; weil nach der Rangformel jede zerlegbare Menge höchstens diesen Wert hat, ist das der Rang.

**Graphen.** Für $M_1 = \dots = M_k$ das Waldmatroid: Ein Graph hat $k$ kantendisjunkte Spannbäume genau dann, wenn jede Partition $\mathcal{P}$ der Knoten mindestens $k\,(\lvert\mathcal{P}\rvert - 1)$ Kanten zwischen den Klassen hat (Tutte, Nash-Williams). Seine Kanten lassen sich in $k$ Wälder zerlegen genau dann, wenn jede Knotenmenge $U$ höchstens $k\,(\lvert U \rvert - 1)$ Kanten in sich hat (Nash-Williams). Die Arboricity ist $\max_U \lceil \lvert E(U) \rvert / (\lvert U \rvert - 1) \rceil$.

**Reduktion auf den Schnitt ($k = 2$).** Grundmenge $E \times \{1, 2\}$; $M_A$: Kopie $j$ in $M_j$ unabhängig; $M_B$: jedes Element in höchstens einer Kopie. Die größte gemeinsame unabhängige Menge von $M_A$ und $M_B$ hat $r(E)$ Elemente.

**Literatur.** Die Formeln für Spannbäume, Überdeckung und den Rang der Vereinigung stehen in Kaisers Kurzbeweis (arXiv 0911.2809) und in Vorlesungsnotizen von Goemans (MIT, 18.438, Vorlesung 13); schnelle Verfahren (Matroid-Partition in nahezu linearer Zeit) bei Blikstad, Mukhopadhyay, Nanongkai und Tu, STOC 2023, nicht nachgebaut (Quelle: Websuche, Auszüge, nicht gegen die Primärtexte geprüft; Standardwerk: Schrijver, *Combinatorial Optimization*, Kap. 42, nicht eingesehen). Die Zuschreibung der Rangformel an einzelne Autoren ist hier nicht belegt; die Zertifikate aus der erreichbaren Menge sind hergeleitet und an allen kleinen Paaren und Plänen nachgerechnet.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
