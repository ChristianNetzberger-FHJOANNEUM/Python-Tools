# 📸 Photo Tool GUI - Features & Roadmap

## ✅ **Phase 1: FERTIG** (v0.3.0 PoC)

### **Core Features**
- ✅ Photo Grid View
- ✅ Burst Detection & Viewer
- ✅ Quality Indicators (Blur Score)
- ✅ **NEW: Flexible Rating Filter (0-5 Stars)**
- ✅ Star Rating System
- ✅ Caching & Progress Bar
- ✅ Sorting (Name, Rating, Date)

### **Filters**
```
✅ Rating (0★ to 5★) - Multi-select
✅ In Bursts
✅ Sort by Name/Rating/Date
✅ Clear Filters Button
```

---

## 🔄 **Phase 2: NEXT** (v0.3.1)

### **Advanced Filters** ⏱️ 2-3h
- [ ] **Color Labels** (Lightroom-Style)
  - 🔴 Red, 🟡 Yellow, 🟢 Green, 🔵 Blue, 🟣 Purple
  - Stored in JSON sidecar
- [ ] **Keywords/Tags**
  - Auto-extract from EXIF/IPTC
  - Manual tagging UI
  - Autocomplete
- [ ] **GPS Filter**
  - "Has GPS" checkbox
  - Filter by location (later)

### **Lightbox** ⏱️ 2-3h
- [ ] Fullscreen viewer
- [ ] Arrow keys navigation
- [ ] Rate with 1-5 keys
- [ ] ESC to close

### **Keyboard Shortcuts** ⏱️ 1h
- [ ] 1-5: Quick rating
- [ ] ←/→: Navigate photos
- [ ] Space: Lightbox toggle
- [ ] C: Toggle color label

---

## 🚀 **Phase 3: ADVANCED** (v0.4.0)

### **Burst Management** ⏱️ 1 day
```python
# Select photos in burst
[✓] Photo 1 (BEST) ⭐⭐⭐⭐⭐
[✓] Photo 2        ⭐⭐⭐⭐☆
[ ] Photo 3        ⭐⭐☆☆☆

Actions:
- Keep Selected (2)
- Delete Others
- Undo Burst
- Move to Archive
```

### **Map View** 🗺️ ⏱️ 1 day
```javascript
// Show photos on map (GPS from EXIF)
import Leaflet from 'leaflet';

Features:
- Pin für jedes Foto mit GPS
- Cluster bei Zoom-out
- Click → Show photo
- Filter by map bounds
```

### **Batch Operations** ⏱️ 1 day
- [ ] Select multiple photos (Checkboxes)
- [ ] "Rate All Selected"
- [ ] "Tag All Selected"
- [ ] "Color Label All"
- [ ] "Export Selected"
- [ ] "Delete Selected"

### **Statistics Dashboard** ⏱️ 1 day
- [ ] Rating distribution chart
- [ ] Quality histogram
- [ ] Photos per month/year
- [ ] Camera usage stats
- [ ] Top locations (if GPS)

---

## 🗺️ **GPS/Geo-Tagging Details**

### **Already Available in EXIF:**
```python
from photo_tool.io import get_gps_coordinates, get_keywords

# Extract GPS
coords = get_gps_coordinates(photo.path)
# → { 'latitude': 47.123, 'longitude': 15.456 }

# Extract keywords
keywords = get_keywords(photo.path)
# → ['landscape', 'sunset', 'beach']
```

### **How GPS works:**
1. ✅ **Lumix S5 embeds GPS** (wenn aktiviert)
2. ✅ **EXIF contains**: GPSLatitude, GPSLongitude
3. ✅ **Already extractable** with existing code
4. 🔄 **Need to add**: Map view UI

### **Map Implementation Plan:**
```html
<!-- Use Leaflet.js (lightweight) -->
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

<div id="map" style="height: 600px;"></div>

<script>
  const map = L.map('map').setView([47.0, 15.0], 8);
  
  // Add OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
  
  // Add photo markers
  photos.forEach(photo => {
    if (photo.gps) {
      L.marker([photo.gps.latitude, photo.gps.longitude])
        .bindPopup(`<img src="${photo.thumbnail}" width="200"><br>${photo.name}`)
        .addTo(map);
    }
  });
</script>
```

---

