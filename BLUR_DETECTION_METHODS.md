# Blur Detection Methoden - Vergleich und Empfehlungen

## Problem mit aktueller Methode (Laplacian Variance)

### Aktuelle Methode: **Laplacian Variance**
```python
laplacian = cv2.Laplacian(gray, cv2.CV_64F)
score = laplacian.var()
```

### Vorteile:
- ✅ Schnell und effizient
- ✅ Gut für allgemeine Schärfe-Bewertung
- ✅ Funktioniert gut bei texturierten Bildern

### **Probleme:**
- ❌ **Verwackelte Bilder (< 10):** Motion Blur wird erkannt
- ❌ **Himmel/homogene Bereiche:** Niedriger Score obwohl Vordergrund scharf ist
- ❌ **Globale Bewertung:** Bewertet gesamtes Bild, nicht nur interessante Bereiche
- ❌ **Empfindlich auf Rauschen:** Rauschen kann als "Schärfe" interpretiert werden

## Alternative Methoden

### 1. **Tenengrad (Sobel-basiert)** ⭐ Empfohlen
```python
def detect_blur_tenengrad(image_path: Path) -> float:
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Sobel operators
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    
    # Gradient magnitude
    fm = np.sqrt(gx**2 + gy**2)
    score = fm.mean()
    
    return float(score)
```

**Vorteile:**
- ✅ Fokussiert auf Kanten (ignoriert homogene Bereiche besser)
- ✅ Robuster gegen Rauschen
- ✅ Gut für Bewegungsunschärfe
- ✅ Besser für Bilder mit Himmel/Wasser

**Threshold-Werte:**
- < 5: Sehr unscharf
- 5-15: Unscharf
- 15-30: Akzeptabel
- 30-50: Scharf
- > 50: Sehr scharf

---

### 2. **FFT (Frequenz-Analyse)**
```python
def detect_blur_fft(image_path: Path) -> float:
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    
    # FFT
    fft = np.fft.fft2(img)
    fft_shift = np.fft.fftshift(fft)
    magnitude = np.abs(fft_shift)
    
    # High frequency content
    h, w = magnitude.shape
    cy, cx = h // 2, w // 2
    radius = min(cy, cx) // 3
    
    high_freq = magnitude.copy()
    y, x = np.ogrid[:h, :w]
    mask = ((y - cy)**2 + (x - cx)**2) <= radius**2
    high_freq[mask] = 0
    
    score = np.sum(high_freq) / (h * w)
    return float(score)
```

**Vorteile:**
- ✅ Erkennt Bewegungsunschärfe besonders gut
- ✅ Frequenzbasiert - objektiver
- ✅ Gut für Motion Blur vs. Focus Blur Unterscheidung

**Nachteile:**
- ❌ Langsamer als Laplacian/Tenengrad
- ❌ Komplex zu interpretieren

---

### 3. **ROI (Region of Interest) - Adaptive Methode** ⭐⭐ Beste Lösung
```python
def detect_blur_roi(image_path: Path) -> float:
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Edge detection to find ROI
    edges = cv2.Canny(gray, 50, 150)
    
    # Find regions with edges (interesting areas)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        # Fallback to full image
        return detect_blur_laplacian(image_path)
    
    # Calculate blur only on ROI
    roi_scores = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h > 100:  # Ignore small regions
            roi = gray[y:y+h, x:x+w]
            laplacian = cv2.Laplacian(roi, cv2.CV_64F)
            roi_scores.append(laplacian.var())
    
    if roi_scores:
        # Weighted average (favor higher scores)
        return float(np.mean(sorted(roi_scores, reverse=True)[:len(roi_scores)//2]))
    
    return detect_blur_laplacian(image_path)
```

**Vorteile:**
- ✅ **Löst das Himmel-Problem!** Ignoriert homogene Bereiche
- ✅ Fokussiert auf interessante Bereiche (Vordergrund, Objekte)
- ✅ Adaptive - passt sich an Bildinhalt an
- ✅ Beste Ergebnisse für gemischte Szenen

**Empfohlen für:**
- Landschaftsfotos mit Himmel
- Portraits mit unscharfem Hintergrund
- Architekturfotos mit homogenen Flächen

---

### 4. **Brenner's Focus Measure**
```python
def detect_blur_brenner(image_path: Path) -> float:
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    
    # Squared differences
    dx = np.diff(img, axis=1)
    score = np.sum(dx**2)
    
    return float(score / img.size)
```

**Vorteile:**
- ✅ Sehr schnell
- ✅ Einfach zu implementieren

**Nachteile:**
- ❌ Empfindlich auf Rauschen
- ❌ Nicht so robust wie Laplacian/Tenengrad

---

## Empfohlene Implementierung

