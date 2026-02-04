# Changelog

All notable changes to Photo Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- RAW format support (RW2, CR3, DNG)
- Desktop GUI (PySide6)
- GraphQL API
- Web frontend
- Advanced video analysis (scene detection, content-based duplicates)
- Advanced audio features (waveform, similarity detection)
- Batch export with presets

## [0.2.1] - 2026-02-04

### Added - Audio Support 🎵
- **Audio file management**: Scan and index audio files alongside photos/videos
- **Audio metadata extraction**: Title, artist, album, genre, duration, sample rate, codec (requires ffprobe)
- **Mixed media workflows**: Photos, videos, AND audio in same workspace
- **New CLI commands**:
  - `audio info <file>` - Show detailed audio information
  - `audio list` - List all audio files with metadata
- **Supported formats**: MP3, WAV, M4A, AAC, FLAC, OGG, OPUS, WMA
- **Complete DaVinci Resolve workflow**: Manage video + audio assets together

### Changed
- Scanner now detects audio files automatically (MediaFile extended)
- Scan output shows photos/videos/audio breakdown
- All analysis commands skip audio files with informative messages
- Default config includes common audio extensions (.mp3, .wav)
- Version bumped to 0.2.1

### Documentation
- Added AUDIO_SUPPORT.md - Complete audio usage guide
- Updated README.md with audio features
- Updated example configs with audio extensions

### Technical
- New module: `photo_tool/io/audio_metadata.py` - Audio metadata extraction
- New CLI commands: `commands_audio.py`
- Extended scanner with AUDIO_EXTENSIONS
- MediaFile now supports "audio" type

## [0.2.0] - 2026-02-04

### Added - Video Support 🎥
- Video file management (scan, index, organize)
- Video metadata extraction (duration, resolution, codec, fps)
- Video thumbnail generation (first frame extraction)
- Mixed media workflows (photos + videos together)
- New CLI commands:
  - `video info <file>` - Show detailed video information
  - `video list` - List all videos with metadata
  - `rate set <file> --stars N` - Rate photos/videos
  - `rate get <file>` - Get rating
- MediaFile class for unified photo/video handling
- Support for: MP4, MOV, AVI, MKV, MTS/M2TS, WEBM
- ffprobe integration for detailed metadata (optional)
- DaVinci Resolve workflow support (rate/tag for import)

### Changed
- Scanner detects media type automatically
- Photo analysis commands skip videos with info message
- Default config includes video extensions
- Scan output shows photo/video breakdown
- Thumbnail system handles both photos and videos

### Documentation
- Added VIDEO_SUPPORT.md - Complete video usage guide
- Updated README.md with video features
- Updated examples with mixed media workflows

## [0.1.0] - 2026-02-04

### Added
- Initial release
- CLI interface with Typer
- Workspace management system
- Photo scanning with EXIF reading
- Three-stage analysis pipeline:
  - Time-based grouping
  - Perceptual hashing (pHash, dHash, aHash)
  - Visual similarity clustering
- Quality analysis:
  - Blur detection (Laplacian variance)
  - Exposure histogram
  - Clipping detection
- Organization features:
  - Burst photo organization
  - Duplicate detection
  - Folder creation with naming strategies
- Rating system (JSON sidecars)
- Report generation:
  - Text reports
  - HTML reports with thumbnails
- Configuration system (YAML + Pydantic validation)
- Dry-run mode for safe previewing
- Progress bars and rich console output
- SQLite database for photo indexing
- Thumbnail caching
- Comprehensive documentation:
  - README.md
  - QUICKSTART.md
  - GETTING_STARTED.md
  - ARCHITECTURE.md
  - DEVELOPMENT.md

### Features by Module

#### CLI Commands
- `workspace init` - Create new workspace
- `workspace info` - Show workspace details
- `scan` - Scan directories for photos
- `scan exif` - Show EXIF metadata
- `analyze bursts` - Find burst sequences
- `analyze quality` - Detect blur and quality issues
- `organize bursts` - Organize bursts into folders
- `organize dedupe` - Handle duplicates
- `report generate` - Generate analysis reports

#### Analysis Methods
- Perceptual hashing (imagehash library)
- Blur detection (OpenCV Laplacian)
- SSIM comparison (scikit-image)
- Time-based grouping (EXIF timestamps)
- Sequential clustering algorithm

#### Safety Features
- Dry-run mode by default
- No destructive operations without confirmation
- EXIF metadata preservation
- Move operations (not delete)
- Comprehensive error handling and logging

### Technical Stack
- Python 3.10+
- Typer for CLI
- Pydantic for validation
- Pillow + OpenCV for images
- imagehash for perceptual hashing
- Rich for terminal output
- PyYAML for configuration
- SQLite for indexing

### Known Limitations
- JPG/PNG only (no RAW support yet)
- Single-user/local only (no web interface)
- Sequential processing (no parallel execution)
- Basic clustering algorithm (could be improved with graph-based clustering)
- English-only error messages

### Performance
- Tested with up to 10,000 photos
- Time-based grouping: O(n log n)
- Hash computation: ~0.1s per photo
- Clustering: O(n²) within groups (but groups are small)

## [0.0.1] - 2026-02-04

### Added
- Project structure
- Module scaffolding
- Initial documentation

---

## Version Numbering

- **Major (X.0.0)**: Breaking changes
- **Minor (0.X.0)**: New features, backwards compatible
- **Patch (0.0.X)**: Bug fixes, no new features

## Release Process

1. Update version in `photo_tool/__init__.py`
2. Update version in `pyproject.toml`
3. Update this CHANGELOG.md
4. Commit: `git commit -am "Release vX.Y.Z"`
5. Tag: `git tag -a vX.Y.Z -m "Version X.Y.Z"`
6. Push: `git push && git push --tags`
7. Build: `python -m build`
8. Publish: `twine upload dist/*`
