# 🖼️ Export-Optimierung für Smart TV & Web

Photo Tool unterstützt jetzt **intelligente Export-Profile** für verschiedene Verwendungszwecke.

---

## 🎯 Export-Profile

### **1. Smart TV (4K) - `smart_tv`**
```yaml
Für: Samsung/LG Smart TV über NAS
Auflösung: 3840 × 2160 (4K UHD)
JPEG Qualität: 92 (sehr hoch)
Thumbnail: 600px, Q85
Dateigröße: ~2-5 MB pro Bild
Progressive: Ja
WebP: Nein (TVs unterstützen oft kein WebP)

Empfohlen für:
✓ 4K Fernseher (55"+)
✓ NAS-Verbindung (Gigabit LAN)
✓ Beste Bildqualität auf großem Bildschirm
✓ Slideshow/Diashow
```

### **2. Smart TV (Full HD) - `smart_tv_fullhd`**
```yaml
Für: Smart TV mit Full HD
Auflösung: 1920 × 1080 (Full HD)
JPEG Qualität: 90 (hoch)
Thumbnail: 500px, Q85
Dateigröße: ~800 KB - 1.5 MB pro Bild
Progressive: Ja
WebP: Nein

Empfohlen für:
✓ Full HD Fernseher (32"-50")
✓ Langsamere Netzwerke
✓ Ältere Smart TVs
✓ Kleinere Dateien bei guter Qualität
```

### **3. Web Gallery - `web`**
```yaml
Für: Standard Web-Galerien
Auflösung: 1920 × 1280
JPEG Qualität: 85 (gut)
Thumbnail: 400px, Q80
Dateigröße: ~400-800 KB pro Bild
Progressive: Ja
WebP: Optional (--generate-webp flag)

Empfohlen für:
✓ Netlify/Vercel/GitHub Pages
✓ Portfolio-Websites
✓ Kunden-Galerien
✓ Gute Balance: Qualität vs. Dateigröße
```

### **4. Web Optimized - `web_optimized`**
```yaml
Für: Hochoptimierte Web-Galerien
Auflösung: 1600 × 1200
JPEG Qualität: 80
WebP Qualität: 85 (automatisch generiert!)
Thumbnail: 400px, Q75
Dateigröße JPEG: ~300-500 KB
Dateigröße WebP: ~150-300 KB (50% kleiner!)
Progressive: Ja

Empfohlen für:
✓ Schnelles Web-Laden
✓ Mobile Nutzer
✓ SEO-Optimierung (PageSpeed)
✓ Moderne Browser (WebP + JPEG Fallback)
```

### **5. Archive Quality - `archive`**
```yaml
Für: Archivierung/Backup
Auflösung: 4000 × 4000 (maximale Größe)
JPEG Qualität: 95 (sehr hoch)
Thumbnail: 600px, Q90
Dateigröße: ~5-15 MB pro Bild
Progressive: Nein
WebP: Nein

Empfohlen für:
✓ Langzeitarchivierung
✓ Druck-Vorbereitung
✓ Backup-Kopien
✓ Maximale Qualität
```

---

## 🚀 Verwendung

### **CLI (Kommandozeile)**

```powershell
# Export für Smart TV (4K)
python -m photo_tool.cli.main export gallery \
    --photos *.jpg \
    --output D:\Exports\SmartTV \
    --profile smart_tv \
    --title "Urlaub 2026"

# Export für Web (optimiert mit WebP)
python -m photo_tool.cli.main export gallery \
    --photos *.jpg \
    --output D:\Exports\Web \
    --profile web_optimized \
    --generate-webp \
    --title "Portfolio"

# Export für NAS (Full HD, schneller)
python -m photo_tool.cli.main export gallery \
    --photos *.jpg \
    --output D:\Exports\NAS \
    --profile smart_tv_fullhd \
    --title "Familie 2026"
```

### **Web-GUI**

```javascript
// Export-Dialog im Browser
{
    "photo_ids": ["photo1.jpg", "photo2.jpg"],
    "title": "Meine Galerie",
    "output_name": "urlaub-2026",
    "template": "photoswipe",
    "profile": "web_optimized",      // ← NEU!
    "generate_webp": true             // ← NEU!
}
```

**Im GUI:**
1. Fotos filtern (z.B. 5★ + Green)
2. **"Export"** klicken
3. **Profil auswählen:**
   - 📺 Smart TV (4K)
   - 🖥️ Smart TV (Full HD)
   - 🌐 Web Gallery
   - ⚡ Web Optimized
   - 📦 Archive
4. WebP aktivieren (für Web)
5. Export!

