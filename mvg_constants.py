"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

import itertools
import math

N_MIN, N_MAX, DEFAULT_N = 6, 9, 7           # Standorte inklusive Depot (Knoten A); bis 9 (16 mögliche Leitungen)
SEED_MAX, DEFAULT_SEED = 999999, 8
HUB_FACTOR = 0.4                            # nur vom Plan-Erzeuger gebraucht (keine Nabe in dieser Demo)
COST_SCALE = 100                            # nur vom Plan-Erzeuger gebraucht
K_MIN, K_MAX, DEFAULT_K = 1, 4, 2           # Zahl der Wälder
C_MIN, C_MAX, DEFAULT_C = 2, 8, 6           # Zahl der Kabelfarben (Aufgabe „Wald und Farbregel“)
ENUM_MAX_N = 5                              # alle Paare von Matroiden bis zu so vielen Elementen aufzählen
PAIR_SAMPLE = 2500                          # Experiment 4: bei 5 Elementen Rangformel, Matroid und Verfahren an so vielen Zufallspaaren
REDUCTION_SAMPLE = 600                      # und die Reduktion auf den Schnitt an so vielen
PLAY_SEED = 20261111
SERIES_N = (6, 7, 8)
SERIES_SEEDS = 20

GRAPHS = ("plan", "k4", "k5", "k6", "k33")
GRAPH_NAMES = {
    "plan": "Leitungsnetz (Plan)",
    "k4": "K4 (4 Standorte, 6 Leitungen)",
    "k5": "K5 (5 Standorte, 10 Leitungen)",
    "k6": "K6 (6 Standorte, 15 Leitungen)",
    "k33": "K3,3 (6 Standorte, 9 Leitungen)",
}
TASKS = ("waelder", "farben")
TASK_NAMES = {
    "waelder": "k Wälder (Spannbäume packen, Überdeckung)",
    "farben": "Wald ∨ Farbregel (zwei verschiedene Matroide)",
}


def _circle(n, r=0.38):
    return tuple((0.5 + r * math.cos(2 * math.pi * i / n + math.pi / 2), 0.5 + r * math.sin(2 * math.pi * i / n + math.pi / 2)) for i in range(n))


FIXED_POINTS = {
    "k4": ((0.15, 0.15), (0.85, 0.15), (0.85, 0.85), (0.15, 0.85)),
    "k5": _circle(5),
    "k6": _circle(6),
    "k33": ((0.15, 0.2), (0.15, 0.5), (0.15, 0.8), (0.85, 0.2), (0.85, 0.5), (0.85, 0.8)),
}
FIXED_EDGES = {
    "k4": tuple(itertools.combinations(range(4), 2)),
    "k5": tuple(itertools.combinations(range(5), 2)),
    "k6": tuple(itertools.combinations(range(6), 2)),
    "k33": tuple((a, b) for a in range(3) for b in range(3, 6)),
}

COLOR_NODE = "#4c78a8"
COLOR_DEPOT = "#f0a30a"
COLOR_PATH = "#f0a30a"                      # Halo um den Verbesserungsweg
COLOR_UNASSIGNED = "#c0392b"                # nicht untergebrachte Leitungen
COLOR_OTHER = "rgba(150,150,150,0.55)"
FOREST_COLORS = ("#2F6B65", "#4c78a8", "#9467bd", "#8c564b")
COLOR_CLASS = ("#4c78a8", "#1b9e77", "#9467bd", "#d95f02", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf")
PALETTE = ("rgba(200,60,60,0.55)", "rgba(60,150,80,0.55)", "rgba(70,110,200,0.55)", "rgba(200,150,40,0.55)", "rgba(150,80,180,0.55)", "rgba(40,170,170,0.55)",
           "rgba(170,100,60,0.55)", "rgba(120,120,120,0.55)")

TWO_TREE_SEED = 3                           # Plan mit 6 Standorten, auf dem es zwei kantendisjunkte Spannbäume gibt (gefunden mit dem Partitionsverfahren, Seeds 0 bis 39)

PRESETS = {
    "Standardfall (Voreinstellung)": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "graph": "plan", "task": "waelder", "k": DEFAULT_K, "c": DEFAULT_C},
    "Zwei Spannbäume": {"n": N_MIN, "seed": TWO_TREE_SEED, "graph": "plan", "task": "waelder", "k": 2, "c": DEFAULT_C},
    "K4: zwei Bäume": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "graph": "k4", "task": "waelder", "k": 2, "c": DEFAULT_C},
    "K5: drei Wälder": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "graph": "k5", "task": "waelder", "k": 3, "c": DEFAULT_C},
    "Wald und Farbregel": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "graph": "plan", "task": "farben", "k": 2, "c": 4},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "Das Leitungsnetz (7 Standorte, 12 Leitungen) auf zwei Wälder verteilen: Es gibt nur einen kantendisjunkten Spannbaum (zwei Spannbäume ohne gemeinsame Leitung gibt es nicht), das Verfahren zeigt eine Partition, die die Bedingung von Tutte verletzt.",
    "Zwei Spannbäume": "Ein Plan mit 6 Standorten, dessen 10 Leitungen genau zwei kantendisjunkte Spannbäume bilden.",
    "K4: zwei Bäume": "Der vollständige Graph auf 4 Knoten: zwei kantendisjunkte Spannbäume, die zusammen alle 6 Leitungen enthalten.",
    "K5: drei Wälder": "K5 (10 Leitungen): nur zwei Spannbäume, aber alle Leitungen passen auf drei Wälder (Arboricity 3).",
    "Wald und Farbregel": "Vereinigung zweier verschiedener Matroide: ein Wald und eine Farbregel (höchstens eine Leitung je Farbe, 4 Farben).",
}
