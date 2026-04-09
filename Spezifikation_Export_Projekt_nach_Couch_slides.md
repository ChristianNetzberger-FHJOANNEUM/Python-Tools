# Spezifikation: Projekt-Bewertung → Couch in `slides.json` beim Export

**Status:** Festgelegt zur Implementierung (Entwurf für Abnahme).  
**Bezug:** `Spezifikation_Export_EXIF_und_GalerieRatings.md`, `photo_tool/actions/export.py` (`export_gallery`, `_merge_couch_from_existing_slides_json`), `photo_tool/projects/project_sidecar.py`, `gui_poc` Export-Modal + `POST /api/export/gallery`.

---

## 1. Ziel

Beim **Slideshow-/Galerie-Export** aus einem **Projekt** soll optional der **Projekt-Arbeitsstand** (Sterne und Farbe in der **Projekt-Ebene**) als **Startwert** in die Felder **`couch_rating`** / **`couch_color`** der **`slides.json`** (und damit in das eingebettete `photos`-JSON der `index.html`) übernommen werden können.

**Nutzen:** Bequem am PC im Projekt bewerten, danach am **TV mit Remote** auf derselben **Couch-Ebene** weitermachen, ohne manuell dieselben Sterne erneut setzen zu müssen. Bestehende **NAS-Couch-Werte** sollen nur dann berührt werden, wenn der Anwender das **explizit** wählt (siehe Modi).

---

## 2. Begriffe

| Begriff | Bedeutung |
|--------|-----------|
| **Projekt-Sterne / -Farbe** | Die für **Bewertungsebene „Projekt“** gültigen Werte: aus Projekt-Sidecar (`rating`, `color`), mit derselben **Semantik** wie `ProjectSidecarManager.merge_metadata(..., active_rating_layer=project)` für Sterne und Farbe (Projekt-Override gesetzt → Projekt; sonst Fallback auf Archiv/global wie im Tool). |
| **Couch in `slides.json`** | `couch_rating`, `couch_color` pro Slide; werden vom **Slideshow-Hub** / Remote geändert und sind die **Galerie-Session-Ebene**. |
| **Merge (bestehend)** | `_merge_couch_from_existing_slides_json`: übernimmt **`couch_*`** aus einer bereits vorhandenen **`slides.json`** im Zielordner anhand **`source_path`**. |

---

## 3. Datenquelle für die Übernahme

- Pro exportiertem Bild: **`photo_path`** (wie heute).
- Wenn die Option aktiv ist und ein **Projekt-Kontext** vorliegt (`project_id` → Projektverzeichnis):  
  **`ProjectSidecarManager(project_dir).merge_metadata(get_metadata(photo_path), photo_path, active_rating_layer=project)`**  
  Daraus für die Spezifikation relevant:
  - **Sterne:** Ergebnisfeld **`rating`** (ganzzahlig 0–5, nach Merge-Regeln Projekt-Ebene).
  - **Farbe:** Ergebnisfeld **`color`** (erlaubte Label wie heute im Tool, oder `null`/keine Farbe).

**Hinweis:** `couch_rating` / `couch_color` **im Projekt-Sidecar** sind **nicht** die Quelle dieses Features — es geht um den **Projekt-Arbeitsstand**, nicht um bereits importierte Couch-Werte im Sidecar.

---

## 4. Schreibziel

- In **`photo_entry`** und **`slides_manifest`** (wie in `_slide_manifest_entry`):  
  **`couch_rating`**, **`couch_color`** gemäß gewähltem Modus (Abschnitt 5).
- **`rating`** / **`color`** (Archiv-Snapshot in `slides.json`) bleiben von dieser Option **unberührt**; sie werden weiter wie heute aus den bisherigen Export-Metadaten gefüllt.

---

## 5. Modi (`project_to_couch_mode`)

Frei textlich in UI; technisch ein Enum-String:

| Wert | Bezeichnung UI (Vorschlag) | Verhalten |
|------|-----------------------------|-----------|
| `off` | *Aus* (Standard) | Keine Änderung gegenüber heute: nach Merge ist `couch_*` wie bisher (aus alter `slides.json` oder `null`). |
| `fill_empty` | *Nur leere Couch-Felder füllen* | Nach **`_merge_couch_from_existing_slides_json`**: für jeden Slide, bei dem **`couch_rating`** fehlt bzw. **`null`** ist (und analog **`couch_color`** wenn kein gesetzter Couch-Farbwert), **Projekt-Sterne/-Farbe** in `couch_*` schreiben. Bereits gesetzte **NAS-Couch-Werte** bleiben erhalten. |
| `replace_all` | *Projekt überschreibt Couch in dieser Galerie* | Nach Merge: für **alle** exportierten Slides **`couch_rating`** und **`couch_color`** aus der Projekt-Ebene setzen (**bestehende Couch-Werte aus alter `slides.json` gehen für diese Felder verloren**). |

**Reihenfolge im Export (verbindlich):**

