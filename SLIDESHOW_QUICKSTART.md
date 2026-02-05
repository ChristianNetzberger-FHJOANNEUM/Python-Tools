# 🎬🎵 Slideshow + Music Quick Start

Get up and running in 5 minutes!

---

## 🚀 Quick Test (No Music)

```powershell
# 1. Activate environment
cd C:\_Git\Python-tools
.\venv\Scripts\Activate.ps1

# 2. Run example
python examples\export_slideshow_example.py

# 3. Open the generated gallery
# Location: C:\PhotoTool_Test\exports\slideshow-basic\gallery\index.html
```

**In Browser:**
- Click **"🎬 Start Slideshow"** button
- Photos auto-advance every 5 seconds
- Press `Space` to pause/resume
- Press `F` for fullscreen
- Press `Escape` to exit

---

## 🎵 With Music (5 Minutes)

### **1. Prepare Music Files**

```powershell
# Create music folder
mkdir C:\Music

# Copy your MP3 files there
# Example:
# C:\Music\track1.mp3
# C:\Music\track2.mp3
```

### **2. Edit Example Script**

Open `examples\export_slideshow_example.py` and update line ~61:

```python
# Change this:
music_files = [
    Path("C:/Music/track1.mp3"),
    Path("C:/Music/track2.mp3"),
]

# To your actual music files:
music_files = [
    Path("C:/Music/your-song.mp3"),
]
```

### **3. Run Export**

```powershell
python examples\export_slideshow_example.py
```

### **4. Test Gallery**

Open: `C:\PhotoTool_Test\exports\slideshow-music\gallery\index.html`

- Click **"🎬 Start Slideshow"**
- Music plays automatically!
- Controls appear for volume/play/pause

---

## 📺 Smart TV Test (10 Minutes)

### **1. Export TV-Optimized Gallery**

```python
# Quick script: export_tv_test.py
from pathlib import Path
from photo_tool.actions.export import export_gallery
from photo_tool.workspace import Workspace
from photo_tool.config import load_config
from photo_tool.io import scan_multiple_directories, filter_by_type

workspace_path = Path("C:/PhotoTool_Test")
ws = Workspace(workspace_path)
config = load_config(ws.config_file)

all_media = scan_multiple_directories(
    config.scan.roots,
    config.scan.extensions,
    config.scan.recurse,
    show_progress=False
)

photos = filter_by_type(all_media, "photo")
photo_paths = [p.path for p in photos[:20]]

export_gallery(
    photo_paths=photo_paths,
    output_dir=workspace_path / "exports" / "tv-test",
    title="TV Test Gallery",
    slideshow_enabled=True,
    slideshow_duration=8,  # Longer for TV viewing
    smart_tv_mode=True,    # Larger buttons!
    max_image_size=1920    # HD resolution
)

print("✅ Gallery ready: C:/PhotoTool_Test/exports/tv-test/gallery/")
```

### **2. Copy to USB**

```powershell
# Copy gallery to USB drive (assume E: is USB)
xcopy /E /I "C:\PhotoTool_Test\exports\tv-test\gallery" "E:\tv-gallery\"
```

### **3. On Smart TV**

1. Insert USB drive
2. Open TV Browser (Samsung Internet, WebOS, etc.)
3. Navigate to USB drive
4. Open `tv-gallery/index.html`
5. Click **"🎬 Start Slideshow"** with remote
6. Enjoy!

---

## 🌐 Network Server (For TV Without USB)

### **Option A: Python HTTP Server**

```powershell
# Serve galleries over network
cd C:\PhotoTool_Test\exports
python -m http.server 8080

# Find your PC IP
ipconfig
# Look for IPv4 Address: 192.168.x.x
```

### **Option B: Flask Server (Already Running)**

```powershell
# Your GUI server already serves exports!
cd gui_poc
python server.py

# Access from TV:
# http://YOUR-PC-IP:8000/exports/tv-test/gallery/
```

