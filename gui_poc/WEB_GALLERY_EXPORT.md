# 🌐 Web-Gallery Export (Phase 4)

## 📊 **Feature-Überblick**

Export filtered photo selections as standalone web galleries for sharing.

---

## 🎯 **Use Cases**

```
1. Client Presentation
   → Filter: 5★ + Green Label
   → Export gallery
   → Send link to client

2. Portfolio
   → Filter: 5★ best shots
   → Export with PhotoSwipe
   → Upload to website

3. Event Gallery
   → Filter: By keywords ("wedding", "2026")
   → Export gallery
   → Share with attendees

4. Prints Selection
   → Filter: 4-5★ landscape shots
   → Export for review
   → Send to print shop
```

---

## 🚀 **Recommended Gallery System: PhotoSwipe**

### **Why PhotoSwipe?**
```
✓ Modern & Touch-enabled
✓ Mobile-friendly
✓ Lightweight (40KB)
✓ No dependencies
✓ Open-source & Free
✓ Works offline
✓ Great UX
```

### **Live Demo:**
https://photoswipe.com/

---

## 📦 **Export Implementation Plan**

### **Step 1: Backend Export Endpoint** (2h)

```python
# photo_tool/actions/export.py

def export_gallery(
    photos: List[Path],
    output_dir: Path,
    template: str = "photoswipe",
    title: str = "Photo Gallery",
    optimize_images: bool = True
):
    """
    Export photos as standalone web gallery
    
    Args:
        photos: List of photo paths to include
        output_dir: Output directory for gallery
        template: Gallery template (photoswipe, lightgallery, etc.)
        title: Gallery title
        optimize_images: Generate web-optimized images
    """
    
    # 1. Create folder structure
    gallery_dir = output_dir / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    
    (gallery_dir / "images").mkdir(exist_ok=True)
    (gallery_dir / "thumbnails").mkdir(exist_ok=True)
    
    # 2. Copy & optimize images
    photo_data = []
    for i, photo in enumerate(photos):
        # Copy original (or resize to max 2000px)
        if optimize_images:
            img_path = _resize_image(photo, gallery_dir / "images" / f"{i:04d}.jpg", max_size=2000)
        else:
            shutil.copy(photo, gallery_dir / "images" / f"{i:04d}.jpg")
        
        # Generate thumbnail
        thumb_path = _generate_thumbnail(photo, gallery_dir / "thumbnails" / f"{i:04d}.jpg", size=300)
        
        # Get metadata
        metadata = get_metadata(photo)
        
        photo_data.append({
            'src': f"images/{i:04d}.jpg",
            'thumbnail': f"thumbnails/{i:04d}.jpg",
            'width': 2000,  # or actual width
            'height': 1333,  # or actual height
            'title': photo.name,
            'rating': metadata.get('rating', 0),
            'color': metadata.get('color'),
            'keywords': metadata.get('keywords', [])
        })
    
    # 3. Generate HTML from template
    template_html = _load_template(template)
    html = template_html.format(
        title=title,
        photos_json=json.dumps(photo_data, indent=2),
        total_photos=len(photos)
    )
    
    # 4. Write index.html
    (gallery_dir / "index.html").write_text(html, encoding='utf-8')
    
    return gallery_dir
```

### **Step 2: PhotoSwipe Template** (1h)

