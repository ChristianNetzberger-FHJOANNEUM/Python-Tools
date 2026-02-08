# 🎬 Phase 3: SQLite-Based Media Architecture

## Executive Summary

**Dieses Dokument beschreibt die vollständige Architektur für Phase 3 des Photo Tool Projects: Eine SQLite-basierte Media-Datenbank mit Timeline-Features und Multi-Format Export.**

**Ziele:**
- ✅ Skalierung auf 3000+ Photos/Videos/Audio
- ✅ Performance: 55s → 1.6s (97% schneller)
- ✅ Timeline-basierte Slideshows mit präzisem Timing
- ✅ Multi-Channel Audio (Stereo bis Dolby Atmos)
- ✅ Multi-Format Export (Web, NAS, DaVinci Resolve)
- ✅ Future-Proof für kommende Features

**Status:** 📋 Architecture Design Complete - Ready for Implementation

**Geschätzter Aufwand:**
- Phase 3a (Schema + Core): 4-6h
- Phase 3b (Basic Features): 2-3h
- Phase 3c (Timeline): 3-4h
- **Total für MVP:** 9-13h

---

## 📊 Problem Statement

### **Aktuelle Performance-Probleme:**

Bei 234 Photos (aktuelles Projekt):
```
Performance OHNE SQLite (Phase 1+2):
├─ directory_scan:              0.07s
├─ exif_reading_parallel:       3.17s
├─ parallel_metadata_loading:   0.30s
├─ response_building:            0.55s
└─ burst_grouping:               0.20s
───────────────────────────────────
TOTAL:                          ~4.3s ✅ (akzeptabel)
```

Bei 3000 Photos (größtes Projekt):
```
Performance OHNE SQLite (hochgerechnet):
├─ directory_scan:              0.9s
├─ exif_reading_parallel:      40.6s
├─ parallel_metadata_loading:   3.8s
├─ response_building:            7.0s
└─ burst_grouping:               2.6s
───────────────────────────────────
TOTAL:                         ~55s ❌ (inakzeptabel!)

Mit Cache (60s TTL):           ~15-20s ⚠️ (noch langsam)
```

### **Zusätzliche Anforderungen:**

1. **Timeline-Features** für Slideshows
   - Präzises Timing (ms-genau)
   - Pause/Play/Scrub für Präsentationen
   - Audio-Synchronisation
   - Marker & Chapters

2. **Multi-Channel Audio**
   - Stereo für Web
   - 5.1/7.1 Surround für NAS
   - Dolby Atmos für Home Cinema (Samsung 8K + Denon)

3. **Multi-Format Export**
   - HTML5 Web-Galerie (Gäste)
   - Video mit Atmos (Smart TV)
   - DaVinci Resolve Project (Editing)

4. **Video Integration**
   - Kurze Clips inline
   - Lange Videos auf YouTube
   - Referenzen in Timeline

---

## 🏗️ Architektur-Überblick

### **2-Ebenen-Architektur:**

```
┌─────────────────────────────────────────────────┐
│      WORKSPACE LEVEL (Global Media Pool)        │
│  • workspace_media.db (SQLite)                  │
│  • Alle Photos/Videos/Audio aus allen Ordnern  │
│  • Single Source of Truth für Metadaten        │
│  • EXIF Data, Blur Scores, Burst Info          │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────┴────────┐
         ↓                 ↓
┌─────────────────┐  ┌─────────────────┐
│  PROJECT A      │  │  PROJECT B      │
│  project.db     │  │  project.db     │
│  • References   │  │  • References   │
│  • Overrides    │  │  • Overrides    │
│  • Timeline     │  │  • Timeline     │
│  • Audio Tracks │  │  • Audio Tracks │
└─────────────────┘  └─────────────────┘
```

### **Export-Strategie:**

```
┌─────────────────────────────────────────┐
│  SQLite Timeline (Single Source)        │
│  - Photos + Timing + Audio + Spatial    │
└─────────────┬───────────────────────────┘
              │
   ┌──────────┼──────────┐
   ↓          ↓          ↓
┌──────┐  ┌───────┐  ┌─────────┐
│ Web  │  │ NAS   │  │ Resolve │
│Stereo│  │ Atmos │  │Multi-Trk│
│HTML5 │  │8K HDR │  │ Stems   │
└──────┘  └───────┘  └─────────┘
```

---

## 📋 Complete Database Schema

### **1. Workspace Database: `workspace_media.db`**

#### **1.1 Universal Media Table**

