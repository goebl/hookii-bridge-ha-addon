ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip3 install --no-cache-dir \
      paho-mqtt==2.1.0 \
      fastapi==0.115.5 \
      uvicorn==0.32.1

COPY main.py /opt/main.py
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
