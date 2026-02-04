# Photo Tool v0.2.1 - Audio Support Release

## 🎵 Neu: Audio-Dateien-Verwaltung!

Photo Tool kann jetzt **Fotos, Videos UND Audio** zusammen verwalten - perfekt für komplette DaVinci Resolve Projekte!

## Was ist neu?

### Audio-Features

✅ **Scannen**: Audio-Dateien (.mp3, .wav, .flac, .m4a, etc.) werden erkannt  
✅ **Metadaten**: Titel, Artist, Album, Genre, Dauer, Sample-Rate, Codec  
✅ **Rating**: Audio-Dateien bewerten und kommentieren  
✅ **Komplette Projekte**: Videos + Audio für DaVinci Resolve  
✅ **Musik-Bibliotheken**: Organisiere deine Musik-Sammlung  

### Neue Commands

```powershell
# Audio-Info anzeigen
photo-tool audio info recording.mp3

# Alle Audio-Dateien auflisten
photo-tool audio list --sort duration

# Audio-Dateien bewerten
photo-tool rate set music.mp3 --stars 5 --comment "Perfect intro"
```

### Intelligentes Filtern

Audio-Dateien werden automatisch bei Foto-Analysen übersprungen:

```powershell
photo-tool scan
# ✓ Found 1523 files:
#   Photos: 450
#   Videos: 73
#   Audio: 1000

photo-tool analyze bursts
# Note: Skipping 1073 video/audio files
# → Analysiert nur die 450 Fotos!
```

## Quick Start mit Audio

```powershell
# 1. Workspace erstellen
photo-tool workspace init D:\MyProject

# 2. Config editieren (Audio-Extensions hinzufügen)
notepad D:\MyProject\config.yaml
# extensions: [".jpg", ".mp4", ".mov", ".wav", ".mp3"]

# 3. Scannen
photo-tool scan --workspace D:\MyProject

# 4. Audio auflisten
photo-tool audio list --sort duration

# 5. Audio bewerten
photo-tool rate set F:\Audio\intro.wav --stars 5 --comment "Use this"
```

## DaVinci Resolve Workflow

Perfekt für komplette Video-Projekte mit Audio:

```powershell
# Projekt-Workspace
photo-tool workspace init D:\Film_Project

# Config:
# scan:
#   roots: ["F:/Video", "F:/Audio", "F:/Photos"]
#   extensions: [".mp4", ".mov", ".wav", ".mp3", ".jpg"]

# Scannen
photo-tool scan
# ✓ Found 856 files:
#   Photos: 123
#   Videos: 194
#   Audio: 539

# Organisieren
photo-tool video list --sort date
photo-tool audio list --sort duration

# Bewerten
photo-tool rate set VIDEO001.mp4 --stars 5
photo-tool rate set music_intro.wav --stars 5
photo-tool rate set voiceover.wav --stars 5 --comment "Final take"

# Nur 5-Sterne in DaVinci importieren!
```

## Unterstützte Audio-Formate

### DaVinci Resolve Kompatibel
- ✅ **WAV** - Beste Wahl für DaVinci
- ✅ **AAC/M4A** - Moderne Alternative
- ⚠️ **MP3** - Funktioniert, aber WAV besser

### Weitere Formate
- **FLAC** - Lossless (konvertieren für DaVinci)
- **OGG** - Open Source (konvertieren)
- **OPUS** - Modern (konvertieren)

## Typische Use Cases

### 1. DaVinci Resolve Projekt

```
D:\Film_Project\
├── Video\
│   ├── CLIP001.mp4    → rate 5 stars
│   └── CLIP002.mp4    → rate 4 stars
├── Audio\
│   ├── music_intro.wav    → rate 5 stars "Intro"
│   ├── sfx_wind.wav       → rate 4 stars "Background"
│   └── voiceover.wav      → rate 5 stars "Final take"
└── Photos\
    └── still_001.jpg      → rate 4 stars "B-roll"
```

### 2. Musik-Bibliothek

```powershell
photo-tool workspace init D:\Music --root "D:\Music"
photo-tool scan
# ✓ Found 5000 files:
#   Audio: 5000

photo-tool audio list
photo-tool rate set "favorite_song.mp3" --stars 5
```

### 3. Field Recordings

```powershell
photo-tool workspace init D:\Recordings --root "F:\Recorder"
photo-tool scan
# ✓ Found 47 files:
#   Audio: 47

photo-tool audio list --sort date
photo-tool rate set recording_001.wav --stars 5 --comment "Perfect ambience"
```

