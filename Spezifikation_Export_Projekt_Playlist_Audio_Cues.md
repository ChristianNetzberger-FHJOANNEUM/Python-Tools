# Spezifikation: Projekt-Playlist & Audio-Cues im Galerie-Export

**Status:** verbindlich für Photo-Tool-Export (`export_gallery`) und eingebettete Slideshow (`index.html`).  
**Bezug:** `Spezifikation_Slideshow_Audio_und_Lichtsteuerung.md` §5.5.1 (Erbe-Semantik für Hintergrund-Stem), `photo_tool/projects/playlist_folder.py`, `photo_tool/actions/export.py`.

---

## 1. Ziel

- Im Projekt unter `playlist/` liegen **Audiodateien** (stabile `track_id` in `.ids/`), **Reihenfolge** (`playlist_order.yaml` oder alphabetisch), und **sparse Audio-Cues** in `audio_cues.yaml`.
- Beim Export mit **Slideshow-Template** und gesetztem **Projekt** werden Tracks nach `galerie/playlist/<track_id>.<ext>` kopiert und **`audio_cues`** + **`playlist_tracks`** + **`light_cues`** in `slides.json` sowie im HTML eingebettet.
- Die **Laufzeit-Semantik** der Cues entspricht der **Stem-Erbe-Logik** aus der Slideshow-Spezifikation (§5.5.1), ausgedrückt als **kompakte Sparse-Liste** statt pro-Folie `music_track` bzw. `light_cue`.

---

## 2. Datenformate

### 2.1 Projekt: `playlist/audio_cues.yaml`

```yaml
cues:
  - at_slide: <int>    # siehe Abschnitt 3 (Projekt-Index)
    track_id: <uuid>
```

### 2.2 Projekt: `playlist/light_cues.yaml`

```yaml
cues:
  - at_slide: <int>    # Projekt-Index wie bei Audio (Abschnitt 3)
    effect_id: <str>   # z. B. Szene-Id für LAN-Gateway / QLC+ / Eigenbau
```

### 2.3 Export: `slides.json` (Auszug)

| Feld | Bedeutung |
|------|-----------|
| `playlist_tracks` | `[{ "track_id", "src", "filename" }, …]` — `src` relativ zur Galeriewurzel |
| `audio_cues` | `[{ "at_slide", "track_id" }, …]` — **Export-Index** (0-basiert), nach Remap (Abschnitt 4) |
| `light_cues` | analog `at_slide` nach Export-Index |

---

## 3. Zwei Index-Systeme

| Index | Bedeutung |
|--------|-----------|
| **Projekt-Folienindex** | Position in `projects/<id>.yaml` → `photo_ids` (ungefilterte Reihenfolge). |
| **Export-Folienindex** | Position in der **tatsächlich exportierten** Liste (`photo_paths` beim Export), 0 … N−1. |

**Regel:** In `audio_cues.yaml` und `light_cues.yaml` speichert das UI **Projekt-Indizes** (gleiche Reihenfolge wie der Media-Tab: `this.photos` / Manifest). Beim Export mappt `filter_cues_for_export` über **Pfadgleichheit** auf **Export-Indizes**: zuerst `projects/<id>.yaml` → `photo_ids`, falls leer (z. B. reines Filter-Projekt) die beim Export mitgesendete Liste **`manifest_photo_paths`** (vollständige Manifest-Pfade in Manifest-Reihenfolge) ↔ die exportierte Fotoliste. Fehlt die Folie im Export (Filter), entfällt der Cue mit Warnung.

### 3.1 Stabilität bei Filtern, neuen Ordnern und Re-Export

- **Anker ist die Bilddatei**, nicht die bloße Indexzahl: In `projects/<projekt>.yaml` verweist jeder Eintrag in `photo_ids` typischerweise auf einen **stabilen Pfad** (oder eine ID, die auf denselben Pfad zeigt). `build_project_index_to_export_index` ordnet jedem **Projekt-Index** den **Export-Index** zu, der dieselbe Datei in `photo_paths` trägt.
- **Sterne-/Farbfilter** ändern nur, **welche** Pfade exportiert werden. Ein Cue „an der dritten Projektfolie“ bleibt derselbe Pfad zugeordnet; nach dem Export sitzt er auf dem passenden **Export-**`at_slide`. Wird die Folie **herausgefiltert**, gibt es keinen Export-Index → Cue **verworfen** (Warnung), bewusst kein „Rutschen“ auf eine andere Folie.
- **Neue Medienordner / Sortierung nach Aufnahmedatum:** Solange sich die **Zuordnung photo_ids → Datei** nicht ungewollt ändert, bleiben Cues sinnvoll. Wird die Reihenfolge in `photo_ids` neu aufgebaut, **verschieben** sich Projekt-Indizes — Cues in YAML beziehen sich weiterhin auf **dieselbe Indexposition in der Liste**; der Nutzer sollte Cues dann anpassen oder über das GUI neu setzen. **Track-IDs** in `.ids/` bleiben pro Audiodatei stabil.
- **Re-Export** derselben Auswahl liefert dieselbe **Export-**`at_slide`-Zuordnung für Audio- und Licht-Cues, solange Projekt- und Export-Pfade zusammenpassen.

