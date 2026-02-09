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
    music_files: Optional[List[str]] = None,
    slideshow_enabled: bool = False,
    slideshow_duration: int = 5,
    smart_tv_mode: bool = False,
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
        - web: Standard web gallery (1920×1280, Q85)
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
    images_dir.mkdir(exist_ok=True)
    thumbs_dir.mkdir(exist_ok=True)
    
    # Process photos
    photo_data = []
    
    _export_progress['step'] = 'processing'
    
    # Track total file sizes
    total_original_size = 0
    total_jpeg_size = 0
    total_webp_size = 0
    
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
            
            # Clean up temp file if created
            if temp_edited_path and temp_edited_path.exists():
                temp_edited_path.unlink()
            
            # Generate optimized thumbnail (from already edited source if applicable)
            thumb_result = generate_optimized_thumbnail(
                source_path=source_for_export if apply_edits else photo_path,
                output_path=thumb_path,
                profile=export_profile,
                generate_webp=generate_webp
            )
            
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
            music_files=music_files,
            slideshow_duration=slideshow_duration,
            smart_tv_mode=smart_tv_mode
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
    slideshow_duration: int = 5,
    smart_tv_mode: bool = False
) -> str:
    """Generate fullscreen slideshow template with music support (based on working GUI slideshow)"""
    
    photos_json = json.dumps(photo_data, indent=2)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Convert music file paths to HTML-friendly format
    music_html = ""
    music_controls_html = ""
    if music_files:
        music_sources = '\n'.join([
            f'            <source src="{Path(music).as_posix()}" type="audio/mpeg">'
            for music in music_files
        ])
        music_html = f'''
        <audio id="bgMusic" loop>
{music_sources}
        </audio>'''
        music_controls_html = '''
                    <button class="slideshow-btn" onclick="toggleMusic()" title="Music (M)">
                        <span id="musicIcon">🎵</span> Music
                    </button>'''
    
    button_padding = "16px 32px" if smart_tv_mode else "12px 24px"
    button_font = "1.2rem" if smart_tv_mode else "1rem"
    
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
            pointer-events: none;
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
            pointer-events: none;
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
    </style>
</head>
<body>
    <div class="slideshow" id="slideshow" onmousemove="showControlsTemporarily()" onclick="showControlsTemporarily()">
        <div class="slideshow-header">
            <div class="slideshow-title">
                <span>🎬</span>
                <span>{title}</span>
                <span style="color: #888; font-size: 0.9rem; margin-left: 10px;" id="counter">
                    1 / {len(photo_data)}
                </span>
            </div>
            <div style="display: flex; gap: 10px;">
                <button class="slideshow-btn" onclick="toggleFullscreen()" id="fullscreenBtn">
                    ⛶ Fullscreen
                </button>
            </div>
        </div>
        
        <div class="slideshow-main" onclick="togglePlay()">
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
                <button class="slideshow-btn" onclick="prevSlide()" id="prevBtn">
                    ⏮️ Prev
                </button>
                
                <button class="slideshow-btn primary" onclick="togglePlay()" id="playBtn">
                    ⏸️ Pause
                </button>
                
                <button class="slideshow-btn" onclick="nextSlide()" id="nextBtn">
                    Next ⏭️
                </button>
                
                <div class="slideshow-settings">
                    <div class="slideshow-setting">
                        <span>Speed:</span>
                        <select id="speedSelect" onchange="changeSpeed()">
                            <option value="2">2s</option>
                            <option value="3">3s</option>
                            <option value="5" selected>5s</option>
                            <option value="7">7s</option>
                            <option value="10">10s</option>
                        </select>
                    </div>
                    
                    <div class="slideshow-setting">
                        <input type="checkbox" id="loopCheck" onchange="toggleLoop()" checked>
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
        
        const slideshow = document.getElementById('slideshow');
        const slideshowMain = document.querySelector('.slideshow-main');
        const playBtn = document.getElementById('playBtn');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const progressBar = document.getElementById('progressBar');
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
                startSlideshow();
            }} else {{
                stopSlideshow();
            }}
        }}
        
        function startSlideshow() {{
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
            hideControlsTimeout = setTimeout(() => {{
                if (isPlaying) {{
                    slideshow.classList.add('hide-controls');
                }}
            }}, 3000);
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
        
        // Auto-start
        if (isPlaying) {{
            startSlideshow();
        }}
        
        // Auto-play music
        if (bgMusic) {{
            bgMusic.play().catch(e => console.log('Music autoplay blocked:', e));
        }}
        
        // Start hiding controls after initial delay
        setTimeout(() => {{
            if (isPlaying) {{
                slideshow.classList.add('hide-controls');
            }}
        }}, 3000);
        
        // Generated: {now}
    </script>
</body>
</html>'''
