# 🚀 Export-Profile Quick Reference

## Schnellübersicht

| Profil | Use Case | Auflösung | JPEG | WebP | Dateigröße |
|--------|----------|-----------|------|------|------------|
| **📺 smart_tv** | Samsung TV 4K | 3840×2160 | Q92 | ❌ | ~3 MB |
| **🖥️ smart_tv_fullhd** | Samsung TV FHD | 1920×1080 | Q90 | ❌ | ~1 MB |
| **🌐 web** | Web Standard | 1920×1280 | Q85 | ⚠️ | ~650 KB |
| **⚡ web_optimized** | Web Schnell | 1600×1200 | Q80 | ✅ | ~450 KB (280 KB WebP) |
| **📦 archive** | Archiv/Print | 4000×4000 | Q95 | ❌ | ~6 MB |

---

## 🎯 Empfehlungen

### Smart TV Setup (Samsung/LG + NAS)

**Empfohlen:** `smart_tv` oder `smart_tv_fullhd`

```powershell
# Via GUI:
1. Photos filtern
2. Export klicken
3. Profil: "📺 Smart TV (4K)" wählen
4. Export!

# Ergebnis in: C:\PhotoTool_Test\exports\gallery\
```

**NAS Setup:**
```
1. Export Ordner auf NAS kopieren
2. Samsung TV → Web Browser → http://NAS-IP/gallery/
3. Vollbild (F11) für Slideshow
```

---

### Web Upload (Netlify/Vercel)

**Empfohlen:** `web_optimized` + WebP

```powershell
# Via GUI:
1. Photos filtern (z.B. 5★ + Green)
2. Export klicken
3. Profil: "⚡ Web Optimized"
4. ✅ Generate WebP aktivieren
5. Export!

# Upload:
→ https://app.netlify.com/drop
→ Drag & Drop "gallery" Ordner
→ Fertig!
```

---

## 📊 Dateigrössen-Beispiel

**100 Fotos (je 8 MB Original = 800 MB):**

| Profil | Total JPEG | Total WebP | Upload-Zeit (10 Mbps) |
|--------|-----------|------------|----------------------|
| smart_tv | 320 MB | - | 4:16 min |
| smart_tv_fullhd | 110 MB | - | 1:28 min |
| web | 65 MB | - | 52 sec |
| web_optimized | 45 MB | 28 MB | 36 sec (JPEG), 22 sec (WebP) |
| archive | 650 MB | - | 8:40 min |

---

## 🌐 Browser-Support

### WebP Support:
✅ Chrome, Edge, Firefox, Opera  
✅ Safari 14+  
✅ Mobile (alle modernen)  
❌ IE11, Safari <14  
❌ Smart TVs (meist)

**Photo Tool generiert automatisch JPEG-Fallback!**

---

## ⚡ Best Practices

### Für Smart TV:
```
✓ Verwende smart_tv_fullhd (schneller)
✓ Export auf NAS mit Gigabit LAN
✓ HTTP Server auf NAS (nicht SMB)
✓ F11 im TV Browser für Vollbild
```

### Für Web:
```
✓ Verwende web_optimized + WebP
✓ Lazy Loading (automatisch)
✓ Progressive JPEG (automatisch)
✓ < 100 Fotos pro Galerie (Performance)
```

### Für Archiv:
```
✓ Verwende archive Profil
✓ Externe Festplatte/NAS Backup
✓ Inkl. Ratings & Metadata
✓ Original-EXIF bleibt erhalten
```

---

## 🛠️ Troubleshooting

### **"Export dauert zu lange"**
→ Verwende kleineres Profil (web statt archive)  
→ Weniger Fotos exportieren  
→ WebP deaktivieren (schneller)

### **"Dateien zu groß für Web"**
→ Verwende `web_optimized` statt `web`  
→ WebP aktivieren  
→ Weniger Fotos pro Galerie

### **"Smart TV zeigt Bilder nicht"**
→ Prüfe: HTTP Server läuft?  
→ URL: http://NAS-IP:8080/ (nicht \\NAS\...)  
→ Browser im TV aktualisieren (Strg+F5)

### **"WebP funktioniert nicht"**
→ Browser zu alt? → JPEG Fallback wird verwendet  
→ Smart TV? → WebP nicht unterstützt (normal)

---

## 📝 Zusammenfassung

```
Smart TV (NAS):      smart_tv_fullhd
Web (Portfolio):     web_optimized + WebP
Web (Kunde):         web
Archiv/Backup:       archive
```

**Standard-Empfehlung:** `web_optimized` + WebP ✅
