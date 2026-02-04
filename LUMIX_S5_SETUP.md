# Photo Tool Setup für Lumix S5

Spezielle Anleitung für die Verwaltung von Lumix S5 Fotos, Videos und Audio (komplette DaVinci Resolve Projekte).

## Typische Lumix S5 Ordnerstruktur

```
F:\                         (SD-Karte oder externe Disk)
└── DCIM\
    ├── 100_PANA\
    │   ├── P1010001.JPG    (Foto)
    │   ├── P1010002.JPG
    │   ├── P1010003.MP4    (Video)
    │   └── ...
    ├── 101_PANA\
    │   ├── P1010100.JPG
    │   ├── P1010101.MP4
    │   └── ...
    └── 999_PANA\
```

## Schnell-Setup

### 1. Workspace erstellen

```powershell
# Workspace auf schneller interner Disk
photo-tool workspace init D:\Lumix_Workspace --root "F:\DCIM"
```

### 2. Config anpassen

Öffne `D:\Lumix_Workspace\config.yaml`:

```yaml
workspace:
  path: "D:/Lumix_Workspace"

scan:
  roots:
    - "F:/DCIM"              # Deine SD-Karte/USB-Disk
    - "F:/AUDIO"             # Falls du Audio-Aufnahmen hast
  extensions:
    # Lumix S5 Fotos
    - ".jpg"
    - ".jpeg"
    # Lumix S5 Videos
    - ".mp4"                 # Standard Video
    - ".mov"                 # High FPS / RAW Video
    # Audio (optional, für DaVinci Resolve Projekte)
    - ".wav"                 # Professionell
    - ".mp3"                 # Musik/SFX
  recurse: true              # Durchsucht alle 10X_PANA Ordner

grouping:
  time_window_seconds: 3.0   # Lumix S5 Burst: ~9 fps
  max_group_gap_seconds: 2.0

similarity:
  method: "phash"
  phash_threshold: 6         # Standard

quality:
  blur_method: "laplacian"
  blur_threshold: 120.0      # Für 24MP anpassen (ggf. 150-200)

actions:
  dry_run: true              # Sicherheit zuerst!
  burst_folder_naming: "first_filename"
  min_group_size: 2
```

### 3. Scannen

```powershell
photo-tool scan --workspace D:\Lumix_Workspace

# Output:
# ✓ Found 1247 files:
#   Photos: 1053
#   Videos: 194
```

## Typische Workflows

### Workflow 1: Nach dem Shooting

```powershell
# 1. SD-Karte anschließen (F:\)
# 2. Scannen
photo-tool scan --workspace D:\Lumix_Workspace

# 3. Bursts finden
photo-tool analyze bursts

# 4. Vorschau
photo-tool organize bursts --dry-run

# 5. Anwenden
photo-tool organize bursts --apply

# 6. Report generieren
photo-tool report generate --format html

# 7. Report öffnen
start D:\Lumix_Workspace\reports\cluster_report.html
```

### Workflow 2: Videos + Audio für DaVinci Resolve vorbereiten

```powershell
# 1. Workspace für komplettes Projekt
photo-tool workspace init D:\Project_2024 --root "F:\"

# Config editieren:
# scan:
#   roots: ["F:/DCIM", "F:/AUDIO"]
#   extensions: [".mp4", ".mov", ".wav", ".mp3"]

# 2. Scannen
photo-tool scan
# ✓ Found 523 files:
#   Videos: 194
#   Audio: 329

# 3. Videos auflisten
photo-tool video list --sort duration

# 4. Audio auflisten
photo-tool audio list --sort duration

# 5. Bewerten
photo-tool rate set F:\DCIM\VIDEO001.mp4 --stars 5
photo-tool rate set F:\AUDIO\music_intro.wav --stars 5 --comment "Intro music"
photo-tool rate set F:\AUDIO\voiceover.wav --stars 5 --comment "Final take"

# 6. Später: Nur 4-5 Sterne in DaVinci importieren
```

### Workflow 3: Unscharfe Fotos finden

```powershell
# Qualitätsanalyse
photo-tool analyze quality --top 50

# Output: Top 50 unscharfste Fotos
# #  Photo           Blur Score
# 1  P1010234.JPG    45.23      (sehr unscharf!)
# 2  P1010456.JPG    67.89
# ...
# 50 P1010789.JPG    118.45     (noch okay)

# Diese dann manuell prüfen und löschen/behalten
```

