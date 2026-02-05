# Pre-Scan Architecture - Implementierungsplan

## Übersicht

Das Pre-Scan System analysiert Medienordner einmalig und speichert alle Ergebnisse in Sidecar-Dateien (.phototool.json). Diese Daten stehen dann sofort für alle Workspaces und Projekte zur Verfügung.

## Architektur

### Komponenten

```
photo_tool/
├── prescan/
│   ├── __init__.py
│   ├── scanner.py          # Haupt-Scanner
│   ├── sidecar.py          # Sidecar-Management
│   ├── analyzers/
│   │   ├── blur.py         # Blur-Analyse (alle Methoden)
│   │   ├── burst.py        # Burst-Erkennung
│   │   ├── histogram.py    # Histogram-Analyse
│   │   ├── quality.py      # Qualitäts-Metriken
│   │   └── exif.py         # EXIF-Extraktion
│   └── index.py            # Ordner-Index
```

## Sidecar-Format

### Dateiname
```
Original:  IMG_1234.jpg
Sidecar:   IMG_1234.jpg.phototool.json
```

### Schema v1.0

```json
{
  "version": "1.0",
  "photo": {
    "path": "IMG_1234.jpg",
    "size_bytes": 4567890,
    "modified_at": "2024-01-15T12:30:00Z",
    "file_hash": "sha256:abc123..."
  },
  
  "scan_info": {
    "scanned_at": "2024-01-15T14:30:00Z",
    "scanner_version": "1.0.0",
    "scan_duration_ms": 2345
  },
  
  "analyses": {
    "blur": { /* siehe oben */ },
    "burst": { /* siehe oben */ },
    "histogram": { /* siehe oben */ },
    "exif": { /* siehe oben */ },
    "quality": { /* siehe oben */ }
  }
}
```

## Scanner-Workflow

### 1. Initialisierung
```python
from photo_tool.prescan import FolderScanner

scanner = FolderScanner(
    folder_path="C:/Photos/2024/",
    analyzers=['blur', 'burst', 'histogram', 'exif'],
    threads=4,  # Parallel processing
    skip_existing=True  # Skip already scanned photos
)
```

### 2. Ausführung
```python
# Option A: Blocking
scanner.scan()

# Option B: Non-blocking mit Progress
async for progress in scanner.scan_async():
    print(f"{progress.current}/{progress.total} - {progress.message}")
```

### 3. Fortschritt
```python
{
  "status": "running",
  "total": 1234,
  "completed": 567,
  "current_file": "IMG_1234.jpg",
  "current_analyzer": "blur_roi",
  "elapsed_seconds": 1234,
  "estimated_remaining_seconds": 2345,
  "errors": []
}
```

## Integration mit Workspace

### Beim Hinzufügen eines Folders

```python
# Alte Methode (ohne Sidecar):
workspace.add_folder("C:/Photos/2024/")
→ Alle Analysen müssen on-demand berechnet werden

# Neue Methode (mit Sidecar):
workspace.add_folder("C:/Photos/2024/")
→ Sidecar-Daten werden sofort geladen
→ Blur-Scores, Burst-Links etc. sofort verfügbar
→ Nur fehlende Analysen werden nachberechnet
```

### API-Integration

```python
# Check if folder is scanned
GET /api/folders/{folder_id}/scan-status

Response:
{
  "is_scanned": true,
  "scan_date": "2024-01-15T14:30:00Z",
  "coverage": {
    "blur": 100,      # % of photos with blur data
    "burst": 100,
    "histogram": 100,
    "exif": 98
  },
  "needs_rescan": false
}

# Trigger scan
POST /api/folders/{folder_id}/scan
{
  "analyzers": ["blur", "burst"],
  "force_rescan": false
}

# Get scan progress
GET /api/folders/{folder_id}/scan-progress (SSE)
```

## Sidecar-Management

