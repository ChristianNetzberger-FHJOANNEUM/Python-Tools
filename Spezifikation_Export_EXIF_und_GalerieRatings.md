# Spezifikation: EXIF in Export + Galerie-Ratings + Rückimport

**Status:** Festgelegt zur Implementierung (Stand: Entwurf zur Abnahme).  
**Ziel:** Klare Trennung zwischen (A) portablen Metadaten in exportierten Bilddateien und (B) galeriespezifischen Bewertungen ohne Schreibzugriff des Hubs auf Original-Sidecars.

---

## 1. Ziele

1. **Export-JPEGs** enthalten für Kurz-/Langpräsentation und Karten-Nutzung **fest eingebettete** Metadaten: **GPS**, **Aufnahmedatum**, **Sterne-Rating** (Werte **zum Zeitpunkt des Exports** aus der Photo-Tool-Datenhaltung).
2. **Galerie-Ratings** (Couch, Remote, Slideshow-Instanz) leben **nur** in der **Export-Artefakt-Ebene** (`slides.json` / eingebettetes `photos` / optional begleitende Datei im selben Ordner) — **nicht** in den allgemeinen Scan-Sidecars neben den Originalen über den NAS-Hub.
3. **Rückimport** dieser Galerie-Bewertungen ins Photo Tool erfolgt **nur auf explizite User-Aktion** (Assistent/Dialog), mit nachvollziehbarem Abgleich — **keine** stillen Pfad-Operationen durch den Hub auf dem NAS.

## 2. Nicht-Ziele (bewusst ausgeschlossen)

- Der Slideshow-Hub **schreibt nicht** in `.metadata.json` neben **Originaldateien** (weder Scan-noch Projekt-Sidecars), solange dieses Konzept gilt.
- Kein automatischer Zwei-Wege-Sync zwischen NAS-Galerie und Photo Tool ohne User-Bestätigung.
- Keine Garantie, dass **WebP**-Ausgaben dieselbe Metadaten-Reichweite wie JPEG haben (siehe Abschnitt 4).

---

## 3. Begriffe

| Begriff | Bedeutung |
|---------|-----------|
| **Original** | Quelldatei im Workspace/Projekt; Sidecars optional getrennt nach Produktregeln. |
| **Export-Artefakt** | Dateien unter der exportierten Galerie: `images/*.jpg`, `thumbnails/*`, `slides.json`, `index.html`, ggf. `music/*`. |
| **Export-Sicht Rating** | Sterne (0–5), die beim Export aus der für diese Datei gültigen Metadaten-Quelle gelesen und nach §4 in EXIF übernommen werden. |
| **Galerie-Rating** | Nachträgliche Änderung nur für **diese** Web-Galerie-Instanz; Quelle der Wahrheit: §5. |

---

## 4. EXIF / XMP in exportierten JPEGs (fix im Export)

### 4.1 Geltungsbereich

- **Primär:** Ausgabe-**JPEG** unter `gallery/images/` (wie vom Export-Profile erzeugt).
- **WebP:** Wenn erzeugt, gilt: **Best effort**; falls keine zuverlässige Einbettung aller Felder möglich, bleiben Karten/Filter für die Web-Slideshow auf **`slides.json` / `photos`** (single source für den Player).

### 4.2 Zu schreibende Felder (Minimalumfang)

| Information | Vorschlag technische Abbildung | Quelle (lesend beim Export) |
|-------------|-------------------------------|------------------------------|
| Aufnahmedatum/-zeit | EXIF `DateTimeOriginal` (und konsistent `DateTimeDigitized` falls sinnvoll) | Capture-Zeit aus Photo Tool / Original-Metadaten (heutige Export-Logik erweitern wo nötig) |
| GPS-Position | EXIF GPS IFD (Lat/Lon, Höhe optional; Referenz WGS84) | Vorhandene GPS-Daten aus Metadaten-Quelle; **nur wenn opt-in** (siehe 4.4) |
| Sterne | XMP `xmp:Rating` (1–5) und kompatibel ggf. zusätzlich gängige EXIF-Rating-Konventionen, sofern ohne Konflikt | Aktuelles `rating` aus derselben Quelle wie heute beim Füllen von `photo_entry` / `slides` |

