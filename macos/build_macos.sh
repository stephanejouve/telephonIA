#!/bin/bash
# Build script pour telephonIA.app (macOS)
# Usage: bash macos/build_macos.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build/macos"
DIST_DIR="$PROJECT_ROOT/dist"
APP_NAME="telephonIA"
APP_BUNDLE="$BUILD_DIR/$APP_NAME.app"

echo "=== Build telephonIA.app ==="
echo "Projet : $PROJECT_ROOT"
echo ""

# Nettoyage
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# -------------------------------------------------------
# Phase 1 : Build React
# -------------------------------------------------------
echo "--- Phase 1/5 : Build React ---"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
STATIC_DIR="$PROJECT_ROOT/src/telephonia/web/static"

if [ -f "$FRONTEND_DIR/package.json" ]; then
    cd "$FRONTEND_DIR"
    npm install --silent
    npm run build
    # Vite build dans frontend/dist/ -> copier vers static/
    rm -rf "$STATIC_DIR"
    mkdir -p "$STATIC_DIR"
    cp -R "$FRONTEND_DIR/dist/"* "$STATIC_DIR/"
    cd "$PROJECT_ROOT"
    echo "React build OK -> $STATIC_DIR ($(ls "$STATIC_DIR" | wc -l | tr -d ' ') fichiers)"
else
    echo "ATTENTION: frontend/package.json absent, skip build React"
    if [ ! -d "$STATIC_DIR" ] || [ -z "$(ls -A "$STATIC_DIR" 2>/dev/null | grep -v .gitkeep)" ]; then
        echo "ERREUR: Pas de build React dans $STATIC_DIR"
        exit 1
    fi
    echo "Utilisation du build React existant"
fi
echo ""

# -------------------------------------------------------
# Phase 2 : Build py2app (backend Python)
# -------------------------------------------------------
echo "--- Phase 2/5 : Build py2app ---"
cd "$SCRIPT_DIR"

# py2app ne supporte pas Python 3.13+ (module imp supprime)
# On utilise un venv Python 3.11 dedie au build
PYTHON311=$(which python3.11 2>/dev/null || true)
if [ -z "$PYTHON311" ]; then
    echo "ERREUR: python3.11 requis pour py2app (3.13+ incompatible)"
    exit 1
fi
# Resoudre le vrai chemin (pas un symlink Homebrew)
PYTHON311_REAL=$(python3.11 -c "import sys; print(sys.executable)")
echo "Python 3.11 : $PYTHON311_REAL"

BUILD_VENV="$BUILD_DIR/venv_py2app"
"$PYTHON311" -m venv "$BUILD_VENV"
"$BUILD_VENV/bin/pip" install --quiet --upgrade pip setuptools
"$BUILD_VENV/bin/pip" install --quiet py2app
"$BUILD_VENV/bin/pip" install --quiet \
    fastapi "uvicorn[standard]" pydub keyring edge-tts python-multipart requests
# Installer telephonia pour que py2app le trouve
"$BUILD_VENV/bin/pip" install --quiet -e "$PROJECT_ROOT"

# Nettoyer les builds py2app precedents
rm -rf build dist

echo "Lancement py2app (semi-standalone)..."
"$BUILD_VENV/bin/python" py2app_setup.py py2app \
    --dist-dir "$BUILD_DIR/py2app_output" 2>&1 | grep -E "^(error|Done|creating|running)" || true

PY2APP_APP=$(find "$BUILD_DIR/py2app_output" -name "*.app" -maxdepth 1 | head -1)

if [ -z "$PY2APP_APP" ] || [ ! -d "$PY2APP_APP" ]; then
    echo "ERREUR: py2app n'a pas produit de .app"
    exit 1
fi

# Corriger le symlink Python : pointer vers le system Python, pas le venv
PY2APP_PYTHON_LINK="$PY2APP_APP/Contents/MacOS/python"
if [ -L "$PY2APP_PYTHON_LINK" ]; then
    rm "$PY2APP_PYTHON_LINK"
    ln -s "$PYTHON311_REAL" "$PY2APP_PYTHON_LINK"
    echo "Symlink Python corrige -> $PYTHON311_REAL"
fi

echo "py2app OK -> $PY2APP_APP"
cd "$PROJECT_ROOT"
echo ""

# -------------------------------------------------------
# Phase 3 : Compile Swift
# -------------------------------------------------------
echo "--- Phase 3/5 : Compile Swift ---"
SWIFT_SRC="$SCRIPT_DIR/TelephonIA/main.swift"
SWIFT_BIN="$BUILD_DIR/telephonIA"

swiftc "$SWIFT_SRC" \
    -framework AppKit \
    -framework WebKit \
    -target x86_64-apple-macos11.0 \
    -O \
    -o "$SWIFT_BIN"

echo "Swift compile OK -> $SWIFT_BIN"
echo ""

# -------------------------------------------------------
# Phase 4 : Assembler le .app
# -------------------------------------------------------
echo "--- Phase 4/5 : Assemblage $APP_NAME.app ---"

# Structure du bundle
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources/python_backend"

# Binaire Swift (point d'entree)
cp "$SWIFT_BIN" "$APP_BUNDLE/Contents/MacOS/telephonIA"

# Info.plist
cp "$SCRIPT_DIR/TelephonIA/Info.plist" "$APP_BUNDLE/Contents/Info.plist"

# Backend py2app -> python_backend/
PY2APP_RESOURCES="$PY2APP_APP/Contents/Resources"
PYTHON_BACKEND="$APP_BUNDLE/Contents/Resources/python_backend"

