# Plain-Python image for running bridge.py outside Home Assistant Supervisor.
#
# This is the image Tor's k3s cluster builds + runs - same bridge.py as the
# HA add-on (which has its own hookii_bridge/Dockerfile based on the HA
# Supervisor base image with bashio + run.sh wrapper). Keeping the two
# Dockerfiles disjoint means HA OS users get bashio + options.json wiring
# while operators running outside Supervisor get a tiny generic image
# configurable directly via env vars.
#
# Usage:
#   docker build -t hookii-bridge:local .
#   docker run --rm -e HOOKII_ACCOUNTS="me:foo@bar:secret" \
#              -e LOCAL_MQTT_USER=mqtt -e LOCAL_MQTT_PASS=mqtt \
#              -e LOCAL_MQTT_HOST=192.168.1.10 hookii-bridge:local
#
# See hookii_bridge/bridge.py top-level docstring for the full env list.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir paho-mqtt==2.1.0 requests==2.32.3

WORKDIR /app
COPY hookii_bridge/bridge.py /app/bridge.py

CMD ["python", "/app/bridge.py"]
