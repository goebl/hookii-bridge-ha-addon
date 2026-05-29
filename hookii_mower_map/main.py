"""Hookii Neomow yard visualizer.

Subscribes directly to your local Mosquitto/EMQX broker (the same broker the
Hookii Bridge add-on publishes to), captures the cloud's STATUS / DEVICE_MAP_V2
/ ALL_PATH_LIST_V2 / ALL_PATH_INDEX_V2 messages per mower, and renders an SVG
view of the yard with:

- Boundary polygon (when DEVICE_MAP_V2 is captured)
- Path coverage split into cut (thick green) vs transit (thin light) segments
- Live trail of recent positions in the per-mower colour
- Robot live position + heading arrow
- "Last fix" timestamp watermark

Endpoints:
  GET /             — JSON index of configured mowers + endpoints
  GET /svg/<label>  — Latest SVG (image/svg+xml, no-cache)
  GET /page/<label> — HTML wrapper with 10-second meta-refresh, ready to drop
                      into a Home Assistant iframe card
  GET /state/<label>— JSON of the mower's current position + battery + capture
                      timestamps
  GET /all          — Grid HTML showing every configured mower at once

Configuration is via environment variables (see DOCS.md). Defaults match the
field names the Hookii Bridge add-on publishes - if you're running both add-ons
side by side, the only required values are the broker auth + the mower list.
"""
from __future__ import annotations

import json
import math
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOCAL_MQTT_HOST = os.environ.get("LOCAL_MQTT_HOST", "127.0.0.1")
LOCAL_MQTT_PORT = int(os.environ.get("LOCAL_MQTT_PORT", "1883"))
LOCAL_MQTT_USER = os.environ.get("LOCAL_MQTT_USER", "")
LOCAL_MQTT_PASS = os.environ.get("LOCAL_MQTT_PASS", "")
TOPIC_PREFIX = os.environ.get("TOPIC_PREFIX", "hookii/details/device")

TRAIL_MAX = int(os.environ.get("TRAIL_MAX", "2000"))
PERSIST_DIR = Path(os.environ.get("PERSIST_DIR", "/data"))
PERSIST_DIR.mkdir(parents=True, exist_ok=True)


def parse_mowers(spec: str) -> dict[str, dict]:
    """Parse the MOWERS env var into a per-label state dict.

    Format: ``label1:serial1:color1;label2:serial2:color2;...``

    `color` is optional and defaults to a curated palette. Each label becomes
    the URL slug on the /svg/<label>, /page/<label>, /state/<label> endpoints.

    Example::

        MOWERS=garden:HKX1EB100JD25010115:#22c55e;pond:HKX2EB100JD24080170
    """
    palette = ["#22c55e", "#3b82f6", "#f59e0b", "#a855f7", "#ec4899", "#06b6d4"]
    result: dict[str, dict] = {}
    for i, raw in enumerate(spec.split(";")):
        raw = raw.strip()
        if not raw:
            continue
        parts = raw.split(":")
        if len(parts) < 2:
            print(f"WARNING: MOWERS entry {raw!r} is malformed (need label:serial[:color])", flush=True)
            continue
        label = parts[0].strip()
        serial = parts[1].strip()
        color = parts[2].strip() if len(parts) >= 3 else palette[i % len(palette)]
        result[label] = {
            "serial": serial,
            "color": color,
            "trail": deque(maxlen=TRAIL_MAX),
            "robot_x": None,
            "robot_y": None,
            "heading": None,
            "battery": None,
            "work_status": None,
            "online_status": None,
            "last_update": None,
            "device_map": None,
            "path_list": None,
            "path_index": None,
            "device_map_at": None,
            "path_list_at": None,
            "path_index_at": None,
            "min_x": -1000, "max_x": 1000,
            "min_y": -1000, "max_y": 1000,
        }
    return result


MOWERS_RAW = os.environ.get("MOWERS", "").strip()
if not MOWERS_RAW:
    print("FATAL: MOWERS env var is required. Format: label1:serial1[:color1];label2:serial2[:color2]", flush=True)
    raise SystemExit(2)

state = parse_mowers(MOWERS_RAW)
if not state:
    print("FATAL: no usable mowers parsed from MOWERS env var", flush=True)
    raise SystemExit(2)

# Reverse index: serial → label, used by the MQTT message handler.
serial_to_label = {s["serial"]: label for label, s in state.items()}


# ---------------------------------------------------------------------------
# Persistence (so captures survive container restarts)
# ---------------------------------------------------------------------------

