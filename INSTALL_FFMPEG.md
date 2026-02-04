# ffmpeg Installation für Video-Support

Photo Tool kann Videos auch ohne ffmpeg verwalten, aber für vollständige Metadaten (Dauer, Auflösung, Codec) wird **ffprobe** benötigt (Teil von ffmpeg).

## Windows - Schnelle Installation

### Option 1: Winget (Windows 11, empfohlen)

```powershell
# Einfachste Methode
winget install ffmpeg

# Verifizieren
ffprobe -version
```

### Option 2: Chocolatey

```powershell
# Falls Chocolatey installiert ist
choco install ffmpeg

# Verifizieren
ffprobe -version
```

### Option 3: Manuell (immer funktioniert)

**Schritt-für-Schritt:**

1. **Download ffmpeg:**
   - Gehe zu: https://www.gyan.dev/ffmpeg/builds/
   - Download: `ffmpeg-release-essentials.zip` (ca. 80 MB)
   - Oder direkt: https://github.com/BtbN/FFmpeg-Builds/releases

2. **Entpacken:**
   ```powershell
   # Erstelle Ordner
   New-Item -Path "C:\ffmpeg" -ItemType Directory
   
   # Entpacke ffmpeg-release-essentials.zip nach C:\ffmpeg\
   # Sodass: C:\ffmpeg\bin\ffprobe.exe existiert
   ```

3. **Zu PATH hinzufügen:**
   - Windows-Taste drücken
   - "Umgebungsvariablen" tippen
   - "Umgebungsvariablen für dieses Konto bearbeiten" klicken
   - Bei "Path" auf **Bearbeiten** klicken
   - **Neu** klicken
   - Hinzufügen: `C:\ffmpeg\bin`
   - **OK** → **OK** → **OK**

4. **PowerShell NEU STARTEN**

5. **Verifizieren:**
   ```powershell
   ffprobe -version
   
   # Sollte zeigen:
   # ffprobe version 6.x.x ...
   ```

### Option 4: Portable (ohne PATH)

```powershell
# ffmpeg in Photo Tool Verzeichnis kopieren
Copy-Item C:\Downloads\ffmpeg\bin\ffprobe.exe C:\_Git\Python-tools\

# Photo Tool findet es dann automatisch im aktuellen Verzeichnis
```

## Testen ob ffmpeg funktioniert

### In PowerShell:

```powershell
# Version anzeigen
ffprobe -version

# Sollte ausgeben:
# ffprobe version 6.1.1 Copyright (c) 2007-2024 the FFmpeg developers
# built with gcc ...
```

### In Photo Tool:

```powershell
# Video-Info abrufen (zeigt ob ffprobe funktioniert)
photo-tool video info F:\DCIM\100_PANA\VIDEO001.mp4

# MIT ffprobe:
# ✓ Duration: 00:05:23
# ✓ Resolution: 3840x2160
# ✓ Frame Rate: 29.97 fps
# ✓ Codec: h264

# OHNE ffprobe:
# ⚠ Warning: ffprobe not found!
# ⚠ Install ffmpeg to get detailed video information
# Size: 2.3 GB (nur Basis-Infos)
```

## macOS

```bash
# Mit Homebrew
brew install ffmpeg

# Verifizieren
ffprobe -version
```

## Linux

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg

# Verifizieren
ffprobe -version
```

### Fedora/RHEL:
```bash
sudo dnf install ffmpeg

# Verifizieren
ffprobe -version
```

## Was wenn ffprobe nicht installiert werden kann?

Photo Tool funktioniert auch ohne ffprobe:

### ✅ Funktioniert OHNE ffprobe:
- Video-Dateien scannen
- Thumbnails generieren (OpenCV)
- Videos nach Größe/Datum sortieren
- Rating/Tagging
- Organisation nach Dateiname

### ❌ Funktioniert NICHT ohne ffprobe:
- Genaue Video-Dauer
- Auflösung (width x height)
- Frame-Rate
- Codec-Information
- Bit-Rate
- Präzise Metadaten

### Warnung die du siehst:

```
Warning: ffprobe not found!
Install ffmpeg to get detailed video information
Download from: https://ffmpeg.org/download.html

Filename      VIDEO001.mp4
Path          F:\DCIM\100_PANA
Size          2.3 GB
Captured      2024-12-25 14:30:45
```

Ohne weitere Details.

## Troubleshooting

### "ffprobe not recognized"

**Problem:** ffprobe nicht im PATH

**Lösung:**
```powershell
# Prüfe wo ffprobe ist
where.exe ffprobe

# Wenn nichts gefunden:
# 1. PATH prüfen
$env:PATH -split ';'

# 2. ffprobe manuell suchen
Get-ChildItem C:\ -Recurse -Filter ffprobe.exe -ErrorAction SilentlyContinue

# 3. Zu PATH hinzufügen (siehe oben)
```

### "ffprobe funktioniert im Terminal, aber nicht in Photo Tool"

**Problem:** Terminal wurde vor PATH-Update geöffnet

**Lösung:**
```powershell
# Terminal NEU STARTEN
# Oder venv neu aktivieren
deactivate
.\venv\Scripts\activate
```

### Temporärer PATH (nur für diese Session)

```powershell
# Falls ffprobe in C:\ffmpeg\bin ist
$env:PATH += ";C:\ffmpeg\bin"

# Jetzt testen
photo-tool video info VIDEO001.mp4
```

## Verifizierung

### Kompletter Test:

```powershell
# 1. ffprobe verfügbar?
ffprobe -version

# 2. Photo Tool erkennt es?
python -c "from photo_tool.io.video_metadata import is_ffprobe_available; print('ffprobe:', 'OK' if is_ffprobe_available() else 'NOT FOUND')"

# 3. Video-Info funktioniert?
photo-tool video info <dein-video.mp4>
```

## Alternative: ffmpeg-python Library

Falls du ffprobe-Binaries nicht installieren willst/kannst:

```powershell
# Alternative: Python-Wrapper (langsamer)
pip install ffmpeg-python

# Photo Tool könnte später auch das unterstützen
```

## Zusammenfassung

| Methode | Aufwand | Empfehlung |
|---------|---------|------------|
| **Winget** | ⭐ Niedrig | ✅ Beste Option (Windows 11) |
| **Chocolatey** | ⭐⭐ Mittel | ✅ Gut (wenn choco installiert) |
| **Manuell** | ⭐⭐⭐ Hoch | ✅ Funktioniert immer |
| **Portable** | ⭐⭐ Mittel | ⚠️ OK für Tests |
| **Ohne ffmpeg** | - | ⚠️ Basis-Features nur |

**Empfehlung:** 
```powershell
winget install ffmpeg
```

Dann neu starten und testen:
```powershell
photo-tool video info <dein-video.mp4>
```

---

**Download:** https://ffmpeg.org/download.html  
**Windows Builds:** https://www.gyan.dev/ffmpeg/builds/
