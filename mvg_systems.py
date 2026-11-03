"""Die Netze der Demo: das Leitungsnetz (Plan) und feste Graphen (K4, K5, K6, K3,3); Tabellen der Matroide (Wald, Farbregel) auf den Leitungen."""

import random
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import mvg_constants as C
from mvg_algorithm import graphic_table, partition_table
from mvg_scenario import LETTERS, Instance, make_instance


@dataclass(frozen=True)
class Net:
    key: str
    n: int                      # Zahl der Standorte
    edges: tuple                # ((u, v), …), Position = Nummer der Leitung
    labels: tuple               # Name je Leitung
    inst: Instance              # Standorte und Leitungen für die Zeichnung


def build_net(graph: str, n: int, seed: int) -> Net:
    if graph == "plan":
        inst = make_instance(n, seed)
        return Net(graph, inst.n, tuple((u, w) for u, w, _ in inst.edges), tuple(inst.label(e) for e in range(inst.m)), inst)
    if graph not in C.FIXED_EDGES:
        raise ValueError(f"unbekanntes Netz: {graph}")
    edges = C.FIXED_EDGES[graph]
    points = C.FIXED_POINTS[graph]
    inst = Instance(tuple(points), tuple((u, w, 0) for u, w in edges))
    return Net(graph, len(points), tuple(edges), tuple(f"{LETTERS[u]}–{LETTERS[w]}" for u, w in edges), inst)


@lru_cache(maxsize=24)
def _cached_net(graph: str, n: int, seed: int) -> Net:
    return build_net(graph, n, seed)


def get_net(graph: str, n: int, seed: int) -> Net:
    """Gleiches Netz für gleiche Eingaben; bei festen Graphen zählen n und der Seed nicht für das Netz (die Farben hängen dort vom Seed ab, nicht das Netz)."""
    if graph != "plan":
        n, seed = 0, 0
    return _cached_net(graph, n, seed)


@lru_cache(maxsize=24)
def forest_table(graph: str, n: int, seed: int) -> np.ndarray:
    net = get_net(graph, n, seed)
    return graphic_table(net.n, list(net.edges))


def edge_colors(net: Net, seed: int, c: int) -> list[int]:
    """Farbe (0 bis c − 1) je Leitung, deterministisch aus dem Seed."""
    rng = random.Random(seed * 31 + 7)
    return [rng.randrange(c) for _ in net.edges]


def color_table(net: Net, seed: int, c: int) -> np.ndarray:
    return partition_table(len(net.edges), edge_colors(net, seed, c))