---

## 4. Effektiver Audio-Stem (verbindlich)

Entspricht **logisch** `Spezifikation_Slideshow_Audio_und_Lichtsteuerung.md` §5.5.1, wenn man jeden sparse Cue als „ab dieser Folie setzt sich `music_track` auf diese Datei“ interpretiert.

Für **Export-Folienindex** `j` (0-basiert):

1. Betrachte alle Cues mit `at_slide ≤ j` (bereits **Export-**`at_slide` nach Remap).
2. Der **geltende Cue** ist der mit **maximalem** `at_slide` (der **letzte** definierter Wechsel **vor oder auf** Folie `j`).
3. **Kein** Cue mit `at_slide ≤ j` → **kein** Stem aus der Projekt-Playlist für diese Folie (**Stille**, bis ein späterer Cue greift); kein automatischer Default-Track aus der Cue-Liste.

**Folienwechsel / Seek (Progress-Bar):** Bei jedem angezeigten Index `j` wird `effectiveTrack(j)` aus den Cues bestimmt. **Nur** wenn sich die **effektive** `track_id` / Quelle gegenüber dem **bereits laufenden** Stem **ändert**, werden Quelle gewechselt, `load()` + `play()` (idempotent wie §3 der Slideshow-Spezifikation: nur bei Änderung handeln).

**Zwischen zwei Cues:** Derselbe Stem bleibt aktiv (kein Stopp nur weil die aktuelle Folie keinen eigenen Cue-Eintrag hat).

**Mehrere Cues mit gleichem `at_slide`:** Es gilt der **letzte** verarbeitete Eintrag mit diesem Index (Normalisierung beim Speichern bevorzugt ohne Duplikate).

### 4.1 Effektiver Licht-Cue (verbindlich)

Gleiche Konstruktion wie in Abschnitt 4, mit `light_cues` und Feld **`effect_id`** statt `track_id`:

- `effectiveLight(j)` = Cue mit **maximalem** `at_slide ≤ j` aus der exportierten `light_cues`-Liste.
- **Kein** Licht-Cue mit `at_slide ≤ j` → effektiv **kein** Licht (`null` / leer); kein automatischer Default aus der Liste.
- **Wechsel nur bei neuer effektiver `effect_id`:** intern wird nur bei Änderung ein optionaler **HTTP-POST** ausgelöst (siehe Abschnitt 9).

---

## 5. Verwaiste Cues

- `at_slide` außerhalb 0 … N−1 nach Remap, oder `track_id` ohne kopierte Datei → Cue wird **verworfen**, im Export-Log und optional `cue_export_warnings` in `slides.json` dokumentiert (**keine** Übernahme auf „nächste“ Folie).

---

## 6. Implementierungsstand (Kurz)

| Teil | Status |
|------|--------|
| YAML laden / speichern, `track_id`, Export `playlist/` | umgesetzt |
| Projekt- → Export-Index-Remap (`filter_cues_for_export` + `photo_paths`) | umgesetzt |
| `slides.json` + HTML-Embed + optional `slides.json`-Fetch-Fallback | umgesetzt |
| **Effektiver Cue = max `at_slide ≤ j`** inkl. Seek (Progress-Bar) | umgesetzt in `export.py` → `effectiveAudioCueForSlide` + `applyProjectCueForSlide` |
| **Effektiver Licht-Cue = max `at_slide ≤ j`** | umgesetzt → `effectiveLightCueForSlide` + `applyLightCuesForSlide` |
| **Hub-`state` mit effektiven Cues** (LAN-Debug / später Bridge) | umgesetzt: `effective_audio_*`, `effective_light_*` |
| **Optional `?light_proxy=`** | POST JSON bei Licht-Wechsel an konfigurierbare URL (CORS beachten) |

---

## 7. Echtzeit-Performance (Sparse Cues)

**Kurz: praktisch kein messbarer Einfluss** auf die Slideshow-Performance.

