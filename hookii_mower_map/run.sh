#!/usr/bin/with-contenv bashio
# Dual-mode launcher:
#   - HA add-on (Supervisor present) → read /data/options.json via bashio
#   - Standalone k3s/docker (no Supervisor) → read env vars directly
# When `bashio` is available and the Supervisor responds, we hydrate the env
# from the add-on config; otherwise we trust the env that's already set
# (k3s Deployment / docker -e flags) and skip the bashio calls entirely.

set -e

# Supervisor presence detected via SUPERVISOR_TOKEN env var, which is only
# set by HA Supervisor. Probing `bashio::supervisor.ping` directly triggers
# bashio internals that reference SUPERVISOR_TOKEN, and on some base images
# that combines with `set -u` to kill the script before our probe even
# returns - so we check the env var FIRST and only then call bashio.
if [ -n "${SUPERVISOR_TOKEN:-}" ] && command -v bashio >/dev/null 2>&1; then
  # Hosted as an HA add-on - pull config from options.json.
  MOWERS=$(bashio::config 'mowers')
  LOCAL_MQTT_HOST=$(bashio::config 'local_mqtt_host')
  LOCAL_MQTT_PORT=$(bashio::config 'local_mqtt_port')
  LOCAL_MQTT_USER=$(bashio::config 'local_mqtt_user')
  LOCAL_MQTT_PASS=$(bashio::config 'local_mqtt_pass')
  TOPIC_PREFIX=$(bashio::config 'topic_prefix')
  TRAIL_MAX=$(bashio::config 'trail_max')
  LOG_LEVEL=$(bashio::config 'log_level')
  ROTATE_DEG=$(bashio::config 'rotate_deg')
fi

# Validate the minimum config regardless of source.
if [ -z "${MOWERS}" ]; then
  echo "FATAL: MOWERS is required - format: label1:serial1[:color1];label2:serial2[:color2] (e.g. garden:HKX1EB100JD25010115:#22c55e)." >&2
  exit 1
fi
if [ -z "${LOCAL_MQTT_USER}" ] || [ -z "${LOCAL_MQTT_PASS}" ]; then
  echo "FATAL: LOCAL_MQTT_USER / LOCAL_MQTT_PASS are required - they must match a user on your Mosquitto broker." >&2
  exit 1
fi

export MOWERS
export LOCAL_MQTT_HOST="${LOCAL_MQTT_HOST:-core-mosquitto}"
export LOCAL_MQTT_PORT="${LOCAL_MQTT_PORT:-1883}"
export LOCAL_MQTT_USER
export LOCAL_MQTT_PASS
export TOPIC_PREFIX="${TOPIC_PREFIX:-hookii/details/device}"
export TRAIL_MAX="${TRAIL_MAX:-2000}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export PERSIST_DIR="${PERSIST_DIR:-/data}"
export ROTATE_DEG="${ROTATE_DEG:-0}"

echo "Starting Hookii Mower Map: broker=${LOCAL_MQTT_HOST}:${LOCAL_MQTT_PORT} mowers=${MOWERS}"
exec uvicorn --host 0.0.0.0 --port 8000 --app-dir /opt main:app
