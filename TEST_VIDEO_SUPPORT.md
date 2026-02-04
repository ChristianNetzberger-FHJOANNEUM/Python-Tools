# Video-Support testen

Schnelle Test-Anleitung für die neuen Video-Features.

## Voraussetzungen

```powershell
# 1. Im venv sein
cd C:\_Git\Python-tools
.\venv\Scripts\activate

# 2. Version prüfen
photo-tool version
# Photo Tool v0.2.0 ✅
```

## Test 1: Video scannen (ohne ffprobe)

```powershell
# Workspace erstellen
photo-tool workspace init D:\VideoTest --root "F:\DCIM"

# Config editieren - Videos hinzufügen
notepad D:\VideoTest\config.yaml

# Ändern:
scan:
  extensions: [".jpg", ".jpeg", ".mp4", ".mov"]

# Scannen
photo-tool scan --workspace D:\VideoTest

# Erwartete Ausgabe:
# ✓ Found XXX files:
#   Photos: XXX
#   Videos: XXX
```

## Test 2: Video-Info (Basis ohne ffprobe)

```powershell
# Einzelnes Video anschauen
photo-tool video info F:\DCIM\100_PANA\VIDEO001.mp4

# Erwartete Ausgabe (OHNE ffprobe):
# ⚠ Warning: ffprobe not found!
# 
# Video information for: VIDEO001.mp4
# Filename      VIDEO001.mp4
# Size          2.3 GB
# Captured      2024-12-25 14:30:45
```

## Test 3: ffprobe installieren (optional)

```powershell
# Windows 11
winget install ffmpeg

# Terminal NEU STARTEN
# Dann testen:
ffprobe -version

# Jetzt nochmal Video-Info:
photo-tool video info F:\DCIM\100_PANA\VIDEO001.mp4

# Erwartete Ausgabe (MIT ffprobe):
# Video information for: VIDEO001.mp4
# Filename      VIDEO001.mp4
# Size          2.3 GB
# Captured      2024-12-25 14:30:45
# Duration      00:05:23          ← NEU!
# Resolution    3840x2160          ← NEU!
# Frame Rate    29.97 fps          ← NEU!
# Codec         h264               ← NEU!
# Bit Rate      85.3 Mbps          ← NEU!
```

## Test 4: Video-Liste

```powershell
# Alle Videos auflisten
photo-tool video list --workspace D:\VideoTest

# Nach Dauer sortiert
photo-tool video list --sort duration

# Nach Größe sortiert
photo-tool video list --sort size

# Nach Datum sortiert
photo-tool video list --sort date
```

## Test 5: Rating

```powershell
# Video bewerten
photo-tool rate set F:\DCIM\100_PANA\VIDEO001.mp4 --stars 5 --comment "Bestes Video"

# Rating abrufen
photo-tool rate get F:\DCIM\100_PANA\VIDEO001.mp4

# Erwartete Ausgabe:
# VIDEO001.mp4
#   Stars: ⭐⭐⭐⭐⭐ (5/5)
#   Comment: Bestes Video
```

## Test 6: Gemischte Analyse

```powershell
# Scannen (Fotos + Videos)
photo-tool scan --workspace D:\VideoTest

# Burst-Analyse (nur Fotos)
photo-tool analyze bursts --workspace D:\VideoTest

# Erwartete Ausgabe:
# Step 1: Scanning media files...
# ✓ Found 856 files:
#   Photos: 723
#   Videos: 133
# 
# Note: Skipping 133 video files (not applicable for burst detection)
# 
# Step 2: Reading capture times...
# ...
```

## Test 7: Thumbnail

```python
# Python-Test
from pathlib import Path
from photo_tool.io import generate_thumbnail
from photo_tool.workspace import Workspace

ws = Workspace("D:/VideoTest")
video = Path("F:/DCIM/100_PANA/VIDEO001.mp4")

# Thumbnail generieren
thumb = generate_thumbnail(video, ws.thumbnails_dir)
print(f"Thumbnail: {thumb}")

# Sollte eine JPG-Datei im cache/thumbnails/ Ordner erstellen
```

## Test 8: Report mit Videos

```powershell
# HTML-Report generieren
photo-tool report generate --workspace D:\VideoTest --format html

# Report öffnen
start D:\VideoTest\reports\cluster_report.html

# Report sollte Fotos zeigen (Videos werden in Reports noch nicht angezeigt)
```

## Erwartete Ergebnisse

### ✅ Funktioniert

- [x] Videos werden gescannt
- [x] Video-Anzahl wird korrekt gezeigt
- [x] video info zeigt Basis-Info (ohne ffprobe)
- [x] video info zeigt volle Info (mit ffprobe)
- [x] video list funktioniert
- [x] Rating funktioniert für Videos
- [x] Thumbnails werden generiert
- [x] Foto-Analyse überspringt Videos korrekt

### ⚠️ Einschränkungen (wie erwartet)

- [ ] Videos in Burst-Analyse (wird übersprungen)
- [ ] Videos in Quality-Analyse (wird übersprungen)
- [ ] Video-Ähnlichkeits-Erkennung (kommt in v0.3)
- [ ] Videos in HTML-Report (kommt später)

## Bekannte Probleme

### Problem: "Could not read frame from video"

**Ursache:** Unbekannter Codec oder korrupte Datei

**Lösung:** 
- Prüfe ob Video in VLC abspielbar ist
- Versuche anderen Video-Datei

### Problem: ffprobe langsam bei vielen Videos

**Erklärung:** Normal - ffprobe muss jedes Video analysieren

**Lösung:** 
- Metadaten werden gecacht
- Zweiter Scan ist schneller

## Erfolgs-Kriterien

Test ist erfolgreich wenn:

1. ✅ `photo-tool version` zeigt `v0.2.0`
2. ✅ `photo-tool video --help` zeigt Commands
3. ✅ Scan zeigt Photo/Video Breakdown
4. ✅ Video-Info zeigt mindestens Größe und Datum
5. ✅ Rating funktioniert für Videos
6. ✅ Foto-Analyse ignoriert Videos korrekt

## Nächste Schritte nach erfolgreichem Test

1. **Git Commit:**
   ```bash
   git add .
   git commit -m "feat: add video support v0.2.0"
   git push
   ```

2. **Mit echten Daten testen:**
   - Ganzen DCIM-Ordner scannen
   - Bursts organisieren
   - Videos bewerten

3. **ffmpeg installieren** für volle Features

4. **Feedback geben:**
   - Was funktioniert gut?
   - Was fehlt?
   - Was sollte verbessert werden?

## Support

Bei Problemen:
- Logs: `D:\VideoTest\logs\`
- Debug-Modus: `photo-tool --debug video info ...`
- GitHub Issues: Bug-Reports

---

**Version:** 0.2.0  
**Test-Dauer:** 5-10 Minuten  
**Status:** Ready for testing! 🚀
