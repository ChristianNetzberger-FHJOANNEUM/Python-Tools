# Getting Started with Photo Tool

This guide will help you set up and use Photo Tool for managing your photo collection.

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Install Photo Tool

```bash
# Navigate to project directory
cd C:\_Git\Python-tools

# Install in development mode (recommended)
pip install -e .

# Or install with all optional dependencies
pip install -e ".[dev,gui,server]"
```

## Quick Start Guide

### 1. Create a Workspace

A workspace is where Photo Tool stores its cache, database, and reports.

```bash
# Create workspace and specify your photo directories
photo-tool workspace init D:\PhotoWorkspace --root E:\Photos --root F:\Camera
```

This creates:
- `D:\PhotoWorkspace\` - workspace directory
- `config.yaml` - configuration file
- `cache/` - thumbnails and hashes
- `db/` - photo index database
- `reports/` - analysis reports
- `exports/` - processed images

### 2. Configure Your Workspace

Edit `D:\PhotoWorkspace\config.yaml` to customize settings:

```yaml
scan:
  roots: 
    - E:\Photos
    - F:\Camera
  extensions: [".jpg", ".jpeg", ".png"]
  recurse: true

grouping:
  time_window_seconds: 3.0      # Burst detection window
  max_group_gap_seconds: 2.0    # Max gap within burst

similarity:
  method: "phash"
  phash_threshold: 6            # Lower = stricter similarity

actions:
  dry_run: true                 # Preview before making changes
  burst_folder_naming: "first_filename"
  min_group_size: 2
```

### 3. Scan Your Photos

```bash
# Scan configured directories
photo-tool scan --workspace D:\PhotoWorkspace

# Or scan specific directories
photo-tool scan --root E:\Photos
```

### 4. Find Burst Sequences

```bash
# Analyze and find burst photos (preview only)
photo-tool analyze bursts --workspace D:\PhotoWorkspace

# Adjust settings
photo-tool analyze bursts --time-window 5.0 --threshold 8
```

### 5. Organize Burst Photos

```bash
# Preview what will happen (DRY RUN - recommended first!)
photo-tool organize bursts --workspace D:\PhotoWorkspace --dry-run

# Actually move photos into folders
photo-tool organize bursts --workspace D:\PhotoWorkspace --apply

# Only organize groups of 3+ photos
photo-tool organize bursts --apply --min-size 3
```

### 6. Analyze Photo Quality

```bash
# Find blurry photos
photo-tool analyze quality --workspace D:\PhotoWorkspace

# Show top 50 blurriest photos
photo-tool analyze quality --top 50
```

### 7. Generate Reports

```bash
# Generate text report
photo-tool report generate --format text

# Generate HTML report with thumbnails
photo-tool report generate --format html --output report.html

# HTML without thumbnails (faster)
photo-tool report generate --format html --no-thumbnails
```

## Common Workflows

### Workflow 1: Quick Burst Organization

Perfect for after a photoshoot where you took many burst sequences.

```bash
# 1. Create workspace
photo-tool workspace init D:\PhotoWorkspace --root E:\DCIM\Camera

# 2. Preview burst detection
photo-tool analyze bursts

# 3. Organize (dry run first)
photo-tool organize bursts --dry-run

# 4. Apply if happy with preview
photo-tool organize bursts --apply
```

### Workflow 2: Find Duplicates

Find and handle duplicate photos across your collection.

```bash
# 1. List duplicates
photo-tool organize dedupe --action list

# 2. Move duplicates to separate folder
photo-tool organize dedupe --action move --move-to duplicates/ --apply

# 3. Or delete duplicates (keeping best quality)
photo-tool organize dedupe --action delete --strategy keep_best --apply
```

### Workflow 3: Quality Check

Find and review low-quality photos.

```bash
# 1. Analyze quality
photo-tool analyze quality --top 100

# 2. Generate detailed report
photo-tool report generate --format html --output quality_report.html

# 3. Review in browser and manually delete/edit as needed
```

## Tips

### Safety First
- Always use `--dry-run` first to preview changes
- Photo Tool never deletes originals during burst organization (only moves them)
- Keep backups of important photos

### Performance
- First scan can be slow for large collections (thousands of photos)
- Thumbnails are cached - subsequent operations are faster
- Time-based grouping is fast, visual similarity is slower

### Customization
- Adjust `phash_threshold` if you get too many/few matches
  - Lower (0-3): Very strict, only nearly identical photos
  - Medium (4-8): Default, good for burst detection
  - Higher (9+): Looser, finds more variations
- Adjust `time_window_seconds` based on your camera's burst rate
  - Fast burst (10fps): 2-3 seconds
  - Slow continuous: 5-10 seconds

### Best Practices
1. Start with a small subset of photos to test settings
2. Use dry-run mode extensively
3. Check generated reports before applying bulk operations
4. Keep workspace config.yaml in version control
5. Regularly clear cache if disk space is limited:
   ```bash
   # Manually delete cache
   rm -r D:\PhotoWorkspace\cache\*
   ```

## Troubleshooting

### "No photos found"
- Check that scan roots in config.yaml are correct
- Verify extensions include your photo formats
- Make sure recurse: true if photos are in subdirectories

### "No EXIF data"
- Some photos (screenshots, edited images) may lack EXIF
- Photo Tool falls back to file modification time
- You can still use visual similarity clustering

### "Too many/few bursts detected"
- Adjust time_window_seconds in config
- Adjust phash_threshold (lower = stricter)
- Use --time-window and --threshold CLI options to test

### Slow performance
- First run builds cache (slow)
- Subsequent runs reuse cached hashes (fast)
- For huge collections (100k+ photos), consider processing in batches

## Next Steps

- Read [README.md](README.md) for architecture details
- Explore GUI options (future): PySide6 desktop app
- Set up GraphQL API (future): Client/server architecture
- Add RAW format support (future): RW2, CR3, etc.

## Getting Help

- Check configuration: `photo-tool workspace info`
- Enable debug logging: `photo-tool --debug <command>`
- Review logs in: `D:\PhotoWorkspace\logs\`

---

Happy photo organizing! 📸
