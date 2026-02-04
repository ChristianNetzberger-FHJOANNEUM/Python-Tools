# Photo Tool

Modern photo management tool for organizing, rating, and curating large photo collections.

## Features

### Core Functionality
- **Intelligent Burst Detection**: Automatically groups similar photos taken in quick succession
- **Duplicate Detection**: Finds visually similar images using perceptual hashing
- **Quality Analysis**: Detects blurry photos, exposure issues, and provides quality scores
- **Non-destructive Workflow**: All operations can be previewed (dry-run mode)
- **EXIF-aware**: Reads camera metadata (Lumix S5 optimized)
- **Workspace System**: Organized project structure with cache and reports

### Three-Stage Pipeline

1. **Time-based Grouping**: Fast pre-filtering using EXIF timestamps
2. **Visual Similarity**: Perceptual hashing (pHash/dHash) for quick comparison
3. **Clustering & Actions**: Group similar photos and organize into folders

### Planned Features
- Browser-based GUI with filmstrip view
- Histograms and exposure analysis
- Basic editing (crop, gamma, rotate)
- GraphQL API for client/server architecture
- Rating and tagging system

## Installation

```bash
# Clone repository
git clone <repository-url>
cd Python-tools

# Install with pip (development mode)
pip install -e .

# Or with optional dependencies
pip install -e ".[dev,gui,server]"
```

## Quick Start

```bash
# Initialize a workspace
photo-tool workspace init D:\PhotoWorkspace

# Scan photos from source folders
photo-tool scan --roots "E:\Lumix\2026_Trip"

# Find and group burst photos (dry-run)
photo-tool group-bursts --dry-run

# Generate report
photo-tool report --format text

# Apply changes (move photos into folders)
photo-tool apply --move-bursts

# Analyze photo quality
photo-tool quality --detect-blur --rank
```

## Configuration

Edit `config.yaml` in your workspace:

```yaml
scan:
  extensions: [".jpg", ".jpeg", ".png"]
  recurse: true

grouping:
  time_window_seconds: 3
  max_group_gap_seconds: 2

similarity:
  method: "phash"
  phash_threshold: 6

quality:
  blur_method: "laplacian"
  blur_threshold: 120.0
```

## Architecture

```
photo_tool/
├── cli/           # Command-line interface
├── config/        # Configuration management
├── workspace/     # Workspace and database
├── io/            # File I/O, EXIF, thumbnails
├── analysis/      # Similarity detection, quality analysis
├── actions/       # Organize, rate, dedupe
├── editing/       # Image operations (future)
└── ui/            # GUI components (future)
```

## Development

```bash
# Run tests
pytest

# Format code
black photo_tool tests

# Lint
ruff check photo_tool tests

# Type checking
mypy photo_tool
```

## License

MIT License - See LICENSE file for details

## Roadmap

- [x] Core architecture and CLI
- [x] EXIF reading and time-based grouping
- [x] Perceptual hashing for similarity detection
- [x] Burst photo clustering
- [x] Quality analysis (blur detection)
- [ ] Browser-based GUI with filmstrip
- [ ] GraphQL API
- [ ] Rating and tagging
- [ ] Basic image editing
- [ ] RAW format support (RW2)
- [ ] Advanced filtering and search
