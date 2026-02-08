# 🚀 Performance Analyse: Media Tab Loading

## Executive Summary

Das Laden von Photos im Media Tab ist **extrem langsam** aufgrund mehrerer sequentieller Operationen ohne Caching oder Parallelisierung. Bei 234 Photos werden **mindestens 702 I/O-Operationen** durchgeführt.

**Geschätzte Ladezeit:** 5-15 Sekunden (abhängig von Festplatte)
**Nach Optimierung:** <1 Sekunde möglich

---

## 🔍 Detaillierte Analyse

### 1. **Directory Scanning** (Zeilen 149-154 in server.py)

```python
all_media = scan_multiple_directories(
    enabled_folders,
    config.scan.extensions,
    recursive=config.scan.recurse,
    show_progress=False
)
```

**Was passiert:**
- `find_files()` durchläuft **rekursiv** alle Ordner
- Liest `stat()` für jede Datei → **234 stat() calls**
- Erstellt `MediaFile` Objekte mit Zeitstempel
- Keine Caching-Mechanismus

**Problem:**
- ✖️ Jedes Mal beim Laden: kompletter Verzeichnis-Scan
- ✖️ Sequentiell, nicht parallelisiert
- ✖️ Auch wenn sich nichts geändert hat

**Impact:** ~1-3 Sekunden bei 234 Photos

---

### 2. **Sorting by Capture Time** (Zeilen 162-180 in server.py)

```python
for photo in photos:
    capture_time = get_capture_time(photo.path, fallback_to_mtime=True)
    # EXIF lesen für JEDES Photo!
    photos_with_times.append((photo, capture_time))
```

**Was passiert:**
- `get_capture_time()` öffnet **jede Bilddatei**
- Liest EXIF-Daten mit PIL/Pillow
- **234 Dateien öffnen** nur um zu sortieren!

**Problem:**
- ✖️ EXIF wird bei jedem Request neu gelesen
- ✖️ Keine Caching von capture_time
- ✖️ Sequentiell, nicht parallelisiert

**Impact:** ~3-5 Sekunden bei 234 Photos

---

### 3. **Metadata Loading** (Zeilen 188-232 in server.py)

```python
for photo in photos_page:
    metadata = get_metadata(photo.path)  # ❌ Sidecar JSON lesen
    
    # Burst info aus Sidecar laden
    sidecar = SidecarManager(photo.path)  # ❌ Nochmal Sidecar
    if sidecar.exists:
        sidecar.load()  # ❌ JSON parsen
```

**Was passiert:**
- `get_metadata()` liest `.{filename}.metadata.json` → **234 JSON file reads**
- `SidecarManager` liest `.{filename}.sidecar.json` → **234 weitere JSON reads**
- Insgesamt: **468 JSON-Datei-Operationen**

**Problem:**
- ✖️ Keine Bulk-Loading
- ✖️ Sequentiell (eine nach der anderen)
- ✖️ Jedes Mal neu gelesen, kein Cache

**Impact:** ~2-4 Sekunden bei 234 Photos

---

### 4. **Thumbnail Paths** (Zeilen 247-248)

```python
'thumbnail': f"/thumbnails/{photo.path.stem}.jpg",
'full_image': f"/images/{photo.path.stem}{photo.path.suffix}"
```

**Was passiert:**
- Nur URLs generiert, keine echte Operation
- Thumbnails werden später on-demand generiert

**Problem:**
- ✔️ Gut: Lazy loading von Thumbnails
- ⚠️ Aber: Kein Preloading-Mechanismus

**Impact:** Minimal (~0.1 Sekunden)

---

## 📊 Performance-Engpässe Zusammenfassung

| Operation | Anzahl | Typ | Dauer (geschätzt) | Parallelisierbar? |
|-----------|--------|-----|-------------------|-------------------|
| **Directory Scan** | 1x | File I/O | 1-3s | ✅ Ja (multithreaded) |
| **EXIF Read (Sorting)** | 234x | Image I/O | 3-5s | ✅ Ja (multiprocessing) |
| **Metadata JSON Read** | 234x | File I/O | 1-2s | ✅ Ja (multithreaded) |
| **Sidecar JSON Read** | 234x | File I/O | 1-2s | ✅ Ja (multithreaded) |
| **Response Building** | 234x | CPU | 0.1-0.2s | ❌ Nein (zu klein) |
| **TOTAL** | **703 I/O** | - | **6-12s** | - |

---

## 🎯 Optimierungs-Möglichkeiten

### **Priority 1: Caching (Quick Wins)**

