# Photo Tool - Configuration & Storage Guide

## Übersicht der Speicherorte

Das Photo Tool verwendet eine hierarchische Struktur für alle Konfigurationsdateien und Metadaten.

---

## 1. Globale Konfiguration (User Home Directory)

**Basis-Pfad**: `%USERPROFILE%\.photo_tool\`  
(Windows: `C:\Users\<username>\.photo_tool\`)

### 1.1 Media Manager Configuration
```
%USERPROFILE%\.photo_tool\media\media_folders.json
```

**Zweck**: Zentrale Registry aller registrierten Media-Folder

**Struktur**:
```json
{
  "version": "1.0",
  "updated": "2026-02-05T10:30:00",
  "folders": [
    {
      "path": "E:\\Lumix-2026-01",
      "name": "Lumix S5 Jan 2026",
      "category": "usb",
      "is_scanned": true,
      "scan_date": "2026-02-05T10:15:00",
      "scan_coverage": {
        "blur": 1.0,
        "burst": 0.0
      },
      "total_photos": 961,
      "total_videos": 0,
      "total_audio": 0,
      "total_size_bytes": 1234567890,
      "volume_label": "LUMIX",
      "volume_serial": "1A2B3C4D",
      "added_at": "2026-02-05T09:00:00",
      "last_accessed": "2026-02-05T10:30:00",
      "notes": "Camera SD Card"
    }
  ]
}
```

**Verwaltung durch**: `photo_tool.media.manager.MediaManager`

---

### 1.2 Workspace Registry
```
%USERPROFILE%\.photo_tool\workspaces.json
```

**Zweck**: Liste aller Workspaces + aktuell aktiver Workspace

**Struktur**:
```json
{
  "workspaces": [
    "C:\\Photos\\Nepal-2025",
    "C:\\Photos\\Japan-2024",
    "D:\\Projects\\Wedding-Photos"
  ],
  "current_workspace": "C:\\Photos\\Nepal-2025"
}
```

**Verwaltung durch**: `photo_tool.workspace.manager.WorkspaceManager`

---

## 2. Workspace-Spezifische Konfiguration

**Pfad**: `<workspace_path>\config.yaml`

Jeder Workspace hat seine eigene Konfigurationsdatei im Workspace-Verzeichnis selbst.

### Beispiel: `C:\Photos\Nepal-2025\config.yaml`

```yaml
# Workspace Configuration
workspace:
  name: "Nepal Trekking 2025"
  created: "2026-02-05"
  description: "Annapurna Circuit Trek"

# Media folders linked to this workspace
folders:
  - path: "E:\\Lumix-2026-01\\101_PANA"
    enabled: true
    photo_count: 961
    last_scan: "2026-02-05T10:15:00"
  
  - path: "E:\\NEPAL-2025\\Galaxy-S22"
    enabled: true
    photo_count: 1227
    last_scan: "2026-02-04T18:30:00"

# Projects in this workspace
projects:
  default:
    name: "All Photos"
    created: "2026-02-05"
    
    # Blur detection settings (per project)
    blur_detection:
      method: "laplacian"
      threshold: 50
      enabled: true
    
    # Burst detection settings (per project)
    burst_detection:
      time_threshold: 2.0
      similarity_threshold: 0.85
      enabled: true
    
    # Export settings
    export:
      slideshow_duration: 3
      transition_effect: "fade"
      music_file: null

# Scan settings
scan:
  recursive: true
  extensions:
    - "*.jpg"
    - "*.jpeg"
    - "*.png"
    - "*.raw"
    - "*.arw"
```

**Verwaltung durch**: `photo_tool.config.load.load_config()` und `save_config()`

---

## 3. Photo-Sidecar Files (Analyse-Metadaten)

**Pfad**: `<photo_directory>\<photo_filename>.phototool.json`

Jedes Foto erhält ein Sidecar-File mit allen Analyseergebnissen.

### Beispiel: `E:\Lumix-2026-01\101_PANA\P1012569.JPG.phototool.json`

```json
{
  "scan_info": {
    "scanned_at": "2026-02-05T10:15:23",
    "scanner_version": "1.0.0",
    "updated_at": "2026-02-05T10:15:23"
  },
  
  "analyses": {
    "blur": {
      "laplacian": {
        "score": 123.45,
        "is_blurred": false
      },
      "tenengrad": {
        "score": 234.56,
        "is_blurred": false
      },
      "roi": {
        "score": 345.67,
        "is_blurred": false
      },
      "computed_at": "2026-02-05T10:15:23"
    },
    
    "burst": {
      "is_burst": true,
      "group_id": "burst_20260105_140530",
      "group_size": 5,
      "position": 2,
      "neighbors": {
        "prev": "P1012568.JPG",
        "next": "P1012570.JPG"
      },
      "similarity_scores": {
        "prev": 0.92,
        "next": 0.89
      },
      "computed_at": "2026-02-05T10:16:45"
    }
  },
  
  "exif": {
    "capture_time": "2026-01-05T14:05:30",
    "camera_model": "Lumix S5",
    "lens": "20-60mm",
    "iso": 800,
    "focal_length": 35,
    "aperture": 5.6,
    "shutter_speed": "1/200"
  }
}
```

**Zweck**: 
- Speichert **alle** Analyse-Scores (blur, burst, histogramme, etc.)
- Bleibt persistent, auch wenn Foto in andere Workspaces/Projekte eingebunden wird
- Ermöglicht dynamisches Thresholding ohne Re-Scan
- Portable mit dem Foto (kann gemeinsam kopiert/verschoben werden)

**Verwaltung durch**: `photo_tool.prescan.sidecar.SidecarManager`

---

## 4. Project-Spezifische Daten (zukünftig)

**Pfad**: `<workspace_path>\projects\<project_name>\`

Für zukünftige Features:
- Photo-Selections pro Projekt
- Export-Caches
- Gallery-Exports
- Slideshow-Konfigurationen

---

## Hierarchie Zusammenfassung

```
%USERPROFILE%\.photo_tool\              # Global config root
├── media\
│   └── media_folders.json              # Media Manager: Alle registrierten Folders
├── workspaces.json                     # Workspace Registry: Liste aller Workspaces
└── (optional: global settings)

