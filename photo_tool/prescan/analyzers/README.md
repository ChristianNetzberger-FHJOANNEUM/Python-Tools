# Photo Analysis Output Format

## ⚠️ CRITICAL: JSON Format Specification

**Before implementing a new analyzer or modifying existing ones:**

1. **READ THE DOCUMENTATION:**
   - See `gui_poc/docs/JSON_SIDECAR_FORMAT.md` for the official format specification
   - This document defines field names, types, and structures

2. **FOLLOW THE STANDARD:**
   - Use the documented field names exactly
   - Use the documented data types
   - Don't invent new formats without updating the documentation first

3. **WHY THIS MATTERS:**
   - The migration system (`gui_poc/db_manager.py`) expects specific field names
   - The database schema (`gui_poc/db/schemas/workspace_schema.sql`) maps to these fields
   - Format mismatches cause data loss and bugs

---

## Current Analyzer Output Formats

### Blur Analysis (`blur.py`)

**Output Structure:**
```json
{
  "laplacian": {
    "score": 107.98,
    "computed_at": "2026-02-06T09:40:48.174940",
    "method_version": "1.0"
  },
  "tenengrad": {
    "score": 21.55,
    "computed_at": "2026-02-06T09:40:49.374367",
    "method_version": "1.0"
  },
  "roi": {
    "score": 946.52,
    "computed_at": "2026-02-06T09:41:00.898297",
    "method_version": "1.0"
  },
  "computed_at": "2026-02-06T09:41:00.898297"
}
```

**Migration Notes:**
- ✅ Field names match documentation
- ⚠️ Uses `computed_at` instead of `detection_date` (both supported)
- ⚠️ Missing `threshold` fields (migration uses defaults: 50.0, 100.0, 60.0)

---

### Burst Analysis (`burst.py`)

**Output Structure (Version 1 - Current):**
```json
{
  "burst_neighbors": [
    {
      "path": "E:\\Lumix-2026-01\\101_PANA\\P1012785.JPG",
      "time_diff": 1.0,
      "similarity": 0.9,
      "direction": "previous"
    }
  ],
  "is_burst_candidate": true,
  "burst_group_size": 2,
  "computed_at": "2026-02-06T21:01:16.392467"
}
```

**⚠️ FORMAT MISMATCH DETECTED:**
- ❌ Uses `burst_neighbors` (array of objects) instead of `neighbors` (array of strings)
- ❌ Missing `burst_id` field (generated during migration)
- ❌ Uses `computed_at` instead of `detection_date`

**Migration Workaround:**
The migration system (`db_manager.py`) was updated to:
1. Accept both `burst_neighbors` and `neighbors`
2. Extract `path` from objects if needed: `[{path: "..."}]` → `["..."]`
3. Generate `burst_id` from neighbor paths if missing
4. Post-process to assign consistent `burst_id` to all photos in a group

**Recommended Fix:**
Update `burst.py` to output Version 2 format:
```json
{
  "is_burst_candidate": true,
  "burst_id": "a4720613550b",
  "neighbors": [
    "E:\\Lumix-2026-01\\101_PANA\\P1012785.JPG"
  ],
  "score": 0.9,
  "detection_date": 1739024645
}
```

This would eliminate the need for migration workarounds.

---

## How to Add a New Analyzer

### Step 1: Read the Documentation
- Review `gui_poc/docs/JSON_SIDECAR_FORMAT.md`
- Check if your analysis type is already documented
- If not documented, add it to the spec first!

### Step 2: Implement the Analyzer
```python
class MyAnalyzer:
    def analyze(self, photo_path: Path) -> Dict[str, Any]:
        # Your analysis logic here
        
        # Return data in the documented format
        return {
            'my_field': value,
            'confidence': 0.95,
            'detection_date': int(time.time())  # Use detection_date, not computed_at
        }
    
    @property
    def name(self) -> str:
        return 'my_analysis'  # This becomes the key in analyses dict
```

### Step 3: Update Database Schema (if needed)
If your analysis adds new fields:

1. Update `gui_poc/db/schemas/workspace_schema.sql`:
   ```sql
   ALTER TABLE photo_metadata ADD COLUMN my_field TEXT;
   ```

2. Update `gui_poc/db_manager.py`:
   ```python
   my_data = sidecar_data.get('my_analysis', {})
   cursor.execute("INSERT INTO ... my_field = ?", (my_data.get('my_field'),))
   ```

3. Update documentation: `gui_poc/docs/JSON_SIDECAR_FORMAT.md`

### Step 4: Update Migration System
Test that existing `.phototool.json` files still work:

```bash
cd gui_poc
python quick_migrate.py
```

---

## Testing Checklist

Before committing analyzer changes:

- [ ] Output format matches documentation
- [ ] Field names are correct (check spelling!)
- [ ] Data types are correct (strings, integers, floats, arrays)
- [ ] Timestamps use Unix epoch (integers) or ISO 8601 (strings)
- [ ] Migration system handles the output correctly
- [ ] Database receives the data correctly
- [ ] UI displays the data correctly
- [ ] Documentation is updated

---

## Common Mistakes to Avoid

1. ❌ **Inventing new field names**
   - Wrong: `blur_neighbors`
   - Right: `burst_neighbors` (check docs!)

2. ❌ **Wrong data types**
   - Wrong: `"neighbors": "path1.jpg,path2.jpg"` (comma-separated string)
   - Right: `"neighbors": ["path1.jpg", "path2.jpg"]` (array)

3. ❌ **Inconsistent timestamp formats**
   - Wrong: Mix of Unix timestamps and ISO 8601 strings
   - Right: Pick one and document it

4. ❌ **Missing required fields**
   - Some fields like `is_burst_candidate` are required by the database
   - Check the schema before omitting fields

5. ❌ **Using nested objects when simple values work**
   - Wrong: `"neighbors": [{"path": "..."}]` (unnecessarily complex)
   - Right: `"neighbors": ["..."]` (simple and efficient)

---

## Contact & Questions

If you're unsure about the format:
1. Read `gui_poc/docs/JSON_SIDECAR_FORMAT.md` first
2. Check existing analyzer implementations
3. Ask before implementing a new format
4. Update documentation when adding new features

**Remember:** Format consistency prevents bugs and saves debugging time!
