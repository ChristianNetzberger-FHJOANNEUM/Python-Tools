"""
Per-workspace publish / NAS landing settings and manifest.json merge.
Stored at <workspace>/publish_settings.json (not in git by default).
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def default_publish_settings() -> Dict[str, Any]:
    return {
        "publish_root": "",
        "nas_web_public_base": "",
        "manifest_relative": "manifest.json",
    }


def publish_settings_file(workspace: Path) -> Path:
    return Path(workspace).resolve() / "publish_settings.json"


def load_publish_settings(workspace: Path) -> Dict[str, Any]:
    out = default_publish_settings()
    p = publish_settings_file(workspace)
    if not p.is_file():
        return out
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return out
    if not isinstance(raw, dict):
        return out
    for k in out:
        if k in raw and isinstance(raw[k], str):
            out[k] = raw[k].strip()
    if "manifest_relative" in raw and isinstance(raw["manifest_relative"], str):
        mr = raw["manifest_relative"].strip().replace("\\", "/")
        if mr and not mr.startswith("/") and ".." not in mr:
            out["manifest_relative"] = mr
    return out


def save_publish_settings(workspace: Path, data: Dict[str, Any]) -> None:
    ws = Path(workspace).resolve()
    ws.mkdir(parents=True, exist_ok=True)
    cur = load_publish_settings(ws)
    if "publish_root" in data and isinstance(data["publish_root"], str):
        cur["publish_root"] = data["publish_root"].strip()
    if "nas_web_public_base" in data and isinstance(data["nas_web_public_base"], str):
        cur["nas_web_public_base"] = data["nas_web_public_base"].strip().rstrip("/")
    if "manifest_relative" in data and isinstance(data["manifest_relative"], str):
        mr = data["manifest_relative"].strip().replace("\\", "/")
        if mr and ".." not in mr and not mr.startswith("/"):
            cur["manifest_relative"] = mr
    publish_settings_file(ws).write_text(
        json.dumps(cur, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def validate_slug(slug: str) -> Optional[str]:
    s = (slug or "").strip().lower()
    if not s or not _SLUG_RE.match(s):
        return None
    return s


def manifest_path_for_workspace(workspace: Path) -> Tuple[Path, Dict[str, Any]]:
    cfg = load_publish_settings(workspace)
    root_s = (cfg.get("publish_root") or "").strip()
    if not root_s:
        raise ValueError("publish_root ist leer — unter Einstellungen → Veröffentlichung eintragen.")
    root = Path(root_s).expanduser()
    try:
        root = root.resolve()
    except OSError:
        root = Path(root_s)
    mr = (cfg.get("manifest_relative") or "manifest.json").strip() or "manifest.json"
    parts = Path(mr).parts
    if ".." in parts or Path(mr).is_absolute():
        raise ValueError("manifest_relative muss ein relativer Dateiname/Pfad ohne .. sein.")
    return root / mr, cfg


def load_or_create_manifest(manifest_file: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if manifest_file.is_file():
        try:
            raw = json.loads(manifest_file.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data = raw
        except (OSError, json.JSONDecodeError):
            data = {}
    if not isinstance(data, dict):
        data = {}
    galleries = data.get("galleries")
    if not isinstance(galleries, list):
        galleries = []
    data["version"] = 1
    data["galleries"] = galleries
    return data


def _is_under_parent(child: Path, parent: Path) -> bool:
    try:
        child_r = child.resolve()
        parent_r = parent.resolve()
    except OSError:
        return False
    try:
        child_r.relative_to(parent_r)
        return True
    except ValueError:
        return False


def build_landing_entry(
    *,
    workspace: Path,
    slug: str,
    title: str,
    description: str = "",
    href: Optional[str] = None,
    thumb: Optional[str] = None,
    require_gallery_dir: bool = True,
) -> Dict[str, Any]:
    s = validate_slug(slug)
    if not s:
        raise ValueError("Ungültiger Slug (nur Kleinbuchstaben, Zahlen, Bindestrich).")
    manifest_file, cfg = manifest_path_for_workspace(workspace)
    root = manifest_file.parent
    gallery_dir = (root / s).resolve()
    if require_gallery_dir:
        if not gallery_dir.is_dir():
            raise ValueError(f"Galerie-Ordner fehlt (noch nicht exportiert?): {gallery_dir}")
        if not _is_under_parent(gallery_dir, root):
            raise ValueError("Galerie-Ordner liegt nicht unter publish_root.")

    href_out = (href or "").strip() or f"{s}/"
    if not href_out.endswith("/"):
        href_out += "/"

    thumb_out = (thumb or "").strip()
    if not thumb_out and gallery_dir.is_dir():
        for cand in (
            f"{s}/images/0000.jpg",
            f"{s}/images/0001.jpg",
            f"{s}/images/0000.jpeg",
        ):
            p = root / cand
            try:
                if p.is_file():
                    thumb_out = cand.replace("\\", "/")
                    break
            except OSError:
                continue

    entry = {
        "id": str(uuid.uuid4()),
        "slug": s,
        "title": (title or s).strip() or s,
        "href": href_out,
        "description": (description or "").strip(),
        "thumb": thumb_out or None,
    }
    base = (cfg.get("nas_web_public_base") or "").strip().rstrip("/")
    entry["public_url"] = f"{base}/{href_out}" if base else None
    return entry


def merge_landing_entry_into_manifest(
    workspace: Path,
    entry: Dict[str, Any],
    *,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Upsert gallery entry by slug; write manifest unless dry_run."""
    manifest_file, _ = manifest_path_for_workspace(workspace)
    slug = entry.get("slug")
    if not isinstance(slug, str) or not validate_slug(slug):
        raise ValueError("invalid entry slug")

    data = load_or_create_manifest(manifest_file)
    galleries: List[Dict[str, Any]] = list(data.get("galleries") or [])
    replaced = False
    out_entry = {k: v for k, v in entry.items() if k != "public_url"}
    for i, g in enumerate(galleries):
        if isinstance(g, dict) and g.get("slug") == slug:
            old_id = g.get("id")
            galleries[i] = {**out_entry}
            if old_id:
                galleries[i]["id"] = old_id
            replaced = True
            break
    if not replaced:
        galleries.append({**out_entry})

    data["galleries"] = galleries

    if not dry_run:
        manifest_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = manifest_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(manifest_file)

    return {
        "manifest_path": str(manifest_file),
        "replaced": replaced,
        "galleries_count": len(galleries),
        "entry": entry,
        "dry_run": dry_run,
    }
