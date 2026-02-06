# Bugfixes - Workspace Creation & Scan Error

## Issues Fixed

### 1. ✅ Workspace Creation Path
**Problem:** When creating a workspace, the entered path was used directly instead of creating a subfolder with the workspace name.

**Example (Before):**
- User enters name: "Vacation 2024"
- User browses to: "C:/PhotoTool"
- Workspace created at: "C:/PhotoTool" ❌

**Example (After):**
- User enters name: "Vacation 2024"
- User browses to: "C:/PhotoTool"
- Workspace created at: "C:/PhotoTool/Vacation 2024" ✅

**Solution:**
- Frontend now combines parent path + workspace name
- Formula: `parentPath/workspaceName`
- UI shows preview: "💡 Workspace will be created as: C:/PhotoTool/Vacation 2024"
- Label changed from "Workspace Path" to "Parent Folder" for clarity

**Files Modified:**
- `gui_poc/static/index.html`:
  - `addWorkspace()` method: Constructs full path before API call
  - Modal UI: Shows preview of final path
  - Label: Changed to "Parent Folder"

**Code:**
```javascript
const parentPath = this.newWorkspacePath;
const workspaceName = this.newWorkspaceName.trim();
const fullWorkspacePath = parentPath.endsWith('/') || parentPath.endsWith('\\') 
    ? parentPath + workspaceName 
    : parentPath + '/' + workspaceName;
```

### 2. ✅ Scan Error - `recurse` Parameter
**Problem:** Scanner functions expected parameter named `recursive` but code was using `recurse`.

**Error Message:**
```
Error during scan: scan_multiple_directories() got an unexpected keyword argument 'recurse'
```

**Root Cause:**
- Function signature: `scan_multiple_directories(..., recursive: bool = True)`
- Code was calling: `scan_multiple_directories(..., recurse=True)`
- Parameter name mismatch

**Locations Fixed:**

#### 1. `gui_poc/server.py` (7 occurrences)
**Before:**
```python
all_media = scan_multiple_directories(
    enabled_folders,
    config.scan.extensions,
    config.scan.recurse,  # ❌ Positional arg (wrong position)
    show_progress=False
)
```

**After:**
```python
all_media = scan_multiple_directories(
    enabled_folders,
    config.scan.extensions,
    recursive=config.scan.recurse,  # ✅ Named argument
    show_progress=False
)
```

**Fixed in:**
- `/api/photos` endpoint (line ~122)
- `/api/keywords` endpoint (line ~358)
- `/api/bursts` endpoint (line ~636, ~700)
- `/api/stats` endpoint (line ~951)
- `/api/quality/detect-blur` endpoint (line ~1089)
- `/api/quality/blur-scores` endpoint (line ~1175)

#### 2. `photo_tool/prescan/scanner.py` (1 occurrence)
**Before:**
```python
media = scan_multiple_directories(
    [self.folder],
    extensions=['.jpg', '.jpeg', '.png', '.raw', '.arw', '.cr2', '.nef'],
    recurse=True,  # ❌ Wrong parameter name
    show_progress=False
)
```

**After:**
```python
media = scan_multiple_directories(
    [self.folder],
    extensions=['.jpg', '.jpeg', '.png', '.raw', '.arw', '.cr2', '.nef'],
    recursive=True,  # ✅ Correct parameter name
    show_progress=False
)
```

## Function Signature Reference

**Correct signature** (from `photo_tool/io/scanner.py`):
```python
def scan_multiple_directories(
    roots: List[Path],
    extensions: List[str],
    recursive: bool = True,  # ← Correct name
    show_progress: bool = True
) -> List[MediaFile]:
```

## Testing

### Workspace Creation
1. Open "Add Workspace" modal
2. Enter name: "Test Workspace"
3. Browse to parent folder: "C:/PhotoTool"
4. Verify preview shows: "C:/PhotoTool/Test Workspace"
5. Create workspace
6. Verify folder created at: "C:/PhotoTool/Test Workspace/"
7. Verify workspace appears in list

### Scan Functionality
1. Go to Media Manager tab
2. Add a media folder
3. Click "🔍 Scan" button
4. Verify progress bar appears and updates
5. Verify no console errors
6. Verify scan completes successfully
7. Check folder shows "✓ SCANNED" badge

## Impact

### Before Fix
- **Workspace Creation:** Confusing, workspaces created at wrong location
- **Scanning:** Completely broken, error on every scan attempt
- **User Experience:** Frustrating, core features not working

### After Fix
- **Workspace Creation:** Clear, intuitive, works as expected
- **Scanning:** Fully functional, progress visible
- **User Experience:** Smooth, professional

## Related Files

### Modified
- `gui_poc/server.py` - Fixed 7 scan calls
- `photo_tool/prescan/scanner.py` - Fixed 1 scan call
- `gui_poc/static/index.html` - Fixed workspace creation path logic

### Reference
- `photo_tool/io/scanner.py` - Function signature definition

## Recommendations

### Code Quality
1. **Use Named Arguments:** Always use named arguments for boolean parameters
   - ✅ `recursive=True` (clear intent)
   - ❌ `True` (ambiguous)

2. **Parameter Naming:** Keep parameter names consistent across codebase
   - Function uses: `recursive`
   - Config uses: `recurse`
   - Solution: Convert at call site: `recursive=config.scan.recurse`

3. **Type Hints:** Use type hints to catch such errors early
   ```python
   def scan(recursive: bool = True):  # IDE will warn on wrong args
   ```

### Testing
1. **Integration Tests:** Add tests for scanner calls
2. **API Tests:** Test all endpoints that use scanner
3. **UI Tests:** Test workspace creation flow

## Migration Notes

### For Existing Workspaces
- Workspaces created before this fix are at the parent level
- They will continue to work normally
- New workspaces will be created in subfolders
- No migration needed

### For Developers
- Update any custom code that calls `scan_multiple_directories()`
- Use named argument: `recursive=True/False`
- Check for similar issues with other functions

## Summary

✅ **2 Critical Bugs Fixed**
- Workspace creation now creates subfolder with workspace name
- Scanning now works correctly with proper parameter name

Both issues were parameter-related:
1. Path construction in frontend
2. Parameter naming in function calls

Simple fixes with big impact on usability!
