# Workspace Cleanup Guide

## Datum: 2026-02-06

---

## Übersicht

Feature zum **sicheren Entfernen** von Workspaces, inkl. optionalem Löschen von Config-Files.

**Wichtig**: Medien-Files werden **NIE** gelöscht! Nur Workspace-Registry-Einträge und optional `config.yaml`.

---

## Features

### 1. Workspace aus Registry entfernen

**Was passiert:**
- Workspace wird aus `~/.photo_tool/workspaces.json` entfernt
- `config.yaml` bleibt erhalten
- Alle Medien bleiben erhalten

**Wann benutzen:**
- Workspace temporär deaktivieren
- Registry aufräumen, aber Config behalten
- Workspace später wieder hinzufügen möglich

---

### 2. Workspace entfernen + Config löschen

**Was passiert:**
- Workspace wird aus Registry entfernt
- `<workspace_path>/config.yaml` wird gelöscht
- Alle Medien bleiben erhalten

**Wann benutzen:**
- Alte/inkompatible Configs entfernen
- Workspace komplett aufräumen
- Neu anfangen mit sauberer Config

---

## GUI Bedienung

### Workspace Manager Tab

Jede Workspace-Karte zeigt:

```
┌─────────────────────────────────┐
│ Workspace Name        ● ACTIVE  │
│ C:\Photos\Nepal-2025            │
│                                 │
│ [Switch] [🗑️]                   │
└─────────────────────────────────┘
```

**🗑️ Delete Button**:
- Nur bei inaktiven Workspaces klickbar
- Aktiver Workspace: Button disabled (grau)
- Klick öffnet 2-stufigen Bestätigungs-Dialog

---

## Bestätigungs-Dialog

### Schritt 1: Grundsätzliche Bestätigung

```
Remove Workspace "Nepal-2025"?

Path: C:\Photos\Nepal-2025

This will remove the workspace from the registry.
Media files will NOT be deleted.

Continue?

[OK] [Cancel]
```

- **OK** → Weiter zu Schritt 2
- **Cancel** → Abbrechen

---

### Schritt 2: Config-Löschung

```
Delete config.yaml file?

File: C:\Photos\Nepal-2025/config.yaml

This will permanently delete the workspace configuration.
Media files will remain untouched.

YES = Delete config.yaml
NO = Keep config.yaml (only remove from registry)

[OK = YES] [Cancel = NO]
```

- **OK (YES)** → Workspace + Config löschen
- **Cancel (NO)** → Nur aus Registry entfernen

---

## Backend Implementation

### WorkspaceManager.remove_workspace()

```python
def remove_workspace(self, path: str, delete_config: bool = False) -> bool:
    """
    Remove a workspace from the list
    
    Args:
        path: Workspace path
        delete_config: If True, also delete config.yaml (but NOT media files)
    
    Returns:
        True if successful
    """
```

**Sicherheitsfeatures**:
- Nur `config.yaml` wird gelöscht
- Medien-Ordner bleiben unberührt
- Registry wird immer aktualisiert
- Logging aller Aktionen

---

### API Endpoint: DELETE /api/workspaces/<path>

**Request**:
```json
{
  "delete_config": true  // Optional, default: false
}
```

**Response (Success)**:
```json
{
  "success": true,
  "message": "Workspace removed and config deleted"
}
```

**Response (Error)**:
```json
{
  "error": "Workspace not found or could not be deleted"
}
```

---

## Use Cases

### Case 1: Alte inkompatible Configs aufräumen

**Problem**: Nach Schema-Änderungen funktionieren alte Configs nicht mehr

**Lösung**:
1. Workspace im Workspace Manager finden
2. 🗑️ Button klicken
3. Beide Dialoge mit OK bestätigen
4. → Alte Config gelöscht, Medien bleiben
5. Optional: Workspace neu erstellen mit frischer Config

---

### Case 2: Workspace temporär deaktivieren

**Problem**: Zu viele Workspaces in der Liste

