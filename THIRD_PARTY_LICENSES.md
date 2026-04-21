# Third-party licenses

telephonIA redistribue en l'état, dans ses bundles Windows (PyInstaller) et macOS (py2app), les binaires suivants — merci à leurs auteurs.

## ffmpeg + ffprobe

- **Source** : builds « release-essentials » de Gyan Doshi, https://www.gyan.dev/ffmpeg/builds/ (Windows) ; Homebrew `ffmpeg` formula (macOS).
- **Licence** : **LGPL-2.1** pour les builds essentials (pas de codecs non-free). Le texte complet est disponible sur https://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt.
- **Ce que nous redistribuons** : `ffmpeg.exe` + `ffprobe.exe` (Windows) et `ffmpeg` + `ffprobe` (macOS), binaires utilisés par [pydub](https://github.com/jiaaro/pydub) pour l'encodage audio et l'introspection de flux.
- **Droits utilisateur (LGPL)** : vous avez le droit de remplacer les binaires embarqués par une version que vous compilez vous-même. Dans le bundle Windows, les `.exe` se trouvent à la racine de `_MEIPASS` (dossier décompressé au lancement de l'exécutable). Dans le bundle macOS, ils sont dans `TelephonIA.app/Contents/Resources/python_backend/`.
- **Crédits** : projet ffmpeg, https://ffmpeg.org/, © 2000-present Fabrice Bellard et al.

## edge-tts, pydub, Pillow, FastAPI, Uvicorn, etc.

Les dépendances Python sont installées via Poetry et leurs licences respectives (MIT, BSD-3, Apache-2.0, LGPL selon les cas) s'appliquent. Le fichier `poetry.lock` liste les versions exactes ; l'arbre complet est visible via `poetry show --tree`.

## Rapport de bug / question licence

Ouvrir un ticket sur le repo telephonIA.
