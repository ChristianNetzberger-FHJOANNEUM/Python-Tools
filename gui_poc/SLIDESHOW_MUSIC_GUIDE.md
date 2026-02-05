# 🎬🎵 Slideshow + Music Export Guide

## Overview

Export standalone photo galleries with integrated slideshow and music playback. Perfect for Smart TV viewing, presentations, and sharing!

---

## ✨ Features

### **🎬 Slideshow Mode**
- ✅ Auto-play with configurable duration (2-10 seconds per photo)
- ✅ Smooth fade transitions
- ✅ Loop playback (restarts from beginning)
- ✅ True fullscreen support (Fullscreen API)
- ✅ Keyboard controls (Space, F, Arrow keys)
- ✅ Touch-friendly controls for mobile/tablet

### **🎵 Music Integration**
- ✅ Multiple audio tracks (MP3, WAV, OGG)
- ✅ Playlist with auto-advance
- ✅ Volume control
- ✅ Play/Pause controls
- ✅ Synced with slideshow (starts/stops together)

### **📺 Smart TV Mode**
- ✅ Larger buttons optimized for TV remote
- ✅ Works on Samsung/LG/Sony Smart TV browsers
- ✅ Fullscreen optimized layout
- ✅ No mouse required (keyboard/remote only)

---

## 🚀 Quick Start

### **1. Python API Usage**

```python
from pathlib import Path
from photo_tool.actions.export import export_gallery

# Basic export with slideshow (no music)
photos = [
    Path("C:/Photos/IMG_001.JPG"),
    Path("C:/Photos/IMG_002.JPG"),
    Path("C:/Photos/IMG_003.JPG"),
]

gallery_dir = export_gallery(
    photo_paths=photos,
    output_dir=Path("C:/Exports/vacation-2026"),
    title="Vacation 2026",
    slideshow_enabled=True,
    slideshow_duration=5  # 5 seconds per photo
)

print(f"Gallery created: {gallery_dir}")
# Open: C:/Exports/vacation-2026/gallery/index.html
```

### **2. Export with Music**

```python
from pathlib import Path
from photo_tool.actions.export import export_gallery

photos = [...]  # Your photo list

music_files = [
    Path("C:/Music/summer-vibes.mp3"),
    Path("C:/Music/chill-beats.mp3"),
]

gallery_dir = export_gallery(
    photo_paths=photos,
    output_dir=Path("C:/Exports/beach-party"),
    title="Beach Party 2026",
    music_files=music_files,
    slideshow_enabled=True,
    slideshow_duration=7,  # 7 seconds per photo
)
```

### **3. Smart TV Optimized Export**

```python
gallery_dir = export_gallery(
    photo_paths=photos,
    output_dir=Path("C:/Exports/family-gathering"),
    title="Family Gathering 2026",
    music_files=[Path("C:/Music/family-theme.mp3")],
    slideshow_enabled=True,
    slideshow_duration=8,  # Longer duration for TV
    smart_tv_mode=True  # 🆕 Larger buttons for TV remote
)
```

---

## 🌐 Web API Usage (Flask Server)

### **Export via HTTP POST**

```javascript
// JavaScript example
const response = await fetch('http://localhost:8000/api/export/gallery', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        photo_ids: [
            'C:/Photos/IMG_001.JPG',
            'C:/Photos/IMG_002.JPG'
        ],
        title: 'Vacation 2026',
        output_name: 'vacation-2026',
        template: 'photoswipe',
        
        // 🆕 Slideshow + Music options
        music_files: [
            'C:/Music/track1.mp3',
            'C:/Music/track2.mp3'
        ],
        slideshow_enabled: true,
        slideshow_duration: 6,  // seconds
        smart_tv_mode: false
    })
});

const data = await response.json();
console.log('Gallery created:', data.gallery_path);
console.log('Music tracks:', data.music_count);
```

---

## 🎮 User Controls

### **In Browser (Desktop/Mobile)**

#### **Before Slideshow:**
- Click **"🎬 Start Slideshow"** button
- Gallery opens in fullscreen
- Music starts automatically (if available)

#### **During Slideshow:**

| Key | Action |
|-----|--------|
| `Space` | Pause/Resume slideshow & music |
| `F` | Toggle fullscreen |
| `←` / `→` | Previous/Next photo |
| `Escape` | Exit slideshow |

#### **Music Controls:**
- **▶️ / ⏸️** - Play/Pause music
- **Volume slider** - Adjust volume (0-100%)
- **Now Playing** - Current track name

---

### **On Smart TV**

#### **Samsung/LG/Sony TV:**

1. Open TV Browser (Samsung Internet, WebOS Browser, etc.)
2. Navigate to: `http://YOUR-PC-IP:8000/vacation-2026/gallery/`
3. Use TV Remote:
   - **Select/OK** - Click "Start Slideshow"
   - **Back/Return** - Exit slideshow
   - **Left/Right** - Navigate photos
   - **Play/Pause** - Toggle slideshow (if supported)

---

## 📁 Gallery File Structure

