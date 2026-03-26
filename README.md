# telephonIA

Generateur de bandes sonores SVI (Serveur Vocal Interactif) par IA.

Automatise la creation de messages telephoniques professionnels via l'API
ElevenLabs (text-to-speech), avec mixage musique de fond optionnel.

## Cas d'usage

Societe fictive **Les Saveurs du Terroir** (epicerie fine en ligne) avec 3 messages :

| Message | Duree | Musique |
|---------|-------|---------|
| Pre-decroche | ~10s | Non |
| Attente | ~50s | Oui (-15 dB) |
| Repondeur | ~30s | Non |

## Pre-requis

- Python >= 3.11
- [Poetry](https://python-poetry.org/)
- [ffmpeg](https://ffmpeg.org/) (utilise par pydub)
- Cle API [ElevenLabs](https://elevenlabs.io/) dans le trousseau macOS

### Installation de ffmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### Ajout de la cle API au trousseau

```bash
security add-generic-password -s "elevenlabs_api_key" -a "telephonia" -w "VOTRE_CLE_API"
```

## Installation

```bash
git clone <url-du-repo>
cd telephonIA
poetry install
```

## Utilisation

```bash
# Placer une musique de fond (optionnel)
cp votre_musique.mp3 assets/musique_fond.mp3

# Generer les messages SVI
poetry run telephonia
```

Les fichiers sont generes dans `output/` en deux formats :
- **MP3** (192 kbps) — pour ecoute et archivage
- **WAV** (16 kHz, mono, 16 bit) — format standard telephonie

## Developpement

```bash
# Tests
poetry run pytest tests/ -v

# Formatage
poetry run black src/ tests/ --line-length=100
poetry run isort src/ tests/ --profile black --line-length=100

# Lint
poetry run ruff check src/
```

## Licence

MIT