C:\Photos\Nepal-2025\                   # Workspace Directory
├── config.yaml                         # Workspace + Project configs
└── projects\                           # (zukünftig)
    ├── default\
    ├── gallery-web\
    └── slideshow-family\

E:\Lumix-2026-01\101_PANA\             # Media Folder (z.B. USB SD-Card)
├── P1012569.JPG                        # Original Photo
├── P1012569.JPG.phototool.json        # Sidecar: Blur/Burst/EXIF Scores
├── P1012570.JPG
├── P1012570.JPG.phototool.json
└── ...
```

---

## Vorteile dieser Architektur

### 1. **Separation of Concerns**
- **Media Manager**: Verwaltet physische Speicherorte
- **Workspace**: Logische Gruppierung von Media-Folders
- **Project**: Selektionen und Export-Einstellungen
- **Sidecar**: Foto-spezifische Metadaten

### 2. **Portabilität**
- Sidecar-Files bleiben beim Foto (USB-Stick, Backup, etc.)
- Workspaces sind unabhängig von Media-Ordnern
- USB-Drive Letter-Änderungen werden erkannt (Volume-Serial)

### 3. **Performance**
- Pre-Scan einmal, nutzen überall
- Blur/Burst-Scores werden nur einmal berechnet
- Dynamisches Thresholding ohne Re-Computation

### 4. **Flexibilität**
- Gleicher Media-Folder in mehreren Workspaces
- Verschiedene Projekte mit unterschiedlichen Blur-Thresholds
- Individuelle Export-Settings pro Projekt

---

## Config-Pfade zur Laufzeit ermitteln

### Python API:
```python
from photo_tool.media import MediaManager
from photo_tool.workspace.manager import WorkspaceManager
from pathlib import Path

# Media Manager Config
mm = MediaManager()
print(f"Media Config: {mm.config_file}")
# → C:\Users\<user>\.photo_tool\media\media_folders.json

# Workspace Registry
wm = WorkspaceManager()
print(f"Workspace Registry: {wm.workspaces_file}")
# → C:\Users\<user>\.photo_tool\workspaces.json

# Aktueller Workspace Config
workspace_path = Path(wm.current_workspace)
config_path = workspace_path / "config.yaml"
print(f"Workspace Config: {config_path}")
# → C:\Photos\Nepal-2025\config.yaml

# Sidecar für Foto
from photo_tool.prescan.sidecar import SidecarManager
photo = Path("E:/Lumix-2026-01/101_PANA/P1012569.JPG")
sidecar = SidecarManager(photo)
print(f"Sidecar: {sidecar.sidecar_path}")
# → E:\Lumix-2026-01\101_PANA\P1012569.JPG.phototool.json
```

---

## Backup-Empfehlungen

### Was sollte gesichert werden?

1. **Global Config** (klein, wichtig)
   - `%USERPROFILE%\.photo_tool\` komplett

2. **Workspace Configs** (klein, wichtig)
   - Jede `<workspace>\config.yaml`

3. **Sidecar Files** (groß, wertvoll)
   - Alle `.phototool.json` Files mit den Original-Fotos zusammen
   - Bei Backup der Fotos **immer** die Sidecars inkludieren!

### Backup-Strategie:
```bash
# Backup Global Configs
robocopy %USERPROFILE%\.photo_tool\ D:\Backup\phototool-config\ /MIR

# Backup Workspace + Sidecars
robocopy E:\Lumix-2026-01\ D:\Backup\photos\ /MIR /XF *.tmp
```

---

## Troubleshooting

### Config-Location prüfen:
```python
from pathlib import Path
print(f"Home: {Path.home()}")
print(f"Photo Tool Config: {Path.home() / '.photo_tool'}")
```

### Configs zurücksetzen:
```bash
# ACHTUNG: Löscht alle Configs!
rmdir /s %USERPROFILE%\.photo_tool
```

### Einzelne Komponente zurücksetzen:
```bash
# Nur Media Manager
del %USERPROFILE%\.photo_tool\media\media_folders.json

# Nur Workspaces
del %USERPROFILE%\.photo_tool\workspaces.json
```

---

## Änderungshistorie

- **2026-02-05**: Initiale Dokumentation (Phase 1 + 2)
- Media Manager + Workspace Registry implementiert
- Sidecar-System für Blur + Burst Detection
