#!/usr/bin/with-contenv bashio
# Read the add-on options and start the mower map visualizer.

set -e

MOWERS=$(bashio::config 'mowers')
LOCAL_MQTT_HOST=$(bashio::config 'local_mqtt_host')
LOCAL_MQTT_PORT=$(bashio::config 'local_mqtt_port')
LOCAL_MQTT_USER=$(bashio::config 'local_mqtt_user')
LOCAL_MQTT_PASS=$(bashio::config 'local_mqtt_pass')
TOPIC_PREFIX=$(bashio::config 'topic_prefix')
TRAIL_MAX=$(bashio::config 'trail_max')
LOG_LEVEL=$(bashio::config 'log_level')

if bashio::var.is_empty "${MOWERS}"; then
  bashio::log.fatal "mowers is required - format: label1:serial1[:color1];label2:serial2[:color2] (e.g. garden:HKX1EB100JD25010115:#22c55e)."
  exit 1
fi
if bashio::var.is_empty "${LOCAL_MQTT_USER}" || bashio::var.is_empty "${LOCAL_MQTT_PASS}"; then
  bashio::log.fatal "local_mqtt_user / local_mqtt_pass are required - they must match a user on your Mosquitto broker."
  exit 1
fi

export MOWERS
export LOCAL_MQTT_HOST
export LOCAL_MQTT_PORT
export LOCAL_MQTT_USER
export LOCAL_MQTT_PASS
export TOPIC_PREFIX="${TOPIC_PREFIX:-hookii/details/device}"
export TRAIL_MAX="${TRAIL_MAX:-2000}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export PERSIST_DIR=/data

bashio::log.info "Starting Hookii Mower Map: broker=${LOCAL_MQTT_HOST}:${LOCAL_MQTT_PORT} mowers=${MOWERS}"
exec uvicorn --host 0.0.0.0 --port 8000 --app-dir /opt main:app
