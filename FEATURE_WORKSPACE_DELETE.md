# Feature: Workspace Delete mit Config-Löschung

## Datum: 2026-02-06

---

## Problem

User berichtete:
> "wie kann man workspaces entfernen? und deren configs löschen? es scheint, dass einige workspaces mit alten und inkompatiblen configs vorhanden sind, da wir die methoden der verwaltung verändert haben."

**Anforderungen**:
1. ✅ Workspaces aus Registry entfernen
2. ✅ Config-Files löschen können
3. ✅ GUI mit Remove-Button
4. ✅ Medien NIEMALS löschen
5. ✅ Alte/inkompatible Configs aufräumen

---

## Lösung

### 1. Backend: Erweiterte remove_workspace() Funktion

**Datei**: `photo_tool/workspace/manager.py`

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

**Features**:
- Entfernt Workspace aus Registry (`~/.photo_tool/workspaces.json`)
- Optional: Löscht `config.yaml` im Workspace-Verzeichnis
- **Sicherheit**: Nur `config.yaml` wird gelöscht, niemals Medien!
- Logging aller Aktionen

---

### 2. Backend: API Endpoint erweitert

**Datei**: `gui_poc/server.py`

**Endpoint**: `DELETE /api/workspaces/<path>`

**Request Body**:
```json
{
  "delete_config": true  // Optional, default: false
}
```

**Response**:
```json
{
  "success": true,
  "message": "Workspace removed and config deleted"
}
```

---

### 3. Frontend: 🗑️ Delete Button

**Datei**: `gui_poc/static/index.html`

#### Workspace-Karte mit Delete-Button

```html
<button @click="confirmDeleteWorkspace(workspace)"
        :disabled="workspace.path === currentWorkspace">
    🗑️
</button>
```

**Button-Status**:
- ✅ **Enabled**: Bei inaktiven Workspaces
- ❌ **Disabled**: Aktiver Workspace kann nicht gelöscht werden

---

#### 2-Stufen-Bestätigungs-Dialog

**Schritt 1**: Workspace entfernen?
```
Remove Workspace "Nepal-2025"?

Path: C:\Photos\Nepal-2025

This will remove the workspace from the registry.
Media files will NOT be deleted.

Continue?
```

**Schritt 2**: Config auch löschen?
```
Delete config.yaml file?

File: C:\Photos\Nepal-2025/config.yaml

This will permanently delete the workspace configuration.
Media files will remain untouched.

YES = Delete config.yaml
NO = Keep config.yaml (only remove from registry)
```

**Ergebnis**:
- User wählt: Nur Registry oder Registry + Config
- Medien bleiben IMMER erhalten
- Klare Feedback-Meldung nach Aktion

---

## Sicherheitsfeatures

### 1. Schutz vor versehentlichem Löschen

✅ **Aktiver Workspace**:
- Delete-Button ist disabled
- Alert: "Cannot delete the currently active workspace"
- User muss erst zu anderem Workspace wechseln

✅ **2-Stufen-Bestätigung**:
- Erste Bestätigung: Wirklich entfernen?
- Zweite Bestätigung: Config auch löschen?
- Klare, ausführliche Meldungen

✅ **Medien-Schutz**:
- Nur `config.yaml` wird gelöscht
- Alle Foto/Video-Files bleiben
- Alle Sidecar-Files bleiben
- Alle Unterordner bleiben

---

### 2. Was wird gelöscht / behalten?

**❌ Gelöscht (nur bei delete_config=true)**:
- `<workspace_path>/config.yaml`

**✅ Immer behalten**:
- Alle Fotos (`.jpg`, `.raw`, etc.)
- Alle Videos (`.mp4`, etc.)
- Sidecar-Files (`.phototool.json`)
- Alle Unterordner
- Alle anderen Files im Workspace

**✅ Immer entfernt**:
- Workspace-Eintrag in `~/.photo_tool/workspaces.json`

---

## Use Cases

### Case 1: Alte inkompatible Configs aufräumen