#### 1.1 **In-Memory Cache für Scan-Ergebnisse**
```python
# Cache directory scan für X Minuten
_scan_cache = {
    'data': None,
    'timestamp': None,
    'folders': None
}

def get_cached_scan(folders, max_age_seconds=60):
    if (_scan_cache['data'] and 
        _scan_cache['folders'] == folders and
        time.time() - _scan_cache['timestamp'] < max_age_seconds):
        return _scan_cache['data']
    
    # Scan und cache
    data = scan_multiple_directories(folders, ...)
    _scan_cache['data'] = data
    _scan_cache['timestamp'] = time.time()
    _scan_cache['folders'] = folders
    return data
```

**Gewinn:** ~1-3 Sekunden bei wiederholten Requests
**Risiko:** Niedrig (optional: file watchers für Invalidierung)

---

#### 1.2 **Metadata Batch Loading**
```python
# Statt 234x einzeln:
for photo in photos:
    metadata = get_metadata(photo.path)  # ❌

# Besser: Batch load
def get_metadata_batch(photo_paths: List[Path]) -> Dict[Path, dict]:
    results = {}
    for path in photo_paths:
        meta_file = path.parent / f".{path.stem}.metadata.json"
        if meta_file.exists():
            with open(meta_file, 'r') as f:
                results[path] = json.load(f)
        else:
            results[path] = DEFAULT_METADATA
    return results

metadata_map = get_metadata_batch(photos_page)
```

**Gewinn:** ~1-2 Sekunden (bessere Dateisystem-Locality)
**Risiko:** Sehr niedrig

---

### **Priority 2: Parallelisierung**

#### 2.1 **Multithreading für I/O-Operationen**

```python
from concurrent.futures import ThreadPoolExecutor
import threading

def load_photo_metadata(photo):
    """Lädt alle Metadaten für ein Photo"""
    metadata = get_metadata(photo.path)
    sidecar = SidecarManager(photo.path)
    burst_info = None
    if sidecar.exists:
        sidecar.load()
        # ... burst info extrahieren
    return {
        'photo': photo,
        'metadata': metadata,
        'burst_info': burst_info
    }

# Parallel processing
with ThreadPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(load_photo_metadata, photos_page))
```

**Gewinn:** ~60-80% schneller (2-4s → 0.5-1s)
**Risiko:** Niedrig (JSON reads sind I/O-bound, ideal für Threading)

---

#### 2.2 **Multiprocessing für EXIF-Reads**

```python
from concurrent.futures import ProcessPoolExecutor

def get_capture_time_worker(photo_path):
    """Worker für EXIF-Read in separatem Prozess"""
    from photo_tool.io import get_capture_time
    return get_capture_time(photo_path, fallback_to_mtime=True)

# Parallel EXIF reading
with ProcessPoolExecutor(max_workers=4) as executor:
    capture_times = list(executor.map(
        get_capture_time_worker, 
        [p.path for p in photos]
    ))
```

**Gewinn:** ~70-85% schneller (3-5s → 0.5-1s)
**Risiko:** Mittel (Prozess-Overhead, Pickling)

---

### **Priority 3: Pre-Scanning & Database**

#### 3.1 **Media Manager Pre-Scan mit SQLite**

**Idee:** Media Manager hat bereits Scan-Funktionalität!
```python
# Nutze existierende Prescan-Daten
from photo_tool.media import MediaManager
mm = MediaManager()

# Folder wurde bereits gescannt → Daten in SQLite
folder_data = mm.get_folder_by_path(folder_path)
if folder_data and folder_data.is_scanned:
    # Nutze gecachte Daten (photos_count, scan_date)
    # → Keine Directory-Scans mehr nötig!
```

**Gewinn:** ~90% schneller (6-12s → <1s)
**Risiko:** Mittel (Integration mit existierendem System)

---

#### 3.2 **SQLite-Index für Metadaten**

```sql
CREATE TABLE photo_metadata (
    path TEXT PRIMARY KEY,
    rating INTEGER,
    color TEXT,
    keywords TEXT, -- JSON array
    capture_time TEXT,
    blur_laplacian REAL,
    blur_tenengrad REAL,
    blur_roi REAL,
    updated_at INTEGER
);

CREATE INDEX idx_capture_time ON photo_metadata(capture_time);
CREATE INDEX idx_rating ON photo_metadata(rating);
```

**Gewinn:** ~95% schneller (Single query statt 468 file reads)
**Risiko:** Hoch (Architektur-Änderung, Synchronisation)

---

## 💡 Empfohlene Implementierungs-Reihenfolge

### **Phase 1: Quick Wins (1-2 Stunden)**
1. ✅ In-Memory Cache für Directory Scans
2. ✅ Batch-Loading für Metadaten
3. ✅ Response-Pagination verbessern (kleinere Chunks)

