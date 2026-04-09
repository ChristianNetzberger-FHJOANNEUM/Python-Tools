# Spezifikation: Slideshow — dynamische Audio-Playlists, kontextbezogene Musik, Licht-Cues

**Status:** **Finalisiert** zur Orientierung für Implementierung (Stand: konsolidiert inkl. Mehrspur-Audio und Erbe-Semantik).  
**Bezug:** `photo_tool/actions/export.py` (`slides.json`, eingebettetes `photos`-JSON, `mergeCouchRatingsFromSlidesJson`), Slideshow Remote Hub (`slideshow_hub`), Parallelen zu segmentierten Shows (z. B. ImmerGallery / Sidecar-Konzept).

---

## 1. Ziel

1. **Audio:** Die Slideshow soll **ohne erneutes Erzeugen der `index.html`** durch reines Befüllen von `music/` bzw. Aktualisieren von Manifestdaten eine **aktuelle Playlist** nutzen können; optional **Stem pro Folienabschnitt** aus `slides.json`; optional **parallele One-Shots** (z. B. Stinger/LFE-Ereignis) gemäß Abschnitt 5.6. Ohne Angaben: Verhalten wie heute (Legacy).
2. **Licht:** Dieselbe **zeitliche/sequenzielle Logik** (Wechsel bei Folienwechsel oder Segmentgrenze) soll **Licht-Cues** transportieren können, die von **LAN-Diensten** oder **lokalen Steuerrechnern** ausgewertet werden.
3. **Kompatibilität:** Bestehende Galerien ohne neue Felder verhalten sich **unverändert** (Abwärtskompatibilität).

---

## 2. Begriffe

| Begriff | Bedeutung |
|--------|-----------|
| **Galeriewurzel** | HTTP(s)-URL des Ordners mit `index.html`, `slides.json`, `images/`, `music/` … |
| **Effektiver Slide-Index** | Aktuell angezeigte Folie `i` in der Slideshow (0-basiert), wie heute. |
| **Segment (Audio, Stem)** | Zwei aufeinanderfolgende Slides können **dieselbe** effektive **Hintergrundspur** (`music_track` / Default) haben; diese **läuft in Schleife**, bis ein Slide einen **neuen** Stem setzt (explizit oder durch neuen Default). |
| **One-Shot / SFX-Layer** | Kurze Clips (z. B. „Subwoofer-Stinger“), die **parallel** zum Stem **einmalig** oder **überblendend** abgespielt werden; siehe Abschnitt 5.6. |
| **Segment (Licht)** | Entsprechend: ein **Cue** oder **Cue-Id** bleibt **wirksam**, bis ein Slide mit anderem Cue folgt. |
| **`slides[]` in `slides.json`** | Kanonische Manifestzeilen inkl. `source_path`, `couch_*`, optional neue Felder für Audio/Licht. |
| **Runtime-Merge** | Wie bei `couch_*`: TV lädt `slides.json` und mergt Felder in das **laufende** `photos`-Array (bereits vorbereitet für NAS-Updates). |

---

## 3. Designprinzipien

1. **Kein Browser-Dateisystemzugriff:** Ein reiner Web-Client kann den Ordner `music/` **nicht** auflisten. Stattdessen gilt eine der folgenden **Discover**-Strategien (siehe Abschnitt 5).
2. **Einzelquelle der Wahrheit für Kontext:** Steuerinformationen für „welcher Track / welcher Lichtzustand zu dieser Folie gehört“ liegen bevorzugt in **`slides.json`** (pro Slide oder als globale Defaults). Sidecars im Photo Tool können diese Felder **beim Export** in die Manifestzeile schreiben (analog `couch_*` / Metadaten).
3. **Idempotenz bei Folienwechsel:** Beim Wechsel `i → j` vergleicht die Slideshow die **effektiven** Werte für Index `j` mit den **aktuell aktiven**; nur bei Änderung werden Audio neu geladen bzw. Lichtnachrichten gesendet.

---

## 4. Erweiterungen in `slides.json`

### 4.1 Top-Level (optional)

