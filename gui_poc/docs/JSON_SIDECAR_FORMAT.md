# JSON Sidecar Format Documentation

**Version:** 2.0 (Burst Format Updated)  
**Date:** 2026-02-08  
**Status:** Reference Implementation

## ⚠️ CRITICAL: Before Changing This Specification

**This document is the single source of truth for JSON sidecar format.**

Before making ANY changes to this specification:

1. 📋 **Check [SOFTWARE_REGISTRY.md](./SOFTWARE_REGISTRY.md)** to see which components will be affected
2. 💬 **Discuss the change** with the team (breaking changes require approval)
3. 📝 **Document the change** in this file (mark as "Proposed" first)
4. 🔧 **Update all registered components** (see registry for list)
5. ✅ **Test end-to-end** (analysis → migration → database → API → frontend)
6. 📦 **Commit all changes together** (atomic deployment)

**Components that depend on this spec:**
- `photo_tool/prescan/analyzers/burst.py` (write)
- `photo_tool/prescan/analyzers/blur.py` (write)
- `gui_poc/static/app.js` (write user metadata)
- `gui_poc/migration.py` (read)
- `gui_poc/db_manager.py` (read & transform)
- `gui_poc/server.py` (indirect read via database)

---

## ⚠️ IMPORTANT: Format Versioning

This documentation describes **two versions** of the JSON sidecar format:

1. **Version 1 (Current):** Written by existing analysis tools (`photo_tool/prescan/analyzers/`)
   - Used in production since 2026-02-06
   - Contains detailed analysis data (e.g., `burst_neighbors` with objects)
   - Some fields use different names (e.g., `computed_at` instead of `detection_date`)

2. **Version 2 (Planned):** Idealized format for future implementations
   - Simplified structure
   - Consistent field naming
   - Better for manual editing

**The migration system (`db_manager.py`) supports BOTH versions** to ensure compatibility with existing `.phototool.json` files.

---

## Overview

The photo tool uses **JSON sidecar files** as the **source of truth** for all media metadata. These files are portable, human-readable, and version-control friendly.

## File Naming Convention

There are THREE types of JSON sidecar files, each with a specific purpose:

### 1. User Metadata: `.{stem}.metadata.json` (PRIMARY)

**Purpose:** User-edited metadata (rating, color, keywords, comment)  
**Location:** Same folder as media file  
**Visibility:** Hidden file (starts with dot)  
**Example:** For `P1012337.JPG` → `.P1012337.metadata.json`

```json
{
  "rating": 3,
  "color": "red",
  "keywords": ["wedding", "bride", "outdoor"],
  "comment": "Beautiful sunset shot",
  "gps": {
    "latitude": 47.3769,
    "longitude": 8.5417,
    "altitude": 408
  },
  "updated": "2026-02-08T15:30:45.123456"
}
```

### 2. Analysis Data: `.{filename}.phototool.json` (ANALYSIS)

**Purpose:** Computed analysis results (blur, burst, faces, etc.)  
**Location:** Same folder as media file  
**Visibility:** Hidden file (starts with dot)  
**Example:** For `P1012337.JPG` → `.P1012337.JPG.phototool.json`

**Complete File Structure:**

```json
{
  "version": "1.0",
  "photo": {
    "path": "E:\\Photos\\P1012337.JPG",
    "name": "P1012337.JPG",
    "size_bytes": 2849280,
    "modified_at": "2025-11-24T20:11:00"
  },
  "scan_info": {
    "scanned_at": "2026-02-08T20:38:45.061980",
    "scanner_version": "1.0.0",
    "updated_at": "2026-02-08T20:38:53.861446"
  },
  "analyses": {
    "blur": {
      "laplacian": {
        "score": 45.67,
        "computed_at": "2026-02-08T15:30:45.123456",
        "method_version": "1.0"
      },
      "tenengrad": {
        "score": 123.45,
        "computed_at": "2026-02-08T15:30:46.234567",
        "method_version": "1.0"
      },
      "roi": {
        "score": 67.89,
        "computed_at": "2026-02-08T15:30:47.345678",
        "method_version": "1.0"
      },
      "computed_at": "2026-02-08T15:30:47.345678"
    },
    "burst": {
      "is_burst_candidate": true,
      "burst_id": "a4720613550b",
      "neighbors": [
        "E:\\Photos\\P1012336.JPG",
        "E:\\Photos\\P1012338.JPG"
      ],
      "score": 0.92,
      "detection_date": 1739024645
    },
    "faces": {
      "face_count": 2,
      "faces": [
        {
          "x": 0.3,
          "y": 0.4,
          "width": 0.15,
          "height": 0.2,
          "confidence": 0.98
        }
      ],
      "detection_date": 1739024645
    }
  }
}
```

