"""
Video metadata extraction using ffprobe
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from ..util.logging import get_logger


logger = get_logger("video_metadata")


def is_ffprobe_available() -> bool:
    """Check if ffprobe is available in PATH"""
    try:
        subprocess.run(
            ['ffprobe', '-version'],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def extract_video_metadata(video_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from video file using ffprobe
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dictionary with video metadata
        
    Raises:
        RuntimeError: If ffprobe is not available
        ValueError: If video cannot be read
    """
    if not is_ffprobe_available():
        logger.warning(
            "ffprobe not found. Install ffmpeg to extract video metadata. "
            "Download from: https://ffmpeg.org/download.html"
        )
        return _get_basic_video_info(video_path)
    
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        data = json.loads(result.stdout)
        return _parse_ffprobe_output(data, video_path)
    
    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe failed for {video_path}: {e}")
        return _get_basic_video_info(video_path)
    except json.JSONDecodeError as e:
        logger.error(f"Could not parse ffprobe output for {video_path}: {e}")
        return _get_basic_video_info(video_path)
    except Exception as e:
        logger.error(f"Error extracting video metadata from {video_path}: {e}")
        return _get_basic_video_info(video_path)


def _parse_ffprobe_output(data: dict, video_path: Path) -> Dict[str, Any]:
    """Parse ffprobe JSON output"""
    metadata = {}
    
    # Format info
    format_info = data.get('format', {})
    metadata['duration'] = float(format_info.get('duration', 0))
    metadata['size_bytes'] = int(format_info.get('size', 0))
    metadata['bit_rate'] = int(format_info.get('bit_rate', 0))
    metadata['format_name'] = format_info.get('format_name', 'unknown')
    
    # Creation time
    tags = format_info.get('tags', {})
    creation_time = (
        tags.get('creation_time') or 
        tags.get('com.apple.quicktime.creationdate') or
        tags.get('date')
    )
    
    if creation_time:
        try:
            # Try different datetime formats
            for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    metadata['created_time'] = datetime.strptime(creation_time, fmt)
                    break
                except ValueError:
                    continue
        except Exception as e:
            logger.debug(f"Could not parse creation time '{creation_time}': {e}")
    
    # Video stream info
    video_stream = None
    for stream in data.get('streams', []):
        if stream.get('codec_type') == 'video':
            video_stream = stream
            break
    
    if video_stream:
        metadata['width'] = int(video_stream.get('width', 0))
        metadata['height'] = int(video_stream.get('height', 0))
        metadata['codec'] = video_stream.get('codec_name', 'unknown')
        metadata['fps'] = _parse_frame_rate(video_stream.get('r_frame_rate', '0/1'))
    
    return metadata


def _parse_frame_rate(fps_string: str) -> float:
    """Parse frame rate string like '30000/1001' to float"""
    try:
        if '/' in fps_string:
            num, den = fps_string.split('/')
            return float(num) / float(den)
        return float(fps_string)
    except:
        return 0.0


def _get_basic_video_info(video_path: Path) -> Dict[str, Any]:
    """Get basic video info without ffprobe (fallback)"""
    stat = video_path.stat()
    
    return {
        'size_bytes': stat.st_size,
        'created_time': None,
        'duration': 0,
        'width': 0,
        'height': 0,
        'codec': 'unknown',
        'fps': 0.0,
        'bit_rate': 0,
        'format_name': video_path.suffix.lower()[1:]  # .mp4 -> mp4
    }


def get_video_capture_time(video_path: Path, fallback_to_mtime: bool = True) -> Optional[datetime]:
    """
    Get video capture time from metadata or file modification time
    
    Args:
        video_path: Path to video
        fallback_to_mtime: Use file modification time if metadata not available
        
    Returns:
        Datetime object or None
    """
    metadata = extract_video_metadata(video_path)
    
    # Try metadata first
    if 'created_time' in metadata and metadata['created_time']:
        return metadata['created_time']
    
    # Fallback to file modification time
    if fallback_to_mtime:
        stat = video_path.stat()
        return datetime.fromtimestamp(stat.st_mtime)
    
    return None


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format (HH:MM:SS)"""
    if seconds <= 0:
        return "00:00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
