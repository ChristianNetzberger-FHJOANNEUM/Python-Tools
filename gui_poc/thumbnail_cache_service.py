"""
Shared thumbnail cache generation (SQLite paths → workspace/cache/thumbnails).
Used by the GUI API and optionally by generate_thumbnails.py.
"""

from __future__ import annotations

import os
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from photo_tool.util.logging import get_logger

logger = get_logger("thumbnail_cache")


def _path_is_under_root_norm(file_s: str, root_s: str) -> bool:
    c = os.path.normcase(os.path.normpath(file_s))
    rf = os.path.normcase(os.path.normpath(root_s))
    if c == rf:
        return True
    if not c.startswith(rf):
        return False
    if len(c) > len(rf) and c[len(rf)] not in (os.sep, "/"):
        return False
    return True


def _photo_under_enabled_roots(path_str: str, roots: List[Path]) -> bool:
    if not roots:
        return True
    variants = [path_str]
    p = Path(path_str)
    try:
        variants.append(str(p.resolve(strict=False)))
    except (OSError, ValueError, RuntimeError, TypeError):
        pass
    variants = list(dict.fromkeys(variants))
    for r in roots:
        rvars = [str(r)]
        try:
            try:
                rvars.append(str(r.resolve(strict=False)))
            except TypeError:
                rvars.append(str(r.resolve()))
        except (OSError, ValueError, RuntimeError):
            pass
        rvars = list(dict.fromkeys(rvars))
        for c in variants:
            for rv in rvars:
                if _path_is_under_root_norm(c, rv):
                    return True
    return False


def generate_one_thumbnail(
    photo_path: Path,
    workspace_path: Path,
    *,
    force: bool = False,
) -> str:
    """
    Create or skip one JPEG in workspace/cache/thumbnails/<stem>.jpg    Returns status: created | exists | missing | error
    """
    cache_dir = workspace_path / "cache" / "thumbnails"
    cache_dir.mkdir(parents=True, exist_ok=True)
    thumb_path = cache_dir / f"{photo_path.stem}.jpg"
    if thumb_path.exists() and not force:
        return "exists"
    try:
        if not photo_path.is_file():
            return "missing"
    except OSError:
        return "missing"

    try:
        from PIL import Image

        img = Image.open(photo_path)
        try:
            exif = img.getexif()
            if exif:
                orientation = exif.get(0x0112)
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
        except Exception:
            pass
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        img.save(thumb_path, "JPEG", quality=85, optimize=True)
        return "created"
    except Exception as e:
        logger.warning("Thumbnail failed %s: %s", photo_path, e)
        return "error"


def load_photo_paths_from_db(
    db_path: Path,
    *,
    enabled_roots: Optional[List[Path]] = None,
) -> List[str]:
    if not db_path.is_file():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT path FROM media WHERE media_type = 'photo' AND is_available = 1"
    )
    out: List[str] = []
    for row in cur.fetchall():
        p = row["path"]
        if not p:
            continue
        s = str(p).strip()
        if not s:
            continue
        if enabled_roots is not None and not _photo_under_enabled_roots(s, enabled_roots):
            continue
        out.append(s)
    conn.close()
    return out


def run_thumbnail_batch(
    workspace_path: Path,
    db_path: Path,
    *,
    scope: str = "all",
    force: bool = False,
    max_workers: int = 8,
    enabled_roots: Optional[List[Path]] = None,
    progress: Optional[Callable[[int, int, str, Dict[str, int]], None]] = None,
) -> Dict[str, int]:
    """
    scope: 'all' — every photo row in DB; 'enabled' — only paths under enabled_roots.
    progress: optional callback(done, total, last_path, counts) where counts has created/exists/missing/error.
    """
    roots_filter: Optional[List[Path]] = None
    if scope == "enabled":
        roots_filter = enabled_roots or []
    elif scope != "all":
        raise ValueError("scope must be 'all' or 'enabled'")

    paths = load_photo_paths_from_db(db_path, enabled_roots=roots_filter)
    total = len(paths)
    counts = {"created": 0, "exists": 0, "missing": 0, "error": 0}
    if progress:
        progress(0, total, "", dict(counts))
    if total == 0:
        return counts

    def work(path_str: str) -> Tuple[str, str]:
        st = generate_one_thumbnail(Path(path_str), workspace_path, force=force)
        return path_str, st

    done = 0
    with ThreadPoolExecutor(max_workers=max(1, min(max_workers, 16))) as ex:
        futures = {ex.submit(work, p): p for p in paths}
        for fut in as_completed(futures):
            try:
                path_str, st = fut.result()
            except Exception as e:
                logger.warning("thumbnail worker: %s", e)
                st = "error"
                path_str = futures.get(fut, "")
            if st not in counts:
                st = "error"
            counts[st] += 1
            done += 1
            if progress and (done % 25 == 0 or done == total):
                progress(done, total, path_str, dict(counts))

    if progress:
        progress(total, total, "", dict(counts))
    return counts


def workspace_db_path_default() -> Path:
    return Path(__file__).resolve().parent / "db" / "workspace_media.db"
