# Database Re-Sync Guide

## When Do You Need This?

Run a database re-sync when:

1. **JSON files were deleted/updated** but the database still has old data
2. **Burst containers not showing correctly** (e.g., all folders except the first one)
3. **JSON and Database are out of sync** (verified using diagnostic buttons)

## How to Re-Sync

### Method 1: Automatic Re-Sync Script (Recommended)

Run this script to completely rebuild the database from current JSON files:

```powershell
cd c:\_Git\Python-tools\gui_poc
python resync_database.py
```

**What it does:**
- Clears all metadata from the database
- Re-scans all JSON sidecar files
- Imports fresh data into the database
- Preserves folder structure and media references

**When to use:**
- After deleting old JSON files
- When burst data is inconsistent across folders
- After changing JSON format versions

### Method 2: Manual Re-Scan (Slower)

If you prefer to re-scan folders individually:

1. Click the **🔍 Scan** button for each folder
2. Wait for each scan to complete
3. The database will be updated automatically

**When to use:**
- Only one or two folders need updating
- You want to re-analyze photos (blur + burst detection)

## Diagnostic Tools

Use these buttons to check sync status:

### 📄 JSON Button
- Shows how many JSON files exist
- Counts burst data in JSON files
- Displays sample entries from JSON

### 🗄️ DB Button
- Shows how many photos are in the database
- Counts burst data in database
- Displays sample entries from database

**Compare both reports** to see if they match!

## Example: Fixing the Current Issue

Based on the diagnostic output:

```
Database Status:
- 101_PANA: 95 bursts, 23 groups ✅ (correct)
- 102_PANA: 0 bursts ❌ (needs migration)
- 103_PANA: 428 bursts, 380 groups ❌ (OLD data!)
- 104_PANA: 183 bursts, 79 groups ✅ (looks good)
```

**Fix:**
1. Run `python resync_database.py`
2. Wait for re-sync to complete
3. Restart the server
4. Reload the Media tab
5. All folders should now show correct burst containers

## Changes in This Update

### 1. **Disabled HTTP Request Logging**
   - No more terminal spam from thumbnail requests
   - Only errors are logged now
   - Easier to see important scan progress

### 2. **Added Diagnostic Buttons**
   - **📄 JSON**: Check JSON sidecar files
   - **🗄️ DB**: Check database records
   - Located next to the Scan button in Media Manager

### 3. **Database Re-Sync Script**
   - `resync_database.py`: Complete database rebuild
   - Safe to run multiple times
   - Always creates a fresh sync from current JSON files

## Troubleshooting

### Q: Burst containers still not showing after re-sync?
**A:** Restart the server after running `resync_database.py`

### Q: Re-sync script says "Cancelled"?
**A:** You must type `yes` (not just `y`) to confirm the re-sync

### Q: Can I run re-sync while server is running?
**A:** No! Stop the server first, run re-sync, then restart

### Q: Will re-sync delete my photos or JSON files?
**A:** No! It only updates the database. Your files are safe.

### Q: How long does re-sync take?
**A:** ~1-2 seconds per 100 photos (reads JSON files only, no image processing)
