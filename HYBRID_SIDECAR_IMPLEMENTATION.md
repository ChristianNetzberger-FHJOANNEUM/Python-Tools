# Hybrid-Sidecar System - Implementation Complete ✅

## Status: **FERTIG & BEREIT ZUM TESTEN** 🚀

Das Hybrid-Sidecar System ist vollständig implementiert und wartet auf deine ersten Tests!

---

## 📋 Was wurde implementiert?

### 1. **Backend: ProjectSidecarManager** ✅
**Datei:** `photo_tool/projects/project_sidecar.py`

Neue Klasse zur Verwaltung projekt-spezifischer Metadaten:
- **Speicherort:** `workspace/projects/{project_id}/.sidecars/`
- **Format:** JSON-Dateien pro Foto (z.B. `P1012591.JPG.json`)
- **Funktionalität:**
  - `merge_metadata()`: Merged globale + projekt-spezifische Daten
  - `set_rating()`, `set_color()`: Speichert Projekt-Overrides
  - `add_keyword()`, `remove_keyword()`: Keyword-Management
  - `has_override()`: Prüft ob Overrides existieren
  - `get_stats()`: Statistiken über Overrides
  - `list_overrides()`: Liste aller Fotos mit Overrides

**Metadata-Hierarchie:**
1. **Global-Sidecar** (`.phototool.json` neben Foto) = Basis
2. **Project-Sidecar** (in `.sidecars/`) = Override (höhere Priorität!)

---

### 2. **Backend: API Endpoints erweitert** ✅

#### Erweiterte Endpoints (mit `?project_id=...` Parameter):

**`POST /api/photos/<photo_id>/rate?project_id=test-only`**
- Setzt Rating im **Project-Sidecar** (nicht global!)
- Response: `{ "success": true, "rating": 5, "target": "project" }`

**`POST /api/photos/<photo_id>/color?project_id=test-only`**
- Setzt Color Label im **Project-Sidecar**
- Response: `{ "success": true, "color": "red", "target": "project" }`

**`POST /api/photos/<photo_id>/keywords?project_id=test-only`**
- Fügt Keywords zum **Project-Sidecar** hinzu
- Keywords werden mit globalen gemergt (kombiniert!)

#### Neue Endpoints:

**`GET /api/projects/<project_id>/sidecar-stats`**
- Statistiken über Projekt-Overrides
- Response:
  ```json
  {
    "stats": {
      "total_overrides": 15,
      "rating_overrides": 12,
      "color_overrides": 8,
      "keyword_overrides": 5
    },
    "photos_with_overrides": ["P1012591.JPG", "P1012592.JPG", ...]
  }
  ```

---

### 3. **Backend: Media Loading mit Hybrid-Daten** ✅

**`GET /api/projects/<project_id>/media`**
- Lädt Fotos mit **gemergten Metadaten** (global + project)
- Jedes Foto bekommt zusätzliche Felder:
  ```json
  {
    "id": "...",
    "rating": 5,
    "color": "red",
    "keywords": ["natur", "baum", "projekt-tag"],
    "has_project_override": true,
    "rating_source": "project",
    "color_source": "project"
  }
  ```

---

### 4. **Frontend: Project-Context Integration** ✅

**Alle Metadaten-Aktionen prüfen `currentProjectId`:**

```javascript
// Rate Photo
let url = `/api/photos/${photo.id}/rate`;
if (this.currentProjectId) {
    url += `?project_id=${this.currentProjectId}`;
}
// -> Speichert in Project-Sidecar statt Global!
```

**Betrifft Methoden:**
- `rate(photo, rating)`
- `setColor(photo, color)`
- `addKeyword(photo, keyword)`
- `removeKeyword(photo, keyword)`

---

### 5. **UI: Visual Override-Indikator** ✅

**Photo-Card Badge (unten rechts):**
```html
<!-- Zeigt "📁" Symbol wenn Projekt-Override existiert -->
<div v-if="photo.has_project_override" 
     style="...background: rgba(139, 92, 246, 0.9)...">
    📁
</div>
```

