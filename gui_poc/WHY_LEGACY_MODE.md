# Why Is the System Using Legacy File-Based Loading?

**Symptom:** You see this message in the terminal:
```
🐌 Using legacy file-based loading (SQLite not available)
```

---

## Root Cause

The SQLite database is **empty** (has 0 media items), so the system falls back to legacy mode.

### How the Check Works

```python
# From server.py lines 2631-2644
cursor.execute("SELECT COUNT(*) as count FROM media")
media_count = cursor.fetchone()['count']

sqlite_available = (media_count > 0)  # ← Returns False if empty!

if use_sqlite == 'auto':  # Default mode
    use_sqlite = sqlite_available  # ← Disabled if count=0
```

**If database is empty → SQLite disabled → Legacy mode activated**

---

## Why Is Your Database Empty?

Looking at your terminal logs, the `resync_database.py` script:

1. ✅ **Cleared the database** successfully
2. ❌ **Failed during migration** (ProcessPoolExecutor + KeyboardInterrupt errors)
3. Result: Database is empty

From your terminal (lines 356-461):
```
🗑️ Clearing old metadata...
✅ Database cleared

🚀 Re-migrating 4 folders...
[1/4] Migrating: E:\Lumix-2026-01\101_PANA
...
KeyboardInterrupt
Traceback (most recent call last):
  ...ProcessPoolExecutor errors...
```

The migration failed because of a Windows multiprocessing issue (worker processes trying to run `input()` prompts).

---

## Impact of Using Legacy Mode

**Performance:**
- Legacy mode is **slower** for large collections
- Must read JSON files + EXIF data on every load
- No database cache benefits

**Functionality:**
- ✅ Burst containers **still work** (your current output shows this!)
- ✅ All features functional
- ❌ Just slower to load

**From your terminal:**
- 101_PANA: 24 burst groups with 87 photos ✅ Working!
- 102_PANA: 153 groups with 327 photos ✅ Working!
- 103_PANA: 136 groups with 288 photos ✅ Working!
- 104_PANA: 80 groups with 171 photos ✅ Working!

---

## Solutions (Choose One)

### ✅ Option 1: Auto-Migration (Easiest)

The system has **built-in auto-migration** that runs when you enable folders!

**Steps:**
1. **Open the app** in your browser
2. Go to **Settings** (gear icon)
3. Click **"Media Manager"** tab
4. **Toggle ON** each folder you want to use
5. The system will auto-migrate on first access

**Code location:** `server.py` lines 2674-2707

**What happens:**
- System checks if folder has 0 items in database
- Automatically runs migration
- Populates database with JSON data
- Enables SQLite fast path

**Advantages:**
- No command line needed
- Works through UI
- Built-in safety checks

---

### ✅ Option 2: Run Migration Script

Use the **new** migration script (fixed for Windows):

```powershell
cd c:\_Git\Python-tools\gui_poc
python migrate_folders.py
```

**What it does:**
- Migrates your 4 folders:
  - `E:\Lumix-2026-01\101_PANA`
  - `E:\Lumix-2026-01\102_PANA`
  - `E:\Lumix-2026-01\103_PANA`
  - `E:\Lumix-2026-01\104_PANA`
- Reads all JSON sidecar files
- Populates SQLite database
- Enables fast path

**To customize folders:**
Edit `FOLDERS_TO_MIGRATE` list at the top of `migrate_folders.py`

---

### ⚠️ Option 3: Use Legacy Mode Permanently

If you don't want to use SQLite:

**No action needed!** Legacy mode is the fallback and works fine for smaller collections.

**When to consider this:**
- You have < 1000 photos
- Loading speed is acceptable
- You prefer simpler architecture

---

## How to Verify SQLite Is Working

After migrating, restart the server and look for:

```
💾 Using SQLite for project pasang-wedding-slideshow (FAST PATH)
✅ SQLite load complete: 234 items in 0.123s
```

**Instead of:**
```
🐌 Using legacy file-based loading (SQLite not available)
```

---

## Performance Comparison

**Legacy Mode (Current):**
```
📊 Project Media Performance: {
  'directory_scan': 0.07s,
  'exif_reading_parallel': 6.34s,       ← Reads EXIF every time
  'parallel_metadata_loading': 0.77s,   ← Loads JSON every time
  'response_building': 0.32s,
  'burst_grouping': 0.12s
}
Total: ~7.5 seconds
```

**SQLite Mode (Expected):**
```
📊 SQLite Performance: {
  'sqlite_query': 0.05s,                ← Just query database
  'response_building': 0.15s,
  'burst_grouping': 0.05s
}
Total: ~0.25 seconds (30x faster!)
```

---

## Recommendation

**Use Option 1 (Auto-Migration via UI)**

This is the easiest and safest method:
- Works through the UI
- No command line needed
- Built-in error handling
- You can enable folders one at a time

Just toggle the folders ON in the Media Manager settings page!

---

## Files Reference

- `migrate_folders.py` - New migration script (Windows-safe)
- `resync_database.py` - Full database resync (fixed)
- `server.py` lines 2631-2707 - SQLite check & auto-migration logic
- `WHY_LEGACY_MODE.md` - This document