**Erwarteter Gewinn:** ~40-50% schneller (6-12s → 3-6s)

---

### **Phase 2: Parallelisierung (2-4 Stunden)**
1. ✅ ThreadPoolExecutor für Metadata-Reads
2. ✅ ProcessPoolExecutor für EXIF-Reads (optional)
3. ✅ Async I/O für JSON-Dateien (optional)

**Erwarteter Gewinn:** ~70-80% schneller (6-12s → 1-3s)

---

### **Phase 3: Media Manager Integration (4-8 Stunden)**
1. ⚠️ Nutze existierende Prescan-Daten
2. ⚠️ SQLite-Index für schnelle Queries
3. ⚠️ File watcher für Auto-Invalidierung

**Erwarteter Gewinn:** ~90-95% schneller (6-12s → <1s)

---

## 🔧 Technische Details: Threading vs Multiprocessing

### **Threading (empfohlen für I/O)**
```python
# Gut für:
- JSON file reads (metadata, sidecars)
- Network requests
- Kleine File I/O Operations

# Python GIL ist KEIN Problem bei I/O!
# Während ein Thread auf Disk wartet, arbeiten andere
```

### **Multiprocessing (für CPU-intensive Ops)**
```python
# Gut für:
- EXIF parsing (PIL/Pillow)
- Image processing
- Blur detection

# Overhead: ~100ms pro Prozess-Start
# → Nur sinnvoll bei >50 Photos
```

---

## ⚠️ Potentielle Fallstricke

### 1. **Race Conditions bei Caching**
```python
# Problem: Mehrere Requests gleichzeitig
request1: cache = None → scan → cache = result1
request2: cache = None → scan → cache = result2  # Doppelte Arbeit!

# Lösung: Lock verwenden
_cache_lock = threading.Lock()
with _cache_lock:
    if cache is None:
        cache = scan()
```

### 2. **Memory Overhead bei Parallelisierung**
```python
# Problem: 234 Photos × 8 Threads = 1872 Photo-Objekte im Memory
# Lösung: Chunking + Generator-Pattern

def process_in_chunks(items, chunk_size=50):
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i+chunk_size]
        yield from process_chunk_parallel(chunk)
```

### 3. **File Handle Limits**
```python
# Windows: ~512 open file handles default
# → Bei vielen Threads: "Too many open files"
# Lösung: max_workers <= 8
```

---

## 📈 Performance-Metriken zum Tracking

```python
import time

class PerformanceMonitor:
    def __init__(self):
        self.timings = {}
    
    def measure(self, name):
        """Context manager für timing"""
        class Timer:
            def __enter__(self):
                self.start = time.time()
                return self
            
            def __exit__(self, *args):
                duration = time.time() - self.start
                timings[name] = duration
                logger.info(f"{name}: {duration:.2f}s")
        
        return Timer()

# Usage:
perf = PerformanceMonitor()

with perf.measure("directory_scan"):
    all_media = scan_multiple_directories(...)

with perf.measure("metadata_loading"):
    for photo in photos:
        metadata = get_metadata(photo.path)

with perf.measure("total_request"):
    # ... entire request ...
```

---

## 🎯 Zusammenfassung

| Optimierung | Aufwand | Gewinn | Risiko | Priorität |
|-------------|---------|--------|--------|-----------|
| In-Memory Cache | 1h | 40% | Niedrig | 🔥 Hoch |
| Batch Metadata Loading | 1h | 20% | Sehr niedrig | 🔥 Hoch |
| Threading (I/O) | 2h | 60% | Niedrig | 🔥 Hoch |
| Multiprocessing (EXIF) | 2h | 50% | Mittel | ⚠️ Mittel |
| SQLite Index | 8h | 90% | Hoch | ⏰ Später |

**Empfehlung:** Start mit Phase 1 + 2 (Quick Wins + Threading)
**Ergebnis:** 6-12s → 1-3s (75-85% schneller)

---

## 🚀 Nächste Schritte

1. **Performance Baseline erstellen**
   - Timer einbauen
   - Aktuelle Zeiten messen
   - Logs analysieren

2. **Quick Wins implementieren**
   - In-Memory Cache
   - Batch Loading
   - Testing

3. **Threading einbauen**
   - ThreadPoolExecutor für Metadaten
   - Testing mit verschiedenen photo counts
   - Error handling

4. **Monitoring einbauen**
   - Response-Times tracken
   - Cache hit/miss rates
   - Bottleneck-Analyse

Bereit zur Implementierung? 🎉
