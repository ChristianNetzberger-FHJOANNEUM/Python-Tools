# 🏷️ Keywords/Tags System Guide

## ✅ **Was ist FERTIG:**

### **1. Keywords auf Fotos** ✅
```
Jedes Foto zeigt:
[landscape] [sunset] [austria] + tag

- Click "×" → Entfernt Tag
- Click "+ tag" → Öffnet Input
- Type & Enter → Fügt Tag hinzu
- Autocomplete mit Suggestions!
```

### **2. Filter by Keywords** ✅
```
🏷️ Keywords (12)
[landscape (45)] [sunset (23)] [portrait (67)]

- Click Tag → Filter by Tag
- Multi-Select möglich
- Active filters angezeigt
```

### **3. Autocomplete** ✅
```
Type "land..."
┌─────────────────┐
│ landscape  (45) │  ← Click to use
│ landmark   (12) │
└─────────────────┘
```

### **4. Backend Storage** ✅
```json
// .P1022811.metadata.json
{
  "rating": 5,
  "color": "green",
  "keywords": ["landscape", "sunset", "austria"],
  "updated": "2026-02-04T..."
}
```

---

## 🎯 **Wie man Keywords verwendet:**

### **1. Keywords hinzufügen:**
```
1. Hover über Foto
2. Click "+ tag"
3. Type keyword (z.B. "landscape")
4. Press Enter oder wähle aus Suggestions
5. ✓ Tag wird hinzugefügt
```

### **2. Keywords entfernen:**
```
1. Hover über Keyword-Tag
2. Click "×"
3. ✓ Tag wird entfernt
```

### **3. Nach Keywords filtern:**
```
1. Scroll zu "🏷️ Keywords" Filter
2. Click auf einen Keyword-Chip
3. ✓ Zeigt nur Fotos mit diesem Tag
4. Click mehrere für OR-Filter
```

### **4. Keyword Vorschläge:**
```
Beim Tippen erscheinen Suggestions:
- Bereits verwendete Keywords
- Sortiert nach Häufigkeit
- Zeigt Anzahl (count)
```

---

## 💡 **Best Practices:**

### **Kategorien-System:**
```
Location:
- austria, vienna, salzburg
- alps, danube, lake

Subject:
- landscape, portrait, macro
- architecture, nature, urban

Event:
- wedding, concert, exhibition
- vacation, work, personal

Camera:
- lumix-s5, dji-osmo360
- 24mm, 50mm, 85mm

Quality:
- best, keeper, edit
- reject, review, maybe
```

### **Naming Conventions:**
```
✓ Lowercase:     "landscape" nicht "Landscape"
✓ Singular:      "photo" nicht "photos"
✓ Hyphens:       "lumix-s5" nicht "lumix s5"
✓ Short:         "austria" nicht "taken in austria"
✓ Specific:      "vienna" besser als "city"
```

---

## 🔄 **Keywords aus EXIF (Auto-Import)**

### **EXIF/IPTC Keywords lesen:**
```python
from photo_tool.io import get_keywords

# Liest Keywords aus EXIF
keywords = get_keywords(photo_path)
# → ['landscape', 'sunset']
```

### **Automatisch importieren:**
```python
# Für alle Fotos EXIF Keywords in Metadata übernehmen
from photo_tool.io import scan_multiple_directories, get_keywords
from photo_tool.actions.metadata import set_keywords

for photo in photos:
    exif_keywords = get_keywords(photo.path)
    if exif_keywords:
        set_keywords(photo.path, exif_keywords)
```

---

## 🎨 **Keyword-Workflows:**

### **Workflow 1: Neue Fotos taggen**
```
1. Filter: "☆☆☆☆☆ Unrated"
2. Browse durch Fotos
3. Rate & Tag gleichzeitig
4. Schnell durchklicken
```

### **Workflow 2: Collection für Client**
```
1. Filter: "client-name" + "5★"
2. Export als Gallery
3. Send link
```

