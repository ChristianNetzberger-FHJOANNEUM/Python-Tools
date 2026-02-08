# Software Maintenance Guide

**Last Updated:** 2026-02-08

---

## Quick Start: Before Making Changes

### I want to add/change a JSON field

1. ✅ Read `JSON_SIDECAR_FORMAT.md`
2. ✅ Read `SOFTWARE_REGISTRY.md` 
3. ✅ Check which components are affected
4. ✅ Update specification document first
5. ✅ Update all affected components (see registry)
6. ✅ Add your component to registry if new
7. ✅ Test end-to-end

### I want to add a new analyzer

1. ✅ Read `JSON_SIDECAR_FORMAT.md`
2. ✅ Read `photo_tool/prescan/analyzers/README.md`
3. ✅ Follow the documented output format
4. ✅ Add analyzer to `SOFTWARE_REGISTRY.md`
5. ✅ Update `migration.py` to read your data
6. ✅ Update `db_manager.py` to write to database
7. ✅ Update `server.py` to serve data (if needed)
8. ✅ Update `app.js` to display data (if needed)

### I want to understand the architecture

1. ✅ Start with `docs/README.md` (overview)
2. ✅ Read `COMPATIBILITY_ANALYSIS.md` (big picture)
3. ✅ Read `DATABASE_ARCHITECTURE.md` (SQLite schema)
4. ✅ Read `SYNC_STRATEGY.md` (JSON ↔ SQLite)

---

## Critical Documentation Files

### Must-Read Before Changes

| File | Purpose | When to Read |
|------|---------|--------------|
| `JSON_SIDECAR_FORMAT.md` | **Format Specification** | Before ANY format changes |
| `SOFTWARE_REGISTRY.md` | **Component Inventory** | Before ANY format changes |
| `DATABASE_ARCHITECTURE.md` | Database Schema | Before schema changes |
| `SYNC_STRATEGY.md` | Sync Mechanisms | Before migration changes |

### Reference Documentation

| File | Purpose | When to Read |
|------|---------|--------------|
| `COMPATIBILITY_ANALYSIS.md` | Data flow & compatibility | Understanding architecture |
| `PHASE3_SQLITE_ARCHITECTURE.md` | Original design doc | Historical context |
| `photo_tool/prescan/analyzers/README.md` | Analyzer guidelines | Adding new analyzers |

---

## Component Update Checklist

When changing JSON sidecar format, update in this order:

### Phase 1: Specification
- [ ] Update `JSON_SIDECAR_FORMAT.md` with new format
- [ ] Mark as "Proposed" or "Draft" initially
- [ ] Document rationale for change
- [ ] Include examples (before/after)

### Phase 2: Writers (Components that produce JSON)
- [ ] Update `photo_tool/prescan/analyzers/*.py` if needed
- [ ] Update `gui_poc/static/app.js` if user metadata changes
- [ ] Test output format matches specification

### Phase 3: Readers (Components that consume JSON)
- [ ] Update `gui_poc/migration.py` to parse new format
- [ ] Update `gui_poc/db_manager.py` to handle new fields
- [ ] Add backward compatibility if needed
- [ ] Test with both old and new JSON files

### Phase 4: Database
- [ ] Update `gui_poc/db/schemas/workspace_schema.sql` if new columns needed
- [ ] Create migration script if schema changes
- [ ] Run schema migration on existing databases
- [ ] Verify data integrity

### Phase 5: API
- [ ] Update `gui_poc/server.py` if API response changes
- [ ] Test API endpoints return correct data
- [ ] Update API documentation if needed

### Phase 6: Frontend
- [ ] Update `gui_poc/static/app.js` if display logic changes
- [ ] Update `gui_poc/static/index.html` if UI changes
- [ ] Test in browser

### Phase 7: Documentation
- [ ] Update `SOFTWARE_REGISTRY.md` with new version numbers
- [ ] Mark specification as "Stable" in `JSON_SIDECAR_FORMAT.md`
- [ ] Update `COMPATIBILITY_ANALYSIS.md` if data flow changes
- [ ] Update this checklist if process changes

### Phase 8: Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] End-to-end test: Analysis → Migration → DB → API → Frontend
- [ ] Backward compatibility verified
- [ ] No data loss confirmed

### Phase 9: Deployment
- [ ] Commit all changes together (atomic)
- [ ] Tag release with version number
- [ ] Deploy to production
- [ ] Monitor for errors

---

## Common Scenarios

### Scenario 1: Add New Metadata Field

**Example:** Add `is_favorite` boolean to user metadata

**Steps:**
1. Update `JSON_SIDECAR_FORMAT.md`:
   ```json
   {
     "rating": 3,
     "is_favorite": true  // NEW
   }
   ```

2. Update `gui_poc/static/app.js` to write field:
   ```javascript
   metadata.is_favorite = photo.isFavorite
   ```

3. Update `gui_poc/db/schemas/workspace_schema.sql`:
   ```sql
   ALTER TABLE media ADD COLUMN is_favorite BOOLEAN DEFAULT 0;
   ```