### **On TV:**
1. Open TV Browser
2. Navigate to: `http://192.168.1.XXX:8080/tv-test/gallery/`
3. Start slideshow!

---

## 💡 One-Liner Exports

### **Basic Slideshow:**
```python
from pathlib import Path
from photo_tool.actions.export import export_gallery

export_gallery([Path("photo.jpg")], Path("C:/Export"), "My Gallery", slideshow_enabled=True)
```

### **With Music:**
```python
export_gallery(
    [Path("photo.jpg")], 
    Path("C:/Export"), 
    "My Gallery", 
    music_files=[Path("C:/Music/song.mp3")],
    slideshow_enabled=True
)
```

### **TV Mode:**
```python
export_gallery(
    [Path("photo.jpg")], 
    Path("C:/Export"), 
    "TV Gallery", 
    smart_tv_mode=True,
    slideshow_duration=8
)
```

---

## 🎯 Common Workflows

### **Workflow 1: Party Tonight**
```powershell
# 1. Export best photos
python -c "
from pathlib import Path
from photo_tool.actions.export import export_gallery
from photo_tool.workspace import Workspace
from photo_tool.config import load_config
from photo_tool.io import scan_multiple_directories, filter_by_type
from photo_tool.actions.metadata import get_metadata

ws = Workspace(Path('C:/PhotoTool_Test'))
config = load_config(ws.config_file)
all_media = scan_multiple_directories(config.scan.roots, config.scan.extensions, False, False)
photos = filter_by_type(all_media, 'photo')

# Get 5-star photos
best = [p.path for p in photos if get_metadata(p.path).get('rating', 0) == 5][:50]

export_gallery(best, Path('C:/Exports/party'), 'Party Tonight', 
               music_files=[Path('C:/Music/party-mix.mp3')],
               slideshow_enabled=True, slideshow_duration=7, smart_tv_mode=True)
print('✅ Ready for party!')
"

# 2. Copy to USB
xcopy /E /I C:\Exports\party\gallery E:\party

# 3. Plug into TV and enjoy!
```

### **Workflow 2: Client Presentation**
```python
# No music for professional setting
export_gallery(
    client_photos,
    Path("C:/Client/gallery"),
    "Project Showcase",
    slideshow_enabled=True,
    slideshow_duration=6,
    max_image_size=2000  # High quality
)
```

---

## 🐛 Quick Troubleshooting

### **No music playing?**
- ✅ Check file paths are correct
- ✅ Use MP3 format (best compatibility)
- ✅ Click "Start Slideshow" (autoplay needs user gesture)

### **Slideshow not advancing?**
- ✅ Check browser console (F12) for errors
- ✅ Press Space to ensure not paused
- ✅ Verify `slideshow_enabled=True`

### **TV buttons too small?**
- ✅ Set `smart_tv_mode=True`
- ✅ Reload page after re-export

### **Files not found?**
- ✅ Check workspace exists: `C:/PhotoTool_Test`
- ✅ Run scan first: `photo-tool scan`
- ✅ Verify photo paths are absolute

---

## 📚 Full Documentation

- **Complete Guide:** `gui_poc/SLIDESHOW_MUSIC_GUIDE.md`
- **Implementation Details:** `SLIDESHOW_MUSIC_IMPLEMENTATION.md`
- **Smart TV Setup:** `gui_poc/SMART_TV_GUIDE.md`
- **Examples:** `examples/README.md`

---

## ✅ Success Checklist

- [ ] Exported basic slideshow
- [ ] Tested in browser (Chrome/Firefox/Safari)
- [ ] Added music file
- [ ] Tested music playback
- [ ] Tried keyboard controls (Space, F, arrows)
- [ ] Tested fullscreen mode
- [ ] Exported TV-optimized version
- [ ] Tested on actual Smart TV

---

**That's it! You're ready to create amazing photo galleries with slideshow and music! 🎉**

Questions? Check the full guides in `gui_poc/` folder or ask!