---

## 📊 Vergleich: Dateigrößen

**Beispiel:** 24 Megapixel Foto (6000×4000, Original 8 MB)

| Profile | Auflösung | JPEG | WebP | Einsparung |
|---------|-----------|------|------|------------|
| **smart_tv** | 3840×2160 | 3.2 MB | - | 60% |
| **smart_tv_fullhd** | 1920×1080 | 1.1 MB | - | 86% |
| **web** | 1920×1280 | 650 KB | - | 92% |
| **web_optimized** | 1600×1200 | 450 KB | 280 KB | 94% (JPEG), 96% (WebP) |
| **archive** | 4000×4000 | 6.5 MB | - | 19% |

**100 Fotos:**
- Original: **800 MB**
- Smart TV 4K: **320 MB** ← Für NAS perfekt!
- Web Optimized (WebP): **28 MB** ← Schnelles Web-Loading!

---

## 🖥️ Smart TV Setup

### **Samsung Smart TV + NAS**

1. **Export mit `smart_tv` Profil:**
   ```powershell
   python -m photo_tool.cli.main export gallery \
       --photos "F:\Urlaub\*.jpg" \
       --output "D:\NAS_Share\Fotos\Urlaub2026" \
       --profile smart_tv \
       --title "Urlaub Italien 2026"
   ```

2. **Ordnerstruktur:**
   ```
   NAS_Share/Fotos/Urlaub2026/
   ├── gallery/
   │   ├── index.html       ← Im TV Browser öffnen
   │   ├── images/          ← 4K Bilder (3840×2160)
   │   └── thumbnails/      ← Vorschau (600px)
   ```

3. **Samsung TV:**
   - **Web Browser** öffnen
   - URL: `\\NAS\Fotos\Urlaub2026\gallery\index.html`
   - Oder: HTTP Server auf NAS einrichten (empfohlen!)

4. **Mit HTTP Server (empfohlen):**
   ```powershell
   # Python HTTP Server auf NAS
   cd D:\NAS_Share\Fotos\Urlaub2026\gallery
   python -m http.server 8080
   
   # Im Samsung TV Browser:
   # http://NAS-IP:8080
   ```

5. **Vollbild-Slideshow:**
   - Galerie öffnen
   - **F11** drücken (Vollbild)
   - Automatische Slideshow startet

---

## 🌐 Web-Deployment

### **Netlify (kostenlos, 1 Minute)**

```powershell
# 1. Export mit web_optimized Profil
python -m photo_tool.cli.main export gallery \
    --photos "F:\Portfolio\*.jpg" \
    --output "D:\Exports\Portfolio" \
    --profile web_optimized \
    --generate-webp \
    --title "My Portfolio 2026"

# 2. Upload zu Netlify
# Gehe zu: https://app.netlify.com/drop
# Ziehe "gallery" Ordner ins Fenster
# Fertig! → https://your-gallery-abc123.netlify.app
```

### **GitHub Pages**

```powershell
# 1. Export
python -m photo_tool.cli.main export gallery \
    --photos "*.jpg" \
    --output "D:\github\my-gallery" \
    --profile web_optimized \
    --generate-webp

# 2. Push zu GitHub
cd D:\github\my-gallery\gallery
git init
git add .
git commit -m "Add photo gallery"
git remote add origin https://github.com/username/gallery
git push -u origin main

# 3. GitHub Pages aktivieren
# Settings → Pages → Source: main branch
# URL: https://username.github.io/gallery/
```

### **Eigener Server (Apache/Nginx)**

```bash
# Export
python -m photo_tool.cli.main export gallery \
    --photos "*.jpg" \
    --output "/var/www/html/galleries/2026" \
    --profile web_optimized \
    --generate-webp

# URL: https://yoursite.com/galleries/2026/
```

---

## ⚡ WebP-Support

### **Was ist WebP?**
- Modernes Bildformat von Google
- **50% kleinere Dateien** bei gleicher Qualität
- Unterstützt von allen modernen Browsern (Chrome, Firefox, Edge, Safari 14+)

### **Automatic Fallback:**
```html
<!-- Photo Tool generiert automatisch: -->
<picture>
    <source srcset="images/0001.webp" type="image/webp">
    <img src="images/0001.jpg" alt="Photo">
</picture>

<!-- Browser lädt WebP wenn unterstützt, sonst JPEG -->
```

### **Wann WebP verwenden?**
✅ **Ja:**
- Web-Galerien
- Portfolio-Websites
- Mobile-optimierte Seiten
- SEO/PageSpeed wichtig

