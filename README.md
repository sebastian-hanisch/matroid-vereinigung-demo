# Matroid-Vereinigung – disjunkte Strukturen packen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-matroid-vereinigung-demo.streamlit.app/)** -->

Neuntes Stück der Reihe **Matroide und Submodularität** (Bereich Kombinatorik) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Die Demo behandelt die **Vereinigung** von Matroiden: Eine Menge ist unabhängig, wenn sie sich in **k Teile zerlegen** lässt, von denen Teil j in Mj unabhängig ist. Anders als der Schnitt aus Stück 7 ist die Vereinigung **wieder ein Matroid**, mit einer Formel für den Rang. Auf dem Leitungsnetz heißt das: **k kantendisjunkte Spannbäume** (Tutte, Nash-Williams) und die kleinste Zahl von **Wäldern**, die alle Leitungen überdecken (die **Arboricity**). Gerechnet wird mit dem **Partitionsverfahren**: Ein kürzester Weg im Austauschgraphen bringt eine weitere Leitung unter, und wenn keiner mehr da ist, zeigt die erreichbare Menge ein **Zertifikat**. Man kann die Vereinigung auch auf den Schnitt aus Stück 7 zurückführen; die Demo misst bei Paaren mit höchstens 5 Elementen, dass die Reduktion in ihrer Zählweise mehr Orakelaufrufe braucht.

**Einordnung in die Reihe:** Nachfolger von [gewichteter-schnitt-demo](../gewichteter-schnitt-demo) (Stück 8), [matroid-schnitt-demo](../matroid-schnitt-demo) (Stück 7: Schnitt zweier Matroide, Austauschgraph), [dualmatroid-demo](../dualmatroid-demo) (Stück 6), [greedy-optimalitaet-demo](../greedy-optimalitaet-demo) (Stück 5), [rang-basen-kreise-demo](../rang-basen-kreise-demo) (Stück 4), [matroid-demo](../matroid-demo) (Stück 3), [unabhaengigkeitssystem-demo](../unabhaengigkeitssystem-demo) (Stück 2) und [greedy-austausch-demo](../greedy-austausch-demo) (Stück 1). Stück 7 liefert den Austauschgraphen und die Reduktion; hier wird er für k Matroide gebaut, und die Vereinigung wird mit dem Schnitt verglichen.

## Warum dieses Problem

Wie viele **disjunkte** Strukturen passen in ein Netz? Zwei Spannbäume ohne gemeinsame Leitung (Ersatzweg, falls einer ausfällt), oder: Auf wie wenige Wälder lassen sich alle Leitungen verteilen? Beides ist eine Vereinigung von Matroiden, und die Antwort hat eine **Formel in beide Richtungen**: Entweder gibt es die Zerlegung, oder eine Partition der Standorte beziehungsweise eine Knotenmenge zeigt, warum nicht. Das Partitionsverfahren liefert beides.

## Befunde und Korrekturen gegenüber dem Plan

- **Zertifikat bei vollständiger Zerlegung:** Die erste Messung nahm bei einer Zerlegung aller Elemente R = E und fand das Zertifikat nur bei etwa 70 % der Fälle. Richtig: Sind alle untergebracht, gibt es keine Quellen, R = ∅ und |E ∖ R| + Σ rj(R) = |E|.
- **Der Plan 6 Standorte, Seed 0 hat keine zwei Spannbäume:** Das Preset „Zwei Spannbäume“ nimmt den ersten Plan mit 6 Standorten, auf dem es sie gibt (Seed 3, gefunden mit dem Partitionsverfahren).
- **Die Messreihe der App hat 20 Pläne je Größe** (Seeds 0 bis 19); die Messung vor dem Bau lief über 200 Pläne (bei 9 Standorten 40) mit denselben Aussagen.
- **Alle Paare bis 4 Elemente, bei 5 eine Stichprobe von 2 500 (Formel, Matroid, Verfahren, Zertifikat) beziehungsweise 600 (Reduktion).**
- **Port 9349;** Repo `matroid-vereinigung-demo`, Präfix `mvg_`; `networkx` nur in den Tests.

## Modell

