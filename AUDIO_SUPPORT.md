# Audio Support in Photo Tool

Photo Tool v0.2.1+ includes audio file management capabilities, perfect for managing complete DaVinci Resolve projects (video + audio) or organizing music libraries alongside photos.

## Features (v0.2.1 - Audio Basics)

### ✅ What Works

- **Scanning**: Find and index audio files (.mp3, .wav, .m4a, .flac, etc.)
- **Metadata Extraction**: Read title, artist, album, duration, sample rate, codec
- **Rating/Tagging**: Rate and tag audio files for later use
- **Time-based Organization**: Sort and organize by recording date
- **Mixed Media**: Handle photos, videos, AND audio in the same workspace

### ⚠️ What Doesn't Work Yet

- **Waveform Visualization**: Not implemented yet
- **Audio Similarity Detection**: Not implemented yet
- **Duplicate Detection**: Basic (size/name), not content-based
- **Transcoding**: Not supported

## Installation Requirements

### For Full Audio Support

Install **ffmpeg** (includes ffprobe for metadata extraction):

**Windows:**
```powershell
winget install ffmpeg
```

See [INSTALL_FFMPEG.md](INSTALL_FFMPEG.md) for detailed installation instructions.

### Without ffmpeg

Photo Tool will still work but with limited audio metadata:
- File size, modification date
- No duration, sample rate, codec info
- No ID3 tags (title, artist, album)

## Configuration

### Add Audio Extensions

Edit your workspace `config.yaml`:

```yaml
scan:
  roots:
    - "F:/Lumix/DCIM"      # Videos + photos
    - "F:/Audio"           # Audio recordings
    - "D:/Music"           # Music library
  extensions:
    - ".jpg"
    - ".jpeg"
    - ".mp4"
    - ".mov"
    - ".mp3"               # MP3 audio
    - ".wav"               # WAV uncompressed
    - ".m4a"               # AAC audio
    - ".flac"              # Lossless
    - ".ogg"               # Ogg Vorbis
  recurse: true
```

### DaVinci Resolve Setup

For complete project management:

```yaml
scan:
  roots:
    - "F:/Project/Video"   # Video clips
    - "F:/Project/Audio"   # Audio recordings, music
  extensions:
    # Video
    - ".mp4"
    - ".mov"
    # Audio
    - ".mp3"
    - ".wav"               # DaVinci prefers WAV
    - ".aac"
  recurse: true
```

## Usage

### Scan Mixed Media

```powershell
# Scan for photos, videos, AND audio
photo-tool scan --workspace D:\MyWorkspace

# Output shows:
# ✓ Found 1523 files:
#   Photos: 450
#   Videos: 73
#   Audio: 1000
```

### Audio-Specific Commands

```powershell
# Show detailed audio info
photo-tool audio info F:\Audio\recording.mp3

# List all audio files with metadata
photo-tool audio list --workspace D:\MyWorkspace

# Sort by duration
photo-tool audio list --sort duration

# Sort by size
photo-tool audio list --sort size
```

### Audio Information Display

```
Audio information for: recording.mp3

Filename      recording.mp3
Path          F:\Audio
Size          4.2 MB
Date          2024-12-25 14:30:45
Duration      00:03:45
Title         My Recording
Artist        John Doe
Album         Field Recordings 2024
Genre         Ambient
Sample Rate   48.0 kHz
Channels      Stereo
Codec         mp3
Bit Rate      320 kbps
Format        mp3
```

### Rating Audio Files

```powershell
# Rate audio for later use
photo-tool rate set F:\Audio\recording.mp3 --stars 5 --comment "Perfect take"
photo-tool rate set F:\Audio\ambient.wav --stars 4

# View rating
photo-tool rate get F:\Audio\recording.mp3
# ⭐⭐⭐⭐⭐ (5/5)
# Comment: Perfect take
```

### Mixed Workflows

```powershell
# Scan everything
photo-tool scan --workspace D:\MyWorkspace

# Analyze photos (videos/audio automatically skipped)
photo-tool analyze bursts
# Note: Skipping 1073 video/audio files

# Organize photos (videos/audio untouched)
photo-tool organize bursts --apply

# View all audio
photo-tool audio list --sort duration

# View all videos
photo-tool video list --sort date
```

## DaVinci Resolve Workflow

Perfect for organizing complete project assets before importing:

### 1. Project Setup

```powershell
# Create workspace for project
photo-tool workspace init D:\Project_Workspace

# Edit config
# config.yaml:
scan:
  roots:
    - "F:/Footage"       # Video clips
    - "F:/Audio"         # Audio files
  extensions: [".mp4", ".mov", ".wav", ".mp3"]
```

### 2. Scan and Organize

```powershell
# Scan all media
photo-tool scan --workspace D:\Project_Workspace
# ✓ Found 523 files:
#   Videos: 194
#   Audio: 329

# List videos
photo-tool video list --sort duration

# List audio
photo-tool audio list --sort duration
```

