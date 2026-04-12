"""
Project playlist folder: audio files under <project_dir>/playlist/ with stable track IDs.

- Optional playlist_order.yaml (YAML is master): only listed filenames are active; others ignored.
- If no YAML: all audio files, alphabetical order (case-insensitive).
- Per-track ID in playlist/.ids/<filename>.json → {"track_id": "uuid", "filename": "..."}
- Sparse cues in playlist/audio_cues.yaml → cues: [{at_slide: int, track_id: str}, ...] (at_slide = switch to this track from that slide until the next cue or end of track)
- Light cues in playlist/light_cues.yaml → cues: [{at_slide: int, effect_id: str}, ...] (one effect per slide)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from ..audio.access import AUDIO_EXTENSIONS
from ..util.logging import get_logger

logger = get_logger("playlist_folder")

PLAYLIST_SUBDIR = "playlist"
IDS_SUBDIR = ".ids"
ORDER_YAML = "playlist_order.yaml"
CUES_YAML = "audio_cues.yaml"
LIGHT_CUES_YAML = "light_cues.yaml"

# Reserved names inside playlist root (never treated as audio)
_RESERVED = frozenset(
    {
        ORDER_YAML.lower(),
        CUES_YAML.lower(),
        LIGHT_CUES_YAML.lower(),
        IDS_SUBDIR.lower(),
    }
)


def playlist_root(project_dir: Path) -> Path:
    return Path(project_dir) / PLAYLIST_SUBDIR


def ids_dir(project_dir: Path) -> Path:
    return playlist_root(project_dir) / IDS_SUBDIR


def order_yaml_path(project_dir: Path) -> Path:
    return playlist_root(project_dir) / ORDER_YAML


def cues_yaml_path(project_dir: Path) -> Path:
    return playlist_root(project_dir) / CUES_YAML


def light_cues_yaml_path(project_dir: Path) -> Path:
    return playlist_root(project_dir) / LIGHT_CUES_YAML


def _is_audio_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS


def _safe_id_filename(name: str) -> str:
    """Sidecar filename for .ids/<safe>.json (basename may contain dots)."""
    if not name or name in (".", ".."):
        return "_invalid"
    # Keep alnum, dot, dash, underscore; collapse unsafe
    safe = re.sub(r"[^A-Za-z0-9._\-]", "_", name)
    return safe or "_file"


def ensure_playlist_structure(project_dir: Path) -> Path:
    """Create playlist/ and .ids/; return playlist root."""
    root = playlist_root(project_dir)
    root.mkdir(parents=True, exist_ok=True)
    ids_dir(project_dir).mkdir(parents=True, exist_ok=True)
    return root


def _load_or_create_track_id(ids_dir_path: Path, filename: str) -> str:
    """Return stable track_id for filename; create sidecar if missing."""
    fn = Path(filename).name
    side = ids_dir_path / f"{_safe_id_filename(fn)}.json"
    if side.exists():
        try:
            with open(side, "r", encoding="utf-8") as f:
                data = json.load(f)
            tid = data.get("track_id")
            if isinstance(tid, str) and tid.strip():
                return tid.strip()
        except Exception as e:
            logger.warning("bad id sidecar %s: %s", side, e)
    tid = str(uuid.uuid4())
    data = {"track_id": tid, "filename": fn}
    try:
        with open(side, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except OSError as e:
        logger.error("write id sidecar %s: %s", side, e)
    return tid


def _list_audio_files_flat(playlist_dir: Path) -> List[Path]:
    """Top-level audio files only; skip reserved / hidden."""
    if not playlist_dir.is_dir():
        return []
    out: List[Path] = []
    for p in playlist_dir.iterdir():
        if p.name.startswith("."):
            continue
        if not _is_audio_file(p):
            continue
        if p.name.lower() in _RESERVED:
            continue
        out.append(p)
    return sorted(out, key=lambda x: x.name.lower())


def _load_order_yaml(path: Path) -> Optional[List[str]]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except Exception as e:
        logger.warning("playlist_order.yaml read failed: %s", e)
        return None
    if not isinstance(raw, dict):
        return None
    order = raw.get("order")
    if not isinstance(order, list):
        return None
    names: List[str] = []
    for x in order:
        if isinstance(x, str) and x.strip():
            names.append(Path(x.strip()).name)
    return names


def resolve_ordered_tracks(project_dir: Path) -> Tuple[List[Dict[str, Any]], str]:
    """
    Build ordered track list for UI/export.

    Returns (tracks, order_mode) where order_mode is 'yaml' or 'alpha'.
    Each track: { track_id, filename, path (absolute str), order }
    """
    pd = Path(project_dir)
    root = ensure_playlist_structure(pd)
    iddir = ids_dir(pd)
    files_by_name = {p.name: p for p in _list_audio_files_flat(root)}
    order_path = order_yaml_path(pd)
    yaml_order = _load_order_yaml(order_path)

    tracks: List[Dict[str, Any]] = []
    if yaml_order is not None:
        # YAML is master: only names that exist on disk
        for i, name in enumerate(yaml_order):
            p = files_by_name.get(name)
            if p is None:
                continue
            tid = _load_or_create_track_id(iddir, name)
            tracks.append(
                {
                    "track_id": tid,
                    "filename": name,
                    "path": str(p.resolve()),
                    "order": i,
                }
            )
        return tracks, "yaml"

    # No YAML (or empty): all files, alphabetical
    for i, p in enumerate(sorted(files_by_name.values(), key=lambda x: x.name.lower())):
        name = p.name
        tid = _load_or_create_track_id(iddir, name)
        tracks.append(
            {
                "track_id": tid,
                "filename": name,
                "path": str(p.resolve()),
                "order": i,
            }
        )
    return tracks, "alpha"


def load_cues(project_dir: Path) -> List[Dict[str, Any]]:
    """Sparse cues: sorted by at_slide."""
    path = cues_yaml_path(Path(project_dir))
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except Exception as e:
        logger.warning("audio_cues.yaml read failed: %s", e)
        return []
    if not isinstance(raw, dict):
        return []
    cues = raw.get("cues")
    if not isinstance(cues, list):
        return []
    out: List[Dict[str, Any]] = []
    for c in cues:
        if not isinstance(c, dict):
            continue
        at = c.get("at_slide")
        tid = c.get("track_id")
        try:
            at_i = int(at)
        except (TypeError, ValueError):
            continue
        if not isinstance(tid, str) or not tid.strip():
            continue
        out.append({"at_slide": at_i, "track_id": tid.strip()})
    out.sort(key=lambda x: x["at_slide"])
    return out


def save_cues(project_dir: Path, cues: List[Dict[str, Any]]) -> None:
    """Replace audio_cues.yaml with normalized sparse cues."""
    pd = Path(project_dir)
    ensure_playlist_structure(pd)
    path = cues_yaml_path(pd)
    norm: List[Dict[str, Any]] = []
    seen: set = set()
    for c in cues:
        if not isinstance(c, dict):
            continue
        try:
            at_i = int(c.get("at_slide"))
        except (TypeError, ValueError):
            continue
        tid = c.get("track_id")
        if not isinstance(tid, str) or not tid.strip():
            continue
        tid = tid.strip()
        key = (at_i, tid)
        if key in seen:
            continue
        seen.add(key)
        norm.append({"at_slide": at_i, "track_id": tid})
    norm.sort(key=lambda x: (x["at_slide"], x["track_id"]))
    body = {"cues": norm}
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(body, f, default_flow_style=False, allow_unicode=True)


def save_order_yaml(project_dir: Path, filenames: List[str]) -> None:
    """Write playlist_order.yaml (YAML becomes master)."""
    pd = Path(project_dir)
    ensure_playlist_structure(pd)
    path = order_yaml_path(pd)
    clean = [Path(str(x)).name for x in filenames if x and isinstance(x, str)]
    body = {"order": clean}
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(body, f, default_flow_style=False, allow_unicode=True)


def delete_order_yaml(project_dir: Path) -> None:
    """Remove playlist_order.yaml → fall back to alphabetical."""
    p = order_yaml_path(Path(project_dir))
    try:
        if p.exists():
            p.unlink()
    except OSError as e:
        logger.warning("delete %s: %s", p, e)


def append_filename_to_order_yaml_if_present(project_dir: Path, filename: str) -> None:
    """If playlist_order.yaml exists, append filename so new uploads stay visible (YAML master)."""
    path = order_yaml_path(Path(project_dir))
    if not path.exists():
        return
    fn = Path(filename).name
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        logger.warning("append_filename_to_order_yaml: read %s", e)
        return
    order = raw.get("order")
    if not isinstance(order, list):
        return
    names = {Path(str(x)).name for x in order if isinstance(x, str) and str(x).strip()}
    if fn in names:
        return
    order.append(fn)
    save_order_yaml(project_dir, order)


def remove_filename_from_order_yaml(project_dir: Path, filename: str) -> None:
    path = order_yaml_path(Path(project_dir))
    if not path.exists():
        return
    fn = Path(filename).name
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return
    order = raw.get("order")
    if not isinstance(order, list):
        return
    new_order = [x for x in order if isinstance(x, str) and Path(x.strip()).name != fn]
    save_order_yaml(project_dir, new_order)


def try_convert_wma_to_mp3(path: Path) -> Tuple[Path, Optional[str]]:
    """
    If path is .wma, convert to .mp3 with ffmpeg and remove the .wma.
    Returns (final_path, error_message_or_none).
    """
    if path.suffix.lower() != ".wma":
        return path, None
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return path, (
            "ffmpeg wurde nicht gefunden — bitte ffmpeg installieren, um .wma nach .mp3 zu konvertieren, "
            "oder die Datei lokal nach .mp3 wandeln."
        )
    out = path.with_suffix(".mp3")
    if out.exists():
        try:
            if out.resolve() != path.resolve():
                return path, f"Zieldatei existiert bereits: {out.name}"
        except OSError:
            return path, f"Zieldatei existiert bereits: {out.name}"
    try:
        proc = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(path),
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "2",
                str(out),
            ],
            capture_output=True,
            timeout=600,
            check=False,
        )
        if proc.returncode != 0:
            err = (proc.stderr or b"").decode("utf-8", errors="replace")[-400:]
            return path, f"ffmpeg Fehler (Code {proc.returncode}): {err}"
    except subprocess.TimeoutExpired:
        return path, "ffmpeg: Timeout bei der Konvertierung."
    except OSError as e:
        return path, f"ffmpeg: {e}"
    try:
        path.unlink()
    except OSError as e:
        logger.warning("remove wma after convert: %s", e)
    return out, None


def delete_playlist_track_file(project_dir: Path, filename: str) -> Optional[str]:
    """
    Remove audio file, sidecar, trim order yaml, remove audio cues referencing this track_id.
    Returns error string or None on success.
    """
    pd = Path(project_dir)
    fn = Path(filename).name
    root = playlist_root(pd)
    fp = root / fn
    iddir = ids_dir(pd)
    track_id: Optional[str] = None
    side = iddir / f"{_safe_id_filename(fn)}.json"
    if side.exists():
        try:
            with open(side, "r", encoding="utf-8") as f:
                track_id = json.load(f).get("track_id")
            side.unlink()
        except OSError as e:
            logger.warning("delete sidecar %s: %s", side, e)
        except json.JSONDecodeError:
            try:
                side.unlink()
            except OSError:
                pass
    if fp.is_file():
        try:
            fp.unlink()
        except OSError as e:
            return f"Datei konnte nicht gelöscht werden: {e}"
    remove_filename_from_order_yaml(pd, fn)
    if track_id and isinstance(track_id, str) and track_id.strip():
        tid = track_id.strip()
        cues = load_cues(pd)
        cues = [c for c in cues if c.get("track_id") != tid]
        save_cues(pd, cues)
    return None


def resolve_track_path_by_id(project_dir: Path, track_id: str) -> Optional[Path]:
    """Find absolute path for a track_id by scanning .ids sidecars."""
    if not track_id or not isinstance(track_id, str):
        return None
    tid = track_id.strip()
    iddir = ids_dir(Path(project_dir))
    if not iddir.is_dir():
        return None
    for side in iddir.glob("*.json"):
        try:
            with open(side, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("track_id") == tid:
                fn = data.get("filename")
                if not isinstance(fn, str) or not fn.strip():
                    continue
                p = playlist_root(Path(project_dir)) / Path(fn).name
                if p.is_file():
                    return p.resolve()
        except Exception:
            continue
    return None


def load_light_cues(project_dir: Path) -> List[Dict[str, Any]]:
    """Sparse light cues; one effect_id per at_slide (last wins)."""
    path = light_cues_yaml_path(Path(project_dir))
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except Exception as e:
        logger.warning("light_cues.yaml read failed: %s", e)
        return []
    if not isinstance(raw, dict):
        return []
    cues = raw.get("cues")
    if not isinstance(cues, list):
        return []
    by_slide: Dict[int, Dict[str, Any]] = {}
    for c in cues:
        if not isinstance(c, dict):
            continue
        at = c.get("at_slide")
        eid = c.get("effect_id")
        try:
            at_i = int(at)
        except (TypeError, ValueError):
            continue
        if not isinstance(eid, str) or not eid.strip():
            continue
        by_slide[at_i] = {"at_slide": at_i, "effect_id": eid.strip()}
    return sorted(by_slide.values(), key=lambda x: x["at_slide"])


def save_light_cues(project_dir: Path, cues: List[Dict[str, Any]]) -> None:
    """Replace light_cues.yaml; one cue per at_slide."""
    pd = Path(project_dir)
    ensure_playlist_structure(pd)
    path = light_cues_yaml_path(pd)
    by_slide: Dict[int, Dict[str, Any]] = {}
    for c in cues:
        if not isinstance(c, dict):
            continue
        try:
            at_i = int(c.get("at_slide"))
        except (TypeError, ValueError):
            continue
        eid = c.get("effect_id")
        if not isinstance(eid, str) or not eid.strip():
            continue
        by_slide[at_i] = {"at_slide": at_i, "effect_id": eid.strip()}
    norm = sorted(by_slide.values(), key=lambda x: x["at_slide"])
    body = {"cues": norm}
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(body, f, default_flow_style=False, allow_unicode=True)


def load_project_photo_order(project_dir: Path) -> Optional[List[str]]:
    """Paths in project slide order from <projects_dir>/<folder_name>.yaml photo_ids."""
    pd = Path(project_dir)
    yml = pd.parent / f"{pd.name}.yaml"
    if not yml.is_file():
        return None
    try:
        with open(yml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        logger.warning("project yaml read failed for cue remap: %s: %s", yml, e)
        return None
    if not isinstance(data, dict):
        return None
    ids = data.get("photo_ids")
    if not isinstance(ids, list) or not ids:
        return None
    out: List[str] = []
    for x in ids:
        if isinstance(x, str) and x.strip():
            out.append(x.strip())
        elif x is not None:
            out.append(str(x).strip())
    return out or None


def _path_match_keys(path_str: str) -> List[str]:
    """Several string forms of the same file (Windows drive/UNC, normcase) for cue remap."""
    raw = str(path_str).strip()
    if not raw:
        return []
    keys: List[str] = [raw]
    try:
        keys.append(str(Path(raw).resolve()))
    except (OSError, ValueError):
        pass
    keys.append(os.path.normcase(os.path.normpath(raw)))
    try:
        keys.append(os.path.normcase(os.path.normpath(str(Path(raw).resolve()))))
    except (OSError, ValueError):
        pass
    out: List[str] = []
    seen = set()
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def build_project_index_to_export_index(
    project_photo_ids: List[str],
    export_photo_paths: List[Path],
) -> Dict[int, int]:
    """Map project slide index (photo_ids order) -> export slide index for this photo_paths list."""

    path_to_proj_index: Dict[str, int] = {}
    for i, pid in enumerate(project_photo_ids):
        for k in _path_match_keys(pid):
            if k not in path_to_proj_index:
                path_to_proj_index[k] = i
    out: Dict[int, int] = {}
    for e_idx, ep in enumerate(export_photo_paths):
        for k in _path_match_keys(str(ep)):
            pi = path_to_proj_index.get(k)
            if pi is not None:
                out[pi] = e_idx
                break
    return out


def filter_cues_for_export(
    project_dir: Path,
    slide_count: int,
    export_photo_paths: Optional[List[Path]] = None,
    canonical_project_photo_paths: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """
    Cues for gallery export: drop orphans (no reassignment). Orphans are:
    - invalid YAML rows (missing fields, bad types),
    - at_slide outside 0..slide_count-1 for this export (after project→export remap),
    - audio: track_id not present in the current project playlist order.

    When export_photo_paths is set and project slide order is known, at_slide in YAML is
    interpreted as **project slide index** (same order as ``projects/<id>.yaml`` photo_ids
    when present, otherwise ``canonical_project_photo_paths`` from the GUI — same order as
    the Media tab / manifest). It is remapped to the export index matching that file in
    export_photo_paths. If the photo is not part of this export (e.g. color filter), the
    cue is dropped with a warning.

    If slide order cannot be determined (no yaml photo_ids and no canonical list),
    at_slide is treated as **export index** (legacy).

    Returns (audio_cues, light_cues, warning_messages) for logging and slides.json.
    """
    warnings: List[str] = []
    pd = Path(project_dir)
    tracks, _ = resolve_ordered_tracks(pd)
    valid_ids = {t["track_id"] for t in tracks}

    yaml_order = load_project_photo_order(pd)
    proj_order = yaml_order
    if (not proj_order) and canonical_project_photo_paths:
        proj_order = [str(p).strip() for p in canonical_project_photo_paths if str(p).strip()]
        logger.info(
            "Cue export: no photo_ids in project yaml — using manifest from client (%d paths) for cue remap",
            len(proj_order),
        )
    proj_to_exp: Optional[Dict[int, int]] = None
    if proj_order and export_photo_paths is not None:
        proj_to_exp = build_project_index_to_export_index(proj_order, export_photo_paths)
        if proj_to_exp:
            logger.info(
                "Cue export: remapping project slides (%d) -> export order (%d slides)",
                len(proj_order),
                slide_count,
            )
        elif slide_count > 0:
            logger.warning(
                "Cue export: no project photo path matched export paths; "
                "treating YAML at_slide as export index (check path strings in project.yaml vs export)"
            )
            proj_to_exp = None

    if slide_count <= 0:
        range_hint = "(no slides in this export)"
    else:
        range_hint = f"0..{slide_count - 1}"

    path_cues = cues_yaml_path(pd)
    raw_audio: List[Any] = []
    if path_cues.exists():
        try:
            with open(path_cues, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            if isinstance(doc, dict):
                cues = doc.get("cues")
                if isinstance(cues, list):
                    raw_audio = cues
        except Exception as e:
            warnings.append(f"audio_cues.yaml read failed: {e}")
            raw_audio = []

    out_audio: List[Dict[str, Any]] = []
    for c in raw_audio:
        if not isinstance(c, dict):
            warnings.append("audio cue row skipped: not an object")
            continue
        at = c.get("at_slide")
        tid = c.get("track_id")
        try:
            at_i = int(at)
        except (TypeError, ValueError):
            warnings.append(f"audio cue dropped: invalid at_slide {at!r}")
            continue
        if not isinstance(tid, str) or not tid.strip():
            warnings.append(f"audio cue dropped: missing track_id (at_slide index was {at_i})")
            continue
        tid = tid.strip()
        proj_at = at_i
        if proj_to_exp is not None:
            if at_i not in proj_to_exp:
                warnings.append(
                    f"audio cue dropped: project slide {proj_at} not in this export (selection/filter), track_id={tid}"
                )
                continue
            at_i = proj_to_exp[at_i]
        if at_i < 0 or at_i >= slide_count:
            warnings.append(
                f"audio cue dropped: at_slide={at_i} out of range for {range_hint}, track_id={tid}"
            )
            continue
        if tid not in valid_ids:
            warnings.append(
                f"audio cue dropped: track_id not in playlist ({tid}) at export slide={at_i}"
            )
            continue
        out_audio.append({"at_slide": at_i, "track_id": tid})
    out_audio.sort(key=lambda x: (x["at_slide"], x["track_id"]))

    path_light = light_cues_yaml_path(pd)
    raw_light: List[Any] = []
    if path_light.exists():
        try:
            with open(path_light, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            if isinstance(doc, dict):
                cues = doc.get("cues")
                if isinstance(cues, list):
                    raw_light = cues
        except Exception as e:
            warnings.append(f"light_cues.yaml read failed: {e}")
            raw_light = []

    by_slide: Dict[int, Dict[str, Any]] = {}
    for c in raw_light:
        if not isinstance(c, dict):
            warnings.append("light cue row skipped: not an object")
            continue
        at = c.get("at_slide")
        eid = c.get("effect_id")
        try:
            at_i = int(at)
        except (TypeError, ValueError):
            warnings.append(f"light cue dropped: invalid at_slide {at!r}")
            continue
        if not isinstance(eid, str) or not eid.strip():
            warnings.append(f"light cue dropped: missing effect_id (at_slide index was {at_i})")
            continue
        eid = eid.strip()
        proj_at = at_i
        if proj_to_exp is not None:
            if at_i not in proj_to_exp:
                warnings.append(
                    f"light cue dropped: project slide {proj_at} not in this export (selection/filter), effect_id={eid}"
                )
                continue
            at_i = proj_to_exp[at_i]
        if at_i < 0 or at_i >= slide_count:
            warnings.append(
                f"light cue dropped: at_slide={at_i} out of range for {range_hint}, effect_id={eid}"
            )
            continue
        by_slide[at_i] = {"at_slide": at_i, "effect_id": eid}
    out_light = sorted(by_slide.values(), key=lambda x: x["at_slide"])

    return out_audio, out_light, warnings


# Relative to gallery index.html (same folder name as project playlist/ but independent tree)
GALLERY_EXPORT_PLAYLIST_SUBDIR = "playlist"


def export_playlist_to_gallery(
    project_dir: Path,
    gallery_dir: Path,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Copy every track from the project playlist into gallery_dir/GALLERY_EXPORT_PLAYLIST_SUBDIR/
    as <track_id><original ext> so exports are stable and cue track_ids resolve.

    Returns (playlist_tracks for slides.json / slideshow embed, warnings).
    """
    warnings: List[str] = []
    pd = Path(project_dir)
    dest_root = Path(gallery_dir) / GALLERY_EXPORT_PLAYLIST_SUBDIR
    if dest_root.exists():
        shutil.rmtree(dest_root, ignore_errors=True)
    dest_root.mkdir(parents=True, exist_ok=True)

    tracks, _ = resolve_ordered_tracks(pd)
    out: List[Dict[str, Any]] = []
    for t in tracks:
        src = Path(str(t.get("path", "")))
        tid = t.get("track_id")
        if not src.is_file() or not isinstance(tid, str) or not tid.strip():
            warnings.append(f"playlist export skip: invalid track row {t!r}")
            continue
        tid = tid.strip()
        ext = src.suffix.lower() if src.suffix else ".mp3"
        dest_name = f"{tid}{ext}"
        dest = dest_root / dest_name
        try:
            shutil.copy2(src, dest)
        except OSError as e:
            warnings.append(f"playlist copy failed {src.name}: {e}")
            continue
        fn = t.get("filename")
        if not isinstance(fn, str) or not fn.strip():
            fn = src.name
        rel = f"{GALLERY_EXPORT_PLAYLIST_SUBDIR}/{dest_name}"
        out.append({"track_id": tid, "src": rel, "filename": fn})

    return out, warnings