**Vereinigung:** I ist in M1 ∨ … ∨ Mk unabhängig, wenn I = I1 ∪ … ∪ Ik mit Ij unabhängig in Mj. **Aufgabe „k Wälder“:** Mj ist das Waldmatroid (graphisches Matroid) des Netzes für alle j; eine Zerlegung ist ein Packen von k kantendisjunkten Wäldern. **Aufgabe „Wald ∨ Farbregel“:** M1 ist der Wald, M2 die Farbregel (höchstens eine Leitung je Kabelfarbe; Farben zufällig aus dem Seed). **Netze:** der Plan wie in den Stücken davor (n Standorte, Depot A in der Mitte, min(n(n − 1)/2, 2n − 2) mögliche Leitungen) und die festen Netze K4, K5, K6 und K3,3. Die Sätze stehen im Expander „📐 Mathematische Formulierung“ in der App (mit einer Skizze für das Zertifikat); ein vollständiger Beweis steht dort nicht.

## Methodik

- **Partitionsverfahren:** Austauschgraph auf den Leitungen: Pfeil x → y, wenn y im Teil Ij liegt und Ij − y + x in Mj unabhängig ist (`partition_steps`). Quellen sind die nicht untergebrachten Leitungen, Senken die Leitungen, die ohne Tausch in ein Mj passen; ein kürzester Weg (Breitensuche) lässt jede Leitung den Platz ihres Nachfolgers übernehmen.
- **Zertifikat:** R = von den nicht untergebrachten Leitungen aus erreichbar; |E ∖ R| + Σ rj(R) ist gleich der Zahl der untergebrachten (`certificate_value`). Bei Wäldern sind die Zusammenhangskomponenten von R eine Partition, die die Bedingung von Tutte verletzt (bei Spannbäumen), beziehungsweise eine zu dichte Knotenmenge (bei der Überdeckung).
- **Rangformel:** r(X) = Minimum über alle Y ⊆ X von |X ∖ Y| + Σ rj(Y), aus allen Teilmengen berechnet (`union_rank`).
- **Tutte und Nash-Williams:** Minimum über alle Partitionen der Standorte (bei 9 Standorten 21 147) und Maximum über alle Knotenmengen (`tutte_min`, `nash_williams`).
- **Reduktion auf den Schnitt (k = 2):** Grundmenge E × {1, 2}; M_A: Kopie 1 in M1, Kopie 2 in M2; M_B: jede Leitung in höchstens einer Kopie; größte gemeinsame Menge mit dem faulen Verfahren aus Stück 7 (`reduction_row`).
- **Alle kleinen Paare:** alle Paare beschrifteter Matroide mit 1 bis 4 Elementen und 2 500 Zufallspaare bei 5 für Rangformel, Matroid, Verfahren und Zertifikat; die Reduktion bei 600 Paaren mit 5 Elementen (`small_union_row`).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` und werden dort mit den Funktionen der App nachgerechnet. Plan: 7 Standorte, 12 mögliche Leitungen, Seed 8, Zerlegung in k = 2 Teile (außer wo anders angegeben).

| Beispiel | Leitungen | untergebracht | Orakelaufrufe | kantendisjunkte Spannbäume | Arboricity |
|---|---|---|---|---|---|
| Plan 7/8, zwei Wälder | 12 | 11 | 105 | 1 | 3 |
| Plan 6/3 („Zwei Spannbäume“), zwei Wälder | 10 | 10 | 35 | 2 | 2 |
| K4, zwei Wälder | 6 | 6 | 15 | 2 | 2 |
| K5, drei Wälder | 10 | 10 | 29 | 2 | 3 |
| Plan 7/8, Wald ∨ Farbregel mit 4 Farben | 12 | 10 | 116 | – | – |

| Frage | Befund |
|---|---|
| **Feste Netze** (kantendisjunkte Spannbäume / Arboricity) | K4: 2 / 2; K5: 2 / 3; K6: 3 / 3; K3,3: 1 / 2. Für K_n sind es ⌊n/2⌋ und ⌈n/2⌉; das Partitionsverfahren und die Formeln von Tutte und Nash-Williams geben dieselben Zahlen wie die Aufzählung aller kantendisjunkten Bäume beziehungsweise Wälder. |
| **Zertifikat auf dem Plan 7/8** (zwei Wälder) | Es gibt nur **1** kantendisjunkten Spannbaum (zwei Spannbäume ohne gemeinsame Leitung gibt es nicht): Eine Partition mit **3** Klassen hat nur **3** Leitungen zwischen den Klassen, für zwei Spannbäume wären **4** nötig. Die Arboricity ist **3**: Eine Knotenmenge mit **5** Standorten hat **9** Leitungen, zwei Wälder nehmen dort höchstens **8** auf. Beides kommt aus den Zusammenhangskomponenten der erreichbaren Menge R. |
| **Zertifikat bei K5 mit drei Wäldern** | Für drei Spannbäume scheitert es an der Partition in 5 Einzelklassen: **10** Leitungen dazwischen, gebraucht **12**. |
| **Wald ∨ Farbregel** | Plan 7/8 mit 6 Farben: **11** von 12 Leitungen (6 im Wald, 5 in der Farbregel), das Minimum über alle 4 096 Mengen Y wird bei **4** Mengen angenommen; mit 4 Farben: **10** (6 + 4), bei **2** Mengen. |
| **Alle kleinen Paare** (4, 25, 256, 4 624 und 2 500 bei 5 Elementen; zusammen **7 409**) | Die Rangformel gilt, die Vereinigung ist ein Matroid, das Partitionsverfahren findet den Rang und das Zertifikat stimmt bei **allen 7 409**. |
| **Reduktion auf den Schnitt** (4, 25, 256, 4 624 und 600 Paare; zusammen **5 509**) | Dieselbe Zahl bei **allen 5 509**. Orakelaufrufe je Paar direkt / über den Schnitt: 1 Element: 1,5 / 4,2; 2: 3,7 / 12,7; 3: 6,7 / 26,5; 4: 10,3 / 47,4; 5: 14,4 / 76,4. Bei 5 Elementen braucht die Reduktion in dieser Zählweise das **5,3-Fache** (Stichprobe von 600 Paaren). |
| **Messreihe** (20 Pläne je Größe, zwei Wälder) | Zwei Spannbäume haben bei 6 Standorten **10**, bei 7 **5**, bei 8 **1** der 20 Pläne; die Arboricity ist bei genau diesen Plänen 2, bei den übrigen 3. Orakelaufrufe im Mittel: 43, 72, 109. Bei 200 Plänen je Größe (Seeds 0 bis 199) sind es 128, 71, 33 mit zwei Spannbäumen; die Anteile der 20er-Reihe gelten nur für diese Pläne. |
| **Dreieck von Hand** | Ein Wald nimmt 2 der 3 Kanten auf, zwei Wälder alle 3 (Arboricity 2); zwei Spannbäume bräuchten 4 Kanten, es gibt nur 3 (1 kantendisjunkter Spannbaum). |

## Ehrliche Grenzen

- **Kleine Grundmengen.** Höchstens 16 Leitungen; Rangformel und Zertifikat kommen aus allen Teilmengen. Die Orakelaufrufe zählen Fragen an Tabellen, keine Rechenzeit. Bei großen Netzen genügt ein Orakel für „ist die Menge ein Wald?“, die Zahlen der Literatur sind andere.
- **Ungewichtet, ungerichtet.** Mit Kosten braucht man den gewichteten Schnitt aus Stück 8; gerichtete Strukturen (Arboreszenzen) brauchen den Schnitt aus Stück 7. Die Reduktion mit Kosten rechnet diese Demo nicht durch.
- **Das Orakel der Vereinigung ist teuer.** Jede Frage „ist I unabhängig?“ ist ein Lauf des Partitionsverfahrens; die Vereinigung ist ein Matroid, wird aber nicht als Tabelle gebaut, sondern bei jedem Aufruf neu gerechnet.
- **Beispiele auf wenigen Plänen.** Anteile und Aufrufe gelten für den Plan 7/8, die Presets und die Seeds 0 bis 19, nicht allgemein; die Paare mit 5 Elementen sind Stichproben (2 500 von 164 836 beziehungsweise 600 bei der Reduktion). Die Sätze stehen im Expander (mit einer Skizze für das Zertifikat); ein vollständiger Beweis steht dort nicht, und die Messung ersetzt ihn nicht.
- **Quellen nur als Auszüge** (Kaisers Kurzbeweis, arXiv 0911.2809; Vorlesungsnotizen von Goemans, MIT; Blikstad, Mukhopadhyay, Nanongkai, Tu, STOC 2023 für schnelle Verfahren; Websuche): Die Zuschreibung der Rangformel an einzelne Autoren ist nicht belegt, die Zertifikate aus der erreichbaren Menge sind hergeleitet und gemessen; das Standardwerk (Schrijver, *Combinatorial Optimization*, Kap. 42) ist nicht eingesehen.

## Verifikation

- **Kern:** Partitionsverfahren, Rangformel, Zertifikat, Tutte, Nash-Williams, Reduktion gegen Handrechnung am Dreieck, am Viereck mit Diagonale und an der Farbregel (`tests/conftest.py`, `tests/test_algorithm.py`); Randfälle: zwei Standorte, nicht zusammenhängender Graph, Schlinge, leere Grundmenge, Reglergrenzen, feste Netze, alle Zweige der Spielwiese (`tests/test_edge_cases.py`).
- **Orakel** (`tests/test_oracle_matroid_vereinigung.py`): Wälder mit `networkx.is_forest`; kantendisjunkte Spannbäume durch Aufzählung aller Bäume; Überdeckung durch Verzweigen über Wälder; größte zerlegbare Menge durch Aufzählung; Wald ∨ Farbregel als „bester Wald plus Zahl der übrigen Farben“; 125 Spannbäume des K5 (Cayley); bekannte Werte für K4, K5, K6, K3,3.
- **Eigenschaften** (`tests/test_properties.py`): das Verfahren findet den Rang, Zertifikat und Teile stimmen; jede Runde bringt genau eine Leitung mehr unter und nur der erste Knoten des Wegs ist nicht untergebracht; die Vereinigung ist ein Matroid; Reihenfolge und Umbenennen ändern den Rang nicht; uniforme Matroide addieren ihre Ränge; Vereinigung mit einem freien Matroid ist frei; schwache Dualität für jedes Y.
- **Verdikte und Presets:** jeder Zweig und jede Zahl der Verdikte an handgesetzten Werten; jedes Preset zeigt den versprochenen Effekt; kein einzelner Reglerwechsel trifft ein anderes Preset.
- **Zahlen aus dieser README:** `tests/test_claims.py`.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an den Grenzen), Hauptansicht, Experimente, Spielwiese, Permalink, PDF; Layout (Kopf, Schnellstart, Hervorhebung) und Footer.
- **Umfang:** siehe `pytest --collect-only -q tests`.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche: Partitionslauf, Kernfrage, vier Experimente und Messreihe, Spielwiese, Grenzen, Formeln |
| `mvg_constants.py` | Reglergrenzen, Netze und Aufgaben mit Namen, feste Graphen, Farben, Presets |
| `mvg_scenario.py` | Plan: Standorte, mögliche Leitungen (wie in den Stücken davor) |
| `mvg_algorithm.py` | Kern: Tabellen, Partitionsverfahren, Rangformel, Zertifikat, Tutte, Nash-Williams, Reduktion, alle kleinen Paare |
| `mvg_systems.py` | die Netze und Matroide (Wald, Farbregel) als Tabellen |
| `mvg_evaluation.py` | Kennzahlen, Ansichten der Experimente, Verdikte |
| `mvg_visualization.py` | Netz mit Teilen, Weg und Klassen; Balken |
| `mvg_presets.py` | Permalink, Presets, Zufalls-Seed |
| `mvg_layout.py` | fester Kopf |
| `mvg_pdf_export.py` | PDF des aktuellen Beispiels |
| `tests/` | Kern, Orakel, Eigenschaften, Verdikte, Presets, Claims, Randfälle, Oberfläche, Layout, Footer, Importe |

## Bewusst nicht umgesetzt

- Vereinigung mit Gewichten (kostenminimale Packung) und Stand der Forschung; das Polytop der Vereinigung (Stück 10).
- Das Orakel der Vereinigung als Tabelle über sehr große Grundmengen; Packung von Spannbäumen in großen Netzen mit schnellen Verfahren (nur Literaturhinweis).
- Gerichtete Packung (Arboreszenzen), Matroid-Parität.
- Erklärseite „verständlich erklärt“ und Website-Einbindung (erst mit der vollständigen Linie).

## Lokal ausführen

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt`, dann `python -m pytest tests -q`. Die CI läuft mit Python 3.12 (`.github/workflows/tests.yml`); die in Streamlit Cloud eingestellte Python-Version ist beim Deploy zu nennen.

Gebaut mit Streamlit, Plotly, numpy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