def persist_capture(label: str, msg_type: str, payload: str) -> None:
    p = PERSIST_DIR / f"{label}_{msg_type}.json"
    try:
        p.write_text(payload, encoding="utf-8")
        print(f"  persisted {p}", flush=True)
    except Exception as e:
        print(f"  persist failed: {e}", flush=True)


def persist_status(label: str, s: dict) -> None:
    """Save the latest STATUS so a restart doesn't wipe last-known position.

    Mowers only broadcast STATUS while online; without this the visualizer
    would show "Waiting for data..." between restarts and the first STATUS push
    after the container comes back up.
    """
    p = PERSIST_DIR / f"{label}_STATUS.json"
    payload = {
        "serial": s["serial"],
        "robot_x": s["robot_x"],
        "robot_y": s["robot_y"],
        "heading": s["heading"],
        "battery": s["battery"],
        "work_status": s["work_status"],
        "online_status": s["online_status"],
        "last_update": s["last_update"],
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        p.write_text(json.dumps(payload), encoding="utf-8")
    except Exception as e:
        print(f"  status persist failed: {e}", flush=True)


def load_persisted() -> None:
    """Restore captures and last-known STATUS on startup."""
    for label, s in state.items():
        for kind, msg_type in (
            ("device_map", "DEVICE_MAP_V2"),
            ("path_list", "ALL_PATH_LIST_V2"),
            ("path_index", "ALL_PATH_INDEX_V2"),
        ):
            p = PERSIST_DIR / f"{label}_{msg_type}.json"
            if p.exists():
                try:
                    s[kind] = json.loads(p.read_text(encoding="utf-8"))
                    s[f"{kind}_at"] = datetime.fromtimestamp(
                        p.stat().st_mtime, tz=timezone.utc
                    ).isoformat()
                    print(f"loaded {p}", flush=True)
                except Exception as e:
                    print(f"load failed {p}: {e}", flush=True)

        sp = PERSIST_DIR / f"{label}_STATUS.json"
        if sp.exists():
            try:
                data = json.loads(sp.read_text(encoding="utf-8"))
                s["robot_x"] = data.get("robot_x")
                s["robot_y"] = data.get("robot_y")
                s["heading"] = data.get("heading")
                s["battery"] = data.get("battery")
                s["work_status"] = data.get("work_status")
                s["online_status"] = data.get("online_status")
                s["last_update"] = data.get("last_update")
                print(
                    f"loaded {sp} (pos={s['robot_x']},{s['robot_y']})",
                    flush=True,
                )
            except Exception as e:
                print(f"load failed {sp}: {e}", flush=True)

        # Fallback: derive last known position from path_list when STATUS
        # was never captured (e.g. mower has been offline since first boot).
        if s["robot_x"] is None and s.get("path_list"):
            try:
                pts = (
                    s["path_list"]["data"]["ALL_PATH_LIST_V2"]["pathList"][0]
                    .get("pathPointList", [])
                )
                if pts:
                    last = pts[-1]
                    s["robot_x"] = int(last.get("x", 0))
                    s["robot_y"] = int(last.get("y", 0))
                    s["last_update"] = s.get("path_list_at")
                    print(
                        f"fallback {label} pos from path_list last point: "
                        f"{s['robot_x']},{s['robot_y']}",
                        flush=True,
                    )
            except Exception as e:
                print(f"path_list fallback failed {label}: {e}", flush=True)


# ---------------------------------------------------------------------------
# MQTT listener
# ---------------------------------------------------------------------------

def handle_status(s: dict, status: dict) -> None:
    """Update mower state from a STATUS message."""
    x = status.get("robotX")
    y = status.get("robotY")
    heading = status.get("robotNavigation")
    if heading is None:
        heading = status.get("robotNav")  # older field name
    if x is None or y is None:
        return
    try:
        x = int(x)
        y = int(y)
    except Exception:
        return

    s["robot_x"] = x
    s["robot_y"] = y
    s["heading"] = heading
    s["battery"] = status.get("electricity")
    s["online_status"] = status.get("onlineStatus")
    s["last_update"] = (
        status.get("updateTime")
        or datetime.now(timezone.utc).isoformat()
    )

    # Trail: add a point if the mower has moved >5cm since the last sample
    if not s["trail"] or (
        abs(s["trail"][-1][0] - x) > 5 or abs(s["trail"][-1][1] - y) > 5
    ):
        s["trail"].append((x, y, time.time()))

    # Auto-expand the SVG viewport bounds with padding
    pad = 200
    s["min_x"] = min(s["min_x"], x - pad)
    s["max_x"] = max(s["max_x"], x + pad)
    s["min_y"] = min(s["min_y"], y - pad)
    s["max_y"] = max(s["max_y"], y + pad)

    # Throttled persist - only after a meaningful move or once per minute
    now = time.time()
    last_saved = s.get("_status_saved_at") or 0
    moved = (
        s.get("_status_saved_xy") is None
        or abs(s["_status_saved_xy"][0] - x) > 20
        or abs(s["_status_saved_xy"][1] - y) > 20
    )
    if moved or (now - last_saved) > 60:
        for label, v in state.items():
            if v is s:
                persist_status(label, s)
                break
        s["_status_saved_at"] = now
        s["_status_saved_xy"] = (x, y)


def on_message(client: mqtt.Client, userdata, msg):
    try:
        payload_raw = msg.payload.decode("utf-8", errors="replace")
        payload = json.loads(payload_raw)
    except Exception:
        return

    msg_type = payload.get("msgType", "?")
    serial = msg.topic.rsplit("/", 1)[-1]
    label = serial_to_label.get(serial)
    if not label:
        return
    s = state[label]

    if msg_type == "STATUS":
        status = payload.get("data", {}).get("STATUS", {})
        handle_status(s, status)

    elif msg_type == "DEVICE_MAP_V2":
        s["device_map"] = payload
        s["device_map_at"] = datetime.now(timezone.utc).isoformat()
        persist_capture(label, "DEVICE_MAP_V2", payload_raw)
        print(
            f"  GOT DEVICE_MAP_V2 for {label} ({len(payload_raw)} bytes)",
            flush=True,
        )

    elif msg_type == "ALL_PATH_LIST_V2":
        # Sanity check: don't overwrite good data with empty/blank payload.
        # When the mower comes online or the app reconnects, the broker may
        # briefly send empty path data - keep the last known good map.
        new_pts = (
            payload.get("data", {}).get("ALL_PATH_LIST_V2", {})
            .get("pathList", [{}])[0].get("pathPointList", [])
        )
        existing_pts_count = 0
        if s.get("path_list"):
            try:
                existing_pts_count = len(
                    s["path_list"]["data"]["ALL_PATH_LIST_V2"]["pathList"][0]
                    .get("pathPointList", [])
                )
            except Exception:
                pass
        # Lenient threshold: a real "new zone" can legitimately drop the count
        # significantly without being bogus.
        if not existing_pts_count or len(new_pts) >= existing_pts_count * 0.10:
            s["path_list"] = payload
            s["path_list_at"] = datetime.now(timezone.utc).isoformat()
            persist_capture(label, "ALL_PATH_LIST_V2", payload_raw)
            print(
                f"  GOT ALL_PATH_LIST_V2 for {label} ({len(payload_raw)} bytes, {len(new_pts)} pts)",
                flush=True,
            )
        else:
            print(
                f"  SKIPPED stale ALL_PATH_LIST_V2 for {label} "
                f"({len(new_pts)} pts vs {existing_pts_count} existing)",
                flush=True,
            )

    elif msg_type == "ALL_PATH_INDEX_V2":
        s["path_index"] = payload
        s["path_index_at"] = datetime.now(timezone.utc).isoformat()
        # Only persist once - these messages are noisy and the same data
        # rides every refresh, no point overwriting the file every cycle.
        if not (PERSIST_DIR / f"{label}_ALL_PATH_INDEX_V2.json").exists():
            persist_capture(label, "ALL_PATH_INDEX_V2", payload_raw)


def mqtt_listener() -> None:
    """Long-running thread: connect to local broker, subscribe per mower."""
    while True:
        try:
            client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=f"hookii-mower-map-{os.getpid()}",
            )
            if LOCAL_MQTT_USER:
                client.username_pw_set(LOCAL_MQTT_USER, LOCAL_MQTT_PASS)
            client.on_message = on_message

            print(
                f"connecting to MQTT {LOCAL_MQTT_HOST}:{LOCAL_MQTT_PORT}",
                flush=True,
            )
            client.connect(LOCAL_MQTT_HOST, LOCAL_MQTT_PORT, keepalive=60)

            # One per configured mower - keeps wildcard noise out of the
            # logs and means an unknown extra mower on the broker is silently
            # ignored rather than logged as "unknown serial".
            for label, s in state.items():
                topic = f"{TOPIC_PREFIX}/{s['serial']}"
                client.subscribe(topic, qos=0)
                print(f"  subscribed {topic} -> {label}", flush=True)

            client.loop_forever(retry_first_connection=True)
        except Exception as e:
            print(f"MQTT loop error: {e}", flush=True)
            try:
                client.disconnect()
            except Exception:
                pass
            time.sleep(5)


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------