**Top-Level Fields:**

#### `version` (String)
Schema version of the .phototool.json file format.
- **Type:** String
- **Current Version:** "1.0"
- **Usage:** Future schema migrations

#### `photo` (Object)
Basic photo file information (cached for performance).
- **Fields:**
  - `path` (String): Absolute path to photo
  - `name` (String): Filename only
  - `size_bytes` (Integer): File size in bytes
  - `modified_at` (String, ISO 8601): File modification timestamp

#### `scan_info` (Object)
Information about when and how the photo was scanned.
- **Fields:**
  - `scanned_at` (String, ISO 8601): When photo was first scanned
  - `scanner_version` (String): Version of scanner that created this file
  - `updated_at` (String, ISO 8601): Last update timestamp

#### `analyses` (Object)
Container for all analysis results. Each analysis type is a key in this object.
- **Keys:** `blur`, `burst`, `faces`, `landscape`, `night`, etc.
- **See below for detailed field specifications**

---

**Detailed Analysis Specifications:**

### 3. Legacy Format: `.metadata.json` (NON-HIDDEN)

**Purpose:** Older non-hidden metadata format  
**Location:** Same folder as media file  
**Visibility:** Visible file  
**Example:** For `P1012337.JPG` → `P1012337.metadata.json`

**NOTE:** This format is deprecated in favor of the hidden `.{stem}.metadata.json` format.

---

## Field Specifications

### User Metadata Fields

#### `rating` (Integer, 0-5)
User's quality rating of the photo.
- **Type:** Integer
- **Range:** 0 (unrated) to 5 (best)
- **Default:** 0
- **Usage:** Filtering, sorting, export selection

#### `color` (String, enum)
Color label for organization.
- **Type:** String or `null`
- **Values:** `"red"`, `"yellow"`, `"green"`, `"blue"`, `"purple"`, `null`
- **Default:** `null`
- **Usage:** Visual organization, quick filtering

#### `keywords` (Array of Strings)
User-defined tags for searching and organization.
- **Type:** Array of strings
- **Default:** `[]`
- **Example:** `["wedding", "outdoor", "portrait"]`
- **Usage:** Search, filtering, export

#### `comment` (String)
User's free-text note about the photo.
- **Type:** String or `null`
- **Default:** `null`
- **Usage:** Documentation, context

#### `gps` (Object)
GPS location data (if available).
- **Type:** Object or `null`
- **Fields:**
  - `latitude` (Float): Latitude in decimal degrees
  - `longitude` (Float): Longitude in decimal degrees
  - `altitude` (Float, optional): Altitude in meters
- **Default:** `null`
- **Source:** EXIF data or manual entry

#### `updated` (String, ISO 8601)
Timestamp of last metadata update.
- **Type:** String (ISO 8601 format)
- **Example:** `"2026-02-08T15:30:45.123456"`
- **Auto-generated:** Yes

---

### Analysis Data Fields

#### `blur` (Object)
Blur/sharpness detection results.

**Structure:**
```json
{
  "laplacian": {
    "score": 45.67,
    "threshold": 50.0,
    "is_sharp": false
  },
  "tenengrad": {
    "score": 123.45,
    "threshold": 100.0,
    "is_sharp": true
  },
  "roi": {
    "score": 67.89,
    "threshold": 60.0,
    "is_sharp": true
  },
  "detection_date": 1739024645
}
```

