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
security add-generic-password -l "elevenlabs_api_key" -a "telephonia" -s "elevenlabs_api_key" -w "VOTRE_CLE_API"
```

La cle est lue via `security find-generic-password -l "elevenlabs_api_key" -w`.

## Installation

```bash
git clone https://github.com/stephanejouve/telephonIA.git
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

Les fichiers sont generes dans `output/` au format standard telephonie :
- **WAV** — LPCM16 @ 16 kHz, mono, 16 bit (< 8 Mo, < 2 min)

## Format de sortie

Le format WAV produit est directement compatible avec les serveurs SVI :

| Spec | Valeur |
|------|--------|
| Format | WAV (LPCM) |
| Frequence | 16 000 Hz |
| Canaux | Mono |
| Resolution | 16 bits |
| Poids max | < 8 Mo |
| Duree max | < 2 min |

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

## Configuration des messages

Les textes SVI sont definis dans `src/telephonia/config.py`. Pour les modifier :

1. Editer `get_default_messages()` dans `config.py`
2. Relancer `poetry run telephonia`

Chaque message est un `SVIMessage` avec :
- `name` — identifiant du fichier de sortie
- `text` — texte a synthetiser
- `target_duration` — duree cible (secondes)
- `background_music` — chemin musique de fond (optionnel)
- `music_volume_db` — volume musique en dB (defaut: -15)

## Voix

Voix par defaut : **Charlotte** (ElevenLabs, francais).
Pour changer de voix, modifier `voice_id` dans `generator.py`.

Voix FR recommandees : Charlotte, Mathieu.

## Licence

MIT