### **Workflow 3: Print Selection**
```
1. Filter: "print" + "landscape" + "5★"
2. Batch export
3. Send to print shop
```

### **Workflow 4: Social Media**
```
1. Tag: "instagram", "facebook"
2. Filter by tag
3. Batch resize & export
4. Upload
```

---

## 📊 **Keyword Statistics:**

### **Top 10 Keywords:**
```
GET /api/keywords

Response:
{
  "keywords": [
    { "name": "landscape", "count": 245 },
    { "name": "sunset", "count": 89 },
    { "name": "portrait", "count": 156 },
    ...
  ],
  "total": 78
}
```

### **Filter by Count:**
```
GET /api/keywords?min_count=10

Nur Keywords mit mind. 10 Fotos
```

---

## 🔍 **Advanced Filtering:**

### **OR Filter (Any):**
```
Click: [landscape] [portrait]
→ Zeigt Fotos mit "landscape" ODER "portrait"
```

### **Combined Filters:**
```
Rating:  [5★]
Color:   [🟢 Green]
Keyword: [landscape]
→ Zeigt: 5★ Green Landscape Fotos
```

### **Exclude (Later):**
```
Future feature:
[landscape] [NOT: people]
→ Landschaft ohne Menschen
```

---

## 🚀 **API Endpoints:**

### **Add Keyword:**
```javascript
POST /api/photos/{id}/keywords
Body: { "add": "landscape" }

Response: { "keywords": ["landscape", "sunset"] }
```

### **Remove Keyword:**
```javascript
POST /api/photos/{id}/keywords
Body: { "remove": "landscape" }

Response: { "keywords": ["sunset"] }
```

### **Set All Keywords:**
```javascript
POST /api/photos/{id}/keywords
Body: { "keywords": ["new", "list", "here"] }

Response: { "keywords": ["new", "list", "here"] }
```

### **Get All Keywords:**
```javascript
GET /api/keywords?min_count=5

Response: {
  "keywords": [
    { "name": "landscape", "count": 245 },
    { "name": "sunset", "count": 89 }
  ],
  "total": 78
}
```

---

## 💾 **Migration von EXIF:**

### **Bulk Import Script:**
```python
# scripts/import_exif_keywords.py

from pathlib import Path
from photo_tool.io import scan_multiple_directories, get_keywords
from photo_tool.actions.metadata import set_keywords, get_metadata

def import_exif_keywords(photo_dir):
    """Import keywords from EXIF to metadata"""
    
    photos = scan_multiple_directories([photo_dir], ['.jpg', '.jpeg'])
    
    imported = 0
    for photo in photos:
        # Get existing metadata
        metadata = get_metadata(photo.path)
        existing_keywords = metadata.get('keywords', [])
        
        # Get EXIF keywords
        exif_keywords = get_keywords(photo.path)
        
        if exif_keywords:
            # Merge with existing
            all_keywords = list(set(existing_keywords + exif_keywords))
            set_keywords(photo.path, all_keywords)
            imported += 1
            print(f"✓ {photo.path.name}: {exif_keywords}")
    
    print(f"\n✓ Imported keywords for {imported} photos")

if __name__ == '__main__':
    import_exif_keywords(Path("E:/Lumix-2026-01/test"))
```

---

## 🎯 **Nächste Features (Later):**

### **Hierarchische Tags:**
```
location/
  ├─ austria/
  │  ├─ vienna
  │  └─ salzburg
  └─ germany/
     └─ munich
```

### **Smart Suggestions (AI):**
```
- Auto-suggest based on image content
- Learn from your tagging patterns
- Location from GPS
```

### **Batch Tagging:**
```
Select 50 photos
→ "Add tag to all: landscape"
→ ✓ All tagged
```

### **Export Keywords to EXIF:**
```
Write metadata keywords back to EXIF
→ Lightroom/Bridge compatible
```

---

**Ready to tag! 🏷️✨**
