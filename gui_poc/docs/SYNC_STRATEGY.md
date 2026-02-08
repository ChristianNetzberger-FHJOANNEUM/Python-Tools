# JSON ↔ SQLite Synchronization Strategy

**Version:** 1.0  
**Date:** 2026-02-08  
**Status:** Phase 3a Implemented

## Design Principle

```
JSON Sidecars = SOURCE OF TRUTH
SQLite Database = PERFORMANCE CACHE
```

**On Conflict: JSON ALWAYS WINS**

---

## Data Flow Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     USER ACTIONS                             │
│  - Edit rating/color/keywords in UI                          │
│  - Run analysis (blur, burst, faces)                         │
│  - Import new media                                          │
└───────────────────┬──────────────────────────────────────────┘
                    │
                    ↓
┌──────────────────────────────────────────────────────────────┐
│             STEP 1: WRITE TO JSON FIRST                      │
│  - .{stem}.metadata.json (user data)                         │
│  - .{filename}.phototool.json (analysis data)                │
│  - Atomic write (temp file → rename)                         │
└───────────────────┬──────────────────────────────────────────┘
                    │
                    ↓
┌──────────────────────────────────────────────────────────────┐
│             STEP 2: SYNC TO SQLITE                           │
│  - Update workspace_media.db                                 │
│  - Update project.db (if override)                           │
│  - Track sync timestamp                                      │
└──────────────────────────────────────────────────────────────┘
```

---

## Synchronization Modes

### 1. Full Migration (Initial Setup)

**When:** First time a folder is added to workspace  
**Scope:** All files in folder  
**Process:**

1. Scan folder for media files (photos, videos, audio)
2. For each file:
   - Check if `.{stem}.metadata.json` exists → load user metadata
   - Check if `.{filename}.phototool.json` exists → load analysis data
   - Extract EXIF from media file (photos only)
   - Insert into `workspace_media.db`
3. Track migration in `sync_status` table

**Performance:**
- 234 photos: **~30-45 seconds** (with EXIF extraction)
- Parallelized with `ThreadPoolExecutor` (4 workers)
- Sequential SQLite writes (thread-safe)

**Code:**
```python
manager = MigrationManager(workspace_root)
stats = manager.migrate_folders_to_sqlite(folders=['E:\\Photos\\Folder1'])
```

---

### 2. Incremental Sync (File Change Detection)

**When:** JSON file modified after initial migration  
**Scope:** Single file  
**Process:**

1. Detect JSON file change (file watcher or manual trigger)
2. Load updated JSON data
3. Find corresponding record in SQLite (by `path`)
4. Update SQLite record
5. Set `updated_at` timestamp

**Triggers:**
- User edits metadata in UI
- Analysis completes and writes `.phototool.json`
- External tool modifies JSON

**Code:**
```python
# After writing to JSON
with open('.P1012337.metadata.json', 'w') as f:
    json.dump(metadata, f)

# Sync to SQLite
workspace_db.sync_file_metadata(path, metadata)
```

---

### 3. Folder Rescan (Verify & Update)

**When:** User requests folder refresh  
**Scope:** All files in folder  
**Process:**

1. Scan folder for media files
2. For each file:
   - Check if exists in SQLite
   - If missing: Add new record (new file)
   - If exists: Compare `file_mtime` with `json_mtime`
     - If `file_mtime` > `json_mtime`: Re-sync (JSON changed)
     - If same: Skip (already synced)
3. Mark missing files as `is_available = 0`

**Use Cases:**
- New files added to folder outside of app
- Files deleted outside of app
- JSON files modified externally

---

### 4. Conflict Resolution

**Scenario:** User edits in UI while external tool also edits JSON

**Strategy:**
1. **Timestamp Comparison:**
   - Compare `json_mtime` (file modification time) with `updated_at` (SQLite)
   - If `json_mtime` > `updated_at`: JSON is newer → reload from JSON
   - If `updated_at` > `json_mtime`: SQLite is newer → write to JSON

2. **JSON Wins Policy:**
   - If timestamps are very close (< 1 second): **JSON wins**
   - Reason: JSON is portable, SQLite can be regenerated

3. **User Notification:**
   - If conflict detected: Log warning
   - Optional: Show UI notification for manual resolution

**Code:**
```python
def resolve_conflict(path: str, db_record: dict, json_data: dict):
    json_mtime = os.path.getmtime(json_path)
    db_updated = db_record['updated_at']
    
    if json_mtime > db_updated:
        # JSON is newer, reload
        workspace_db.sync_from_json(path, json_data)
        return 'json_win'
    else:
        # DB is newer, write to JSON
        write_json_metadata(path, db_record)
        return 'db_win'