**Situation**: Nach Schema-Updates funktionieren alte Configs nicht mehr

**Lösung**:
1. Workspace Manager öffnen
2. Alten Workspace finden
3. 🗑️ Button klicken
4. OK → OK (YES = Config löschen)
5. ✓ Workspace entfernt, Config gelöscht, Medien safe
6. Optional: Workspace neu anlegen mit frischer Config

---

### Case 2: Workspace temporär deaktivieren

**Situation**: Zu viele Workspaces in der Liste, Config behalten

**Lösung**:
1. 🗑️ Button klicken
2. OK → Cancel (NO = Config behalten)
3. ✓ Workspace aus Liste, aber Config bleibt
4. Später: Workspace wieder hinzufügen

---

### Case 3: Bulk-Cleanup mit Script

**Situation**: Viele Test-Workspaces mit broken Configs

**Lösung**: Cleanup-Script verwenden

```bash
# Dry-run (zeigt nur an)
python cleanup_workspaces.py

# Tatsächlich löschen
python cleanup_workspaces.py --delete
```

**Script-Features**:
- Findet alle invaliden Workspaces
- Zeigt Grund für Invalidität
- Fragt vor Löschung nach
- Batch-Delete mit einem Befehl

---

## Cleanup-Script

### Usage

**Datei**: `cleanup_workspaces.py`

```bash
# 1. Dry-run: Zeigt nur an, was gelöscht würde
python cleanup_workspaces.py

# Output:
# ✓ VALID:   Nepal-2025
# ❌ INVALID: Test-Workspace
#            Reason: config.yaml not found
#
# Invalid workspaces: 5

# 2. Tatsächlich löschen
python cleanup_workspaces.py --delete

# Confirmation:
# Type 'DELETE' to confirm: DELETE
#
# ✓ Removed: Test-Workspace
# ✓ Removed: Debug-1
# ...
```

---

### Script-Checks

Das Script prüft:
1. ✅ Workspace-Pfad existiert?
2. ✅ `config.yaml` existiert?
3. ✅ `config.yaml` ist valide (ladbares YAML)?

**Invalide Gründe**:
- Pfad existiert nicht
- `config.yaml` fehlt
- `config.yaml` ist korrupt
- Schema-Fehler im Config

---

## GUI Workflow

### Einzelnen Workspace löschen

```
1. Workspace Manager Tab öffnen
   
2. Workspace-Karte finden
   ┌─────────────────────────────┐
   │ Test-Workspace              │
   │ C:\Test                     │
   │ [Switch] [🗑️]               │
   └─────────────────────────────┘

3. 🗑️ Button klicken
   
4. Dialog 1: "Remove Workspace?"
   → [OK]
   
5. Dialog 2: "Delete config.yaml?"
   → [OK = YES] oder [Cancel = NO]
   
6. ✓ "Workspace removed and config deleted"
```

---

## Testing

### Test 1: Config behalten

```bash
1. Workspace erstellen
2. Verify: config.yaml existiert
3. Workspace löschen (NO bei Config-Frage)
4. Check Registry: Workspace weg ✓
5. Check Filesystem: config.yaml da ✓
6. Check Media: Alle Files da ✓
```

---

### Test 2: Config löschen

```bash
1. Workspace erstellen
2. Verify: config.yaml existiert
3. Workspace löschen (YES bei Config-Frage)
4. Check Registry: Workspace weg ✓
5. Check Filesystem: config.yaml weg ✓
6. Check Media: Alle Files da ✓
```

---

### Test 3: Aktiver Workspace

```bash
1. Workspace aktivieren
2. 🗑️ Button klicken
3. Alert: "Cannot delete the currently active workspace" ✓
4. Button ist disabled (grau) ✓
```

---

### Test 4: Cleanup-Script