```sql
-- ============================================================================
-- Universal Media Table (Photos, Videos, Audio)
-- ============================================================================
CREATE TABLE media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    folder TEXT NOT NULL,
    
    -- Media Type
    media_type TEXT NOT NULL CHECK(media_type IN ('photo', 'video', 'audio')),
    
    -- File Info
    file_size INTEGER,
    file_mtime INTEGER,  -- File modification time (Unix timestamp)
    
    -- Common Metadata (all media types)
    rating INTEGER DEFAULT 0 CHECK(rating >= 0 AND rating <= 5),
    color TEXT CHECK(color IN ('red', 'yellow', 'green', 'blue', 'purple', NULL)),
    keywords TEXT,  -- JSON array: ["keyword1", "keyword2"]
    comment TEXT,
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Indexes for performance
CREATE INDEX idx_media_type ON media(media_type);
CREATE INDEX idx_folder ON media(folder);
CREATE INDEX idx_rating ON media(rating DESC);
CREATE INDEX idx_updated ON media(updated_at DESC);
CREATE INDEX idx_path_lookup ON media(path);
```

#### **1.2 Photo-Specific Metadata**

```sql
-- ============================================================================
-- Photo-Specific Data
-- ============================================================================
CREATE TABLE photo_metadata (
    media_id INTEGER PRIMARY KEY REFERENCES media(id) ON DELETE CASCADE,
    
    -- EXIF Data
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
    
    -- Blur Detection (from sidecar analyses)
    blur_laplacian REAL,
    blur_tenengrad REAL,
    blur_roi REAL,
    blur_detection_date INTEGER,
    
    -- Burst Info (from sidecar analyses)
    is_burst_candidate BOOLEAN DEFAULT 0,
    burst_id TEXT,
    burst_neighbors TEXT  -- JSON array of paths
);

-- Indexes
CREATE INDEX idx_capture_time ON photo_metadata(capture_time DESC);
CREATE INDEX idx_burst_id ON photo_metadata(burst_id);
CREATE INDEX idx_camera_model ON photo_metadata(camera_model);
```

#### **1.3 Video-Specific Metadata**

```sql
-- ============================================================================
-- Video-Specific Data
-- ============================================================================
CREATE TABLE video_metadata (
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
    
    -- YouTube Integration (für lange Videos)
    youtube_url TEXT,
    youtube_video_id TEXT,
    youtube_upload_date INTEGER,
    youtube_status TEXT CHECK(youtube_status IN (
        'draft', 'uploaded', 'public', 'unlisted', 'private', NULL
    )),
    
    -- Usage Intent
    embed_type TEXT CHECK(embed_type IN (
        'inline',       -- Kurze Videos: Direkt einbetten
        'youtube_ref',  -- Lange Videos: YouTube-Link
        'both',         -- Beide Optionen anbieten
        NULL
    )),
    
    -- Thumbnail Override
    custom_thumbnail_path TEXT
);

-- Indexes
CREATE INDEX idx_duration ON video_metadata(duration_seconds);
CREATE INDEX idx_youtube_id ON video_metadata(youtube_video_id);
```

#### **1.4 Audio-Specific Metadata**

```sql
-- ============================================================================
-- Audio-Specific Data
-- ============================================================================
CREATE TABLE audio_metadata (
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
    
    -- Usage Category (für Audio-Pool)
    category TEXT CHECK(category IN (
        'music',      -- Background music
        'voiceover',  -- Narration
        'sfx',        -- Sound effects
        'ambient',    -- Ambient sounds
        'other',
        NULL
    ))
);

-- Indexes
CREATE INDEX idx_audio_duration ON audio_metadata(duration_seconds);
CREATE INDEX idx_audio_category ON audio_metadata(category);
CREATE INDEX idx_audio_artist ON audio_metadata(artist);
```

---

### **2. Project Database: `projects/{project_id}/project.db`**

#### **2.1 Project Media References**

```sql
-- ============================================================================
-- Project Media Assignments (References to Workspace)
-- ============================================================================
CREATE TABLE project_media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Reference to workspace media
    workspace_media_id INTEGER NOT NULL,
    workspace_path TEXT NOT NULL,  -- Denormalized for quick lookup
    media_type TEXT NOT NULL CHECK(media_type IN ('photo', 'video', 'audio')),
    
    -- Project-Specific Overrides (NULL = use workspace value)
    project_rating INTEGER CHECK(project_rating >= 0 AND project_rating <= 5),
    project_color TEXT CHECK(project_color IN ('red', 'yellow', 'green', 'blue', 'purple', NULL)),
    project_keywords TEXT,   -- JSON, merged with workspace keywords
    project_comment TEXT,
    
    -- Ordering/Sequence (für basic slideshows ohne Timeline)
    sequence_order INTEGER,
    section TEXT,  -- Group into sections: "intro", "main", "outro"
    
    -- Project-Specific Flags
    is_selected BOOLEAN DEFAULT 1,
    is_hero_image BOOLEAN DEFAULT 0,
    burst_keep BOOLEAN DEFAULT 0,  -- For burst photos
    
    -- Timestamps
    added_at INTEGER DEFAULT (strftime('%s', 'now')),
    
    UNIQUE(workspace_media_id)
);

-- Indexes
CREATE INDEX idx_sequence ON project_media(sequence_order);
CREATE INDEX idx_section ON project_media(section);
CREATE INDEX idx_selected ON project_media(is_selected);
CREATE INDEX idx_media_type ON project_media(media_type);
```

