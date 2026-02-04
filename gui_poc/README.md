# 📸 Photo Tool PoC - Web GUI

**Full-featured** web interface for Photo Tool with burst detection, filtering, and gallery export.

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
# Activate your venv first
cd C:\_Git\Python-tools
.\venv\Scripts\Activate.ps1

# Install Flask
pip install flask flask-cors
```

### 2. Start Server

```powershell
cd gui_poc
python server.py
```

### 3. Open Browser

Open: **http://localhost:8000**

---

## ✨ Features

### **Core Features:**
- ✅ **Photo Grid** - Browse all photos as thumbnails
- ✅ **Lightbox Viewer** - Fullscreen photo viewing
- ✅ **Star Rating** - Click stars to rate 1-5
- ✅ **Color Labels** - Lightroom-style 🔴🟡🟢🔵🟣
- ✅ **Keywords/Tags** - Tag & filter photos
- ✅ **Statistics** - Total/Rated/Unrated counts

### **Advanced Features:**
- ✅ **Burst Detection** - Find & view photo series
- ✅ **Quality Indicators** - Blur/sharpness scores
- ✅ **Smart Filtering** - By rating, color, keywords, bursts
- ✅ **Sorting** - By name, rating, date
- ✅ **Web Gallery Export** - PhotoSwipe standalone galleries
- ✅ **Keyboard Shortcuts** - Lightning-fast workflow
- 🎬 **NEW: Slideshow Mode** - Auto-play with fade transitions, controls & loop
- ⛶ **NEW: True Fullscreen** - Browser Fullscreen API (like YouTube, no UI!)
- 👻 **NEW: Auto-Hide Controls** - YouTube-style UX, controls vanish after 3s!

### **Performance:**
- ✅ **Caching** - Instant burst reload
- ✅ **Progress Bars** - Real-time analysis updates
- ✅ **Lazy Loading** - Smooth scrolling
- ✅ **On-the-fly Thumbnails** - Auto-generate if missing

---

## 🎮 Usage

### **Photo Management:**
1. **Browse Photos** - Scroll through thumbnail grid
2. **Rate Photos** - Click stars (1-5) or use keyboard (1-5 in lightbox)
3. **Color Label** - Click color dots or press C in lightbox
4. **Add Keywords** - Click "+ tag", type, press Enter
5. **Lightbox** - Click photo for fullscreen view

### **Burst Detection:**
1. **Switch to Bursts Tab** - Analyzes photo series
2. **Click Burst Group** - Opens detail viewer
3. **Navigate** - Use ◄ ► buttons or arrow keys
4. **Rate** - Rate individual photos in burst
5. **View Quality** - See blur scores & BEST badge

### **Filtering:**
1. **Rating Filter** - Select 0-5 stars (multi-select)
2. **Color Filter** - Filter by color labels
3. **Keyword Filter** - Click tags to filter
4. **In Bursts** - Show only photos in burst groups
5. **Clear Filters** - Reset all filters

### **Slideshow:** 🎬 **NEW!**
1. **Filter Photos** (optional) - Select photos for slideshow
2. **Click Slideshow** - 🎬 button next to Export
3. **Auto-Play** - Starts automatically with smooth fade transitions
4. **Fullscreen** - ⛶ button or press `F` for true fullscreen (no browser UI!)
5. **Keyboard Controls:**
   - `F` - Toggle fullscreen 🆕
   - `Space` - Play/Pause
   - `←` `→` - Navigate photos
   - `↑` `↓` - Adjust speed
   - `L` - Toggle loop
   - `ESC` - Exit fullscreen / Exit slideshow
6. **Settings** - Speed (2-10s), Loop on/off
7. **Smart TV Ready** - Works on Samsung/LG browsers with fullscreen support!

See: `SLIDESHOW_QUICKSTART.md` and `FULLSCREEN_GUIDE.md` for detailed guides!

### **Export:**
1. **Filter Photos** - Apply desired filters
2. **Click Export** - Top-right button
3. **Enter Title** - Gallery name
4. **Choose Template** - PhotoSwipe or Simple
5. **Export** - Creates standalone HTML gallery
6. **Share** - Upload to Netlify/Vercel/GitHub Pages

---

## 🔧 Configuration

Edit workspace path in `server.py`:

```python
workspace_path = Path("C:/PhotoTool_Test")  # Change this
```

Or make it configurable:

```python
import os
workspace_path = Path(os.getenv("PHOTO_TOOL_WORKSPACE", "C:/PhotoTool_Test"))
```

---

## 📝 API Endpoints

```
GET  /                              # Main HTML page
GET  /api/photos                    # List photos (paginated)
POST /api/photos/{id}/rate          # Rate a photo
GET  /api/stats                     # Get statistics
GET  /thumbnails/{filename}         # Serve thumbnail
```

---

## 🐛 Troubleshooting

### Thumbnails not loading?

Make sure you've run scan to generate thumbnails:

```powershell
python -m photo_tool.cli.main scan scan -w "C:\PhotoTool_Test"
```

### CORS errors?

Already handled with `flask-cors`

### Port 8000 already in use?

Change port in `server.py`:

```python
app.run(debug=True, port=8080)  # Use 8080 instead
```

---

## ⌨️ Keyboard Shortcuts

### **In Lightbox:**
```
←/→     Navigate photos
1-5     Quick rating
C       Cycle color labels
0       Clear rating
ESC     Close lightbox
```

See `KEYBOARD_SHORTCUTS.md` for full list.

---

## 📦 Export Galleries

### **Export Process:**
1. Filter photos (e.g., 5★ + Green + "landscape")
2. Click "📦 Export Gallery"
3. Enter title and choose template
4. Gallery created in `C:\PhotoTool_Test\exports\`

### **Templates:**
- **PhotoSwipe** - Modern, fullscreen, touch-enabled
- **Simple** - Lightweight grid, no dependencies

### **Deployment:**
```powershell
# Upload to Netlify (free, 1 minute)
# 1. Go to: https://app.netlify.com/drop
# 2. Drag & drop the "gallery" folder
# 3. Get shareable link!
```

---

## 🚀 Production Roadmap (v0.3.0+)

Future enhancements:

1. **FastAPI** instead of Flask (async, better performance)
2. **Vue/Nuxt** proper build system (SPA/SSR)
3. **Map View** - GPS coordinates on interactive map
4. **Burst Management** - Select & delete from bursts
5. **Batch Operations** - Rate/tag/color multiple photos
6. **Video Player** - Play videos in lightbox
7. **Audio Player** - Play audio files
8. **Basic Editing** - Crop, rotate, adjust

---

## 💡 Tips

- **Responsive** - Works on desktop, tablet, mobile
- **Dark Theme** - Easy on the eyes
- **Fast** - Lazy loading for performance
- **No Database** - Uses existing file system

---

**Enjoy! 🎉**
