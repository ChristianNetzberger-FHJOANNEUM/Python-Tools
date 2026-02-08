-- ============================================================================
-- PROJECT DATABASE SCHEMA
-- ============================================================================
-- 
-- Purpose: Project-specific data (timeline, audio tracks, references)
-- Location: projects/{project_id}/project.db
-- 
-- Design Principle: Project-specific data only (NOT portable)
-- - References to workspace media (by ID and path)
-- - Timeline configuration
-- - Audio track assignments
-- - Spatial audio settings
-- 
-- Version: 1.0
-- Date: 2026-02-08
-- ============================================================================

-- ============================================================================
-- 1. PROJECT MEDIA ASSIGNMENTS (References to Workspace)
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Reference to workspace media
    workspace_media_id INTEGER NOT NULL,
    workspace_path TEXT NOT NULL,  -- Denormalized for quick lookup and sync
    media_type TEXT NOT NULL CHECK(media_type IN ('photo', 'video', 'audio')),
    
    -- Project-Specific Overrides (NULL = use workspace value)
    project_rating INTEGER CHECK(project_rating >= 0 AND project_rating <= 5),
    project_color TEXT CHECK(project_color IN ('red', 'yellow', 'green', 'blue', 'purple', NULL)),
    project_keywords TEXT,   -- JSON array, merged with workspace keywords
    project_comment TEXT,
    
    -- Ordering/Sequence (for basic slideshows without timeline)
    sequence_order INTEGER,
    section TEXT,  -- Group into sections: "intro", "main", "outro"
    
    -- Project-Specific Flags
    is_selected BOOLEAN DEFAULT 1,
    is_hero_image BOOLEAN DEFAULT 0,
    burst_keep BOOLEAN DEFAULT 0,  -- For burst photos (project-specific decision)
    
    -- Timestamps
    added_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now')),
    
    UNIQUE(workspace_media_id)
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_pm_sequence ON project_media(sequence_order);
CREATE INDEX IF NOT EXISTS idx_pm_section ON project_media(section);
CREATE INDEX IF NOT EXISTS idx_pm_selected ON project_media(is_selected);
CREATE INDEX IF NOT EXISTS idx_pm_media_type ON project_media(media_type);
CREATE INDEX IF NOT EXISTS idx_pm_workspace_id ON project_media(workspace_media_id);

-- ============================================================================
-- 2. TIMELINE CONFIGURATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL UNIQUE,
    
    -- Timeline Settings
    total_duration REAL,  -- Calculated from all slides (in seconds)
    default_slide_duration REAL DEFAULT 5.0,
    default_transition_duration REAL DEFAULT 1.0,
    
    -- Playback Settings
    autoplay BOOLEAN DEFAULT 1,
    loop BOOLEAN DEFAULT 0,
    show_controls BOOLEAN DEFAULT 1,
    show_progress_bar BOOLEAN DEFAULT 1,
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- ============================================================================
-- 3. TIMELINE SLIDES (Precise Timing)
-- ============================================================================

CREATE TABLE IF NOT EXISTS timeline_slides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    media_id INTEGER NOT NULL REFERENCES project_media(id) ON DELETE CASCADE,
    
    -- Timeline Position
    sequence_order INTEGER NOT NULL,
    start_time REAL NOT NULL,  -- Seconds from timeline start
    duration REAL NOT NULL,     -- How long slide is displayed
    
    -- Transition
    transition_type TEXT DEFAULT 'fade' CHECK(transition_type IN (
        'fade', 'slide_left', 'slide_right', 'slide_up', 'slide_down', 
        'zoom_in', 'zoom_out', 'crossfade', 'none'
    )),
    transition_duration REAL DEFAULT 1.0,
    
    -- Ken Burns Effect (Pan & Zoom during slide)
    pan_start_x REAL DEFAULT 0.5 CHECK(pan_start_x >= 0.0 AND pan_start_x <= 1.0),
    pan_start_y REAL DEFAULT 0.5 CHECK(pan_start_y >= 0.0 AND pan_start_y <= 1.0),
    pan_end_x REAL DEFAULT 0.5 CHECK(pan_end_x >= 0.0 AND pan_end_x <= 1.0),
    pan_end_y REAL DEFAULT 0.5 CHECK(pan_end_y >= 0.0 AND pan_end_y <= 1.0),
    zoom_start REAL DEFAULT 1.0,   -- 1.0 = no zoom, >1.0 = zoomed in
    zoom_end REAL DEFAULT 1.0,
    
    -- Text Overlay (Optional)
    caption TEXT,
    caption_position TEXT CHECK(caption_position IN (
        'top', 'bottom', 'center', 'top_left', 'top_right', 
        'bottom_left', 'bottom_right', NULL
    )),
    caption_style TEXT,  -- JSON: {"color": "#fff", "fontSize": "24px", "fontFamily": "Arial"}
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    
    UNIQUE(project_id, sequence_order)
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_ts_project_time ON timeline_slides(project_id, start_time);
CREATE INDEX IF NOT EXISTS idx_ts_project_order ON timeline_slides(project_id, sequence_order);

