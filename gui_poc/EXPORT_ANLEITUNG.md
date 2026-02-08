# 📦🎬🎵 Gallery Export Anleitung  

**Alles zentral in der Photo Tool Web GUI!**

---

## ✅ Wichtig zu wissen

**Keine separaten Scripts nötig!** Alles ist direkt in deiner Web GUI integriert.

Die Beispiel-Scripts (`examples/`) sind nur **Demos** für Entwickler. Du kannst alles über die GUI machen!

---

## 🚀 So verwendest du es

### **1. GUI starten**

```powershell
cd C:\_Git\Python-tools\gui_poc
python server.py
```

Browser öffnet sich automatisch: `http://localhost:8000`

### **2. Photos filtern (optional)**

Filtere die Photos die du exportieren willst:
- ⭐ Rating (1-5 Sterne)
- 🎨 Color Labels (Rot, Gelb, Grün, etc.)
- 🏷️ Keywords/Tags
- 📸 Bursts

**Beispiel:**
- Nur 5-Sterne Photos
- Nur mit Keyword "vacation"
- Nur grüne Label

### **3. Export öffnen**

Klicke oben rechts auf: **"📦 Export Gallery"**

### **4. Einstellungen anpassen**

**Im Export-Dialog siehst du jetzt:**

#### **Basis-Einstellungen:**
- 📝 **Gallery Title** - Name deiner Gallery
- 🎨 **Template** - PhotoSwipe (empfohlen) oder Simple

#### **🎬 Slideshow Einstellungen:**
- ✅ **Enable Slideshow Mode** - Slideshow aktivieren
- ⏱️ **Duration per Photo** - 2-15 Sekunden (Slider)
- 📺 **Smart TV Mode** - Größere Buttons für TV-Fernbedienung

#### **🎵 Background Music (Optional):**
- Pfade zu deinen Musik-Dateien (eine pro Zeile)
- Format: `C:/Music/track1.mp3`
- Mehrere Tracks möglich (Playlist)

**Beispiel Music-Eingabe:**
```
C:/Music/summer-vibes.mp3
C:/Music/chill-beats.mp3
C:/Music/vacation-theme.mp3
```

### **5. Export starten**

Klicke: **"📦 Export Gallery"**

**Progress Bar** zeigt Fortschritt:
- Photos werden optimiert
- Thumbnails generiert
- Music-Dateien kopiert
- HTML generiert

### **6. Gallery öffnen**

Nach dem Export siehst du:
```
✓ Gallery exported successfully!

Photos: 42
🎵 Music tracks: 2
🎬 Slideshow: 5s per photo

Location: C:/PhotoTool_Test/exports/vacation-2026/gallery
Open: C:/PhotoTool_Test/exports/vacation-2026/gallery/index.html
```

**Einfach die `index.html` im Browser öffnen!**

---

## 🎮 Gallery benutzen

### **Im Browser:**

1. Gallery-Grid mit allen Photos
2. Klick auf **"🎬 Start Slideshow"** Button
3. Fullscreen öffnet sich
4. Music startet automatisch (wenn vorhanden)
5. Photos wechseln automatisch

### **Keyboard Controls:**

| Taste | Aktion |
|-------|--------|
| `Space` | Pause/Resume |
| `F` | Fullscreen ein/aus |
| `←` `→` | Nächstes/Vorheriges Photo |
| `Escape` | Slideshow beenden |

### **Music Controls:**

- **▶️ / ⏸️** - Play/Pause Music
- **Volume Slider** - Lautstärke anpassen
- **Now Playing** - Aktueller Track

---

## 📺 Auf Smart TV nutzen

### **Methode 1: USB-Stick**

```powershell
# Gallery-Ordner auf USB kopieren
xcopy /E /I "C:\PhotoTool_Test\exports\vacation-2026\gallery" "E:\tv-gallery\"
```

**Auf dem TV:**
1. USB-Stick einstecken
2. TV Browser öffnen (Samsung Internet, WebOS, etc.)
3. Zu USB navigieren
4. `tv-gallery/index.html` öffnen
5. **"🎬 Start Slideshow"** klicken
6. Genießen! 🎉

### **Methode 2: Netzwerk**

**Flask Server läuft bereits:**
```
http://DEINE-PC-IP:8000/exports/vacation-2026/gallery/
```

**Auf dem TV:**
1. TV Browser öffnen
2. URL eingeben: `http://192.168.1.XXX:8000/exports/vacation-2026/gallery/`
3. Slideshow starten!

**PC-IP finden:**
```powershell
ipconfig
# Suche nach "IPv4-Adresse"
```

---

## 💡 Workflow-Beispiele

### **Beispiel 1: Party heute Abend**

1. GUI starten
2. Filter: 5-Sterne + "party"
3. Export öffnen:
   - Title: "Party Tonight"
   - Slideshow: ✅ (8 Sekunden)
   - Smart TV: ✅
   - Music: `C:/Music/party-mix.mp3`
4. Export → USB → TV
5. Party! 🎉

### **Beispiel 2: Kunden-Präsentation**

1. GUI starten
2. Filter: 5-Sterne + "projekt-name"
3. Export öffnen:
   - Title: "Client Project 2026"
   - Slideshow: ✅ (6 Sekunden)
   - Smart TV: ❌ (für Laptop)
   - Music: ❌ (professionell ohne Music)
