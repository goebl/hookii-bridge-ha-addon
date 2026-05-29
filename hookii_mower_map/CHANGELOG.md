# Changelog

## 1.0.0 (2026-05-29)

- Initial public release.
- Subscribes directly to the local MQTT broker (does not require a Home Assistant token or WebSocket).
- Auto-renders a per-mower SVG yard view with boundary polygon, cut/transit path segments, live trail and current robot position + heading arrow.
- Captures `STATUS` / `DEVICE_MAP_V2` / `ALL_PATH_LIST_V2` / `ALL_PATH_INDEX_V2` and persists to `/data` so a container restart doesn't lose the last-known position or boundary.
- Per-mower colour configurable via the `mowers` option; defaults to a curated palette.
- HTTP API: `/svg/<label>`, `/page/<label>` (10-second auto-refresh iframe-ready HTML), `/state/<label>`, `/all` (grid of every configured mower).