-- ============================================================================
-- 4. AUDIO TRACKS (Multi-Track Support with Spatial Audio)
-- ============================================================================

CREATE TABLE IF NOT EXISTS timeline_audio_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    audio_id INTEGER REFERENCES project_media(id) ON DELETE SET NULL,  -- NULL for multi-channel sources
    
    -- Track Assignment
    track_number INTEGER DEFAULT 1,  -- Track 1 = Background, 2 = Voiceover, 3 = SFX
    track_name TEXT,
    track_type TEXT CHECK(track_type IN (
        'music', 'dialog', 'sfx', 'ambience', 'foley', NULL
    )),
    
    -- Timeline Position
    start_time REAL NOT NULL,  -- When audio starts on timeline (seconds)
    duration REAL,             -- NULL = until end of audio file
    end_time REAL,             -- Calculated: start_time + duration
    
    -- ============================================================================
    -- SPATIAL AUDIO CONFIGURATION (Future-Ready for Dolby Atmos)
    -- ============================================================================
    
    -- Channel Mode (determines export format)
    channel_mode TEXT DEFAULT 'stereo' CHECK(channel_mode IN (
        'mono',           -- Single channel
        'stereo',         -- L/R
        'surround_51',    -- 5.1: FL, FR, C, LFE, SL, SR
        'surround_71',    -- 7.1: + BL, BR
        'atmos_bed',      -- Atmos bed channels (7.1.4)
        'atmos_object'    -- Atmos audio object (movable)
    )),
    
    -- Stereo/Mono Positioning
    pan REAL DEFAULT 0.0 CHECK(pan >= -1.0 AND pan <= 1.0),  -- -1=left, 0=center, 1=right
    
    -- 3D Spatial Position (for Object-Based Audio like Atmos)
    position_x REAL DEFAULT 0.0 CHECK(position_x >= -1.0 AND position_x <= 1.0),  -- Left(-1) to Right(1)
    position_y REAL DEFAULT 0.0 CHECK(position_y >= -1.0 AND position_y <= 1.0),  -- Back(-1) to Front(1)
    position_z REAL DEFAULT 0.0 CHECK(position_z >= 0.0 AND position_z <= 1.0),   -- Floor(0) to Ceiling(1)
    
    -- Spatial Movement (Position over time)
    spatial_animation TEXT,  -- JSON: [{"time": 0, "x": -1, "y": 0, "z": 0.5}, {"time": 5, "x": 1, "y": 0, "z": 0.5}]
    
    -- Volume & Processing
    volume REAL DEFAULT 1.0 CHECK(volume >= 0.0 AND volume <= 2.0),
    fade_in REAL DEFAULT 0.0,   -- Fade-in duration (seconds)
    fade_out REAL DEFAULT 0.0,  -- Fade-out duration (seconds)
    
    -- Audio Ducking (for voiceover over music)
    ducking_enabled BOOLEAN DEFAULT 0,
    ducking_amount REAL DEFAULT 0.3 CHECK(ducking_amount >= 0.0 AND ducking_amount <= 1.0),
    ducking_target_track INTEGER,  -- Which track number triggers ducking
    
    -- Loop/Repeat
    loop_audio BOOLEAN DEFAULT 0,
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_tat_project_time ON timeline_audio_tracks(project_id, start_time, track_number);
CREATE INDEX IF NOT EXISTS idx_tat_track ON timeline_audio_tracks(track_number);
CREATE INDEX IF NOT EXISTS idx_tat_audio_id ON timeline_audio_tracks(audio_id);

