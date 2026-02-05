# 📁 Projects - Quick Start Guide

## ✅ Phase 1 - Fertig!

**Neue Features:**
- ✅ Projects Tab in der GUI
- ✅ Projekt-Erstellung mit verschiedenen Modi
- ✅ Projekt-Verwaltung (Load, Export, Delete)
- ✅ Persistente Export-Settings
- ✅ Touch-optimiert (große Buttons)

---

## 🚀 Erste Schritte

### **1. Server starten**

```powershell
cd C:\_Git\Python-tools\gui_poc
python server.py
```

Browser: `http://localhost:8000`

---

### **2. Neues Projekt erstellen**

**Methode A: Über Export-Dialog**
```
1. [Photos] Tab öffnen
2. Photos filtern:
   - Rating: 5★ ✅
   - Keywords: "vacation" ✅
   - Ergebnis: 87 photos

3. Export-Button (oben rechts)
4. Export-Settings anpassen:
   - Duration: 7s
   - Smart TV Mode: ✅
   - Music: C:/Music/summer-vibes.mp3

5. Button: [💾 Save as Project]
6. Name: "Vacation 2026 - Highlights"
7. Mode: Filter (Dynamic)
8. [Save Project]

✓ Project gespeichert!
```

**Methode B: Direkt im Projects Tab**
```
1. [Projects] Tab öffnen
2. [✨ New Project]
3. Name eingeben
4. Mode wählen
5. [Save Project]
```

---

### **3. Project laden**

```
1. [Projects] Tab öffnen
2. Project-Card finden
3. [📂 Load] Button

→ Filter werden wiederhergestellt
→ Export-Settings werden geladen
→ Switch zu [Photos] Tab
→ Gefilterte Photos werden angezeigt
```

---

### **4. Project exportieren**

```
1. [Projects] Tab
2. Project-Card finden
3. [📤 Export] Button

→ Project wird geladen
→ Export-Dialog öffnet sich
→ Settings sind vorausgefüllt
→ [Export Gallery] klicken
```

---

## 🎮 Selection Modes

### **Filter Mode (Dynamic)** ⭐ Empfohlen für die meisten Fälle

**Was:**
- Speichert Filter-Kriterien
- Photos werden bei jedem Laden neu gefiltert
- Neue Photos mit passenden Kriterien werden automatisch eingeschlossen

**Beispiel:**
```yaml
filters:
  ratings: [5]
  keywords: ["vacation", "beach"]
  colors: ["green"]
```

**Wann nutzen:**
- "Alle 5-Sterne Urlaubsfotos"
- "Beste Familienfotos"
- "Landschaftsaufnahmen mit 4-5 Sternen"

**Vorteil:** Automatische Updates wenn du neue Photos bewertest!

---

### **Explicit Mode (Static)**

**Was:**
- Speichert exakte Photo-Liste
- Genau diese Photos, nicht mehr, nicht weniger
- Ändert sich nie automatisch

**Beispiel:**
```yaml
photo_ids:
  - "C:/Photos/IMG_1234.JPG"
  - "C:/Photos/IMG_5678.JPG"
  # Genau 42 Photos
```

**Wann nutzen:**
- Handverlesene Auswahl für Kunde
- Perfekt kuratierte Slideshow
- "Diese genau 50 besten Photos"

**Vorteil:** Vollständige Kontrolle, keine Überraschungen!

---

### **Hybrid Mode (Filter + Manual)**

**Was:**
- Filter als Basis
- Plus manuelle Hinzufügungen
- Plus manuelle Ausschlüsse

**Beispiel:**
```yaml
filters:
  ratings: [4, 5]
  keywords: ["greece"]
manual_additions:
  - "IMG_1111.JPG"  # Auch 3★ aber schön
manual_exclusions:
  - "IMG_9999.JPG"  # Trotz 5★ ausschließen
```

**Wann nutzen:**
- Filter als Startpunkt
- Mit manueller Feinabstimmung
- "Fast alle 5-Sterne, aber diese 3 Photos extra dazu"

**Vorteil:** Beste von beiden Welten!

---

## 💡 Workflow-Beispiele

### **Use Case 1: Urlaubsfotos organisieren**

```
Workspace: "Urlaub_2018-2022"
Photos: 5000+

Projects erstellen:

1. "Griechenland 2018 - Best"
   Mode: Filter
   Filters: Rating 5★, Keywords "greece, santorini"
   Settings: Duration 7s, TV Mode
   Music: Greek-Summer.mp3
   
2. "Italien 2019 - Familie"
   Mode: Filter
   Filters: Rating 4-5★, Keywords "italy, family"
   Settings: Duration 8s
   Music: Italian-Theme.mp3

3. "Spanien 2020 - Handpicked"
   Mode: Explicit
   Photos: Genau 50 handverlesene Photos
   Settings: Duration 6s
   
✓ Übersichtlich organisiert!
✓ Schneller Export
✓ Settings werden wiederverwendet
```