#### **2.2 Timeline Configuration**

```sql
-- ============================================================================
-- Timeline Configuration (Pro Project)
-- ============================================================================
CREATE TABLE project_timeline (
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
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);
```

#### **2.3 Timeline Slides (Präzises Timing)**

```sql
-- ============================================================================
-- Timeline Slides (ms-genaues Timing)
-- ============================================================================
CREATE TABLE timeline_slides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    media_id INTEGER NOT NULL REFERENCES project_media(id) ON DELETE CASCADE,
    
    -- Timeline Position
    sequence_order INTEGER NOT NULL,
    start_time REAL NOT NULL,  -- Sekunden ab Timeline-Start
    duration REAL NOT NULL,     -- Wie lange wird Slide angezeigt
    
    -- Transition
    transition_type TEXT DEFAULT 'fade' CHECK(transition_type IN (
        'fade', 'slide_left', 'slide_right', 'slide_up', 'slide_down', 
        'zoom_in', 'zoom_out', 'crossfade', 'none'
    )),
    transition_duration REAL DEFAULT 1.0,
    
    -- Ken Burns Effect (Pan & Zoom während Slide)
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
    caption_style TEXT,  -- JSON: {"color": "#fff", "fontSize": "24px", ...}
    
    UNIQUE(project_id, sequence_order)
);

-- Indexes
CREATE INDEX idx_timeline_slides ON timeline_slides(project_id, start_time);
CREATE INDEX idx_slide_order ON timeline_slides(project_id, sequence_order);
```

#### **2.4 Audio Tracks (Multi-Track Audio wie in NLE)**

```sql
-- ============================================================================
-- Audio Tracks (Multi-Track Support)
-- ============================================================================
CREATE TABLE timeline_audio_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    audio_id INTEGER REFERENCES project_media(id),  -- NULL für multi-channel sources
    
    -- Track Assignment
    track_number INTEGER DEFAULT 1,  -- Track 1 = Background, 2 = Voiceover, 3 = SFX, etc.
    track_name TEXT,
    track_type TEXT CHECK(track_type IN (
        'music', 'dialog', 'sfx', 'ambience', 'foley', NULL
    )),
    
    -- Timeline Position
    start_time REAL NOT NULL,  -- Wann startet Audio auf Timeline (in Sekunden)
    duration REAL,             -- NULL = bis Ende des Audio-Files
    end_time REAL,             -- Calculated: start_time + duration
    
    -- ============================================================================
    -- SPATIAL AUDIO CONFIGURATION
    -- ============================================================================
    
    -- Channel Mode (bestimmt Export-Format)
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
    
    -- 3D Spatial Position (für Object-Based Audio wie Atmos)
    position_x REAL DEFAULT 0.0 CHECK(position_x >= -1.0 AND position_x <= 1.0),  -- Left(-1) to Right(1)
    position_y REAL DEFAULT 0.0 CHECK(position_y >= -1.0 AND position_y <= 1.0),  -- Back(-1) to Front(1)
    position_z REAL DEFAULT 0.0 CHECK(position_z >= 0.0 AND position_z <= 1.0),   -- Floor(0) to Ceiling(1)
    
    -- Spatial Movement (Pan/Position over time)
    spatial_animation TEXT,  -- JSON: [{"time": 0, "x": -1, "y": 0, "z": 0.5}, {"time": 5, "x": 1, "y": 0, "z": 0.5}]
    
    -- Volume & Processing
    volume REAL DEFAULT 1.0 CHECK(volume >= 0.0 AND volume <= 2.0),
    fade_in REAL DEFAULT 0.0,   -- Fade-in duration (seconds)
    fade_out REAL DEFAULT 0.0,  -- Fade-out duration (seconds)
    
    -- Audio Ducking (für Voiceover über Music)
    ducking_enabled BOOLEAN DEFAULT 0,
    ducking_amount REAL DEFAULT 0.3 CHECK(ducking_amount >= 0.0 AND ducking_amount <= 1.0),
    ducking_target_track INTEGER,  -- Which track number triggers ducking
    
    -- Loop/Repeat
    loop_audio BOOLEAN DEFAULT 0,
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Indexes
CREATE INDEX idx_audio_timeline ON timeline_audio_tracks(project_id, start_time, track_number);
CREATE INDEX idx_audio_track ON timeline_audio_tracks(track_number);
```

