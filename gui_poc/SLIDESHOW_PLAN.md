# 🎬 Slideshow Feature - Implementation Plan

## ✅ **Ja, Slideshows sind absolut möglich!**

### **Was geplant ist:**

```
🎬 Auto-Play Slideshow
✓ Überblendeffekte (Fade, Slide, Zoom)
✓ Automatic Replay (Loop)
✓ Timing Control (2-10s pro Bild)
✓ Pause/Play
✓ Music Support (optional)
✓ Fullscreen Mode
```

---

## 🎯 **Slideshow Modi:**

### **1. Basic Slideshow (Phase 3)** ⏱️ 2-3h
```javascript
// Simple fade-in/fade-out
Features:
- Auto-advance (5s per photo)
- Fade transition (1s)
- Play/Pause button
- Progress indicator
- Loop on/off
```

### **2. Advanced Slideshow (Phase 4)** ⏱️ 1 Tag
```javascript
// Professional transitions
Features:
- Multiple effects (fade, slide, zoom, pan)
- Ken Burns effect (slow zoom)
- Timing customization (1-30s)
- Speed control (slow/normal/fast)
- Transition speed (0.5-3s)
```

### **3. Cinematic Slideshow (Phase 5)** ⏱️ 2-3 Tage
```javascript
// Hollywood-style
Features:
- Background music
- Title slides
- Text overlays
- Video export (MP4)
- Custom soundtrack
- Beat-sync (music-matched transitions)
```

---

## 🎨 **Transition Effects:**

### **Standard Transitions:**
```css
1. Fade (Cross-dissolve)
   opacity: 0 → 1

2. Slide
   - Slide Left
   - Slide Right
   - Slide Up
   - Slide Down

3. Zoom
   - Zoom In
   - Zoom Out

4. Pan & Zoom (Ken Burns)
   - Slow zoom with pan
   - Professional look
```

### **Advanced Transitions:**
```css
5. Blur → Focus
6. Rotate
7. Flip (3D)
8. Cube (3D)
9. Parallax
10. Mosaic
```

---

## 🚀 **Implementation - Phase 3 (Basic)**

### **Frontend Code:**

```javascript
// Slideshow Component
data() {
    return {
        showSlideshow: false,
        slideshowPhotos: [],
        slideshowIndex: 0,
        slideshowInterval: null,
        slideshowSettings: {
            duration: 5000,      // 5s per photo
            transition: 'fade',  // fade, slide, zoom
            transitionSpeed: 1000, // 1s transition
            loop: true,
            autoStart: true
        }
    }
},

methods: {
    startSlideshow() {
        this.showSlideshow = true;
        this.slideshowPhotos = this.filteredPhotos;
        this.slideshowIndex = 0;
        
        if (this.slideshowSettings.autoStart) {
            this.playSlideshow();
        }
    },
    
    playSlideshow() {
        this.slideshowInterval = setInterval(() => {
            this.nextSlide();
        }, this.slideshowSettings.duration);
    },
    
    pauseSlideshow() {
        if (this.slideshowInterval) {
            clearInterval(this.slideshowInterval);
            this.slideshowInterval = null;
        }
    },
    
    nextSlide() {
        this.slideshowIndex++;
        
        if (this.slideshowIndex >= this.slideshowPhotos.length) {
            if (this.slideshowSettings.loop) {
                this.slideshowIndex = 0;
            } else {
                this.pauseSlideshow();
            }
        }
    },
    
    prevSlide() {
        this.slideshowIndex--;
        if (this.slideshowIndex < 0) {
            this.slideshowIndex = this.slideshowPhotos.length - 1;
        }
    }
}
```

### **CSS Transitions:**

```css
/* Fade Effect */
.slideshow-image {
    animation: fadeIn 1s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* Slide Effect */
@keyframes slideIn {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
}

/* Zoom Effect */
@keyframes zoomIn {
    from { transform: scale(0.8); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}

/* Ken Burns Effect */
@keyframes kenBurns {
    0% { transform: scale(1) translate(0, 0); }
    100% { transform: scale(1.15) translate(-5%, -5%); }
}
```

