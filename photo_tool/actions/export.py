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

logger = get_logger("export")


def export_gallery(
    photo_paths: List[Path],
    output_dir: Path,
    title: str = "Photo Gallery",
    template: str = "photoswipe",
    max_image_size: int = 2000,
    thumbnail_size: int = 400,
    include_metadata: bool = True
) -> Path:
    """
    Export photos as standalone web gallery
    
    Args:
        photo_paths: List of photo paths to include
        output_dir: Output directory for gallery
        title: Gallery title
        template: Template name (photoswipe, simple)
        max_image_size: Max width/height for images
        thumbnail_size: Thumbnail size
        include_metadata: Include ratings, colors, keywords
        
    Returns:
        Path to generated gallery directory
    """
    
    logger.info(f"Exporting gallery with {len(photo_paths)} photos to {output_dir}")
    
    # Create directory structure
    gallery_dir = output_dir / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    
    images_dir = gallery_dir / "images"
    thumbs_dir = gallery_dir / "thumbnails"
    images_dir.mkdir(exist_ok=True)
    thumbs_dir.mkdir(exist_ok=True)
    
    # Process photos
    photo_data = []
    
    for i, photo_path in enumerate(photo_paths):
        try:
            # Generate image filename
            img_filename = f"{i:04d}{photo_path.suffix}"
            thumb_filename = f"{i:04d}.jpg"
            
            # Copy and resize image
            img_path = images_dir / img_filename
            thumb_path = thumbs_dir / thumb_filename
            
            # Resize main image
            with Image.open(photo_path) as img:
                # Get original dimensions
                width, height = img.size
                
                # Resize if needed
                if width > max_image_size or height > max_image_size:
                    img.thumbnail((max_image_size, max_image_size), Image.Resampling.LANCZOS)
                    width, height = img.size
                
                # Convert RGBA to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Save image
                img.save(img_path, 'JPEG', quality=90, optimize=True)
            
            # Generate thumbnail
            with Image.open(photo_path) as img:
                img.thumbnail((thumbnail_size, thumbnail_size), Image.Resampling.LANCZOS)
                
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                img.save(thumb_path, 'JPEG', quality=85, optimize=True)
            
            # Get metadata if requested
            metadata = {}
            if include_metadata:
                metadata = get_metadata(photo_path)
            
            # Add to photo data
            photo_data.append({
                'src': f"images/{img_filename}",
                'thumbnail': f"thumbnails/{thumb_filename}",
                'width': width,
                'height': height,
                'title': photo_path.name,
                'rating': metadata.get('rating', 0),
                'color': metadata.get('color'),
                'keywords': metadata.get('keywords', [])
            })
            
            logger.debug(f"Processed {photo_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to process {photo_path}: {e}")
            continue
    
    # Generate HTML
    if template == "photoswipe":
        html = _generate_photoswipe_html(title, photo_data)
    else:
        html = _generate_simple_html(title, photo_data)
    
    # Write HTML file
    index_path = gallery_dir / "index.html"
    index_path.write_text(html, encoding='utf-8')
    
    logger.info(f"Gallery exported successfully to {gallery_dir}")
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

            let html = `<img src="${{photo.thumbnail}}" alt="${{photo.title}}" loading="lazy">`;
            
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