## Lumix S5 Spezifika

### Foto-Modi

| Modus | Format | Burst-Rate | Empfohlene Settings |
|-------|--------|------------|---------------------|
| **Einzelbild** | JPG | - | Standard |
| **Burst Low** | JPG | 6 fps | time_window: 3.0 |
| **Burst High** | JPG | 9 fps | time_window: 2.0 |
| **6K Photo** | JPG | 18/30 fps | time_window: 5.0, min_group_size: 5 |

### Video-Modi

| Modus | Format | Auflösung | Empfehlung |
|-------|--------|-----------|------------|
| **4K 60p** | MP4 | 3840x2160 | Hauptformat |
| **FHD 180fps** | MP4 | 1920x1080 | Slow-Motion |
| **4K ProRes** | MOV | 3840x2160 | High Quality |
| **V-Log** | MP4/MOV | variabel | Farbkorrektur |

### EXIF/Metadata

Lumix S5 speichert:
- ✅ **Fotos**: Vollständige EXIF-Daten
- ✅ **Videos**: Creation Date, Duration, Resolution
- ✅ **Kamera-Modell**: "DC-S5"
- ✅ **Objektiv**: Z.B. "LUMIX S 20-60mm F3.5-5.6"

## Kalibrierung für Lumix S5

### Blur-Threshold anpassen

```powershell
# Standard-Test mit 10 Fotos
photo-tool analyze quality --top 10

# Notiere die Scores
# Scharf: 180-250
# OK: 120-180
# Unscharf: < 120

# In config.yaml anpassen:
quality:
  blur_threshold: 150.0    # Anpassen basierend auf deinen Werten
```

### Burst-Erkennung testen

```powershell
# Test mit verschiedenen Zeitfenstern
photo-tool analyze bursts --time-window 2.0   # Streng (9fps Burst)
photo-tool analyze bursts --time-window 3.0   # Standard
photo-tool analyze bursts --time-window 5.0   # Locker (6K Photo)

# Wenn zu viele Gruppen: time_window verkleinern
# Wenn zu wenige Gruppen: time_window vergrößern
```

## Ordnerstruktur nach Organisation

### Vorher (DCIM original)

```
F:\DCIM\100_PANA\
├── P1010001.JPG
├── P1010002.JPG  (Burst mit 001)
├── P1010003.JPG  (Burst mit 001-002)
├── P1010004.JPG
├── P1010005.MP4  (Video)
└── P1010006.JPG
```

### Nachher (nach organize bursts)

```
F:\DCIM\100_PANA\
├── P1010001\              (Burst-Ordner)
│   ├── P1010001.JPG      (bestes Foto markiert)
│   ├── P1010002.JPG
│   └── P1010003.JPG
├── P1010004.JPG           (Einzelfoto, bleibt außen)
├── P1010005.MP4           (Video, unverändert)
└── P1010006.JPG           (Einzelfoto)
```

## ffmpeg Installation für Video-Metadaten

### Windows (empfohlen)

**Option 1: Winget (Windows 11)**
```powershell
winget install ffmpeg
```

**Option 2: Chocolatey**
```powershell
choco install ffmpeg
```

**Option 3: Manuell**
1. Download: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
2. Entpacken nach `C:\ffmpeg\`
3. Zu PATH hinzufügen:
   - Windows-Taste → "Umgebungsvariablen"
   - PATH bearbeiten
   - Neu: `C:\ffmpeg\bin`
   - OK

**Verifizieren:**
```powershell
ffprobe -version
# Output: ffprobe version ...
```

### Ohne ffmpeg

Photo Tool funktioniert auch ohne ffmpeg:
- ✅ Thumbnails (OpenCV)
- ✅ Datei-Größe, Datum
- ❌ Keine Dauer, Auflösung, Codec-Info

## Beispiel: Shooting-Tag organisieren

```powershell
# Morgens: SD-Karte von Lumix S5 anschließen
# F:\DCIM\10X_PANA\ enthält 500 JPG + 50 MP4

# 1. Workspace erstellen
photo-tool workspace init D:\Shooting_2024-02-04 --root "F:\DCIM"

# 2. Scannen
photo-tool scan --workspace D:\Shooting_2024-02-04
# ✓ Found 550 files:
#   Photos: 500
#   Videos: 50