1. Wie heute: `photo_data` / `slides_manifest` aufbauen (inkl. `rating`/`color` aus bisheriger Logik, `couch_*` zunächst `null` wo zutreffend).
2. **`_merge_couch_from_existing_slides_json(...)`** ausführen (NAS-Couch bleibt erhalten, sofern Datei und `source_path` passen).
3. Wenn `project_to_couch_mode != off` **und** gültiger Projekt-Kontext: **`apply_project_to_couch_seed(...)`** gemäß Modus `fill_empty` oder `replace_all`.
4. HTML / `slides.json` schreiben wie heute.

Damit gibt es **keine parallelen konkurrierenden Schritte**; Konflikte sind durch den Modus aufgelöst.

---

## 6. Projekt-Kontext und API

- Die Option ist nur sinnvoll, wenn der Export **aus einem Projekt** erfolgt.  
- **`POST /api/export/gallery`** erhält optional:
  - **`project_id`** (String, Pflicht **wenn** `project_to_couch_mode` ≠ `off`),  
  - **`project_to_couch_mode`**: `off` \| `fill_empty` \| `replace_all` (Default: `off`).

**Validierung:**

- Wenn `project_to_couch_mode !== off` und kein `project_id` oder Projekt nicht ladebar → **400** mit klarer Meldung.
- Unbekannter Modus → **400**.

**`export_gallery`-Signatur (Erweiterung):**

```text
project_dir: Optional[Path] = None
project_to_couch_mode: Literal["off", "fill_empty", "replace_all"] = "off"
```

- `project_dir` wird vom Server aus `project_id` aufgelöst und nur gereicht, wenn die Option aktiv ist (oder immer durchreichen, Funktion ignoriert bei `off` — Implementierungsdetail).

---

## 7. Export-Modal (GUI)

- Gruppe nur anzeigen, wenn **ein Projekt ausgewählt** ist und Template **Slideshow** (bzw. sobald `slides.json` erzeugt wird — bei „nur photoswipe“ ohne Manifest die Gruppe ausblenden oder deaktivieren).
- **Checkbox oder Radio:**
  - Standard: **Aus**.
  - **„Couch-Startwerte aus Projekt übernehmen“** mit Unteroptionen:
    - *Nur wo Couch noch leer* (`fill_empty`) — **empfohlener Default** bei aktivierter Checkbox.
    - *Alle Couch-Werte im Export ersetzen* (`replace_all`) — mit **kurzem Warnhinweis** („überschreibt bestehende TV/Remote-Bewertungen in dieser `slides.json`“).

Optional: Tooltip mit Verweis auf **Reihenfolge Merge → Seed**.

---

## 8. Randfälle

| Fall | Erwartung |
|------|-----------|
| Kein Projekt-Sidecar für ein Bild | `merge_metadata` liefert effektiv Archiv-Sterne/-Farbe; diese werden im Modus `fill_empty`/`replace_all` wie spezifiziert nach `couch_*` übernommen, sofern die Modusbedingung greift. |
| Neu exportiert in **leeren** Ordner | Kein Merge; Seed füllt `couch_*` gemäß Modus (bei `replace_all` alle mit Projekt-Sicht). |
| **`quick_update`** | Gleiche Reihenfolge Schritt 2–3; Manifest und Option gelten wie bei vollem Export. |
| **Abweichende `source_path`** nach Verschieben | Wie heute: Merge trifft nicht; Seed kann trotzdem `couch_*` setzen — Anwender soll wissen, dass NAS-Historie ggf. nicht gemerged wurde. |

---

## 9. Sicherheit und Transparenz

- Keine stillen Schreibzugriffe auf **Original-Sidecars**; nur **`slides.json`** / eingebettetes JSON im Exportordner.
- Modus **`replace_all`** bewusst **destruktiv** für **Couch in dieser Galerie** → UI-Warnung; kein Default.
- **`fill_empty`** ist **sanft**: typischer Workflow „PC vorsortieren, Couch am TV neu beginnen oder ergänzen“.

---

## 10. Nicht-Ziele

- Kein automatischer Sync zurück ins Photo Tool.
- Keine Änderung am Hub-Protokoll.
- Keine Übernahme der **Couch-Ebene** (`couch_rating` im Sidecar) als Quelle für dieses Feature (nur **Projekt-Ebene**).

---

## 11. Abnahmekriterien

1. Export mit `off`: Byte-für-Byte gleiches Couch-Verhalten wie vor dem Feature (bei gleicher Eingabe).
2. Export mit `fill_empty` + bestehende `slides.json` mit teilweise Couch: nur **fehlende** `couch_rating`/`couch_color` werden aus Projekt-Sicht gesetzt.
3. Export mit `replace_all`: alle Slides in neuer `slides.json` haben `couch_*` = Projekt-Sicht; alte NAS-Couch-Werte aus Merge **nicht** mehr vorhanden (außer sie identisch zur Projekt-Sicht).
4. Ohne `project_id` und Modus ≠ `off`: API-Fehler, kein halbfertiger Export.
5. Dokumentation der Option in Kurzform in **Export-Hilfe** oder bestehendem Export-Doku-Abschnitt (nach Implementierung).

---

*Ende der Spezifikation.*