**Fields:**
- `laplacian.score` (Float): Variance of Laplacian (higher = sharper)
- `laplacian.threshold` (Float): Threshold for sharpness detection
- `laplacian.is_sharp` (Boolean): Whether image is sharp by this metric
- `tenengrad.score` (Float): Tenengrad variance
- `tenengrad.threshold` (Float): Threshold
- `tenengrad.is_sharp` (Boolean): Sharpness by Tenengrad
- `roi.score` (Float): Region-of-interest blur score
- `roi.threshold` (Float): ROI threshold
- `roi.is_sharp` (Boolean): ROI sharpness
- `detection_date` (Integer): Unix timestamp

**Thresholds:**
- Laplacian: < 50 = blurry, 50-100 = moderate, > 100 = sharp
- Tenengrad: < 100 = blurry, 100-200 = moderate, > 200 = sharp
- ROI: < 60 = blurry, 60-120 = moderate, > 120 = sharp

#### `burst` (Object)
Burst photo detection and grouping.

**Current Format (Version 2):**

The burst analyzer (`photo_tool/prescan/analyzers/burst.py`) writes the following format:

```json
{
  "is_burst_candidate": true,
  "burst_id": "a4720613550b",
  "neighbors": [
    "E:\\Photos\\P1012336.JPG",
    "E:\\Photos\\P1012338.JPG"
  ],
  "score": 0.92,
  "detection_date": 1739024645
}
```

**Fields:**
- `is_burst_candidate` (Boolean): Whether photo is part of a burst
- `burst_id` (String): Unique ID for the burst group (12 chars, hex hash)
- `neighbors` (Array of Strings): Full paths to neighboring burst photos
- `score` (Float, 0-1): Average similarity score with neighbors
- `detection_date` (Integer): Unix timestamp when burst was detected

**Generation Process:**
1. **Burst detection:** Scan all photos in a folder, identify candidates (time < 3s, similarity > 0.85)
2. **Graph clustering:** Group mutually-linked photos into burst groups using graph DFS
3. **Assign `burst_id`:** Generate consistent 12-char hex ID for each burst group
4. **Write to sidecar:** Save burst data including all neighbor paths

**Burst Detection Criteria:**
- Time threshold: Photos within 3 seconds
- Similarity threshold: Visual similarity > 0.85 (histogram correlation)
- Grouping: All photos with same `burst_id` belong to same burst

**Burst Leader Selection (for UI display):**

The frontend displays burst groups as **collapsed containers** with a single "leader" photo shown. The leader selection happens in the API layer (`server.py`) during data loading:

1. **Group photos by `burst_id`:** All photos sharing the same `burst_id` are grouped together
2. **Select one leader per group:** The first photo alphabetically (by filename) becomes the leader
3. **Mark as `is_burst_lead: true`:** Only the leader gets this flag set to `true`
4. **Set `burst_count`:** Only the leader shows the count (total photos in burst)
5. **Non-leaders hidden:** Photos with `is_burst_lead: false` are hidden from the main grid (shown only when burst is expanded)

**Example:**
- Burst group with `burst_id = "a4720613550b"`:
  - `P1012336.JPG` → `is_burst_lead: true`, `burst_count: 3` (shown in grid)
  - `P1012337.JPG` → `is_burst_lead: false`, `burst_count: 0` (hidden until expanded)
  - `P1012338.JPG` → `is_burst_lead: false`, `burst_count: 0` (hidden until expanded)

This ensures that:
- **95 photos in bursts** with **30 unique burst groups** → Display **30 containers** (not 95!)
- Clicking a container expands it to show all photos in that burst
- Users see a clean, organized grid without duplicates

#### `faces` (Object)
Face detection results.

**Structure:**
```json
{
  "face_count": 2,
  "faces": [
    {
      "x": 0.3,
      "y": 0.4,
      "width": 0.15,
      "height": 0.2,
      "confidence": 0.98
    }
  ],
  "detection_date": 1739024645
}
```

**Fields:**
- `face_count` (Integer): Number of faces detected
- `faces` (Array): Array of face objects
  - `x`, `y` (Float, 0-1): Normalized coordinates (0=left/top, 1=right/bottom)
  - `width`, `height` (Float, 0-1): Normalized dimensions
  - `confidence` (Float, 0-1): Detection confidence
- `detection_date` (Integer): Unix timestamp

#### `landscape` (Object)
Landscape photo detection.

