#!/bin/sh
# ============================================
# BUILD & DEPLOY FRONTEND — node:20-alpine
# Usage: sh scripts/build-frontend.sh
# ============================================

set -e

PROJECT_DIR="/share/ZFS18_DATA/Container/AssetManagment"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
CONTAINER="asset-app"
NODE_IMAGE="node:20-alpine"

echo "🔨 Building frontend with ${NODE_IMAGE}..."
cd "${FRONTEND_DIR}"

# 1. Build via Docker
docker run --rm \
  -v "$(pwd)":/app \
  -w /app \
  ${NODE_IMAGE} \
  sh -c "npm install && npm run build"

# 2. Clean old assets in container
echo "🧹 Cleaning old assets..."
docker exec ${CONTAINER} sh -c "rm -f /app/static/dist/assets/*"

# 3. Deploy new build
echo "📦 Deploying new build..."
docker cp dist/. ${CONTAINER}:/app/static/dist/

# 4. Verify
echo "✅ Deploy complete. Files in container:"
docker exec ${CONTAINER} ls -la /app/static/dist/assets/
echo ""
echo ">>> Fai Ctrl+Shift+R nel browser per vedere le modifiche"
