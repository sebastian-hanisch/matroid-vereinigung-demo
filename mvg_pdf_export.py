"""PDF-Export des aktuellen Beispiels (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import mvg_constants as C
from mvg_evaluation import Analysis, Settings, elemente, run_view, verdict_final, verdict_round

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "€": "EUR", "„": '"', "“": '"', "×": "x", "≈": "~", "∖": "\\", "∩": "n", "∪": "u", "∨": "v", "∅": "{}", "½": "1/2", "₁": "1", "₂": "2", "²": "2", "Σ": "Summe", "⌊": "[", "⌋": "]"}


def _s(text) -> str:
    out = str(text).replace("**", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: Analysis, settings: Settings) -> bytes:
    run = run_view(settings)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Matroid-Vereinigung"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    net = C.GRAPH_NAMES[settings.graph] + (f", {settings.n} Standorte, Plan-Seed {settings.seed}" if settings.graph == "plan" else "")
    task = C.TASK_NAMES[settings.task] + (f", k = {settings.k}" if settings.task == "waelder" else f", {settings.c} Farben")
    pdf.multi_cell(0, 5, _s(f"{net}; {elemente(a.m)}. Aufgabe: {task}. Untergebracht: {a.size} von {a.m}; Rangformel {a.formula}; Zertifikat {a.certificate}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, _s("Lauf des Partitionsverfahrens"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for i in range(len(run["rounds"])):
        pdf.multi_cell(0, 5, _s(verdict_round(a, run, i)[1]), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    pdf.multi_cell(0, 5, _s(verdict_final(a)[1]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: matroid-vereinigung-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
