"""
Image optimization profiles for different export targets
Supports Smart TV (NAS), Web, and custom profiles
"""

from dataclasses import dataclass
from typing import Optional, Literal
from pathlib import Path

from PIL import Image

from ..util.logging import get_logger

logger = get_logger("export_profiles")


ExportTarget = Literal["smart_tv", "web", "web_optimized", "archive", "custom"]


@dataclass
class ImageProfile:
    """Image optimization profile"""
    name: str
    max_width: int
    max_height: int
    jpeg_quality: int
    webp_quality: Optional[int] = None  # If set, also export WebP
    progressive: bool = True
    optimize: bool = True
    thumbnail_size: int = 400
    thumbnail_quality: int = 80
    description: str = ""


# Predefined export profiles
EXPORT_PROFILES = {
    "smart_tv": ImageProfile(
        name="Smart TV (4K/Full HD)",
        max_width=3840,
        max_height=2160,
        jpeg_quality=92,
        webp_quality=None,  # TVs often don't support WebP
        progressive=True,
        optimize=True,
        thumbnail_size=600,
        thumbnail_quality=85,
        description="High-quality images for Samsung/LG Smart TV via NAS"
    ),
    
    "smart_tv_fullhd": ImageProfile(
        name="Smart TV (Full HD)",
        max_width=1920,
        max_height=1080,
        jpeg_quality=90,
        webp_quality=None,
        progressive=True,
        optimize=True,
        thumbnail_size=500,
        thumbnail_quality=85,
        description="Full HD images for Smart TV (smaller files)"
    ),
    
    "web": ImageProfile(
        name="Web Gallery",
        max_width=1920,
        max_height=1280,
        jpeg_quality=85,
        webp_quality=None,
        progressive=True,
        optimize=True,
        thumbnail_size=400,
        thumbnail_quality=80,
        description="Standard web gallery (good balance)"
    ),
    
    "web_optimized": ImageProfile(
        name="Web Optimized",
        max_width=1600,
        max_height=1200,
        jpeg_quality=80,
        webp_quality=85,  # Generate WebP + JPEG
        progressive=True,
        optimize=True,
        thumbnail_size=400,
        thumbnail_quality=75,
        description="Highly optimized for web (WebP + JPEG fallback)"
    ),
    
    "archive": ImageProfile(
        name="Archive Quality",
        max_width=4000,
        max_height=4000,
        jpeg_quality=95,
        webp_quality=None,
        progressive=False,
        optimize=True,
        thumbnail_size=600,
        thumbnail_quality=90,
        description="High quality for archival purposes"
    ),
}


def optimize_image(
    source_path: Path,
    output_path: Path,
    profile: ImageProfile,
    generate_webp: bool = False
) -> dict:
    """
    Optimize image according to profile
    
    Args:
        source_path: Source image path
        output_path: Output JPEG path
        profile: Optimization profile
        generate_webp: Also generate WebP version
        
    Returns:
        Dict with file sizes and paths
    """
    result = {
        'jpeg_path': output_path,
        'jpeg_size': 0,
        'webp_path': None,
        'webp_size': 0,
        'original_size': source_path.stat().st_size,
        'width': 0,
        'height': 0
    }
    
    try:
        with Image.open(source_path) as img:
            # Get original dimensions
            orig_width, orig_height = img.size
            
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                    img = background
                else:
                    img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Apply EXIF orientation
            try:
                exif = img.getexif()
                if exif:
                    orientation = exif.get(0x0112)
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
            except:
                pass
            
            # Resize if needed
            width, height = img.size
            if width > profile.max_width or height > profile.max_height:
                # Calculate new size maintaining aspect ratio
                ratio = min(profile.max_width / width, profile.max_height / height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                width, height = new_size
            
            result['width'] = width
            result['height'] = height
            
            # Save JPEG
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            save_kwargs = {
                'format': 'JPEG',
                'quality': profile.jpeg_quality,
                'optimize': profile.optimize
            }
            
            if profile.progressive:
                save_kwargs['progressive'] = True
            
            img.save(output_path, **save_kwargs)
            result['jpeg_size'] = output_path.stat().st_size
            
            # Save WebP if requested
            if generate_webp and profile.webp_quality:
                webp_path = output_path.with_suffix('.webp')
                img.save(
                    webp_path,
                    format='WEBP',
                    quality=profile.webp_quality,
                    method=4  # Compression method (0-6, higher = slower but better)
                )
                result['webp_path'] = webp_path
                result['webp_size'] = webp_path.stat().st_size
        
        # Log compression stats
        compression_ratio = (1 - result['jpeg_size'] / result['original_size']) * 100
        logger.debug(
            f"Optimized {source_path.name}: "
            f"{result['original_size']//1024}KB → {result['jpeg_size']//1024}KB "
            f"({compression_ratio:.1f}% reduction)"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to optimize {source_path}: {e}")
        raise


def generate_optimized_thumbnail(
    source_path: Path,
    output_path: Path,
    profile: ImageProfile,
    generate_webp: bool = False
) -> dict:
    """
    Generate optimized thumbnail
    
    Args:
        source_path: Source image path
        output_path: Output thumbnail path (JPEG)
        profile: Optimization profile
        generate_webp: Also generate WebP version
        
    Returns:
        Dict with file info
    """
    result = {
        'jpeg_path': output_path,
        'jpeg_size': 0,
        'webp_path': None,
        'webp_size': 0
    }
    
    try:
        with Image.open(source_path) as img:
            # Convert to RGB
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                    img = background
                else:
                    img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Apply EXIF orientation
            try:
                exif = img.getexif()
                if exif:
                    orientation = exif.get(0x0112)
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
            except:
                pass
            
            # Create thumbnail
            size = (profile.thumbnail_size, profile.thumbnail_size)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save JPEG
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(
                output_path,
                format='JPEG',
                quality=profile.thumbnail_quality,
                optimize=True
            )
            result['jpeg_size'] = output_path.stat().st_size
            
            # Save WebP if requested
            if generate_webp and profile.webp_quality:
                webp_path = output_path.with_suffix('.webp')
                img.save(
                    webp_path,
                    format='WEBP',
                    quality=profile.thumbnail_quality,
                    method=4
                )
                result['webp_path'] = webp_path
                result['webp_size'] = webp_path.stat().st_size
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate thumbnail for {source_path}: {e}")
        raise


def get_profile(target: str) -> ImageProfile:
    """
    Get export profile by name
    
    Args:
        target: Profile name (smart_tv, web, web_optimized, etc.)
        
    Returns:
        ImageProfile instance
        
    Raises:
        ValueError if profile not found
    """
    if target not in EXPORT_PROFILES:
        available = ", ".join(EXPORT_PROFILES.keys())
        raise ValueError(f"Unknown profile '{target}'. Available: {available}")
    
    return EXPORT_PROFILES[target]


def list_profiles() -> dict:
    """
    List all available export profiles
    
    Returns:
        Dict of profile names and descriptions
    """
    return {
        name: {
            'name': profile.name,
            'description': profile.description,
            'max_resolution': f"{profile.max_width}×{profile.max_height}",
            'jpeg_quality': profile.jpeg_quality,
            'webp_support': profile.webp_quality is not None,
            'thumbnail_size': profile.thumbnail_size
        }
        for name, profile in EXPORT_PROFILES.items()
    }
