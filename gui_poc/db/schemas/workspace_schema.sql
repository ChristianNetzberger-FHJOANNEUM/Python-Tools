-- ============================================================================
-- WORKSPACE MEDIA DATABASE SCHEMA
-- ============================================================================
-- 
-- Purpose: Global media pool for ALL photos/videos/audio in workspace
-- Location: workspace/workspace_media.db
-- 
-- Design Principle: SQLite as PERFORMANCE CACHE, JSON as SOURCE OF TRUTH
-- - JSON sidecars (.metadata.json, .sidecar.json) remain portable
-- - SQLite provides fast queries, aggregations, indexes
-- - Auto-sync keeps both systems in sync
-- 
-- Version: 1.0
-- Date: 2026-02-08
-- ============================================================================

-- ============================================================================
-- 1. UNIVERSAL MEDIA TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    folder TEXT NOT NULL,
    
    -- Workspace Association (for filtering)
    workspace_path TEXT,  -- NULL = available for all workspaces
    
    -- Media Type Classification
    media_type TEXT NOT NULL CHECK(media_type IN ('photo', 'video', 'audio')),
    
    -- File Info
    file_size INTEGER,
    file_mtime INTEGER,  -- File modification time (Unix timestamp)
    
    -- Availability Status
    is_available BOOLEAN DEFAULT 1,  -- 0 = file/folder no longer exists
    last_verified INTEGER,  -- Last time file existence was verified
    
    -- Common Metadata (synced from JSON sidecars)
    rating INTEGER DEFAULT 0 CHECK(rating >= 0 AND rating <= 5),
    color TEXT CHECK(color IN ('red', 'yellow', 'green', 'blue', 'purple', NULL)),
    keywords TEXT,  -- JSON array: ["keyword1", "keyword2"]
    comment TEXT,
    
    -- Sync Status
    json_mtime INTEGER,  -- When JSON was last synced
    sync_status TEXT DEFAULT 'synced' CHECK(sync_status IN ('synced', 'pending', 'conflict')),
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_media_type ON media(media_type);
CREATE INDEX IF NOT EXISTS idx_folder ON media(folder);
CREATE INDEX IF NOT EXISTS idx_workspace ON media(workspace_path);
CREATE INDEX IF NOT EXISTS idx_available ON media(is_available);
CREATE INDEX IF NOT EXISTS idx_rating ON media(rating DESC);
CREATE INDEX IF NOT EXISTS idx_color ON media(color);
CREATE INDEX IF NOT EXISTS idx_updated ON media(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_path_lookup ON media(path);
CREATE INDEX IF NOT EXISTS idx_filename ON media(filename);

-- ============================================================================
-- 2. PHOTO-SPECIFIC METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS photo_metadata (
    media_id INTEGER PRIMARY KEY REFERENCES media(id) ON DELETE CASCADE,
    
    -- EXIF Data (from original file or sidecar)
    capture_time TEXT,
    width INTEGER,
    height INTEGER,
    camera_make TEXT,
    camera_model TEXT,
    lens_model TEXT,
    iso INTEGER,
    aperture REAL,
    shutter_speed TEXT,
    focal_length REAL,
    orientation INTEGER,
    
    -- ============================================================================
    -- RAW + JPEG TANDEM (Phase 4a - FUTURE-READY)
    -- ============================================================================
    has_raw_tandem BOOLEAN DEFAULT 0,
    raw_file_path TEXT,              -- Path to RAW file (RW2, CR2, NEF, etc.)
    jpeg_file_path TEXT,             -- Path to JPEG file
    tandem_primary TEXT CHECK(tandem_primary IN ('raw', 'jpeg', NULL)),
    tandem_export_from TEXT CHECK(tandem_export_from IN ('raw', 'jpeg', 'auto', NULL)) DEFAULT 'auto',
    
    -- ============================================================================
    -- NON-DESTRUCTIVE EDITS (Phase 4b - FUTURE-READY)
    -- ============================================================================
    has_edits BOOLEAN DEFAULT 0,
    edit_stack TEXT,                 -- JSON: [{"operation": "exposure", "params": {...}, "enabled": true}]
    edit_version TEXT DEFAULT '1.0', -- Schema version for edit operations
    edits_updated_at INTEGER,
    edits_applied_by TEXT,           -- User or "auto"
    
    -- ============================================================================
    -- RENDER CACHE (Phase 4c - FUTURE-READY)
    -- ============================================================================
    cached_thumbnail_path TEXT,      -- Path to edited thumbnail (800px)
    cached_preview_path TEXT,        -- Path to edited preview (2048px)
    cached_fullres_path TEXT,        -- Path to cached full-res render
    cache_invalidated BOOLEAN DEFAULT 0,
    cache_date INTEGER,
    cache_size_bytes INTEGER,
    
    -- ============================================================================
    -- ADVANCED ANALYSES (Phase 4d - FUTURE-READY)
    -- ============================================================================
    analyses_extended TEXT,          -- JSON: {"landscape": {...}, "night": {...}, "faces": [...]}
    
    -- Landscape Detection
    is_landscape_photo BOOLEAN DEFAULT 0,
    landscape_confidence REAL,
    horizon_angle REAL,
    
    -- Night/Low-Light Detection
    is_night_photo BOOLEAN DEFAULT 0,
    night_detection_confidence REAL,
    
    -- Face Detection
    face_count INTEGER DEFAULT 0,
    faces_data TEXT,                 -- JSON: [{"x": 0.3, "y": 0.4, "confidence": 0.98}]
    
    -- Blur Detection (from sidecar analyses.blur)
    blur_laplacian REAL,
    blur_laplacian_threshold REAL,
    blur_tenengrad REAL,
    blur_tenengrad_threshold REAL,
    blur_roi REAL,
    blur_roi_threshold REAL,
    blur_detection_date INTEGER,
    
    -- Burst Info (from sidecar analyses.burst)
    is_burst_candidate BOOLEAN DEFAULT 0,
    burst_id TEXT,
    burst_neighbors TEXT,  -- JSON array of paths
    burst_score REAL,
    burst_detection_date INTEGER,
    
    -- Quality Metrics
    sharpness_score REAL,
    exposure_score REAL,
    
    -- Sync Info
    exif_synced_at INTEGER,
    sidecar_synced_at INTEGER
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_photo_capture_time ON photo_metadata(capture_time DESC);
CREATE INDEX IF NOT EXISTS idx_photo_burst_id ON photo_metadata(burst_id);
CREATE INDEX IF NOT EXISTS idx_photo_camera ON photo_metadata(camera_model);
CREATE INDEX IF NOT EXISTS idx_photo_burst_candidate ON photo_metadata(is_burst_candidate);
CREATE INDEX IF NOT EXISTS idx_photo_has_raw ON photo_metadata(has_raw_tandem);
CREATE INDEX IF NOT EXISTS idx_photo_has_edits ON photo_metadata(has_edits);
CREATE INDEX IF NOT EXISTS idx_photo_landscape ON photo_metadata(is_landscape_photo);
CREATE INDEX IF NOT EXISTS idx_photo_night ON photo_metadata(is_night_photo);

-- ============================================================================
-- 3. VIDEO-SPECIFIC METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS video_metadata (
    media_id INTEGER PRIMARY KEY REFERENCES media(id) ON DELETE CASCADE,
    
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
    
    -- YouTube Integration (for long videos)
    youtube_url TEXT,
    youtube_video_id TEXT,
    youtube_upload_date INTEGER,
    youtube_status TEXT CHECK(youtube_status IN (
        'draft', 'uploaded', 'public', 'unlisted', 'private', NULL
    )),
    
    -- Usage Intent
    embed_type TEXT CHECK(embed_type IN (
        'inline',       -- Short videos: embed directly
        'youtube_ref',  -- Long videos: YouTube link
        'both',         -- Both options available
        NULL
    )),
    
    -- Thumbnail
    custom_thumbnail_path TEXT,
    thumbnail_time REAL DEFAULT 0.0,  -- Time in video for thumbnail extraction
    
    -- Sync Info
    video_info_synced_at INTEGER
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_video_duration ON video_metadata(duration_seconds);
CREATE INDEX IF NOT EXISTS idx_video_youtube_id ON video_metadata(youtube_video_id);
CREATE INDEX IF NOT EXISTS idx_video_codec ON video_metadata(codec);

-- ============================================================================
-- 4. AUDIO-SPECIFIC METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS audio_metadata (
    media_id INTEGER PRIMARY KEY REFERENCES media(id) ON DELETE CASCADE,
    
    -- Audio Properties
    duration_seconds REAL,
    sample_rate INTEGER,
    channels INTEGER,
    bitrate INTEGER,
    codec TEXT,
    
    -- Music Metadata (ID3 tags)
    title TEXT,
    artist TEXT,
    album TEXT,
    genre TEXT,
    year INTEGER,
    track_number INTEGER,
    
    -- Usage Category (for audio pool)
    category TEXT CHECK(category IN (
        'music',      -- Background music
        'voiceover',  -- Narration/dialog
        'sfx',        -- Sound effects
        'ambient',    -- Ambient sounds
        'foley',      -- Foley sounds
        'other',
        NULL
    )),
    
    -- Audio Analysis
    bpm REAL,  -- Beats per minute (for music)
    key_signature TEXT,  -- Musical key
    energy_level REAL CHECK(energy_level >= 0.0 AND energy_level <= 1.0),
    
    -- Sync Info
    audio_info_synced_at INTEGER
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_audio_duration ON audio_metadata(duration_seconds);
CREATE INDEX IF NOT EXISTS idx_audio_category ON audio_metadata(category);
CREATE INDEX IF NOT EXISTS idx_audio_artist ON audio_metadata(artist);
CREATE INDEX IF NOT EXISTS idx_audio_genre ON audio_metadata(genre);

-- ============================================================================
-- 5. SYNC STATUS TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS sync_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- What was synced
    sync_type TEXT NOT NULL CHECK(sync_type IN (
        'full_rebuild',     -- Complete rebuild from JSON
        'incremental',      -- Single file update
        'folder_scan',      -- Folder rescan
        'migration'         -- Initial migration
    )),
    
    -- Sync Details
    items_processed INTEGER DEFAULT 0,
    items_added INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    items_deleted INTEGER DEFAULT 0,
    items_errors INTEGER DEFAULT 0,
    
    -- Performance
    duration_seconds REAL,
    
    -- Status
    status TEXT CHECK(status IN ('running', 'completed', 'failed', 'partial')),
    error_message TEXT,
    
    -- Timestamps
    started_at INTEGER,
    completed_at INTEGER
);

CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_status(status, started_at DESC);

-- ============================================================================
-- 6. DATABASE METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS db_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Initialize metadata
INSERT OR IGNORE INTO db_metadata (key, value) VALUES 
    ('schema_version', '1.0'),
    ('created_at', strftime('%s', 'now')),
    ('db_type', 'workspace');

-- ============================================================================
-- END OF WORKSPACE SCHEMA
-- ============================================================================
