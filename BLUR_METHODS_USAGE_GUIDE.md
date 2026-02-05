# Blur Detection Methods - Benutzeranleitung

## 🎯 Übersicht

Sie können jetzt zwischen **drei verschiedenen Blur-Detection-Methoden** wählen und diese direkt in der GUI vergleichen!

### Verfügbare Methoden:

1. **Laplacian Variance** (LAP)
   - Bereich: 0-300
   - Geschwindigkeit: ⚡⚡⚡ Sehr schnell
   - Ideal für: Allgemeine Verwendung, schnelle Bewertung
   - Problem: Niedrige Scores bei Himmel/homogenen Flächen

2. **Tenengrad (Sobel)** (TEN)
   - Bereich: 0-50
   - Geschwindigkeit: ⚡⚡ Schnell
   - Ideal für: **Bilder mit viel Himmel**, Wasser, homogene Flächen
   - Vorteil: Fokussiert auf Kanten, ignoriert homogene Bereiche

3. **ROI-based (Adaptive)** (ROI)
   - Bereich: 0-300
   - Geschwindigkeit: ⚡ Mittel
   - Ideal für: **Gemischte Szenen**, Vordergrund scharf/Hintergrund unscharf
   - Vorteil: Analysiert nur interessante Bereiche, ignoriert Himmel automatisch

## 📋 Verwendung

### 1. Methode auswählen

**In Projects Tab:**
```
Quality Detection Settings
→ Blur Detection
→ Method Dropdown: [Laplacian / Tenengrad / ROI]
→ "Calculate Blur Scores (METHOD)"
```

**In Photos Tab:**
```
Blur Threshold Section
→ Method Dropdown: [Laplacian / Tenengrad / ROI]
→ Wählen und automatisch neu laden
```

### 2. Blur Scores berechnen

1. Wählen Sie eine Methode
2. Klicken Sie "Calculate Blur Scores (METHOD)"
3. Warten Sie auf Abschluss (Progress Bar sichtbar)
4. Scores werden in Thumbnails angezeigt

### 3. Threshold anwenden

**Photos Tab:**
```
🔍 Blur Threshold
Method: [Tenengrad]  ← Aktive Methode
Threshold: 15 (Strict)
───────────────────────
🔍 15 TEN  ← In Thumbnails
```

**Threshold-Bereiche je nach Methode:**

| Methode | Min | Max | Empfohlen für verwackelte Bilder |
|---------|-----|-----|----------------------------------|
| Laplacian | 0 | 300 | 0-20 |
| Tenengrad | 0 | 50 | 5-15 |
| ROI | 0 | 300 | 0-30 |

## 🔬 Methoden im Vergleich

### Beispiel-Szenario: Landschaftsfoto mit Himmel

**Bild:** Berglandschaft mit blauem Himmel (70% Himmel, 30% Berge scharf)

| Methode | Score | Interpretation |
|---------|-------|----------------|
| **Laplacian** | 45 | "Unscharf" (wegen Himmel) ❌ |
| **Tenengrad** | 28 | "Scharf" (Kanten der Berge) ✅ |
| **ROI** | 156 | "Sehr scharf" (nur Berge analysiert) ✅ |

**Empfehlung:** Tenengrad oder ROI für solche Bilder!

### Beispiel-Szenario: Verwackeltes Foto

**Bild:** Motion Blur, keine Details erkennbar

| Methode | Score | Interpretation |
|---------|-------|----------------|
| **Laplacian** | 8 | "Sehr unscharf" ✅ |
| **Tenengrad** | 3 | "Sehr unscharf" ✅ |
| **ROI** | 12 | "Sehr unscharf" ✅ |

**Alle Methoden erkennen es korrekt!**

### Beispiel-Szenario: Portrait mit unscharfem Hintergrund

**Bild:** Person scharf, Hintergrund Bokeh

| Methode | Score | Interpretation |
|---------|-------|----------------|
| **Laplacian** | 85 | "Leicht unscharf" (Hintergrund senkt Score) ⚠️ |
| **Tenengrad** | 32 | "Scharf" (Gesicht hat Kanten) ✅ |
| **ROI** | 187 | "Sehr scharf" (nur Person analysiert) ✅ |

**Empfehlung:** ROI für Portraits mit Bokeh!

## 💡 Workflow-Empfehlungen

### Workflow 1: Schnelle erste Sortierung
```
1. Laplacian verwenden (schnellste Methode)
2. Threshold: 20
3. Extrem verwackelte Bilder werden geflaggt
4. Manuelle Review der geflaggten Fotos
```

### Workflow 2: Landschaftsfotos mit Himmel
```
1. Tenengrad verwenden
2. Threshold: 10-15
3. Verwackelte/unscharfe erkannt, Himmel ignoriert
4. Oder: ROI verwenden für adaptive Erkennung
```

### Workflow 3: Verschiedene Methoden vergleichen
```
1. Laplacian berechnen → Scores ansehen
2. Tenengrad berechnen → Vergleichen
3. ROI berechnen → Beste Methode wählen
4. Threshold mit bester Methode anwenden
```

**Tooltip zeigt alle Scores:**
```
Hover über 🔍 156 LAP:
→ "LAP: 156 - Sharp | TEN: 32 | ROI: 187"
```

## 🎨 Visuelle Hinweise