```

---

## Field-Level Mapping

### User Metadata: `.{stem}.metadata.json` → `media` table

| JSON Field | SQLite Column | Type | Notes |
|------------|---------------|------|-------|
| `rating` | `media.rating` | INTEGER (0-5) | User quality rating |
| `color` | `media.color` | TEXT | Color label |
| `keywords` | `media.keywords` | TEXT (JSON array) | Tags for search |
| `comment` | `media.comment` | TEXT | Free text note |
| `gps.latitude` | *(not in media)* | - | Future: separate GPS table |
| `updated` | `media.json_mtime` | INTEGER (Unix) | Sync timestamp |

**Sync Code:**
```python
# JSON → SQLite
def sync_user_metadata(path: str, json_data: dict):
    cursor.execute("""
        UPDATE media 
        SET rating = ?, color = ?, keywords = ?, comment = ?,
            json_mtime = ?, updated_at = ?
        WHERE path = ?
    """, (
        json_data.get('rating', 0),
        json_data.get('color'),
        json.dumps(json_data.get('keywords', [])),
        json_data.get('comment'),
        int(time.time()),
        int(time.time()),
        path
    ))
```

---

### Analysis Data: `.{filename}.phototool.json` → `photo_metadata` table

| JSON Path | SQLite Column | Type | Notes |
|-----------|---------------|------|-------|
| `analyses.blur.laplacian.score` | `blur_laplacian` | REAL | Laplacian variance |
| `analyses.blur.laplacian.threshold` | `blur_laplacian_threshold` | REAL | Threshold used |
| `analyses.blur.tenengrad.score` | `blur_tenengrad` | REAL | Tenengrad variance |
| `analyses.blur.tenengrad.threshold` | `blur_tenengrad_threshold` | REAL | Threshold used |
| `analyses.blur.roi.score` | `blur_roi` | REAL | ROI blur score |
| `analyses.blur.roi.threshold` | `blur_roi_threshold` | REAL | ROI threshold |
| `analyses.blur.detection_date` | `blur_detection_date` | INTEGER (Unix) | When analyzed |
| `analyses.burst.is_burst_candidate` | `is_burst_candidate` | BOOLEAN | Part of burst? |
| `analyses.burst.burst_id` | `burst_id` | TEXT (12 chars) | Burst group ID |
| `analyses.burst.neighbors` | `burst_neighbors` | TEXT (JSON array) | Related photos |
| `analyses.burst.score` | `burst_score` | REAL (0-1) | Similarity score |
| `analyses.burst.detection_date` | `burst_detection_date` | INTEGER (Unix) | When analyzed |
| `analyses.faces.face_count` | `face_count` | INTEGER | Number of faces |
| `analyses.faces.faces` | `faces_data` | TEXT (JSON) | Face coordinates |
| `analyses.landscape.is_landscape` | `is_landscape_photo` | BOOLEAN | Is landscape? |
| `analyses.landscape.confidence` | `landscape_confidence` | REAL (0-1) | Confidence |
| `analyses.landscape.horizon_angle` | `horizon_angle` | REAL | Horizon angle |
| `analyses.night.is_night_photo` | `is_night_photo` | BOOLEAN | Night photo? |
| `analyses.night.confidence` | `night_detection_confidence` | REAL (0-1) | Confidence |

**Sync Code:**
```python
# JSON → SQLite
def sync_analysis_data(media_id: int, sidecar_data: dict):
    blur = sidecar_data.get('blur', {})
    burst = sidecar_data.get('burst', {})
    
    cursor.execute("""
        UPDATE photo_metadata 
        SET blur_laplacian = ?, blur_tenengrad = ?, blur_roi = ?,
            is_burst_candidate = ?, burst_id = ?, burst_neighbors = ?,
            sidecar_synced_at = ?
        WHERE media_id = ?
    """, (
        blur.get('laplacian', {}).get('score'),
        blur.get('tenengrad', {}).get('score'),
        blur.get('roi', {}).get('score'),
        burst.get('is_burst_candidate', 0),
        burst.get('burst_id'),
        json.dumps(burst.get('neighbors', [])),
        int(time.time()),
        media_id
    ))