### 3. Rate and Tag

```powershell
# Rate best video clips
photo-tool rate set F:\Footage\CLIP001.mp4 --stars 5
photo-tool rate set F:\Footage\CLIP007.mp4 --stars 5

# Rate audio tracks
photo-tool rate set F:\Audio\music_intro.wav --stars 5 --comment "Intro music"
photo-tool rate set F:\Audio\sfx_wind.wav --stars 4 --comment "Background ambience"
photo-tool rate set F:\Audio\voiceover.wav --stars 5 --comment "Final take"
```

### 4. Export for DaVinci

```python
# export_for_davinci.py
from pathlib import Path
from photo_tool.actions.rating import get_rating
import shutil

# Collect rated media
video_source = Path("F:/Footage")
audio_source = Path("F:/Audio")
target = Path("D:/DaVinci/Import")

# Copy 4-5 star videos
for video in video_source.rglob("*.mp4"):
    rating = get_rating(video)
    if rating and rating >= 4:
        shutil.copy2(video, target / "video" / video.name)

# Copy 4-5 star audio
for audio in audio_source.rglob("*.wav"):
    rating = get_rating(audio)
    if rating and rating >= 4:
        shutil.copy2(audio, target / "audio" / audio.name)
```

## Supported Audio Formats

| Format | Extension | Common Use | Metadata | DaVinci |
|--------|-----------|------------|----------|---------|
| **MP3** | .mp3 | Music, voice | ✅ ID3 | ⚠️ OK |
| **WAV** | .wav | Professional audio | ⚠️ Limited | ✅ Best |
| **M4A/AAC** | .m4a, .aac | iTunes, modern | ✅ | ✅ Good |
| **FLAC** | .flac | Lossless music | ✅ | ⚠️ Convert |
| **OGG** | .ogg | Open source | ✅ | ❌ Convert |
| **OPUS** | .opus | Modern efficient | ✅ | ❌ Convert |
| **WMA** | .wma | Windows | ⚠️ | ⚠️ Convert |

**DaVinci Resolve Recommendation:** Use WAV or AAC for best compatibility.

## Metadata Extraction

### With ffprobe (Recommended)

```
Title:         My Song
Artist:        Artist Name
Album:         Album Title
Genre:         Rock
Duration:      00:03:45
Sample Rate:   48.0 kHz
Channels:      Stereo
Codec:         mp3
Bit Rate:      320 kbps
```

### Without ffprobe (Fallback)

```
Size:          4.2 MB
Date:          2024-12-25 14:30:45
```

## Use Cases

### 1. Music Library Organization

```powershell
# Create workspace for music
photo-tool workspace init D:\Music_Library --root "D:\Music"

# Add audio extensions
# config.yaml: extensions: [".mp3", ".flac", ".m4a"]

# Scan
photo-tool scan
# ✓ Found 5000 files:
#   Audio: 5000

# List by artist/title
photo-tool audio list --sort name

# Rate favorites
photo-tool rate set "Best Song.mp3" --stars 5
```

### 2. Field Recordings

```powershell
# Workspace for recordings
photo-tool workspace init D:\Recordings --root "F:\Recorder"

# Scan
photo-tool scan
# ✓ Found 47 files:
#   Audio: 47

# List by date
photo-tool audio list --sort date

# Rate and comment
photo-tool rate set recording_001.wav --stars 5 --comment "Perfect nature ambience"
photo-tool rate set recording_002.wav --stars 3 --comment "Too much wind"
```

### 3. Podcast Production

```powershell
# Workspace for podcast episode
photo-tool workspace init D:\Podcast_Ep05

# Scan raw recordings
photo-tool scan
# ✓ Found 12 files:
#   Audio: 12

# Show info
photo-tool audio info host_intro.wav
photo-tool audio info guest_interview.wav
photo-tool audio info music_outro.mp3

# Rate takes
photo-tool rate set host_intro_take2.wav --stars 5 --comment "Best take"
photo-tool rate set host_intro_take1.wav --stars 2 --comment "Too many ums"
```

### 4. Complete DaVinci Project

```powershell
# Mixed media workspace
photo-tool workspace init D:\Film_Project

# config.yaml:
scan:
  roots:
    - "F:/Video"
    - "F:/Audio"
    - "F:/Photos"  # Stills for B-roll
  extensions: [".mp4", ".mov", ".jpg", ".wav", ".mp3"]

# Scan
photo-tool scan
# ✓ Found 856 files:
#   Photos: 123
#   Videos: 194
#   Audio: 539

# Organize by type
photo-tool video list --sort date
photo-tool audio list --sort duration
photo-tool scan  # See photos count

# Rate everything
photo-tool rate set VIDEO001.mp4 --stars 5
photo-tool rate set music_intro.wav --stars 5
photo-tool rate set photo_001.jpg --stars 4
```

## Technical Details

### Sample Rates

