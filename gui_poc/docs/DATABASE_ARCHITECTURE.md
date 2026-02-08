# Database Architecture Documentation

**Version:** 1.0  
**Date:** 2026-02-08  
**Status:** Phase 3a Implemented

## Overview

The photo tool uses **SQLite databases** as a **performance cache** for fast queries, with **JSON sidecars as the source of truth** for portability and data integrity.

## Architecture Principle

```
┌─────────────────────────────────────────────────────────────┐
│                    JSON SIDECARS                            │
│              (Source of Truth)                              │
│  - .{stem}.metadata.json (user data)                        │
│  - .{filename}.phototool.json (analysis data)               │
│  - Portable, version-control friendly                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Bidirectional Sync
                   ↓
┌─────────────────────────────────────────────────────────────┐
│                    SQLite DATABASES                         │
│              (Performance Cache)                            │
│  - workspace_media.db (global media pool)                   │
│  - {project}.db (project-specific data)                     │
│  - Fast queries, aggregations, indexes                      │
└─────────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**
- **JSON = Source of Truth:** All changes written to JSON first
- **SQLite = Cache:** Optimized for read performance (queries, filters, sorts)
- **Bidirectional Sync:** Changes in JSON auto-sync to SQLite, and vice versa
- **Conflict Resolution:** JSON always wins in conflicts

---

## Database Files

### 1. Workspace Database: `workspace_media.db`

**Location:** `{workspace_root}/db/workspace_media.db`  
**Purpose:** Global media pool for ALL photos/videos/audio in the workspace  
**Scope:** Cross-project, shared media library

**Use Cases:**
- Fast media queries across all projects
- Filtering by folder, date, camera, rating, color
- Burst grouping and analysis queries
- Media pool for audio/video selection

**Tables:**
- `media` - Universal media table (all types)
- `photo_metadata` - Photo-specific EXIF and analysis data
- `video_metadata` - Video-specific metadata
- `audio_metadata` - Audio-specific metadata
- `sync_status` - Sync operation tracking
- `db_metadata` - Database version and info

### 2. Project Database: `{project_name}.db`

**Location:** `{workspace_root}/db/{project_name}.db`  
**Purpose:** Project-specific overrides and timeline data  
**Scope:** Single project

**Use Cases:**
- Project-specific rating/color overrides
- Timeline and sequence management
- Media selection (which photos/videos in this project)
- Export configurations

**Tables:**
- `project_info` - Project metadata
- `media_overrides` - Project-specific rating/color overrides
- `timeline` - Media sequencing and timing
- `export_configs` - Export presets

---

## Schema: Workspace Database

### Table: `media`

**Purpose:** Universal table for all media types (photos, videos, audio)

```sql
CREATE TABLE media (
    -- Identity
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,           -- Full absolute path
    filename TEXT NOT NULL,              -- Filename only
    folder TEXT NOT NULL,                -- Parent folder path
    
    -- Workspace Association
    workspace_path TEXT,                 -- NULL = available to all workspaces
    
    -- Classification
    media_type TEXT NOT NULL,            -- 'photo', 'video', 'audio'
    
    -- File Info
    file_size INTEGER,                   -- Bytes
    file_mtime INTEGER,                  -- File modification time (Unix)
    
    -- Availability
    is_available BOOLEAN DEFAULT 1,      -- 0 = file/folder missing
    last_verified INTEGER,               -- Last existence check (Unix)
    
    -- User Metadata (synced from .{stem}.metadata.json)
    rating INTEGER DEFAULT 0,            -- 0-5
    color TEXT,                          -- 'red', 'yellow', 'green', 'blue', 'purple', NULL
    keywords TEXT,                       -- JSON array: ["tag1", "tag2"]
    comment TEXT,                        -- Free text
    
    -- Sync Tracking
    json_mtime INTEGER,                  -- When JSON was last synced
    sync_status TEXT DEFAULT 'synced',   -- 'synced', 'pending', 'conflict'
    
    -- Timestamps
    created_at INTEGER,                  -- When record created (Unix)
    updated_at INTEGER                   -- When record last updated (Unix)
);
```

**Indexes:**
```sql
CREATE INDEX idx_media_type ON media(media_type);
CREATE INDEX idx_folder ON media(folder);
CREATE INDEX idx_workspace ON media(workspace_path);
CREATE INDEX idx_available ON media(is_available);
CREATE INDEX idx_rating ON media(rating DESC);
CREATE INDEX idx_color ON media(color);
CREATE INDEX idx_updated ON media(updated_at DESC);
CREATE INDEX idx_path_lookup ON media(path);
CREATE INDEX idx_filename ON media(filename);
```

**Key Fields:**
- `path`: Absolute path, **unique** identifier
- `rating`: User's quality rating (0=unrated, 1-5=quality)
- `color`: Color label for visual organization
- `keywords`: JSON array of tags (stored as TEXT)
- `sync_status`: Track if DB is in sync with JSON

---

### Table: `photo_metadata`

**Purpose:** Photo-specific EXIF data and analysis results

```sql
CREATE TABLE photo_metadata (
    media_id INTEGER PRIMARY KEY,        -- FK to media.id
    
    -- EXIF Data
    capture_time TEXT,                   -- ISO 8601 datetime
    width INTEGER,                       -- Pixels
    height INTEGER,                      -- Pixels
    camera_make TEXT,                    -- "Panasonic"
    camera_model TEXT,                   -- "DMC-GH4"
    lens_model TEXT,                     -- "LUMIX G 12-35mm"
    iso INTEGER,                         -- ISO speed
    aperture REAL,                       -- f-stop (e.g., 2.8)
    shutter_speed TEXT,                  -- "1/125"
    focal_length REAL,                   -- mm
    orientation INTEGER,                 -- EXIF orientation (1-8)
    
    -- Blur Analysis (from .phototool.json → analyses.blur)
    blur_laplacian REAL,                 -- Laplacian variance
    blur_laplacian_threshold REAL,       -- Threshold used
    blur_tenengrad REAL,                 -- Tenengrad variance
    blur_tenengrad_threshold REAL,       -- Threshold used
    blur_roi REAL,                       -- ROI blur score
    blur_roi_threshold REAL,             -- ROI threshold
    blur_detection_date INTEGER,         -- Unix timestamp
    
    -- Burst Analysis (from .phototool.json → analyses.burst)
    is_burst_candidate BOOLEAN,          -- Part of a burst?
    burst_id TEXT,                       -- Burst group ID (12 chars hex)
    burst_neighbors TEXT,                -- JSON array of paths
    burst_score REAL,                    -- Similarity score (0-1)
    burst_detection_date INTEGER,        -- Unix timestamp
    
    -- Face Detection (from .phototool.json → analyses.faces)
    face_count INTEGER DEFAULT 0,        -- Number of faces
    faces_data TEXT,                     -- JSON: [{"x": 0.3, "y": 0.4, "confidence": 0.98}]
    
    -- Landscape Detection (from .phototool.json → analyses.landscape)
    is_landscape_photo BOOLEAN,          -- Is a landscape?
    landscape_confidence REAL,           -- Confidence (0-1)
    horizon_angle REAL,                  -- Degrees (-90 to +90)
    
    -- Night Detection (from .phototool.json → analyses.night)
    is_night_photo BOOLEAN,              -- Night/low-light?
    night_detection_confidence REAL,     -- Confidence (0-1)
    
    -- Quality Metrics
    sharpness_score REAL,                -- Overall sharpness
    exposure_score REAL,                 -- Exposure quality
    
    -- RAW + JPEG Tandem (Phase 4a - FUTURE)
    has_raw_tandem BOOLEAN DEFAULT 0,
    raw_file_path TEXT,
    jpeg_file_path TEXT,
    tandem_primary TEXT,                 -- 'raw', 'jpeg', NULL
    tandem_export_from TEXT,             -- 'raw', 'jpeg', 'auto'
    
    -- Non-Destructive Edits (Phase 4b - FUTURE)
    has_edits BOOLEAN DEFAULT 0,
    edit_stack TEXT,                     -- JSON: [{"op": "exposure", "params": {...}}]
    edit_version TEXT,                   -- Schema version
    edits_updated_at INTEGER,
    edits_applied_by TEXT,               -- User or "auto"
    
    -- Render Cache (Phase 4c - FUTURE)
    cached_thumbnail_path TEXT,
    cached_preview_path TEXT,
    cached_fullres_path TEXT,
    cache_invalidated BOOLEAN,
    cache_date INTEGER,
    cache_size_bytes INTEGER,
    
    -- Advanced Analyses (Phase 4d - FUTURE)
    analyses_extended TEXT,              -- JSON: {"custom_analyses": {...}}
    
    -- Sync Tracking
    exif_synced_at INTEGER,              -- When EXIF last synced
    sidecar_synced_at INTEGER,           -- When sidecar last synced
    
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);
```

**Indexes:**
```sql
CREATE INDEX idx_photo_capture_time ON photo_metadata(capture_time DESC);
CREATE INDEX idx_photo_burst_id ON photo_metadata(burst_id);
CREATE INDEX idx_photo_camera ON photo_metadata(camera_model);
CREATE INDEX idx_photo_burst_candidate ON photo_metadata(is_burst_candidate);
CREATE INDEX idx_photo_has_raw ON photo_metadata(has_raw_tandem);
CREATE INDEX idx_photo_has_edits ON photo_metadata(has_edits);
CREATE INDEX idx_photo_landscape ON photo_metadata(is_landscape_photo);
CREATE INDEX idx_photo_night ON photo_metadata(is_night_photo);
```

**Key Fields:**
- `media_id`: Links to `media.id` (1:1 relationship)
- `capture_time`: Primary sort field for photo timeline
- `burst_id`: Groups burst photos together (same ID = same burst)
- `burst_neighbors`: JSON array of full paths to related photos
- All analysis fields are **nullable** (NULL = not analyzed yet)

---

### Table: `video_metadata`

**Purpose:** Video-specific metadata and YouTube integration

```sql
CREATE TABLE video_metadata (
    media_id INTEGER PRIMARY KEY,
    
    -- Video Properties
    duration_seconds REAL,
    width INTEGER,
    height INTEGER,
    fps REAL,
    codec TEXT,
    bitrate INTEGER,
    
    -- Recording Info
    capture_time TEXT,
    camera_make TEXT,
    camera_model TEXT,
    
    -- YouTube Integration
    youtube_url TEXT,
    youtube_video_id TEXT,
    youtube_upload_date INTEGER,
    youtube_status TEXT,                 -- 'draft', 'uploaded', 'public', etc.
    
    -- Usage Intent
    embed_type TEXT,                     -- 'inline', 'youtube_ref', 'both'
    
    -- Thumbnail
    custom_thumbnail_path TEXT,
    thumbnail_time REAL,                 -- Seconds into video
    
    -- Sync
    video_info_synced_at INTEGER,
    
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);
```

**Use Cases:**
- Short videos: `embed_type='inline'` → embed directly in slideshow
- Long videos: `embed_type='youtube_ref'` → link to YouTube
- Mixed: `embed_type='both'` → both options available

---

### Table: `audio_metadata`

**Purpose:** Audio file metadata for media pool

```sql
CREATE TABLE audio_metadata (
    media_id INTEGER PRIMARY KEY,
    
    -- Audio Properties
    duration_seconds REAL,
    sample_rate INTEGER,
    channels INTEGER,                    -- 1=mono, 2=stereo, 6=5.1, 8=7.1
    bitrate INTEGER,
    codec TEXT,
    
    -- ID3 Tags
    title TEXT,
    artist TEXT,
    album TEXT,
    genre TEXT,
    year INTEGER,
    track_number INTEGER,
    
    -- Usage Category
    category TEXT,                       -- 'music', 'voiceover', 'sfx', 'ambient', etc.
    
    -- Analysis
    bpm REAL,                            -- Beats per minute
    key_signature TEXT,                  -- Musical key
    energy_level REAL,                   -- 0.0-1.0
    
    -- Sync
    audio_info_synced_at INTEGER,
    
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);
```

**Use Cases:**
- Audio pool for slideshow background music
- Category filtering (music vs. voiceover vs. SFX)
- BPM-based selection for pacing

---

### Table: `sync_status`

**Purpose:** Track synchronization operations

```sql
CREATE TABLE sync_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    sync_type TEXT NOT NULL,             -- 'full_rebuild', 'incremental', 'folder_scan', 'migration'
    
    -- Statistics
    items_processed INTEGER,
    items_added INTEGER,
    items_updated INTEGER,
    items_deleted INTEGER,
    items_errors INTEGER,
    
    -- Performance
    duration_seconds REAL,
    
    -- Status
    status TEXT,                         -- 'running', 'completed', 'failed', 'partial'
    error_message TEXT,
    
    -- Timestamps
    started_at INTEGER,
    completed_at INTEGER
);
```

---

### Table: `db_metadata`

**Purpose:** Database version and configuration

```sql
CREATE TABLE db_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at INTEGER
);

