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
    max_image_size: int = 2000,
    thumbnail_size: int = 400,
    include_metadata: bool = True,
    music_files: Optional[List[Path]] = None,
    slideshow_enabled: bool = True,
    slideshow_duration: int = 5,
    slideshow_transition: str = "fade",
    smart_tv_mode: bool = False
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
        music_files: Optional list of music files to include
        slideshow_enabled: Enable slideshow functionality
        slideshow_duration: Seconds per photo in slideshow
        slideshow_transition: Transition effect (fade, kenburns)
        smart_tv_mode: Optimize UI for TV remote control
        
    Returns:
        Path to generated gallery directory
    """
    
    global _export_progress
    
    logger.info(f"Exporting gallery with {len(photo_paths)} photos to {output_dir}")
    
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
    
    # Copy music files if provided
    music_data = []
    if music_files:
        music_dir = gallery_dir / "music"
        music_dir.mkdir(exist_ok=True)
        
        _export_progress['step'] = 'music'
        _export_progress['message'] = 'Copying music files...'
        
        for music_file in music_files:
            if music_file.exists():
                dest = music_dir / music_file.name
                shutil.copy2(music_file, dest)
                music_data.append({
                    'filename': music_file.name,
                    'path': f"music/{music_file.name}"
                })
                logger.info(f"Copied music: {music_file.name}")
    
    # Process photos
    photo_data = []
    
    _export_progress['step'] = 'processing'
    
    for i, photo_path in enumerate(photo_paths):
        _export_progress['current'] = i + 1
        _export_progress['message'] = f'Processing {photo_path.name}...'
        try:
            # Generate image filename
            img_filename = f"{i:04d}{photo_path.suffix}"
            thumb_filename = f"{i:04d}.jpg"
            
            # Copy and resize image
            img_path = images_dir / img_filename
            thumb_path = thumbs_dir / thumb_filename
            
            # Resize main image
            with Image.open(photo_path) as img:
                # Apply EXIF orientation FIRST!
                try:
                    from PIL import ImageOps
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    pass  # If EXIF rotation fails, continue with original
                
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
                # Apply EXIF orientation for thumbnail too!
                try:
                    from PIL import ImageOps
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    pass
                
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
        # Use PhotoSwipe template (modern, lightbox-based)
        html = _generate_photoswipe_html(
            title=title,
            photos=photo_data,
            music_data=music_data,
            slideshow_enabled=slideshow_enabled,
            slideshow_duration=slideshow_duration,
            slideshow_transition=slideshow_transition,
            smart_tv_mode=smart_tv_mode
        )
    elif template == "slideshow":
        # Use custom slideshow template (fullscreen slideshow)
        from .export_slideshow_template import generate_slideshow_gallery_html
        html = generate_slideshow_gallery_html(
            title=title,
            photos=photo_data,
            music_data=music_data,
            slideshow_duration=slideshow_duration,
            smart_tv_mode=smart_tv_mode
        )
    else:
        # Simple grid template
        html = _generate_simple_html(title, photo_data)
    
    # Write HTML file
    _export_progress['step'] = 'finalizing'
    _export_progress['message'] = 'Generating HTML...'
    
    index_path = gallery_dir / "index.html"
    index_path.write_text(html, encoding='utf-8')
    
    _export_progress['status'] = 'complete'
    _export_progress['message'] = 'Export complete!'
    
    logger.info(f"Gallery exported successfully to {gallery_dir}")
    logger.info(f"Open {index_path} in browser to view")
    
    return gallery_dir


def _generate_photoswipe_html(
    title: str, 
    photos: List[Dict[str, Any]], 
    music_data: Optional[List[Dict[str, str]]] = None,
    slideshow_enabled: bool = True,
    slideshow_duration: int = 5,
    slideshow_transition: str = "fade",
    smart_tv_mode: bool = False
) -> str:
    """Generate PhotoSwipe template HTML with slideshow and music support"""
    
    photos_json = json.dumps(photos, indent=2)
    music_json = json.dumps(music_data or [], indent=2)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # TV mode adjustments
    tv_button_size = "min-width: 220px; height: 80px; font-size: 1.5rem;" if smart_tv_mode else ""
    tv_controls_size = "font-size: 1.8rem; padding: 15px 30px;" if smart_tv_mode else ""
    
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
            margin-bottom: 15px;
            background: linear-gradient(135deg, #4ade80, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .subtitle {{
            color: #888;
            font-size: 1.1rem;
            margin-bottom: 20px;
        }}
        
        .controls {{
            display: flex;
            gap: 15px;
            justify-content: center;
            align-items: center;
            flex-wrap: wrap;
            margin-top: 20px;
        }}
        
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            {tv_button_size}
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #4ade80, #3b82f6);
            color: #fff;
        }}
        
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(74, 222, 128, 0.4);
        }}
        
        .btn-secondary {{
            background: rgba(255,255,255,0.1);
            color: #fff;
        }}
        
        .btn-secondary:hover {{
            background: rgba(255,255,255,0.2);
        }}
        
        .music-controls {{
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(255,255,255,0.05);
            padding: 8px 16px;
            border-radius: 8px;
        }}
        
        .music-controls button {{
            background: none;
            border: none;
            color: #4ade80;
            cursor: pointer;
            font-size: 1.2rem;
            padding: 5px;
            transition: all 0.3s;
        }}
        
        .music-controls button:hover {{
            color: #3b82f6;
            transform: scale(1.2);
        }}
        
        .volume-slider {{
            width: 80px;
            accent-color: #4ade80;
        }}
        
        #now-playing {{
            color: #888;
            font-size: 0.9rem;
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
        
        /* Slideshow-specific styles */
        .pswp__button--slideshow {{
            background: none !important;
            color: #fff !important;
            font-size: 1.5rem !important;
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
            
            .controls {{
                flex-direction: column;
            }}
            
            .btn {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="subtitle">{len(photos)} photos</div>
        
        {'<div class="controls">' if slideshow_enabled else ''}
            {'<button class="btn btn-primary" id="start-slideshow">🎬 Start Slideshow</button>' if slideshow_enabled else ''}
            
            {'<div class="music-controls" id="music-controls" style="display: none;"><button id="play-pause-music">▶️</button><span id="now-playing">No music</span><input type="range" id="volume" class="volume-slider" min="0" max="100" value="70"></div>' if music_data else ''}
        {'</div>' if slideshow_enabled else ''}
    </div>

    <div class="gallery" id="gallery">
        <!-- Generated by JavaScript -->
    </div>

    <div class="footer">
        Generated with <a href="https://github.com" target="_blank">Photo Tool</a> | {now}
    </div>
    
    <!-- Hidden Audio Player -->
    {f'<audio id="music-player" preload="auto"></audio>' if music_data else ''}

    <!-- PhotoSwipe JS -->
    <script type="module">
        import PhotoSwipeLightbox from 'https://unpkg.com/photoswipe/dist/photoswipe-lightbox.esm.js';
        import PhotoSwipe from 'https://unpkg.com/photoswipe/dist/photoswipe.esm.js';

        // Gallery data
        const photos = {photos_json};
        const musicFiles = {music_json};
        const slideshowDuration = {slideshow_duration * 1000};  // Convert to milliseconds
        
        // State variables
        let slideshowInterval = null;
        let slideshowActive = false;
        let currentTrack = 0;
        
        // Music player setup
        const musicPlayer = document.getElementById('music-player');
        const musicControls = document.getElementById('music-controls');
        const playPauseBtn = document.getElementById('play-pause-music');
        const nowPlaying = document.getElementById('now-playing');
        const volumeSlider = document.getElementById('volume');
        
        if (musicPlayer && musicFiles.length > 0) {{
            // Load first track
            musicPlayer.src = musicFiles[0].path;
            nowPlaying.textContent = musicFiles[0].filename;
            
            // Volume control
            if (volumeSlider) {{
                musicPlayer.volume = 0.7;
                volumeSlider.addEventListener('input', (e) => {{
                    musicPlayer.volume = e.target.value / 100;
                }});
            }}
            
            // Play/Pause button
            if (playPauseBtn) {{
                playPauseBtn.addEventListener('click', () => {{
                    if (musicPlayer.paused) {{
                        musicPlayer.play();
                        playPauseBtn.textContent = '⏸️';
                    }} else {{
                        musicPlayer.pause();
                        playPauseBtn.textContent = '▶️';
                    }}
                }});
            }}
            
            // Auto-play next track
            musicPlayer.addEventListener('ended', () => {{
                currentTrack = (currentTrack + 1) % musicFiles.length;
                musicPlayer.src = musicFiles[currentTrack].path;
                nowPlaying.textContent = musicFiles[currentTrack].filename;
                if (slideshowActive) {{
                    musicPlayer.play();
                }}
            }});
        }}

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
        
        // Slideshow functionality
        const startSlideshowBtn = document.getElementById('start-slideshow');
        
        if (startSlideshowBtn) {{
            startSlideshowBtn.addEventListener('click', () => {{
                // Show music controls
                if (musicControls) {{
                    musicControls.style.display = 'flex';
                }}
                
                // Start music
                if (musicPlayer && musicFiles.length > 0) {{
                    musicPlayer.play().then(() => {{
                        playPauseBtn.textContent = '⏸️';
                    }}).catch(err => {{
                        console.log('Autoplay prevented:', err);
                    }});
                }}
                
                // Open first photo
                lightbox.loadAndOpen(0);
                
                // Request fullscreen
                setTimeout(() => {{
                    if (document.documentElement.requestFullscreen) {{
                        document.documentElement.requestFullscreen().catch(err => {{
                            console.log('Fullscreen request failed:', err);
                        }});
                    }}
                }}, 500);
                
                slideshowActive = true;
            }});
        }}
        
        // PhotoSwipe events
        lightbox.on('change', () => {{
            // Clear existing interval
            if (slideshowInterval) {{
                clearInterval(slideshowInterval);
            }}
            
            // Start new interval if slideshow is active
            if (slideshowActive) {{
                slideshowInterval = setInterval(() => {{
                    const pswp = lightbox.pswp;
                    if (pswp) {{
                        if (pswp.currIndex < photos.length - 1) {{
                            pswp.next();
                        }} else {{
                            // Loop back to start
                            pswp.goTo(0);
                        }}
                    }}
                }}, slideshowDuration);
            }}
        }});
        
        lightbox.on('openingAnimationEnd', () => {{
            if (slideshowActive) {{
                // Start slideshow interval
                slideshowInterval = setInterval(() => {{
                    const pswp = lightbox.pswp;
                    if (pswp) {{
                        if (pswp.currIndex < photos.length - 1) {{
                            pswp.next();
                        }} else {{
                            pswp.goTo(0);
                        }}
                    }}
                }}, slideshowDuration);
            }}
        }});
        
        lightbox.on('close', () => {{
            // Stop slideshow
            slideshowActive = false;
            if (slideshowInterval) {{
                clearInterval(slideshowInterval);
                slideshowInterval = null;
            }}
            
            // Pause music
            if (musicPlayer && !musicPlayer.paused) {{
                musicPlayer.pause();
                if (playPauseBtn) {{
                    playPauseBtn.textContent = '▶️';
                }}
            }}
            
            // Exit fullscreen
            if (document.exitFullscreen && document.fullscreenElement) {{
                document.exitFullscreen();
            }}
        }});
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            const pswp = lightbox.pswp;
            if (!pswp) return;
            
            switch(e.key) {{
                case ' ':  // Space: pause/resume slideshow
                    e.preventDefault();
                    if (slideshowActive) {{
                        if (slideshowInterval) {{
                            clearInterval(slideshowInterval);
                            slideshowInterval = null;
                            if (musicPlayer && !musicPlayer.paused) {{
                                musicPlayer.pause();
                                if (playPauseBtn) playPauseBtn.textContent = '▶️';
                            }}
                        }} else {{
                            slideshowInterval = setInterval(() => {{
                                if (pswp.currIndex < photos.length - 1) {{
                                    pswp.next();
                                }} else {{
                                    pswp.goTo(0);
                                }}
                            }}, slideshowDuration);
                            if (musicPlayer && musicPlayer.paused) {{
                                musicPlayer.play();
                                if (playPauseBtn) playPauseBtn.textContent = '⏸️';
                            }}
                        }}
                    }}
                    break;
                    
                case 'f':  // F: toggle fullscreen
                case 'F':
                    e.preventDefault();
                    if (document.fullscreenElement) {{
                        document.exitFullscreen();
                    }} else if (document.documentElement.requestFullscreen) {{
                        document.documentElement.requestFullscreen();
                    }}
                    break;
            }}
        }});
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
