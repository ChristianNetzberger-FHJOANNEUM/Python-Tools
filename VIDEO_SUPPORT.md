# Video Support in Photo Tool

Photo Tool v0.2+ includes basic video file management capabilities, allowing you to manage videos alongside photos in your Lumix DCIM folders.

## Features (v0.2 - Video Basics)

### ✅ What Works

- **Scanning**: Find and index video files (.mp4, .mov, .avi, etc.)
- **Metadata Extraction**: Read duration, resolution, codec, creation date
- **Thumbnail Generation**: Extract first frame as thumbnail
- **Rating/Tagging**: Rate and tag videos (JSON sidecars)
- **Time-based Organization**: Sort and organize by recording date
- **Mixed Media**: Handle photos and videos in the same workspace

### ⚠️ What Doesn't Work Yet

- **Burst Detection**: N/A for videos (photos only)
- **Blur Detection**: N/A for videos (photos only)
- **Similarity Detection**: Not implemented for videos yet
- **Duplicate Detection**: Basic (size/name), not content-based

## Installation Requirements

### For Full Video Support

Install **ffmpeg** (includes ffprobe for metadata extraction):

**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Add to PATH or place ffmpeg.exe in system directory
3. Verify: `ffprobe -version`

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg  # CentOS/RHEL
```

### Without ffmpeg

Photo Tool will still work but with limited video metadata:
- File size, modification date
- No duration, resolution, codec info
- Thumbnails still work (using OpenCV)

## Configuration

### Add Video Extensions

Edit your workspace `config.yaml`:

```yaml
scan:
  roots:
    - "F:/Lumix/DCIM"
  extensions:
    - ".jpg"
    - ".jpeg"
    - ".png"
    - ".mp4"     # Lumix S5 video format
    - ".mov"     # Alternative format
    - ".avi"
    - ".mts"     # AVCHD format
  recurse: true
```

### Lumix S5 Typical Setup

```yaml
scan:
  roots:
    - "F:/Lumix/DCIM"     # Main DCIM folder
  extensions:
    # Photos
    - ".jpg"
    - ".jpeg"
    # Videos
    - ".mp4"    # 4K, FHD videos
    - ".mov"    # High frame rate, RAW video
  recurse: true
```

## Usage

### Scan Mixed Media

```powershell
# Scan for photos AND videos
photo-tool scan --workspace D:\MyWorkspace

# Output shows:
# ✓ Found 523 files:
#   Photos: 450
#   Videos: 73
```

### Video-Specific Commands

```powershell
# Show detailed video info
photo-tool video info F:\Lumix\VIDEO001.mp4

# List all videos with metadata
photo-tool video list --workspace D:\MyWorkspace

# Sort by duration
photo-tool video list --sort duration
```

### Video Information Display

```
Video information for: VIDEO001.mp4

Filename      VIDEO001.mp4
Path          F:\Lumix\DCIM\100_PANA
Size          2.3 GB
Captured      2024-12-25 14:30:45
Duration      00:05:23
Resolution    3840x2160
Frame Rate    29.97 fps
Codec         h264
Bit Rate      85.3 Mbps
Format        mp4
```

### Mixed Workflows

```powershell
# Scan everything
photo-tool scan --workspace D:\MyWorkspace

# Analyze photos (videos automatically skipped)
photo-tool analyze bursts
# Note: Skipping 73 video files (not applicable for burst detection)

# Organize photos (videos untouched)
photo-tool organize bursts --apply

# View all videos
photo-tool video list --sort date
```

## DaVinci Resolve Workflow

Photo Tool can help organize media before importing to DaVinci Resolve:

### 1. Scan and Tag

```powershell
# Scan your media
photo-tool scan --workspace D:\Project_Workspace

# View videos
photo-tool video list --sort duration

# Rate videos (for later filtering)
photo-tool rate F:\Lumix\VIDEO001.mp4 --stars 5
photo-tool rate F:\Lumix\VIDEO002.mp4 --stars 3
```

### 2. Organize by Date/Event

```yaml
# Workspace for specific event
workspace:
  path: "D:/Events/Wedding_2024"

scan:
  roots:
    - "F:/Lumix/DCIM"
  extensions: [".mp4", ".mov"]  # Videos only