4. Update `gui_poc/migration.py` to read field:
   ```python
   is_favorite = metadata_data.get('is_favorite', False)
   ```

5. Update `gui_poc/db_manager.py` to write to DB:
   ```python
   cursor.execute("... is_favorite = ?", (is_favorite,))
   ```

6. Update `gui_poc/server.py` to include in API:
   ```python
   'is_favorite': media.get('is_favorite', 0)
   ```

7. Update `gui_poc/static/app.js` to display:
   ```javascript
   if (photo.is_favorite) { /* show star */ }
   ```

8. Update `SOFTWARE_REGISTRY.md` with changes

9. Test end-to-end

---

### Scenario 2: Change Existing Field Format

**Example:** Change `keywords` from array to comma-separated string

**⚠️ THIS IS A BREAKING CHANGE**

**Steps:**
1. **Document in spec** with "BREAKING CHANGE" warning
2. **Discuss with team** (get approval first!)
3. **Plan migration strategy**:
   - Option A: Support both formats temporarily
   - Option B: One-time conversion script
4. **Update all components** (see checklist above)
5. **Add conversion logic** in migration for old data
6. **Test thoroughly** with old and new data
7. **Deploy atomically** (all components together)
8. **Monitor** for errors

---

### Scenario 3: Add New Analyzer

**Example:** Add face detection analyzer

**Steps:**
1. **Read spec** (`JSON_SIDECAR_FORMAT.md`)
2. **Check if documented** (face detection is already in spec!)
3. **Implement analyzer**:
   ```python
   class FaceAnalyzer:
       def analyze(self, photo_path):
           # ... face detection logic ...
           return {
               'face_count': 2,
               'faces': [...],
               'detection_date': int(time.time())
           }
       
       @property
       def name(self):
           return 'faces'
   ```

4. **Test output format** matches spec exactly

5. **Update migration** (`migration.py`):
   ```python
   faces_data = sidecar_data.get('faces', {})
   ```

6. **Update DB manager** (`db_manager.py`):
   ```python
   face_count = faces_data.get('face_count', 0)
   faces_json = json.dumps(faces_data.get('faces', []))
   # ... write to database ...
   ```

7. **Update registry** (`SOFTWARE_REGISTRY.md`):
   ```markdown
   #### 1.3 Face Analyzer
   - Location: photo_tool/prescan/analyzers/face.py
   - Format Version: 1.0
   - Status: Active
   ```

8. **Test end-to-end**

---

## Version Control Best Practices

### Commit Messages

**Good:**
```
feat(burst): Update burst analyzer to Version 2 format

- Change burst_neighbors (array of objects) → neighbors (array of strings)
- Add burst_id generation during analysis
- Use detection_date instead of computed_at
- Update SOFTWARE_REGISTRY.md

Breaking change: Old .phototool.json files need re-analysis
Spec: JSON_SIDECAR_FORMAT.md v2.0
```

**Bad:**
```
fixed burst stuff
```

### Branch Strategy

- `main` - Production-ready code
- `feature/burst-v2` - Feature branches for changes
- `hotfix/burst-bug` - Urgent bug fixes

### Pull Requests

Include in PR description:
- [ ] Which components changed
- [ ] Spec document updated
- [ ] Registry updated
- [ ] Tests added/updated
- [ ] Backward compatibility handled
- [ ] Breaking changes documented

---

## Testing Strategy

### Unit Tests

Test each component in isolation:
- Analyzer output format
- Migration parsing
- Database writes

### Integration Tests

Test component interactions:
- Analyzer → Migration
- Migration → Database
- Database → API
- API → Frontend

### End-to-End Tests

Test full workflow:
1. Run analysis on test photos
2. Migrate to database
3. Query API
4. Verify frontend display
5. Edit metadata
6. Verify JSON files updated
7. Re-migrate
8. Verify consistency

### Regression Tests

Test with existing data:
- Old `.phototool.json` files
- Old `.metadata.json` files
- Existing database records

---

## Troubleshooting

### Problem: Format mismatch error during migration

**Solution:**
1. Check which JSON files are causing errors
2. Check analyzer version vs. spec version
3. Update migration to support format version
4. Re-run migration

### Problem: New field not showing in UI

**Checklist:**
- [ ] Field in JSON file?
- [ ] Migration reads field?
- [ ] Database has column?
- [ ] API includes field?
- [ ] Frontend displays field?

Walk through the data flow to find where it breaks.

### Problem: Backward compatibility broken

**Solution:**
1. Add format detection to migration
2. Handle both old and new formats
3. Document in `SOFTWARE_REGISTRY.md`
4. Add tests for both formats

---

## Contact

**Questions about:**
- **Format specification:** See `JSON_SIDECAR_FORMAT.md`
- **Component registry:** See `SOFTWARE_REGISTRY.md`
- **Architecture:** See `docs/README.md`
- **Specific bugs:** Check git history and commit messages

**Before asking:**
1. Read relevant documentation
2. Check `SOFTWARE_REGISTRY.md` for component list
3. Search git history for similar changes
4. Check test files for examples

---

**Remember: Documentation is code. Keep it updated!**