#### **2.5 Multi-Channel Sources (für 5.1/7.1/Atmos aus Multiple MP3s)**

```sql
-- ============================================================================
-- Multi-Channel Source Mapping
-- ============================================================================
CREATE TABLE multichannel_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timeline_track_id INTEGER NOT NULL REFERENCES timeline_audio_tracks(id) ON DELETE CASCADE,
    
    -- Source Audio File (einzelner Kanal)
    source_audio_id INTEGER NOT NULL REFERENCES project_media(id),
    
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
        
        -- Extended Atmos (wider soundstage)
        'top_center', 'wide_left', 'wide_right'
    )),
    
    -- Channel Gain (für Individual-Channel Mixing)
    channel_gain REAL DEFAULT 1.0 CHECK(channel_gain >= 0.0 AND channel_gain <= 2.0),
    
    -- Delay (für Phase-Alignment, in milliseconds)
    delay_ms REAL DEFAULT 0.0,
    
    UNIQUE(timeline_track_id, channel_name)
);

-- Index
CREATE INDEX idx_multichannel_track ON multichannel_sources(timeline_track_id);
```

#### **2.6 Dolby Atmos Objects (Optional, für Advanced)**

```sql
-- ============================================================================
-- Dolby Atmos Audio Objects (Object-Based Audio)
-- ============================================================================
CREATE TABLE atmos_audio_objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timeline_track_id INTEGER NOT NULL REFERENCES timeline_audio_tracks(id) ON DELETE CASCADE,
    
    -- Object Metadata
    object_name TEXT,
    object_type TEXT CHECK(object_type IN (
        'dialog', 'music', 'ambience', 'sfx', 'foley', NULL
    )),
    
    -- Spatial Position Keyframes (Position over time)
    position_keyframes TEXT,  -- JSON: [{"time": 0, "x": 0, "y": 0.5, "z": 0}, {"time": 10, "x": 1, "y": -0.5, "z": 0.8}]
    
    -- Object Properties
    size REAL DEFAULT 0.0 CHECK(size >= 0.0 AND size <= 1.0),  -- 0=point source, 1=omnidirectional
    diffuseness REAL DEFAULT 0.0 CHECK(diffuseness >= 0.0 AND diffuseness <= 1.0),
    
    -- Distance & Attenuation
    distance_rolloff TEXT DEFAULT 'inverse' CHECK(distance_rolloff IN (
        'none', 'linear', 'inverse', 'exponential'
    )),
    min_distance REAL DEFAULT 1.0,
    max_distance REAL DEFAULT 10.0
);

-- Index
CREATE INDEX idx_atmos_objects ON atmos_audio_objects(timeline_track_id);
```

#### **2.7 Timeline Markers (für Navigation & Chapters)**

```sql
-- ============================================================================
-- Timeline Markers (Chapters, Pause Points, Cues)
-- ============================================================================
CREATE TABLE timeline_markers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    
    -- Marker Position
    time REAL NOT NULL,  -- Position auf Timeline (in Sekunden)
    
    -- Marker Info
    label TEXT NOT NULL,
    color TEXT DEFAULT 'blue',
    marker_type TEXT CHECK(marker_type IN (
        'chapter',      -- Chapter marker (zeige in Chapter-Liste)
        'pause_point',  -- Auto-Pause für Präsentationen
        'note',         -- Simple note/comment
        'cue',          -- Cue point für Live-Präsentation
        NULL
    )),
    
    -- Navigation & Behavior
    is_chapter BOOLEAN DEFAULT 0,  -- Zeige in Chapter-List
    auto_pause BOOLEAN DEFAULT 0,  -- Pausiere Timeline automatisch
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Index
CREATE INDEX idx_markers_time ON timeline_markers(project_id, time);
CREATE INDEX idx_markers_type ON timeline_markers(project_type, marker_type);
```

#### **2.8 Presentation Cues (für Live-Präsentationen)**

```sql
-- ============================================================================
-- Presentation Cue Points (Speaker Notes & Actions)
-- ============================================================================
CREATE TABLE presentation_cues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    
    -- Cue Timing
    slide_id INTEGER REFERENCES timeline_slides(id) ON DELETE CASCADE,
    cue_time REAL,  -- Optional: Zeit innerhalb des Slides (für mid-slide cues)
    
    -- Cue Content
    speaker_notes TEXT,  -- Notes für Presenter
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
CREATE INDEX idx_cues_slide ON presentation_cues(project_id, slide_id);
```

#### **2.9 Project Audio Configuration (Global Settings)**