```

### 3. Export Metadata

Rating information is stored in JSON sidecars:
```
F:\Lumix\DCIM\100_PANA\
├── VIDEO001.mp4
├── .VIDEO001.rating.json    ← Rating data
├── VIDEO002.mp4
└── .VIDEO002.rating.json
```

## Technical Details

### Supported Video Formats

| Format | Extension | Lumix S5 | Metadata | Thumbnail |
|--------|-----------|----------|----------|-----------|
| MP4 | .mp4 | ✅ | ✅ | ✅ |
| MOV | .mov | ✅ | ✅ | ✅ |
| AVI | .avi | ⚠️ | ✅ | ✅ |
| MKV | .mkv | ❌ | ✅ | ✅ |
| MTS/M2TS | .mts, .m2ts | ⚠️ AVCHD | ✅ | ✅ |

### Metadata Extraction

**With ffprobe:**
- Duration (precise)
- Resolution (width x height)
- Frame rate
- Codec (h264, h265, etc.)
- Bit rate
- Creation date (from metadata)

**Without ffprobe (fallback):**
- File size
- File modification date
- Extension

### Thumbnail Generation

- Uses OpenCV to extract first frame
- Cached like photo thumbnails
- Automatically tries frame at 1 second (avoids black frames)
- Falls back to first frame if seeking fails

## Limitations (Current Version)

1. **No Content-Based Similarity**
   - Can't find duplicate videos by content
   - Only by filename/size

2. **No Quality Analysis**
   - No blur detection for videos
   - No exposure analysis

3. **No Scene Detection**
   - Can't split videos into scenes
   - No automatic highlight detection

4. **No Transcoding**
   - Can't convert between formats
   - Can't generate proxies

## Future Roadmap

### v0.3 - Video Analysis

- Duplicate detection (content-based)
- Scene detection
- Quality metrics (resolution, bitrate)
- Frame sampling for analysis

### v1.0 - Advanced Video

- Automatic highlight detection
- Proxy generation
- Timeline integration
- Advanced filtering

## Examples

### Example 1: Mixed Lumix S5 DCIM

```powershell
# Setup workspace
photo-tool workspace init D:\Lumix_Jan2024 --root "F:\Lumix\DCIM"

# Edit config to include videos
# config.yaml: extensions: [".jpg", ".mp4", ".mov"]

# Scan
photo-tool scan

# Output:
# ✓ Found 856 files:
#   Photos: 723
#   Videos: 133

# Analyze photos
photo-tool analyze bursts
# Note: Skipping 133 video files

# Organize photos into bursts
photo-tool organize bursts --apply

# List all videos
photo-tool video list --sort duration

# View specific video
photo-tool video info F:\Lumix\DCIM\100_PANA\VIDEO001.mp4
```

### Example 2: Video-Only Workspace

```powershell
# Workspace only for videos
photo-tool workspace init D:\Videos_Workspace

# Edit config
# config.yaml:
scan:
  roots: ["F:/Lumix/DCIM"]
  extensions: [".mp4", ".mov"]  # Videos only

# Scan
photo-tool scan
# ✓ Found 133 files:
#   Photos: 0
#   Videos: 133

# List sorted by date
photo-tool video list --sort date

# List sorted by size (find large files)
photo-tool video list --sort size
```

### Example 3: Rate Videos for DaVinci

```powershell
# View all videos
photo-tool video list

# Rate the good ones
photo-tool rate F:\Lumix\VIDEO001.mp4 --stars 5
photo-tool rate F:\Lumix\VIDEO003.mp4 --stars 5
photo-tool rate F:\Lumix\VIDEO007.mp4 --stars 4

# Mark bad ones
photo-tool rate F:\Lumix\VIDEO002.mp4 --stars 1

# Later: Import only 4-5 star videos to DaVinci Resolve
```

## Troubleshooting

### ffprobe not found

```
Warning: ffprobe not found!
Install ffmpeg to get detailed video information
```

**Solution:** Install ffmpeg (see Installation Requirements above)

### Cannot read video frame

```
Error: Could not read frame from video
```

**Possible causes:**
- Video file corrupted
- Unsupported codec
- Missing codec in OpenCV

**Solution:** Check video plays in VLC or similar player

### Slow thumbnail generation

**First time:** Thumbnails are generated and cached
**Subsequent runs:** Uses cached thumbnails (fast)

**Tip:** Generate thumbnails in background:
```powershell
photo-tool scan --workspace D:\MyWorkspace
# Thumbnails generated during scan
```

## FAQs

**Q: Will this slow down photo analysis?**
A: No, videos are automatically filtered out for photo-specific operations.

**Q: Can I use this without ffmpeg?**
A: Yes, but you'll get limited metadata. Thumbnails still work.

**Q: Does it support RAW video from Lumix S5?**
A: .mov files yes, but not ProRes RAW or Blackmagic RAW yet.

**Q: Can I edit videos?**
A: No, Photo Tool is for management only. Use DaVinci Resolve for editing.

**Q: Does it work with drone videos (DJI)?**
A: Yes, .mp4 and .mov formats work fine.

## See Also

- [GETTING_STARTED.md](GETTING_STARTED.md) - General usage guide
- [README.md](README.md) - Main documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details

---

**Video Support Status:** ✅ v0.2 - Basic functionality available!
