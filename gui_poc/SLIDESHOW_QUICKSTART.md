# 🎬 Slideshow Quick Start

## ✅ **Basic Slideshow ist JETZT live!**

---

## 🚀 **Wie starten?**

### **1. Server starten:**
```powershell
cd C:\_Git\Python-tools
python gui_poc/server.py
```

### **2. Browser öffnen:**
```
http://localhost:8000
```

### **3. Slideshow starten:**
```
1. Photos filtern (optional)
   - Rating filter
   - Color labels
   - Keywords
   
2. "🎬 Slideshow" Button klicken

3. Auto-Play startet automatisch!
```

---

## ⌨️ **Keyboard Shortcuts:**

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `←` | Previous photo |
| `→` | Next photo |
| `↑` | Increase speed (+1s) |
| `↓` | Decrease speed (-1s) |
| `L` | Toggle loop on/off |
| `F` | Toggle fullscreen 🆕 |
| `ESC` | Exit fullscreen / Exit slideshow |

---

## 🎨 **Features:**

### **✅ Implemented:**

#### **Auto-Play**
- Starts automatically
- Smooth fade transitions (1s)
- Configurable duration (2-10s)

#### **Controls**
- ▶️ Play / ⏸️ Pause
- ⏮️ Previous / Next ⏭️
- ⛶ **Fullscreen** (True fullscreen, no browser UI!) 🆕
- Progress bar
- Photo counter (X / Total)

#### **Settings**
- **Speed:** 2s, 3s, 5s, 7s, 10s
- **Loop:** On/Off
- **Transition:** Fade (1s)

#### **Keyboard Navigation**
- Space: Play/Pause
- Arrows: Navigate
- F: Toggle fullscreen 🆕
- ESC: Exit fullscreen / Exit slideshow
- Up/Down: Change speed
- L: Toggle loop

---

## 🎯 **Use Cases:**

### **1. Quick Review:**
```
1. Filter: Rating ≥ 4
2. Start slideshow
3. Review automatically
4. Pause on interesting photos
```

### **2. Party Background:**
```
1. Filter: 5★ + Color: Green
2. Start slideshow
3. Set speed: 7s
4. Enable loop
5. Fullscreen (F11)
6. Let it run all night!
```

### **3. Client Presentation:**
```
1. Filter: Client photos
2. Start slideshow
3. Set speed: 5s
4. Professional presentation!
5. Pause to discuss specific shots
```

---

## 📊 **Technical Details:**

### **Fade Transition:**
```css
/* Smooth 1s fade effect */
transition: opacity 1s ease-in-out;
```

### **Auto-advance:**
```javascript
// Configurable duration
setInterval(() => {
    nextSlide();
}, settings.duration * 1000);
```

### **Loop behavior:**
```javascript
// At end of slideshow:
if (loop) {
    slideshowIndex = 0;  // Start over
} else {
    stopSlideshow();     // Stop playing
}
```

---

## 🎬 **Example Workflow:**

### **Wedding Photos:**
```
1. Scan & Rate photos
2. Filter: 4-5★
3. Color label: Red (favorites)
4. Start slideshow
5. Speed: 7s (slow)
6. Loop: ON
7. Run on Smart TV! 📺
```

### **Portfolio:**
```
1. Filter: 5★ + Green
2. Keywords: "portfolio"
3. Start slideshow
4. Speed: 5s
5. Professional presentation
```

### **Burst Review:**
```
1. Go to Bursts tab
2. Select burst group
3. Review best shots
4. Rate favorites
5. Back to Photos → Slideshow
```

---

## 🚀 **What's NEXT? (Advanced Slideshow)**

### **Phase 4: Advanced Transitions** (1 week)
```
✓ Multiple effects (slide, zoom)
✓ Ken Burns effect (slow zoom + pan)
✓ Transition speed control
✓ Random order
```

### **Phase 5: Cinematic** (2-3 weeks)
```
✓ Background music
✓ Title slides
✓ Text overlays
✓ Beat-sync transitions
✓ Export as MP4 video
```

---

## 📺 **Smart TV Slideshow:**

