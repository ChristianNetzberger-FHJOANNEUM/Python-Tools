"""
Web gallery export functionality
Export filtered photo selections as standalone HTML galleries
"""

import json
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from PIL import Image

from ..util.logging import get_logger
from .metadata import get_metadata
from .export_profiles import get_profile, optimize_image, generate_optimized_thumbnail, list_profiles

logger = get_logger("export")

# Progress tracking for export
_export_progress = {
    'status': 'idle',  # idle, running, complete, error
    'current': 0,
    'total': 0,
    'step': '',
    'message': ''
}


def export_gallery(
    photo_paths: List[Path],
    output_dir: Path,
    title: str = "Photo Gallery",
    template: str = "photoswipe",
    profile: str = "web",
    include_metadata: bool = True,
    generate_webp: bool = False,
    quick_update: bool = False,  # NEW: Skip image processing, only regenerate HTML
    music_files: Optional[List[str]] = None,
    music_autoplay: bool = False,  # NEW: Auto-start music on load
    music_ducking_volume: int = 30,  # NEW: Music volume during pause (0-100%)
    slideshow_enabled: bool = False,
    slideshow_duration: int = 5,
    smart_tv_mode: bool = False,
    splash_title: Optional[str] = None,      # 🎬 Custom splash screen title
    splash_subtitle: Optional[str] = None,   # 🎬 Custom splash screen subtitle
    apply_edits: bool = True,  # NEW: Apply non-destructive edits during export
    # Legacy parameters (deprecated, use profile instead)
    max_image_size: Optional[int] = None,
    thumbnail_size: Optional[int] = None
) -> Path:
    """
    Export photos as standalone web gallery with optimization profiles
    
    Args:
        photo_paths: List of photo paths to include
        output_dir: Output directory for gallery
        title: Gallery title
        template: Template name (photoswipe, simple, slideshow)
        profile: Export profile (smart_tv, web, web_optimized, archive)
        include_metadata: Include ratings, colors, keywords
        generate_webp: Generate WebP versions in addition to JPEG
        music_files: Optional list of music file paths for slideshow
        music_autoplay: Auto-start music on page load (default: False)
        slideshow_enabled: Enable slideshow mode
        slideshow_duration: Duration per photo in seconds (2-15)
        smart_tv_mode: Enable large buttons for Smart TV
        max_image_size: (Deprecated) Use profile instead
        thumbnail_size: (Deprecated) Use profile instead
        
    Returns:
        Path to generated gallery directory
        
    Profiles:
        - smart_tv: 4K quality for Samsung/LG TVs (3840×2160, Q92)
        - smart_tv_fullhd: Full HD for TVs (1920×1080, Q90)
        - web: Standard web gallery (1920×1280, Q85, ~650 KB/photo)
        - web_medium: Medium web gallery (1600×1067, Q83, ~400 KB/photo)
        - web_compact: Compact web gallery (1280×853, Q80, ~250 KB/photo)
        - web_mobile: Mobile-friendly gallery (1024×683, Q78, ~150 KB/photo)
        - web_optimized: Highly optimized (1600×1200, Q80, WebP)
        - archive: High quality archive (4000×4000, Q95)
    """
    
    global _export_progress
    
    # Get export profile
    try:
        export_profile = get_profile(profile)
        logger.info(f"Using export profile: {export_profile.name}")
        logger.info(f"Profile: {export_profile.description}")
    except ValueError as e:
        logger.error(f"Invalid profile: {e}")
        # Fallback to web profile
        export_profile = get_profile("web")
        logger.warning(f"Falling back to 'web' profile")
    
    logger.info(f"Exporting gallery with {len(photo_paths)} photos to {output_dir}")
    logger.info(f"Max resolution: {export_profile.max_width}×{export_profile.max_height}")
    logger.info(f"JPEG quality: {export_profile.jpeg_quality}")
    if generate_webp and export_profile.webp_quality:
        logger.info(f"WebP quality: {export_profile.webp_quality}")
    
    # Initialize progress
    _export_progress['status'] = 'running'
    _export_progress['current'] = 0
    _export_progress['total'] = len(photo_paths)
    _export_progress['step'] = 'setup'
    _export_progress['message'] = 'Creating directory structure...'
    
    # Create directory structure
    gallery_dir = output_dir / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    
    images_dir = gallery_dir / "images"
    thumbs_dir = gallery_dir / "thumbnails"
    music_dir = gallery_dir / "music"
    images_dir.mkdir(exist_ok=True)
    thumbs_dir.mkdir(exist_ok=True)
    
    # Copy music files to gallery directory
    music_file_list = []
    if music_files:
        music_dir.mkdir(exist_ok=True)
        logger.info(f"Copying {len(music_files)} music files...")
        for i, music_path in enumerate(music_files):
            if music_path.exists():
                # Copy with numbered filename to avoid conflicts
                ext = music_path.suffix
                music_filename = f"track{i+1:02d}{ext}"
                dest_path = music_dir / music_filename
                shutil.copy2(music_path, dest_path)
                # Store relative path for HTML
                music_file_list.append(f"music/{music_filename}")
                logger.info(f"  ✓ Copied {music_path.name} → {music_filename}")
            else:
                logger.warning(f"  ⚠️ Music file not found: {music_path}")
    
    # Initialize variables (used in both quick and normal mode)
    photo_data = []
    total_original_size = 0
    total_jpeg_size = 0
    total_webp_size = 0
    
    # ⚡ QUICK UPDATE MODE: Skip image processing, reuse existing images
    if quick_update:
        logger.info("⚡ QUICK UPDATE MODE: Reusing existing images, regenerating HTML only")
        
        # Check if images directory exists and has images
        if not images_dir.exists() or not list(images_dir.glob("*.jpg")):
            logger.error("Quick update failed: No existing images found!")
            logger.error("Run a full export first before using quick update.")
            raise ValueError("Quick update requires existing images. Run full export first.")
        
        existing_images = sorted(images_dir.glob("*.jpg"))
        
        logger.info(f"Found {len(existing_images)} existing images")
        
        for i, img_path in enumerate(existing_images):
            if i >= len(photo_paths):
                break  # Don't exceed the number of photos selected
            
            photo_path = photo_paths[i]
            img_filename = img_path.name
            thumb_filename = img_filename
            
            # Get image dimensions from existing file
            try:
                with Image.open(img_path) as img:
                    width, height = img.size
            except:
                width, height = 1920, 1280  # Fallback dimensions
            
            # Get metadata if requested
            metadata = {}
            if include_metadata:
                metadata = get_metadata(photo_path)
            
            # Build photo data entry
            photo_entry = {
                'src': f"images/{img_filename}",
                'thumbnail': f"thumbnails/{thumb_filename}",
                'width': width,
                'height': height,
                'title': photo_path.name,
                'rating': metadata.get('rating', 0),
                'color': metadata.get('color'),
                'keywords': metadata.get('keywords', [])
            }
            
            # Check for WebP versions
            webp_img = images_dir / img_path.stem
            webp_img = webp_img.with_suffix('.webp')
            if webp_img.exists():
                photo_entry['src_webp'] = f"images/{webp_img.name}"
            
            webp_thumb = thumbs_dir / img_path.stem
            webp_thumb = webp_thumb.with_suffix('.webp')
            if webp_thumb.exists():
                photo_entry['thumbnail_webp'] = f"thumbnails/{webp_thumb.name}"
            
            photo_data.append(photo_entry)
        
        logger.info(f"⚡ Quick update: Reusing {len(photo_data)} existing images")
        
    else:
        # NORMAL MODE: Process all photos        
        _export_progress['step'] = 'processing'
    
        for i, photo_path in enumerate(photo_paths):
            _export_progress['current'] = i + 1
            _export_progress['message'] = f'Processing {photo_path.name}...'
            try:
                # Generate filenames
                img_filename = f"{i:04d}.jpg"
                thumb_filename = f"{i:04d}.jpg"
                
                img_path = images_dir / img_filename
                thumb_path = thumbs_dir / thumb_filename
                
                # Apply edits if enabled and edits exist
                source_for_export = photo_path
                temp_edited_path = None
                
                if apply_edits:
                    try:
                        from .edits import get_edits, has_edits
                        from ..image_processing import apply_all_edits as apply_image_edits
                        
                        if has_edits(photo_path):
                            edits = get_edits(photo_path)
                            
                            # Apply edits to temporary file
                            temp_edited_path = output_dir / f"temp_edited_{i:04d}.jpg"
                            edited_img = apply_image_edits(photo_path, edits, output_format='pil')
                            edited_img.save(temp_edited_path, quality=95)
                            
                            source_for_export = temp_edited_path
                            logger.info(f"  ✨ Applied edits to {photo_path.name}")
                    except ImportError:
                        logger.warning("Image editing module not available, exporting originals")
                    except Exception as e:
                        logger.warning(f"Error applying edits to {photo_path.name}: {e}")
                
                # Optimize main image using profile
                img_result = optimize_image(
                    source_path=source_for_export,
                    output_path=img_path,
                    profile=export_profile,
                    generate_webp=generate_webp
                )
                
                # Generate optimized thumbnail (from already edited source if applicable)
                # MUST be done BEFORE cleaning up temp file!
                thumb_result = generate_optimized_thumbnail(
                    source_path=source_for_export,  # Use same source as main image
                    output_path=thumb_path,
                    profile=export_profile,
                    generate_webp=generate_webp
                )
                
                # Clean up temp file if created (AFTER both main image and thumbnail are done!)
                if temp_edited_path and temp_edited_path.exists():
                    temp_edited_path.unlink()
                
                # Update size stats
                total_original_size += img_result['original_size']
                total_jpeg_size += img_result['jpeg_size']
                if img_result['webp_size']:
                    total_webp_size += img_result['webp_size']
                
                # Get metadata if requested
                metadata = {}
                if include_metadata:
                    metadata = get_metadata(photo_path)
                
                # Build photo data entry
                photo_entry = {
                    'src': f"images/{img_filename}",
                    'thumbnail': f"thumbnails/{thumb_filename}",
                    'width': img_result['width'],
                    'height': img_result['height'],
                    'title': photo_path.name,
                    'rating': metadata.get('rating', 0),
                    'color': metadata.get('color'),
                    'keywords': metadata.get('keywords', [])
                }
                
                # Add WebP sources if generated
                if img_result['webp_path']:
                    photo_entry['src_webp'] = f"images/{i:04d}.webp"
                if thumb_result['webp_path']:
                    photo_entry['thumbnail_webp'] = f"thumbnails/{i:04d}.webp"
                
                photo_data.append(photo_entry)
                
                logger.debug(f"Processed {photo_path.name} - "
                            f"JPEG: {img_result['jpeg_size']//1024}KB"
                            + (f", WebP: {img_result['webp_size']//1024}KB" if img_result['webp_size'] else ""))
                
            except Exception as e:
                logger.error(f"Failed to process {photo_path}: {e}")
                continue
    
    # Generate HTML
    if template == "slideshow":
        html = _generate_slideshow_html(
            title=title,
            photo_data=photo_data,
            music_files=music_file_list,  # Use relative paths instead of absolute
            music_autoplay=music_autoplay,
            music_ducking_volume=music_ducking_volume,  # 🎚️ Pass ducking volume
            slideshow_duration=slideshow_duration,
            smart_tv_mode=smart_tv_mode,
            splash_title=splash_title,        # 🎬 Pass custom splash title
            splash_subtitle=splash_subtitle   # 🎬 Pass custom splash subtitle
        )
    elif template == "photoswipe":
        html = _generate_photoswipe_html(title, photo_data)
    else:
        html = _generate_simple_html(title, photo_data)
    
    # Write HTML file
    _export_progress['step'] = 'finalizing'
    _export_progress['message'] = 'Generating HTML...'
    
    index_path = gallery_dir / "index.html"
    index_path.write_text(html, encoding='utf-8')
    
    _export_progress['status'] = 'complete'
    _export_progress['message'] = 'Export complete!'
    
    # Log compression statistics
    if total_original_size > 0:
        jpeg_ratio = (1 - total_jpeg_size / total_original_size) * 100
        logger.info(f"Compression stats:")
        logger.info(f"  Original: {total_original_size / 1024 / 1024:.1f} MB")
        logger.info(f"  JPEG: {total_jpeg_size / 1024 / 1024:.1f} MB ({jpeg_ratio:.1f}% reduction)")
        if total_webp_size > 0:
            webp_ratio = (1 - total_webp_size / total_original_size) * 100
            logger.info(f"  WebP: {total_webp_size / 1024 / 1024:.1f} MB ({webp_ratio:.1f}% reduction)")
    
    logger.info(f"Gallery exported successfully to {gallery_dir}")
    logger.info(f"Profile: {export_profile.name}")
    if music_file_list:
        logger.info(f"Music tracks: {len(music_file_list)}")
    logger.info(f"Open {index_path} in browser to view")
    
    return gallery_dir