def extract_path_points(s: dict) -> list:
    if not s.get("path_list"):
        return []
    try:
        pl = (
            s["path_list"].get("data", {}).get("ALL_PATH_LIST_V2", {})
            .get("pathList", [])
        )
        if not pl:
            return []
        points = pl[0].get("pathPointList", [])
        if len(points) > 4000:
            step = len(points) // 4000
            points = points[::step]
        return [(p.get("x", 0), p.get("y", 0), p.get("info", 0)) for p in points]
    except Exception:
        return []


def extract_boundary(s: dict) -> list:
    if not s.get("device_map"):
        return []
    try:
        d = s["device_map"].get("data", {}).get("DEVICE_MAP_V2", {})
        if isinstance(d, dict):
            for key in (
                "boundary", "boundaryPoints", "regionPoints",
                "borderPoints", "points",
            ):
                pts = d.get(key)
                if isinstance(pts, list) and pts:
                    return [
                        (p.get("x", p.get("posX", 0)), p.get("y", p.get("posY", 0)))
                        for p in pts if isinstance(p, dict)
                    ]
    except Exception:
        pass
    return []


def render_svg(label: str) -> str:
    s = state.get(label)
    if not s:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"/>'

    color = s["color"]
    if s["robot_x"] is None:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">'
            '<rect width="400" height="300" fill="#0f172a"/>'
            '<text x="20" y="40" fill="#94a3b8" font-family="sans-serif">'
            'Waiting for data...</text></svg>'
        )

    boundary_points = extract_boundary(s)
    path_points_for_bounds = extract_path_points(s)
    bound_pts = []
    if path_points_for_bounds:
        bound_pts = [(p[0], p[1]) for p in path_points_for_bounds]
    elif boundary_points:
        bound_pts = boundary_points
    bound_pts.append((s["robot_x"], s["robot_y"]))

    if len(bound_pts) > 1:
        min_x = min(p[0] for p in bound_pts)
        max_x = max(p[0] for p in bound_pts)
        min_y = min(p[1] for p in bound_pts)
        max_y = max(p[1] for p in bound_pts)
        pad = 200
        min_x -= pad; max_x += pad; min_y -= pad; max_y += pad
    else:
        min_x = s["min_x"]; max_x = s["max_x"]
        min_y = s["min_y"]; max_y = s["max_y"]

    span_x = max(max_x - min_x, 2000)
    span_y = max(max_y - min_y, 2000)
    width = int(span_x)
    height = int(span_y)

    def to_svg(x, y):
        return (x - min_x, max_y - y)  # flip Y for SVG coords

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" '
        f'viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet">',
        f'<rect width="{width}" height="{height}" fill="#0f172a"/>',
    ]
    px = max(span_x, span_y) / 800  # 1 screen px in data units

    if boundary_points:
        pts = " ".join(
            f"{to_svg(x, y)[0]:.1f},{to_svg(x, y)[1]:.1f}" for x, y in boundary_points
        )
        svg.append(
            f'<polygon points="{pts}" fill="#22c55e22" stroke="#22c55e" '
            f'stroke-width="2" stroke-dasharray="4 2"/>'
        )

    path_points = extract_path_points(s)
    if path_points:
        cut_segments: list[list[tuple]] = []
        transit_segments: list[list[tuple]] = []
        cur: list[tuple] = []
        cur_info = None
        for x, y, info in path_points:
            if info != cur_info:
                if cur:
                    (cut_segments if cur_info == 1 else transit_segments).append(cur)
                cur = []
                cur_info = info
            cur.append((x, y))
        if cur:
            (cut_segments if cur_info == 1 else transit_segments).append(cur)

        for seg in cut_segments:
            if len(seg) < 2:
                continue
            pts = " ".join(
                f"{to_svg(x, y)[0]:.0f},{to_svg(x, y)[1]:.0f}" for x, y in seg
            )
            svg.append(
                f'<polyline points="{pts}" fill="none" stroke="#22c55e" '
                f'stroke-width="{px*3:.1f}" stroke-linecap="round" opacity="0.85"/>'
            )
        for seg in transit_segments:
            if len(seg) < 2:
                continue
            pts = " ".join(
                f"{to_svg(x, y)[0]:.0f},{to_svg(x, y)[1]:.0f}" for x, y in seg
            )
            svg.append(
                f'<polyline points="{pts}" fill="none" stroke="#86efac" '
                f'stroke-width="{px*1:.1f}" opacity="0.4"/>'
            )

    if len(s["trail"]) > 1:
        pts = " ".join(
            f"{to_svg(x, y)[0]:.0f},{to_svg(x, y)[1]:.0f}" for x, y, _ in s["trail"]
        )
        svg.append(
            f'<polyline points="{pts}" fill="none" stroke="{color}" '
            f'stroke-width="{px*2:.1f}" opacity="0.7"/>'
        )

    rx, ry = to_svg(s["robot_x"], s["robot_y"])
    r = px * 10
    svg.append(
        f'<circle cx="{rx:.0f}" cy="{ry:.0f}" r="{r:.0f}" fill="{color}" '
        f'stroke="#fff" stroke-width="{px*2:.1f}"/>'
    )
    if s["heading"] is not None:
        try:
            angle_rad = math.radians(float(s["heading"]))
            ahx = math.sin(angle_rad) * px * 18
            ahy = -math.cos(angle_rad) * px * 18
            svg.append(
                f'<line x1="{rx:.0f}" y1="{ry:.0f}" '
                f'x2="{rx + ahx:.0f}" y2="{ry + ahy:.0f}" '
                f'stroke="#fff" stroke-width="{px*3:.1f}"/>'
            )
        except Exception:
            pass

    if s.get("last_update"):
        label_str = f"last fix: {s['last_update']}"
        fs = px * 18
        tx = px * 10
        ty = px * 24
        svg.append(
            f'<text x="{tx:.0f}" y="{ty:.0f}" fill="#e2e8f0" '
            f'font-family="sans-serif" font-size="{fs:.0f}" '
            f'stroke="#0f172a" stroke-width="{px*3:.1f}" paint-order="stroke">'
            f'{label_str}</text>'
        )

    svg.append('</svg>')
    return "\n".join(svg)


