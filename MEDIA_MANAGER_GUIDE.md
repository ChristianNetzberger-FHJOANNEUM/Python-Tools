# Media Manager - Phase 1 Implementation Guide

## Übersicht

Der **Media Manager** ist die oberste Ebene der Photo Tool Hierarchie und ermöglicht die zentrale Verwaltung aller Medienordner mit Pre-Scan Funktionalität.

## Architektur-Hierarchie

```
📱 MEDIA MANAGER (Level 1) - NEU!
   ├── Registrierung aller Medienordner
   ├── Kategorisierung (Internal/USB/Network/Cloud)
   ├── Pre-Scan mit Blur-Detection (3 Methoden)
   └── USB-Laufwerkserkennung via Volume Serial
   
🗂️ WORKSPACE MANAGER (Level 2) - Existiert
   ├── Kombiniert zusammenhängende Medienordner
   └── z.B. "Trekking-Reise 2024": Lumix + Samsung + ActionCam + DJI
   
📁 PROJECT MANAGER (Level 3) - Existiert
   ├── Selektionen für spezifische Ausgaben
   ├── Web-Galerie mit Slideshow
   ├── DaVinci Resolve Filmprojekt
   └── Fotobuch-Auswahl
```

## Funktionen

### 1. Medienordner-Registrierung

**Ordner hinzufügen:**
- Pfad angeben (manuell oder via File Browser)
- Name (optional, verwendet Ordnername falls leer)
- Kategorie auswählen:
  - 💾 **Internal Drive** - Interne Festplatten (C:, D:)
  - 🔌 **USB/External Drive** - USB-Festplatten und externe Laufwerke
  - 🌐 **Network/NAS** - Netzwerkfreigaben, NAS
  - ☁️ **Cloud Storage** - Gemountete Cloud-Ordner (Dropbox, OneDrive, etc.)
  - 📂 **Other** - Sonstige
- Notizen (optional)

**Auto-Erkennung:**
- Kategorie wird automatisch erkannt basierend auf Pfad und Laufwerkstyp
- Volume Label und Serial Number werden bei USB-Laufwerken gespeichert

### 2. Pre-Scan System

**Blur Detection:**
- Scannt alle Fotos mit 3 Methoden parallel:
  - **Laplacian** - Schnell, allgemein
  - **Tenengrad** - Besser für Himmel/homogene Bereiche
  - **ROI** - Adaptiv, beste Ergebnisse für gemischte Szenen

**Sidecar-Dateien:**
- Ergebnisse werden neben jedem Foto gespeichert: `photo.jpg.phototool.json`
- Enthält:
  - Alle 3 Blur-Scores
  - Scan-Datum und Version
  - Foto-Metadaten (Größe, Änderungsdatum)
- Format:
  ```json
  {
    "version": "1.0",
    "photo": {
      "path": "C:/Photos/IMG_1234.jpg",
      "name": "IMG_1234.jpg",
      "size_bytes": 4567890,
      "modified_at": "2024-06-15T14:30:00"
    },
    "scan_info": {
      "scanned_at": "2024-06-20T10:00:00",
      "scanner_version": "1.0.0"
    },
    "analyses": {
      "blur": {
        "laplacian": {
          "score": 125.4,
          "computed_at": "2024-06-20T10:00:00"
        },
        "tenengrad": {
          "score": 45.2,
          "computed_at": "2024-06-20T10:00:00"
        },
        "roi": {
          "score": 87.3,
          "computed_at": "2024-06-20T10:00:00"
        }
      }
    }
  }
  ```

**Performance:**
- Parallel-Verarbeitung mit 4 Threads (konfigurierbar)
- Überspringt bereits gescannte Fotos (außer bei Force-Rescan)
- Erkennt veraltete Scans (Foto wurde nach Scan geändert)
- Echtzeit-Fortschrittsanzeige mit ETA

**Scan-Statistiken:**
- Anzahl gescannter Fotos
- Scan-Coverage pro Analyzer (Blur: 100%)
- Letztes Scan-Datum
- Online/Offline Status

### 3. USB-Laufwerks-Management

**Problem:**
- USB-Laufwerksbuchstaben können sich ändern (E: → F:)
- Lösung: Volume Serial Number wird gespeichert

**Funktionen:**
- Erkennung von Offline-Laufwerken (⚠️ OFFLINE Badge)
- Re-Mapping via Volume Serial wenn verfügbar
- Kategorisierung hilft bei Organisation

## GUI-Elemente

### Media Manager Tab

**Header:**
- "📱 Media Manager" Tab (ganz links)
- Beschreibung: "Register and scan all your media folders"
- ➕ Add Media Folder Button

**Ordner-Cards:**
- Name und Kategorie-Badge
- Pfad (monospace)
- Volume Info (bei USB)
- Status-Badges:
  - ✓ SCANNED - Ordner wurde gescannt
  - ⚠️ OFFLINE - Ordner aktuell nicht verfügbar