### Lesen
```python
from photo_tool.prescan.sidecar import SidecarManager

sidecar = SidecarManager.load("IMG_1234.jpg")
blur_score = sidecar.get("blur.laplacian.score")
is_burst = sidecar.get("burst.is_burst")
```

### Schreiben
```python
sidecar.update({
    "blur.laplacian.score": 156.4,
    "blur.laplacian.computed_at": datetime.now()
})
sidecar.save()
```

### Validierung
```python
if sidecar.is_stale():
    # File modified since scan
    scanner.rescan_photo("IMG_1234.jpg")
```

## Scanner-Implementierung

### FolderScanner

```python
class FolderScanner:
    def __init__(self, folder_path, analyzers, threads=4):
        self.folder = Path(folder_path)
        self.analyzers = self._init_analyzers(analyzers)
        self.threads = threads
        self.index = FolderIndex(folder_path)
    
    def scan(self):
        """Blocking scan"""
        photos = self._discover_photos()
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            for photo in photos:
                if self._should_scan(photo):
                    future = executor.submit(self._scan_photo, photo)
                    futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                self._update_progress(result)
        
        self.index.save()
    
    def _scan_photo(self, photo_path):
        """Scan single photo"""
        sidecar = SidecarManager.load(photo_path)
        
        for analyzer in self.analyzers:
            result = analyzer.analyze(photo_path)
            sidecar.update(analyzer.namespace, result)
        
        sidecar.save()
        return photo_path
```

### Analyzer Interface

```python
class Analyzer(ABC):
    @property
    @abstractmethod
    def namespace(self) -> str:
        """Namespace in sidecar (e.g., 'blur', 'burst')"""
        pass
    
    @abstractmethod
    def analyze(self, photo_path: Path) -> dict:
        """Analyze photo and return results"""
        pass
    
    def should_reanalyze(self, sidecar: dict) -> bool:
        """Check if analysis needs update"""
        return False
```

### BlurAnalyzer

```python
class BlurAnalyzer(Analyzer):
    namespace = "blur"
    
    def analyze(self, photo_path: Path) -> dict:
        results = {}
        
        for method in [BlurMethod.LAPLACIAN, BlurMethod.TENENGRAD, BlurMethod.ROI]:
            score = detect_blur(photo_path, method=method)
            results[method.value] = {
                "score": score,
                "computed_at": datetime.now().isoformat(),
                "method_version": "1.0"
            }
        
        return results
```

## Burst-Verlinkung

### Burst-Erkennung
```python
class BurstAnalyzer(Analyzer):
    namespace = "burst"
    
    def analyze_folder(self, folder_path: Path) -> dict:
        """Analyze all photos in folder for bursts"""
        photos = sorted(self._get_photos(folder_path))
        bursts = self._detect_bursts(photos)
        
        # Update all sidecars with burst info
        for burst in bursts:
            for i, photo in enumerate(burst.photos):
                self._update_sidecar(photo, {
                    "is_burst": True,
                    "burst_id": burst.id,
                    "group_size": len(burst.photos),
                    "position_in_burst": i,
                    "siblings": [p.name for p in burst.photos if p != photo],
                    "similarity_to_prev": burst.similarities[i-1] if i > 0 else None,
                    "similarity_to_next": burst.similarities[i] if i < len(burst.photos)-1 else None
                })
```

### Burst-Links in GUI
```javascript
// Thumbnail zeigt Burst-Info
if (photo.burst && photo.burst.is_burst) {
    // Badge: "📦 5/12" (Position 5 von 12)
    // Click → Lightbox mit allen Burst-Fotos
    // Vergleichs-Ansicht möglich
}
```

## Performance

### Geschwindigkeit
```
Scanner-Performance (geschätzt):
- Blur (3 Methoden): ~200ms/Foto
- Burst: Einmal für ganzen Ordner
- Histogram: ~50ms/Foto
- EXIF: ~10ms/Foto
- Total: ~300ms/Foto

1000 Fotos:
- Single-threaded: ~5 Minuten
- 4 Threads: ~1.5 Minuten
- Overnight: Tausende Fotos möglich
```