❌ **Nein:**
- Smart TVs (meist kein Support)
- Ältere Browser (IE11, Safari <14)
- Email-Anhänge
- Print/Archiv

---

## 🎨 Beispiele

### **Beispiel 1: Hochzeit für Kunden (Web)**
```powershell
python -m photo_tool.cli.main export gallery \
    --photos "F:\Hochzeit_Mueller\selected\*.jpg" \
    --output "D:\Exports\Hochzeit_Mueller" \
    --profile web_optimized \
    --generate-webp \
    --title "Hochzeit Anna & Tom - 15.06.2026"

# → Upload zu Netlify
# → Link an Kunden: https://hochzeit-mueller.netlify.app
```

### **Beispiel 2: Familienfotos für Smart TV**
```powershell
python -m photo_tool.cli.main export gallery \
    --photos "F:\Familie\2026\*.jpg" \
    --output "\\NAS\Fotos\Familie_2026" \
    --profile smart_tv_fullhd \
    --title "Familie 2026"

# → Samsung TV: Web Browser → http://NAS-IP/Fotos/Familie_2026/
```

### **Beispiel 3: Portfolio (Web + Archive)**
```powershell
# Web-Version (optimiert)
python -m photo_tool.cli.main export gallery \
    --photos best_shots/*.jpg \
    --output web_portfolio \
    --profile web_optimized \
    --generate-webp \
    --title "Portfolio 2026"

# Archiv-Version (volle Qualität)
python -m photo_tool.cli.main export gallery \
    --photos best_shots/*.jpg \
    --output archive_portfolio \
    --profile archive \
    --title "Portfolio 2026 - Archive"
```

---

## 🛠️ Technische Details

### **JPEG Progressive Loading**
```
Progressive JPEG:
├── 1. Laden: Grobes Vorschaubild (10% der Daten)
├── 2. Laden: Mittlere Qualität (50%)
└── 3. Laden: Volle Qualität (100%)

→ Besseres UX (User sieht sofort etwas)
→ Empfohlen für Web & TV
```

### **Optimierung-Techniken**
```python
1. LANCZOS Resampling (beste Qualität)
2. EXIF Orientation berücksichtigt
3. Progressive JPEG Encoding
4. Optimized Huffman Tables
5. WebP mit Method=4 (beste Kompression)
6. Lazy Loading (HTML)
```

### **File Size Targets**
```
Smart TV 4K:     2-5 MB     (LAN-Speed ok)
Smart TV FHD:    800KB-1.5MB (schneller)
Web Standard:    400-800 KB  (gute Balance)
Web Optimized:   200-500 KB  (schnell)
WebP:            150-300 KB  (sehr schnell!)
```

---

## 📋 Cheat Sheet

```powershell
# Smart TV 4K (NAS)
--profile smart_tv

# Smart TV Full HD (schneller)
--profile smart_tv_fullhd

# Web Standard
--profile web

# Web Optimiert (mit WebP)
--profile web_optimized --generate-webp

# Archiv/Backup
--profile archive

# Alle Profile anzeigen
python -m photo_tool.cli.main export profiles
```

---

## 🎯 Empfehlungen

| Verwendung | Profil | WebP | Beschreibung |
|------------|--------|------|--------------|
| **Samsung TV (4K)** | `smart_tv` | ❌ | Beste Qualität für großen Bildschirm |
| **Samsung TV (FHD)** | `smart_tv_fullhd` | ❌ | Schneller, kleinere Dateien |
| **Web (Kunde)** | `web_optimized` | ✅ | Schnellstes Laden |
| **Portfolio** | `web` | ⚠️ | Gute Balance |
| **Archiv/Backup** | `archive` | ❌ | Maximale Qualität |

---

## 🚀 Quick Start

```powershell
# 1. Profile anzeigen
python -m photo_tool.cli.main export profiles

# 2. Export für Smart TV
python -m photo_tool.cli.main export gallery \
    --photos *.jpg \
    --profile smart_tv \
    --output \\NAS\Fotos\Urlaub2026

# 3. Export für Web (optimiert)
python -m photo_tool.cli.main export gallery \
    --photos *.jpg \
    --profile web_optimized \
    --generate-webp \
    --output web_gallery

# 4. Upload zu Netlify
# → https://app.netlify.com/drop
# → Drag & Drop "gallery" folder
```

---

**Perfekt für:**
- ✅ Samsung/LG Smart TVs via NAS
- ✅ Web-Galerien (Netlify/Vercel)
- ✅ Portfolio-Websites
- ✅ Kunden-Präsentationen
- ✅ Schnelles Laden auf Mobil

**Viel Erfolg! 🎉**