```

---

## EXIF Data Extraction

**Source:** Photo file itself (JPEG EXIF tags)  
**When:** During migration or file change  
**Fields Extracted:**

```python
from PIL import Image

def extract_exif(photo_path: str) -> dict:
    img = Image.open(photo_path)
    exif = img.getexif()
    
    return {
        'capture_time': exif.get(36867),  # DateTimeOriginal
        'width': img.width,
        'height': img.height,
        'camera_make': exif.get(271),     # Make
        'camera_model': exif.get(272),    # Model
        'lens_model': exif.get(42036),    # LensModel
        'iso': exif.get(34855),           # ISOSpeedRatings
        'aperture': exif.get(33437),      # FNumber
        'shutter_speed': exif.get(33434), # ExposureTime
        'focal_length': exif.get(37386),  # FocalLength
        'orientation': exif.get(274)      # Orientation
    }
```

**Storage:** `photo_metadata` table  
**Sync Strategy:** Extract once during migration, re-extract only if file modified

---

## Burst Data Special Case

**Problem:** Burst detection creates interdependencies between photos

**Solution: Two-Phase Burst Sync**

### Phase 1: Individual Analysis (Per-Photo)
Each photo gets analyzed independently:
```json
{
  "burst_neighbors": [
    {"path": "P1012336.JPG", "similarity": 0.92},
    {"path": "P1012338.JPG", "similarity": 0.88}
  ],
  "is_burst_candidate": true
}
```

### Phase 2: Burst Grouping (Batch)
After all photos analyzed, assign `burst_id`:
```json
{
  "burst_id": "a4720613550b",
  "neighbors": ["P1012336.JPG", "P1012338.JPG"]
}
```

**Sync Strategy:**
1. Phase 1: Write individual analyses to `.phototool.json`
2. Phase 1: Sync `is_burst_candidate` to SQLite (no `burst_id` yet)
3. Phase 2: Assign `burst_id` to all photos in group
4. Phase 2: Update all `.phototool.json` files with `burst_id`
5. Phase 2: Sync `burst_id` and `burst_neighbors` to SQLite

**Important:** Photos with `is_burst_candidate = 1` but `burst_id = NULL` are **incomplete** and should NOT be shown as burst leaders in UI.

---

## Write Operations

### User Edits Metadata in UI

```python
# 1. Update JSON (atomic write)
temp_path = f".P1012337.metadata.json.tmp"
with open(temp_path, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2)
os.replace(temp_path, ".P1012337.metadata.json")

# 2. Sync to SQLite
cursor.execute("""
    UPDATE media 
    SET rating = ?, color = ?, keywords = ?, 
        json_mtime = ?, updated_at = ?
    WHERE path = ?
""", (rating, color, json.dumps(keywords), 
      int(time.time()), int(time.time()), path))
conn.commit()
```

### Analysis Tool Updates Analysis Data

```python
# 1. Compute analysis
blur_results = analyze_blur(photo_path)

# 2. Load existing .phototool.json (if exists)
phototool_data = load_phototool_json(photo_path)

# 3. Update analyses section
phototool_data['analyses']['blur'] = blur_results

# 4. Write to JSON (atomic)
temp_path = f".{filename}.phototool.json.tmp"
with open(temp_path, 'w', encoding='utf-8') as f:
    json.dump(phototool_data, f, indent=2)
os.replace(temp_path, f".{filename}.phototool.json")