| Feld | Typ | Bedeutung |
|------|-----|-----------|
| `slideshow_schema_version` | `integer` | Optional; beginnend mit `2`, wenn Audio/Licht-Felder genutzt werden (Versionskennzeichen für Parser). |
| `music_default_track` | `string \| null` | Relativer Pfad unter der Galeriewurzel, z. B. `music/ambient.mp3`. Wenn `null` oder fehlend: siehe Fallback (Abschnitt 6). |
| `music_playlist` | `string[]` | Geordnete Liste relativer Pfade (Discovery-Alternative zu reinem Ordnerscan). |
| `music_discover` | `object` | Optional; siehe Abschnitt 5.2. |
| `light_endpoint` | `string \| null` | Optional **pro Galerie**: Basis-URL oder logischer Name eines LAN-Gateways (Profil). Darf aus **Sicherheitsgründen** leer sein; dann nur generische Cues ohne Ziel (Abschnitt 7.3). |
| `light_default_cue` | `string \| null` | Cue-Id / Szene, wenn ein Slide **kein** eigenes `light_cue` hat. |

### 4.2 Pro Eintrag in `slides[]`

| Feld | Typ | Bedeutung |
|------|-----|-----------|
| `music_track` | `string \| null` | **Stem** (Hintergrund): Relativer Pfad (z. B. `music/track02.mp3`) oder **nur Dateiname** unter `music/`. `null`/fehlend: **Erbe gemäß Abschnitt 5.5.1**. |
| `music_one_shots` | `array \| null` | Optional: Liste von **Ereignis-Clips** für genau diese Folie (oder leer = keine). Struktur siehe **5.6.3**. |
| `light_cue` | `string \| null` | Opake Id oder Kurzcode (z. B. `intro_blue`, `scene_5`). `null`/fehlend: erbe `light_default_cue` oder „kein Lichtwechsel“. |
| `light_payload` | `object` | Optional **zusätzliche** strukturierte Daten (z. B. `{ "brightness": 0.8, "kelvin": 3200 }`), **nur** wenn das Zielsystem sie versteht. Nicht verpflichtend. |

**Merge-Regel (NAS / Quick-Update):** Analog zu `couch_*` können **`music_track`**, **`music_one_shots`**, **`light_cue`**, **`light_payload`** aus einer auf dem Server aktualisierten `slides.json` **nach `source_path`** in die laufende Slideshow gemerged werden, sofern die TV-Implementierung das vorsieht. Neu exportierte `index.html` muss die Parser für diese Keys kennen.

---

## 5. Audio: Discovery & Abspielreihenfolge

### 5.1 Strategie A — Manifestliste `music_playlist`

- Die Dateien **müssen** unter der Galeriewurzel erreichbar sein (relativ zu `index.html`).
- **Reihenfolge** = Array-Reihenfolge.
- **Neuer Track ohne Export:** Datei nach `music/` legen und Liste in `slides.json` (oder separates `music/manifest.json`) per Editor/Skript ergänzen; **Reload** der Seite oder Re-Fetch von `slides.json`.

### 5.2 Strategie B — Konvention `trackXX`

- `music_discover`: `{ "mode": "track_prefix", "prefix": "music/track", "extension": ".mp3", "max_probe": 99 }`
- Die Slideshow oder ein Helferskript **fordert** nacheinander `music/track01.mp3` … an (**HEAD** oder **GET**), bis eine festgelegte Anzahl aufeinanderfolgender Fehler (z. B. 2× 404).
- **Vorteil:** Kein explizites Array nötig. **Nachteil:** Lücken in der Nummerierung können die Entdeckung vorzeitig beenden (konfigurierbar).

### 5.3 Strategie C — `music/manifest.json`

- Kleine JSON-Datei neben den Tracks: `{ "tracks": [ "music/a.mp3", … ] }`.
- Entkopplung von `slides.json`; praktisch für reine **Hintergrund-Playlist** ohne Folienbindung.

### 5.4 Fallback-Kette (Vorschlag)

1. Wenn `music_playlist` nicht leer → verwenden.
2. Sonst, wenn `music_discover` gesetzt → gemäß Modus.
3. Sonst **Legacy:** in `index.html` eingebettete `<audio><source>…` wie heute (statischer Export).
4. Wenn nichts davon → keine Hintergrundmusik.

### 5.5 Kontext-Musik (`music_track` pro Slide — Stem)

#### 5.5.1 Erbe-Semantik (verbindlich)

Die **effektive Hintergrundspur** `stem(j)` für Slide-Index `j` (0-basiert) wird so gebildet:

1. Wenn `slides[j].music_track` ein **nicht-leerer** String ist → `stem(j) :=` dieser Pfad (neues Segment beginnt).
2. Sonst, wenn `j > 0` → `stem(j) := stem(j - 1)` (**explizites Erbe** vom vorherigen Slide — unabhängig von `music_default_track`).
3. Sonst (`j === 0`) → `stem(0) := music_default_track`, und wenn das fehlt → erster Eintrag von `music_playlist` bzw. Legacy-`<audio>`-„Hauptquelle“ wie in 5.4.

