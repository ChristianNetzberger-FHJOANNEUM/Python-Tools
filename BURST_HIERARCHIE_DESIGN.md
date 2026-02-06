# Burst-Hierarchie im Media Tab - Design & Implementierung

## 1. Burst-Metadaten in Sidecar JSON Files

### Aktuelle Struktur (`.phototool.json`)

```json
{
  "analyses": {
    "burst": {
      "burst_neighbors": [
        {
          "path": "C:/Photos/IMG_0002.jpg",
          "time_diff": 0.5,
          "similarity": 0.92,
          "direction": "next"
        },
        {
          "path": "C:/Photos/IMG_0003.jpg",
          "time_diff": 1.2,
          "similarity": 0.89,
          "direction": "next"
        }
      ],
      "is_burst_candidate": true,
      "burst_group_size": 3,
      "computed_at": "2026-02-06T10:30:00"
    }
  }
}
```

### Verfügbare Daten
- **`burst_neighbors`**: Array mit benachbarten Burst-Fotos
  - `path`: Vollständiger Pfad zum Nachbar-Foto
  - `time_diff`: Zeitdifferenz in Sekunden
  - `similarity`: Ähnlichkeitsscore (0-1)
  - `direction`: "previous" oder "next"
- **`is_burst_candidate`**: Boolean - ist Teil eines Bursts
- **`burst_group_size`**: Anzahl Fotos im Burst
- **`computed_at`**: Zeitstempel der Analyse

## 2. Implementierungsvorschlag: Burst-Container im Media Tab

### Design-Konzept (Apple Photos Style)

```
┌─────────────────────────────────────────────────────┐
│  Media Tab - Thumbnail Grid                         │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [📸] [📸] [📦 Burst (5)] [📸] [📸]                 │
│                  ↓                                   │
│         ┌────────────────┐                          │
│         │  IMG_0001.jpg  │                          │
│         │  ⭐⭐⭐         │                          │
│         │  📊 125        │  ← Blur Score            │
│         │  🔢 5 photos   │  ← Burst Count           │
│         └────────────────┘                          │
│                                                      │
│  Bei Click: Filter auf nur Burst-Fotos              │
└─────────────────────────────────────────────────────┘
```

### Visual Design Details

**Burst-Container Thumbnail:**
- **Border**: Gestrichelte oder doppelte Border (`border: 3px dashed #8b5cf6`)
- **Hintergrund**: Leicht violett/magenta für Unterscheidung (`background: rgba(139, 92, 246, 0.15)`)
- **Badge**: Burst-Icon 📦 + Anzahl Fotos in der oberen rechten Ecke
- **Thumbnail**: Zeigt das ERSTE Foto des Bursts (oder das mit höchstem Rating)
- **Indicator**: Stack-Effekt (3 leicht versetzte Schatten) um Stapel zu simulieren

**Burst-Container beim Hover:**
- Animation: Leichtes "pulsieren" der Border
- Tooltip: "Burst: 5 photos (0.5-2.3s apart) - Click to view all"

## 3. Funktionalität

### Phase 1: Burst-Container im Grid (EINFACH)

1. **Burst-Gruppierung berechnen**
   - Beim Laden der Fotos: Burst-Nachbarn analysieren
   - Jede Burst-Gruppe bekommt eine `burst_id` (z.B. Hash des ersten Fotos)
   - Nur das "Lead"-Foto (erstes oder best-rated) wird im Grid angezeigt

2. **Visuelles Styling**
   - CSS-Klasse `.burst-container` für spezielle Border/Background
   - Badge mit Anzahl Fotos
   - Stack-Shadow-Effekt für 3D-Look

3. **Click-Handler**
   - Click auf Burst-Container → Aktiviert Burst-Filter
   - Zeigt nur Fotos aus diesem Burst
   - "Back to all photos" Button erscheint

### Phase 2: Erweiterter Burst-Viewer (MITTEL)

1. **Inline-Expansion**
   - Click auf Burst → Expandiert zu horizontaler Scrollbar
   - Alle Burst-Fotos werden in einer Reihe angezeigt
   - Zweiter Click → Kollabiert wieder

2. **Burst-Bewertung**
   - Innerhalb des Bursts: Rating vergeben
   - "Best Pick" markieren (Stern-Icon)
   - "Keep" / "Reject" Buttons für schnelles Aussortieren

