# Bugfix: Workspace Scope für Sidecar-Anzeige

## Datum: 2026-02-06

---

## Problem

User berichtete:
> "Allerdings werden sidecar files für folder angezeigt, die nicht zu diesem workspace gehören! die sidecar files sollten nur für die folder des aktiven workspaces angezeigt werden."

**Situation**:
- Neuer Workspace `WS-Test` mit 1 Folder: `C:\Photo-Tool\media-test`
- "Show Config" Modal zeigte Sidecars für **alle** Media-Manager-Folders:
  - `E:\Lumix-2026-01\101_PANA` (234 sidecars) ❌ Nicht im Workspace!
  - `E:\Lumix-2026-01\test` (76 sidecars) ❌ Nicht im Workspace!

**Erwartung**:
- Nur Sidecars für Folders im **aktuellen Workspace** anzeigen
- `C:\Photo-Tool\media-test` (0 sidecars, noch nicht gescannt)

---

## Root Cause

### Backend: get_config_info() Funktion

**Problem-Code** (`gui_poc/server.py`):

```python
# Get folders from workspace and count their sidecars
config = load_config(config_path) if config_path.exists() else None
if config and hasattr(config, 'folders'):
    for folder in config.folders:
        # ... add workspace folders
        config_info['sidecars'].append(...)

# Media folders sidecar counts
for media_folder in media_manager.folders:  # ❌ ALLE Media-Manager-Folders!
    # Check if not already in workspace sidecars
    if not any(s['folder'] == media_folder.path for s in config_info['sidecars']):
        sidecar_count = count_sidecars(media_folder.path)
        config_info['sidecars'].append({  # ❌ Fügt ALLE hinzu!
            'folder': media_folder.path,
            'sidecar_count': sidecar_count,
            'name': media_folder.name,
            'category': media_folder.category
        })
```

**Problem**:
- Zuerst werden Workspace-Folders hinzugefügt (korrekt)
- Dann werden **ALLE** Media-Manager-Folders hinzugefügt (falsch)
- Check `if not any(...)` verhindert Duplikate, aber fügt trotzdem fremde Folders hinzu

---

## Fix

### 1. Backend: Nur Workspace-Folders anzeigen

**Datei**: `gui_poc/server.py`

**Neuer Code**:

```python
# Current workspace info
if workspace_manager.current_workspace:
    ws_path = Path(workspace_manager.current_workspace)
    config_path = ws_path / "config.yaml"
    
    config_info['current_workspace'] = {
        'path': str(ws_path),
        'config_file': str(config_path),
        'exists': config_path.exists(),
        'size': format_size(get_size(config_path))
    }
    
    # Get folders ONLY from current workspace and count their sidecars
    config = load_config(config_path) if config_path.exists() else None
    if config and hasattr(config, 'folders'):
        for folder in config.folders:
            folder_path = folder.get('path', '')
            if folder_path:
                sidecar_count = count_sidecars(folder_path)
                
                # Get additional info from media manager if available
                media_folder = next((mf for mf in media_manager.folders if mf.path == folder_path), None)
                
                config_info['sidecars'].append({
                    'folder': folder_path,
                    'sidecar_count': sidecar_count,
                    'enabled': folder.get('enabled', True),
                    'name': media_folder.name if media_folder else None,  # ✓ Optional
                    'category': media_folder.category if media_folder else None  # ✓ Optional
                })
```

**Änderungen**:
- ❌ **Entfernt**: Loop über `media_manager.folders`
- ✓ **Nur**: Folders aus `config.folders` (aktueller Workspace)
- ✓ **Lookup**: Hole Name/Category aus Media Manager (falls vorhanden)
- ✓ **Graceful**: Falls Folder nicht im Media Manager: `None`

---

### 2. Backend: Leere Folder-Meldung

**Problem**: Wenn Workspace keine enabled Folders hat, sollte klare Meldung kommen

**Fix** (`gui_poc/server.py`):

```python
@app.get('/api/photos')
def get_photos():
    """..."""
    # ...
    
    # Get only enabled folders
    enabled_folders = get_enabled_folders(workspace_path)
    if not enabled_folders:
        # No folders enabled - return empty list
        return jsonify({
            'photos': [],
            'total': 0,
            'offset': 0,
            'limit': 0,
            'message': 'No folders enabled in workspace. Add and enable media folders first.'
        })
```

---

### 3. Frontend: Meldung anzeigen

**Datei**: `gui_poc/static/index.html`

```javascript
async loadPhotos() {
    // ...
    const data = await res.json();
    
    // Check if there's a message (e.g., no folders enabled)
    if (data.message && data.total === 0) {
        this.error = data.message;  // ✓ Zeige Meldung
        this.photos = [];
        this.totalPhotos = 0;
        return;
    }
    
    // ... normal flow
}
```

---

## Ergebnis

### Vorher (Bug):

**Show Config Modal**:
```
📄 Sidecar Files (.phototool.json)

E:\Lumix-2026-01\101_PANA
234 sidecars                      ❌ Nicht im Workspace!
Pasang-1
usb

E:\Lumix-2026-01\test
76 sidecars                       ❌ Nicht im Workspace!
test folder
usb
```