**Wechsel beim Abspielen:** Beim Anzeigen von Slide `j`: wenn `stem(j) !== stem(j_prev)` (mit `j_prev` = zuvor angezeigter Index, beim ersten Start `null`) → Stem-Audio **Quelle wechseln**, **`loop = true`**, `load()` + `play()` nach Nutzerfreigabe/Autoplay-Policy wie heute.

Damit ist ein Block folien ohne eigenes `music_track` **immer** ein durchgehendes **Musiksegment**; **kein** Stillstand durch fehlende Felder in der Mitte der Show.

#### 5.5.2 One-Shots unabhängig vom Stem

**Parallele** Effekte (Abschnitt 5.6) werden **zusätzlich** ausgelöst und reduzieren die Erbe-Logik für den Stem **nicht**.

---

### 5.6 Mehrspur-Audio: Hintergrund + überlagerte Clips („Addieren“)

#### 5.6.1 Zielbild

- **Stem** (Schleife): wie 5.5 — z. B. ruhige Hintergrundmusik.
- **Zusätzliche** `.mp3` (oder andere unterstützte Formate) **parallel**: z. B. kurzer **LFE-/Rumble-Clip** („Subwoofer-Event“), Applaus, Gong — **ohne** den Stem zu stoppen.

**„Addieren“** im Sinne dieser Spezifikation bedeutet **zeitgleiches Abspielen** mit **unabhängiger Lautstärke** (und optional **einfacher Pegelanpassung**), **nicht** zwingend mathematisches Summieren im DSP; für Höreindruck und „Spektakel“ reicht typischerweise **zwei bis wenige Kanäle**.

#### 5.6.2 Technische Optionen (Browser)

| Variante | Beschreibung | Shield / TV-Browser |
|----------|--------------|---------------------|
| **A — Mehrere `HTMLAudioElement`** | Ein Element für Stem (loop), weitere Elemente für One-Shots (kein loop). Steuerung über `volume`, `play()`. | **Denkbar** auf NVIDIA Shield (Chromium/WebView): parallel mehrere `<audio>` werden in der Praxis oft unterstützt; **Gerätetest** empfohlen (RAM, Latenz, Fokus). |
| **B — Web Audio API** | `AudioContext`, optional `GainNode` pro Schicht; Medien können über `MediaElementAudioSourceNode` oder decodierte Buffer gemischt werden; **präzisere** Überblendungen und Pegel. | **Grundsätzlich verfügbar** in modernen Chromium-basierten TV-Browsern; **AudioContext** kann eine **User-Gesture**-Freischaltung brauchen (Splash-Start deckt das ab). Ebenfalls **Gerätetest** (manchmal Sample-Rate-/Suspend-Verhalten). |
| **C — Vorbereiteter Mix als eine Datei** | Stem + Stinger in **einem** File im Schnittprogramm → **kein** Runtime-Mix; einfachste Playback-Kette. | Immer möglich; **kein** separates „Event“ pro Slide ohne neue Datei. |

**Fazit:** **Mit und ohne NVIDIA Shield** denkbar — entscheidend ist **der konkrete Browser auf dem Wiedergabegerät**, nicht die Shield-Hardware an sich. Shield ist ein **Android-TV-Rechner mit Chromium**; ein **PC mit Chrome/Edge** nutzt dieselbe Web-Plattform-Klasse und ist oft der **einfachere Testrechner** vor dem TV.

**Physikalischer Subwoofer:** LFE entsteht erst in der **Kette HDMI → AV-Receiver/Soundbar** (Bass-Management, ggf. `.1`-Kanal bei Mehrkanal-Material). **Stereo**-MP3-Effekte werden typisch **mono summiert** oder virtuell breit gemischt; ein **tiefer Stinger in Stereo** kann den Sub **mitanregen**, ist aber **kein** garantiertes separates LFE-Kanal-Routing — wer harten LFE will, kann **mehrkanaliges** Material oder externe Showcontroller erwägen (außerhalb dieser Slideshow-Spezifikation).

#### 5.6.3 Datenmodell `music_one_shots` (optional, pro Slide)

Jeder Eintrag beschreibt **ein** paralleles Ereignis beim **Eintreffen** auf der Folie (und optional nur einmal pro „Visit“ der Folie):

```json
{
  "file": "music/stingers/subboom.mp3",
  "gain": 1.0,
  "mode": "oneshot",
  "duck_stem_db": 0
}
```