-- Initial values
INSERT INTO db_metadata VALUES
    ('schema_version', '1.0', strftime('%s', 'now')),
    ('created_at', strftime('%s', 'now'), strftime('%s', 'now')),
    ('db_type', 'workspace', strftime('%s', 'now'));
```

---

## Query Patterns

### Get All Photos for a Project

```sql
SELECT 
    m.id, m.path, m.filename, m.folder,
    m.rating, m.color, m.keywords, m.comment,
    pm.capture_time, pm.width, pm.height,
    pm.camera_model, pm.blur_laplacian,
    pm.burst_id, pm.is_burst_candidate, pm.burst_neighbors
FROM media m
LEFT JOIN photo_metadata pm ON m.id = pm.media_id
WHERE m.folder IN ('E:\Photos\Folder1', 'E:\Photos\Folder2')
  AND m.media_type = 'photo'
  AND m.is_available = 1
ORDER BY pm.capture_time DESC;
```

### Get Photos with Rating ≥ 3

```sql
SELECT m.path, m.rating, pm.capture_time
FROM media m
LEFT JOIN photo_metadata pm ON m.id = pm.media_id
WHERE m.media_type = 'photo'
  AND m.rating >= 3
ORDER BY m.rating DESC, pm.capture_time DESC;
```

### Get Burst Groups

```sql
SELECT pm.burst_id, COUNT(*) as photo_count, 
       MIN(pm.capture_time) as first_photo,
       MAX(pm.capture_time) as last_photo
