#!/usr/bin/env python3
"""
Subscribe to the slideshow remote hub WebSocket and log effective audio/light cues
whenever the TV's `state` message changes relevant fields.

Usage (development PC on same LAN as hub):
  pip install websockets
  python slideshow_hub/cue_state_listener.py ws://192.168.1.50:8090/ws/default

The TV must export the gallery with the same hub base and session. Optional: pass
`role=cue_debug` in hello so hub logs can distinguish this client from `remote`.

Later this can be extended into a ZYBO/Raspberry Pi bridge (same JSON, add DMX/OSC).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

try:
    import websockets
except ImportError:  # pragma: no cover
    print("Missing dependency: pip install websockets", file=sys.stderr)
    sys.exit(1)

CUE_KEYS = (
    "effective_audio_track_id",
    "effective_audio_cue_at_slide",
    "effective_light_effect_id",
    "effective_light_cue_at_slide",
)


def _cue_snapshot(msg: Dict[str, Any]) -> Tuple[Optional[int], Dict[str, Any]]:
    idx = msg.get("index")
    snap = {k: msg.get(k) for k in CUE_KEYS}
    return (idx if isinstance(idx, int) else None, snap)


async def run_listener(ws_url: str, role: str, verbose: bool) -> None:
    prev_snap: Optional[Dict[str, Any]] = None
    prev_index: Optional[int] = None
    async with websockets.connect(ws_url, ping_interval=20, ping_timeout=20) as ws:
        await ws.send(json.dumps({"type": "hello", "role": role}))
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(msg, dict):
                continue
            if msg.get("type") != "state":
                if verbose and msg.get("type") in ("hello", "cmd", "rated"):
                    print(f"[hub] {msg.get('type')}", flush=True)
                continue
            idx, snap = _cue_snapshot(msg)
            if snap == prev_snap and idx == prev_index:
                continue
            prev_snap = snap
            prev_index = idx
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
            line = (
                f"{ts} slide={idx} "
                f"audio_tid={snap['effective_audio_track_id']!r} "
                f"audio_cue_at={snap['effective_audio_cue_at_slide']!r} "
                f"light={snap['effective_light_effect_id']!r} "
                f"light_cue_at={snap['effective_light_cue_at_slide']!r}"
            )
            print(line, flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description="Log slideshow effective cues from hub WebSocket.")
    p.add_argument(
        "ws_url",
        help="Full WebSocket URL including session, e.g. ws://NAS:8090/ws/default",
    )
    p.add_argument(
        "--role",
        default="cue_debug",
        help="hello.role sent to hub (default: cue_debug)",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print non-state message types",
    )
    args = p.parse_args()
    try:
        asyncio.run(run_listener(args.ws_url.strip(), args.role.strip(), args.verbose))
    except KeyboardInterrupt:
        print("", file=sys.stderr)


if __name__ == "__main__":
    main()