| Feld | Bedeutung |
|------|-----------|
| `file` | Relativer Pfad zur Galeriewurzel |
| `gain` | Linearer Pegel `0…1` (oder >1 wenn Implementierung erlaubt — Vorsicht vor Clipping) |
| `mode` | In **v1** nur `oneshot` (einmal bis Dateiende). Weitere Modi (z. B. Schleife) erst ab v2 falls nötig. |
| `duck_stem_db` | Optional: Stem kurz **absenken** (Negativ-dB), z. B. `-6`, für bessere Verständlichkeit des FX |

**Auslösung:** Beim Wechsel auf Slide `j` werden **nach** Stem-Update die in `slides[j].music_one_shots` gelisteten Clips gestartet (Reihenfolge = Array-Reihenfolge). **Gleicher Slide erneut** (Loop der Show): erneutes Abspielen nur wenn die Implementierung das explizit vorsieht (**Empfehlung v1:** pro „Enter Slide j“ einmal pro Durchlauf; optional Flag `repeat_on_revisit` später).

Top-Level optional: `music_one_shots_default` — **nicht** in v1 nötig; lieber pro Slide explizit.

---

### 5.7 Parallelen in Slideshow- und Präsentationspraxis

| Umfeld | Bezug zu layering / Ereignissen |
|--------|----------------------------------|
| **PowerPoint / Keynote / LibreOffice** | Pro Folie oder Übergang: **Einblendton**, oft **ein Kanal**; Mehrspur-Mixing ist **kein** Kernfeature, aber „Hintergrundmusik über alle Folien“ + **Übergangssound** kommt dem Stem+One-Shot nahe. |
| **Google Slides** | Begrenzte Audiomenüs; eher nicht Referenz für Mehrspur. |
| **OBS Studio, vMix, mimoLive** | **Mehrere Audiospuren**, Quellen mixen, **Ducking** — professionelles Näherungsbild für „Stem + Stinger“, aber **außerhalb** des reinen Webbrowsers. |
| **QLab** (_Mac, Standard in Live-Events/Museen_) | **Mehrere Cues**, Wellenformen, **gleichzeitige** Wiedergabe, Routing — konzeptionelles Vorbild für **geschichtete** Show, nicht Web. |
| **Web Games / Storytelling** | **Howler.js**, **Tone.js**, Web Audio — etablierte Muster für **BGM + SFX**. |

**Kurz:** **Mehrspur-Hörerlebnis in der Browser-Slideshow** ist **nicht** verbreitet in klassischen Office-Präsentationstools, aber **wohlvertraut** in **Live-AV**, **Streaming** und **interaktiven Web-Apps**. Diese Spezifikation orientiert sich an **Letzterem** und bleibt bewusst **schlank** (Stem + optionale One-Shots).

---

## 6. Lichtsteuerung aus der Slideshow ableiten

### 6.1 Kernidee

- **Gleiche Trigger** wie bei Musik: **Folienwechsel** liefert einen **neuen effektiven** `light_cue` (inkl. optional `light_payload`).
- Die **Slideshow im Browser** führt **kein** natives DMX aus; sie sendet **Nachrichten** an ein **LAN-Ziel**, das der Nutzer konfiguriert (oder eine **Zwischeninstanz** wie Home Assistant / Companion).

### 6.2 Effektiver Licht-Cue

- `effectiveLight(j) = slides[j].light_cue ?? light_default_cue ?? null`
- Nur wenn `effectiveLight(j) !== effectiveLight(i)` (vorheriger Index): **Cue auslösen** (Debouncing / Deduplizierung bei gleichem Cue).

### 6.3 Transport (spezifikativ, wählbar pro Installation)

| Profil | Beschreibung | Hinweis |
|--------|----------------|--------|
| `http_post` | `POST` auf **lokal konfigurierte** URL mit JSON `{ "cue": "...", "slide_index": j, "payload": { ... } }` | CORS: Ziel muss Header erlauben oder Slideshow und Gateway **gleiche Origin**; sonst **Reverse-Proxy** auf NAS/Hub. |
| `http_get` | `GET` mit Query-Parametern (nur für einfache Gateways) | Idempotent, leicht cachebar — Vorsicht. |
| `websocket` | Dauer-Verbindung zu **eigener** Bridge (z. B. kleiner Dienst auf Raspberry Pi) | Flexibel, umgeht CORS wenn die Slideshow die WS-URL direkt anspricht. |
| `osc` | **Nicht nativ im Browser**; Routing über **kleinen lokalen Proxy** (WebSocket → OSC UDP) | Üblich in Showtechnik. |