FROM photo_metadata pm
WHERE pm.burst_id IS NOT NULL
GROUP BY pm.burst_id
HAVING photo_count > 1
ORDER BY first_photo DESC;
```

### Get Photos by Camera

```sql
SELECT pm.camera_model, COUNT(*) as count
FROM photo_metadata pm
GROUP BY pm.camera_model
ORDER BY count DESC;
```

### Find Blurry Photos

```sql
SELECT m.filename, pm.blur_laplacian, pm.blur_tenengrad
FROM media m
JOIN photo_metadata pm ON m.id = pm.media_id
WHERE pm.blur_laplacian < 50
   OR pm.blur_tenengrad < 100
ORDER BY pm.blur_laplacian ASC;
```

---

## Performance Considerations

### Indexes
- All foreign keys are indexed
- Common filter fields (rating, color, capture_time) are indexed
- Burst queries optimized with `burst_id` index

### Query Optimization
- Use `LEFT JOIN` for optional metadata tables
- Filter on `media.is_available = 1` to exclude deleted files
- Use `LIMIT` for paginated results

### Typical Query Times (234 photos)
- Load all photos: **< 10ms**
- Filter by rating: **< 5ms**
- Burst grouping: **< 20ms**
- Full-text search in keywords: **< 15ms**

---

## Migration & Sync Strategy

See `SYNC_STRATEGY.md` for detailed sync behavior.

**Summary:**
1. **Initial Migration:** Scan folders → parse JSON → populate SQLite
2. **Incremental Sync:** Monitor JSON file changes → update SQLite
3. **Conflict Resolution:** JSON always wins
4. **Write Operations:** Write to JSON first → sync to SQLite

---

## Future Enhancements

### Phase 4 Features (Schema Ready)

All Phase 4 fields are **already in the schema** but not yet populated:

1. **RAW + JPEG Tandem** (Phase 4a)
   - `has_raw_tandem`, `raw_file_path`, `jpeg_file_path`
   - Detect and link RAW+JPEG pairs

2. **Non-Destructive Edits** (Phase 4b)
   - `has_edits`, `edit_stack`, `edit_version`
   - Store edit operations as JSON

3. **Render Cache** (Phase 4c)
   - `cached_thumbnail_path`, `cached_preview_path`, `cached_fullres_path`
   - Cache edited/rendered versions

4. **Advanced Analyses** (Phase 4d)
   - `is_landscape_photo`, `is_night_photo`, `face_count`, `faces_data`
   - ML-based image classification

---

## See Also

- `JSON_SIDECAR_FORMAT.md` - JSON file structure
- `SYNC_STRATEGY.md` - Synchronization behavior
- `PHASE3_SQLITE_ARCHITECTURE.md` - Overall system design
- `workspace_schema.sql` - Full SQL schema