4. Export → Email an Kunde

### **Beispiel 3: Hochzeitsfeier**

1. GUI starten
2. Filter: "wedding" + 4-5 Sterne
3. Export öffnen:
   - Title: "Our Wedding Day"
   - Slideshow: ✅ (10 Sekunden, langsam)
   - Smart TV: ✅
   - Music: `C:/Music/wedding-theme.mp3`
4. Export → USB → TV am Festsaal

### **Beispiel 4: Digitaler Bilderrahmen**

1. GUI starten
2. Filter: "family" + 5-Sterne
3. Export öffnen:
   - Title: "Family Memories"
   - Slideshow: ✅ (12 Sekunden, sehr langsam)
   - Smart TV: ✅
   - Music: `C:/Music/nostalgia.mp3`
4. Export → Tablet → Endlos-Loop

---

## 🎵 Music-Dateien vorbereiten

### **Empfohlenes Format:**
- ✅ **MP3** (192-320 kbps) - beste Kompatibilität
- ✅ **OGG** - gut, kleinere Dateien
- ✅ **WAV** - verlustfrei, aber groß
- ⚠️ **AAC/M4A** - eingeschränkte Browser-Unterstützung

### **Wo ablegen?**
Irgendwo auf deinem PC, z.B.:
```
C:\Music\
├── vacation-2026\
│   ├── summer-vibes.mp3
│   └── beach-party.mp3
├── wedding-2025\
│   └── wedding-theme.mp3
└── family\
    └── nostalgia.mp3
```

### **Wie viele Tracks?**
- **Kurze Gallery** (<50 Photos): 1-2 Tracks (3-5 Min)
- **Mittlere Gallery** (50-200): 3-5 Tracks
- **Lange Gallery** (>200): 5+ Tracks oder 1x langer Loop

---

## 📊 Empfehlungen

### **Slideshow Duration:**

| Szenario | Empfohlung |
|----------|------------|
| Schnelle Präsentation | 3-4 Sekunden |
| Normal | 5-6 Sekunden |
| TV im Hintergrund | 8-10 Sekunden |
| Digitaler Bilderrahmen | 12-15 Sekunden |

### **Photo-Anzahl:**

| Gerät | Max Photos | Performance |
|-------|-----------|-------------|
| Desktop | 500+ | ⭐⭐⭐⭐⭐ |
| Tablet | 200 | ⭐⭐⭐⭐ |
| Smart TV | 300 | ⭐⭐⭐⭐ |

### **Smart TV Mode:**

Immer aktivieren wenn:
- ✅ Auf TV anschauen
- ✅ Mit Fernbedienung steuern
- ✅ Aus der Ferne sichtbar sein muss

---

## 🐛 Häufige Probleme

### **Music spielt nicht**

**Lösung:**
- Prüfe Dateipfade (absolute Pfade: `C:/Music/...`)
- Verwende MP3-Format
- Klicke "Start Slideshow" Button (Autoplay braucht User-Interaktion)

### **Photos werden nicht gewechselt**

**Lösung:**
- Slideshow aktiviert? ✅
- Browser-Console (F12) auf Fehler prüfen
- Space-Taste drücken (evtl. pausiert)

### **TV: Buttons zu klein**

**Lösung:**
- "Smart TV Mode" aktivieren ✅
- Neu exportieren
- Gallery neu öffnen

### **Dateien nicht gefunden**

**Lösung:**
- Workspace vorhanden? `C:/PhotoTool_Test`
- Scan durchgeführt? `photo-tool scan`
- Music-Pfade korrekt?

---

## 🎯 Checkliste

**Vor dem Export:**
- [ ] GUI läuft (`python server.py`)
- [ ] Photos gescannt
- [ ] Filter gesetzt (optional)
- [ ] Music-Dateien bereit (optional)

**Export-Einstellungen:**
- [ ] Title eingegeben
- [ ] Slideshow aktiviert (wenn gewünscht)
- [ ] Duration eingestellt
- [ ] Smart TV Mode (für TV)
- [ ] Music-Pfade eingegeben (optional)

**Nach dem Export:**
- [ ] Gallery im Browser getestet
- [ ] Slideshow funktioniert
- [ ] Music abspielbar (wenn vorhanden)
- [ ] Für Zielgerät bereitgestellt (USB/Netzwerk)

---

## 📚 Weitere Dokumentation

- **Quick Start:** `../SLIDESHOW_QUICKSTART.md`
- **Vollständige Anleitung:** `SLIDESHOW_MUSIC_GUIDE.md`
- **Smart TV Setup:** `SMART_TV_GUIDE.md`
- **Technische Details:** `../SLIDESHOW_MUSIC_IMPLEMENTATION.md`

---

## 🎉 Zusammenfassung

**Du brauchst:**
1. ✅ Deine normale Photo Tool Web GUI
2. ✅ Export Button (oben rechts)
3. ✅ Settings im Dialog anpassen
4. ✅ Fertig!

**Keine separaten Scripts! Alles zentral in der GUI!** 🚀

---

**Viel Spaß mit deinen Slideshows! 🎬🎵✨**