**Lösung**:
1. 🗑️ Button klicken
2. Ersten Dialog mit OK bestätigen
3. Zweiten Dialog mit **Cancel** (NO) → Config behalten
4. → Workspace aus Liste entfernt, aber Config bleibt
5. Später: Workspace wieder hinzufügen via "Add Workspace"

---

### Case 3: Test-Workspaces entfernen

**Problem**: Viele Test/Debug-Workspaces angelegt

**Lösung**:
1. Jeden Test-Workspace einzeln löschen
2. Config löschen = YES
3. → Clean Registry + Filesystem

---

## Sicherheit

### Was wird NICHT gelöscht:

✅ **Niemals gelöscht**:
- Foto-Files (`.jpg`, `.raw`, etc.)
- Video-Files (`.mp4`, etc.)
- Sidecar-Files (`.phototool.json`)
- Media-Ordner
- Unterordner im Workspace-Pfad

❌ **Nur wenn explizit gewählt**:
- `config.yaml` (nur bei delete_config=true)

---

### Schutz vor Versehen:

1. **Aktiver Workspace**: Kann nicht gelöscht werden
   - Button ist disabled
   - Meldung: "Switch to another workspace first"

2. **2-Stufen-Bestätigung**:
   - Erst: Workspace entfernen?
   - Dann: Config auch löschen?

3. **Klare Meldungen**:
   - "Media files will NOT be deleted"
   - "Workspace removed (config.yaml kept)"

---

## Workflow: Alle Workspaces neu aufsetzen

Falls du **alle Workspaces** mit frischen Configs neu starten möchtest:

### 1. Alte Workspaces entfernen

Für jeden Workspace:
```
1. Workspace Manager öffnen
2. Sicherstellen, dass Workspace NICHT aktiv ist
3. 🗑️ klicken
4. OK → OK (Config löschen)
5. Wiederholen für alle alten Workspaces
```

---

### 2. Registry komplett zurücksetzen (optional)

**Manuell** (wenn GUI-Methode zu langsam):

```powershell
# Windows PowerShell (VORSICHT!)
del "$env:USERPROFILE\.photo_tool\workspaces.json"
```

**Was passiert:**
- Alle Workspaces aus Registry entfernt
- Config-Files bleiben (falls du NO gewählt hast)
- Server neu starten

---

### 3. Frische Workspaces erstellen

```
1. Workspace Manager → Add Workspace
2. Pfad auswählen
3. Name eingeben
4. → Neue config.yaml wird erstellt
5. Media-Folders hinzufügen
```

---

## Troubleshooting

### Problem: "Workspace not found"

**Ursache**: Workspace existiert nicht mehr im Filesystem

**Lösung**:
```python
# Manuell aus Registry entfernen
import json
from pathlib import Path

registry = Path.home() / ".photo_tool" / "workspaces.json"
data = json.loads(registry.read_text())
data['workspaces'] = [w for w in data['workspaces'] if Path(w['path']).exists()]
registry.write_text(json.dumps(data, indent=2))
```

---

### Problem: Config löschen funktioniert nicht

**Ursache**: Keine Schreibrechte oder Datei ist geöffnet

**Lösung**:
1. Server stoppen
2. Datei manuell löschen
3. Server neu starten

```powershell
# Manuell löschen
del "C:\Photos\Nepal-2025\config.yaml"
```

---

### Problem: Zu viele Test-Workspaces

**Lösung**: Bulk-Delete-Script (siehe unten)

---

## Bulk-Delete-Script

Falls du viele Workspaces auf einmal löschen möchtest:

```python
# cleanup_workspaces.py
from pathlib import Path
from photo_tool.workspace.manager import WorkspaceManager

def cleanup_old_workspaces():
    """Remove all workspaces with old/broken configs"""
    wm = WorkspaceManager()
    
    workspaces_to_remove = []
    
    for ws in wm.workspaces:
        ws_path = Path(ws['path'])
        config_file = ws_path / "config.yaml"
        
        # Check if config exists and is valid
        if not config_file.exists():
            print(f"❌ No config: {ws_path}")
            workspaces_to_remove.append(ws)
            continue
        
        # Try to load config
        try:
            from photo_tool.config import load_config
            load_config(config_file)
            print(f"✓ Valid: {ws_path}")
        except Exception as e:
            print(f"❌ Invalid config: {ws_path} - {e}")
            workspaces_to_remove.append(ws)
    
    # Confirm removal
    if workspaces_to_remove:
        print(f"\nFound {len(workspaces_to_remove)} workspaces to remove:")
        for ws in workspaces_to_remove:
            print(f"  - {ws['name']} ({ws['path']})")
        
        if input("\nDelete all configs? (yes/no): ").lower() == 'yes':
            for ws in workspaces_to_remove:
                wm.remove_workspace(ws['path'], delete_config=True)
                print(f"✓ Removed: {ws['path']}")
            print(f"\n✓ Cleanup complete!")
        else:
            print("Aborted.")
    else:
        print("\n✓ No invalid workspaces found!")

if __name__ == '__main__':
    cleanup_old_workspaces()
```

**Verwendung**:
```bash
cd c:\_Git\Python-tools
python -c "from photo_tool.workspace.manager import WorkspaceManager; wm = WorkspaceManager(); print('\n'.join([f'{w[\"name\"]}: {w[\"path\"]}' for w in wm.workspaces]))"
```

---

## Logging

Alle Workspace-Operationen werden geloggt:

```
INFO - Removed workspace from registry: C:\Photos\Nepal-2025
INFO - Deleted config file: C:\Photos\Nepal-2025\config.yaml
```

**Log-Location**:
- Terminal Output (während Server läuft)
- Optional: `photo_tool.log` (wenn konfiguriert)

---

## Testing

### 1. Test: Workspace entfernen (Config behalten)

```
1. Workspace erstellen
2. Config überprüfen (existiert)
3. Workspace löschen (NO bei Config-Frage)
4. ✓ Registry: Workspace weg
5. ✓ Filesystem: config.yaml existiert noch
```

---

### 2. Test: Workspace + Config löschen

```
1. Workspace erstellen
2. Config überprüfen (existiert)
3. Workspace löschen (YES bei Config-Frage)
4. ✓ Registry: Workspace weg
5. ✓ Filesystem: config.yaml gelöscht
6. ✓ Medien: Alle Files noch da
```

---

### 3. Test: Aktiver Workspace

```
1. Workspace aktivieren
2. 🗑️ Button klicken
3. ✓ Meldung: "Switch to another workspace first"
4. ✓ Button ist disabled
```

---

## Dateien geändert

### Backend
- `photo_tool/workspace/manager.py` - `remove_workspace()` mit `delete_config` Parameter
- `gui_poc/server.py` - DELETE endpoint erweitert

### Frontend
- `gui_poc/static/index.html` - 🗑️ Button + 2-Stufen-Dialog

### Dokumentation
- `WORKSPACE_CLEANUP_GUIDE.md` - Dieses Dokument

---

## Best Practices

### 1. Vor großen Änderungen: Backup!

```powershell
# Backup gesamte Config
xcopy /E /I "$env:USERPROFILE\.photo_tool" "D:\Backup\phototool-config"
```

---

### 2. Workspaces sauber benennen

- ✓ `Nepal-Trekking-2025`
- ✓ `Wedding-Photos-Schmidt`
- ❌ `test`, `test2`, `workspace1`

→ Erleichtert späteres Aufräumen

---

### 3. Regelmäßig aufräumen

- Test-Workspaces direkt nach Tests löschen
- Alte Workspaces monatlich reviewen
- Registry klein halten (max. 10-20 Workspaces)

---

## Zukünftige Features

Mögliche Erweiterungen:

1. **Workspace archivieren** (disabled, aber in Registry)
2. **Workspace exportieren** (inkl. Config)
3. **Workspace duplizieren** (für Varianten)
4. **Bulk-Actions** (mehrere Workspaces auf einmal)
5. **Workspace-Tags** (Filterung/Sortierung)

---

## Support

Bei Problemen:
1. Logs prüfen
2. Registry-File prüfen: `~/.photo_tool/workspaces.json`
3. Config-File prüfen: `<workspace>/config.yaml`
4. Manuell aufräumen (siehe Troubleshooting)