- Buttons:
  - 🔍 Scan - Startet Pre-Scan
  - 🗑️ - Entfernt Ordner aus Registry

**Scan-Fortschritt:**
- Progress Bar mit Prozentanzeige
- Aktuell analysierte Datei
- Photos/sec Rate
- ETA in Sekunden

**Statistiken (bei gescannten Ordnern):**
- Anzahl Photos
- Blur Scan Coverage (%)
- Last Scan Datum/Uhrzeit

### Add Media Folder Modal

**Felder:**
1. **Folder Path*** (required)
   - Input Field
   - 📁 Browse Button (öffnet File Browser)

2. **Name** (optional)
   - Verwendet Ordnername falls leer

3. **Category** (Dropdown)
   - 💾 Internal Drive (C:, D:)
   - 🔌 USB/External Drive
   - 🌐 Network/NAS
   - ☁️ Cloud Storage
   - 📂 Other
   - Hinweis: USB volume serial wird automatisch gespeichert

4. **Notes** (optional, Textarea)
   - z.B. "Lumix S5 DCIM from Trekking Trip 2024"

**Buttons:**
- Cancel
- ➕ Add Folder

## API-Endpoints

### GET `/api/media/folders`
Listet alle registrierten Medienordner.

**Response:**
```json
{
  "success": true,
  "folders": [
    {
      "path": "C:/Photos/2024/",
      "name": "2024 Photos",
      "category": "internal",
      "is_scanned": true,
      "scan_date": "2024-06-20T10:00:00",
      "scan_coverage": { "blur": 100.0 },
      "total_photos": 2188,
      "volume_label": null,
      "volume_serial": null,
      "added_at": "2024-06-01T08:00:00",
      "notes": "Main photo archive"
    }
  ],
  "available_count": 3,
  "unavailable_count": 1
}
```

### POST `/api/media/folders`
Fügt Medienordner hinzu.

**Request:**
```json
{
  "path": "C:/Photos/2024/",
  "name": "Optional Name",
  "category": "internal",
  "notes": "Optional notes"
}
```

**Response:**
```json
{
  "success": true,
  "folder": { /* folder object */ }
}
```

### DELETE `/api/media/folders/<path>`
Entfernt Ordner aus Registry (löscht keine Dateien).

### POST `/api/media/folders/<path>/scan`
Startet Pre-Scan eines Medienordners.

**Request:**
```json
{
  "analyzers": ["blur"],
  "force": false,
  "threads": 4
}
```

**Response:**
```json
{
  "success": true,
  "message": "Scan started",
  "folder": "C:/Photos/2024/"
}
```

### GET `/api/media/folders/<path>/scan-progress`
Server-Sent Events (SSE) für Echtzeit-Fortschritt.

**Event Data:**
```json
{
  "status": "running",
  "total": 2188,
  "completed": 450,
  "current_file": "IMG_1234.jpg",
  "current_analyzer": "blur",
  "elapsed_seconds": 120,
  "estimated_remaining_seconds": 180,
  "photos_per_second": 3.75,
  "error_count": 0
}
```

## Backend-Komponenten

### MediaManager (`photo_tool/media/manager.py`)

**Klassen:**
- `FolderCategory(Enum)` - Kategorien
- `MediaFolder` - Ordner-Datenmodell
- `MediaManager` - Hauptverwaltung

**Persistierung:**
- `~/.photo_tool/media/media_folders.json`

**Methoden:**
- `add_folder()` - Registriert Ordner
- `remove_folder()` - Entfernt Ordner
- `update_scan_status()` - Aktualisiert Scan-Status
- `get_available_folders()` - Nur verfügbare Ordner
- `find_folder_by_volume()` - USB-Erkennung via Serial

### SidecarManager (`photo_tool/prescan/sidecar.py`)

**Funktionen:**
- Lädt/Speichert `.phototool.json` Sidecars
- Dot-Notation für Zugriff: `get('blur.laplacian.score')`
- Staleness-Check (Foto nach Scan geändert?)
- Thread-safe für parallele Verarbeitung

### FolderScanner (`photo_tool/prescan/scanner.py`)

**Scan-Prozess:**
1. Entdeckt alle Fotos im Ordner (rekursiv)
2. Filtert bereits gescannte Fotos (skip_existing)
3. Scannt Fotos parallel mit ThreadPoolExecutor
4. Für jedes Foto:
   - Lädt/erstellt Sidecar
   - Führt Blur-Analyzer aus (3 Methoden)
   - Speichert Ergebnisse in Sidecar
5. Aktualisiert Media Manager Status

**Progress Tracking:**
- `ScanProgress` Klasse
- Callback für Echtzeit-Updates
- Berechnet ETA und Rate

## Workflow-Beispiel

### Erste Verwendung

1. **Media Manager Tab öffnen**
   - Klick auf "📱 Media Manager"

