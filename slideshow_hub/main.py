"""
Slideshow Remote Hub — WebSocket relay + couch ratings API for LAN / NAS.

Ratings (Couch / Remote) update **slides.json** in the exported gallery folder only
(see SLIDESHUB_GALLERY_PATH_MAP). Original photo sidecars are not modified.
"""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional, Set
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


def _ensure_http_slides_json_url(url: str) -> str:
    """httpx requires http(s); users/TVs sometimes omit the scheme or use //-URLs."""
    u = (url or "").strip()
    if not u:
        return u
    low = u.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return u
    if low.startswith("//"):
        return "http:" + u
    if low.startswith("null/") or low == "null":
        raise HTTPException(
            400,
            "Ungültige Galerie-URL (z. B. Slideshow per file:// geöffnet). "
            "Bitte die Galerie am TV über http(s) von der NAS aufrufen.",
        )
    head = u.split("/", 1)[0]
    if "://" not in head:
        return "http://" + u.lstrip("/")
    raise HTTPException(400, f"Unsupported URL for slides.json (need http(s)): {u[:120]}")


def _resolve_slides_json_fs_path(slides_json_url: str) -> Path:
    raw = os.environ.get("SLIDESHUB_GALLERY_PATH_MAP", "").strip()
    if not raw:
        raise HTTPException(
            503,
            "SLIDESHUB_GALLERY_PATH_MAP env not set. "
            'Example: {"http://192.168.0.100:8080":"/volume1/web"} '
            "mapping gallery HTTP origin to filesystem root on this host.",
        )
    mapping = json.loads(raw)
    if not isinstance(mapping, dict) or not mapping:
        raise HTTPException(500, "SLIDESHUB_GALLERY_PATH_MAP must be a non-empty JSON object")

    parsed = urlparse(slides_json_url.strip())
    if not parsed.scheme or not parsed.netloc:
        raise HTTPException(400, "slides_json_url must be absolute http(s) URL")
    origin = f"{parsed.scheme}://{parsed.netloc}".lower()
    path_parts = [p for p in parsed.path.split("/") if p]

    for prefix, fs_root in mapping.items():
        pre = str(prefix).rstrip("/").lower()
        if pre == origin:
            return Path(str(fs_root)).joinpath(*path_parts).resolve()

    raise HTTPException(
        400,
        f"No SLIDESHUB_GALLERY_PATH_MAP entry for origin {origin}. Keys must be http(s)://host:port",
    )


def _slides_json_disk_missing_help(fs_path: Path) -> str:
    """Explain why Path.is_file() may fail though DSM File Station shows the file."""
    parts = [
        "URL→Pfad-Mapping stimmt vermutlich, aber der Hub-Prozess sieht diese Datei nicht."
    ]
    if Path("/.dockerenv").is_file():
        parts.append(
            "Hub in Docker: Host-Ordner als Volume mounten, z. B. "
            "`-v /volume1/web:/volume1/web` oder in Synology Container Manager dieselbe Freigabe zu "
            "einem Container-Pfad binden; SLIDESHUB_GALLERY_PATH_MAP muss genau diesen Zielpfad im Container nutzen "
            "(Beispiel Map-Wert `/data/web`, wenn `-v /volume1/web:/data/web`)."
        )
    try:
        parent_ok = fs_path.parent.is_dir()
    except OSError:
        parent_ok = False
    if not parent_ok:
        parts.append(f"Elternordner im Hub nicht erreichbar: {fs_path.parent}")
    elif not fs_path.exists():
        parts.append(
            "Ordner da, Datei nicht — Groß/Kleinschreibung oder anderer Ordner als im Web (doppeltes /web im URL-Pfad) prüfen."
        )
    else:
        parts.append("Pfad existiert, ist aber keine reguläre Datei.")
    return " ".join(parts)


def _atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)