**Tooltip zeigt Details:**
- `⭐ Rating overridden` (wenn `rating_source === 'project'`)
- `🎨 Color overridden` (wenn `color_source === 'project'`)

---

## 🎯 Workflow: Wie es funktioniert

### Beispiel-Szenario:

1. **Globales Archiv:**
   - `P1012591.JPG` hat Rating: ⭐⭐⭐ (3 Stars)
   - Keywords: `["natur", "wald"]`

2. **Du öffnest Projekt "Fotobuch":**
   - Foto wird mit globalem Rating geladen
   - Du vergibst Rating: ⭐⭐⭐⭐⭐ (5 Stars) **im Projekt**
   - Fügt Keyword `"fotobuch"` hinzu

3. **Was passiert?**
   - **Project-Sidecar erstellt:** `projects/fotobuch/.sidecars/P1012591.JPG.json`
   ```json
   {
     "rating": 5,
     "keywords": ["fotobuch"],
     "updated": "2026-02-06T14:30:00"
   }
   ```
   - **Foto zeigt im Projekt:** ⭐⭐⭐⭐⭐ (5 Stars) + Badge 📁
   - **Keywords:** `["natur", "wald", "fotobuch"]` (gemergt!)

4. **Du öffnest ein anderes Projekt:**
   - Dasselbe Foto zeigt: ⭐⭐⭐ (3 Stars) (global!)
   - Keywords: `["natur", "wald"]` (nur global)

5. **Zurück zum Archiv:**
   - Foto hat weiterhin: ⭐⭐⭐ (3 Stars)
   - **Projekt-Rating bleibt gekapselt!** ✅

---

## 🧪 Test-Checkliste

### Test 1: Rating Override
- [ ] Projekt öffnen (z.B. "test-only")
- [ ] Foto mit globalem Rating auswählen
- [ ] Neues Rating vergeben → Badge 📁 erscheint
- [ ] Anderes Projekt öffnen → Globales Rating wird angezeigt
- [ ] Zurück zum ersten Projekt → Projekt-Rating wird angezeigt

### Test 2: Color Override
- [ ] Foto mit globaler Farbe auswählen
- [ ] Neue Farbe im Projekt setzen → Badge 📁 erscheint
- [ ] Projekt wechseln → Globale Farbe wird angezeigt

### Test 3: Keywords Merge
- [ ] Foto mit globalem Keyword auswählen
- [ ] Projekt-Keyword hinzufügen
- [ ] Beide Keywords werden angezeigt (gemergt!)
- [ ] Projekt wechseln → Nur globale Keywords

### Test 4: Sidecar Stats
- [ ] Browser-Console öffnen
- [ ] API aufrufen: `GET /api/projects/test-only/sidecar-stats`
- [ ] Statistiken prüfen:
  ```json
  {
    "stats": {
      "total_overrides": 3,
      "rating_overrides": 2,
      "color_overrides": 1
    }
  }
  ```

### Test 5: Persistenz
- [ ] Rating im Projekt ändern
- [ ] App neu laden
- [ ] Projekt öffnen → Rating bleibt erhalten

### Test 6: File System Check
- [ ] Navigiere zu: `workspace/projects/test-only/.sidecars/`
- [ ] Prüfe: JSON-Dateien existieren für geratete Fotos
- [ ] Inhalt prüfen:
  ```json
  {
    "rating": 5,
    "updated": "2026-02-06T..."
  }
  ```

---

## 📂 Datei-Struktur

```
workspace/
└── projects/
    └── test-only/
        ├── project.json          # Projekt-Config
        └── .sidecars/            # ← NEU: Projekt-Metadaten
            ├── P1012591.JPG.json
            ├── P1012592.JPG.json
            └── ...

media-folder/
└── 101_PANA/
    ├── P1012591.JPG
    └── P1012591.JPG.phototool.json  # ← Global-Sidecar (Basis)
```

---

## 🔍 Debugging

### Logs prüfen:
```python
# Backend logs zeigen:
logger.info(f"Set project rating for {photo_path.name} in project {project_id}: {rating}")
logger.info(f"Set global rating for {photo_path.name}: {rating}")
```

