# Photo Tool - Quick Start (5 Minutes)

Get started with Photo Tool in 5 minutes! Works with photos AND videos from your Lumix S5.

## Installation

```bash
cd C:\_Git\Python-tools
python -m venv venv
.\venv\Scripts\activate
pip install -e ".[dev]"
```

**Optional:** Install ffmpeg for video metadata:
```bash
winget install ffmpeg
```

## Basic Usage

### 1. Create Workspace (1 min)

```bash
# For Lumix S5 DCIM folder (photos + videos)
photo-tool workspace init D:\MyPhotos --root F:\DCIM
```

Edit `D:\MyPhotos\config.yaml` to include videos:
```yaml
extensions: [".jpg", ".jpeg", ".mp4", ".mov"]
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

1. ✓ Scanned your photos AND videos, read EXIF/metadata
2. ✓ Found photos taken within 3 seconds of each other
3. ✓ Compared them visually using perceptual hashing
4. ✓ Detected sharpest photo in each burst
5. ✓ Moved similar photos into folders (videos untouched)
6. ✓ Generated a report with thumbnails

## Video Bonus

```bash
# List all videos
photo-tool video list --sort duration

# Show video info
photo-tool video info F:\DCIM\100_PANA\VIDEO001.mp4

# Rate videos for DaVinci Resolve
photo-tool rate set VIDEO001.mp4 --stars 5
```

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