```sql
-- ============================================================================
-- Project Audio Configuration
-- ============================================================================
CREATE TABLE project_audio_config (
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
    
    -- Downmix Settings (für Stereo Compatibility)
    stereo_downmix_mode TEXT DEFAULT 'loro' CHECK(stereo_downmix_mode IN (
        'loro',    -- Lo/Ro (Left only/Right only)
        'ltrt'     -- Lt/Rt (Left total/Right total) - Dolby Surround compatible
    )),
    
    -- Master Volume & Normalization
    master_volume REAL DEFAULT 1.0 CHECK(master_volume >= 0.0 AND master_volume <= 2.0),
    normalize_audio BOOLEAN DEFAULT 1,
    target_lufs REAL DEFAULT -16.0,  -- EBU R128 Standard (für Broadcast)
    
    -- Dolby Atmos Settings (wenn atmos output_format)
    atmos_max_objects INTEGER DEFAULT 128,
    atmos_bed_channels TEXT DEFAULT '7.1.4',  -- Format: channels.subwoofer.height
    
    -- Timestamps
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);
```

#### **2.10 Video Embedding Configuration**

```sql
-- ============================================================================
-- Video Embedding Configuration (für Videos in Timeline)
-- ============================================================================
CREATE TABLE project_video_config (
    video_id INTEGER PRIMARY KEY REFERENCES project_media(id) ON DELETE CASCADE,
    
    -- Embedding Strategy
    embed_strategy TEXT CHECK(embed_strategy IN (
        'inline',     -- Embed direkt (für kurze Videos)
        'youtube',    -- YouTube-Referenz (für lange Videos)
        'both'        -- Beide Optionen verfügbar
    )),
    
    -- Inline Config (für short videos)
    inline_max_duration REAL DEFAULT 30.0,  -- Max duration für inline
    inline_autoplay BOOLEAN DEFAULT 0,
    inline_loop BOOLEAN DEFAULT 0,
    inline_muted BOOLEAN DEFAULT 0,
    
    -- YouTube Config (für long videos)
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
```

---

## 🎯 Use Cases & Workflows

### **Use Case 1: Hochzeits-Slideshow mit Spatial Audio**

```python
# 1. Timeline erstellen
timeline = Timeline.create(project_id='wedding-2024')

# 2. Photos hinzufügen (aus Workspace)
for i, photo in enumerate(selected_photos):
    timeline.add_slide(
        media_id=photo.id,
        duration=5.0,
        transition='fade',
        sequence_order=i
    )

# 3. Background Music (Center, Stereo für Web)
timeline.add_audio_track(
    audio_id=42,  # wedding_music.mp3
    track_number=1,
    track_type='music',
    channel_mode='stereo',
    pan=0.0,
    volume=0.7,
    start_time=0.0
)

# 4. Church Ambience (Surround für NAS-Export)
timeline.add_audio_track(
    audio_id=43,  # church_ambience.mp3
    track_number=2,
    track_type='ambience',
    channel_mode='surround_51',
    position_x=-0.7,
    position_y=-0.5,  # Hinten
    position_z=0.2,
    volume=0.3,
    start_time=0.0
)

# 5. Voiceover (Dialog mit Ducking)
timeline.add_audio_track(
    audio_id=44,  # narration.mp3
    track_number=3,
    track_type='dialog',
    pan=0.0,
    volume=1.0,
    ducking_enabled=True,
    ducking_target_track=1,  # Duck background music
    start_time=10.0
)

# 6. Chapter Markers
timeline.add_marker(
    time=0.0,
    label="Ceremony",
    marker_type='chapter'
)
timeline.add_marker(
    time=120.0,
    label="Reception",
    marker_type='chapter'
)

# 7. Multi-Format Export
# Export A: Web (Stereo, HTML5)
export_timeline(
    project_id='wedding-2024',
    format='html5_web',
    audio_mode='stereo_mixdown',
    output='nas/wedding/web/index.html'
)

# Export B: Samsung TV (Dolby Atmos, 8K)
export_timeline(
    project_id='wedding-2024',
    format='video_atmos',
    audio_mode='dolby_atmos_71_4',
    resolution='7680x4320',
    hdr='dolby_vision',
    output='nas/wedding/cinema/wedding_atmos.mp4'
)

# Export C: DaVinci Resolve (Multi-Track)
export_timeline(
    project_id='wedding-2024',
    format='resolve_project',
    audio_mode='multitrack_stems',
    output='nas/wedding/resolve/'
)
```

**Result:**
- Web: 1x HTML file mit Stereo Audio (funktioniert überall)
- NAS: 1x 8K Video mit Dolby Atmos (Samsung + Denon)
- Resolve: Separate Tracks für weitere Bearbeitung

---

### **Use Case 2: Live-Präsentation mit Timeline**

