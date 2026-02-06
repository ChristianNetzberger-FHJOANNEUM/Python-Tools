# Bugfix: Sidecar File Counting

## Datum: 2026-02-06

---

## Problem

User berichtete, dass im "Show Config" Modal **0 Sidecars** angezeigt wurden, obwohl:
- Media Manager zeigte: **234 Photos** in `101_PANA` (✓ SCANNED)
- Media Manager zeigte: **76 Photos** in `test` (✓ SCANNED)

**User Feedback**:
> "There are no sidecar files reported: Sidecar Files (.phototool.json) E:\Lumix-2026-01\101_PANA 0 sidecars ... however, the media manager shows two folders, that have been scanned"

---

## Root Cause

### Naming Convention Mismatch

**Backend suchte nach**: `.*.phototool.json` (mit führendem Punkt)

```python
# gui_poc/server.py - count_sidecars()
return len(list(path.rglob('.*.phototool.json')))  # ❌ Findet nichts!
```

**Tatsächliches Naming**: `FILENAME.JPG.phototool.json` (ohne führenden Punkt)

```
E:\Lumix-2026-01\test\
├── P1012410.JPG
├── P1012410.JPG.phototool.json  ✓ Existiert!
├── P1012411.JPG
├── P1012411.JPG.phototool.json  ✓ Existiert!
└── ...
```

### Warum dieser Unterschied?

**SidecarManager erstellt**:
```python
# photo_tool/prescan/sidecar.py
self.sidecar_path = Path(str(photo_path) + self.SIDECAR_SUFFIX)
```

Für `photo_path = "E:\Lumix-2026-01\test\P1012410.JPG"`:
```
str(photo_path) + ".phototool.json"
= "E:\Lumix-2026-01\test\P1012410.JPG.phototool.json"
```

**Config Guide beschrieb** (ursprünglich fälschlicherweise):
```
.P1012410.phototool.json  # Mit führendem Punkt, ohne .JPG
```

---

## Fix

### 1. Backend: Count-Funktion angepasst

**Datei**: `gui_poc/server.py`

```python
# Count sidecar files
def count_sidecars(folder_path: str) -> int:
    try:
        path = Path(folder_path)
        if not path.exists():
            return 0
        # Match both naming conventions:
        # - New: .PHOTONAME.phototool.json (with leading dot)
        # - Current: PHOTONAME.JPG.phototool.json (no leading dot)
        sidecars = list(path.rglob('*.phototool.json'))  # ✓ Findet alle!
        return len(sidecars)
    except:
        return 0
```

**Änderung**:
- **Vorher**: `.*.phototool.json` (nur Files mit führendem Punkt)
- **Nachher**: `*.phototool.json` (alle `.phototool.json` Files)

**Grund**: 
- Backward-kompatibel mit existierenden Sidecars
- Funktioniert auch, falls zukünftig Naming geändert wird

---

### 2. Dokumentation aktualisiert

**Datei**: `CONFIG_STORAGE_GUIDE.md`

**Vorher** (falsch):
```
E:\Lumix-2026-01\101_PANA\
├── P1012569.JPG
├── .P1012569.phototool.json  ❌ Existiert nicht!
```

**Nachher** (korrekt):
```
E:\Lumix-2026-01\101_PANA\
├── P1012569.JPG
├── P1012569.JPG.phototool.json  ✓ Existiert!
```

---

## Verification

### Manual Count (PowerShell):
```powershell
# test folder
Get-ChildItem "E:\Lumix-2026-01\test" -File | 
    Where-Object { $_.Name -like "*.phototool.json" } | 
    Measure-Object | 
    Select-Object -ExpandProperty Count
# → 76 ✓

# 101_PANA folder
Get-ChildItem "E:\Lumix-2026-01\101_PANA" -File -Recurse | 
    Where-Object { $_.Name -like "*.phototool.json" } | 
    Measure-Object | 
    Select-Object -ExpandProperty Count
# → 234 ✓
```

### Expected Result After Fix:

**Show Config Modal** sollte jetzt zeigen:
```
Sidecar Files (.phototool.json)

E:\Lumix-2026-01\101_PANA
234 sidecars ✓
Pasang-1
usb

E:\Lumix-2026-01\test
76 sidecars ✓
test folder
usb
```

---

## Testing Instructions

1. **Server NEU STARTEN**:
   ```bash
   # Terminal: Ctrl+C
   python gui_poc/server.py
   ```

2. **Media Manager öffnen**
3. **"📋 Show Config" klicken**
4. **Verifizieren**:
   - ✓ `101_PANA`: 234 sidecars (statt 0)
   - ✓ `test`: 76 sidecars (statt 0)

---

## Technical Details

### Sidecar Naming Convention

Das aktuelle System verwendet:
```
<ORIGINAL_FILENAME><SIDECAR_SUFFIX>
```

**Beispiel**:
- Photo: `P1012569.JPG`
- Sidecar: `P1012569.JPG.phototool.json`

**Vorteile**:
- ✓ Einfach zu implementieren (String concatenation)
- ✓ Sichtbar im Explorer (kein Hidden-File)
- ✓ Sort Order: Sidecar direkt nach Photo

**Alternative** (hidden file):
```python
self.sidecar_path = photo_path.parent / f".{photo_path.stem}.phototool.json"
```
- Photo: `P1012569.JPG`
- Sidecar: `.P1012569.phototool.json`

**Nachteile der Alternative**:
- ❌ Hidden file (schwerer zu sehen)
- ❌ Komplexer zu implementieren
- ❌ Müsste alle existierenden Sidecars umbenennen

**Entscheidung**: Aktuelles Naming beibehalten (KISS-Prinzip)

---

## Impact

### Vor dem Fix:
- ❌ "Show Config" zeigte 0 Sidecars
- ❌ User dachte, Scan hätte nicht funktioniert
- ❌ Verwirrung über Speicherorte

### Nach dem Fix:
- ✓ Korrekte Sidecar-Counts angezeigt
- ✓ User sieht Scan-Erfolg bestätigt
- ✓ Transparenz über gespeicherte Daten
- ✓ Dokumentation stimmt mit Realität überein

---

## Lessons Learned

1. **Test with real data**: Mock data führte zu falschen Annahmen über Naming
2. **Verify documentation**: Guide beschrieb Naming, das nicht implementiert war
3. **Glob patterns**: `.*.json` != `*.json` - Wichtiger Unterschied!
4. **Backward compatibility**: Besser Pattern anpassen als Files umbenennen

---

## Related Files

- `gui_poc/server.py` - `count_sidecars()` Funktion
- `photo_tool/prescan/sidecar.py` - `SidecarManager.__init__()`
- `CONFIG_STORAGE_GUIDE.md` - Dokumentation
- `BUGFIX_SIDECAR_COUNTING.md` - Dieses Dokument
