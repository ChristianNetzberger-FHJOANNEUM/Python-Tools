"""
EXIF metadata extraction
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from PIL import Image
from PIL.ExifTags import TAGS
import exifread

from ..util.logging import get_logger


logger = get_logger("exif")


def extract_exif(image_path: Path) -> Dict[str, Any]:
    """
    Extract EXIF metadata from image
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dictionary of EXIF tags
    """
    exif_data = {}
    
    try:
        # Try PIL first (faster for basic EXIF)
        with Image.open(image_path) as img:
            exif = img.getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value
        
        # If we need more detailed EXIF, use exifread
        if not exif_data:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                exif_data = {k: str(v) for k, v in tags.items()}
    
    except Exception as e:
        logger.debug(f"Could not read EXIF from {image_path}: {e}")
    
    return exif_data


def get_capture_time(image_path: Path, fallback_to_mtime: bool = True) -> Optional[datetime]:
    """
    Get photo capture time from EXIF or file modification time
    
    Args:
        image_path: Path to image
        fallback_to_mtime: Use file modification time if EXIF not available
        
    Returns:
        Datetime object or None
    """
    exif = extract_exif(image_path)
    
    # Try various EXIF date fields
    date_fields = [
        'DateTimeOriginal',
        'DateTime',
        'DateTimeDigitized',
        'EXIF DateTimeOriginal',
        'EXIF DateTime',
        'EXIF DateTimeDigitized'
    ]
    
    for field in date_fields:
        if field in exif:
            try:
                date_str = str(exif[field])
                # EXIF format: "YYYY:MM:DD HH:MM:SS"
                return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            except ValueError:
                try:
                    # Try alternative format
                    return datetime.strptime(date_str.split()[0], "%Y:%m:%d")
                except:
                    continue
    
    # Fallback to file modification time
    if fallback_to_mtime:
        stat = image_path.stat()
        return datetime.fromtimestamp(stat.st_mtime)
    
    return None


def get_camera_info(image_path: Path) -> Dict[str, Optional[str]]:
    """
    Extract camera and lens information
    
    Returns:
        Dict with camera_model, lens_model, etc.
    """
    exif = extract_exif(image_path)
    
    return {
        'camera_model': exif.get('Model') or exif.get('EXIF Model'),
        'lens_model': exif.get('LensModel') or exif.get('EXIF LensModel'),
        'focal_length': exif.get('FocalLength') or exif.get('EXIF FocalLength'),
        'aperture': exif.get('FNumber') or exif.get('EXIF FNumber'),
        'iso': exif.get('ISOSpeedRatings') or exif.get('EXIF ISOSpeedRatings'),
        'shutter_speed': exif.get('ExposureTime') or exif.get('EXIF ExposureTime'),
    }


def get_image_dimensions(image_path: Path) -> tuple[int, int]:
    """
    Get image width and height
    
    Returns:
        (width, height) tuple
    """
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        logger.debug(f"Could not read dimensions from {image_path}: {e}")
        return (0, 0)


def get_gps_coordinates(image_path: Path) -> Optional[Dict[str, float]]:
    """
    Extract GPS coordinates from EXIF
    
    Returns:
        Dict with 'latitude' and 'longitude' or None
    """
    exif = extract_exif(image_path)
    
    try:
        # Look for GPS info in EXIF
        gps_latitude = exif.get('GPSLatitude') or exif.get('GPS GPSLatitude')
        gps_latitude_ref = exif.get('GPSLatitudeRef') or exif.get('GPS GPSLatitudeRef')
        gps_longitude = exif.get('GPSLongitude') or exif.get('GPS GPSLongitude')
        gps_longitude_ref = exif.get('GPSLongitudeRef') or exif.get('GPS GPSLongitudeRef')
        
        if not (gps_latitude and gps_longitude):
            return None
        
        # Convert to decimal degrees
        def dms_to_decimal(dms, ref):
            """Convert degrees, minutes, seconds to decimal"""
            if isinstance(dms, str):
                # Parse string format: "[47, 15, 30.5]"
                parts = dms.strip('[]').split(',')
                degrees = float(parts[0])
                minutes = float(parts[1]) if len(parts) > 1 else 0
                seconds = float(parts[2]) if len(parts) > 2 else 0
            else:
                # Assume tuple/list
                degrees = float(dms[0])
                minutes = float(dms[1]) if len(dms) > 1 else 0
                seconds = float(dms[2]) if len(dms) > 2 else 0
            
            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
            
            if ref in ['S', 'W']:
                decimal = -decimal
            
            return decimal
        
        lat = dms_to_decimal(gps_latitude, gps_latitude_ref)
        lon = dms_to_decimal(gps_longitude, gps_longitude_ref)
        
        return {
            'latitude': lat,
            'longitude': lon
        }
    
    except Exception as e:
        logger.debug(f"Could not extract GPS from {image_path}: {e}")
        return None


def get_keywords(image_path: Path) -> list[str]:
    """
    Extract keywords/tags from EXIF/IPTC
    
    Returns:
        List of keywords
    """
    exif = extract_exif(image_path)
    keywords = []
    
    # Check various keyword fields
    keyword_fields = [
        'Keywords',
        'IPTC Keywords',
        'XPKeywords',
        'Subject',
    ]
    
    for field in keyword_fields:
        if field in exif:
            value = exif[field]
            if isinstance(value, str):
                # Split by common delimiters
                keywords.extend([k.strip() for k in value.replace(';', ',').split(',') if k.strip()])
            elif isinstance(value, (list, tuple)):
                keywords.extend([str(k).strip() for k in value if str(k).strip()])
    
    return list(set(keywords))  # Remove duplicates
