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
- Advanced filtering
- Batch export with presets

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