# Wrapper shell au lieu du stub py2app (le stub cherche Info.plist via
# NSBundle.mainBundle ce qui echoue quand il n'est pas dans Contents/MacOS/)
cat > "$PYTHON_BACKEND/telephonia-web" << 'WRAPPER'
#!/bin/bash
# Wrapper de lancement backend telephonIA (remplace le stub py2app)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export RESOURCEPATH="$SCRIPT_DIR"
export ARGVZERO="$0"
export PYTHONNOUSERSITE=1

# Site-packages bundle en priorite (evite typing_extensions systeme etc.)
if [ -d "$SCRIPT_DIR/lib" ]; then
    export PYTHONPATH="$SCRIPT_DIR/lib:${PYTHONPATH:-}"
fi

exec python3.11 -s "$SCRIPT_DIR/__boot__.py" "$@"
WRAPPER
chmod +x "$PYTHON_BACKEND/telephonia-web"

# Bootstrap et config py2app (necessaires au runtime)
for f in __boot__.py site.pyc app.py __error__.sh; do
    [ -f "$PY2APP_RESOURCES/$f" ] && cp "$PY2APP_RESOURCES/$f" "$PYTHON_BACKEND/"
done

# Librairies Python (lib/)
if [ -d "$PY2APP_RESOURCES/lib" ]; then
    # rsync -rL deference les symlinks ; code 23 = symlinks casses ignores (OK)
rsync -rL "$PY2APP_RESOURCES/lib/" "$PYTHON_BACKEND/lib/" 2>/dev/null || {
    rc=$?; [ $rc -eq 23 ] || exit $rc
}
fi

# Include (headers Python necessaires)
if [ -d "$PY2APP_RESOURCES/include" ]; then
    rsync -rL "$PY2APP_RESOURCES/include/" "$PYTHON_BACKEND/include/" 2>/dev/null || {
    rc=$?; [ $rc -eq 23 ] || exit $rc
}
fi

# Build React (static/)
if [ -d "$PY2APP_RESOURCES/static" ] && [ "$(ls -A "$PY2APP_RESOURCES/static" 2>/dev/null)" ]; then
    cp -R "$PY2APP_RESOURCES/static" "$PYTHON_BACKEND/static"
else
    cp -R "$STATIC_DIR" "$PYTHON_BACKEND/static"
fi

# Assets
if [ -d "$PY2APP_RESOURCES/assets" ]; then
    cp -R "$PY2APP_RESOURCES/assets" "$PYTHON_BACKEND/assets"
elif [ -d "$PROJECT_ROOT/assets" ]; then
    cp -R "$PROJECT_ROOT/assets" "$PYTHON_BACKEND/assets"
fi

# ffmpeg + ffprobe (pydub a besoin des deux : ffmpeg pour encoder/mixer,
# ffprobe pour introspecter duree/codec/channels).
for bin_name in ffmpeg ffprobe; do
    if [ -f "$PY2APP_RESOURCES/$bin_name" ]; then
        cp "$PY2APP_RESOURCES/$bin_name" "$PYTHON_BACKEND/$bin_name"
    else
        BIN_SYS=$(which "$bin_name" 2>/dev/null || true)
        if [ -n "$BIN_SYS" ]; then
            cp "$BIN_SYS" "$PYTHON_BACKEND/$bin_name"
        else
            echo "ATTENTION: $bin_name non trouve, le bundle sera incomplet"
        fi
    fi
    [ -f "$PYTHON_BACKEND/$bin_name" ] && chmod +x "$PYTHON_BACKEND/$bin_name"
done

# Icone (optionnel)
if [ -f "$SCRIPT_DIR/AppIcon.icns" ]; then
    cp "$SCRIPT_DIR/AppIcon.icns" "$APP_BUNDLE/Contents/Resources/AppIcon.icns"
fi

echo "Assemblage OK -> $APP_BUNDLE"
echo ""

# -------------------------------------------------------
# Phase 5 : Verification
# -------------------------------------------------------
echo "--- Phase 5/5 : Verification ---"

ERRORS=0

check_file() {
    if [ ! -e "$1" ]; then
        echo "  MANQUANT: $1"
        ERRORS=$((ERRORS + 1))
    else
        SIZE=$(du -sh "$1" 2>/dev/null | cut -f1)
        echo "  OK: $1 ($SIZE)"
    fi
}

check_file "$APP_BUNDLE/Contents/MacOS/telephonIA"
check_file "$APP_BUNDLE/Contents/Info.plist"
check_file "$PYTHON_BACKEND/telephonia-web"
check_file "$PYTHON_BACKEND/__boot__.py"
check_file "$PYTHON_BACKEND/lib"
check_file "$PYTHON_BACKEND/static"
check_file "$PYTHON_BACKEND/ffmpeg"
check_file "$PYTHON_BACKEND/ffprobe"

TOTAL_SIZE=$(du -sh "$APP_BUNDLE" 2>/dev/null | cut -f1)
echo ""
echo "Taille totale: $TOTAL_SIZE"

if [ "$ERRORS" -gt 0 ]; then
    echo ""
    echo "ATTENTION: $ERRORS fichier(s) manquant(s)"
    exit 1
fi

echo ""
echo "=== Build termine avec succes ==="
echo "App: $APP_BUNDLE"
echo ""
echo "Note: build semi-standalone (necessite Python 3.11 installe)"
echo "Pour creer le DMG: bash macos/create_dmg.sh"
