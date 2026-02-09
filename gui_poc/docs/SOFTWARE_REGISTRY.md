# Software Component Registry

**Purpose:** Track all software components that depend on the JSON Sidecar Format specification

**Last Updated:** 2026-02-08

---

## Why This Registry Exists

When the JSON sidecar format changes (new fields, renamed fields, changed data types), **all registered components must be updated** to maintain consistency and prevent bugs.

This registry ensures:
1. ✅ **No component is forgotten** during spec changes
2. ✅ **Breaking changes are identified** before deployment
3. ✅ **Version compatibility** is tracked
4. ✅ **Testing coverage** includes all components

---

## Change Management Process

### When Changing the JSON Sidecar Format:

1. **Propose Change**
   - Document in `JSON_SIDECAR_FORMAT.md`
   - Mark as "Draft" or "Proposed"
   - Include rationale and examples

2. **Impact Analysis**
   - Review this registry
   - Check which components are affected
   - Estimate effort for each component

3. **Update Components**
   - Update all "write" components first (they produce JSON)
   - Update all "read" components second (they consume JSON)
   - Update all "transform" components last

4. **Test & Verify**
   - Run integration tests
   - Verify data flows end-to-end
   - Check backward compatibility if needed

5. **Deploy**
   - Update documentation (mark as "Stable")
   - Update this registry with new version numbers
   - Commit all changes together

---

## Registered Components

### 1. Photo Analysis Tools (WRITE)

Components that **write** JSON sidecar files (`.phototool.json`)

#### 1.1 Blur Analyzer
- **Location:** `photo_tool/prescan/analyzers/blur.py`
- **Format Version:** 1.0
- **Writes:** `.{filename}.phototool.json` → `analyses.blur`
- **Fields Written:**
  - `laplacian.score` (Float)
  - `laplacian.computed_at` (ISO 8601 string)
  - `laplacian.method_version` (String)
  - `tenengrad.score` (Float)
  - `tenengrad.computed_at` (ISO 8601 string)
  - `tenengrad.method_version` (String)
  - `roi.score` (Float)
  - `roi.computed_at` (ISO 8601 string)
  - `roi.method_version` (String)
  - `computed_at` (ISO 8601 string)
- **Spec Compliance:** ⚠️ **Partial**
  - ❌ Missing `threshold` fields (uses hardcoded thresholds internally)
  - ❌ Uses `computed_at` instead of `detection_date`
- **Migration Support:** `db_manager.py` uses defaults for missing thresholds
- **Status:** ✅ Active, In Use
- **Last Updated:** 2026-02-06

#### 1.2 Burst Analyzer
- **Location:** `photo_tool/prescan/analyzers/burst.py`
- **Format Version:** 2.0 (**Updated 2026-02-08**)
- **Writes:** `.{filename}.phototool.json` → `analyses.burst`
- **Fields Written:**
  - `is_burst_candidate` (Boolean)
  - `burst_id` (String, 12 chars hex)
  - `neighbors` (Array of Strings)
  - `score` (Float, 0-1)
  - `detection_date` (Integer, Unix timestamp)
- **Spec Compliance:** ✅ **Full** (Version 2 format)
- **Migration Support:** Fully compatible with `db_manager.py`
- **Status:** ✅ Active, **Recently Updated**
- **Last Updated:** 2026-02-08
- **Breaking Change:** Yes (from Version 1 → Version 2)
  - Old: `burst_neighbors` (array of objects) + `computed_at`
  - New: `neighbors` (array of strings) + `detection_date`
- **⚠️ CRITICAL:** Burst analysis requires scanning ALL photos in a folder together. Never use `skip_existing=True` with burst analyzer, as this will create incomplete burst groups!

---

### 2. User Metadata Tools (WRITE)

Components that **write** user metadata files (`.{stem}.metadata.json`)

#### 2.1 GUI Frontend (Vue.js)
- **Location:** `gui_poc/static/app.js`
- **Format Version:** 1.0
- **Writes:** `.{stem}.metadata.json`
- **Fields Written:**
  - `rating` (Integer, 0-5)
  - `color` (String or null)
  - `keywords` (Array of Strings)
  - `comment` (String or null)
  - `updated` (ISO 8601 string)
- **Spec Compliance:** ✅ **Full**
- **Migration Support:** Fully compatible with `db_manager.py`
- **Status:** ✅ Active, In Use
- **Last Updated:** 2026-01-15

---

### 3. Data Migration (READ & WRITE)

Components that **read** JSON sidecars and **write** to database

#### 3.1 Migration Manager
- **Location:** `gui_poc/migration.py`
- **Format Version:** 1.0 + 2.0 (supports both)
- **Reads:** 
  - `.{stem}.metadata.json` (user metadata)
  - `.{filename}.phototool.json` (analysis data)
- **Writes To:** `workspace_media.db` (SQLite)
- **Spec Compliance:** ✅ **Full**
  - Supports Version 2 burst format (simplified neighbors array)
  - Handles missing fields gracefully (uses defaults)
- **Status:** ✅ Active, In Use
- **Last Updated:** 2026-02-09

