# 📸 Photo Tool PoC - Web GUI

**Proof-of-Concept** web interface for Photo Tool

## 🚀 Quick Start

### 1. Install Flask

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

- ✅ **Photo Grid** - Browse all photos as thumbnails
- ✅ **Star Rating** - Click stars to rate 1-5
- ✅ **Statistics** - Total/Rated/Unrated counts
- ✅ **Lazy Loading** - Load more as you scroll
- ✅ **Persistent Ratings** - Uses existing JSON sidecar system
- ✅ **Modern UI** - Beautiful dark theme

---

## 🎮 Usage

1. **Browse Photos** - Scroll through thumbnail grid
2. **Rate Photos** - Click on stars (1-5)
3. **Load More** - Click "Load More" button
4. **View Stats** - Top bar shows totals

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

## 🚀 Next Steps (v0.3.0)

This is just a PoC! For production GUI:

1. **FastAPI** instead of Flask (better performance)
2. **Vue/Nuxt** proper build system
3. **Lightbox** for fullscreen view
4. **Burst Viewer** for series
5. **Filtering** by rating, date, etc.
6. **Keyboard Shortcuts** (1-5 keys)
7. **Batch Operations** (rate multiple)
8. **Export** selected photos

---

## 💡 Tips

- **Responsive** - Works on desktop, tablet, mobile
- **Dark Theme** - Easy on the eyes
- **Fast** - Lazy loading for performance
- **No Database** - Uses existing file system

---

**Enjoy! 🎉**