### **UI Controls:**

```html
<div class="slideshow-controls">
    <button @click="prevSlide">⏮️ Prev</button>
    <button @click="togglePlay">
        {{ isPlaying ? '⏸️ Pause' : '▶️ Play' }}
    </button>
    <button @click="nextSlide">⏭️ Next</button>
    
    <select v-model="slideshowSettings.transition">
        <option value="fade">Fade</option>
        <option value="slide">Slide</option>
        <option value="zoom">Zoom</option>
        <option value="kenburns">Ken Burns</option>
    </select>
    
    <input type="range" 
           v-model="slideshowSettings.duration" 
           min="1000" 
           max="10000" 
           step="500">
    <span>{{ slideshowSettings.duration / 1000 }}s</span>
    
    <label>
        <input type="checkbox" v-model="slideshowSettings.loop">
        Loop
    </label>
    
    <button @click="exitSlideshow">❌ Exit</button>
</div>

<!-- Progress Bar -->
<div class="slideshow-progress">
    <div class="progress-bar" 
         :style="{ width: (slideshowIndex / slideshowPhotos.length * 100) + '%' }">
    </div>
</div>
```

---

## 🎵 **Background Music (Phase 5)**

### **Implementation:**

```javascript
// Audio Player Integration
data() {
    return {
        slideshowAudio: null,
        audioFile: null
    }
},

methods: {
    selectAudioFile() {
        // File picker
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'audio/*';
        input.onchange = (e) => {
            this.audioFile = e.target.files[0];
            this.loadAudio();
        };
        input.click();
    },
    
    loadAudio() {
        this.slideshowAudio = new Audio(URL.createObjectURL(this.audioFile));
        this.slideshowAudio.loop = this.slideshowSettings.loop;
    },
    
    startSlideshowWithMusic() {
        if (this.slideshowAudio) {
            this.slideshowAudio.play();
        }
        this.playSlideshow();
    }
}
```

---

## 📹 **Video Export (Phase 6)**

### **Create MP4 from Slideshow:**

```python
# Backend: photo_tool/actions/video_export.py

def export_slideshow_video(
    photo_paths: List[Path],
    output_video: Path,
    duration_per_photo: float = 5.0,
    transition_duration: float = 1.0,
    audio_file: Optional[Path] = None,
    resolution: tuple = (1920, 1080)
):
    """
    Export slideshow as MP4 video using ffmpeg
    
    Requires: ffmpeg with concat filter
    """
    
    import subprocess
    
    # 1. Create transition clips
    clips = []
    for i, photo in enumerate(photo_paths):
        # Create clip with fade
        clips.append(f"[{i}:v]fade=t=in:st=0:d={transition_duration}[v{i}];")
    
    # 2. Concat all clips
    concat_filter = "".join(clips) + "".join([f"[v{i}]" for i in range(len(clips))]) + f"concat=n={len(clips)}:v=1:a=0[outv]"
    
    # 3. Add audio if provided
    if audio_file:
        audio_input = ['-i', str(audio_file)]
        audio_filter = '-shortest'
    else:
        audio_input = []
        audio_filter = ''
    
    # 4. Run ffmpeg
    cmd = [
        'ffmpeg',
        *[f'-loop 1 -t {duration_per_photo} -i {photo}' for photo in photo_paths],
        *audio_input,
        '-filter_complex', concat_filter,
        '-map', '[outv]',
        audio_filter,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-r', '30',
        str(output_video)
    ]
    
    subprocess.run(cmd, check=True)
    
    return output_video
```

---

## 🎨 **Slideshow UI Mockup:**

