FROM ghcr.io/home-assistant/base:latest

ARG BUILD_VERSION
ARG BUILD_ARCH

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}" \
  org.opencontainers.image.title="3x-ui Manager" \
  org.opencontainers.image.description="Home Assistant App for managing remote 3x-ui VLESS Reality inbounds, clients and subscriptions." \
  org.opencontainers.image.source="https://github.com/vorlocsev/3xui-manager"

RUN apk add --no-cache \
    python3 \
    py3-flask \
    py3-requests \
    py3-qrcode

COPY app.py /app/app.py
COPY static /app/static

WORKDIR /app
EXPOSE 8099

CMD ["python3", "/app/app.py"]
