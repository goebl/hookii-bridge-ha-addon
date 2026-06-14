# Hookii Bridge

> ℹ️ **Works with both the production and beta Hookii cloud.** Choose with the
> `hookii_env` option: `prod` → `iot.hookii.com` for stable-firmware mowers / a
> normal Hookii account (you get state, battery, the command buttons and
> auto-discovery), or `beta` → `iot.beta.hookii.com` for mowers on BETA firmware
> `1.6.8.4-beta` or newer (adds the granular per-system sensors + firmware-upgrade
> awareness). The bridge degrades gracefully and never fails just because a mower
> is on stable firmware.

Cloud bridge for Hookii Neomow robot mowers (May 2026 protocol).

The original community workaround — "just MQTT-subscribe to `hookii/details/device/<serial>`" — stopped working when Hookii migrated their cloud to a JWT-gated heartbeat protocol on `iot.beta.hookii.com`. This add-on logs in to your Hookii account, keeps the heartbeat alive, normalises the payload back to the legacy shape and republishes it to **your own Mosquitto broker** on the original topic. Any existing Home Assistant template-sensors, automations, dashboards, n8n flows etc. keep working without modification.

For full setup instructions, see [DOCS.md](DOCS.md).