### Browser Console:
```javascript
// Check photo metadata
console.log(photo.has_project_override);  // true/false
console.log(photo.rating_source);         // "project" or "global"
console.log(photo.color_source);          // "project" or "global"
```

### API Test (Browser Console):
```javascript
// Get sidecar stats
fetch('/api/projects/test-only/sidecar-stats')
  .then(r => r.json())
  .then(data => console.log(data));
```

---

## 🎨 UI/UX Features

### Visual Indicators:
- **📁 Badge:** Zeigt Projekt-Override an
- **Tooltip:** Details über welche Felder überschrieben sind
- **Farbe:** Lila/Purple (rgba(139, 92, 246, 0.9))

### Future Enhancements (Optional):
- [ ] "Reset to Global" Button (entfernt Project-Override)
- [ ] "Apply to Global" Button (kopiert Project → Global)
- [ ] Stats-Anzeige im Projects-Tab (X Fotos mit Overrides)
- [ ] Batch-Operations (alle Overrides auf einmal anwenden)

---

## 📊 Performance

### Speicher-Effizienz:
- ✅ **Keine Duplikate:** Nur Overrides werden gespeichert
- ✅ **Kleine Dateien:** ~100-200 Bytes pro Override
- ✅ **Schnell:** Keine DB-Abfragen nötig

### Beispiel:
- **100 Fotos im Projekt**
- **10 mit Rating-Override**
- **Speicher:** ~2 KB (10 × 200 Bytes)

---

## ✅ Implementation Status

| Komponente | Status | Datei |
|------------|--------|-------|
| ProjectSidecarManager | ✅ Fertig | `photo_tool/projects/project_sidecar.py` |
| API Endpoints (rate) | ✅ Fertig | `gui_poc/server.py` (Line 262+) |
| API Endpoints (color) | ✅ Fertig | `gui_poc/server.py` (Line 311+) |
| API Endpoints (keywords) | ✅ Fertig | `gui_poc/server.py` (Line 355+) |
| API Endpoints (stats) | ✅ Fertig | `gui_poc/server.py` (Line 2442+) |
| Media Loading (merge) | ✅ Fertig | `gui_poc/server.py` (Line 2136+) |
| Frontend (rate) | ✅ Fertig | `gui_poc/static/index.html` (Line 5110+) |
| Frontend (setColor) | ✅ Fertig | `gui_poc/static/index.html` (Line 5233+) |
| Frontend (keywords) | ✅ Fertig | `gui_poc/static/index.html` (Line 5343+) |
| UI Badge Indicator | ✅ Fertig | `gui_poc/static/index.html` (Line 2017+) |

---

## 🚀 Nächste Schritte

1. **App starten:**
   ```bash
   cd c:\_Git\Python-tools
   python gui_poc/server.py
   ```

2. **Browser öffnen:**
   - http://localhost:8000

3. **Projekt wählen:**
   - Tab "Projects" → Projekt "test-only" auswählen
   - "Save & Load Media" klicken

4. **Testen:**
   - Fotos raten (1-5 Sterne)
   - Farben setzen
   - Keywords hinzufügen
   - Badge 📁 beobachten!

5. **Feedback:**
   - Funktioniert alles wie erwartet?
   - Gibt es Fehler in der Console?
   - Performance OK?

---

## 🎉 Zusammenfassung

**Du hast jetzt:**
✅ **Projekt-spezifische Ratings** (unabhängig vom globalen Archiv)
✅ **Projekt-spezifische Colors** (gekapselt pro Projekt)
✅ **Hybrid Keywords** (global + projekt, gemergt!)
✅ **Visual Feedback** (📁 Badge zeigt Overrides)
✅ **Keine Duplikate** (effiziente Speicherung)
✅ **Volle Kontrolle** (jedes Projekt ist isoliert!)

**Bereit zum Testen!** 🚀

Falls du Fragen hast oder etwas nicht funktioniert, lass es mich wissen! 😊