Die **konkrete URL/Profil** kann in `light_endpoint` oder **getrennt** in der Slideshow per **Query-Parameter** stehen (z. B. `?lightProxy=http://192.168.1.50:9090`), um **keine** Geheimnisse in `slides.json` zu speichern.

### 6.4 Bekannte Ökosysteme (LAN / halblokal)

Die Slideshow **integriert keine Hersteller-SDKs direkt**; sie spricht **generische** HTTP/WS. Übliche Ziele, die Entwickler oder Hausautomatisierung koppeln:

| Umgebung / Gerät | Kurzbeschreibung |
|------------------|------------------|
| **QLC+** | Open-Source-Lichtsteuerung; **OSC**, **Art-Net**, MIDI; oft **PC im LAN** als Ziel (über Zwischenscript). |
| **Art-Net / sACN** | Standard für DMX über Ethernet; Browser → meist **Bridge** (Pi, Windows-Dienst), nicht roher Browser-UDP. |
| **Philips Hue Bridge** | **HTTP REST** im lokalen Netz (App-Key nötig); für einfache Szenen/Gruppen; CORS ggf. über Proxy. |
| **Home Assistant** | **REST / WebSocket API**; Szenen und Automationen auslösbar per HTTP; gut als **einzige** Anlaufstelle für „Licht + Nebenräume“. |
| **Bitfocus Companion** | Stream-Deck/Show-Control; **HTTP-Request** und viele Modul-Treiber; eignet sich als **Empfänger** von `http_post`-Cues. |
| **MQTT** | Viele IoT-Gateways; Slideshow könnte HTTP an **MQTT-Bridge** senden. |

**Fazit:** Ja — **mit diesem Konzept kann man Lichtsteuerung ableiten**, sofern ein **LAN-Empfänger** die JSON-Cues in echte DMX/Szenen übersetzt. Der Webbrowser bleibt **Trigger**, nicht DMX-Endpunkt.

---

## 7. Kompatibilität mit bestehenden Komponenten

| Komponente | Auswirkung |
|------------|------------|
| **Slideshow Hub / Remote** | Kein Zwang zum Protokollwechsel; `slides.json` kann weiter für Bewertung genutzt werden. Optional später: Remote zeigt **aktiven Track / Cue** aus TV-State. |
| **Photo Tool Export** | Felder optional in `_slide_manifest_entry` / Merge; keine Breaking Changes. |
| **ImmerGallery / Quest** | Konzeptuell **parallel** (Sidecar → Manifest); **dieses** Dokument beschreibt die **Web/NAS-Slideshow**; eine spätere **Zuordnungstabelle** Feld-zu-Feld kann ergänzt werden. |

---

## 8. Sicherheit & Betrieb

1. **`light_endpoint` und Musik-URLs** nur **vertrauenswürdige** Ziele; keine Ausführung beliebigen Contents im JSON.
2. **Lan-Zugriffe** aus der Slideshow sind **von Browser-CORS** abhängig; Produktiv-Setups sollten einen **Proxy unter derselben Origin** wie die Galerie oder den Hub vorsehen.
3. **Autoplay:** Musikwechsel beachtet weiterhin Browser-Richtlinien (User-Gesture über Splash bleibt sinnvoll).

---

## 9. Implementierungsphasen (Empfehlung)

| Phase | Inhalt |
|-------|--------|
| **P1** | `music_track` + Top-Level `music_default_track` + `music_playlist` + Runtime-Audio in der Slideshow; Legacy-`<audio>` als Fallback. |
| **P2** | `music_discover` (track_prefix) optional. |
| **P3** | `light_cue` / `light_payload` + ein Profil `http_post` mit konfigurierbarer Basis-URL (Query oder eingebettete Konstante). |
| **P4** | Export-UI / Sidecar-Mapping im Photo Tool; Dokumentation Proxy-Beispiele (nginx / Hub). |
| **P5** | `music_one_shots` pro Slide: Mehrkanal über mehrere `<audio>` oder Web Audio API; **Shield-/TV-Tests**; optional `duck_stem_db`. |

---

## 10. Schema-Version & zukünftige Erweiterungen

- **`slideshow_schema_version`:** Parser sollen **unbekannte Versionen** weiterhin **best effort** lesen (nur bekannte Felder auswerten). Erhöhung der Version, sobald **inkompatible** Feldsemantik eingeführt wird.
- **Zeitbasierte Licht-Wiederholung** ohne Folienwechsel: **nicht** Bestandteil von v1.
- **`repeat_on_revisit`** für One-Shots bei Loop der Show: optional **v2**.

---

*Ende der Spezifikation (finalisiert).*