### Speicherplatz
```
Sidecar-Größe: ~5-10 KB/Foto
1000 Fotos: ~5-10 MB Sidecars
Vernachlässigbar im Vergleich zu Fotos (5 MB/Foto)
```

## Migration

### Von aktuellem System zu Sidecar

```python
# Schritt 1: Existierende Metadata konvertieren
for photo in workspace.photos:
    metadata = get_metadata(photo.path)
    sidecar = SidecarManager.create(photo.path)
    
    # Migrieren
    if 'blur_score_laplacian' in metadata:
        sidecar.update('blur.laplacian.score', metadata['blur_score_laplacian'])
    
    sidecar.save()

# Schritt 2: Fehlende Analysen ergänzen
scanner = FolderScanner(workspace.folders)
scanner.scan(skip_existing=True)
```

## GUI-Integration

### Scan-Status anzeigen
```
Workspace: "Urlaub 2024"
Folders:
  ✓ C:/Photos/2024/01/  (Scanned: 2024-01-15, 100%)
  ⚠ C:/Photos/2024/02/  (Scanned: 2024-01-10, 85% - needs update)
  ✗ C:/Photos/2024/03/  (Not scanned)
  
[Scan All Folders] [Configure Scanner]
```

### Scan-Progress
```
Scanning: C:/Photos/2024/03/
Progress: ████████████░░░░░░  567 / 1234
Current: IMG_5678.jpg
Analyzer: Blur (ROI method)
Elapsed: 5:23
Remaining: ~8:45
```

## CLI-Tool

```bash
# Scan einzelnen Ordner
python -m photo_tool.prescan scan "C:/Photos/2024/"

# Scan mit spezifischen Analyzern
python -m photo_tool.prescan scan "C:/Photos/2024/" \
    --analyzers blur,burst,histogram

# Rescan (force)
python -m photo_tool.prescan scan "C:/Photos/2024/" --force

# Status check
python -m photo_tool.prescan status "C:/Photos/2024/"

# Statistiken
python -m photo_tool.prescan stats "C:/Photos/2024/"
```

## Vorteile

1. **Einmal berechnen, überall nutzen**
   - Workspaces teilen Analysedaten
   - Keine Duplikation
   
2. **Schnelles Projekt-Setup**
   - Blur-Scores sofort verfügbar
   - Burst-Links vorberechnet
   
3. **Portable**
   - Sidecars können mit Fotos kopiert werden
   - Unabhängig von Workspace-DB
   
4. **Inkrementell**
   - Neue Fotos werden automatisch gescannt
   - Alte Sidecars bleiben gültig
   
5. **Erweiterbar**
   - Neue Analyzer einfach hinzufügen
   - Alte Sidecars bleiben kompatibel

## Nächste Schritte

### Minimal Viable Product (MVP)

1. **Sidecar-Management**
   - [x] JSON-Format definiert
   - [ ] SidecarManager implementieren
   - [ ] Validierung & Migration

2. **Blur-Scanner**
   - [ ] BlurAnalyzer implementieren
   - [ ] Parallel processing
   - [ ] Progress tracking

3. **GUI-Integration**
   - [ ] Scan-Button in Workspace-Tab
   - [ ] Progress-Anzeige
   - [ ] Status-Badge bei Folders

4. **API-Endpoints**
   - [ ] POST /api/folders/{id}/scan
   - [ ] GET /api/folders/{id}/scan-progress
   - [ ] GET /api/folders/{id}/scan-status

### Future Features

- [ ] Burst-Analyzer mit Verlinkung
- [ ] Histogram-Analyzer
- [ ] Quality-Metriken (Noise, DR)
- [ ] Scheduler für automatische Scans
- [ ] Watch-Mode (Ordner überwachen)
- [ ] Cloud-Sync für Sidecars

---

**Status:** 📋 **Konzept fertig, bereit für Implementierung**

Diese Architektur ist professionell, erweiterbar und löst das Performance-Problem elegant!
