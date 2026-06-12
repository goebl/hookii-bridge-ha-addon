ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# paho-mqtt + requests for the bridge; fastapi + uvicorn for the built-in Mower Map.
RUN pip3 install --no-cache-dir \
      paho-mqtt==2.1.0 \
      requests==2.32.3 \
      fastapi==0.115.5 \
      uvicorn==0.32.1

COPY bridge.py /opt/bridge.py
COPY map_server.py /opt/map_server.py
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