-- ============================================================================
-- 5. MULTI-CHANNEL SOURCES (for 5.1/7.1/Atmos from Multiple MP3s)
-- ============================================================================

CREATE TABLE IF NOT EXISTS multichannel_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timeline_track_id INTEGER NOT NULL REFERENCES timeline_audio_tracks(id) ON DELETE CASCADE,
    
    -- Source Audio File (single channel)
    source_audio_id INTEGER NOT NULL REFERENCES project_media(id) ON DELETE CASCADE,
    
    -- Channel Assignment
    channel_name TEXT NOT NULL CHECK(channel_name IN (
        -- Stereo
        'left', 'right',
        
        -- 5.1 Surround
        'front_left', 'front_right', 'center', 'lfe', 
        'surround_left', 'surround_right',
        
        -- 7.1 Surround (adds back channels)
        'back_left', 'back_right',
        
        -- Dolby Atmos Bed Channels (7.1.4)
        'top_front_left', 'top_front_right', 
        'top_back_left', 'top_back_right',
        
        -- Extended Atmos
        'top_center', 'wide_left', 'wide_right'
    )),
    
    -- Channel Gain (for individual channel mixing)
    channel_gain REAL DEFAULT 1.0 CHECK(channel_gain >= 0.0 AND channel_gain <= 2.0),
    
    -- Delay (for phase alignment, in milliseconds)
    delay_ms REAL DEFAULT 0.0,
    
    UNIQUE(timeline_track_id, channel_name)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_mcs_track ON multichannel_sources(timeline_track_id);

-- ============================================================================
-- 6. DOLBY ATMOS OBJECTS (Optional, for Advanced Features)
-- ============================================================================

CREATE TABLE IF NOT EXISTS atmos_audio_objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timeline_track_id INTEGER NOT NULL REFERENCES timeline_audio_tracks(id) ON DELETE CASCADE,
    
    -- Object Metadata
    object_name TEXT,
    object_type TEXT CHECK(object_type IN (
        'dialog', 'music', 'ambience', 'sfx', 'foley', NULL
    )),
    
    -- Spatial Position Keyframes (position over time)
    position_keyframes TEXT,  -- JSON: [{"time": 0, "x": 0, "y": 0.5, "z": 0}, {"time": 10, "x": 1, "y": -0.5, "z": 0.8}]
    
    -- Object Properties
    size REAL DEFAULT 0.0 CHECK(size >= 0.0 AND size <= 1.0),  -- 0=point source, 1=omnidirectional
    diffuseness REAL DEFAULT 0.0 CHECK(diffuseness >= 0.0 AND diffuseness <= 1.0),
    
    -- Distance & Attenuation
    distance_rolloff TEXT DEFAULT 'inverse' CHECK(distance_rolloff IN (
        'none', 'linear', 'inverse', 'exponential'
    )),
    min_distance REAL DEFAULT 1.0,
    max_distance REAL DEFAULT 10.0,
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Index
CREATE INDEX IF NOT EXISTS idx_aao_track ON atmos_audio_objects(timeline_track_id);

-- ============================================================================
-- 7. TIMELINE MARKERS (Navigation, Chapters, Pause Points)
-- ============================================================================

CREATE TABLE IF NOT EXISTS timeline_markers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    
    -- Marker Position
    time REAL NOT NULL,  -- Position on timeline (in seconds)
    
    -- Marker Info
    label TEXT NOT NULL,
    color TEXT DEFAULT 'blue',
    marker_type TEXT CHECK(marker_type IN (
        'chapter',      -- Chapter marker (show in chapter list)
        'pause_point',  -- Auto-pause for presentations
        'note',         -- Simple note/comment
        'cue',          -- Cue point for live presentation
        NULL
    )),
    
    -- Navigation & Behavior
    is_chapter BOOLEAN DEFAULT 0,  -- Show in chapter list
    auto_pause BOOLEAN DEFAULT 0,  -- Auto-pause timeline
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_tm_project_time ON timeline_markers(project_id, time);
CREATE INDEX IF NOT EXISTS idx_tm_project_type ON timeline_markers(project_id, marker_type);
CREATE INDEX IF NOT EXISTS idx_tm_chapters ON timeline_markers(project_id, is_chapter);