**Siehe:** `SMART_TV_QUICKSTART.md`

```
1. Server: host='0.0.0.0'
2. Firewall: Port 8000 freigeben
3. TV Browser: http://192.168.1.X:8000
4. Slideshow starten
5. TV-Fernbedienung nutzen!
```

---

## 🎨 **Current Limitations:**

### **What's NOT yet implemented:**
- ❌ Multiple transition effects (only fade)
- ❌ Ken Burns (zoom + pan)
- ❌ Music
- ❌ Title slides
- ❌ Video export

### **Coming soon!**
All advanced features are planned for Phase 4 & 5!

---

## 💡 **Tips & Tricks:**

### **Best Speed Settings:**
```
2s  - Quick review
3s  - Normal pace
5s  - Comfortable viewing
7s  - Large TV, slow pace
10s - Background display
```

### **Loop vs. One-time:**
```
Loop ON  → Background display, parties
Loop OFF → Presentations, reviews
```

### **Keyboard Speed Adjustment:**
```
While playing:
- Press ↑ to increase speed (+1s)
- Press ↓ to decrease speed (-1s)
- Real-time adjustment!
```

### **Smart TV Remote:**
```
Most TV remotes work:
- OK/Enter   → Toggle play/pause
- Arrows     → Navigate
- Back/Exit  → Close slideshow
```

---

## 🔧 **Troubleshooting:**

### **Slideshow button not visible:**
```
→ Make sure you're on "All Photos" tab
→ At least 1 photo must be visible (check filters)
```

### **Photos don't advance:**
```
→ Check if slideshow is playing (Play button)
→ Try Space key to play/pause
```

### **Transitions too fast/slow:**
```
→ Use Speed dropdown (2-10s)
→ Or use ↑↓ arrow keys while playing
```

### **Photos appear small:**
```
→ Full-size images are loaded automatically
→ If still small, check image.full_image fallback
→ May take a moment on first load
```

---

## 📚 **Documentation:**

### **User Guides:**
- `SLIDESHOW_QUICKSTART.md` (this file)
- `SLIDESHOW_PLAN.md` (full roadmap)
- `SMART_TV_QUICKSTART.md` (TV setup)
- `KEYBOARD_SHORTCUTS.md` (all shortcuts)

### **Developer:**
- See `index.html` lines 1636-1711 (Slideshow HTML)
- See `index.html` lines 2506-2646 (Slideshow methods)
- CSS: Lines 963-1143

---

## 🎯 **Testing Checklist:**

### **Basic Functionality:**
```
✅ Slideshow button appears
✅ Slideshow starts automatically
✅ Photos fade in/out smoothly
✅ Progress bar updates
✅ Photo counter shows X/Total
```

### **Controls:**
```
✅ Play/Pause works
✅ Previous/Next buttons work
✅ Speed dropdown changes speed
✅ Loop checkbox toggles loop
✅ Exit button closes slideshow
```

### **Keyboard:**
```
✅ Space toggles play/pause
✅ Arrows navigate photos
✅ ↑↓ change speed
✅ L toggles loop
✅ ESC exits
```

### **Edge Cases:**
```
✅ Works with 1 photo
✅ Works with 1000+ photos
✅ Loop at end (if enabled)
✅ Stop at end (if loop disabled)
✅ Settings persist during playback
```

---

## 🎉 **Enjoy your Slideshow!**

**Any issues?** Check:
1. Browser console (F12)
2. Server logs
3. This documentation

**Feature requests?** See:
- `SLIDESHOW_PLAN.md` for roadmap
- `FEATURES.md` for all planned features

---

## 🚀 **Next Steps:**

### **Now:**
```
1. Test basic slideshow
2. Try different filters
3. Experiment with speeds
4. Test on Smart TV
```

### **Soon (Phase 4):**
```
1. Multiple transition effects
2. Ken Burns effect
3. Music support
4. Advanced controls
```

### **Later (Phase 5):**
```
1. Title slides
2. Text overlays
3. MP4 video export
4. Beat-sync animations
```

**Viel Spaß! 🎬✨**
