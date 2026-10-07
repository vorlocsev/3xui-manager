FROM ghcr.io/home-assistant/base:latest

RUN apk add --no-cache python3 py3-flask py3-requests py3-qrcode

COPY app.py /app/app.py
COPY static /app/static

WORKDIR /app
EXPOSE 8099
CMD ["python3", "/app/app.py"]
