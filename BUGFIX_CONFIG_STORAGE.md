# Bugfix & Feature: Config Storage Documentation + Show Config Button

## Datum: 2026-02-05

---

## Probleme behoben

### 1. Import-Fehler: `'SidecarManager' from 'photo_tool.prescan'`

**Problem**: 
```
Error: cannot import name 'SidecarManager' from 'photo_tool.prescan'
```

**Root Cause**: 
Die `__init__.py` hatte die Exports auskommentiert mit einem Hinweis "Import modules directly".

**Fix**:

```5:8:c:\_Git\Python-tools\photo_tool\prescan\__init__.py
from photo_tool.prescan.sidecar import SidecarManager
from photo_tool.prescan.scanner import FolderScanner

__all__ = ['SidecarManager', 'FolderScanner']
```

---

### 2. NoneType-Fehler: `argument of type 'NoneType' is not iterable`

**Problem**:
```
Error scanning E:\Lumix-2026-01\101_PANA\P1012568.JPG: argument of type 'NoneType' is not iterable
```

**Root Cause**:
`_data` in `SidecarManager` war manchmal `None` bei Dictionary-Operationen (`'key' in value`).

**Fixes in `photo_tool/prescan/sidecar.py`**:

#### 2.1 `load()` - Sicherstellen, dass immer Dictionary zurückgegeben wird
```python
def load(self) -> Dict[str, Any]:
    """Load sidecar data"""
    if not self.exists:
        self._data = self._create_empty()  # <-- Assign to _data
        return self._data
    
    try:
        with open(self.sidecar_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure it's a valid dictionary
            if not isinstance(data, dict):
                logger.warning(f"Invalid sidecar data for {self.photo_path}, recreating")
                self._data = self._create_empty()
            else:
                self._data = data
        return self._data
    
    except Exception as e:
        logger.error(f"Failed to load sidecar for {self.photo_path}: {e}")
        self._data = self._create_empty()  # <-- Always assign
        return self._data
```

#### 2.2 `save()` - Validate und reconstruct `scan_info` if missing
```python
def save(self, data: Optional[Dict[str, Any]] = None) -> bool:
    """Save sidecar data"""
    if data:
        self._data = data
    
    # Ensure _data exists and is valid
    if not self._data or not isinstance(self._data, dict):
        logger.warning(f"No valid data to save for {self.photo_path}")
        return False
    
    try:
        # Ensure scan_info exists
        if 'scan_info' not in self._data or not isinstance(self._data['scan_info'], dict):
            self._data['scan_info'] = {
                'scanned_at': datetime.now().isoformat(),
                'scanner_version': '1.0.0',
                'updated_at': datetime.now().isoformat()
            }
        
        # Update metadata
        self._data['scan_info']['updated_at'] = datetime.now().isoformat()
        
        with open(self.sidecar_path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to save sidecar for {self.photo_path}: {e}")
        return False
```

#### 2.3 `update_analysis()` - Validate all nested structures
```python
def update_analysis(self, analyzer_name: str, results: Dict[str, Any]) -> None:
    """Update analysis results"""
    if not self._data:
        self.load()
    
    # Ensure _data is a dictionary
    if not isinstance(self._data, dict):
        self._data = self._create_empty()
    
    if 'analyses' not in self._data:
        self._data['analyses'] = {}
    
    # Ensure analyses is a dictionary
    if not isinstance(self._data['analyses'], dict):
        self._data['analyses'] = {}
    
    self._data['analyses'][analyzer_name] = {
        **(results if results else {}),  # <-- Handle None results
        'computed_at': datetime.now().isoformat()
    }
```

---

## Neue Features

### 1. Configuration Storage Documentation

**Datei**: `CONFIG_STORAGE_GUIDE.md`

Vollständige Dokumentation aller Speicherorte:
- **Global Config**: `%USERPROFILE%\.photo_tool\`
  - Media Manager: `media\media_folders.json`
  - Workspace Registry: `workspaces.json`
- **Workspace Config**: `<workspace_path>\config.yaml`
- **Sidecar Files**: `<photo_dir>\.<photo_name>.phototool.json`

Enthält:
- Hierarchie-Diagramme
- JSON-Struktur-Beispiele
- Backup-Empfehlungen
- Troubleshooting-Tipps

---

### 2. "Show Config" Button im Media Manager

#### Backend: `/api/system/config-info` Endpoint

```python
@app.get('/api/system/config-info')
def get_config_info():
    """Get configuration file locations and structure"""