-- ============================================================================
-- 8. PRESENTATION CUES (Speaker Notes & Actions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS presentation_cues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    
    -- Cue Timing
    slide_id INTEGER REFERENCES timeline_slides(id) ON DELETE CASCADE,
    cue_time REAL,  -- Optional: time within slide (for mid-slide cues)
    
    -- Cue Content
    speaker_notes TEXT,  -- Notes for presenter
    action TEXT CHECK(action IN (
        'pause',          -- Pause slideshow
        'continue',       -- Continue playback
        'wait_for_click', -- Wait for user input
        'advance_auto',   -- Auto-advance
        NULL
    )),
    
    -- Audience Interaction
    show_question BOOLEAN DEFAULT 0,
    question_text TEXT,
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Index
CREATE INDEX IF NOT EXISTS idx_pc_slide ON presentation_cues(project_id, slide_id);

-- ============================================================================
-- 9. PROJECT AUDIO CONFIGURATION (Global Settings)
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_audio_config (
    project_id TEXT PRIMARY KEY,
    
    -- Target Output Format
    output_format TEXT DEFAULT 'stereo' CHECK(output_format IN (
        'mono', 'stereo', 'surround_51', 'surround_71', 'atmos'
    )),
    
    -- Sample Rate & Bit Depth
    sample_rate INTEGER DEFAULT 48000 CHECK(sample_rate IN (44100, 48000, 96000, 192000)),
    bit_depth INTEGER DEFAULT 24 CHECK(bit_depth IN (16, 24, 32)),
    
    -- LFE (Low Frequency Effects) Configuration
    lfe_enabled BOOLEAN DEFAULT 1,
    lfe_crossover_freq INTEGER DEFAULT 120,  -- Hz
    
    -- Downmix Settings (for stereo compatibility)
    stereo_downmix_mode TEXT DEFAULT 'loro' CHECK(stereo_downmix_mode IN (
        'loro',    -- Lo/Ro (Left only/Right only)
        'ltrt'     -- Lt/Rt (Left total/Right total) - Dolby Surround compatible
    )),
    
    -- Master Volume & Normalization
    master_volume REAL DEFAULT 1.0 CHECK(master_volume >= 0.0 AND master_volume <= 2.0),
    normalize_audio BOOLEAN DEFAULT 1,
    target_lufs REAL DEFAULT -16.0,  -- EBU R128 Standard
    
    -- Dolby Atmos Settings (when atmos output_format)
    atmos_max_objects INTEGER DEFAULT 128,
    atmos_bed_channels TEXT DEFAULT '7.1.4',  -- Format: channels.subwoofer.height
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- ============================================================================
-- 10. VIDEO EMBEDDING CONFIGURATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_video_config (
    video_id INTEGER PRIMARY KEY REFERENCES project_media(id) ON DELETE CASCADE,
    
    -- Embedding Strategy
    embed_strategy TEXT CHECK(embed_strategy IN (
        'inline',     -- Embed directly (for short videos)
        'youtube',    -- YouTube reference (for long videos)
        'both'        -- Both options available
    )),
    
    -- Inline Config (for short videos)
    inline_max_duration REAL DEFAULT 30.0,  -- Max duration for inline
    inline_autoplay BOOLEAN DEFAULT 0,
    inline_loop BOOLEAN DEFAULT 0,
    inline_muted BOOLEAN DEFAULT 0,
    
    -- YouTube Config (for long videos)
    youtube_start_time INTEGER DEFAULT 0,   -- Start at X seconds
    youtube_end_time INTEGER,               -- End at Y seconds (NULL = full video)
    youtube_autoplay BOOLEAN DEFAULT 0,
    youtube_show_controls BOOLEAN DEFAULT 1,
    youtube_modestbranding BOOLEAN DEFAULT 1,
    
    -- Thumbnail Override
    custom_thumbnail_path TEXT,
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- ============================================================================
-- 11. DATABASE METADATA
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
    ('db_type', 'project');

-- ============================================================================
-- END OF PROJECT SCHEMA
-- ============================================================================
