"""
Simple gallery template with working slideshow (from GUI)
No PhotoSwipe, no color badges - just clean gallery + slideshow
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional


def generate_slideshow_gallery_html(
    title: str,
    photos: List[Dict[str, Any]],
    music_data: Optional[List[Dict[str, str]]] = None,
    slideshow_duration: int = 5,
    smart_tv_mode: bool = False
) -> str:
    """Generate simple gallery with working slideshow (from GUI)"""
    
    photos_json = json.dumps(photos, indent=2)
    music_json = json.dumps(music_data or [], indent=2)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # TV mode adjustments
    tv_button_style = "font-size: 1.5rem; padding: 15px 35px;" if smart_tv_mode else ""
    
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
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #fff;
            min-height: 100vh;
        }}
        
        /* Header */
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
        
        /* Controls */
        .controls {{
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 20px;
        }}
        
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            {tv_button_style}
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #4ade80, #3b82f6);
            color: #fff;
        }}
        
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(74, 222, 128, 0.4);
        }}
        
        /* Gallery Grid */
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            padding: 40px 30px;
            max-width: 1800px;
            margin: 0 auto;
        }}
        
        .gallery-item {{
            cursor: pointer;
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.3s;
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
        
        /* Slideshow */
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
            display: none;
        }}
        
        .slideshow.active {{
            display: flex;
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
            background: linear-gradient(to bottom, rgba(0,0,0,0.8) 0%, transparent 100%);
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
            max-width: 95%;
            max-height: 95%;
            object-fit: contain;
        }}
        
        .slideshow-footer {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 20px 30px;
            background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, transparent 100%);
            z-index: 100;
            transition: opacity 0.3s ease, transform 0.3s ease;
        }}
        
        .slideshow.hide-controls .slideshow-footer {{
            opacity: 0;
            transform: translateY(100%);
            pointer-events: none;
        }}
        
        .slideshow-progress {{
            margin-bottom: 15px;
        }}
        
        .slideshow-progress-bar {{
            height: 4px;
            background: rgba(255,255,255,0.2);
            border-radius: 2px;
            overflow: hidden;
        }}
        
        .slideshow-progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4ade80, #3b82f6);
            transition: width 0.3s;
        }}
        
        .slideshow-controls {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
        }}
        
        .slideshow-btn {{
            padding: 10px 20px;
            background: rgba(255,255,255,0.1);
            border: none;
            color: #fff;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.2s;
            {tv_button_style}
        }}
        
        .slideshow-btn:hover:not(:disabled) {{
            background: rgba(255,255,255,0.2);
            transform: translateY(-2px);
        }}
        
        .slideshow-btn:disabled {{
            opacity: 0.3;
            cursor: not-allowed;
        }}
        
        .slideshow-btn.primary {{
            background: linear-gradient(135deg, #4ade80, #3b82f6);
        }}
        
        .slideshow-settings {{
            display: flex;
            gap: 15px;
            align-items: center;
        }}
        
        .slideshow-setting {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
        }}
        
        .slideshow-setting select {{
            padding: 6px 12px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: #fff;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
        }}
        
        .mode-toggle {{
            display: flex;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            overflow: hidden;
        }}
        
        .mode-toggle button {{
            padding: 8px 16px;
            background: transparent;
            border: none;
            color: #fff;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
        }}
        
        .mode-toggle button.active {{
            background: linear-gradient(135deg, #4ade80, #3b82f6);
            font-weight: 600;
        }}
        
        /* Music Controls */
        .music-controls {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 16px;
            background: rgba(255,255,255,0.05);
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
        
        .footer {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 0.9rem;
        }}
        
        @media (max-width: 768px) {{
            .gallery {{
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
                padding: 20px 15px;
            }}
            h1 {{ font-size: 2rem; }}
            .controls {{ flex-direction: column; }}
            .btn {{ width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="subtitle">{len(photos)} photos</div>
        
        <div class="controls">
            <button class="btn btn-primary" onclick="startSlideshow()">
                🎬 Start Slideshow
            </button>
            
            {'<div class="music-controls" id="music-controls" style="display: none;"><button id="play-pause-music" onclick="toggleMusic()">▶️</button><span id="now-playing">No music</span><input type="range" id="volume" class="volume-slider" min="0" max="100" value="70" oninput="setVolume(this.value)"></div>' if music_data else ''}
        </div>
    </div>

    <div class="gallery" id="gallery"></div>

    <div class="footer">
        Generated with Photo Tool | {now}
    </div>

    <!-- Slideshow -->
    <div id="slideshow" class="slideshow">
        <div class="slideshow-header">
            <div class="slideshow-title">
                <span>🎬</span>
                <span>Slideshow</span>
                <span style="color: #888; font-size: 0.9rem; margin-left: 10px;">
                    <span id="current-index">1</span> / <span id="total-photos">{len(photos)}</span>
                </span>
            </div>
            <div style="display: flex; gap: 10px;">
                <button class="slideshow-btn" onclick="toggleFullscreen()">
                    <span id="fullscreen-text">⛶ Fullscreen</span>
                </button>
                <button class="slideshow-btn" onclick="exitSlideshow()">
                    ❌ Exit
                </button>
            </div>
        </div>
        
        <div class="slideshow-main" id="slideshow-main" onclick="togglePlay()"></div>
        
        <div class="slideshow-footer">
            <div class="slideshow-progress">
                <div class="slideshow-progress-bar">
                    <div class="slideshow-progress-fill" id="progress-fill"></div>
                </div>
            </div>
            
            <div class="slideshow-controls">
                <button class="slideshow-btn" onclick="prevSlide()" id="prev-btn">
                    ⏮️ Prev
                </button>
                
                <button class="slideshow-btn primary" onclick="togglePlay()" id="play-btn">
                    ▶️ Play
                </button>
                
                <button class="slideshow-btn" onclick="nextSlide()" id="next-btn">
                    Next ⏭️
                </button>
                
                <div class="slideshow-settings">
                    <div class="mode-toggle">
                        <button id="mode-auto" class="active" onclick="setMode('auto')">Auto</button>
                        <button id="mode-manual" onclick="setMode('manual')">Manual</button>
                    </div>
                    
                    <div class="slideshow-setting" id="speed-setting">
                        <span>Speed:</span>
                        <select id="duration-select" onchange="changeDuration()">
                            <option value="2">2s</option>
                            <option value="3">3s</option>
                            <option value="5" selected>5s</option>
                            <option value="7">7s</option>
                            <option value="10">10s</option>
                            <option value="15">15s</option>
                        </select>
                    </div>
                    
                    <div class="slideshow-setting">
                        <input type="checkbox" id="loop-checkbox" checked>
                        <label for="loop-checkbox">Loop</label>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Hidden Audio Player -->
    {'<audio id="music-player" preload="auto"></audio>' if music_data else ''}

    <script>
        const photos = {photos_json};
        const musicFiles = {music_json};
        let currentIndex = 0;
        let playing = false;
        let interval = null;
        let duration = {slideshow_duration};
        let hideControlsTimeout = null;
        let mode = 'auto'; // 'auto' or 'manual'
        let touchStartX = 0;
        let touchEndX = 0;
        
        // Music player
        const musicPlayer = document.getElementById('music-player');
        const musicControls = document.getElementById('music-controls');
        const playPauseBtn = document.getElementById('play-pause-music');
        const nowPlaying = document.getElementById('now-playing');
        let currentTrack = 0;
        
        if (musicPlayer && musicFiles.length > 0) {{
            musicPlayer.src = musicFiles[0].path;
            nowPlaying.textContent = musicFiles[0].filename;
            musicPlayer.volume = 0.7;
            
            musicPlayer.addEventListener('ended', () => {{
                currentTrack = (currentTrack + 1) % musicFiles.length;
                musicPlayer.src = musicFiles[currentTrack].path;
                nowPlaying.textContent = musicFiles[currentTrack].filename;
                if (playing) musicPlayer.play();
            }});
        }}
        
        function toggleMusic() {{
            if (musicPlayer.paused) {{
                musicPlayer.play();
                playPauseBtn.textContent = '⏸️';
            }} else {{
                musicPlayer.pause();
                playPauseBtn.textContent = '▶️';
            }}
        }}
        
        function setVolume(value) {{
            if (musicPlayer) musicPlayer.volume = value / 100;
        }}
        
        // Generate gallery grid
        const gallery = document.getElementById('gallery');
        photos.forEach((photo, index) => {{
            const item = document.createElement('div');
            item.className = 'gallery-item';
            item.onclick = () => {{
                currentIndex = index;
                startSlideshow();
            }};
            item.innerHTML = `<img src="${{photo.thumbnail}}" alt="${{photo.title}}" loading="lazy">`;
            gallery.appendChild(item);
        }});
        
        // Generate slideshow images
        const slideshowMain = document.getElementById('slideshow-main');
        photos.forEach((photo, index) => {{
            const container = document.createElement('div');
            container.className = 'slideshow-image-container' + (index === 0 ? ' active' : '');
            container.innerHTML = `<img src="${{photo.src}}" alt="${{photo.title}}" class="slideshow-image">`;
            slideshowMain.appendChild(container);
        }});
        
        function startSlideshow() {{
            const slideshow = document.getElementById('slideshow');
            slideshow.classList.add('active');
            updateSlideshow();
            
            // Start in selected mode
            if (mode === 'auto') {{
                play();
            }} else {{
                pause();
            }}
            
            // Start music
            if (musicPlayer && musicFiles.length > 0) {{
                musicControls.style.display = 'flex';
                musicPlayer.play().catch(() => {{}});
                if (playPauseBtn) playPauseBtn.textContent = '⏸️';
            }}
            
            // Request fullscreen on the slideshow element
            setTimeout(() => {{
                if (slideshow.requestFullscreen) {{
                    slideshow.requestFullscreen().catch(() => {{}});
                }} else if (slideshow.webkitRequestFullscreen) {{
                    slideshow.webkitRequestFullscreen();
                }} else if (slideshow.mozRequestFullScreen) {{
                    slideshow.mozRequestFullScreen();
                }} else if (slideshow.msRequestFullscreen) {{
                    slideshow.msRequestFullscreen();
                }}
            }}, 500);
            
            resetHideControls();
        }}
        
        function exitSlideshow() {{
            document.getElementById('slideshow').classList.remove('active');
            pause();
            
            // Pause music
            if (musicPlayer && !musicPlayer.paused) {{
                musicPlayer.pause();
                if (playPauseBtn) playPauseBtn.textContent = '▶️';
            }}
            
            // Exit fullscreen
            if (document.fullscreenElement) {{
                document.exitFullscreen();
            }}
        }}
        
        function updateSlideshow() {{
            const containers = document.querySelectorAll('.slideshow-image-container');
            containers.forEach((c, i) => {{
                c.classList.toggle('active', i === currentIndex);
            }});
            
            document.getElementById('current-index').textContent = currentIndex + 1;
            document.getElementById('progress-fill').style.width = 
                ((currentIndex + 1) / photos.length * 100) + '%';
            
            document.getElementById('prev-btn').disabled = currentIndex === 0;
            document.getElementById('next-btn').disabled = currentIndex === photos.length - 1;
        }}
        
        function nextSlide() {{
            if (currentIndex < photos.length - 1) {{
                currentIndex++;
                updateSlideshow();
            }} else if (document.getElementById('loop-checkbox').checked) {{
                currentIndex = 0;
                updateSlideshow();
            }} else {{
                pause();
            }}
        }}
        
        function prevSlide() {{
            if (currentIndex > 0) {{
                currentIndex--;
                updateSlideshow();
            }}
        }}
        
        function play() {{
            playing = true;
            document.getElementById('play-btn').textContent = '⏸️ Pause';
            interval = setInterval(nextSlide, duration * 1000);
        }}
        
        function pause() {{
            playing = false;
            document.getElementById('play-btn').textContent = '▶️ Play';
            if (interval) {{
                clearInterval(interval);
                interval = null;
            }}
        }}
        
        function togglePlay() {{
            if (playing) pause();
            else play();
        }}
        
        function changeDuration() {{
            duration = parseInt(document.getElementById('duration-select').value);
            if (playing) {{
                pause();
                play();
            }}
        }}
        
        function setMode(newMode) {{
            mode = newMode;
            
            // Update button states
            document.getElementById('mode-auto').classList.toggle('active', mode === 'auto');
            document.getElementById('mode-manual').classList.toggle('active', mode === 'manual');
            
            // Show/hide speed setting
            document.getElementById('speed-setting').style.display = mode === 'auto' ? 'flex' : 'none';
            
            // Update playback
            if (mode === 'auto' && document.getElementById('slideshow').classList.contains('active')) {{
                if (!playing) play();
            }} else {{
                pause();
            }}
        }}
        
        function toggleFullscreen() {{
            const slideshow = document.getElementById('slideshow');
            
            if (document.fullscreenElement || document.webkitFullscreenElement || 
                document.mozFullScreenElement || document.msFullscreenElement) {{
                
                if (document.exitFullscreen) {{
                    document.exitFullscreen();
                }} else if (document.webkitExitFullscreen) {{
                    document.webkitExitFullscreen();
                }} else if (document.mozCancelFullScreen) {{
                    document.mozCancelFullScreen();
                }} else if (document.msExitFullscreen) {{
                    document.msExitFullscreen();
                }}
                document.getElementById('fullscreen-text').textContent = '⛶ Fullscreen';
            }} else {{
                if (slideshow.requestFullscreen) {{
                    slideshow.requestFullscreen();
                }} else if (slideshow.webkitRequestFullscreen) {{
                    slideshow.webkitRequestFullscreen();
                }} else if (slideshow.mozRequestFullScreen) {{
                    slideshow.mozRequestFullScreen();
                }} else if (slideshow.msRequestFullscreen) {{
                    slideshow.msRequestFullscreen();
                }}
                document.getElementById('fullscreen-text').textContent = '⛶ Exit Fullscreen';
            }}
        }}
        
        // Auto-hide controls
        function resetHideControls() {{
            const slideshow = document.getElementById('slideshow');
            slideshow.classList.remove('hide-controls');
            
            if (hideControlsTimeout) clearTimeout(hideControlsTimeout);
            
            hideControlsTimeout = setTimeout(() => {{
                if (playing) slideshow.classList.add('hide-controls');
            }}, 3000);
        }}
        
        document.getElementById('slideshow').addEventListener('mousemove', resetHideControls);
        document.getElementById('slideshow').addEventListener('click', resetHideControls);
        
        // Touch Events for Swipe (Mobile/Tablet)
        const slideshowMain = document.getElementById('slideshow-main');
        
        slideshowMain.addEventListener('touchstart', (e) => {{
            touchStartX = e.changedTouches[0].screenX;
        }}, false);
        
        slideshowMain.addEventListener('touchend', (e) => {{
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }}, false);
        
        function handleSwipe() {{
            const swipeThreshold = 50;
            const diff = touchStartX - touchEndX;
            
            if (Math.abs(diff) > swipeThreshold) {{
                if (diff > 0) {{
                    // Swipe left - next
                    nextSlide();
                }} else {{
                    // Swipe right - prev
                    prevSlide();
                }}
                resetHideControls();
            }}
        }}
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {{
            if (!document.getElementById('slideshow').classList.contains('active')) return;
            
            switch(e.key) {{
                case 'ArrowRight':
                case 'ArrowDown':
                case 'PageDown':
                    e.preventDefault();
                    nextSlide();
                    resetHideControls();
                    break;
                case 'ArrowLeft':
                case 'ArrowUp':
                case 'PageUp':
                    e.preventDefault();
                    prevSlide();
                    resetHideControls();
                    break;
                case ' ':
                    e.preventDefault();
                    if (mode === 'auto') {{
                        togglePlay();
                    }} else {{
                        nextSlide();
                    }}
                    resetHideControls();
                    break;
                case 'f':
                case 'F':
                    e.preventDefault();
                    toggleFullscreen();
                    break;
                case 'm':
                case 'M':
                    e.preventDefault();
                    setMode(mode === 'auto' ? 'manual' : 'auto');
                    resetHideControls();
                    break;
                case 'Escape':
                    if (document.fullscreenElement || document.webkitFullscreenElement || 
                        document.mozFullScreenElement || document.msFullscreenElement) {{
                        toggleFullscreen();
                    }} else {{
                        exitSlideshow();
                    }}
                    break;
            }}
        }});
        
        // Set initial duration from export
        document.getElementById('duration-select').value = duration;
        
        // Set initial mode display
        setMode('auto');
    </script>
</body>
</html>'''