3. **Quick Actions**
   - "⭐ Keep Best" - Behält nur das höchste Rating
   - "🗑️ Delete Rest" - Löscht alle außer markierte
   - "📊 Stack" - Versteckt alle außer Lead-Foto

## 4. Implementierungs-Komplexität

### Gesamtbewertung: **MITTEL** (ca. 4-6 Stunden für Phase 1)

#### Phase 1: Burst-Container (EINFACH - 2-3h)
**Backend (1h):**
- ✅ Burst-Daten sind bereits in Sidecars vorhanden
- ✅ API-Endpoint für Burst-Gruppen existiert bereits (`/api/projects/<id>/bursts`)
- ⚠️ Anpassung: `get_project_media` muss Burst-Gruppierung mitliefern
- Neue Felder in Response: `is_burst_lead`, `burst_id`, `burst_count`

**Frontend (1-2h):**
- CSS für `.burst-container` Styling (30 min)
- Logik zur Burst-Gruppierung in `filteredPhotos()` (30 min)
- Click-Handler für Burst-Filter (30 min)
- UI für "Viewing Burst X" + Back-Button (30 min)

**Vorteile:**
- Nutzt existierende Datenstruktur
- Minimale Backend-Änderungen
- Kein komplexes State-Management

#### Phase 2: Inline-Expansion (MITTEL - 2-3h)
**Frontend (2-3h):**
- Expandable Grid-Layout (komplexer CSS/Vue)
- Animationen für smooth expand/collapse
- State-Management für expandierte Bursts
- Touch/Swipe Support für Tablet-Nutzung

**Herausforderungen:**
- CSS Grid muss dynamisch angepasst werden
- Animationen müssen performant sein
- Mobile-Responsivität beachten

## 5. Technische Details

### Backend-Änderungen (server.py)

```python
@app.get('/api/projects/<project_id>/media')
def get_project_media(project_id):
    # ... existing code ...
    
    # Burst-Gruppierung hinzufügen
    burst_groups = {}  # burst_id -> [photo_paths]
    
    for item in result_page:
        sidecar = SidecarManager(item.path)
        if sidecar.exists:
            sidecar.load()
            burst_data = sidecar.get('analyses.burst')
            
            if burst_data and burst_data.get('is_burst_candidate'):
                # Bestimme Burst-ID (erstes Foto in der Gruppe)
                neighbors = burst_data.get('burst_neighbors', [])
                all_paths = [str(item.path)] + [n['path'] for n in neighbors]
                all_paths.sort()  # Sortiere für konsistente ID
                burst_id = hashlib.md5(all_paths[0].encode()).hexdigest()[:12]
                
                if burst_id not in burst_groups:
                    burst_groups[burst_id] = []
                burst_groups[burst_id].append(str(item.path))
    
    # Markiere Lead-Fotos
    for item_dict in result:
        item_path = item_dict['path']
        for burst_id, photos in burst_groups.items():
            if item_path in photos:
                item_dict['burst_id'] = burst_id
                item_dict['burst_count'] = len(photos)
                item_dict['is_burst_lead'] = (item_path == photos[0])  # Erstes ist Lead
                break
```

### Frontend-Änderungen (index.html)

```javascript
// Vue Data
data() {
    return {
        // ... existing ...
        activeBurstId: null,  // Aktuell gefilterter Burst
        expandedBursts: new Set()  // Expandierte Burst-Container (Phase 2)
    }
},

// Computed
filteredPhotos() {
    let photos = this.photos;
    
    // ... existing filters ...
    
    // Burst-Filter: Wenn activeBurstId gesetzt, nur diese Fotos zeigen
    if (this.activeBurstId) {
        photos = photos.filter(p => p.burst_id === this.activeBurstId);
    } else {
        // Wenn NICHT in Burst-Ansicht, nur Lead-Fotos zeigen
        photos = photos.filter(p => !p.burst_id || p.is_burst_lead);
    }
    
    return photos;
},

// Methods
viewBurst(burstId) {
    this.activeBurstId = burstId;
    window.scrollTo({ top: 0, behavior: 'smooth' });
},

exitBurstView() {
    this.activeBurstId = null;
}
```

### CSS Styling