**Structure:**
```json
{
  "is_landscape": true,
  "confidence": 0.87,
  "horizon_angle": -2.3,
  "detection_date": 1739024645
}
```

**Fields:**
- `is_landscape` (Boolean): Whether photo is a landscape
- `confidence` (Float, 0-1): Detection confidence
- `horizon_angle` (Float): Horizon line angle in degrees (-90 to +90)
- `detection_date` (Integer): Unix timestamp

#### `night` (Object)
Night/low-light detection.

**Structure:**
```json
{
  "is_night_photo": false,
  "confidence": 0.12,
  "detection_date": 1739024645
}
```

**Fields:**
- `is_night_photo` (Boolean): Whether photo is a night shot
- `confidence` (Float, 0-1): Detection confidence
- `detection_date` (Integer): Unix timestamp

---

## File Management

### Creation
- **User metadata:** Created/updated when user edits rating, color, keywords, or comment
- **Analysis data:** Created by pre-scan analyzers (blur, burst, faces, etc.)

### Portability
- JSON sidecars travel with media files when moved/copied
- Hidden files (starting with `.`) may need special handling on Windows
- Use `attrib -h` to unhide if needed for debugging

### Sync Behavior
- JSON files are the **source of truth**
- SQLite database caches data from JSON for performance
- On conflict: JSON wins
- Changes to user metadata: Write to JSON first, then sync to SQLite
- Changes to analysis data: Write to JSON, invalidate SQLite cache

### Backup
- JSON sidecars should be included in backups
- Small file size (typically < 5KB per file)
- Can be version-controlled (Git-friendly)

---

## Migration Notes

### Current Status
The analyzed folder (`E:\Lumix-2026-01\101_PANA`) has:
- ✅ User metadata files: `.{stem}.metadata.json` (rating, color, keywords)
- ❌ Analysis files: `.{filename}.phototool.json` files **do not exist yet**

### Why No Analysis Files?
Burst detection and other analyses have not been run on this folder yet. To generate these files, run:

```bash
python photo_tool/prescan/main.py --input "E:\Lumix-2026-01\101_PANA" --analyses blur,burst,faces
```

### Database Behavior Without Analysis Files
- User metadata (rating, color) loads correctly from `.{stem}.metadata.json`
- Analysis data (blur, burst) is `NULL` in database
- No fake "burst leaders" are created (fixed in server logic)

---

## Best Practices

1. **Always write to JSON first** before updating SQLite
2. **Use hidden files** (`.{stem}.metadata.json`) for user metadata
3. **Separate concerns:** User data vs. analysis data in different files
4. **Include timestamps** for sync conflict resolution
5. **Validate JSON** before writing to prevent corruption
6. **Atomic writes:** Write to temp file, then rename
7. **Error handling:** Graceful fallback if JSON is missing/corrupt

---

## Future Enhancements

### Phase 4 Features (Future-Ready)
The following fields are planned for future `.phototool.json` files:

#### RAW + JPEG Tandem
```json
{
  "tandem": {
    "has_tandem": true,
    "raw_path": "P1012337.RW2",
    "jpeg_path": "P1012337.JPG",
    "primary": "raw",
    "export_from": "auto"
  }
}
```

#### Non-Destructive Edits
```json
{
  "edits": {
    "has_edits": true,
    "version": "1.0",
    "stack": [
      {
        "operation": "exposure",
        "params": {"value": +0.5},
        "enabled": true
      },
      {
        "operation": "saturation",
        "params": {"value": 1.2},
        "enabled": true
      }
    ],
    "updated_at": 1739024645,
    "applied_by": "user"
  }
}
```

#### Render Cache
```json
{
  "cache": {
    "thumbnail_path": ".cache/P1012337_thumb.jpg",
    "preview_path": ".cache/P1012337_preview.jpg",
    "fullres_path": ".cache/P1012337_fullres.jpg",
    "cache_date": 1739024645,
    "invalidated": false
  }
}
```

---

## See Also

- `DATABASE_ARCHITECTURE.md` - SQLite schema and sync behavior
- `SYNC_STRATEGY.md` - JSON ↔ SQLite synchronization
- `PHASE3_SQLITE_ARCHITECTURE.md` - Overall system design
