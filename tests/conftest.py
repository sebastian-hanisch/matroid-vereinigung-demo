"""Gemeinsame Fixtures: kleine Beispiele, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mvg_algorithm import graphic_table, partition_table  # noqa: E402


@pytest.fixture
def dreieck():
    """Dreieck a, b, c = (0,1), (1,2), (0,2) auf 3 Knoten. Ein Wald hat höchstens 2 Kanten; zwei Wälder nehmen alle 3 auf (Arboricity 2); ein Spannbaum, keine zwei kantendisjunkten (3 < 2 · 2)."""
    return 3, [(0, 1), (1, 2), (0, 2)], graphic_table(3, [(0, 1), (1, 2), (0, 2)])


@pytest.fixture
def vierzyklus_mit_diagonale():
    """K4 minus eine Kante: 5 Kanten auf 4 Knoten (0–1, 1–2, 2–3, 3–0, 0–2). Zwei kantendisjunkte Spannbäume bräuchten 6 Kanten; Arboricity 2 (5 ≤ 2 · 3)."""
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
    return 4, edges, graphic_table(4, edges)


@pytest.fixture
def farben_beispiel():
    """Dreieck a, b, c mit den Farben 0, 0, 1: Wald ∨ Farbregel (höchstens eine Kante je Farbe). Alle 3 Kanten sind zerlegbar: Wald {a, b}, Farbregel {c}."""
    return 3, [(0, 1), (1, 2), (0, 2)], [0, 0, 1], graphic_table(3, [(0, 1), (1, 2), (0, 2)]), partition_table(3, [0, 0, 1])