**Problem**: Alle Media-Manager-Folders angezeigt

---

### Nachher (Fix):

**Show Config Modal**:
```
📄 Sidecar Files (.phototool.json)

C:\Photo-Tool\media-test
0 sidecars                        ✓ Nur Workspace-Folder!
(nicht gescannt)
```

**Korrekt**: Nur Folders im aktuellen Workspace

---

## Testing

### Test 1: Workspace mit 1 Folder

```
1. Neuen Workspace erstellen
2. 1 Media-Folder hinzufügen
3. "Show Config" öffnen
4. ✓ Nur dieser 1 Folder in Sidecar-Liste
5. ✓ Andere Media-Manager-Folders NICHT sichtbar
```

---

### Test 2: Workspace mit 0 Folders

```
1. Neuen Workspace erstellen (ohne Folders)
2. "Show Config" öffnen
3. ✓ Sidecar-Liste ist leer
4. ✓ Keine fremden Folders
```

---

### Test 3: Workspace wechseln

```
1. Workspace A (Folder: E:\Lumix)
2. "Show Config" → zeigt E:\Lumix ✓
3. Wechsel zu Workspace B (Folder: C:\Test)
4. "Show Config" → zeigt C:\Test ✓
5. ✓ E:\Lumix NICHT mehr sichtbar
```

---

## Architektur-Klarstellung

### Hierarchie:

```
Media Manager (global)
├── E:\Lumix-2026-01\101_PANA (234 sidecars)
└── E:\Lumix-2026-01\test (76 sidecars)

Workspace A: Nepal-2025
├── Folder: E:\Lumix-2026-01\101_PANA  ← Link zu Media Manager
└── Folder: E:\NEPAL-2025\Galaxy-S22

Workspace B: WS-Test
└── Folder: C:\Photo-Tool\media-test   ← Eigener Folder
```

**Regel**:
- **Media Manager**: Registriert ALLE Folders (global)
- **Workspace**: Linkt zu ausgewählten Folders
- **Show Config**: Zeigt nur Folders des **aktuellen Workspace**

---

## Zusätzliche Erkenntnis: Projekt-basiertes Laden

User erwähnte auch:
> "es gibt noch keine projekte in diesem neuen workspace, daher sollten auch noch keine photos importiert werden. erst wenn projekte erstellt wurden, sollten die betreffenden photos geladen werden."

**Aktuelles Verhalten**:
- Photos werden aus Workspace-Folders geladen (unabhängig von Projekten)

**User-Erwartung**:
- Photos erst laden, wenn Projekt existiert

**Architektur-Überlegung**:
```
Workspace → enthält Folders
Project → Auswahl/Filter auf Photos aus Workspace
```

**Mögliche Lösung** (für später):
1. Workspace definiert verfügbare Medien
2. Projekt definiert Selektion/Filter
3. Photos-Tab zeigt nur Projekt-Photos (nicht alle Workspace-Photos)

**Status**: Für jetzt → Photos werden aus enabled Folders geladen (wie bisher)

**Hinweis**: Optional Parameter `load_without_project` vorbereitet (aber noch nicht genutzt)

---

## Related Issues

### Issue: Photo-Import ohne Projekt

**User-Feedback**:
> "es gibt noch keine projekte, daher sollten auch noch keine photos importiert werden"

**Analyse**:
- Aktuell: Photos werden aus Workspace-Folders geladen
- User erwartet: Photos erst bei Projekt-Existenz

**Vorschlag für Zukunft**:
1. **Option 1**: Default-Projekt automatisch erstellen
2. **Option 2**: Photos-Tab erst nach Projekt-Erstellung anzeigen
3. **Option 3**: "Create Project" Wizard beim ersten Workspace-Zugriff

**Entscheidung**: Für V1 belassen wie ist (Photos aus Workspace-Folders)

---

## Dateien geändert

- `gui_poc/server.py`:
  - `get_config_info()` - Nur Workspace-Folders für Sidecars
  - `get_photos()` - Meldung bei leeren Folders
- `gui_poc/static/index.html`:
  - `loadPhotos()` - Meldung anzeigen
- `BUGFIX_WORKSPACE_SCOPE.md` - Dieses Dokument

---

## Lessons Learned

1. **Scope is important**: Global vs. Workspace vs. Project
2. **User expectations**: "Show Config" = aktueller Workspace, nicht alle Daten
3. **Clear boundaries**: Media Manager (global) ≠ Workspace (local)
4. **Feature creep**: User erwähnte Projekt-basiertes Laden → separates Feature

---

## Next Steps

Für User:
1. ✅ Server neu starten
2. ✅ "Show Config" testen → nur Workspace-Folders
3. ⚠️ Projekt-basiertes Laden → separates Feature (optional)

Für Entwicklung:
1. ✅ Bugfix deployed
2. 🔄 Projekt-basiertes Photo-Laden → später diskutieren
3. 📝 Dokumentation aktualisiert