def filter_audio_cues_to_exported_tracks(
    audio_cues: List[Dict[str, Any]],
    playlist_tracks: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Keep only cues whose track_id appears in playlist_tracks (files actually copied to gallery).
    Logs dropped cues as warning strings for export log / manifest follow-up.
    """
    exported_ids = {
        str(t.get("track_id", "")).strip()
        for t in playlist_tracks
        if isinstance(t.get("track_id"), str) and str(t.get("track_id", "")).strip()
    }
    out: List[Dict[str, Any]] = []
    dropped: List[str] = []
    for c in audio_cues:
        if not isinstance(c, dict):
            continue
        tid = c.get("track_id")
        if not isinstance(tid, str) or not tid.strip():
            continue
        tid = tid.strip()
        if tid in exported_ids:
            out.append(c)
        else:
            at = c.get("at_slide")
            dropped.append(
                f"audio cue dropped (track not in gallery export): at_slide={at}, track_id={tid}"
            )
    return out, dropped


def build_folder_playlist_state(project_dir: Path) -> Dict[str, Any]:
    """Single payload for API: tracks, order_mode, has_order_yaml, audio + light cues."""
    pd = Path(project_dir)
    tracks, mode = resolve_ordered_tracks(pd)
    has_yaml = order_yaml_path(pd).exists()
    cues = load_cues(pd)
    light_cues = load_light_cues(pd)
    return {
        "tracks": tracks,
        "order_mode": mode,
        "has_order_yaml": has_yaml,
        "cues": cues,
        "light_cues": light_cues,
    }