---

### **Use Case 2: Verschiedene Präsentationen**

```
Workspace: "Professionell"
Photos: 3000+

Projects:

1. "Portfolio - Landschaften"
   Mode: Filter
   Filters: Rating 5★, Keywords "landscape, nature"
   Settings: No Music, Duration 5s
   
2. "Client Presentation - Summer"
   Mode: Explicit
   Photos: Handverlesene 30 Photos
   Settings: No Music, Duration 6s, Professional
   
3. "Instagram Best - Grid"
   Mode: Filter
   Filters: Rating 5★, Colors Green/Blue
   Settings: Fast Duration 3s

✓ Pro Zweck ein Project!
✓ Wiederverwendbar
✓ Schnell exportierbar
```

---

### **Use Case 3: Dynamische Collections**

```
Workspace: "Aktuelle_Photos_2026"
Photos: Wachsend (neue Photos jede Woche)

Project:

"Aktuelle Highlights"
Mode: Filter (Dynamic!)
Filters: Rating 5★
Settings: Duration 7s, Loop

Workflow:
- Jede Woche neue Photos bewerten
- Project laden → Automatisch neue 5★ Photos drin!
- Export → Immer aktuelle Slideshow
- Für TV im Hintergrund

✓ Keine manuelle Aktualisierung nötig!
✓ Immer up-to-date
```

---

## 📊 Project Card Info

```
┌─────────────────────────────────────┐
│ 🌴 Griechenland 2018 Highlights    │ ← Name
│                                     │
│ 📊 87 photos | 🎵                  │ ← Stats
│                                     │
│ Created: 05.02.2026 16:00          │ ← Timestamps
│ Updated: 05.02.2026 18:30          │
│ Exports: 3                          │ ← Export Count
│                                     │
│ [📂 Load] [📤 Export]              │ ← Actions
│ [✏️ Edit] [🗑️ Delete]             │
└─────────────────────────────────────┘
```

---

## 🎯 Best Practices

### **1. Naming Convention**

**Gut:**
- "Griechenland 2018 - Highlights"
- "Familie - Beste Momente"
- "Landschaft 5-Sterne"

**Nicht so gut:**
- "asdf"
- "test123"
- "Gallery 1"

### **2. Mode Selection**

**Filter Mode:**
- Default für die meisten Fälle
- Automatische Updates
- Weniger Wartung

**Explicit Mode:**
- Für finale, perfekte Auswahlen
- Kunden-Präsentationen
- Wenn Stabilität wichtig ist

**Hybrid Mode:**
- Wenn Filter fast passt
- Wenige manuelle Anpassungen nötig

### **3. Export Settings**

**Speichern lohnt sich:**
- Music-Pfade (nervig jedes Mal neu eingeben)
- TV Mode Einstellung
- Duration-Präferenz
- Template-Wahl

### **4. Workspace Organization**

**Pro Workspace:**
- Zeitraum (2018-2020)
- Thema (Urlaub, Familie, Arbeit)
- Projekt (Kunde A, Kunde B)

**Nicht:**
- Alle tausende Photos in einen Workspace
- Zu viele Projects pro Workspace (>20)

---

## 🐛 Troubleshooting

### **Project lädt nicht alle Photos**

**Check:**
- Filter-Kriterien prüfen
- Sind Photos wirklich im Workspace?
- Keywords korrekt geschrieben?

### **Export-Settings nicht gespeichert**

**Lösung:**
- Project neu speichern
- Settings im Export-Dialog prüfen
- Nach Speichern: Project neu laden testen

### **Project verschwindet**

**Ursache:**
- Workspace gewechselt?
- Projects sind pro Workspace!

**Lösung:**
- Richtigen Workspace öffnen
- Check: `C:/PhotoTool_Test/projects/`

---

## 📁 File Structure

```
C:/PhotoTool_Test/              # Dein Workspace
├── config.yaml
├── db.sqlite
├── cache/
├── exports/
└── projects/                   # 🆕 NEU
    ├── projects.yaml           # Project Index
    └── griechenland-2018-highlights.yaml
    └── italien-2019-familie.yaml
    └── spanien-2020-handpicked.yaml
```

---

## 🎉 Zusammenfassung

**Was du jetzt hast:**
- ✅ Project-Verwaltung in GUI
- ✅ 3 Selection Modes (Filter/Explicit/Hybrid)
- ✅ Persistente Export-Settings
- ✅ Touch-optimierte UI
- ✅ Load/Export/Delete Functions
- ✅ Pro Workspace organisiert

**Was du machen kannst:**
1. Photos filtern
2. Als Project speichern (mit Settings!)
3. Später: Project laden
4. Ein-Klick Export
5. Settings bleiben erhalten!

**Nächste Phase (später):**
- Edit Project Function
- Export History anzeigen
- Project-Suche
- Mehr Stats

---

**Viel Spaß mit Projects! 📁✨**