**Stern 0 / keine Bewertung:** Entweder Tag weglassen oder explizit auf „unbewertet“ setzen gemäß gewählter Konvention (in Implementierung festlegen, dokumentieren).

### 4.3 Konsistenz mit `slides.json` / `photos`

- Beim Export: **`rating`**, **`gps`** (falls vorhanden), Aufnahmezeit in **`slides.json`** / `photos` wo bereits vorgesehen **muss** mit den in das JPEG geschriebenen Werten **übereinstimmen** (gleiche Export-Session, keine zwei Wahrheiten).

### 4.4 Datenschutz / Opt-in

- Export-Profil oder Export-Dialog: Option **`Geo in Ausgabe-JPEGs einbetten`** (Standard **aus** oder an sensiblen Profilen **aus**, Produktentscheid).
- Option **`Bewertung in Ausgabe-JPEGs einbetten`** kann mit globalem Export verknüpft werden (Standard **ein**, sofern nicht datenschutzrelevant).

### 4.5 Nicht beschreiben / nicht ändern

- Keine Änderung der **Originaldateien** durch diese Spezifikation.
- Keine Pflicht, **kommentare/keywords** in EXIF zu duplizieren (außerhalb dieses Umfangs, später erweiterbar).

---

## 5. Galerie-Ratings (Ziel: `slides.json` / `photos`)

### 5.1 Autoritative Quelle für die laufende Slideshow

- Der **Player** (exportierte `index.html`) liest Bewertungen für Filter/Anzeige primär aus dem **eingebetteten `photos`-JSON** und/oder **nachgeladenem / aktualisiertem `slides.json`**, nicht aus EXIF der geladenen Pixel (Performance, Einfachheit).

### 5.2 Schema — **festgelegt (Couch vs. Export)**

**Ziel:** Couch-Bewertung ist **explizit getrennt** und **direkt in der Slideshow** nutzbar (Filter, Iteration), ohne die Export-Snapshot-Semantik zu vermischen.

- **`slides.json`** / eingebettete `photos`: pro Slide weiterhin:
  - **`rating`** / **`color`**: Stand **vom letzten Photo-Tool-Export** (wie heute aus Metadaten); entspricht der **EXIF-Snapshot-Logik** in den JPEGs (§4).
  - **`couch_rating`** (0–5, optional `null`) und optional **`couch_color`**: nur **Galerie/Couch-Session** (Remote, Durchklicken am TV).
- **Slideshow-Player:** für Anzeige und Filter **`effective_rating`** = wenn Couch gesetzt ist (Semantik für `null` vs. `0` in Implementierung dokumentieren), sonst `rating`.
- **Workflow:** Slides durchklicken, Sterne vergeben → **Sterne-Filter** erhöhen → weiter („wegsortieren“), nächste Iteration → **Couch-Stand ins Photo Tool importieren** (§6) → **neuer Export** (vollständig, wenn EXIF/JSON neu aus Tool kommen sollen; Quick-Update nur HTML beachten).
- **Wiederverwendung:** Optional separate Datei **`gallery-session.json`** / **`couch-ratings.json`** (Export-ID, Zeitstempel, Mapping) für **anderes Projekt** (z. B. „Best-of aus Galerie“) — **nicht** MVP-Pflicht.

**Video (`.mp4`, später):** gleiche Felder in `slides[]`; eigenes Player-Handling — **eigene Phase**.

### 5.3 Slideshow-Hub `/api/rate`

- **Resource:** **Kein** Schreibzugriff auf `source_path` / Original-Sidecars. Schreiben nur:
  - **`slides[i].couch_rating` / `couch_color`** in **`slides.json`** auf dem Host, **oder**
  - nachgelagert in **`gallery-ratings.json`**, das der Player beim Start per `fetch` merged (sinnvoll, wenn `slides.json` nur read-only über HTTP liegen soll).
- **Konfiguration Hub:** Schreibbar gemounteter Pfad zum **Galerie-Stammordner** (z. B. dieselbe Freigabe wie nginx `mera-peak/`), oder URL-zu-Pfad-Abbild per Env — Details in Implementierung.

