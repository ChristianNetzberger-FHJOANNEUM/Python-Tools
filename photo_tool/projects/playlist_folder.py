"""
Project playlist folder: audio files under <project_dir>/playlist/ with stable track IDs.

- Optional playlist_order.yaml (YAML is master): only listed filenames are active; others ignored.
- If no YAML: all audio files, alphabetical order (case-insensitive).
- Per-track ID in playlist/.ids/<filename>.json → {"track_id": "uuid", "filename": "..."}
- Sparse cues in playlist/audio_cues.yaml → cues: [{at_slide: int, track_id: str}, ...]
"""

from __future__ import annotations

import json
import re
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

# Reserved names inside playlist root (never treated as audio)
_RESERVED = frozenset(
    {
        ORDER_YAML.lower(),
        CUES_YAML.lower(),
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


def build_folder_playlist_state(project_dir: Path) -> Dict[str, Any]:
    """Single payload for API: tracks, order_mode, has_order_yaml, cues."""
    pd = Path(project_dir)
    tracks, mode = resolve_ordered_tracks(pd)
    has_yaml = order_yaml_path(pd).exists()
    cues = load_cues(pd)
    return {
        "tracks": tracks,
        "order_mode": mode,
        "has_order_yaml": has_yaml,
        "cues": cues,
    }