```bash
# Erstelle Test-Workspaces
1. Workspace mit fehlendem config.yaml
2. Workspace mit invalider config.yaml
3. Workspace mit nicht-existentem Pfad

# Run script
python cleanup_workspaces.py

# Verify output:
# ❌ INVALID: Test-1 (config.yaml not found)
# ❌ INVALID: Test-2 (Invalid config: ...)
# ❌ INVALID: Test-3 (Path does not exist)
# Invalid workspaces: 3

# Delete
python cleanup_workspaces.py --delete
# Type 'DELETE' to confirm: DELETE
# ✓ Removed: Test-1
# ✓ Removed: Test-2
# ✓ Removed: Test-3
```

---

## Logging

Alle Aktionen werden geloggt:

```
INFO - Removed workspace from registry: C:\Photos\Nepal-2025
INFO - Deleted config file: C:\Photos\Nepal-2025\config.yaml
```

**Log-Locations**:
- Terminal (stdout)
- `photo_tool.log` (falls konfiguriert)

---

## Dateien

### Neu erstellt:
- `cleanup_workspaces.py` - Cleanup-Script
- `WORKSPACE_CLEANUP_GUIDE.md` - Ausführliche Dokumentation
- `FEATURE_WORKSPACE_DELETE.md` - Dieses Dokument

### Geändert:
- `photo_tool/workspace/manager.py` - `remove_workspace()` erweitert
- `gui_poc/server.py` - DELETE endpoint erweitert
- `gui_poc/static/index.html` - 🗑️ Button + Dialoge

---

## API Changes

### DELETE /api/workspaces/<path>

**Vorher**:
```python
# Nur aus Registry entfernen, keine Parameter
workspace_manager.remove_workspace(workspace_path)
```

**Nachher**:
```python
# Mit delete_config Parameter
data = request.get_json()
delete_config = data.get('delete_config', False)
workspace_manager.remove_workspace(workspace_path, delete_config=delete_config)
```

**Breaking Changes**: ❌ Keine (backward-kompatibel)

---

## Best Practices

### 1. Vor dem Löschen: Backup!

```powershell
# Backup Config
xcopy /E /I "$env:USERPROFILE\.photo_tool" "D:\Backup\phototool"
```

---

### 2. Cleanup regelmäßig durchführen

- Nach größeren Updates
- Monatlich Test-Workspaces löschen
- Registry klein halten (< 20 Workspaces)

---

### 3. Script für Bulk-Operations

- Für >5 Workspaces: Script verwenden
- Für einzelne: GUI Button

---

## Zukünftige Erweiterungen

Mögliche Features:

1. **Workspace archivieren** (disabled, aber nicht gelöscht)
2. **Undo-Funktion** (Trash statt Delete)
3. **Config-Migration** (alte → neue Schemas)
4. **Bulk-Select** (mehrere auf einmal löschen)
5. **Export/Import** (Workspace backup/restore)

---

## User Feedback

> "wie kann man workspaces entfernen? und deren configs löschen?"

✅ **Gelöst durch**:
- 🗑️ Delete-Button in jeder Workspace-Karte
- 2-Stufen-Dialog mit Config-Lösch-Option
- Cleanup-Script für Bulk-Operations
- Klare Trennung: Registry vs. Config vs. Medien

> "alte und inkompatible configs vorhanden sind"

✅ **Gelöst durch**:
- `cleanup_workspaces.py` findet invalide Configs
- Batch-Delete mit einem Befehl
- Config-Validation im Script
- Medien bleiben immer sicher

---

## Zusammenfassung

**Was ist neu:**
- ✅ 🗑️ Delete-Button für jeden Workspace
- ✅ 2-Stufen-Bestätigung mit Config-Option
- ✅ `cleanup_workspaces.py` Script
- ✅ Aktiver Workspace geschützt
- ✅ Medien NIEMALS gelöscht

**Impact:**
- ✅ Alte Configs können aufgeräumt werden
- ✅ Registry bleibt sauber
- ✅ Keine Angst vor versehentlichem Datenverlust
- ✅ Bulk-Operations möglich

**Testing:**
- ✅ GUI: Server neu starten und testen
- ✅ Script: `python cleanup_workspaces.py` ausführen