```css
/* Burst-Container Styling */
.photo-card.burst-container {
    border: 3px dashed #8b5cf6;
    background: rgba(139, 92, 246, 0.1);
    position: relative;
    box-shadow: 
        0 2px 0 rgba(139, 92, 246, 0.3),
        0 4px 0 rgba(139, 92, 246, 0.2),
        0 6px 0 rgba(139, 92, 246, 0.1);  /* Stack-Effekt */
}

.photo-card.burst-container:hover {
    border-color: #a78bfa;
    animation: burst-pulse 1.5s ease-in-out infinite;
}

@keyframes burst-pulse {
    0%, 100% { border-color: #8b5cf6; }
    50% { border-color: #a78bfa; }
}

/* Burst Badge */
.burst-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    background: linear-gradient(135deg, #8b5cf6, #ec4899);
    color: white;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

/* Burst-View Header */
.burst-view-header {
    background: rgba(139, 92, 246, 0.2);
    padding: 15px 20px;
    border-radius: 10px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
```

## 6. UI/UX Flow

### Normale Ansicht
```
User sieht: [📸] [📸] [📦 5] [📸] [📸]
            ↑ normale  ↑ Burst   ↑ normale
            Fotos      Container  Fotos
```

### Nach Click auf Burst-Container
```
┌─────────────────────────────────────────────────┐
│ 📦 Viewing Burst: IMG_0001 (5 photos)   [← Back]│
├─────────────────────────────────────────────────┤
│                                                  │
│  [📸] [📸] [📸] [📸] [📸]                       │
│  0.0s  0.5s  1.2s  1.8s  2.3s  ← Zeitstempel   │
│  ⭐⭐⭐ ⭐⭐   ⭐    -     -                      │
│                                                  │
└─────────────────────────────────────────────────┘
```

## 7. Alternativen & Erweiterungen

### Alternative 1: Burst-Overlay (wie Google Photos)
- Click auf Burst → Fullscreen-Overlay mit Filmstreifen unten
- Komplexität: HOCH (zusätzliche 4-6h)

### Alternative 2: Burst-Spalten-View
- Bursts werden als eigene Spalte im Grid dargestellt
- Pro: Sehr übersichtlich
- Contra: Verschwendet Platz bei vielen Einzelfotos

### Erweiterung: Auto-Stacking
- Option: "Auto-stack bursts" in Settings
- Versteckt Burst-Container standardmäßig
- Zeigt nur das beste Foto + kleinen Badge

## 8. Empfehlung

**START MIT PHASE 1** - Burst-Container im Grid

**Warum:**
- Schnell implementierbar (2-3h)
- Nutzt existierende Infrastruktur
- Sofortiger Mehrwert für User
- Basis für spätere Erweiterungen

**Nächste Schritte:**
1. Backend: `get_project_media` anpassen (Burst-Gruppierung)
2. Frontend: CSS für `.burst-container`
3. Frontend: Burst-Filter Logik
4. Frontend: "View Burst" / "Back" UI

**Nach User-Feedback:**
- Wenn gut angenommen → Phase 2 (Inline-Expansion)
- Wenn zu komplex → Vereinfachen (nur Badge + Link zu Burst-Tab)

## 9. Testing-Checklist

- [ ] Burst-Container wird korrekt erkannt und angezeigt
- [ ] Lead-Foto wird als Thumbnail verwendet
- [ ] Burst-Count Badge zeigt korrekte Anzahl
- [ ] Click auf Container öffnet Burst-View
- [ ] Alle Burst-Fotos werden in Burst-View angezeigt
- [ ] "Back"-Button kehrt zur normalen Ansicht zurück
- [ ] Rating/Color Labels funktionieren in Burst-View
- [ ] Filter (Rating, Color, Blur) funktionieren in Burst-View
- [ ] Performance mit vielen Bursts ist OK (>100 Bursts)
- [ ] Mobile/Touch funktioniert einwandfrei

## 10. Zeitaufwand-Schätzung

| Phase | Backend | Frontend | Testing | Total |
|-------|---------|----------|---------|-------|
| Phase 1 (Container) | 1h | 1.5h | 0.5h | **3h** |
| Phase 2 (Expansion) | 0.5h | 2h | 0.5h | **3h** |
| Polish & UX | - | 1h | 0.5h | **1.5h** |
| **GESAMT** | **1.5h** | **4.5h** | **1.5h** | **7.5h** |

**Realistische Einschätzung mit Debugging/Iteration: 8-10 Stunden**
