#!/usr/bin/env bash
# Build le frontend React et copie dans web/static/ pour servir via FastAPI.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_DIR/frontend"
STATIC_DIR="$PROJECT_DIR/src/telephonia/web/static"

echo "Build du frontend..."
cd "$FRONTEND_DIR"
npm install
npm run build

echo "Copie vers $STATIC_DIR..."
# Nettoyer sauf .gitkeep
find "$STATIC_DIR" -mindepth 1 ! -name '.gitkeep' -delete 2>/dev/null || true
cp -r dist/* "$STATIC_DIR/"

echo "Build termine."
