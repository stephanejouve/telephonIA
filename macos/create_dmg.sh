#!/bin/bash
# Cree un DMG drag-and-drop pour telephonIA.app
# Usage: bash macos/create_dmg.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build/macos"
DIST_DIR="$PROJECT_ROOT/dist"
APP_NAME="telephonIA"
APP_BUNDLE="$BUILD_DIR/$APP_NAME.app"
DMG_NAME="$APP_NAME.dmg"
DMG_PATH="$DIST_DIR/$DMG_NAME"
STAGING_DIR="$BUILD_DIR/dmg_staging"

echo "=== Creation DMG telephonIA ==="

# Verifier que le .app existe
if [ ! -d "$APP_BUNDLE" ]; then
    echo "ERREUR: $APP_BUNDLE introuvable."
    echo "Lancer d'abord: bash macos/build_macos.sh"
    exit 1
fi

# Nettoyage
rm -rf "$STAGING_DIR"
rm -f "$DMG_PATH"
mkdir -p "$STAGING_DIR" "$DIST_DIR"

# Preparer le contenu du DMG
echo "Preparation du contenu..."
cp -R "$APP_BUNDLE" "$STAGING_DIR/"
ln -s /Applications "$STAGING_DIR/Applications"

# Creer le DMG
echo "Creation du DMG..."
hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$STAGING_DIR" \
    -ov \
    -format UDZO \
    "$DMG_PATH"

# Nettoyage staging
rm -rf "$STAGING_DIR"

# Verification
DMG_SIZE=$(du -sh "$DMG_PATH" | cut -f1)
echo ""
echo "=== DMG cree avec succes ==="
echo "Fichier : $DMG_PATH"
echo "Taille  : $DMG_SIZE"
echo ""
echo "Pour installer : ouvrir le DMG et glisser telephonIA dans Applications"