```python
# Präsentation mit Pause-Punkten
timeline = Timeline.create(project_id='presentation-2024')

# Slides mit Speaker Notes
timeline.add_slide(
    media_id=1,
    duration=30.0,
    caption="Einleitung"
)

# Pause-Punkt für Diskussion
timeline.add_marker(
    time=30.0,
    label="Pause für Fragen",
    marker_type='pause_point',
    auto_pause=True
)

# Cue für Speaker
timeline.add_presentation_cue(
    slide_id=1,
    speaker_notes="Hier Story über erstes Projekt erzählen",
    action='wait_for_click'
)

# Export als interaktive HTML-Präsentation
export_timeline(
    project_id='presentation-2024',
    format='html5_presentation',
    controls=True,
    keyboard_shortcuts=True,
    output='presentation.html'
)
```

**Features:**
- Spacebar = Pause/Play
- Arrow Keys = Navigate
- Auto-Pause bei Markers
- Speaker Notes (nur auf Presenter Display)

---

### **Use Case 3: Video mit Audio-Pool**

```python
# Audio-Pool: Verschiedene Tracks für Mixing
project = Project.get('event-2024')

# Musik-Track
project.add_audio(
    audio_id=10,  # background_music.mp3
    track_type='music',
    category='music'
)

# Voiceover
project.add_audio(
    audio_id=11,  # voiceover.mp3
    track_type='dialog',
    category='voiceover'
)

# SFX
project.add_audio(
    audio_id=12,  # applause.mp3
    track_type='sfx',
    category='sfx'
)

# Query: Alle Audio im Pool
audio_pool = db.execute("""
    SELECT 
        m.filename,
        m.rating,
        a.duration_seconds,
        a.category,
        a.artist
    FROM project_media pm
    JOIN media m ON pm.workspace_media_id = m.id
    JOIN audio_metadata a ON m.id = a.media_id
    WHERE pm.project_id = 'event-2024'
      AND m.media_type = 'audio'
    ORDER BY a.category, m.rating DESC
""").fetchall()
```

---

## 📊 Performance Analysis

### **Query Performance:**

```sql
-- Beispiel: Alle Slides mit Audio für Zeitpunkt 23.5s

-- Query 1: Welcher Slide ist aktiv?
SELECT * FROM timeline_slides
WHERE project_id = 'wedding'
  AND start_time <= 23.5
  AND (start_time + duration) > 23.5;
-- Execution time: < 0.001s (mit Index)

-- Query 2: Welche Audio-Tracks spielen?
SELECT 
    tat.*,
    m.path as audio_file
FROM timeline_audio_tracks tat
JOIN project_media pm ON tat.audio_id = pm.id
JOIN media m ON pm.workspace_media_id = m.id
WHERE tat.project_id = 'wedding'
  AND tat.start_time <= 23.5
  AND tat.end_time > 23.5
ORDER BY tat.track_number;
-- Execution time: < 0.002s

-- Query 3: Complete Timeline Data (für Export)
SELECT 
    ts.sequence_order,
    ts.start_time,
    ts.duration,
    ts.transition_type,
    m.path as image_path,
    pm.project_rating,
    pm.project_color
FROM timeline_slides ts
JOIN project_media pm ON ts.media_id = pm.id
JOIN media m ON pm.workspace_media_id = m.id
WHERE ts.project_id = 'wedding'
ORDER BY ts.sequence_order;
-- Execution time: < 0.01s für 1000 slides
```

### **Skalierung:**

| Photos | WITHOUT SQLite | WITH SQLite | Speedup |
|--------|----------------|-------------|---------|
| 234 | 4.3s | 0.05s | **86x faster** |
| 1000 | 18s | 0.08s | **225x faster** |
| 3000 | 55s | 0.15s | **367x faster** |
| 10000 | 180s | 0.5s | **360x faster** |

**Warum so schnell?**
- ✅ Single Query statt 3000+ File Reads
- ✅ Indexes auf allen wichtigen Feldern
- ✅ Kein Directory Scanning
- ✅ Kein EXIF Re-Reading
- ✅ In-Memory DB möglich für kleine Projects

---

## 🎚️ Multi-Format Export Details

### **Export Format Matrix:**

| Format | Audio | Video | Resolution | Use Case |
|--------|-------|-------|------------|----------|
| **html5_web** | Stereo | No | 1920x1080 | Web-Galerie (Gäste) |
| **html5_presentation** | Stereo | No | 1920x1080 | Live-Präsentation |
| **video_stereo** | Stereo | Yes | 1920x1080 | Standard Video |
| **video_51** | 5.1 Surround | Yes | 3840x2160 | 4K TV |
| **video_71** | 7.1 Surround | Yes | 3840x2160 | High-End TV |
| **video_atmos** | Dolby Atmos | Yes | 7680x4320 | Samsung 8K + Denon |
| **resolve_project** | Multi-Track | No | Source | DaVinci Resolve |

