#!/usr/bin/env python3
"""Genere les icones d'application et les favicons web pour telephonIA.

Sources attendues dans scripts/icons/sources/ :
  - TelephonIA.png       — icone d'app (combine + cerveau)
  - FAVICON_TELPHONIA.png — favicon web (combine + texte TELEPHONIA)

Outputs :
  - macos/AppIcon.icns
  - scripts/icons/telephonIA.ico       (embarque par PyInstaller)
  - frontend/public/favicon.ico        (16+32+48, source TelephonIA.png)
  - frontend/public/apple-touch-icon.png (180x180, source FAVICON pour branding)
  - frontend/public/icon-192.png        (PWA)
  - frontend/public/icon-512.png        (PWA)

Traitement :
  1. Supprime le fond blanc -> transparent (seuil tolerance blanc pur).
  2. Crop tight au bbox du contenu non-transparent.
  3. Padding carre transparent.
  4. Resize aux tailles cibles (Lanczos).

Usage depuis la racine du projet :
  poetry run python scripts/icons/generate_icons.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
SOURCES = SCRIPT_DIR / "sources"
ICONSET = SCRIPT_DIR / "AppIcon.iconset"
MACOS_OUT = PROJECT_ROOT / "macos" / "AppIcon.icns"
WIN_ICO_OUT = SCRIPT_DIR / "telephonIA.ico"
FRONTEND_PUB = PROJECT_ROOT / "frontend" / "public"

# Seuil de blanc (0-255). Les pixels RGB >= seuil sur les 3 canaux deviennent
# transparents. Les JPG exports de DALL-E / midjourney ont un blanc pas tout a
# fait pur (sRGB 253-255), donc on prend 240 pour etre permissif.
WHITE_THRESHOLD = 250


def remove_white_bg(img: Image.Image) -> Image.Image:
    """Remplace les pixels quasi-blancs par du transparent."""
    img = img.convert("RGBA")
    datas = img.getdata()
    new_data = []
    for r, g, b, a in datas:
        if r >= WHITE_THRESHOLD and g >= WHITE_THRESHOLD and b >= WHITE_THRESHOLD:
            new_data.append((r, g, b, 0))
        else:
            new_data.append((r, g, b, a))
    img.putdata(new_data)
    return img


def crop_to_content(img: Image.Image, min_ratio: float = 0.01) -> Image.Image:
    """Recadre sur le bbox du contenu non-transparent en ignorant les rangees/
    colonnes qui ne contiennent qu'une trace (< min_ratio des pixels opaques).

    Utile quand le PNG source traine un artefact 1-pixel-wide sur un bord
    (bruit de compression, residu de fond "presque blanc") : getbbox() naif
    inclut l'artefact et decale le contenu. On seuil plutot par densite.
    """
    alpha = img.split()[-1]
    w, h = img.size
    # Colonnes avec au moins min_ratio * h pixels opaques
    col_min = max(1, int(h * min_ratio))
    row_min = max(1, int(w * min_ratio))
    cols = [
        x
        for x in range(w)
        if sum(1 for y in range(h) if alpha.getpixel((x, y)) > 0) >= col_min
    ]
    rows = [
        y
        for y in range(h)
        if sum(1 for x in range(w) if alpha.getpixel((x, y)) > 0) >= row_min
    ]
    if not cols or not rows:
        raise ValueError("Image vide apres filtrage — rien a recadrer")
    return img.crop((min(cols), min(rows), max(cols) + 1, max(rows) + 1))


def make_square(img: Image.Image, padding_ratio: float = 0.05) -> Image.Image:
    """Rend l'image carree avec padding transparent. padding_ratio = marge %."""
    w, h = img.size
    side = max(w, h)
    pad = int(side * padding_ratio)
    canvas_side = side + 2 * pad
    canvas = Image.new("RGBA", (canvas_side, canvas_side), (0, 0, 0, 0))
    off_x = (canvas_side - w) // 2
    off_y = (canvas_side - h) // 2
    canvas.paste(img, (off_x, off_y), img)
    return canvas


def prepare_square_source(src_path: Path) -> Image.Image:
    """Charge, detoure, crop et rend carre."""
    img = Image.open(src_path)
    img = remove_white_bg(img)
    img = crop_to_content(img)
    img = make_square(img)
    return img


def resize(img: Image.Image, size: int) -> Image.Image:
    return img.resize((size, size), Image.Resampling.LANCZOS)


def main() -> int:
    app_src = SOURCES / "TelephonIA.png"
    fav_src = SOURCES / "FAVICON_TELPHONIA.png"
    if not app_src.exists():
        print(f"ERREUR: {app_src} introuvable", file=sys.stderr)
        return 1
    if not fav_src.exists():
        print(f"ERREUR: {fav_src} introuvable", file=sys.stderr)
        return 1

    app_master = prepare_square_source(app_src)
    fav_master = prepare_square_source(fav_src)

    # --- macOS .iconset → .icns ----------------------------------------------
    ICONSET.mkdir(parents=True, exist_ok=True)
    # Sizes required by iconutil for a compliant .icns
    iconset_specs = [
        (16, 1, "icon_16x16.png"),
        (16, 2, "icon_16x16@2x.png"),
        (32, 1, "icon_32x32.png"),
        (32, 2, "icon_32x32@2x.png"),
        (128, 1, "icon_128x128.png"),
        (128, 2, "icon_128x128@2x.png"),
        (256, 1, "icon_256x256.png"),
        (256, 2, "icon_256x256@2x.png"),
        (512, 1, "icon_512x512.png"),
        (512, 2, "icon_512x512@2x.png"),
    ]
    for base, scale, fname in iconset_specs:
        size = base * scale
        resize(app_master, size).save(ICONSET / fname, "PNG")
    MACOS_OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["iconutil", "-c", "icns", str(ICONSET), "-o", str(MACOS_OUT)],
        check=True,
    )
    print(f"  ✔ {MACOS_OUT}")

    # --- Windows .ico multi-resolution ---------------------------------------
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    app_master.save(WIN_ICO_OUT, format="ICO", sizes=ico_sizes)
    print(f"  ✔ {WIN_ICO_OUT}")

    # --- Web favicons --------------------------------------------------------
    FRONTEND_PUB.mkdir(parents=True, exist_ok=True)
    # favicon.ico → petites tailles sans texte (source app)
    (FRONTEND_PUB / "favicon.ico").unlink(missing_ok=True)
    app_master.save(
        FRONTEND_PUB / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
    )
    print(f"  ✔ {FRONTEND_PUB / 'favicon.ico'}")

    # apple-touch-icon → 180x180 avec branding texte (source favicon)
    resize(fav_master, 180).save(FRONTEND_PUB / "apple-touch-icon.png", "PNG")
    print(f"  ✔ {FRONTEND_PUB / 'apple-touch-icon.png'}")

    # PWA icons → source favicon (branding visible)
    resize(fav_master, 192).save(FRONTEND_PUB / "icon-192.png", "PNG")
    resize(fav_master, 512).save(FRONTEND_PUB / "icon-512.png", "PNG")
    print(f"  ✔ {FRONTEND_PUB / 'icon-192.png'}")
    print(f"  ✔ {FRONTEND_PUB / 'icon-512.png'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