# 5. Sync to SQLite
workspace_db.sync_analysis_data(media_id, phototool_data['analyses'])
```

---

## Error Handling

### JSON Read Errors
```python
def safe_load_json(json_path: Path) -> dict:
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {json_path}: {e}")
        return {}  # Return empty dict, don't crash
    except FileNotFoundError:
        return {}  # No JSON file, use defaults
```

### SQLite Write Errors
```python
def safe_db_write(conn, sql, params):
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        logger.error(f"DB integrity error: {e}")
        conn.rollback()
        return False
    except sqlite3.OperationalError as e:
        logger.error(f"DB operational error: {e}")
        conn.rollback()
        return False
```

### Sync Failure Recovery
```python
# Track failed syncs
cursor.execute("""
    UPDATE media 
    SET sync_status = 'conflict'
    WHERE path = ?
""", (path,))

# Later: retry sync
def retry_failed_syncs():
    cursor.execute("SELECT path FROM media WHERE sync_status = 'conflict'")
    for row in cursor.fetchall():
        try:
            resync_file(row['path'])
        except Exception as e:
            logger.error(f"Retry failed for {row['path']}: {e}")
```

---

## Performance Optimization

### Batch Writes
```python
# Bad: Individual commits
for photo in photos:
    cursor.execute("INSERT INTO media ...", values)
    conn.commit()  # SLOW!

# Good: Single commit
cursor.executemany("INSERT INTO media ...", values_list)
conn.commit()  # FAST!
```

### Parallel Processing
```python
# Use ThreadPoolExecutor for I/O-bound tasks
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_photo, p) for p in photos]
    for future in as_completed(futures):
        result = future.result()
```

### Incremental Updates
```python
# Only sync files that changed
for photo_path in photos:
    json_mtime = os.path.getmtime(json_path)
    db_mtime = get_db_mtime(photo_path)
    
    if json_mtime > db_mtime:
        sync_file(photo_path)  # Changed
    else:
        skip_file(photo_path)  # Already synced
```

---

## Validation & Testing

### Data Integrity Check
```python
def validate_sync(folder_path: str):
    """Verify all JSON data is correctly synced to SQLite"""
    
    # Get all media files
    media_files = list(Path(folder_path).glob("*.JPG"))
    
    for media_file in media_files:
        # Load JSON
        json_path = Path(f".{media_file.stem}.metadata.json")
        if json_path.exists():
            json_data = json.load(open(json_path))
            
            # Load from DB
            cursor.execute("SELECT * FROM media WHERE path = ?", (str(media_file),))
            db_row = cursor.fetchone()
            
            # Compare
            assert db_row['rating'] == json_data.get('rating', 0)
            assert db_row['color'] == json_data.get('color')
            # ... more assertions
```

### Sync Performance Test
```python
def benchmark_sync(folder_path: str):
    import time
    
    start = time.time()
    manager = MigrationManager(workspace_root)
    stats = manager.migrate_folders_to_sqlite([folder_path])
    duration = time.time() - start
    
    print(f"Synced {stats['items_processed']} items in {duration:.2f}s")
    print(f"Rate: {stats['items_processed'] / duration:.1f} items/sec")
```

---

## Current Status (2026-02-08)

### ✅ Implemented
- Full migration (folders → SQLite)
- User metadata sync (`.{stem}.metadata.json` → `media` table)
- Analysis data sync (`.phototool.json` → `photo_metadata` table)
- EXIF extraction and caching
- Parallel processing with ThreadPoolExecutor
- Error handling and logging

### ⏳ Pending
- Incremental sync (file watcher)
- Automatic rescan on folder change
- Conflict resolution UI
- Bidirectional sync (SQLite → JSON for edits made in DB)

### 🐛 Known Issues
- **RESOLVED:** Burst data with `is_burst_candidate=1` but no `burst_id` caused fake burst leaders
- **FIX:** Server now requires both `burst_id` AND `burst_neighbors` for `is_burst_lead=True`

---

## See Also

- `JSON_SIDECAR_FORMAT.md` - JSON file structure
- `DATABASE_ARCHITECTURE.md` - SQLite schema
- `PHASE3_SQLITE_ARCHITECTURE.md` - Overall system design
- `migration.py` - Migration implementation
- `db_manager.py` - Database operations