```
┌─────────────────────────────────────────────────────┐
│ 🎬 Slideshow Mode               [❌ Exit Fullscreen] │
├─────────────────────────────────────────────────────┤
│                                                       │
│                                                       │
│                   [LARGE PHOTO]                       │
│                  with fade effect                     │
│                                                       │
│                                                       │
├─────────────────────────────────────────────────────┤
│ ████████████░░░░░░░░░░░░░░░░░░░  45 / 100          │
│                                                       │
│ [⏮️] [⏸️ Pause] [⏭️]  [Fade ▼] [5s ▼] [🔁 Loop]  │
│                                                       │
│ 🎵 [Select Music...]  [🎥 Export as Video]         │
└─────────────────────────────────────────────────────┘
```

---

## 📊 **Feature Roadmap:**

### **Phase 3: Basic Slideshow** ⏱️ 2-3h
```
✓ Auto-advance
✓ Fade transition
✓ Play/Pause
✓ Loop mode
✓ Speed control
✓ Progress bar
```

### **Phase 4: Advanced Slideshow** ⏱️ 1 Tag
```
✓ Multiple transitions
✓ Ken Burns effect
✓ Custom timing per photo
✓ Transition speed control
✓ Random order option
✓ Keyboard controls (Space, arrows)
```

### **Phase 5: Cinematic** ⏱️ 2-3 Tage
```
✓ Background music
✓ Title slides
✓ Text overlays
✓ Multiple soundtracks
✓ Beat-sync transitions
✓ Export as MP4 video
```

---

## 🎬 **Slideshow in Exported Galleries:**

### **Add to PhotoSwipe Template:**

```html
<!-- Auto-play slideshow mode -->
<script>
const lightbox = new PhotoSwipeLightbox({
    gallery: '#gallery',
    children: 'a',
    pswpModule: PhotoSwipe
});

// Add slideshow controls
lightbox.on('uiRegister', function() {
    lightbox.pswp.ui.registerElement({
        name: 'slideshow-button',
        order: 9,
        isButton: true,
        html: '🎬',
        onClick: (event, el) => {
            startSlideshow(lightbox.pswp);
        }
    });
});

function startSlideshow(pswp) {
    let interval = setInterval(() => {
        pswp.next();
        
        // Stop at end
        if (pswp.currIndex === pswp.getNumItems() - 1) {
            clearInterval(interval);
        }
    }, 5000);
    
    // Stop on user interaction
    pswp.on('close', () => clearInterval(interval));
}

lightbox.init();
</script>
```

---

## 💡 **Use Cases:**

### **1. Client Presentation:**
```
Export gallery with slideshow
→ Client clicks "🎬 Play"
→ Auto-plays with transitions
→ Professional presentation!
```

### **2. Event Display:**
```
Wedding/Party photos
→ Export with music
→ Play on TV/Projector
→ Loop all night
```

### **3. Portfolio:**
```
Best work slideshow
→ Ken Burns effect
→ Music soundtrack
→ Share link or video
```

### **4. Social Media:**
```
Export as MP4 video
→ Upload to Instagram/YouTube
→ Automatic transitions
→ Music included
```

---

## 🔧 **Technical Details:**

### **CSS Transitions (Lightweight):**
```css
/* Pure CSS, no libraries needed */
.slideshow-image {
    animation: fade 1s ease-in-out;
}

/* 60 FPS smooth */
@keyframes fade {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
}
```

### **JavaScript Animation (Advanced):**
```javascript
// For complex effects
import { gsap } from 'gsap';

gsap.to('.slideshow-image', {
    duration: 1,
    opacity: 1,
    scale: 1.1,
    ease: 'power2.out'
});
```

### **Video Export (ffmpeg):**
```bash
# Generate MP4 from photos
ffmpeg -framerate 1/5 \\
       -i photo_%04d.jpg \\
       -i soundtrack.mp3 \\
       -c:v libx264 \\
       -vf "fade=t=in:d=1,fade=t=out:d=1" \\
       -shortest \\
       slideshow.mp4
```

---

## 🎵 **Music Integration:**

### **Format Support:**
```
✓ MP3 (most common)
✓ WAV (uncompressed)
✓ M4A (AAC)
✓ OGG (open-source)
```

