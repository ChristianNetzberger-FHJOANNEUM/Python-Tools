"""I/O operations: scanning, EXIF, thumbnails, video metadata, audio metadata"""

from .scanner import scan_directory, scan_multiple_directories, MediaFile, PhotoFile, filter_by_type
from .exif import extract_exif, get_capture_time, get_gps_coordinates, get_keywords
from .thumbnails import generate_thumbnail
from .video_metadata import (
    extract_video_metadata,
    get_video_capture_time,
    is_ffprobe_available,
    format_duration,
    format_file_size
)
from .audio_metadata import (
    extract_audio_metadata,
    get_audio_capture_time,
    format_sample_rate,
    format_channels
)

__all__ = [
    # Scanner
    "scan_directory",
    "scan_multiple_directories",
    "MediaFile",
    "PhotoFile",  # Backwards compatibility
    "filter_by_type",
    # EXIF
    "extract_exif",
    "get_capture_time",
    # Thumbnails
    "generate_thumbnail",
    # Video
    "extract_video_metadata",
    "get_video_capture_time",
    "is_ffprobe_available",
    "format_duration",
    "format_file_size",
    # Audio
    "extract_audio_metadata",
    "get_audio_capture_time",
    "format_sample_rate",
    "format_channels",
]