## 🎨 **Color Labels System**

### **Lightroom-Compatible:**
```json
// .P1022811.metadata.json
{
  "rating": 5,
  "color": "red",  // red, yellow, green, blue, purple, none
  "keywords": ["landscape", "sunset", "beach"],
  "gps": { "lat": 47.123, "lon": 15.456 },
  "comment": "Best sunset shot!",
  "updated": "2026-02-04T15:30:00"
}
```

### **Color Meanings (Your Choice):**
```
🔴 Red    = Urgent / For Client
🟡 Yellow = Review Later
🟢 Green  = Approved / Final
🔵 Blue   = Archive / Keep
🟣 Purple = Experiment / Creative
```

### **UI Implementation:**
```html
<!-- Color picker in photo card -->
<div class="color-labels">
  <span class="color-dot red" :class="{ active: photo.color === 'red' }" 
        @click="setColor(photo, 'red')">🔴</span>
  <span class="color-dot yellow" @click="setColor(photo, 'yellow')">🟡</span>
  <span class="color-dot green" @click="setColor(photo, 'green')">🟢</span>
  <span class="color-dot blue" @click="setColor(photo, 'blue')">🔵</span>
  <span class="color-dot purple" @click="setColor(photo, 'purple')">🟣</span>
</div>
```

---

## 🏷️ **Keywords/Tags System**

### **Sources:**
1. **EXIF/IPTC** (Auto-extract)
2. **Manual Input** (User adds)
3. **AI Suggestions** (Optional, Phase 4)

### **UI Mockup:**
```
┌──────────────────────────────────────┐
│ Tags: [landscape] [sunset] [austria] │
│       + Add tag...                   │
└──────────────────────────────────────┘

Filter by tags:
┌──────────────────────────────────────┐
│ Search: [____]                       │
│                                       │
│ [✓] landscape (245)                  │
│ [✓] sunset (89)                      │
│ [ ] portrait (156)                   │
│ [ ] austria (67)                     │
│ [ ] lumix-s5 (882)                   │
└──────────────────────────────────────┘
```

### **Backend:**
```python
# New file: photo_tool/actions/metadata.py

def set_metadata(photo_path: Path, data: dict):
    """Set all metadata (rating, color, keywords, etc.)"""
    meta_file = photo_path.parent / f".{photo_path.stem}.metadata.json"
    
    with open(meta_file, 'w') as f:
        json.dump(data, f, indent=2)

def get_metadata(photo_path: Path) -> dict:
    """Get all metadata"""
    meta_file = photo_path.parent / f".{photo_path.stem}.metadata.json"
    
    if meta_file.exists():
        with open(meta_file, 'r') as f:
            return json.load(f)
    
    # Auto-extract from EXIF
    return {
        'gps': get_gps_coordinates(photo_path),
        'keywords': get_keywords(photo_path)
    }
```

---

## 📊 **Current Status**

```
Phase 1 (Core)          [████████████████████] 100%
Phase 2 (Advanced)      [████░░░░░░░░░░░░░░░░]  20%
Phase 3 (Professional)  [░░░░░░░░░░░░░░░░░░░░]   0%
```

### **JETZT verfügbar:**
- ✅ Flexible Rating Filter (0-5★)
- ✅ GPS Extraction Function
- ✅ Keywords Extraction Function

### **Nächste 2-3 Stunden:**
- 🔄 Color Labels
- 🔄 Keyword/Tag UI
- 🔄 Lightbox

### **Diese Woche:**
- 🔄 Map View
- 🔄 Burst Management
- 🔄 Batch Operations

---

## 🎯 **Testing GPS Now**

```python
# Test if your Lumix S5 photos have GPS
python -m photo_tool.cli.main

from photo_tool.io import get_gps_coordinates
from pathlib import Path

photo = Path("E:/Lumix-2026-01/test/P1022811.JPG")
gps = get_gps_coordinates(photo)

if gps:
    print(f"✓ GPS found: {gps['latitude']}, {gps['longitude']}")
    print(f"  Google Maps: https://maps.google.com/?q={gps['latitude']},{gps['longitude']}")
else:
    print("✗ No GPS data (activate GPS on camera)")
```

---

**Ready for Phase 2?** 🚀

Next: Implement Color Labels (2h) or jump to Lightbox (2h)?