- **Abzulösendes Legacy:** Bestehendes `/api/rate`, das `_set_metadata(source_path)` aufruft, wird durch obiges Verhalten **ersetzt** oder per Flag umgeschaltet.

### 5.4 Remote-UI

- `slides_json_url` bleibt HTTP-URL; nach erfolgreichem Rating: konsistente Anzeige; optional WebSocket-Broadcast „rated“ ( später).

---

## 6. Rückimport ins Photo Tool

### 6.1 Trigger

- Menüpunkt z. B. **„Bewertungen aus Galerie-Export importieren …“**
- User wählt Ordner oder `slides.json` (lokal oder Netzpfad).

### 6.2 Abgleich

- **Primär:** `source_path` aus `slides.json`, wenn identisch zu bekannten Fotos im aktuellen Workspace/Projekt (normalisierte Pfade, gleicher Datenträger).
- **Fallback:** Stabile **`photo_id`** / Hash in `slides.json` ergänzen (Implementierung), wenn Pfade zwischen Export und Import abweichen.

### 6.3 Was importiert wird

- **Primär:** **`couch_rating`** / **`couch_color`** pro Slide in das Photo Tool übernehmen (auf die zugehörige Datei gemäß `source_path` / Fallback-ID).
- **Konfliktregel (vorläufig):** bei Abweichung zu bestehenden Tool-Metadaten **immer Rückfrage** („immer fragen“); später erweiterbar um globale Regeln.

### 6.4 Ziel im Photo Tool

- Schreiben in die **vom Produkt definierte** Metadaten-Speicherung (projektspezifisch oder global), **nicht** still und nicht ohne Bestätigung.

---

## 7. Sicherheit & Betrieb

- Hub schreibt nur in **freigegebene** Galerie-Pfade (Berechtigungen, Docker-Volume).
- Keine Ausführung von User-HTML aus `slides.json` im Hub (nur JSON-Parsing).

---

## 8. Verbleibende Feinentscheide (klein)

1. **Standard Opt-in Geo** in JPEG: aus/an pro Profil?
2. **WebP:** Nur JPEG EXIF voll, oder WebP bewusst ohne GPS und Hinweis in UI?
3. **„couch_rating löschen“** vs. `null`: Remote „keine Couch-Sterne“ muss vom Player und Import gleich verstanden werden.

---

## 9. Machbarkeit (Implementierung)

| Baustein | Aufwand | Bewertung |
|----------|---------|-----------|
| **`couch_*` in Export-JSON + Merge im Player** | Gering–mittel | Gut machbar; Export um Felder erweitern, Slideshow-JS `effective_rating` + Filter-UI (Schwelle, ein/aus). |
| **Hub schreibt nur Galerie-`slides.json` / Sidecar-JSON** | Mittel | Pfad/Volume auf NAS muss sauber sein; HTTP-GET `slides.json` + lokal schreiben ist Standard. |
| **Rückimport + Konflikt „immer fragen“** | Mittel | Ein Dialog mit Liste/X Abgleich ist überschaubar; Matching über `source_path` zuerst. |
| **EXIF GPS/Datum/Stern im Export-JPEG** | Mittel | PIL/`piexif`/XMP oder vorhandene Hilfen prüfen; Profil-Flags. |
| **Separate `gallery-session.json` für Best-of-Projekt** | Gering | Parallel speichern beim Hub oder beim Import. |
| **MP4 in derselben Logik** | Höher | Manifest + Player müssen Clips tragen; spätere Phase. |

**Gesamt:** Das Konzept ist **implementierbar in klar abgegrenzten Iterationen** (1) Schema + Player + Filter, (2) Hub nur Galerie, (3) Import-Assistent, (4) EXIF im Export, (5) Video.

---

## 10. Abnahme

Festgelegt: **§5.2** separate **`couch_rating`/`couch_color`**, Slideshow mit Filter-Iteration; **§6.3** Konflikte **vorläufig immer Rückfrage**.  
**§5.3** Hub-Ziel: Galerie-Ordner only; Legacy-Rating auf Original-Sidecars wird obsolet.