```
vacation-2026/
└── gallery/
    ├── index.html          # Main gallery page
    ├── images/             # Optimized photos (2000px max)
    │   ├── 0001.jpg
    │   ├── 0002.jpg
    │   └── ...
    ├── thumbnails/         # Grid thumbnails (400px)
    │   ├── 0001.jpg
    │   ├── 0002.jpg
    │   └── ...
    └── music/              # 🆕 Audio files
        ├── track1.mp3
        ├── track2.mp3
        └── ...
```

---

## 🎨 Customization Options

### **Slideshow Duration**

```python
# Fast (2s per photo)
slideshow_duration=2

# Normal (5s per photo)
slideshow_duration=5

# Slow (10s per photo) - best for TV
slideshow_duration=10
```

### **Smart TV Mode**

```python
smart_tv_mode=True  # Larger buttons, bigger fonts
```

**TV Mode Changes:**
- Buttons: 220px wide, 80px tall
- Font size: 1.5rem (50% larger)
- Touch targets optimized for remote navigation

---

## 📺 Smart TV Deployment

### **Method 1: USB Drive**

```powershell
# Export gallery
python export_example.py

# Copy to USB
xcopy /E /I C:\Exports\vacation-2026\gallery\ E:\vacation-gallery\

# On TV:
# 1. Insert USB
# 2. Open TV File Browser
# 3. Navigate to: vacation-gallery/index.html
# 4. Open with browser
```

### **Method 2: Network Server**

```powershell
# Install simple HTTP server
pip install http-server

# Serve galleries
cd C:\Exports
python -m http.server 8080

# On TV Browser:
# Navigate to: http://YOUR-PC-IP:8080/vacation-2026/gallery/
```

### **Method 3: Media Server (Recommended)**

See `ARCHITECTURE.md` for Caddy/nginx setup.

---

## 🎵 Music Recommendations

### **File Formats**
- ✅ **MP3** - Best compatibility (recommended)
- ✅ **OGG** - Good quality, smaller files
- ✅ **WAV** - Lossless, large files
- ⚠️ **AAC** - Limited browser support

### **Track Length**
- Short gallery (<50 photos): 1-2 tracks, 3-5 min each
- Medium gallery (50-200 photos): 3-5 tracks, 3-4 min each
- Long gallery (>200 photos): 5+ tracks or 30+ min loop

### **Volume Levels**
- Mix tracks to consistent volume (normalize)
- Default volume: 70% (adjustable by user)

---

## 🐛 Troubleshooting

### **Music doesn't play**

**Cause:** Browser autoplay policy

**Solution:**
- Some browsers block autoplay
- User must click "Start Slideshow" button (user gesture required)
- Alternative: Click music play button manually

### **Fullscreen not working**

**Cause:** Browser security policy

**Solution:**
- Press `F` key after slideshow starts
- Or manually click fullscreen button in PhotoSwipe

### **Smart TV: Can't click buttons**

**Solution:**
- Use TV remote D-pad (↑↓←→) to navigate
- Press OK/Select to click
- Enable `smart_tv_mode=True` for larger buttons

### **Photos not advancing**

**Check:**
- Is slideshow paused? (Press Space to resume)
- Check browser console for errors (F12)
- Verify `slideshow_duration` is set

---

## 📊 Performance

### **Photo Count Recommendations**

| Device | Max Photos | Slideshow Duration |
|--------|-----------|-------------------|
| Desktop | 500+ | 3-5s |
| Mobile | 200 | 4-6s |
| Smart TV | 300 | 6-10s |

### **File Size Optimization**

**Default Settings (balanced):**
- Main images: 2000px max, 90% quality
- Thumbnails: 400px, 85% quality
- Total size: ~50-100KB per photo

**For Smart TV (optimize):**
```python
export_gallery(
    ...,
    max_image_size=1920,  # HD resolution
    thumbnail_size=300,   # Smaller thumbnails
)
```

---

## 💡 Use Cases

### **1. Party/Event Background Display**
```python
export_gallery(
    photos=party_photos,
    title="Birthday Party 2026",
    music_files=[Path("party-mix.mp3")],
    slideshow_duration=8,
    smart_tv_mode=True
)
# → Copy to USB → Play on TV all night
```

### **2. Client Presentation**
```python
export_gallery(
    photos=best_shots,
    title="Client Project",
    slideshow_duration=6,
    slideshow_enabled=True
    # No music for professional setting
)
# → Email gallery folder or host on web
```

### **3. Family Photo Frame (Digital)**
```python
export_gallery(
    photos=family_memories,
    title="Family Memories",
    music_files=[Path("nostalgia.mp3")],
    slideshow_duration=10,
    smart_tv_mode=True
)
# → Deploy to always-on tablet or TV
```

---

## 🔗 Related Guides

- `SMART_TV_GUIDE.md` - Full Smart TV setup
- `WEB_GALLERY_EXPORT.md` - Gallery export basics
- `KEYBOARD_SHORTCUTS.md` - All keyboard controls

---

## 🎯 Next Steps

1. ✅ **Try basic export** - Export a small gallery with slideshow
2. ✅ **Add music** - Export with 1-2 music tracks
3. ✅ **Test on TV** - Try on Smart TV browser
4. ✅ **Deploy to server** - Set up permanent media server

**Ready to create stunning galleries!** 🎬🎵✨
