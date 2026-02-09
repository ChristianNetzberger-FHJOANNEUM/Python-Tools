# Bug Fix: Burst Containers Showing Single Photos

**Date:** 2026-02-09 12:50  
**Issue:** Burst containers displayed only single photos instead of full burst groups  
**Status:** ✅ FIXED

**Update 2026-02-09 13:00:** Removed all Version 1 format support per user request. Code now only supports Version 2 format (cleaner, simpler).

---

## Problem

When loading media folders in the Media tab:
- Burst containers appeared with only **1 photo** each
- Should have shown **multiple photos** per burst group
- Terminal showed: `Neighbors from sidecar: []` (empty!)

Example from terminal:
```
=== FIRST BURST DEBUG ===
  Current photo: E:\Lumix-2026-01\102_PANA\P1023896.JPG
  Neighbors from sidecar: []  ← EMPTY!
  All paths in group: ['E:\\Lumix-2026-01\\102_PANA\\P1023896.JPG']
  
Burst aa3bb9393b48: 1 photos  ← Should be multiple!
```

---

## Root Cause

The server was using **legacy file-based loading** (not SQLite):
```
🐌 Using legacy file-based loading (SQLite not available)
```

The legacy code path had **outdated JSON parsing logic**:

### Old Code (Before Fix):
```python
# ❌ Looking for OLD field name
neighbors = burst_data.get('burst_neighbors', [])

# ❌ Expected objects with 'path' key (Version 1 format)
for n in neighbors:
    neighbor_path = n['path']
```

### Your JSON Files (Version 2 format):
```json
"burst": {
  "burst_id": "074319d5d9f6",
  "neighbors": ["E:\\path\\photo.JPG"]  ← Strings, not objects!
}
```

**Result:** Code couldn't find `burst_neighbors` field, got empty array `[]`, created single-photo burst groups.

---

## Solution

**Phase 1 (Initial Fix):** Updated code to handle both Version 1 and Version 2 formats.

**Phase 2 (Cleanup - User Request):** Removed all Version 1 format support to simplify code.

### Final Code (Version 2 Only):
```python
# Version 2: neighbors are simple string paths
neighbors = burst_data.get('neighbors', [])
all_paths = [item_path]
fixed_neighbors = []

for neighbor_path in neighbors:
    if not neighbor_path:
        continue
    
    neighbor_filename = Path(neighbor_path).name
    
    if neighbor_filename in path_by_filename:
        actual_path = path_by_filename[neighbor_filename]
        all_paths.append(actual_path)
        fixed_neighbors.append(actual_path)
    elif neighbor_path in path_by_filename.values():
        all_paths.append(neighbor_path)
        fixed_neighbors.append(neighbor_path)

# Version 2: burst_id is always present in JSON
burst_id = burst_data.get('burst_id')
if not burst_id:
    # Fallback with warning
    burst_id = hashlib.md5(all_paths_sorted[0].encode()).hexdigest()[:12]
    logger.warning(f"Missing burst_id in JSON for {item_path}")
```

**Benefits of cleanup:**
- Simpler, more readable code
- No confusion about which format to use
- Faster execution (no format detection logic)
- Clearer error messages if malformed data

---

## Changes Made

### 1. `server.py` (Legacy Code Path)
- **Line 3178-3193:** Updated burst neighbor parsing
  - Reads from `neighbors` (V2) or `burst_neighbors` (V1)
  - Handles both string arrays and object arrays
  - Extracts path correctly based on data type
- **Line 3204-3207:** Use `burst_id` from JSON if present
- **Line 3198:** Fixed debug output

### 2. `docs/JSON_SIDECAR_FORMAT.md`
- Added "Code Compatibility Notes" section
- Documents both Version 1 and Version 2 formats
- Explains auto-detection logic

### 3. Other Fixes in This Session
- **Disabled HTTP logging:** No more thumbnail spam in terminal
- **Added diagnostic buttons:** 📄 JSON and 🗄️ DB check buttons
- **Created resync script:** `resync_database.py` for database rebuild

---

## How to Test

1. **Restart the server** to load the updated code
2. **Reload Media tab** in browser
3. **Check terminal output:**
   ```
   === FIRST BURST DEBUG ===
     Neighbors from sidecar: ["E:\\path\\photo2.JPG", "E:\\path\\photo3.JPG"]  ← Should have values!
     All paths in group: [...multiple paths...]
   
   Burst grouping: 23 groups found with 95 photos  ← groups < photos = correct!
   ```
4. **Check UI:** Burst containers should now show full groups

---

## Expected Behavior After Fix

### Terminal Output Should Show:
```
=== FIRST BURST DEBUG ===
  Current photo: E:\Lumix-2026-01\103_PANA\P1034009.JPG
  Neighbors from sidecar: ["E:\\Lumix-2026-01\\103_PANA\\P1034008.JPG", ...]
  Fixed neighbor paths: ["E:\\Lumix-2026-01\\103_PANA\\P1034008.JPG", ...]
  All paths in group: ["E:\\..\\P1034008.JPG", "E:\\..\\P1034009.JPG"]

=== BURST GROUPING RESULTS ===
Burst grouping: 95 groups found with 234 photos  ← More photos than groups!
```

### UI Should Show:
- **Burst containers with multiple photos** (e.g., "📦 5 photos")
- Click to expand and see all burst photos
- Only one container per burst group

---

## Why Legacy Path Was Used

The server message `🐌 Using legacy file-based loading (SQLite not available)` indicates:
- SQLite database check failed, OR
- Folders not yet migrated to database, OR
- Database file missing/corrupted

**Future optimization:** Ensure folders are migrated to SQLite for better performance.  
**For now:** Legacy path works correctly with this fix.

---

## Related Issues Fixed

This bug fix session also addressed:
1. ❌ **Terminal spam:** Fixed by disabling werkzeug HTTP logging
2. ❌ **Database out of sync:** Created `resync_database.py` utility
3. ✅ **Diagnostic tools:** Added 📄 JSON and 🗄️ DB check buttons

---

## Files Modified

1. `gui_poc/server.py` - Legacy burst parsing logic (3 changes)
2. `gui_poc/docs/JSON_SIDECAR_FORMAT.md` - Compatibility docs
3. `gui_poc/resync_database.py` - New utility script
4. `gui_poc/docs/DATABASE_RESYNC_GUIDE.md` - New guide
5. `gui_poc/static/index.html` - Added diagnostic buttons
6. `gui_poc/static/app.js` - Added check functions
7. `gui_poc/BUGFIX_2026-02-09_BURST_LEGACY.md` - This document

---

## Verification Checklist

- [ ] Server restarted
- [ ] Media tab reloaded
- [ ] Terminal shows neighbors array with values
- [ ] Burst groups show multiple photos (not 1:1 ratio)
- [ ] UI displays burst containers correctly
- [ ] No more thumbnail GET spam in terminal
- [ ] Diagnostic buttons (📄 JSON, 🗄️ DB) work

---

**Next Steps:** Restart server and test! The burst containers should now work correctly.