def _generate_photoswipe_html(title: str, photos: List[Dict[str, Any]]) -> str:
    """Generate PhotoSwipe template HTML"""
    
    photos_json = json.dumps(photos, indent=2)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    
    <!-- PhotoSwipe CSS -->
    <link rel="stylesheet" href="https://unpkg.com/photoswipe/dist/photoswipe.css">
    
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #fff;
            min-height: 100vh;
        }}
        
        .header {{
            padding: 40px 30px;
            text-align: center;
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
        }}
        
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #4ade80, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .subtitle {{
            color: #888;
            font-size: 1.1rem;
        }}
        
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            padding: 40px 30px;
            max-width: 1800px;
            margin: 0 auto;
        }}
        
        .gallery-item {{
            position: relative;
            cursor: pointer;
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s ease;
            background: rgba(255,255,255,0.05);
        }}
        
        .gallery-item:hover {{
            transform: translateY(-8px);
            box-shadow: 0 12px 40px rgba(74, 222, 128, 0.3);
        }}
        
        .gallery-item img {{
            width: 100%;
            height: 280px;
            object-fit: cover;
            display: block;
        }}
        
        .photo-overlay {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.9));
            padding: 20px 15px 15px;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        
        .gallery-item:hover .photo-overlay {{
            opacity: 1;
        }}
        
        .photo-title {{
            font-size: 0.9rem;
            color: #fff;
            margin-bottom: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .stars {{
            color: #fbbf24;
            font-size: 0.9rem;
        }}
        
        .keywords {{
            margin-top: 8px;
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }}
        
        .keyword {{
            background: rgba(59, 130, 246, 0.3);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.75rem;
            color: #93c5fd;
        }}
        
        .color-badge {{
            position: absolute;
            top: 15px;
            left: 15px;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 3px solid #fff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.5);
        }}
        
        .footer {{
            text-align: center;
            padding: 40px 30px;
            color: #666;
            font-size: 0.9rem;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        
        .footer a {{
            color: #4ade80;
            text-decoration: none;
        }}
        
        @media (max-width: 768px) {{
            .gallery {{
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
                padding: 20px 15px;
            }}
            
            h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="subtitle">{len(photos)} photos</div>
    </div>

    <div class="gallery" id="gallery">
        <!-- Generated by JavaScript -->
    </div>

    <div class="footer">
        Generated with <a href="https://github.com" target="_blank">Photo Tool</a> | {now}
    </div>

    <!-- PhotoSwipe JS -->
    <script type="module">
        import PhotoSwipeLightbox from 'https://unpkg.com/photoswipe/dist/photoswipe-lightbox.esm.js';
        import PhotoSwipe from 'https://unpkg.com/photoswipe/dist/photoswipe.esm.js';

        const photos = {photos_json};

        const colorHex = {{
            red: '#ef4444',
            yellow: '#fbbf24',
            green: '#4ade80',
            blue: '#3b82f6',
            purple: '#a855f7'
        }};

        // Generate gallery HTML
        const gallery = document.getElementById('gallery');
        
        photos.forEach((photo, index) => {{
            const item = document.createElement('a');
            item.href = photo.src;
            item.className = 'gallery-item';
            item.setAttribute('data-pswp-width', photo.width);
            item.setAttribute('data-pswp-height', photo.height);

            // Use <picture> for WebP support with JPEG fallback
            let imgHtml;
            if (photo.thumbnail_webp) {{
                imgHtml = `
                    <picture>
                        <source srcset="${{photo.thumbnail_webp}}" type="image/webp">
                        <img src="${{photo.thumbnail}}" alt="${{photo.title}}" loading="lazy">
                    </picture>
                `;
            }} else {{
                imgHtml = `<img src="${{photo.thumbnail}}" alt="${{photo.title}}" loading="lazy">`;
            }}
            
            let html = imgHtml;
            
            // Color badge
            if (photo.color) {{
                html += `<div class="color-badge" style="background: ${{colorHex[photo.color]}}"></div>`;
            }}

            // Overlay with metadata
            let overlayContent = `<div class="photo-title">${{photo.title}}</div>`;
            
            if (photo.rating > 0) {{
                const stars = '★'.repeat(photo.rating) + '☆'.repeat(5 - photo.rating);
                overlayContent += `<div class="stars">${{stars}}</div>`;
            }}
            
            if (photo.keywords && photo.keywords.length > 0) {{
                overlayContent += '<div class="keywords">';
                photo.keywords.forEach(kw => {{
                    overlayContent += `<span class="keyword">${{kw}}</span>`;
                }});
                overlayContent += '</div>';
            }}
            
            html += `<div class="photo-overlay">${{overlayContent}}</div>`;

            item.innerHTML = html;
            gallery.appendChild(item);
        }});

        // Initialize PhotoSwipe
        const lightbox = new PhotoSwipeLightbox({{
            gallery: '#gallery',
            children: 'a',
            pswpModule: PhotoSwipe,
            preload: [1, 2]
        }});
        
        lightbox.init();
    </script>
</body>
</html>'''


def _generate_simple_html(title: str, photos: List[Dict[str, Any]]) -> str:
    """Generate simple grid template HTML (no dependencies)"""
    
    photos_html = ""
    for photo in photos:
        stars = "★" * photo.get('rating', 0) + "☆" * (5 - photo.get('rating', 0))
        keywords_html = " ".join([f'<span class="keyword">{k}</span>' for k in photo.get('keywords', [])])
        
        photos_html += f'''
        <div class="gallery-item">
            <a href="{photo['src']}" target="_blank">
                <img src="{photo['thumbnail']}" alt="{photo['title']}">
            </a>
            <div class="photo-info">
                <div class="photo-title">{photo['title']}</div>
                {f'<div class="stars">{stars}</div>' if photo.get('rating', 0) > 0 else ''}
                {f'<div class="keywords">{keywords_html}</div>' if keywords_html else ''}
            </div>
        </div>
        '''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: system-ui, sans-serif;
            background: #0a0a0a;
            color: #fff;
            padding: 30px;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5rem;
        }}
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            max-width: 1800px;
            margin: 0 auto;
        }}
        .gallery-item {{
            background: #1a1a1a;
            border-radius: 8px;
            overflow: hidden;
        }}
        .gallery-item img {{
            width: 100%;
            height: 250px;
            object-fit: cover;
        }}
        .photo-info {{
            padding: 12px;
        }}
        .photo-title {{
            font-size: 0.9rem;
            margin-bottom: 5px;
        }}
        .stars {{
            color: gold;
            font-size: 0.9rem;
        }}
        .keywords {{
            margin-top: 8px;
        }}
        .keyword {{
            background: rgba(59, 130, 246, 0.3);
            padding: 2px 6px;
            border-radius: 8px;
            font-size: 0.75rem;
            margin-right: 4px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="gallery">
        {photos_html}
    </div>
</body>
</html>'''


def _generate_slideshow_html(
    title: str,
    photo_data: List[Dict[str, Any]],
    music_files: Optional[List[str]] = None,
    music_autoplay: bool = False,
    music_ducking_volume: int = 30,  # 🎚️ Music volume during pause (0-100%)
    slideshow_duration: int = 5,
    smart_tv_mode: bool = False,
    splash_title: str = None,  # 🆕 Custom splash title
    splash_subtitle: str = None  # 🆕 Custom splash subtitle (date)
) -> str:
    """Generate fullscreen slideshow template with music support (based on working GUI slideshow)"""
    
    photos_json = json.dumps(photo_data, indent=2)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Convert music file paths to HTML-friendly format
    music_html = ""
    music_controls_html = ""
    if music_files:
        music_sources = '\n'.join([
            f'            <source src="{music}" type="audio/mpeg">'
            for music in music_files
        ])
        music_html = f'''
        <audio id="bgMusic" loop preload="auto">
{music_sources}
        </audio>'''
        music_controls_html = '''
                    <button class="slideshow-btn" onclick="event.stopPropagation(); toggleMusic();" title="Music (M)">
                        <span id="musicIcon">🎵</span> Music
                    </button>'''
    
    button_padding = "16px 32px" if smart_tv_mode else "12px 24px"
    button_font = "1.2rem" if smart_tv_mode else "1rem"
    
    # Splash screen configuration
    splash_bg = "splash.jpg"  # Try custom splash first
    splash_fallback = photo_data[0]['src'] if photo_data else ''
    
    # Use custom titles if provided, otherwise use defaults
    if not splash_title:
        splash_title = title
    if not splash_subtitle:
        splash_subtitle = f"{len(photo_data)} photos{' • Background music' if music_files else ''}"
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #000;
            color: #fff;
            overflow: hidden;
        }}
        
        .slideshow {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: #000;
            display: flex;
            flex-direction: column;
            z-index: 3000;
        }}
        
        .slideshow.hide-controls {{
            cursor: none;
        }}
        
        .slideshow-header {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 30px;
            background: linear-gradient(to bottom, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.4) 70%, transparent 100%);
            backdrop-filter: blur(10px);
            z-index: 100;
            transition: opacity 0.3s ease, transform 0.3s ease;
        }}
        
        .slideshow.hide-controls .slideshow-header {{
            opacity: 0;
            transform: translateY(-100%);
            /* pointer-events: none; -- REMOVED: Allow clicks to show controls */
        }}
        
        .slideshow-title {{
            font-size: 1.2rem;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .slideshow-main {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }}
        
        .slideshow-image-container {{
            position: absolute;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 1s ease-in-out;
        }}
        
        .slideshow-image-container.active {{
            opacity: 1;
        }}
        
        .slideshow-image {{
            max-width: 100%;
            max-height: 100%;
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}
        
        .slideshow-footer {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 20px 30px;
            background: linear-gradient(to top, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.4) 70%, transparent 100%);
            backdrop-filter: blur(10px);
            z-index: 100;
            transition: opacity 0.3s ease, transform 0.3s ease;
        }}
        
        .slideshow.hide-controls .slideshow-footer {{
            opacity: 0;
            transform: translateY(100%);
            /* pointer-events: none; -- REMOVED: Allow clicks to show controls */
        }}
        
        .slideshow-progress {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .slideshow-progress-bar {{
            flex: 1;
            height: 6px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
            overflow: hidden;
            cursor: pointer;
            position: relative;
        }}
        
        .slideshow-progress-bar:hover {{
            background: rgba(255, 255, 255, 0.3);
        }}
        
        .slideshow-progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #8b5cf6, #ec4899);
            border-radius: 3px;
            transition: width 0.3s ease;
        }}
        
        .slideshow-progress-text {{
            color: #888;
            font-size: 0.9rem;
            min-width: 80px;
            text-align: right;
        }}
        
        .slideshow-controls {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
        }}
        
        .slideshow-btn {{
            background: rgba(255, 255, 255, 0.1);
            border: none;
            color: #fff;
            padding: {button_padding};
            border-radius: 8px;
            font-size: {button_font};
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .slideshow-btn:hover {{
            background: rgba(255, 255, 255, 0.2);
            transform: scale(1.05);
        }}
        
        .slideshow-btn:disabled {{
            opacity: 0.3;
            cursor: not-allowed;
        }}
        
        .slideshow-btn.primary {{
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
        }}
        
        .slideshow-btn.primary:hover {{
            background: linear-gradient(135deg, #7c3aed, #db2777);
        }}
        
        .slideshow-settings {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        
        .slideshow-setting {{
            display: flex;
            align-items: center;
            gap: 10px;
            color: #ccc;
            font-size: 0.9rem;
        }}
        
        .slideshow-setting select {{
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
        }}
        
        .slideshow-setting input[type="checkbox"] {{
            width: 20px;
            height: 20px;
            cursor: pointer;
        }}
        
        /* 🎬 Splash Screen - 2/3 Photo + 1/3 UI Layout */
        .splash-screen {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: #000;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            opacity: 1;
            transition: opacity 0.5s ease;
        }}
        
        .splash-screen.hidden {{
            opacity: 0;
            pointer-events: none;
        }}
        
        .splash-background {{
            position: relative;
            flex: 2;  /* 2/3 of screen height */
            background-size: cover;
            background-position: center;
            filter: brightness(0.7);
            overflow: hidden;
        }}
        
        .splash-background img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .splash-content {{
            flex: 1;  /* 1/3 of screen height */
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
            background: linear-gradient(to bottom, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.95) 100%);
            gap: 30px;
        }}
        
        .splash-title {{
            font-size: 2.5rem;
            font-weight: bold;
            text-align: center;
            text-shadow: 0 4px 20px rgba(0, 0, 0, 0.8);
            line-height: 1.2;
        }}
        
        .splash-subtitle {{
            font-size: 1.4rem;
            color: #ccc;
            text-align: center;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.8);
            margin-top: -15px;
        }}
        
        .splash-play-btn {{
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
            border: none;
            color: #fff;
            width: 140px;
            height: 140px;
            border-radius: 50%;
            font-size: 4rem;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 15px 50px rgba(139, 92, 246, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .splash-play-btn:hover {{
            transform: scale(1.1);
            box-shadow: 0 20px 70px rgba(139, 92, 246, 0.8);
        }}
        
        .splash-play-btn:active {{
            transform: scale(0.95);
        }}
        
        @media (max-width: 768px) {{
            .splash-title {{
                font-size: 1.8rem;
            }}
            
            .splash-subtitle {{
                font-size: 1.1rem;
            }}
            
            .splash-play-btn {{
                width: 120px;
                height: 120px;
                font-size: 3.5rem;
            }}
            
            .splash-content {{
                padding: 30px 20px;
                gap: 25px;
            }}
        }}
    </style>
</head>
<body>
    <!-- 🎬 Splash Screen with Custom Photo -->
    <div class="splash-screen" id="splashScreen">
        <div class="splash-background">
            <img src="{splash_bg}" 
                 onerror="this.src='{splash_fallback}'" 
                 alt="Welcome">
        </div>
        <div class="splash-content">
            <div class="splash-title">{splash_title}</div>
            <button class="splash-play-btn" onclick="startSlideshow()" title="Start Slideshow">
                ▶️
            </button>
            <div class="splash-subtitle">{splash_subtitle}</div>
        </div>
    </div>
    
    <div class="slideshow" id="slideshow" onmousemove="showControlsTemporarily()" style="display: none;">
        <div class="slideshow-header">
            <div class="slideshow-title">
                <span>🎬</span>
                <span>{title}</span>
                <span style="color: #888; font-size: 0.9rem; margin-left: 10px;" id="counter">
                    1 / {len(photo_data)}
                </span>
            </div>
            <div style="display: flex; gap: 10px;">
                <button class="slideshow-btn" onclick="event.stopPropagation(); toggleFullscreen();" id="fullscreenBtn">
                    ⛶ Fullscreen
                </button>
            </div>
        </div>
        
        <div class="slideshow-main">
            <!-- Images will be added by JavaScript -->
        </div>
        
        <div class="slideshow-footer">
            <div class="slideshow-progress">
                <div class="slideshow-progress-bar">
                    <div class="slideshow-progress-fill" id="progressBar"></div>
                </div>
                <div class="slideshow-progress-text" id="progressText">1 / {len(photo_data)}</div>
            </div>
            
            <div class="slideshow-controls">
                <button class="slideshow-btn" onclick="event.stopPropagation(); prevSlide();" id="prevBtn">
                    ⏮️ Prev
                </button>
                
                <button class="slideshow-btn primary" onclick="event.stopPropagation(); togglePlay();" id="playBtn">
                    ⏸️ Pause
                </button>
                
                <button class="slideshow-btn" onclick="event.stopPropagation(); nextSlide();" id="nextBtn">
                    Next ⏭️
                </button>
                
                <div class="slideshow-settings">
                    <div class="slideshow-setting">
                        <span>Speed:</span>
                        <select id="speedSelect" onchange="event.stopPropagation(); changeSpeed();">
                            <option value="2">2s</option>
                            <option value="3">3s</option>
                            <option value="5" selected>5s</option>
                            <option value="7">7s</option>
                            <option value="10">10s</option>
                        </select>
                    </div>
                    
                    <div class="slideshow-setting">
                        <input type="checkbox" id="loopCheck" onchange="event.stopPropagation(); toggleLoop();" checked>
                        <label for="loopCheck">Loop</label>
                    </div>
                </div>
                
{music_controls_html}
            </div>
        </div>
    </div>
    
{music_html}
    
    <script>
        const photos = {photos_json};
        let currentIndex = 0;
        let isPlaying = true;
        let isLooping = true;
        let isFullscreen = false;
        let hideControlsTimeout = null;
        let slideInterval = null;
        let slideDuration = {slideshow_duration * 1000};
        
        // 🎚️ Music ducking configuration
        const MUSIC_DUCKING_VOLUME = {music_ducking_volume / 100.0};  // Convert 0-100% to 0.0-1.0
        const MUSIC_FULL_VOLUME = 1.0;
        
        const slideshow = document.getElementById('slideshow');
        const slideshowMain = document.querySelector('.slideshow-main');
        const playBtn = document.getElementById('playBtn');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const progressBar = document.getElementById('progressBar');
        const progressBarContainer = document.querySelector('.slideshow-progress-bar');
        const progressText = document.getElementById('progressText');
        const counter = document.getElementById('counter');
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        const speedSelect = document.getElementById('speedSelect');
        const bgMusic = document.getElementById('bgMusic');
        
        // Preload and create all image containers
        photos.forEach((photo, i) => {{
            const container = document.createElement('div');
            container.className = 'slideshow-image-container' + (i === 0 ? ' active' : '');
            
            const img = document.createElement('img');
            img.src = photo.src;
            img.alt = photo.title || `Photo ${{i + 1}}`;
            img.className = 'slideshow-image';
            
            container.appendChild(img);
            slideshowMain.appendChild(container);
        }});
        
        const imageContainers = document.querySelectorAll('.slideshow-image-container');
        
        function updateDisplay() {{
            imageContainers.forEach((container, i) => {{
                container.classList.toggle('active', i === currentIndex);
            }});
            
            const progress = ((currentIndex + 1) / photos.length * 100);
            progressBar.style.width = progress + '%';
            progressText.textContent = `${{currentIndex + 1}} / ${{photos.length}}`;
            counter.textContent = `${{currentIndex + 1}} / ${{photos.length}}`;
            
            prevBtn.disabled = currentIndex === 0 && !isLooping;
            nextBtn.disabled = currentIndex === photos.length - 1 && !isLooping;
        }}
        
        function nextSlide() {{
            if (currentIndex < photos.length - 1) {{
                currentIndex++;
            }} else if (isLooping) {{
                currentIndex = 0;
            }}
            updateDisplay();
        }}
        
        function prevSlide() {{
            if (currentIndex > 0) {{
                currentIndex--;
            }} else if (isLooping) {{
                currentIndex = photos.length - 1;
            }}
            updateDisplay();
        }}
        
        function togglePlay() {{
            isPlaying = !isPlaying;
            playBtn.textContent = isPlaying ? '⏸️ Pause' : '▶️ Play';

            if (isPlaying) {{
                startAutoplay();
                // 🎚️ Restore full music volume when playing
                const bgMusic = document.getElementById('bgMusic');
                if (bgMusic) {{
                    bgMusic.volume = MUSIC_FULL_VOLUME;
                }}
            }} else {{
                stopSlideshow();
                // 🎚️ Duck music volume when paused
                const bgMusic = document.getElementById('bgMusic');
                if (bgMusic) {{
                    bgMusic.volume = MUSIC_DUCKING_VOLUME;
                }}
            }}
        }}
        
        function startAutoplay() {{
            stopSlideshow();
            slideInterval = setInterval(() => {{
                nextSlide();
                if (!isLooping && currentIndex === photos.length - 1) {{
                    stopSlideshow();
                    isPlaying = false;
                    playBtn.textContent = '▶️ Play';
                }}
            }}, slideDuration);
        }}
        
        function stopSlideshow() {{
            if (slideInterval) {{
                clearInterval(slideInterval);
                slideInterval = null;
            }}
        }}
        
        function changeSpeed() {{
            slideDuration = parseInt(speedSelect.value) * 1000;
            if (isPlaying) {{
                startSlideshow();
            }}
        }}
        
        function toggleLoop() {{
            isLooping = document.getElementById('loopCheck').checked;
            updateDisplay();
        }}
        
        function jumpToSlide(index) {{
            if (index >= 0 && index < photos.length) {{
                currentIndex = index;
                updateDisplay();
                // Restart slideshow if playing
                if (isPlaying) {{
                    startAutoplay();
                }}
            }}
        }}
        
        function toggleFullscreen() {{
            if (!document.fullscreenElement) {{
                slideshow.requestFullscreen().then(() => {{
                    isFullscreen = true;
                    fullscreenBtn.textContent = '⛶ Exit Fullscreen';
                }}).catch(err => {{
                    console.log('Fullscreen error:', err);
                }});
            }} else {{
                document.exitFullscreen().then(() => {{
                    isFullscreen = false;
                    fullscreenBtn.textContent = '⛶ Fullscreen';
                }});
            }}
        }}
        
        function showControlsTemporarily() {{
            slideshow.classList.remove('hide-controls');
            
            clearTimeout(hideControlsTimeout);
            // Only auto-hide if slideshow is playing
            if (isPlaying) {{
                hideControlsTimeout = setTimeout(() => {{
                    slideshow.classList.add('hide-controls');
                }}, 3000);
            }}
        }}
        
        // 📱 Mobile-friendly: Toggle controls visibility on tap (without affecting playback)
        function toggleControlsVisibility() {{
            const isHidden = slideshow.classList.contains('hide-controls');
            
            if (isHidden) {{
                // Show controls
                showControlsTemporarily();
            }} else {{
                // Hide controls immediately if playing, keep visible if paused
                if (isPlaying) {{
                    slideshow.classList.add('hide-controls');
                    clearTimeout(hideControlsTimeout);
                }}
            }}
        }}
        
        function toggleMusic() {{
            if (bgMusic) {{
                if (bgMusic.paused) {{
                    bgMusic.play();
                    document.getElementById('musicIcon').textContent = '🎵';
                }} else {{
                    bgMusic.pause();
                    document.getElementById('musicIcon').textContent = '🔇';
                }}
            }}
        }}
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {{
            showControlsTemporarily();
            
            switch(e.key) {{
                case 'ArrowLeft':
                    prevSlide();
                    break;
                case 'ArrowRight':
                    nextSlide();
                    break;
                case ' ':
                    e.preventDefault();
                    togglePlay();
                    break;
                case 'f':
                case 'F':
                    toggleFullscreen();
                    break;
                case 'm':
                case 'M':
                    if (bgMusic) toggleMusic();
                    break;
                case 'Escape':
                    if (isFullscreen) {{
                        document.exitFullscreen();
                    }}
                    break;
            }}
        }});
        
        // Handle fullscreen changes
        document.addEventListener('fullscreenchange', () => {{
            isFullscreen = !!document.fullscreenElement;
            fullscreenBtn.textContent = isFullscreen ? '⛶ Exit Fullscreen' : '⛶ Fullscreen';
        }});
        
        // 📱 Touch event handling for mobile devices
        slideshowMain.addEventListener('click', (e) => {{
            toggleControlsVisibility();
        }});
        
        slideshowMain.addEventListener('touchend', (e) => {{
            e.preventDefault();  // Prevent double-firing with click
            toggleControlsVisibility();
        }});
        
        // Make progress bar clickable (jump to slide)
        progressBarContainer.addEventListener('click', (e) => {{
            e.stopPropagation();  // Prevent triggering toggleControlsVisibility
            const rect = progressBarContainer.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const percent = clickX / rect.width;
            const targetIndex = Math.floor(percent * photos.length);
            jumpToSlide(Math.max(0, Math.min(photos.length - 1, targetIndex)));
            showControlsTemporarily();
        }});
        
        // 🎬 Splash Screen: Start slideshow on button click
        function startSlideshowFromSplash() {{
            // Hide splash screen
            const splashScreen = document.getElementById('splashScreen');
            splashScreen.classList.add('hidden');
            
            // Show slideshow
            const slideshow = document.getElementById('slideshow');
            slideshow.style.display = 'flex';
            
            // 🖥️ Auto-enter fullscreen (if supported)
            if (document.documentElement.requestFullscreen) {{
                document.documentElement.requestFullscreen().catch(err => {{
                    console.log('Fullscreen request failed:', err);
                }});
            }}
            
            // Start playing
            isPlaying = true;
            playBtn.textContent = '⏸️ Pause';
            startAutoplay();
            
            // 🎵 Start music with better buffering handling
            if (bgMusic) {{
                // Check if music is ready
                if (bgMusic.readyState >= 2) {{
                    // HAVE_CURRENT_DATA or better - can play now
                    bgMusic.play().catch(e => console.log('Music playback blocked:', e));
                }} else {{
                    // Wait for music to load enough data
                    bgMusic.addEventListener('canplay', function startMusic() {{
                        bgMusic.play().catch(e => console.log('Music playback blocked:', e));
                        bgMusic.removeEventListener('canplay', startMusic);
                    }}, {{ once: true }});
                }}
            }}
            
            // Hide controls after 3 seconds
            setTimeout(() => {{
                slideshow.classList.add('hide-controls');
            }}, 3000);
        }}
        
        // Make startSlideshow globally accessible for splash button
        window.startSlideshow = startSlideshowFromSplash;
        
        // Initialize display
        updateDisplay();
        
        // Generated: {now}
    </script>
</body>
</html>'''