Common audio sample rates:
- **44.1 kHz** - CD quality, music
- **48.0 kHz** - Video standard, DaVinci default
- **96.0 kHz** - High-res audio
- **192.0 kHz** - Audiophile, overkill for video

### Bit Rates

MP3 bit rates:
- **128 kbps** - Low quality
- **192 kbps** - Acceptable
- **256 kbps** - Good
- **320 kbps** - Maximum MP3 quality

### Channels

- **Mono (1 channel)** - Voice recordings, phone
- **Stereo (2 channels)** - Music, most video
- **5.1 Surround (6 channels)** - Cinema
- **7.1 Surround (8 channels)** - High-end cinema

## Limitations (Current Version)

1. **No Waveform Display**
   - Can't visualize audio
   - Command-line only

2. **No Content-Based Similarity**
   - Can't find similar sounding audio
   - No duplicate detection by content

3. **No Audio Processing**
   - Can't normalize levels
   - Can't convert formats
   - Can't trim/edit

4. **No Playlist Management**
   - Can't create playlists
   - Can't export M3U

## Future Roadmap

### v0.3 - Enhanced Audio

- Waveform visualization
- Peak level detection
- Silence detection
- Content-based duplicate detection

### v1.0 - Advanced Features

- Audio transcoding
- Batch normalization
- Playlist management
- Integration with DAWs

## Examples

### Example 1: Music Library

```powershell
# Setup
photo-tool workspace init D:\Music --root "D:\Music"

# Config: extensions: [".mp3", ".flac"]

# Scan
photo-tool scan
# ✓ Found 5000 files:
#   Audio: 5000

# View all
photo-tool audio list

# Find longest tracks
photo-tool audio list --sort duration

# Rate favorites
photo-tool rate set "favorite_song.mp3" --stars 5
```

### Example 2: DaVinci Resolve Audio Library

```powershell
# Setup workspace
photo-tool workspace init D:\Audio_Library

# config.yaml:
scan:
  roots:
    - "F:/Audio/Music"
    - "F:/Audio/SFX"
    - "F:/Audio/Voiceover"
  extensions: [".wav", ".mp3", ".aac"]

# Scan
photo-tool scan
# ✓ Found 1234 files:
#   Audio: 1234

# Browse by category (based on folder)
photo-tool audio list --sort name

# Rate for project
photo-tool rate set music_intro.wav --stars 5 --comment "Project intro"
photo-tool rate set sfx_door.wav --stars 4 --comment "Scene 3"
```

### Example 3: Field Recording Session

```powershell
# After recording session
photo-tool workspace init D:\Recording_Session_2024-02-04

# Scan from recorder
photo-tool scan --roots "F:\RECORDER\AUDIO"

# List by date/time
photo-tool audio list --sort date

# Review and rate
photo-tool audio info AUDIO001.wav
photo-tool rate set AUDIO001.wav --stars 5 --comment "Perfect take - use this"

photo-tool audio info AUDIO002.wav
photo-tool rate set AUDIO002.wav --stars 2 --comment "Wind noise"
```

## Troubleshooting

### ffprobe not found

```
Warning: ffprobe not found!
Install ffmpeg to get detailed audio information
```

**Solution:** Install ffmpeg - see [INSTALL_FFMPEG.md](INSTALL_FFMPEG.md)

### No metadata shown

**Possible causes:**
- ffprobe not installed
- Audio file has no embedded metadata
- Unsupported metadata format

**Solution:** 
- Install ffmpeg for best results
- Use proper audio tagging tools to add metadata

### "Unknown codec"

**Cause:** Rare or proprietary audio codec

**Solution:**
- Try playing in VLC to verify file
- Consider converting to standard format (WAV, MP3)

## FAQs

**Q: Will this slow down photo analysis?**
A: No, audio files are automatically filtered out for photo-specific operations.

**Q: Can I use this without ffmpeg?**
A: Yes, but you'll get limited metadata. File size, date, and basic info still work.

**Q: Does it work with DRM-protected audio?**
A: No, DRM-protected files (iTunes M4P, etc.) are not supported.

**Q: Can I edit audio files?**
A: No, Photo Tool is for management only. Use Audacity or DaVinci Fairlight for editing.

**Q: Does it read playlists (M3U, PLS)?**
A: Not yet, coming in future versions.

**Q: Can I manage podcast libraries?**
A: Yes! Rate episodes, organize by date, comment on favorites.

## See Also

- [VIDEO_SUPPORT.md](VIDEO_SUPPORT.md) - Video file management
- [GETTING_STARTED.md](GETTING_STARTED.md) - General usage guide
- [LUMIX_S5_SETUP.md](LUMIX_S5_SETUP.md) - Camera-specific setup
- [INSTALL_FFMPEG.md](INSTALL_FFMPEG.md) - ffmpeg installation

---

**Audio Support Status:** ✅ v0.2.1 - Basic functionality available!  
**Perfect for:** DaVinci Resolve workflows, music organization, field recordings