- Die Laufzeitlogik ermittelt den effektiven Cue pro Folienwechsel/Seek durch einen **Scan über die sortierte Cue-Liste** (`audio_cues`), nicht über alle Folien. Die Komplexität ist **O(C)** mit **C = Anzahl Cues** (typisch klein, oft «20).
- **Sparse** bedeutet wenige Cues über viele Folien → **C klein** → der Scan ist vernachlässigbar gegenüber Bilddecodierung, Layout, Transitions und **Audio-`load()`** (Netzwerk/Disk), wenn überhaupt ein Track gewechselt wird.
- Zwischen zwei Cues ändert sich die effektive `track_id` nicht → **kein** erneutes Laden; nur Indexwechsel und ggf. UI-Updates.

Fazit: Sparse-Cues sind aus Performance-Sicht **unkritisch** und tendenziell **günstiger** als viele dicht gesetzte Cues (mehr Scan-Schritte, aber weiterhin trivial; mehr potenzielle Track-Wechsel wären teurer als der Scan).

---

## 8. Manuelle Tests (Export + Seek)

**Voraussetzung:** Galerie mit Slideshow exportiert, Projekt mit mindestens zwei Tracks und mindestens zwei Cues auf unterschiedlichen **Export-**Folienindizes. Optional: `?debug_cues=1` in der URL für Konsolen-Logs (`cueDiagSlideshowAudio`).

| # | Szenario | Erwartung |
|---|----------|-----------|
| 1 | **Vor den ersten Cue springen** (Progress-Bar auf Folie `j` mit `j < at_slide` des ersten Cues) | Stille bzw. kein Projekt-Stem, bis eine Folie erreicht wird, bei der ein Cue mit `at_slide ≤ j` existiert. |
| 2 | **Zwischen zwei Cues** (Folie ohne eigenen Eintrag, aber `j` liegt nach Cue A und vor Cue B) | Es läuft weiter der Track von **Cue A** (kein Stopp nur wegen „kein Cue auf dieser Folie“). |
| 3 | **Nach dem letzten Cue** | Der Stem des letzten Cues bleibt gültig, bis ein **anderer** effektiver Track durch Seek oder einen späteren (hier: nicht vorhandenen) Cue entstünde. |
| 4 | **Seek von (2) zu (1)** | Beim Sprung zurück vor den ersten Cue: Audio stoppt / Stille; beim erneuten Vorwärts ab erstem Cue: korrekter Track ohne „hängenden“ falschen Stem. |

Nach Änderungen am Export erneut **exportieren** und dieselben vier Fälle kurz durchklicken.

---

## 9. Licht-Cues in der Slideshow

- **Einbettung:** `EXPORT_LIGHT_CUES` in `index.html` (wie Audio), zusätzlich in `slides.json`; Fallback-Laden aus `slides.json`, wenn nur dort vorhanden (analog Audio).
- **Laufzeit:** siehe §4.1. Nach dem Splash-Start gelten Licht-Wechsel wie Audio pro **angezeigtem** Folienindex (inkl. Seek).
- **Hardware-Brücke:** Query-Parameter **`light_proxy=<URL>`** (vollständige URL). Bei **Änderung** der effektiven `effect_id` sendet die Slideshow `POST` mit JSON  
  `{ "effect_id": "<str|null>", "slide_index": <int>, "cue_at_slide": <int|null> }`.  Browser-CORS: Ziel muss die Anfrage erlauben oder über **gleiche Origin** / Reverse-Proxy erreichbar sein.

---

## 10. LAN: Cues und Slideshow-State debuggen

Der **Slideshow Hub** verteilt WebSocket-Nachrichten vom TV an alle Clients. Die TV-Slideshow ergänzt jede **`type: "state"`**-Nachricht um:

| Feld | Bedeutung |
|------|-----------|
| `effective_audio_track_id` | aktuelle effektive `track_id` oder `null` |
| `effective_audio_cue_at_slide` | `at_slide` des gewählten Audio-Cues oder `null` |
| `effective_light_effect_id` | aktuelle effektive `effect_id` oder `null` |
| `effective_light_cue_at_slide` | `at_slide` des gewählten Licht-Cues oder `null` |

**Test-Client am Entwicklungs-PC:** `slideshow_hub/cue_state_listener.py` — Verbindung z. B. `ws://<NAS-IP>:8090/ws/default` (gleiche Session wie Export). Beim Connect sendet das Skript `hello` mit `role: "cue_debug"`; der TV antwortet mit einem **State** (wie beim Handy-Remote). Jede Folienänderung auf dem TV liefert neue States; das Skript loggt nur bei **Änderung** der effektiven Cue-Felder.

**Ausblick:** Derselbe Endpunkt und dasselbe JSON eignen sich für einen **ZYBO / Raspberry Pi**, der `state` oder nur Cue-Kanten verarbeitet und DMX/OSC ausgibt — ohne die Slideshow selbst zu ändern, solange das Nachrichtenformat stabil bleibt.