```

**Response**:
```json
{
  "global_config": {
    "root": "C:\\Users\\username\\.photo_tool",
    "exists": true
  },
  "media_manager": {
    "config_file": "C:\\Users\\username\\.photo_tool\\media\\media_folders.json",
    "exists": true,
    "size": "2.3 KB",
    "folder_count": 3
  },
  "workspace_registry": {
    "config_file": "C:\\Users\\username\\.photo_tool\\workspaces.json",
    "exists": true,
    "size": "156 B",
    "workspace_count": 2
  },
  "current_workspace": {
    "path": "C:\\Photos\\Nepal-2025",
    "config_file": "C:\\Photos\\Nepal-2025\\config.yaml",
    "exists": true,
    "size": "1.2 KB"
  },
  "sidecars": [
    {
      "folder": "E:\\Lumix-2026-01\\101_PANA",
      "sidecar_count": 961,
      "name": "Lumix S5 Jan 2026",
      "category": "usb",
      "enabled": true
    },
    {
      "folder": "E:\\NEPAL-2025\\Galaxy-S22",
      "sidecar_count": 1227,
      "name": "Samsung Galaxy",
      "category": "usb"
    }
  ]
}
```

**Features**:
- Dateigröße-Formatierung (B, KB, MB, GB)
- Rekursives Zählen von Sidecar-Files
- USB-Volume-Informationen
- Scan-Status pro Folder

---

#### Frontend: Config Modal

**Button im Media Manager**:
```html
<button @click="showConfigInfo">
    📋 Show Config
</button>
```

**Modal Features**:
- **Global Config Root**: Zeigt `.photo_tool` Verzeichnis
- **Media Manager**: Config-Datei + Anzahl Folders
- **Workspace Registry**: Config-Datei + Anzahl Workspaces
- **Current Workspace**: Pfad und config.yaml
- **Sidecar Files**: Liste aller Folders mit Sidecar-Counts

**Styling**:
- Farbcodiert nach Komponente:
  - 🌍 Global: Grün
  - 📱 Media Manager: Blau
  - 🗂️ Workspace: Violett
  - 📄 Sidecars: Gold
- Monospace-Font für Pfade
- Status-Indikatoren (✓ Exists / ✗ Not Found)
- Category-Badges (usb, network, internal)

---

## Testing

### 1. Import-Fehler
```bash
python -c "from photo_tool.prescan import SidecarManager, FolderScanner; print('OK')"
# → OK
```

### 2. Sidecar Robustness
Test mit:
- Fehlenden Sidecar-Files (werden erstellt)
- Korrupten JSON-Files (werden neu erstellt)
- Fehlenden Feldern (werden hinzugefügt)

### 3. Config Info Button
1. Media Manager öffnen
2. "📋 Show Config" klicken
3. Modal zeigt:
   - Alle Config-Pfade
   - Dateigrößen
   - Sidecar-Counts
   - Category-Badges

---

## Vorteile

### 1. Robustheit
- Alle Sidecar-Operationen sind nun `None`-sicher
- Automatische Rekonstruktion bei fehlenden Feldern
- Graceful Handling von Dateisystem-Fehlern

### 2. Transparenz
- Benutzer sieht **exakt**, wo alle Daten gespeichert werden
- Sidecar-Counts helfen bei Troubleshooting
- Config-Pfade sind kopierbar für manuellen Zugriff

### 3. Wartbarkeit
- Zentrale Dokumentation (`CONFIG_STORAGE_GUIDE.md`)
- API-Endpoint für programmatischen Zugriff
- Hilfreich für Backups und Migrationen

---

## Dateien geändert

### Backend
- `c:\_Git\Python-tools\photo_tool\prescan\__init__.py` - Exports reaktiviert
- `c:\_Git\Python-tools\photo_tool\prescan\sidecar.py` - NoneType-Fixes
- `c:\_Git\Python-tools\gui_poc\server.py` - `/api/system/config-info` Endpoint

### Frontend
- `c:\_Git\Python-tools\gui_poc\static\index.html` - "Show Config" Button + Modal

### Dokumentation
- `c:\_Git\Python-tools\CONFIG_STORAGE_GUIDE.md` - Vollständige Storage-Doku
- `c:\_Git\Python-tools\BUGFIX_CONFIG_STORAGE.md` - Dieses Dokument

---

## Nächste Schritte

1. **Server neu starten** und Media Manager testen
2. Folder scannen und Sidecar-Robustheit verifizieren
3. "Show Config" Button testen
4. Bei Bedarf: Backup-Script für alle Configs erstellen

---

## User Feedback

> "im media manager können jetzt medienfolder addiert werden und gescannt werden (vorerst nur blur scan). im workspace manager können workspaces erzeugt werden, medienfolder addiert werden. wo werden die konfigurationsfiles für den mediamanger und die workspaces gespeicert?"

✅ **Beantwortet** durch `CONFIG_STORAGE_GUIDE.md` und "Show Config" Button

> "vielleicht wäre im media manager ein button 'show config', der zumindest eine textausgabe des filetrees für .json configs ausführt."

✅ **Implementiert** als grafisches Modal mit allen Infos