# 3. Fotos: Bursts finden und organisieren
photo-tool analyze bursts
photo-tool organize bursts --dry-run
photo-tool organize bursts --apply

# 4. Fotos: Unscharfe finden
photo-tool analyze quality --top 20

# 5. Videos: Übersicht
photo-tool video list --sort duration

# 6. Videos: Die besten bewerten
photo-tool rate set F:\DCIM\100_PANA\VIDEO003.mp4 --stars 5
photo-tool rate set F:\DCIM\100_PANA\VIDEO007.mp4 --stars 5

# 7. Report
photo-tool report generate --format html
start D:\Shooting_2024-02-04\reports\cluster_report.html

# 8. Abends: Nur 4-5 Sterne Videos in DaVinci Resolve importieren
```

## Tipps für Lumix S5

### 1. Regelmäßig scannen

```powershell
# Nach jedem Shooting-Tag:
photo-tool scan --workspace D:\Current_Project
```

### 2. Verschiedene Workspaces für verschiedene Projekte

```
D:\PhotoWorkspaces\
├── Event_Hochzeit\         (nur die 500 Event-Fotos)
├── Landscape_2024\         (nur Landschaftsfotos)
└── Archive_All\            (alle Fotos für Duplikat-Check)
```

### 3. Blur-Threshold für 24MP kalibrieren

Lumix S5 hat 24 Megapixel. Typische Werte:
- **Sehr scharf**: > 200
- **Scharf**: 150-200
- **OK**: 100-150
- **Unscharf**: < 100

Teste mit deinen Fotos und passe an!

### 4. 6K Photo Modus

Wenn du 6K Photo (18 fps) nutzt:

```yaml
grouping:
  time_window_seconds: 5.0      # Längere Sequenzen
  max_group_gap_seconds: 1.0    # Kleine Lücken erlaubt

actions:
  min_group_size: 5             # Mindestens 5 Fotos = 1 Gruppe
```

## Fehlerbehebung

### "No videos found" obwohl Videos da sind

```yaml
# Prüfe extensions in config.yaml
extensions:
  - ".mp4"    # Kleingeschrieben!
  - ".MP4"    # Oder Großgeschrieben explizit angeben
```

### Langsame Video-Scans

Erste Scan generiert Thumbnails (langsam).
Nachfolgende Scans nutzen Cache (schnell).

### Laufwerksbuchstabe ändert sich

```yaml
# Statt Laufwerksbuchstabe: Volume-Label nutzen (Windows)
# Oder: Fester USB-Port + Registry-Eintrag

# Oder: Kopiere DCIM auf interne Disk
xcopy /E /I F:\DCIM E:\Lumix_Backup\DCIM
```

## Workflow: DaVinci Resolve Integration

### 1. Vorsortierung mit Photo Tool

```powershell
# Videos bewerten
photo-tool video list
photo-tool rate set VIDEO001.mp4 --stars 5
photo-tool rate set VIDEO002.mp4 --stars 4
photo-tool rate set VIDEO003.mp4 --stars 1  # Aussortiert
```

### 2. Export-Script für DaVinci

```python
# export_for_resolve.py
from pathlib import Path
from photo_tool.actions.rating import get_rating
import shutil

source = Path("F:/DCIM")
target = Path("D:/DaVinci/Import")

for video in source.rglob("*.mp4"):
    rating = get_rating(video)
    if rating and rating >= 4:
        shutil.copy2(video, target / video.name)
        print(f"Copied: {video.name} (Rating: {rating})")
```

### 3. In DaVinci Resolve importieren

Nur die 4-5 Sterne Videos aus `D:\DaVinci\Import\`

## See Also

- [VIDEO_SUPPORT.md](VIDEO_SUPPORT.md) - Detaillierte Video-Dokumentation
- [AUDIO_SUPPORT.md](AUDIO_SUPPORT.md) - Audio-Datei-Verwaltung
- [GETTING_STARTED.md](GETTING_STARTED.md) - Allgemeine Anleitung
- [QUICKSTART.md](QUICKSTART.md) - 5-Minuten-Start

---

**Optimiert für:** Panasonic Lumix S5, S5II, S5IIX  
**Getestet mit:** SD-Karte, USB-C Disk, DCIM-Struktur