2. **Medienordner hinzufügen**
   - Klick "➕ Add Media Folder"
   - Pfad angeben: `E:/DCIM/Lumix_S5/`
   - Kategorie: USB
   - Notizen: "Lumix S5 DCIM"
   - Klick "Add Folder"

3. **Ordner scannen**
   - Klick "🔍 Scan" Button
   - Fortschritt wird live angezeigt
   - Bei 2000 Fotos: ~8-10 Minuten mit 4 Threads
   - Kann über Nacht laufen für große Archive

4. **Weitere Ordner hinzufügen**
   - Samsung Galaxy S22 Camera
   - DJI ActionCam
   - DJI 360 OSMO
   - Alle scannen

### Workspace erstellen

5. **Workspaces Tab**
   - Neuer Workspace: "Trekking-Reise 2024"
   - Aktiviere alle relevanten Ordner:
     - ✓ Lumix S5
     - ✓ Samsung Galaxy
     - ✓ DJI ActionCam
     - ✓ DJI 360 OSMO
   - **Vorteil:** Blur-Scores sind bereits verfügbar!

### Projekt erstellen

6. **Projects Tab**
   - Neues Projekt: "Web-Galerie Trekking"
   - Blur-Threshold anpassen (bereits berechnet!)
   - Fotos selektieren
   - Galerie exportieren

## Vorteile

### ✅ Zeit-Ersparnis
- Pre-Scan läuft einmalig (nachts)
- Blur-Scores sofort verfügbar beim Erstellen neuer Projekte
- Kein Warten bei Foto-Selektion

### ✅ Flexibilität
- Mehrere Workspaces können dieselben Medienordner verwenden
- Blur-Scores sind absolute Werte (unabhängig vom Projekt)
- 3 Methoden ermöglichen beste Auswahl je nach Foto-Art

### ✅ USB-Freundlich
- Volume Serial ermöglicht Erkennung trotz Laufwerksbuchstaben-Änderung
- Offline-Anzeige wenn USB nicht verbunden
- Automatische Kategorisierung

### ✅ Skalierbar
- Parallel-Verarbeitung
- Skip-existing für inkrementelle Scans
- Staleness-Check für geänderte Fotos

### ✅ Erweiterbar
- Sidecar-System bereit für weitere Analyzer:
  - Burst-Detection
  - Histogram
  - EXIF-Extraktion
  - Face-Detection
  - etc.

## Nächste Schritte (Phase 2+)

1. **Burst-Analyzer** im Pre-Scan
2. **Histogram-Analyzer** für Belichtung
3. **EXIF-Bulk-Extraktion**
4. **Face-Detection** (optional)
5. **CLI-Tool** für Batch-Scans
6. **Background-Scan** während GUI läuft
7. **Scan-Scheduler** (automatisch neue Fotos)

## Installation/Setup

### Abhängigkeiten

Optional (für USB-Laufwerks-Erkennung):
```bash
pip install pywin32
```

Ohne `pywin32`:
- Kategorie-Erkennung verwendet Fallback (C: = Internal, andere = USB)
- Volume Serial wird nicht gespeichert
- Alle anderen Funktionen arbeiten normal

### Start

```bash
cd c:\_Git\Python-tools
python gui_poc/server.py
```

Öffne Browser: `http://localhost:8000`

## Datenspeicherung

### Media Manager
```
C:/Users/<user>/.photo_tool/media/
├── media_folders.json      # Registry aller Ordner
```

### Sidecars
```
C:/Photos/2024/
├── IMG_1234.jpg
├── IMG_1234.jpg.phototool.json  # Sidecar mit Blur-Scores
├── IMG_1235.jpg
├── IMG_1235.jpg.phototool.json
...
```

## Troubleshooting

### Problem: "Scan bleibt hängen"
- Check: Sind alle Fotos lesbar?
- Lösung: Error-Count in Progress anzeigen

### Problem: "USB-Laufwerk nicht erkannt"
- Check: `pywin32` installiert?
- Lösung: Manuell Kategorie auf "usb" setzen

### Problem: "Ordner zeigt OFFLINE"
- Check: Ist USB-Laufwerk angeschlossen?
- Check: Stimmt der Pfad noch?
- Lösung: Ordner neu hinzufügen falls Pfad geändert

### Problem: "Scan ist langsam"
- Lösung 1: Threads erhöhen (4 → 8)
- Lösung 2: Über Nacht laufen lassen
- Lösung 3: skip_existing=True verwenden

## Fazit

Der **Media Manager** ist die ideale Basis für ein professionelles DAM-System. Die Pre-Scan Architektur ermöglicht:

- **Schnelle** Projekt-Erstellung
- **Flexible** Workspace-Organisation
- **Zuverlässige** USB-Verwaltung
- **Skalierbare** Analyse-Pipeline

Perfekt für große Foto-Archive und Multi-Kamera Workflows! 🎉
