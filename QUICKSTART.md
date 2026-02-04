# Photo Tool - Quick Start (5 Minutes)

Get started with Photo Tool in 5 minutes!

## Installation

```bash
cd C:\_Git\Python-tools
pip install -e .
```

## Basic Usage

### 1. Create Workspace (1 min)

```bash
photo-tool workspace init D:\MyPhotos --root E:\Camera
```

### 2. Find Burst Photos (2 min)

```bash
# Preview (safe - won't change anything)
photo-tool analyze bursts --workspace D:\MyPhotos
```

### 3. Organize (1 min)

```bash
# Dry run (preview what will happen)
photo-tool organize bursts --workspace D:\MyPhotos --dry-run

# Apply changes
photo-tool organize bursts --workspace D:\MyPhotos --apply
```

### 4. Generate Report (1 min)

```bash
photo-tool report generate --workspace D:\MyPhotos --format html
```

Open `D:\MyPhotos\reports\cluster_report.html` in your browser!

## That's It!

Your burst photos are now organized into folders, with the best photo from each burst easily identifiable.

## What Photo Tool Did

1. ✓ Scanned your photos and read EXIF timestamps
2. ✓ Found photos taken within 3 seconds of each other
3. ✓ Compared them visually using perceptual hashing
4. ✓ Detected sharpest photo in each burst
5. ✓ Moved similar photos into folders
6. ✓ Generated a report with thumbnails

## Next Steps

- Adjust settings in `D:\MyPhotos\config.yaml`
- Try quality analysis: `photo-tool analyze quality`
- Find duplicates: `photo-tool organize dedupe`
- Read [GETTING_STARTED.md](GETTING_STARTED.md) for detailed workflows

## Safety Features

- **Dry-run by default** - Preview before making changes
- **No deletion** - Only moves files into folders
- **EXIF preserved** - All metadata stays intact
- **Undo-friendly** - Just move files back out of folders

---

**Important:** Always use `--dry-run` first to see what will happen!