# ---------------------------------------------------------------------------
# HTTP API
# ---------------------------------------------------------------------------

app = FastAPI(title="Hookii Mower Map")


@app.get("/")
def root():
    return {
        "mowers": [
            {"label": label, "serial": s["serial"], "color": s["color"]}
            for label, s in state.items()
        ],
        "endpoints": ["/svg/{label}", "/page/{label}", "/state/{label}", "/all"],
    }


@app.get("/svg/{label}")
def get_svg(label: str):
    if label not in state:
        raise HTTPException(status_code=404, detail=f"unknown mower {label!r}")
    return Response(
        content=render_svg(label),
        media_type="image/svg+xml",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@app.get("/state/{label}")
def get_state(label: str):
    s = state.get(label)
    if not s:
        raise HTTPException(status_code=404, detail=f"unknown mower {label!r}")
    return {
        "serial": s["serial"],
        "robot_x": s["robot_x"],
        "robot_y": s["robot_y"],
        "heading": s["heading"],
        "battery": s["battery"],
        "trail_len": len(s["trail"]),
        "last_update": s["last_update"],
        "device_map_captured": s["device_map_at"],
        "path_list_captured": s["path_list_at"],
        "path_index_captured": s["path_index_at"],
    }


@app.get("/page/{label}", response_class=HTMLResponse)
def get_page(label: str):
    if label not in state:
        raise HTTPException(status_code=404, detail=f"unknown mower {label!r}")
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{label}</title>
<meta http-equiv="refresh" content="10">
<style>
  html, body {{ background:#0f172a; margin:0; padding:0; height:100%; overflow:hidden; }}
  img {{ width:100%; height:100%; object-fit:contain; display:block; }}
</style></head><body>
<img src="/svg/{label}?t={int(time.time())}" alt="{label}"/>
</body></html>"""


@app.get("/all", response_class=HTMLResponse)
def get_all():
    blocks = []
    for label in state:
        blocks.append(
            f'<div class="mower"><h2>{label.upper()}</h2>'
            f'<img src="/svg/{label}?t={int(time.time())}"/></div>'
        )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Hookii Mower Map</title>
<meta http-equiv="refresh" content="10">
<style>
  body {{ background:#0f172a; color:#f1f5f9; font-family:sans-serif; margin:0; padding:12px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(380px,1fr)); gap:12px; }}
  .mower {{ background:#1e293b; border-radius:8px; padding:8px; }}
  h2 {{ margin:4px 8px; font-size:14px; }}
  img {{ width:100%; height:auto; display:block; border-radius:4px; }}
</style></head><body>
<div class="grid">{"".join(blocks)}</div>
</body></html>"""


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

load_persisted()
threading.Thread(target=mqtt_listener, name="mqtt", daemon=True).start()
print(
    f"hookii-mower-map ready: {len(state)} mower(s) configured: "
    f"{', '.join(state.keys())}",
    flush=True,
)