STATIC_DIR = Path(__file__).resolve().parent / "static"


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms.setdefault(session_id, set()).add(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        if session_id in self._rooms:
            self._rooms[session_id].discard(websocket)
            if not self._rooms[session_id]:
                del self._rooms[session_id]

    async def broadcast(self, session_id: str, message: dict, sender: WebSocket | None = None) -> None:
        if session_id not in self._rooms:
            return
        data = json.dumps(message)
        dead: list[WebSocket] = []
        for ws in self._rooms[session_id]:
            if sender is not None and ws is sender:
                continue
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._rooms[session_id].discard(ws)


manager = ConnectionManager()

# Last gallery_base (HTTP folder of running slideshow) per WebSocket session, from TV "state" messages
session_gallery_base: Dict[str, str] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Slideshow Remote Hub", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "slideshow_hub"}


@app.get("/remote", response_class=HTMLResponse)
def remote_page() -> FileResponse:
    path = STATIC_DIR / "remote.html"
    if not path.exists():
        raise HTTPException(404, "remote.html missing")
    return FileResponse(path, media_type="text/html; charset=utf-8")


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    sid = session_id or "default"
    await manager.connect(sid, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg: Dict[str, Any] = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("type") == "state":
                gb = msg.get("gallery_base")
                if isinstance(gb, str) and gb.strip():
                    session_gallery_base[sid] = gb.strip().rstrip("/") + "/"
            await _broadcast_all(sid, msg, sender=websocket)
    except WebSocketDisconnect:
        manager.disconnect(sid, websocket)


async def _broadcast_all(
    session_id: str, message: dict, sender: WebSocket | None = None
) -> None:
    if session_id not in manager._rooms:
        return
    data = json.dumps(message)
    dead: list[WebSocket] = []
    for ws in manager._rooms[session_id]:
        if sender is not None and ws is sender:
            continue
        try:
            await ws.send_text(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        manager._rooms[session_id].discard(ws)


class RateRequest(BaseModel):
    slides_json_url: str | None = Field(
        None,
        description="Full URL to slides.json; optional if TV already sent gallery_base for this session",
    )
    slide_index: int = Field(..., ge=0)
    rating: int | None = Field(None, ge=0, le=5)
    rating_delta: int | None = Field(
        None,
        description="Relative change to couch_rating: only -1 or +1; mutually exclusive with rating",
    )
    color: str | None = Field(None, description="red|yellow|green|blue|purple or none to clear couch color")
    session_id: str | None = Field(
        None,
        description="Same WebSocket session as /remote — TV updates live via broadcast",
    )


@app.get("/api/slides-json")
async def api_slides_json(
    slides_json_url: Optional[str] = None,
    session_id: str = "default",
) -> dict:
    """Return slides manifest from disk (same path rules as POST /api/rate). Used by /remote for star-filter."""
    sid = (session_id or "").strip() or "default"
    slides_url = (slides_json_url or "").strip()
    if not slides_url:
        base = session_gallery_base.get(sid)
        if base:
            slides_url = base.rstrip("/") + "/slides.json"
    if not slides_url:
        raise HTTPException(
            400,
            "slides_json_url missing: set gallery on remote or open TV slideshow first (same session).",
        )
    slides_url = _ensure_http_slides_json_url(slides_url)
    fs_path = _resolve_slides_json_fs_path(slides_url)
    if not fs_path.is_file():
        raise HTTPException(
            400,
            f"slides.json not found on hub at {fs_path} — {_slides_json_disk_missing_help(fs_path)}",
        )
    try:
        return json.loads(fs_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(400, f"Invalid slides.json on disk: {e}") from e


@app.post("/api/rate")
async def api_rate(body: RateRequest) -> dict:
    sid = (body.session_id or "").strip() or "default"
    slides_url = (body.slides_json_url or "").strip()
    if not slides_url:
        base = session_gallery_base.get(sid)
        if base:
            slides_url = base.rstrip("/") + "/slides.json"
    if not slides_url:
        raise HTTPException(
            400,
            "slides_json_url missing: either enter Galerie-Basis-URL on remote, or open the slideshow on the TV "
            "first so it reports gallery_base (same WebSocket session).",
        )

    slides_url = _ensure_http_slides_json_url(slides_url)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(slides_url)
            r.raise_for_status()
            remote_manifest = r.json()
    except Exception as e:
        raise HTTPException(400, f"Cannot load slides.json: {e}") from e

    remote_slides = remote_manifest.get("slides") or []
    if body.slide_index >= len(remote_slides):
        raise HTTPException(400, f"slide_index out of range (max {len(remote_slides) - 1})")

    fs_path = _resolve_slides_json_fs_path(slides_url)
    if not fs_path.is_file():
        raise HTTPException(
            400,
            f"slides.json not found on hub at {fs_path} — {_slides_json_disk_missing_help(fs_path)}",
        )

    try:
        disk_manifest = json.loads(fs_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(400, f"Invalid slides.json on disk: {e}") from e

    slides = disk_manifest.get("slides") or []
    if body.slide_index >= len(slides):
        raise HTTPException(400, "slides.json on disk has fewer slides than URL manifest")

    entry = slides[body.slide_index]
    if entry.get("source_path") != remote_slides[body.slide_index].get("source_path"):
        raise HTTPException(
            409,
            "slides.json on disk is out of sync with URL (source_path mismatch). Re-copy gallery or fix file.",
        )

    couch_rating: int | None | Any = entry.get("couch_rating")
    couch_color: str | None | Any = entry.get("couch_color")

    if body.rating_delta is not None:
        if body.rating is not None:
            raise HTTPException(400, "rating_delta cannot be combined with absolute rating")
        if body.rating_delta not in (-1, 1):
            raise HTTPException(400, "rating_delta must be -1 or +1")
        old_n = 0
        if couch_rating is not None:
            try:
                old_n = int(couch_rating)
            except (TypeError, ValueError):
                old_n = 0
        old_n = max(0, min(5, old_n))
        couch_rating = max(0, min(5, old_n + body.rating_delta))
    elif body.rating is not None:
        couch_rating = body.rating
    if body.color is not None:
        c = body.color.lower().strip()
        if c in ("none", ""):
            couch_color = None
        elif c in {"red", "yellow", "green", "blue", "purple"}:
            couch_color = c
        else:
            raise HTTPException(400, f"invalid color: {body.color}")

    if body.rating_delta is None and body.rating is None and body.color is None:
        raise HTTPException(400, "nothing to update (set rating, rating_delta, or color)")

    entry["couch_rating"] = couch_rating
    entry["couch_color"] = couch_color
    slides[body.slide_index] = entry
    disk_manifest["slides"] = slides

    try:
        _atomic_write_json(fs_path, disk_manifest)
    except OSError as e:
        raise HTTPException(500, f"Cannot write slides.json: {e}") from e

    payload = {
        "type": "rated",
        "ok": True,
        "slide_index": body.slide_index,
        "couch_rating": couch_rating,
        "couch_color": couch_color,
    }
    await _broadcast_all(sid, payload)

    return {"ok": True, "slide_index": body.slide_index, "couch_rating": couch_rating, "couch_color": couch_color}


def main() -> None:
    import uvicorn

    uvicorn.run("slideshow_hub.main:app", host="0.0.0.0", port=8090, reload=False)


if __name__ == "__main__":
    main()
