"""
Slideshow Remote Hub — WebSocket relay + optional rating API for LAN / NAS.

TV (exported index.html) and phones/tablets connect to the same session;
commands and state sync through this process. Ratings write the same
hidden sidecars as photo_tool: .{stem}.metadata.json next to the source file.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Set
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


def _metadata_file(photo_path: Path) -> Path:
    return photo_path.parent / f".{photo_path.stem}.metadata.json"


def _get_metadata(photo_path: Path) -> Dict[str, Any]:
    meta_file = _metadata_file(photo_path)
    if meta_file.exists():
        try:
            return json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "rating": 0,
        "color": None,
        "keywords": [],
        "comment": None,
        "gps": None,
        "updated": None,
    }


def _set_metadata(photo_path: Path, updates: Dict[str, Any]) -> None:
    existing = _get_metadata(photo_path)
    existing.update(updates)
    existing["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta_file = _metadata_file(photo_path)
    meta_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

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
            await _broadcast_all(sid, msg)
    except WebSocketDisconnect:
        manager.disconnect(sid, websocket)


async def _broadcast_all(session_id: str, message: dict) -> None:
    if session_id not in manager._rooms:
        return
    data = json.dumps(message)
    dead: list[WebSocket] = []
    for ws in manager._rooms[session_id]:
        try:
            await ws.send_text(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        manager._rooms[session_id].discard(ws)


class RateRequest(BaseModel):
    slides_json_url: str = Field(..., description="Full URL to slides.json (e.g. http://nas:8080/show/slides.json)")
    slide_index: int = Field(..., ge=0)
    rating: int | None = Field(None, ge=0, le=5)
    color: str | None = Field(None, description="red|yellow|green|blue|purple or null to clear")


@app.post("/api/rate")
async def api_rate(body: RateRequest) -> dict:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(body.slides_json_url)
            r.raise_for_status()
            manifest = r.json()
    except Exception as e:
        raise HTTPException(400, f"Cannot load slides.json: {e}") from e

    slides = manifest.get("slides") or []
    if body.slide_index >= len(slides):
        raise HTTPException(400, f"slide_index out of range (max {len(slides) - 1})")

    entry = slides[body.slide_index]
    src = entry.get("source_path")
    if not src:
        raise HTTPException(400, "slide has no source_path")

    photo_path = Path(src)
    if not photo_path.is_file():
        raise HTTPException(
            400,
            f"source photo missing on hub host: {photo_path}. "
            "Export from paths the NAS can see, or run the hub on the PC that has the files.",
        )

    updates: dict = {}
    if body.rating is not None:
        updates["rating"] = body.rating
    if body.color is not None:
        c = body.color.lower().strip()
        if c in ("none", ""):
            updates["color"] = None
        elif c in {"red", "yellow", "green", "blue", "purple"}:
            updates["color"] = c
        else:
            raise HTTPException(400, f"invalid color: {body.color}")

    if not updates:
        raise HTTPException(400, "nothing to update (set rating or color)")

    _set_metadata(photo_path, updates)
    updated = _get_metadata(photo_path)
    return {"ok": True, "slide_index": body.slide_index, "metadata": {"rating": updated.get("rating"), "color": updated.get("color")}}


def main() -> None:
    import uvicorn

    uvicorn.run("slideshow_hub.main:app", host="0.0.0.0", port=8090, reload=False)


if __name__ == "__main__":
    main()