#### 3.2 Database Manager
- **Location:** `gui_poc/db_manager.py`
- **Format Version:** 1.0 + 2.0 (supports both)
- **Reads:** JSON sidecar data (via `migration.py`)
- **Writes To:** SQLite database tables
- **Spec Compliance:** ✅ **Full**
  - Handles both `burst_neighbors` and `neighbors` field names
  - Extracts paths from objects if needed
  - Generates `burst_id` if missing
  - Supports both `computed_at` and `detection_date`
- **Status:** ✅ Active, In Use
- **Last Updated:** 2026-02-08

---

### 4. API Server (READ)

Components that **read** from database and serve to frontend

#### 4.1 Flask API Server
- **Location:** `gui_poc/server.py`
- **Format Version:** N/A (reads from SQLite, not JSON)
- **Reads From:** `workspace_media.db` (SQLite)
- **Serves To:** Frontend (JSON API)
- **API Endpoints:**
  - `GET /api/projects/<id>/media` - Load media for project
  - `PUT /api/projects/<id>/media/<media_id>` - Update metadata
- **Spec Compliance:** ✅ **Full**
  - Correctly checks for `burst_id` AND `burst_neighbors` before setting `is_burst_lead`
  - Parses `burst_neighbors` from JSON string
- **Status:** ✅ Active, In Use
- **Last Updated:** 2026-02-08

---

### 5. Frontend Display (READ)

Components that **read** from API and display to user

#### 5.1 Vue.js Frontend
- **Location:** `gui_poc/static/app.js`, `gui_poc/static/index.html`
- **Format Version:** N/A (consumes API, not JSON files)
- **Reads From:** Flask API (JSON HTTP responses)
- **Displays:** 
  - Photo thumbnails with metadata overlays
  - Burst containers with grouping
  - Filters (rating, color, burst, blur)
- **Spec Compliance:** ✅ **Full**
  - Expects `is_burst_lead`, `burst_id`, `burst_count`, `burst_neighbors`
  - Handles missing burst data gracefully
- **Status:** ✅ Active, In Use
- **Last Updated:** 2026-02-08

---

## Component Dependency Graph

```
User Edits        Photo Analysis
    ↓                  ↓
.metadata.json    .phototool.json
    ↓                  ↓
    └──────┬───────────┘
           ↓
    migration.py (READ)
           ↓
    db_manager.py (TRANSFORM & WRITE)
           ↓
    workspace_media.db (SQLite)
           ↓
    server.py (READ & SERVE)
           ↓
    app.js (READ & DISPLAY)
           ↓
         User
```

---

## Format Version Matrix

| Component | JSON Format | Burst Format | Status |
|-----------|-------------|--------------|--------|
| `blur.py` | 1.0 | N/A | ⚠️ Partial (missing thresholds) |
| `burst.py` | 2.0 | Version 2 | ✅ Full |
| `app.js` (write) | 1.0 | N/A | ✅ Full |
| `migration.py` | 1.0 + 2.0 | Both | ✅ Full (backward compatible) |
| `db_manager.py` | 1.0 + 2.0 | Both | ✅ Full (backward compatible) |
| `server.py` | N/A | N/A | ✅ Full |
| `app.js` (read) | N/A | N/A | ✅ Full |

---

## Planned Changes

### Short Term (Next Sprint)

**None currently planned.**

### Long Term (Future)

1. **Blur Analyzer Update**
   - Add `threshold` fields to output
   - Change `computed_at` → `detection_date`
   - **Impact:** `blur.py`, `migration.py`, `db_manager.py`
   - **Effort:** Low (1 hour)

2. **GPS Support**
   - Add `gps` table to database schema
   - Update migration to extract GPS from metadata
   - **Impact:** `workspace_schema.sql`, `migration.py`, `db_manager.py`, `server.py`, `app.js`
   - **Effort:** Medium (4 hours)

3. **RAW + JPEG Tandem Detection**
   - Add tandem analyzer
   - Update schema (already prepared)
   - **Impact:** New analyzer, `migration.py`, `db_manager.py`
   - **Effort:** High (8 hours)

---

## Testing Requirements

When changing JSON sidecar format:

1. **Unit Tests**
   - [ ] Test analyzer output format
   - [ ] Test migration parsing
   - [ ] Test database writes

2. **Integration Tests**
   - [ ] End-to-end: Analysis → Migration → Database → API → Frontend
   - [ ] Backward compatibility with old format
   - [ ] Forward compatibility with new format

3. **Regression Tests**
   - [ ] Existing `.phototool.json` files still work
   - [ ] Old data migrates correctly
   - [ ] No data loss

---

## Version History

| Date | Version | Changes | Components Affected |
|------|---------|---------|---------------------|
| 2026-02-06 | 1.0 | Initial implementation | All |
| 2026-02-08 | 1.1 | Burst format update (V1 → V2) | `burst.py`, `migration.py`, `db_manager.py` |

---

## Contact & Maintenance

**Registry Owner:** Project Lead  
**Last Review:** 2026-02-08  
**Next Review:** When adding new components or changing format

**To Add a Component:**
1. Add entry to appropriate section
2. Specify format version and compliance status
3. Document fields read/written
4. Update dependency graph if needed
5. Commit with descriptive message
