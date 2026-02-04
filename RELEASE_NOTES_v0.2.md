# Photo Tool v0.2.0 - Video Support Release

## 🎥 Neu: Video-Verwaltung!

Photo Tool kann jetzt Videos **zusammen mit Fotos** verwalten - perfekt für Lumix S5 DCIM-Ordner!

## Was ist neu?

### Video-Features

✅ **Scannen**: Videos (.mp4, .mov, .avi, etc.) werden erkannt  
✅ **Metadaten**: Dauer, Auflösung, Codec, Frame-Rate  
✅ **Thumbnails**: Erster Frame als Vorschau  
✅ **Rating**: Videos bewerten für DaVinci Resolve Workflow  
✅ **Gemischte Medien**: Fotos und Videos in einem Workspace  

### Neue Commands

```powershell
# Video-Info anzeigen
photo-tool video info VIDEO001.mp4

# Alle Videos auflisten
photo-tool video list --sort duration

# Videos bewerten
photo-tool rate set VIDEO001.mp4 --stars 5
photo-tool rate get VIDEO001.mp4
```

### Intelligentes Filtern

Foto-Analyse überspringt automatisch Videos:

```powershell
photo-tool scan
# ✓ Found 1247 files:
#   Photos: 1053
#   Videos: 194

photo-tool analyze bursts
# Note: Skipping 194 video files (not applicable for burst detection)
# → Analysiert nur die 1053 Fotos!
```

## Quick Start mit Videos

```powershell
# 1. Workspace erstellen
photo-tool workspace init D:\MyMedia --root "F:\DCIM"

# 2. Config editieren (Video-Extensions hinzufügen)
notepad D:\MyMedia\config.yaml
# extensions: [".jpg", ".jpeg", ".mp4", ".mov"]

# 3. Scannen
photo-tool scan --workspace D:\MyMedia

# 4. Fotos analysieren (Videos werden übersprungen)
photo-tool analyze bursts

# 5. Videos auflisten
photo-tool video list --sort duration

# 6. Videos bewerten
photo-tool rate set F:\DCIM\100_PANA\VIDEO001.mp4 --stars 5
```

## Lumix S5 Optimiert

Perfekt für DCIM-Ordner mit gemischten Inhalten:

```
F:\DCIM\100_PANA\
├── P1010001.JPG    ✅ Foto
├── P1010002.JPG    ✅ Foto (Burst)
├── P1010003.JPG    ✅ Foto (Burst)
├── P1010004.MP4    ✅ Video (4K 60fps)
├── P1010005.MOV    ✅ Video (HFR 180fps)
└── ...

→ Photo Tool verwaltet ALLES!
```

## Technische Details

### Unterstützte Video-Formate

- **MP4** - Lumix S5 Standard
- **MOV** - Lumix S5 High-Quality/ProRes
- **AVI** - Legacy
- **MKV** - Container
- **MTS/M2TS** - AVCHD
- **WEBM** - Web

### Metadaten-Extraktion

**Mit ffprobe (empfohlen):**
```
Duration:      00:05:23
Resolution:    3840x2160
Frame Rate:    29.97 fps
Codec:         h264
Bit Rate:      85.3 Mbps
Size:          2.3 GB
```

**Ohne ffprobe (Basis):**
```
Size:          2.3 GB
Captured:      2024-12-25 14:30:45
```

### Installation ffprobe (optional)

**Windows:**
```powershell
winget install ffmpeg
```

**Siehe:** [INSTALL_FFMPEG.md](INSTALL_FFMPEG.md) für Details

## Migration von v0.1

### Automatische Kompatibilität

Bestehende Workspaces funktionieren weiter:
- ✅ PhotoFile → MediaFile (Alias)
- ✅ Alte Commands unverändert
- ✅ Configs funktionieren
- ✅ Keine Breaking Changes

### Config updaten (optional)

```yaml
# Alte config.yaml (v0.1)
scan:
  extensions: [".jpg", ".jpeg", ".png"]

# Neue config.yaml (v0.2) - Videos hinzufügen
scan:
  extensions: [".jpg", ".jpeg", ".png", ".mp4", ".mov"]
```

Oder lass es wie es ist - dann werden nur Fotos gescannt.

## Bekannte Einschränkungen (v0.2)

❌ **Keine Content-basierte Video-Duplikat-Erkennung**  
❌ **Keine Video-Qualitätsanalyse** (Bitrate-Check, etc.)  
❌ **Keine Szenen-Erkennung**  
❌ **Kein Transcoding**  

**Kommt in v0.3+**

## Breaking Changes

Keine! v0.2 ist voll kompatibel mit v0.1.

## Upgrade

```powershell
# Im Git-Repo
cd C:\_Git\Python-tools
git pull

# Neu installieren
pip install -e ".[dev]"

# Version prüfen
photo-tool version
# Photo Tool v0.2.0
```

## Dokumentation

- **VIDEO_SUPPORT.md** - Komplette Video-Anleitung
- **LUMIX_S5_SETUP.md** - Spezifisch für Lumix S5
- **INSTALL_FFMPEG.md** - ffmpeg Installation

## Feedback

Video-Support ist NEU! Bitte teste und gib Feedback:
- GitHub Issues: Bug-Reports
- GitHub Discussions: Feature-Wünsche
- Pull Requests: Verbesserungen

## Roadmap

### v0.3 - Enhanced Video (nächste 4-8 Wochen)
- Szenen-Erkennung
- Video-Duplikat-Erkennung (Content-based)
- Proxy-Generierung
- Qualitäts-Metriken

### v1.0 - Web Application
- Browser-GUI
- Filmstrip-Ansicht für Videos
- Timeline-Integration
- DaVinci Resolve XML-Export

---

**Release Date:** 4. Februar 2026  
**Version:** 0.2.0  
**Status:** Stable, ready for production use  

Viel Spaß mit Video-Support! 🎬