### **Features:**
```
✓ Upload audio file
✓ Auto-loop or stop at end
✓ Fade in/out
✓ Volume control
✓ Multiple tracks (playlist)
✓ Beat detection (advanced)
```

---

## 📦 **Slideshow Export Options:**

### **1. Interactive HTML (lightweight)**
```
✓ Runs in browser
✓ No dependencies
✓ Share link
✓ ~1 MB for 100 photos
```

### **2. Standalone HTML + Music**
```
✓ Embedded audio
✓ One-file gallery
✓ Offline playback
✓ ~10-20 MB
```

### **3. MP4 Video (universal)**
```
✓ Upload anywhere
✓ Instagram, YouTube, etc.
✓ No browser needed
✓ ~50-200 MB (depends on length)
```

---

## 🎯 **Implementation Timeline:**

### **Week 1: Basic Slideshow** ✅ Doable now
```
Day 1-2: Core slideshow logic
Day 3: Transitions (fade, slide)
Day 4: Controls & settings
Day 5: Testing & polish
```

### **Week 2: Advanced Features**
```
Day 1-2: Multiple effects
Day 3: Ken Burns
Day 4: Music integration
Day 5: Export options
```

### **Week 3: Video Export**
```
Day 1-2: ffmpeg integration
Day 3: Audio sync
Day 4: Title slides
Day 5: Batch export
```

---

## 💼 **Real-World Examples:**

### **Wedding Photographer:**
```
1. Filter: 5★ + "wedding" tag
2. Order by timeline
3. Start slideshow (5s per photo)
4. Add romantic music
5. Export as MP4
6. Send to couple
```

### **Travel Blogger:**
```
1. Filter: "austria" + 4-5★
2. Start slideshow with Ken Burns
3. Add travel music
4. Export as HTML
5. Embed in blog post
```

### **Portfolio Presentation:**
```
1. Filter: 5★ + Green + "best"
2. Start cinematic slideshow
3. Professional transitions
4. Export as video
5. Upload to YouTube
```

---

## 📚 **Libraries to Consider:**

### **For Transitions:**
```
1. GSAP (GreenSock)
   - Professional animations
   - 60 FPS smooth
   - https://greensock.com/

2. Swiper.js
   - Touch-enabled
   - Many effects
   - https://swiperjs.com/

3. Reveal.js (for presentations)
   - Slide-based
   - Professional
   - https://revealjs.com/
```

### **For Video Export:**
```
1. ffmpeg (Python subprocess)
   - Industry standard
   - Already installed!

2. moviepy (Python library)
   - Python-native
   - Easier API
   - pip install moviepy
```

---

## 🎯 **Next Steps:**

### **Immediate (Can do now):**
```
1. Add "🎬 Slideshow" button to GUI
2. Implement basic fade slideshow
3. Play/Pause/Loop controls
4. Export slideshow-enabled gallery
```

### **This Week:**
```
1. Multiple transition effects
2. Timing customization
3. Music upload
4. MP4 export (ffmpeg)
```

### **Later:**
```
1. Beat-sync animations
2. Title slides
3. Text overlays
4. Advanced effects
```

---

## 💡 **Answer to your question:**

**Ja, absolut!** Slideshows mit:
- ✅ Überblendeffekten (Fade, Slide, Zoom)
- ✅ Automatic Replay (Loop)
- ✅ Timing Control
- ✅ Music Support
- ✅ Video Export

Sind **definitiv denkbar und planbar**! 🎬✨

**Implementation:**
- Basic: 2-3 Stunden
- Advanced: 1 Woche
- Cinematic with Video Export: 2-3 Wochen

---

## 🚀 **Soll ich JETZT Basic Slideshow implementieren?**

**Das würde bedeuten:**
- 🎬 Play Button in GUI
- ⏸️ Pause/Play Controls
- 🔄 Loop Toggle
- ⏱️ Speed Control (1-10s)
- 🎨 Fade Transition

**Zeit: 2-3 Stunden**

**Oder erst Progress Bar testen?** 🎯
