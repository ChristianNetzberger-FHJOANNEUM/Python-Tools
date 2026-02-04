# Photo Tool

Modern photo management tool for organizing, rating, and curating large photo collections.

## Features

### Core Functionality
- **Intelligent Burst Detection**: Automatically groups similar photos taken in quick succession
- **Duplicate Detection**: Finds visually similar images using perceptual hashing
- **Quality Analysis**: Detects blurry photos, exposure issues, and provides quality scores
- **Video Support** (v0.2): Manage videos alongside photos, extract metadata, generate thumbnails
- **Audio Support** (NEW v0.2.1): Manage audio files, extract metadata, rate tracks
- **Non-destructive Workflow**: All operations can be previewed (dry-run mode)
- **EXIF-aware**: Reads camera metadata (Lumix S5 optimized)
- **Workspace System**: Organized project structure with cache and reports

### Three-Stage Pipeline

1. **Time-based Grouping**: Fast pre-filtering using EXIF timestamps
2. **Visual Similarity**: Perceptual hashing (pHash/dHash) for quick comparison
3. **Clustering & Actions**: Group similar photos and organize into folders

### Video Features (v0.2)
- Scan and index video files (.mp4, .mov, .avi)
- Extract video metadata (duration, resolution, codec)
- Generate video thumbnails (first frame)
- Rate and tag videos for later editing
- Time-based organization
- DaVinci Resolve workflow support

### Audio Features (v0.2.1)
- Scan and index audio files (.mp3, .wav, .flac, .m4a)
- Extract audio metadata (title, artist, album, duration)
- Rate and tag audio tracks
- Complete DaVinci Resolve project management (video + audio)
- Music library organization
- Field recording management

### Planned Features
- Browser-based GUI with filmstrip view
- Histograms and exposure analysis
- Basic editing (crop, gamma, rotate)
- GraphQL API for client/server architecture
- Advanced video analysis (scene detection, duplicates)

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
photo-tool workspace init D:\MediaWorkspace --root "F:\Lumix\DCIM"

# Scan photos, videos, AND audio
photo-tool scan --workspace D:\MediaWorkspace

# Find and group burst photos (dry-run)
photo-tool analyze bursts --dry-run

# Generate report
photo-tool report generate --format text

# Organize photos into folders
photo-tool organize bursts --apply

# Analyze photo quality
photo-tool analyze quality --top 50

# Video commands
photo-tool video info F:\Lumix\VIDEO001.mp4
photo-tool video list --sort duration

# Audio commands
photo-tool audio info F:\Audio\recording.mp3
photo-tool audio list --sort duration

# Rate any media file
photo-tool rate set VIDEO001.mp4 --stars 5
photo-tool rate set recording.mp3 --stars 4 --comment "Great take"
```

## Configuration

Edit `config.yaml` in your workspace:

```yaml
scan:
  extensions: [".jpg", ".jpeg", ".png", ".mp4", ".mov", ".mp3", ".wav"]  # Photos + Videos + Audio
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
- [x] **Video support (v0.2)** - Metadata, thumbnails, mixed media
- [x] **Audio support (v0.2.1)** - Metadata, rating, mixed workflows
- [ ] Browser-based GUI with filmstrip
- [ ] GraphQL API
- [ ] Advanced video analysis (scene detection, duplicates)
- [ ] Advanced audio features (waveform, similarity)
- [ ] Basic image editing
- [ ] RAW format support (RW2, CR3)
- [ ] Advanced filtering and search