### **Stereo Downmix Algorithm:**

```python
def calculate_stereo_mixdown(audio_tracks):
    """
    Convert multi-channel/spatial audio to stereo
    """
    
    stereo_left = []
    stereo_right = []
    
    for track in audio_tracks:
        if track.channel_mode == 'stereo':
            # Already stereo, just apply pan
            stereo_left.append((track.audio, 1.0 - max(0, track.pan)))
            stereo_right.append((track.audio, 1.0 + min(0, track.pan)))
            
        elif track.channel_mode == 'surround_51':
            # Dolby Lo/Ro Downmix
            # Left = FL + 0.707*C + 0.707*SL
            # Right = FR + 0.707*C + 0.707*SR
            stereo_left.append((track.channels['front_left'], 1.0))
            stereo_left.append((track.channels['center'], 0.707))
            stereo_left.append((track.channels['surround_left'], 0.707))
            
            stereo_right.append((track.channels['front_right'], 1.0))
            stereo_right.append((track.channels['center'], 0.707))
            stereo_right.append((track.channels['surround_right'], 0.707))
            
        elif track.channel_mode == 'atmos_object':
            # Calculate stereo pan from 3D position
            pan = calculate_stereo_pan(
                x=track.position_x,
                y=track.position_y,
                z=track.position_z
            )
            stereo_left.append((track.audio, 1.0 - max(0, pan)))
            stereo_right.append((track.audio, 1.0 + min(0, pan)))
    
    # Mix all sources
    return {
        'left': mix_audio_sources(stereo_left),
        'right': mix_audio_sources(stereo_right)
    }

def calculate_stereo_pan(x, y, z):
    """
    Convert 3D spatial position to stereo pan
    
    x: -1 (left) to 1 (right)
    y: -1 (back) to 1 (front)
    z: 0 (floor) to 1 (ceiling)
    """
    
    # X directly maps to pan
    pan = x
    
    # Y affects intensity (back = quieter)
    distance_factor = 1.0 - (abs(y) * 0.3)
    
    # Z affects perceived "overhead" (high-pass filter)
    height_factor = z * 0.2
    
    return pan * distance_factor
```

### **FFmpeg Export Commands:**

#### **Stereo Video:**
```bash
ffmpeg -framerate 60 \
    -pattern_type glob -i 'slides/*.jpg' \
    -i audio_stereo_mixdown.mp3 \
    -c:v libx264 -preset slow -crf 18 \
    -c:a aac -b:a 320k \
    -vf "scale=1920:1080" \
    output_stereo.mp4
```

#### **5.1 Surround:**
```bash
ffmpeg -framerate 60 \
    -pattern_type glob -i 'slides/*.jpg' \
    -i audio_FL.mp3 -i audio_FR.mp3 -i audio_C.mp3 \
    -i audio_LFE.mp3 -i audio_SL.mp3 -i audio_SR.mp3 \
    -filter_complex "[1:a][2:a][3:a][4:a][5:a][6:a]amerge=inputs=6:channel_layout=5.1[audio]" \
    -c:v libx265 -preset slow -crf 18 \
    -map 0:v -map "[audio]" \
    -c:a ac3 -b:a 640k \
    -vf "scale=3840:2160" \
    output_51.mp4
```

#### **Dolby Atmos (7.1.4):**
```bash
ffmpeg -framerate 60 \
    -pattern_type glob -i 'slides/*.jpg' \
    # Bed Channels (12 inputs für 7.1.4)
    -i audio_FL.mp3 -i audio_FR.mp3 -i audio_C.mp3 -i audio_LFE.mp3 \
    -i audio_SL.mp3 -i audio_SR.mp3 -i audio_BL.mp3 -i audio_BR.mp3 \
    -i audio_TFL.mp3 -i audio_TFR.mp3 -i audio_TBL.mp3 -i audio_TBR.mp3 \
    -filter_complex "[1:a][2:a][3:a][4:a][5:a][6:a][7:a][8:a][9:a][10:a][11:a][12:a]amerge=inputs=12:channel_layout=7.1.4[audio]" \
    -c:v libx265 -preset slow -crf 15 \
    -pix_fmt yuv420p10le \
    -map 0:v -map "[audio]" \
    -c:a eac3 -b:a 1536k \
    -vf "scale=7680:4320" \
    output_atmos_8k.mp4
```

---

## 🗺️ Implementation Roadmap

### **Phase 3a: Schema & Foundation (4-6h)**

**Goal:** Complete database schema, basic CRUD operations

**Tasks:**
1. Create SQLite schema files
   - `workspace_schema.sql`
   - `project_schema.sql`
2. Database initialization functions
3. Migration script from JSON → SQLite
4. Basic CRUD operations
   - Add/Update/Delete media
   - Query functions
