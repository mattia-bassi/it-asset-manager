#!/usr/bin/env sh
set -e

# Create log dir if mounted
mkdir -p /data/log || true

if [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
  echo "[boot] running migrations..."
  alembic upgrade head
fi

echo "[boot] using DB_HOST=${DB_HOST:-mariadb-asset-management} DB_NAME=${DB_NAME:-assetdb}"

if [ -f /app/data/ssl/cert.pem ] && [ -f /app/data/ssl/key.pem ]; then
  echo "[boot] SSL certificates found, starting with HTTPS..."
  exec uvicorn app.main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8000}" --ssl-keyfile /app/data/ssl/key.pem --ssl-certfile /app/data/ssl/cert.pem
else
  echo "[boot] No SSL certificates, starting with HTTP..."
  exec uvicorn app.main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8000}"
fi

