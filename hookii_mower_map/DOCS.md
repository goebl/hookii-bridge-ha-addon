# Hookii Mower Map

Live SVG yard visualizer for Hookii Neomow robot mowers. Subscribes to the same
local Mosquitto/EMQX broker the [Hookii Bridge](../hookii_bridge/DOCS.md) add-on
publishes to, captures the cloud's `STATUS` / `DEVICE_MAP_V2` /
`ALL_PATH_LIST_V2` messages per mower, and renders a per-mower SVG with the
boundary polygon, cut/transit path segments, live trail and current robot
position with heading arrow.

> ⚠️ **You must run the Hookii Bridge add-on first.** This add-on is a pure
> consumer of the bridge's MQTT output - it does NOT talk to Hookii's cloud
> directly. If the bridge isn't publishing to your broker, the map will sit at
> "Waiting for data..." forever.

## What you get

- A web UI at the add-on's ingress URL with an HTML grid of every configured
  mower (`/all`)
- One auto-refreshing HTML page per mower (`/page/<label>`) ready to drop into
  a Lovelace `iframe` card
- A raw SVG endpoint per mower (`/svg/<label>`)
- A small JSON state endpoint per mower (`/state/<label>`) for automations

Captured payloads are persisted to `/data` so a container restart doesn't wipe
the boundary polygon or last-known position.

## Prerequisites

1. The [Hookii Bridge](../hookii_bridge/DOCS.md) add-on (or any equivalent
   process) is publishing the cloud's STATUS/path payloads to a local MQTT
   broker on the topic format `hookii/details/device/<SERIAL>`.
2. You know each mower's full serial number (16 chars, starts with `HKX`). You
   can read these off the bridge add-on's log or from the Hookii mobile app.
3. You have credentials for a user on the same MQTT broker the bridge uses.
   You can re-use the bridge's credentials, or create a dedicated read-only
   user for the map.

## Configuration

| Field | Required | Default | Description |
|---|---|---|---|
| **mowers** | yes | — | Semicolon-separated mower list: `label:serial[:color];label:serial[:color];...`. `label` is a short slug used in URLs (`/svg/<label>`). `color` is optional and defaults to a curated palette. |
| **local_mqtt_host** | yes | `core-mosquitto` | MQTT broker hostname. Use `core-mosquitto` if you run the official Mosquitto add-on; otherwise your broker's IP. |
| **local_mqtt_port** | no | `1883` | |
| **local_mqtt_user** | yes | — | |
| **local_mqtt_pass** | yes | — | |
| **topic_prefix** | no | `hookii/details/device` | Topic prefix the bridge publishes to. Only change this if you customised `LOCAL_TOPIC_FMT` on the bridge. |
| **trail_max** | no | `2000` | Number of recent position samples to keep for the live trail polyline (drawn in the mower colour). |
| **log_level** | no | `INFO` | `DEBUG` for verbose per-message logs. |

### Example configuration

```yaml
mowers: "garden:HKX1EB100JD25010115:#22c55e;pond:HKX2EB100JD24080170:#3b82f6"
local_mqtt_host: "core-mosquitto"
local_mqtt_port: 1883
local_mqtt_user: "mowermap"
local_mqtt_pass: "********"
```

This configures two mowers. The first one is reachable at `/svg/garden`,
`/page/garden` and `/state/garden`. The second one at the analogous `pond`
URLs. Both appear together in the `/all` grid.

## Adding the map to a Lovelace dashboard

Open the dashboard you want the map on, switch to YAML mode, and add an iframe
card:

```yaml
type: iframe
url: /hassio/ingress/hookii_mower_map/page/garden
aspect_ratio: 100%
```

If you've disabled add-on ingress, point the iframe at the add-on's host:port
instead (e.g. `http://homeassistant.local:8000/page/garden`).

For a side-by-side view of every mower in one card:

```yaml
type: iframe
url: /hassio/ingress/hookii_mower_map/all
aspect_ratio: 80%
```

## What gets rendered

| Element | Source | When it appears |
|---|---|---|
| Boundary polygon (dashed green) | `DEVICE_MAP_V2` | After the mower has streamed its mapped region at least once |
| Cut path segments (thick green) | `ALL_PATH_LIST_V2` points where `info=1` | When the mower has been actively cutting in the current zone |
| Transit path segments (thin light green) | `ALL_PATH_LIST_V2` points where `info=0` | When the mower has been moving without cutting |
| Live trail (mower colour polyline) | `STATUS` position samples > 5cm apart | Builds up as the mower moves; capped at `trail_max` points |
| Robot circle + heading arrow | `STATUS.robotX/robotY/robotNav` | Whenever the mower is online and streaming STATUS |
| "Last fix" watermark | `STATUS` timestamp | Always, once a STATUS has been received |

Coordinates are in centimetres relative to the dock. The SVG viewport
auto-expands as new positions are observed.

## Troubleshooting

### "Waiting for data..." that never resolves

Run the bridge add-on first and confirm it's publishing. From any MQTT client:

```bash
mosquitto_sub -h <broker> -u <user> -P <pass> -t 'hookii/details/device/+' -v
```

You should see a steady stream of `STATUS` / `NOTICE_ALARM` / `REGION_TASK`
payloads tagged with each serial. If you don't, the bridge isn't publishing -
check its log.

### Map renders but no boundary polygon

`DEVICE_MAP_V2` is sent by the cloud less often than STATUS - it can take
minutes to hours after the mower first comes online. The map will keep
rendering live positions + trail in the meantime, and the polygon appears the
moment the first `DEVICE_MAP_V2` is captured (it's persisted to `/data` so it
survives restarts).

### Map renders but path coverage is empty / sparse

Path coverage comes from `ALL_PATH_LIST_V2`. The bridge streams this whenever
it arrives from the cloud, which is usually as the mower starts/finishes a
task. If your mower hasn't run a job since you installed the bridge, the path
will be empty until the next mowing session ends.

### A mower I configured shows up as 404

Check that the label in `/svg/<label>` exactly matches the slug in your
`mowers` config (lowercase, no spaces). The label is the part **before** the
first colon in each semicolon-separated entry.

## Privacy / data exposure

The add-on listens to MQTT on your LAN only. It does NOT phone home, NOT
upload anything, and NOT contact Hookii's cloud directly. All persisted captures
stay in `/data` on your Home Assistant host. The HTTP API is exposed via Home
Assistant Ingress by default, which means it's only reachable through HA's
authenticated UI.

## See also

- [Hookii Bridge](../hookii_bridge/DOCS.md) - the source of all the MQTT data
  this add-on consumes
- [Repository README](../README.md) - covers both add-ons and the
  non-Supervisor install path