### **Hybrid-Ansatz: Kombination mehrerer Methoden**
```python
def detect_blur_hybrid(image_path: Path) -> dict:
    """
    Kombiniert mehrere Methoden für robuste Bewertung
    
    Returns:
        {
            'laplacian': float,
            'tenengrad': float,
            'roi': float,
            'combined': float,  # Weighted average
            'recommendation': str
        }
    """
    scores = {
        'laplacian': detect_blur_laplacian(image_path),
        'tenengrad': detect_blur_tenengrad(image_path),
        'roi': detect_blur_roi(image_path)
    }
    
    # Weighted combination (ROI gets highest weight)
    combined = (
        scores['laplacian'] * 0.2 +
        scores['tenengrad'] * 0.3 +
        scores['roi'] * 0.5
    )
    
    scores['combined'] = combined
    
    # Recommendation based on combined score
    if combined < 20:
        scores['recommendation'] = 'Delete - Very Blurry'
    elif combined < 50:
        scores['recommendation'] = 'Review - Blurry'
    elif combined < 100:
        scores['recommendation'] = 'Acceptable'
    elif combined < 150:
        scores['recommendation'] = 'Good'
    else:
        scores['recommendation'] = 'Excellent'
    
    return scores
```

---

## Praktische Empfehlung für Ihr Projekt

### **Kurzfristig (Schnelle Verbesserung):**
Implementieren Sie **Tenengrad** als Alternative:

```python
# In photo_tool/analysis/similarity/blur.py

class BlurMethod(Enum):
    LAPLACIAN = "laplacian"
    TENENGRAD = "tenengrad"  # NEU
    VARIANCE = "variance"

def detect_blur_tenengrad(image_path: Path) -> float:
    """Tenengrad gradient method - better for images with sky/homogeneous areas"""
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Sobel operators
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Gradient magnitude
        fm = np.sqrt(gx**2 + gy**2)
        score = fm.mean()
        
        return float(score)
    
    except Exception as e:
        logger.error(f"Error detecting blur (Tenengrad) for {image_path}: {e}")
        raise

def detect_blur(image_path: Path, method: BlurMethod = BlurMethod.TENENGRAD):
    # ... rest of code, add Tenengrad case
```

**Threshold-Anpassung:**
- Laplacian: 0-300 (aktuell)
- Tenengrad: 0-50 (neuer Range)

### **Mittelfristig (Beste Lösung):**
Implementieren Sie **ROI-basierte Methode** für Bilder mit Himmel/homogenen Bereichen.

### **Langfristig (Professionell):**
Implementieren Sie **Hybrid-Ansatz** mit mehreren Scores und ML-basierter Bewertung.

---

## Sofortmaßnahmen für aktuelle Probleme

### Problem 1: "Verwackelte Bilder unter 10"
✅ **Gelöst:** Threshold kann jetzt auf 0 gesetzt werden
- Threshold 0-20: Nur extrem verwackelte Bilder

### Problem 2: "Himmel führt zu niedrigem Score"
🔧 **Lösung:** Tenengrad-Methode implementieren
- Fokussiert auf Kanten, ignoriert homogene Bereiche besser
- Threshold: 5-10 für verwackelte Bilder

### Problem 3: "Falsche Farb-Markierungen"
✅ **Gelöst:** Logic Bug behoben
- Jetzt wird korrekt gezählt
- Alert zeigt: "Total flagged (blur < threshold): X"

---

## Nächste Schritte

1. **Sofort:**
   - ✅ Threshold 0-300 implementiert
   - ✅ Bug behoben (Farb-Markierungen)
   - ✅ Blur Score in Thumbnails angezeigt

2. **Nächste Version:**
   - [ ] Tenengrad-Methode implementieren
   - [ ] Method-Selector in GUI (Laplacian vs. Tenengrad)
   - [ ] Threshold-Empfehlungen je nach Methode

3. **Zukünftig:**
   - [ ] ROI-basierte Methode
   - [ ] Hybrid-Score
   - [ ] ML-basierte Klassifizierung

---

## Verwendung

```python
# Aktuell (Laplacian Variance)
score = detect_blur(photo_path)
# Score: 0-300+ (höher = schärfer)
# Threshold empfohlen: 0-20 für verwackelte Bilder

# Mit Tenengrad (nach Implementierung)
score = detect_blur(photo_path, method=BlurMethod.TENENGRAD)
# Score: 0-50+ (höher = schärfer)
# Threshold empfohlen: 5-15 für unscharfe Bilder
```

---

**Status:** 
- ✅ Threshold 0-300 implementiert
- ✅ Bug behoben
- ⏳ Alternative Methoden dokumentiert
- ⏳ Tenengrad-Implementierung empfohlen
