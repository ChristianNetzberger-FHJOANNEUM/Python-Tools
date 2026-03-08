# 🎬 Splash Screen Customization Guide

Your exported slideshow now includes a beautiful splash screen with customizable text and images!

---

## ✨ **What You Can Customize**

### **1. 🎬 Custom Welcome Photo**

- **Filename:** `splash.jpg` (place in gallery root, same folder as `index.html`)
- **Fallback:** If `splash.jpg` is missing, the first photo from your gallery is automatically used.
- **Recommended Size:** 1920×1280 or similar (matching your export resolution)

### **2. ✍️ Custom Text**

Configure via the **Export Modal** in the Photo Tool:

- **Title** (e.g., "Pasang weds Lhamu")
- **Subtitle** (e.g., "December 2025")

**Defaults if left empty:**
- Title → Gallery name
- Subtitle → Photo count + music indicator

**✅ Persistent Settings:** Your text settings are automatically saved in `localStorage` and restored when you reopen the export modal!

---

## 📐 **Layout Design**

```
┌─────────────────────────────┐
│                             │
│   [Splash Photo - 2/3]      │  ← Your custom image (splash.jpg)
│                             │
├─────────────────────────────┤
│   Title Text                │
│   [▶ PLAY BUTTON]           │  ← Large, centered, mobile-friendly
│   Subtitle Text             │  ← Lower 1/3 UI
└─────────────────────────────┘
```

**Key Features:**
- ✅ Large play button (120×140px) for mobile users
- ✅ Respects browser autoplay policies (requires explicit user interaction)
- ✅ Music and slideshow start together on button click

---

## 🚀 **How to Use**

### **Step 1: Prepare Your Splash Photo**

```powershell
# Copy a photo from your exported gallery
copy "C:\PhotoTool_Test\exports\pasang-wedding\gallery\images\0042.jpg" "C:\_Git\Slideshows\Pasang-Wedding\splash.jpg"
```

### **Step 2: Export with Custom Text**

1. Open the **Export Modal** in the Photo Tool
2. Scroll to **Slideshow Settings**
3. Fill in the **"Splash Screen Text"** fields:
   - Title: `Pasang weds Lhamu`
   - Subtitle: `December 2025`
4. Click **Export Gallery**

**💡 Settings are automatically saved!** Next time you export, your text will be pre-filled.

### **Step 3: Test Your Slideshow**

```powershell
# Run the dedicated slideshow server
python serve_slideshow.py
```

Open the URL shown (e.g., `http://192.168.0.110:8000`) on your smartphone!

---

## ❓ **FAQ**

**Q: Where does `splash.jpg` go?**
A: **Gallery root** (same folder as `index.html`). Example:
```
C:\_Git\Slideshows\Pasang-Wedding\
├── index.html
├── splash.jpg  ← HERE!
├── images/
└── thumbnails/
```

**Q: Can I use any photo from the gallery?**
A: Yes! Just copy it to the root and rename to `splash.jpg`.

**Q: What if I don't provide custom text?**
A: Defaults are used:
- Title → Gallery name (e.g., "Pasang Wedding Slideshow")
- Subtitle → "234 photos • Background music"

**Q: Do I need to re-export to change the splash photo?**
A: **No!** Just replace `splash.jpg` in the deployed gallery folder. The slideshow picks it up automatically (no re-export needed).

**Q: Why is the play button so large?**
A: Mobile UX! Smartphones require explicit user interaction to play audio. A large, visible button ensures users can easily start the experience.

**Q: Are my settings saved?**
A: **Yes!** Export settings (text, profiles, music, etc.) are automatically saved to `localStorage` and persist across sessions. No need to re-enter everything!

---

## 🎨 **Design Specs**

| Element | Desktop | Mobile |
|---------|---------|--------|
| Play Button | 140×140px | 120×120px |
| Splash Photo | 2/3 height | 2/3 height |
| UI Section | 1/3 height | 1/3 height |
| Title Font | 3rem | 2rem |
| Subtitle Font | 1.5rem | 1.2rem |

---

**🎉 Enjoy your custom splash screen!**
