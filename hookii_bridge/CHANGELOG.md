# Changelog

## 1.0.1 (2026-05-29)

- Docs-only: scrubbed Conscient Systems / k3s-specific references from `bridge.py` docstrings so the file reads cleanly as a standalone Python script for HA OS users (or for anyone else who wants to run it under systemd / Docker Compose / etc.). No behaviour change.

## 1.0.0 (2026-05-29)

- Initial public release.
- Logs in to `iot.beta.hookii.com` REST API with your Hookii account, opens MQTT session over self-signed TLS, keeps a 15 s heartbeat alive so the cloud keeps pushing STATUS for your mower(s).
- Normalises both protocol payload shapes (legacy `electricity` / new `battery`, flat motor temps / nested `chassisData`, top-level `workStatus` / nested `workTimeStatusInfo.workStatus`) so all existing Home Assistant template sensors keep working.
- Auto-learns per-mower model code from the first observed STATUS push (works for Neomow X Pro `0002` and any non-Pro variant your account owns).
- Accepts either cleartext password or a 32-character MD5-uppercased hash in `hookii_password` (auto-detected).
