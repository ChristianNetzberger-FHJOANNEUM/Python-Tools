# 📸 Photo Tool Examples

This folder contains practical examples demonstrating Photo Tool features.

## 🎬 Slideshow + Music Export

### **export_slideshow_example.py**

Demonstrates the new slideshow and music features for gallery export.

**Run:**
```powershell
cd C:\_Git\Python-tools
python examples\export_slideshow_example.py
```

**Examples included:**
1. **Basic slideshow** - Simple auto-play slideshow
2. **With music** - Slideshow with background music playlist
3. **Smart TV optimized** - Large buttons for TV remote
4. **Filtered export** - Export only 5-star or tagged photos

**Requirements:**
- Workspace initialized at `C:/PhotoTool_Test`
- Photos scanned (`photo-tool scan`)
- Optional: Music files (MP3) for music example

---

## 🚀 Quick Start

```python
from pathlib import Path
from photo_tool.actions.export import export_gallery

# Export with slideshow + music
gallery = export_gallery(
    photo_paths=[Path("photo1.jpg"), Path("photo2.jpg")],
    output_dir=Path("C:/Exports/my-gallery"),
    title="My Gallery",
    music_files=[Path("C:/Music/track.mp3")],
    slideshow_enabled=True,
    slideshow_duration=5
)

# Open in browser: {gallery}/index.html
```

---

## 📺 Deployment to Smart TV

### Method 1: USB Drive
```powershell
# Export gallery
python examples\export_slideshow_example.py

# Copy to USB
xcopy /E /I C:\PhotoTool_Test\exports\smart-tv-demo\gallery\ E:\tv-gallery\

# On TV: Open browser → USB → tv-gallery/index.html
```

### Method 2: Network Server
```powershell
# Serve galleries over network
cd C:\PhotoTool_Test\exports
python -m http.server 8080

# On TV: Open browser → http://YOUR-PC-IP:8080/smart-tv-demo/gallery/
```

---

## 🎵 Music File Setup

Place music files anywhere accessible:

```
C:\Music\
├── vacation-soundtrack.mp3
├── chill-vibes.mp3
└── family-theme.mp3
```

Then reference in export:
```python
music_files=[
    Path("C:/Music/vacation-soundtrack.mp3"),
    Path("C:/Music/chill-vibes.mp3"),
]
```

---

## 📖 More Information

- **Slideshow Guide:** `gui_poc/SLIDESHOW_MUSIC_GUIDE.md`
- **Smart TV Setup:** `gui_poc/SMART_TV_GUIDE.md`
- **Gallery Export:** `gui_poc/WEB_GALLERY_EXPORT.md`

---

**Happy exporting! 🎬🎵**