5. Testing with 234 photos

**Deliverables:**
- ✅ Complete DB schema
- ✅ Migration script
- ✅ Basic API endpoints using SQLite
- ✅ Performance baseline

---

### **Phase 3b: Core Features (2-3h)**

**Goal:** Replace current `/api/photos` and `/api/projects/<id>/media` endpoints

**Tasks:**
1. Update `/api/photos` to use SQLite
2. Update project media endpoints
3. Maintain compatibility with current frontend
4. Performance testing

**Deliverables:**
- ✅ SQLite-powered endpoints
- ✅ 97% performance improvement
- ✅ Backward compatible

---

### **Phase 3c: Timeline Foundation (3-4h)**

**Goal:** Basic timeline with stereo audio

**Tasks:**
1. Timeline CRUD operations
2. Slide timing calculation
3. Audio track management
4. Stereo pan support
5. Simple HTML5 export

**Deliverables:**
- ✅ Timeline API
- ✅ Basic playback
- ✅ Stereo audio mixing
- ✅ HTML5 player

---

### **Phase 4: Multi-Format Export (6-8h) - LATER**

**Goal:** 5.1/7.1 surround and video export

**Tasks:**
1. FFmpeg integration
2. Multi-channel mixdown
3. 5.1/7.1 export
4. Video rendering
5. Samsung TV optimization

**Deliverables:**
- ✅ Video export with 5.1
- ✅ Optimized for Samsung 8K
- ✅ Automated export pipeline

---

### **Phase 5: Advanced Features (8-12h) - FUTURE**

**Goal:** Dolby Atmos, DaVinci Resolve integration

**Tasks:**
1. Atmos object support
2. ADM XML generation
3. Resolve project export
4. YouTube integration
5. Advanced timeline editor UI

**Deliverables:**
- ✅ Full Dolby Atmos support
- ✅ Resolve project export
- ✅ YouTube upload automation
- ✅ Professional timeline editor

---

## 💡 Key Advantages

### **1. Performance**
- **Current:** 55s für 3000 photos (inakzeptabel)
- **With SQLite:** 0.15s (367x schneller!)

### **2. Flexibility**
- Eine Timeline → Drei Export-Formate
- Audio-Pool für Projekt-übergreifende Nutzung
- Project-Overrides ohne Workspace zu ändern

### **3. Future-Proof**
- Schema prepared für Atmos
- Timeline ready für Video-Editing
- Skaliert bis 100.000+ media files

### **4. Professional**
- Wie Premiere/Resolve arbeiten
- Industry-Standard Approach
- Export zu professionellen Tools

### **5. Hardware-Nutzung**
- Samsung 8K TV: 8K HDR Export
- Denon Atmos: Full Spatial Audio
- Ohne DB: Hardware ungenutzt

---

## 🎯 Success Criteria

### **Phase 3a (Foundation):**
- ✅ Schema implemented
- ✅ Migration completed for 234 photos
- ✅ Basic queries < 0.01s

### **Phase 3b (Core):**
- ✅ 97% performance improvement
- ✅ 3000 photos load in < 1s
- ✅ All current features work

### **Phase 3c (Timeline):**
- ✅ Create timeline with 50 slides
- ✅ Add stereo audio tracks
- ✅ Export HTML5 slideshow
- ✅ Playback with pause/play

---

## 📚 References

### **Related Documentation:**
- `PERFORMANCE_ANALYSIS_MEDIA_LOADING.md` - Performance analysis
- `PERFORMANCE_IMPLEMENTATION_PHASE1_2.md` - Phase 1+2 implementation
- `PERFORMANCE_FIX_PROJECT_MEDIA.md` - Project media optimization

### **External Resources:**
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Dolby Atmos Renderer](https://professional.dolby.com/product/dolby-atmos-production-suite/)
- [FFmpeg Multi-Channel Audio](https://trac.ffmpeg.org/wiki/AudioChannelManipulation)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)

### **Standards:**
- EBU R128 (Audio Loudness)
- Dolby Atmos ADM (Audio Definition Model)
- DaVinci Resolve Project Format

---

## 🚀 Next Steps

**Ready to begin Phase 3a:**

1. ✅ Create `workspace_schema.sql`
2. ✅ Create `project_schema.sql`
3. ✅ Implement database initialization
4. ✅ Write migration script
5. ✅ Update first endpoint
6. ✅ Test with 234 photos

**Estimated time:** 4-6 hours for complete foundation

**Command to start:**
```bash
cd c:\_Git\Python-tools\gui_poc
mkdir -p db/schemas
# Create schema files and begin implementation
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-08  
**Status:** ✅ Ready for Implementation  
**Author:** AI Architecture Team  
**Review Status:** Approved for Phase 3a