```html
<!-- templates/photoswipe.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    
    <!-- PhotoSwipe CSS -->
    <link rel="stylesheet" href="https://unpkg.com/photoswipe/dist/photoswipe.css">
    
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: system-ui, -apple-system, sans-serif;
            background: #0a0a0a;
            color: #fff;
        }
        .header {
            padding: 30px;
            text-align: center;
            background: rgba(255,255,255,0.05);
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #888;
            font-size: 1.1rem;
        }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
            padding: 30px;
            max-width: 1800px;
            margin: 0 auto;
        }
        .gallery-item {
            position: relative;
            cursor: pointer;
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.3s;
        }
        .gallery-item:hover {
            transform: scale(1.05);
        }
        .gallery-item img {
            width: 100%;
            height: 250px;
            object-fit: cover;
            display: block;
        }
        .photo-info {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.8));
            padding: 15px 10px 10px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .gallery-item:hover .photo-info {
            opacity: 1;
        }
        .stars {
            color: gold;
            font-size: 0.9rem;
        }
        .color-badge {
            position: absolute;
            top: 10px;
            left: 10px;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 2px solid #fff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }
        .footer {
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <div class="subtitle">{{ total_photos }} photos</div>
    </div>

    <div class="gallery" id="gallery">
        <!-- Generated by JavaScript -->
    </div>

    <div class="footer">
        Generated with Photo Tool | {{ date }}
    </div>

    <!-- PhotoSwipe JS -->
    <script type="module">
        import PhotoSwipeLightbox from 'https://unpkg.com/photoswipe/dist/photoswipe-lightbox.esm.js';
        import PhotoSwipe from 'https://unpkg.com/photoswipe/dist/photoswipe.esm.js';

        const photos = {{ photos_json }};

        // Generate gallery HTML
        const gallery = document.getElementById('gallery');
        photos.forEach((photo, index) => {
            const item = document.createElement('a');
            item.href = photo.src;
            item.className = 'gallery-item';
            item.setAttribute('data-pswp-width', photo.width);
            item.setAttribute('data-pswp-height', photo.height);

            let html = `<img src="${photo.thumbnail}" alt="${photo.title}">`;
            
            if (photo.color) {
                const colors = {
                    red: '#ef4444',
                    yellow: '#fbbf24',
                    green: '#4ade80',
                    blue: '#3b82f6',
                    purple: '#a855f7'
                };
                html += `<div class="color-badge" style="background: ${colors[photo.color]}"></div>`;
            }

            if (photo.rating > 0) {
                const stars = '★'.repeat(photo.rating) + '☆'.repeat(5 - photo.rating);
                html += `<div class="photo-info"><div class="stars">${stars}</div></div>`;
            }

            item.innerHTML = html;
            gallery.appendChild(item);
        });

        // Initialize PhotoSwipe
        const lightbox = new PhotoSwipeLightbox({
            gallery: '#gallery',
            children: 'a',
            pswpModule: PhotoSwipe
        });
        lightbox.init();
    </script>
</body>
</html>
```

### **Step 3: GUI Export Button** (1h)

```html
<!-- In GUI: Add export button -->
<div class="action-bar">
    <button @click="exportGallery" class="export-btn">
        📦 Export Gallery ({{ filteredPhotos.length }} photos)
    </button>
</div>

<script>
async exportGallery() {
    if (this.filteredPhotos.length === 0) {
        alert('No photos to export!');
        return;
    }

    // Get photo IDs
    const photoIds = this.filteredPhotos.map(p => p.id);

    // Call export endpoint
    const res = await fetch('/api/export/gallery', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            photo_ids: photoIds,
            title: prompt('Gallery title:', 'My Photo Gallery'),
            template: 'photoswipe',
            optimize: true
        })
    });

    const data = await res.json();

    if (data.success) {
        alert(`Gallery exported to: ${data.output_path}\nOpen index.html to view!`);
    }
}
</script>
```

---

## 🎨 **Alternative Gallery Templates**

### **1. Lightgallery.js**
```
More features, social sharing
https://www.lightgalleryjs.com/
```

### **2. Nanogallery2**
```
Masonry/Grid layouts
https://nanogallery2.nanostudio.org/
```

### **3. Custom Grid**
```
Simple CSS Grid (no dependencies)
Perfect for portfolios
```

---

## 📤 **Deployment Options**

### **1. Static Hosting (Free)**
```
Netlify Drop: https://app.netlify.com/drop
Vercel: https://vercel.com/
GitHub Pages: https://pages.github.com/
```

### **2. Own Website**
```
Upload via FTP to:
https://yoursite.com/galleries/2026-sunset/
```

### **3. Cloud Storage**
```
Google Drive (public link)
Dropbox (shared folder)
AWS S3 (static website)
```

---

## 🔗 **Sharing & Linking**

### **Generated URLs:**
```
https://yoursite.com/gallery-2026-sunset/

Shareable:
- Email link
- QR code
- Social media
- Embedded in blog
```

### **Features:**
```html
<!-- Share buttons -->
<div class="share-buttons">
    <button onclick="shareTwitter()">Share on Twitter</button>
    <button onclick="shareWhatsApp()">Share on WhatsApp</button>
    <button onclick="copyLink()">Copy Link</button>
</div>
```

---

## 📊 **Gallery Statistics**

### **Track Views (Optional):**
```html
<!-- Simple analytics -->
<script>
  // Google Analytics
  gtag('event', 'gallery_view', {
    'gallery_name': '{{ title }}',
    'photo_count': {{ total_photos }}
  });
</script>
```

---

## 🎯 **Next Steps**

1. ✅ **Implement backend export** (2h)
2. ✅ **Create PhotoSwipe template** (1h)
3. ✅ **Add GUI export button** (1h)
4. ✅ **Test with filtered selection**
5. ✅ **Deploy to Netlify/Vercel**

**Total: ~4-5 hours for Phase 4 feature** 🚀

---

## 💡 **Advanced Features (Later)**

```
- Password protection
- Download buttons
- EXIF info overlay
- Comments/Likes
- Slideshow mode
- Print ordering integration
- Custom branding/logo
```

---

**Ready to implement when you are!** 🌐✨
