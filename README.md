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
- Cle API [ElevenLabs](https://elevenlabs.io/) dans le trousseau systeme

### Installation de ffmpeg

```bash
# macOS
brew install ffmpeg

# Windows
winget install ffmpeg
# ou : choco install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### Ajout de la cle API au trousseau

La cle est stockee via [keyring](https://pypi.org/project/keyring/) (multiplateforme) :
- **macOS** : Trousseau d'acces (Keychain)
- **Windows** : Credential Manager
- **Linux** : Secret Service (GNOME Keyring / KWallet)

```bash
# Methode universelle (macOS / Windows / Linux)
keyring set elevenlabs_api_key telephonia

# Ou via Python
python -c "import keyring; keyring.set_password('elevenlabs_api_key', 'telephonia', 'VOTRE_CLE')"
```

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

Le CLI propose deux modes :
1. **Textes par defaut** — messages pre-configures (Les Saveurs du Terroir)
2. **Saisie manuelle** — formulaire interactif pour saisir les 3 textes

### Musique de fond

Placer un fichier MP3 dans `assets/musique_fond.mp3`. Il sera mixe
automatiquement avec le message d'attente a -15 dB.

Sources de musiques libres de droits recommandees :

| Site | Recherche suggeree |
|------|--------------------|
| [pixabay.com/music](https://pixabay.com/music/) | "corporate background", "hold music" |
| [incompetech.com](https://incompetech.com/) | Musiques de Kevin MacLeod |
| [mixkit.co/free-music](https://mixkit.co/free-music/) | Filtre par mood |
| [freemusicarchive.org](https://freemusicarchive.org/) | Catalogue pro |

Privilegier une musique **neutre, sans voix, sans rythme trop marque** (2-3 min
minimum, le script la boucle automatiquement si elle est trop courte).

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

## Convertisseur G.729 -> WAV

Outil integre pour convertir des fichiers G.729 (VoIP) en WAV telephonie.

```bash
# Via Python (multiplateforme — macOS / Windows / Linux)
poetry run g729towav

# Via script shell (macOS / Linux uniquement)
./scripts/g729towav.sh fichier.g729              # un fichier
./scripts/g729towav.sh *.g729                    # batch
```

Le CLI Python propose la conversion unitaire ou batch (dossier entier).
Sortie : WAV 16 kHz, mono, 16 bits.

## Configuration des messages

Les textes par defaut sont dans `src/telephonia/config.py`.
Pour une saisie ponctuelle, utiliser le mode 2 (saisie manuelle) du CLI.

## Voix

Voix par defaut : **Charlotte** (ElevenLabs, francais).
Pour changer de voix, modifier `voice_id` dans `generator.py`.

Voix FR recommandees : Charlotte, Mathieu.

## Licence

MIT