### 4. Podcast Production

```powershell
photo-tool workspace init D:\Podcast_Ep05
photo-tool scan
# ✓ Found 12 files:
#   Audio: 12

photo-tool audio info host_intro_take2.wav
photo-tool rate set host_intro_take2.wav --stars 5 --comment "Best take"
```

## Metadaten-Extraktion

### Mit ffprobe (empfohlen):

```
Filename      recording.mp3
Size          4.2 MB
Duration      00:03:45
Title         My Recording
Artist        John Doe
Album         Field Recordings 2024
Genre         Ambient
Sample Rate   48.0 kHz
Channels      Stereo
Codec         mp3
Bit Rate      320 kbps
```

### Ohne ffprobe (Basis):

```
Filename      recording.mp3
Size          4.2 MB
Date          2024-12-25 14:30:45
```

## Migration von v0.2.0

### Automatische Kompatibilität

Bestehende Workspaces funktionieren weiter:
- ✅ Keine Breaking Changes
- ✅ Alte Commands unverändert
- ✅ Configs funktionieren

### Config updaten (optional)

```yaml
# Alte config.yaml (v0.2.0)
scan:
  extensions: [".jpg", ".jpeg", ".mp4", ".mov"]

# Neue config.yaml (v0.2.1) - Audio hinzufügen
scan:
  extensions: [".jpg", ".jpeg", ".mp4", ".mov", ".wav", ".mp3"]
```

## Bekannte Einschränkungen (v0.2.1)

❌ **Keine Waveform-Visualisierung**  
❌ **Keine Audio-Ähnlichkeits-Erkennung**  
❌ **Kein Audio-Processing** (Normalisierung, etc.)  
❌ **Keine Playlist-Verwaltung**  

**Kommt in v0.3+**

## Breaking Changes

Keine! v0.2.1 ist voll kompatibel mit v0.2.0 und v0.1.0.

## Upgrade

```powershell
# Im Git-Repo
cd C:\_Git\Python-tools
git pull

# Neu installieren
pip install -e ".[dev]"

# Version prüfen
photo-tool version
# Photo Tool v0.2.1
```

## Dokumentation

- **AUDIO_SUPPORT.md** - Komplette Audio-Anleitung
- **VIDEO_SUPPORT.md** - Video-Datei-Verwaltung
- **LUMIX_S5_SETUP.md** - Lumix S5 + Audio
- **INSTALL_FFMPEG.md** - ffmpeg Installation

## ffmpeg Installation (optional)

Für vollständige Audio-Metadaten:

```powershell
# Windows 11 - einfachste Methode
winget install ffmpeg

# Terminal neu starten
# Testen
photo-tool audio info recording.mp3
```

Ohne ffmpeg: Basis-Infos (Größe, Datum) funktionieren trotzdem!

## Zusammenfassung v0.2.1

### Was wurde hinzugefügt?

1. ✅ Audio-Datei-Scanning (.mp3, .wav, .flac, .m4a, etc.)
2. ✅ Audio-Metadaten (Titel, Artist, Album, Dauer, Sample-Rate)
3. ✅ CLI Commands: `audio info`, `audio list`
4. ✅ Rating für Audio-Dateien
5. ✅ Komplette DaVinci Resolve Workflows
6. ✅ Musik-Bibliotheks-Verwaltung

### Was hat sich geändert?

- Scanner erkennt Audio-Typ automatisch
- Scan-Output zeigt Photos/Videos/Audio breakdown
- Alle Analyse-Commands überspringen Audio korrekt
- Default Config inkludiert Audio-Extensions

## Feedback

Audio-Support ist NEU! Bitte teste und gib Feedback:
- Funktioniert es mit deinen Audio-Dateien?
- Welche Features fehlen noch?
- Wie ist die DaVinci Resolve Integration?

## Roadmap

### v0.3 - Enhanced Audio & Video (nächste 4-8 Wochen)
- Waveform-Visualisierung
- Audio-Ähnlichkeits-Erkennung
- Video-Szenen-Erkennung
- Proxy-Generierung

### v1.0 - Web Application
- Browser-GUI
- Filmstrip + Waveform Ansicht
- Timeline-Integration
- DaVinci Resolve XML-Export

---

**Release Date:** 4. Februar 2026  
**Version:** 0.2.1  
**Status:** Stable, ready for production use  

**Changelog:**
- v0.1.0 - Foto-Management
- v0.2.0 - Video-Support
- v0.2.1 - Audio-Support ← **Du bist hier**

Viel Spaß mit Audio-Support! 🎵🎬📸