### Thumbnail-Anzeige
```
photo_IMG_1234.jpg
2024-01-15 14:30
🔍 32 TEN          ← Grün = Scharf
⭐⭐⭐⭐⭐
```

**Farbkodierung (unabhängig von Methode):**
- 🔴 Rot: Sehr unscharf
- 🟠 Orange: Unscharf
- 🟡 Gelb: Akzeptabel
- 🟢 Grün: Scharf
- 💚 Hell-Grün: Sehr scharf

**Methoden-Kürzel:**
- LAP = Laplacian
- TEN = Tenengrad
- ROI = ROI-based

## 📊 Threshold-Empfehlungen

### Laplacian (0-300)
```
0-10:    Extrem verwackelt
10-50:   Sehr unscharf
50-100:  Unscharf
100-150: Akzeptabel
150-200: Scharf
200+:    Sehr scharf
```

**Empfohlene Thresholds:**
- Verwackelte Bilder entfernen: **10-20**
- Unscharfe Bilder entfernen: **50-80**
- Nur perfekte Fotos: **150+**

### Tenengrad (0-50)
```
0-5:   Extrem verwackelt
5-10:  Sehr unscharf
10-20: Unscharf
20-30: Akzeptabel
30-40: Scharf
40+:   Sehr scharf
```

**Empfohlene Thresholds:**
- Verwackelte Bilder entfernen: **5-10**
- Unscharfe Bilder entfernen: **15-20**
- Nur perfekte Fotos: **30+**

### ROI (0-300)
```
Ähnlich wie Laplacian, aber:
- Scores generell höher (Himmel ignoriert)
- Threshold 50-100 für gemischte Szenen
```

## 🔧 Technische Details

### Datenspeicherung
Jede Methode speichert ihre Scores separat:
```json
{
  "blur_score_laplacian": 156.4,
  "blur_score_tenengrad": 32.1,
  "blur_score_roi": 187.3,
  "blur_method": "tenengrad"
}
```

### API-Verwendung
```python
# Berechnen mit spezifischer Methode
POST /api/quality/detect-blur
{
  "method": "tenengrad",
  "force": false
}

# Scores für Methode abrufen
GET /api/quality/blur-scores?method=tenengrad

# Threshold mit Methode anwenden
POST /api/quality/apply-threshold
{
  "method": "tenengrad",
  "threshold": 15,
  "flag_color": "red"
}
```

## 🎯 Schnellreferenz

| Problem | Empfohlene Methode | Threshold |
|---------|-------------------|-----------|
| Verwackelte Bilder | Alle (Laplacian am schnellsten) | LAP: 10-20, TEN: 5-10 |
| Bilder mit Himmel | **Tenengrad** oder **ROI** | TEN: 15-25, ROI: 80-120 |
| Portraits mit Bokeh | **ROI** | 80-150 |
| Gemischte Sammlung | **ROI** (adaptive) | 50-100 |
| Schnelle Sortierung | **Laplacian** | 20-50 |

## 💾 Workflow-Beispiel

```
Schritt 1: Initiale Berechnung
- Methode: Laplacian (schnell)
- Ergebnis: 50 Fotos mit Score < 50
- Problem: Viele Landschaftsfotos dabei (Himmel)

Schritt 2: Tenengrad-Vergleich
- Methode: Tenengrad
- Ergebnis: 15 Fotos mit Score < 15
- Besser! Himmel wird ignoriert

Schritt 3: Feintuning
- Threshold anpassen: 10 → 12
- 8 Fotos geflaggt
- Manuelle Review
- Entscheidung: 6 löschen, 2 behalten

Schritt 4: Export
- Gallery ohne geflaggerte Fotos exportieren
- Nur scharfe Bilder in Slideshow
```

## ⚠️ Bekannte Einschränkungen

### Laplacian
- ❌ Niedrige Scores bei Himmel/Wasser
- ❌ Bewertet gesamtes Bild
- ✅ Sehr schnell

### Tenengrad
- ✅ Besser für Himmel/homogene Bereiche
- ✅ Fokus auf Kanten
- ⚠️ Kleinerer Score-Range (0-50)

### ROI
- ✅ Beste Ergebnisse für gemischte Szenen
- ✅ Ignoriert Himmel automatisch
- ⚠️ Etwas langsamer
- ⚠️ Bei sehr homogenen Bildern Fallback zu Laplacian

## 🚀 Tipps & Tricks

1. **Mehrere Methoden vergleichen:**
   - Alle drei Methoden berechnen
   - Tooltip zeigt alle Scores
   - Beste Methode für Ihr Archiv wählen

2. **Threshold dynamisch anpassen:**
   - Methode wechseln
   - Threshold wird automatisch begrenzt
   - Sofort neue Histogram-Verteilung sehen

3. **Verschiedene Thresholds testen:**
   - Kein Re-run nötig
   - Threshold ändern, Apply klicken
   - Sofort Ergebnis sehen

4. **Kombinierte Strategie:**
   - Laplacian: < 20 → Löschen (verwackelt)
   - Tenengrad: < 15 → Review (potentiell unscharf)
   - ROI: < 100 → Flag für manuelle Prüfung

---

**Status:** ✅ **VOLLSTÄNDIG IMPLEMENTIERT**

Alle drei Methoden sind verfügbar und können in der GUI gewählt werden. Starten Sie den Server neu und experimentieren Sie mit verschiedenen Methoden!
