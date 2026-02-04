"""
Audio metadata extraction using ffprobe
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from ..util.logging import get_logger


logger = get_logger("audio_metadata")


def extract_audio_metadata(audio_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from audio file using ffprobe
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Dictionary with audio metadata
    """
    from .video_metadata import is_ffprobe_available
    
    if not is_ffprobe_available():
        logger.warning(
            "ffprobe not found. Install ffmpeg to extract audio metadata."
        )
        return _get_basic_audio_info(audio_path)
    
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(audio_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        data = json.loads(result.stdout)
        return _parse_audio_ffprobe_output(data, audio_path)
    
    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe failed for {audio_path}: {e}")
        return _get_basic_audio_info(audio_path)
    except json.JSONDecodeError as e:
        logger.error(f"Could not parse ffprobe output for {audio_path}: {e}")
        return _get_basic_audio_info(audio_path)
    except Exception as e:
        logger.error(f"Error extracting audio metadata from {audio_path}: {e}")
        return _get_basic_audio_info(audio_path)


def _parse_audio_ffprobe_output(data: dict, audio_path: Path) -> Dict[str, Any]:
    """Parse ffprobe JSON output for audio"""
    metadata = {}
    
    # Format info
    format_info = data.get('format', {})
    metadata['duration'] = float(format_info.get('duration', 0))
    metadata['size_bytes'] = int(format_info.get('size', 0))
    metadata['bit_rate'] = int(format_info.get('bit_rate', 0))
    metadata['format_name'] = format_info.get('format_name', 'unknown')
    
    # Tags
    tags = format_info.get('tags', {})
    
    # Creation/recording time
    creation_time = (
        tags.get('creation_time') or 
        tags.get('date') or
        tags.get('year')
    )
    
    if creation_time:
        try:
            for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y']:
                try:
                    metadata['created_time'] = datetime.strptime(str(creation_time), fmt)
                    break
                except ValueError:
                    continue
        except Exception as e:
            logger.debug(f"Could not parse creation time '{creation_time}': {e}")
    
    # Audio metadata tags
    metadata['title'] = tags.get('title', tags.get('Title', ''))
    metadata['artist'] = tags.get('artist', tags.get('Artist', ''))
    metadata['album'] = tags.get('album', tags.get('Album', ''))
    metadata['genre'] = tags.get('genre', tags.get('Genre', ''))
    metadata['comment'] = tags.get('comment', tags.get('Comment', ''))
    
    # Audio stream info
    audio_stream = None
    for stream in data.get('streams', []):
        if stream.get('codec_type') == 'audio':
            audio_stream = stream
            break
    
    if audio_stream:
        metadata['codec'] = audio_stream.get('codec_name', 'unknown')
        metadata['sample_rate'] = int(audio_stream.get('sample_rate', 0))
        metadata['channels'] = int(audio_stream.get('channels', 0))
        metadata['channel_layout'] = audio_stream.get('channel_layout', 'unknown')
    
    return metadata


def _get_basic_audio_info(audio_path: Path) -> Dict[str, Any]:
    """Get basic audio info without ffprobe (fallback)"""
    stat = audio_path.stat()
    
    return {
        'size_bytes': stat.st_size,
        'created_time': None,
        'duration': 0,
        'codec': 'unknown',
        'sample_rate': 0,
        'channels': 0,
        'channel_layout': 'unknown',
        'bit_rate': 0,
        'format_name': audio_path.suffix.lower()[1:],  # .mp3 -> mp3
        'title': '',
        'artist': '',
        'album': '',
        'genre': '',
        'comment': ''
    }


def get_audio_capture_time(audio_path: Path, fallback_to_mtime: bool = True) -> Optional[datetime]:
    """
    Get audio recording/creation time from metadata or file modification time
    
    Args:
        audio_path: Path to audio file
        fallback_to_mtime: Use file modification time if metadata not available
        
    Returns:
        Datetime object or None
    """
    metadata = extract_audio_metadata(audio_path)
    
    # Try metadata first
    if 'created_time' in metadata and metadata['created_time']:
        return metadata['created_time']
    
    # Fallback to file modification time
    if fallback_to_mtime:
        stat = audio_path.stat()
        return datetime.fromtimestamp(stat.st_mtime)
    
    return None


def format_sample_rate(sample_rate: int) -> str:
    """Format sample rate in human-readable format"""
    if sample_rate == 0:
        return "Unknown"
    
    if sample_rate >= 1000:
        return f"{sample_rate / 1000:.1f} kHz"
    return f"{sample_rate} Hz"


def format_channels(channels: int, layout: str = '') -> str:
    """Format channel info in human-readable format"""
    if channels == 0:
        return "Unknown"
    
    # Common layouts
    if channels == 1:
        return "Mono"
    elif channels == 2:
        return "Stereo"
    elif channels == 6 and 'surround' in layout.lower():
        return "5.1 Surround"
    elif channels == 8 and 'surround' in layout.lower():
        return "7.1 Surround"
    else:
        return f"{channels} channels"
