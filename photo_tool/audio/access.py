"""
Workspace-scoped audio paths: roots from enabled workspace folders, browse, playlist validation.
"""

from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..config import load_config
from ..util.logging import get_logger
from ..workspace import Workspace

logger = get_logger("audio_access")

AUDIO_EXTENSIONS = frozenset(
    {
        ".wav",
        ".mp3",
        ".flac",
        ".ogg",
        ".m4a",
        ".aac",
        ".opus",
        ".wma",
        ".aiff",
        ".aif",
    }
)


def _canonical(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path


def match_audio_root(root_str: str, roots: List[Path]) -> Optional[Path]:
    """Return canonical path if root_str matches one of the allowed workspace roots."""
    if not root_str or not isinstance(root_str, str):
        return None
    try:
        r = _canonical(Path(root_str))
    except Exception:
        return None
    for a in roots:
        if _canonical(a) == r:
            return r
    return None


def audio_roots_for_workspace(workspace_path: Path) -> List[Path]:
    """Enabled workspace folders — used as allowed audio library roots (MVP)."""
    ws = Workspace(workspace_path)
    config = load_config(ws.config_file)
    roots: List[Path] = []
    if not config.folders:
        return roots
    for folder in config.folders:
        if not folder.get("enabled", True):
            continue
        raw = folder.get("path")
        if not raw:
            continue
        try:
            roots.append(_canonical(Path(str(raw))))
        except OSError as e:
            logger.warning("audio root skip %s: %s", raw, e)
    return roots


def path_under_roots(candidate: Path, roots: List[Path]) -> bool:
    c = _canonical(candidate)
    for root in roots:
        r = _canonical(root)
        try:
            if c.is_relative_to(r):
                return True
        except ValueError:
            continue
    return False


def resolve_path_under_audio_roots(
    path_str: str, roots: List[Path]
) -> Tuple[Optional[Path], Optional[str]]:
    """
    Resolve path_str to a real file path if it exists and lies under roots.
    Returns (path, None) or (None, error_message).
    """
    if not path_str or not isinstance(path_str, str):
        return None, "invalid path"
    try:
        p = Path(path_str)
        rp = _canonical(p)
    except Exception:
        return None, "invalid path"
    if not path_under_roots(rp, roots):
        return None, "path not under allowed audio roots"
    if not rp.is_file():
        return None, "not a file"
    suffix = rp.suffix.lower()
    if suffix not in AUDIO_EXTENSIONS:
        return None, f"unsupported audio type {suffix!r}"
    return rp, None


def resolve_dir_under_audio_roots(
    path_str: str, roots: List[Path]
) -> Tuple[Optional[Path], Optional[str]]:
    """Resolve directory under roots (for browse)."""
    if not path_str or not isinstance(path_str, str):
        return None, "invalid path"
    try:
        p = Path(path_str)
        rp = _canonical(p)
    except Exception:
        return None, "invalid path"
    if not path_under_roots(rp, roots):
        return None, "path not under allowed audio roots"
    if not rp.is_dir():
        return None, "not a directory"
    return rp, None


def list_audio_directory(
    dir_path: Path,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Non-recursive listing: subdirs + audio files with size."""
    directories: List[Dict[str, Any]] = []
    files: List[Dict[str, Any]] = []
    try:
        for item in sorted(dir_path.iterdir(), key=lambda x: x.name.lower()):
            try:
                if item.is_dir():
                    directories.append(
                        {
                            "name": item.name,
                            "path": str(item),
                        }
                    )
                elif item.is_file():
                    suf = item.suffix.lower()
                    if suf in AUDIO_EXTENSIONS:
                        try:
                            size_b = item.stat().st_size
                        except OSError:
                            size_b = 0
                        files.append(
                            {
                                "name": item.name,
                                "path": str(item),
                                "size_bytes": size_b,
                                "ext": suf,
                            }
                        )
            except (OSError, PermissionError):
                continue
    except (OSError, PermissionError) as e:
        logger.warning("list_audio_directory: %s", e)
    return directories, files


def guess_mimetype(file_path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(file_path))
    if mime and mime.startswith("audio/"):
        return mime
    ext = file_path.suffix.lower()
    fallback = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".opus": "audio/opus",
        ".wma": "audio/x-ms-wma",
        ".aiff": "audio/aiff",
        ".aif": "audio/aiff",
    }
    return fallback.get(ext, "application/octet-stream")


def validate_playlist_paths(
    tracks: List[Dict[str, Any]], roots: List[Path]
) -> Optional[str]:
    """Return error message if any track source_path is invalid."""
    for i, t in enumerate(tracks):
        if not isinstance(t, dict):
            return f"track {i} is not an object"
        sp = t.get("source_path")
        if not sp:
            return f"track {i} missing source_path"
        _, err = resolve_path_under_audio_roots(str(sp), roots)
        if err:
            return f"track {i}: {err}"
    return None


def normalize_playlist_from_request(
    body: Optional[Dict[str, Any]], roots: List[Path]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate and return {tracks, default_track_id} or (None, error).
    Assigns id/order where missing.
    """
    if body is None:
        return None, "missing body"
    if not isinstance(body, dict):
        return None, "body must be an object"
    tracks_raw = body.get("tracks")
    if tracks_raw is None:
        tracks_raw = []
    if not isinstance(tracks_raw, list):
        return None, "tracks must be a list"
    tracks: List[Dict[str, Any]] = []
    for i, t in enumerate(tracks_raw):
        if not isinstance(t, dict):
            return None, f"tracks[{i}] must be an object"
        sp = t.get("source_path")
        if not sp:
            return None, f"tracks[{i}] needs source_path"
        rp, err = resolve_path_under_audio_roots(str(sp), roots)
        if err or rp is None:
            return None, f"tracks[{i}]: {err or 'invalid path'}"
        tid = t.get("id")
        if not tid or not isinstance(tid, str):
            tid = str(uuid.uuid4())
        label = t.get("label")
        if label is not None and not isinstance(label, str):
            label = str(label)
        order = t.get("order")
        if order is None:
            order = i
        elif not isinstance(order, int):
            try:
                order = int(order)
            except (TypeError, ValueError):
                order = i
        tracks.append(
            {
                "id": tid,
                "source_path": str(rp),
                "label": label,
                "order": order,
            }
        )
    tracks.sort(key=lambda x: x["order"])
    default_id = body.get("default_track_id")
    if default_id is not None:
        if not isinstance(default_id, str):
            return None, "default_track_id must be a string"
        ids = {tr["id"] for tr in tracks}
        if default_id and default_id not in ids:
            return None, "default_track_id must match a track id"
    out = {
        "tracks": tracks,
        "default_track_id": default_id if default_id else None,
    }
    return out, None


def playlist_from_paths(paths: List[str], roots: List[Path]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Build playlist dict from absolute paths (all must validate)."""
    if not isinstance(paths, list):
        return None, "paths must be a list"
    tracks: List[Dict[str, Any]] = []
    for i, p in enumerate(paths):
        if not p or not isinstance(p, str):
            return None, f"paths[{i}] invalid"
        rp, err = resolve_path_under_audio_roots(p, roots)
        if err:
            return None, f"paths[{i}]: {err}"
        name = rp.name if rp else Path(p).name
        tracks.append(
            {
                "id": str(uuid.uuid4()),
                "source_path": str(rp) if rp else p,
                "label": name,
                "order": i,
            }
        )
    return {"tracks": tracks, "default_track_id": tracks[0]["id"] if tracks else None}, None
