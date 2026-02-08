# GUI PoC - Photo Tool

A modern, performance-optimized web interface for managing and rating photos.

## Quick Start

```bash
# Install dependencies
pip install flask flask-cors

# Start the server
python server.py

# Open browser
http://localhost:5000
```

## Project Structure

```
gui_poc/
├── server.py                    # Flask backend server
├── static/
│   ├── index.html              # Main HTML (optimized, 148 KB)
│   ├── styles.css              # CSS styles (34 KB, cacheable)
│   ├── app.js                  # Vue 3 application (127 KB, cacheable)
│   └── index_original.html     # Backup of original file
├── PERFORMANCE_OPTIMIZATION.md  # Detailed optimization report
└── README.md                    # This file
```

## Recent Performance Optimizations ⚡

The web interface has been optimized for better performance:

- **53% reduction** in main HTML file size (314 KB → 148 KB)
- **Cacheable assets**: CSS and JS now load separately and cache efficiently
- **Production Vue build**: Faster runtime, smaller size
- **Resource hints**: Preconnect, DNS prefetch, and preload for faster loading

See [PERFORMANCE_OPTIMIZATION.md](./PERFORMANCE_OPTIMIZATION.md) for details.

## Features

### Core Functionality
- 📸 **Media Manager**: Register and scan photo folders
- 🗂️ **Workspaces**: Organize photo collections
- 📁 **Projects**: Filter-based or folder-based projects
- 🎬 **Media View**: Browse, rate, and manage photos
- 📦 **Bursts**: Automatic burst detection and management
- 🎬 **Slideshow**: Full-screen photo slideshow with controls

### Photo Management
- ⭐ **Rating System**: 5-star rating with keyboard shortcuts
- 🎨 **Color Labels**: Red, Yellow, Green, Blue, Purple
- 🏷️ **Keywords**: Tag photos with searchable keywords
- 🔍 **Blur Detection**: Automatic detection of blurry photos
- 🔎 **Advanced Filtering**: Filter by rating, color, keywords, blur

### Export & Sharing
- 📤 **Gallery Export**: Create standalone HTML photo galleries
- 🖼️ **Multiple Templates**: PhotoSwipe, grid layouts
- 📱 **Responsive**: Works on desktop, tablet, and mobile
- 🎵 **Music Support**: Add background music to slideshows

## Browser Compatibility

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers

## Development

### File Modifications
- **index.html**: Structure and Vue templates only
- **styles.css**: All CSS styles, animations, and media queries
- **app.js**: Vue 3 application logic, data, and methods

### Future Optimizations
See the "Further Optimization Opportunities" section in [PERFORMANCE_OPTIMIZATION.md](./PERFORMANCE_OPTIMIZATION.md).

## Rollback

If you need to restore the original version:

```bash
cd static
mv index.html index_optimized.html
mv index_original.html index.html
```

## Requirements

- Python 3.8+
- Flask
- Flask-CORS
- photo_tool module (parent directory)

## License

Part of the Python-tools repository.
