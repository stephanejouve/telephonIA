# telephonIA

[![GitHub Release](https://img.shields.io/github/v/release/stephanejouve/telephonIA)](https://github.com/stephanejouve/telephonIA/releases/latest)
[![CI](https://github.com/stephanejouve/telephonIA/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/stephanejouve/telephonIA/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/stephanejouve/telephonIA/branch/main/graph/badge.svg)](https://codecov.io/gh/stephanejouve/telephonIA)
[![SLSA](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)

> Les exécutables publiés sur les Releases GitHub sont signés via une
> [attestation SLSA](https://slsa.dev) (GitHub + Sigstore). Vérification
> côté utilisateur : `gh attestation verify telephonIA-*.exe --repo stephanejouve/telephonIA`.

Generateur de bandes sonores SVI (Serveur Vocal Interactif) par IA.

Automatise la creation de messages telephoniques professionnels via
text-to-speech (ElevenLabs ou Edge TTS), avec mixage musique de fond,
import audio existant et conversion G.729.

## Fonctionnalites

- **Interface web** — editeur de textes, lecteur audio, selecteur de voix,
  gestion de la musique de fond, import de fichiers audio existants
- **Double moteur TTS** — ElevenLabs (premium) ou Microsoft Edge TTS (gratuit,
  aucune cle requise)
- **Mixage intelligent** — intro et outro musicales d'une mesure (BPM detecte
  automatiquement), voix superposee a la musique de fond
- **Import audio** — importer un enregistrement existant (MP3, WAV, OGG, FLAC,
  M4A, AAC, WMA) avec mixage musique de fond automatique, ou un fichier G.729
  (conversion directe sans mixage)
- **Format telephonie** — sortie WAV LPCM 16 kHz, mono, 16 bits, compatible
  avec tous les serveurs SVI
- **Convertisseur G.729** — outil CLI dedie pour convertir des fichiers VoIP
  G.729 en WAV telephonie (unitaire ou batch)

## Les 3 messages SVI

| Message | Description | Musique |
|---------|-------------|---------|
| Pre-decroche | Court message d'accueil a la prise d'appel | Optionnelle |
| Attente | Message diffuse pendant la mise en attente | Optionnelle |
| Repondeur | Message du repondeur (hors horaires) | Optionnelle |

Des textes par defaut sont fournis (societe fictive *Les Saveurs du Terroir*)
et sont editables depuis l'interface web ou le CLI.

## Pre-requis

- Python >= 3.11
- [Poetry](https://python-poetry.org/)
- [ffmpeg](https://ffmpeg.org/) (utilise par pydub)

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

### Cle API ElevenLabs (optionnel)

Sans cle, telephonIA utilise **Edge TTS** (gratuit, voix Microsoft).
Pour utiliser ElevenLabs (voix premium), ajouter la cle au trousseau systeme :

```bash
# Methode universelle (macOS / Windows / Linux)
keyring set elevenlabs_api_key telephonia

# Ou via Python
python -c "import keyring; keyring.set_password('elevenlabs_api_key', 'telephonia', 'VOTRE_CLE')"
```

```powershell
# Windows PowerShell (Credential Manager natif)
cmdkey /generic:elevenlabs_api_key /user:telephonia /pass:VOTRE_CLE
```

Le trousseau utilise [keyring](https://pypi.org/project/keyring/) :
- **macOS** : Trousseau d'acces (Keychain)
- **Windows** : Credential Manager
- **Linux** : Secret Service (GNOME Keyring / KWallet)

## Installation

```bash
git clone https://github.com/stephanejouve/telephonIA.git
cd telephonIA
poetry install
```

Un executable Windows (`.exe`) est disponible dans les
[releases GitHub](https://github.com/stephanejouve/telephonIA/releases/latest).

## Utilisation

### Interface web (recommande)

```bash
poetry run telephonia-web
```

Le navigateur s'ouvre automatiquement. L'interface affiche :
- les 3 messages avec editeur de texte
- le selecteur de voix TTS
- le lecteur audio pour chaque message genere
- le bouton de generation TTS
- l'upload/suppression de musique de fond
- l'import de fichiers audio existants (avec mixage) ou G.729 (conversion directe)
- le telechargement des fichiers WAV generes

L'URL LAN est affichee dans la console pour un acces depuis un autre poste du
reseau local.

### CLI

```bash
# Generer les messages SVI
poetry run telephonia
```

Le CLI propose deux modes :
1. **Textes par defaut** — messages pre-configures
2. **Saisie manuelle** — formulaire interactif pour saisir les 3 textes

### Import audio existant

Depuis l'interface web, le bouton **Importer audio** sur chaque carte de
message permet d'importer un enregistrement existant :

- **Formats audio** (MP3, WAV, OGG, FLAC, M4A, AAC, WMA) — le fichier est
  converti au format telephonie et **mixe avec la musique de fond** si elle est
  active. Utile quand on prefere une voix enregistree au TTS tout en conservant
  le mixage musical.
- **Fichiers G.729** (.g729) — conversion directe via ffmpeg, **sans mixage**.
  Le fichier G.729 remplace integralement l'audio du message.

### Musique de fond

La musique peut etre geree depuis l'interface web (upload/suppression) ou
placee manuellement dans `assets/musique_fond.mp3`.

Le mixage ajoute automatiquement :
- **Intro** : 1 mesure de musique seule (duree calculee selon le BPM detecte)
- **Corps** : voix superposee a la musique (volume musique : -15 dB)
- **Outro** : 1 mesure de musique seule

La musique est bouclée automatiquement si elle est plus courte que le message.

Sources de musiques libres de droits :

| Site | Recherche suggeree |
|------|--------------------|
| [pixabay.com/music](https://pixabay.com/music/) | "corporate background", "hold music" |
| [incompetech.com](https://incompetech.com/) | Musiques de Kevin MacLeod |
| [mixkit.co/free-music](https://mixkit.co/free-music/) | Filtre par mood |
| [freemusicarchive.org](https://freemusicarchive.org/) | Catalogue pro |

Privilegier une musique **neutre, sans voix, sans rythme trop marque** (2-3 min
minimum).

## Convertisseur G.729

Outil CLI dedie pour convertir des fichiers G.729 (VoIP) en WAV telephonie :

```bash
# Via Python (multiplateforme)
poetry run g729towav

# Via script shell (macOS / Linux)
./scripts/g729towav.sh fichier.g729              # un fichier
./scripts/g729towav.sh *.g729                    # batch
```

Le CLI propose la conversion unitaire ou batch (dossier entier).

## Format de sortie

Tous les fichiers generes sont au format standard telephonie :

| Spec | Valeur |
|------|--------|
| Format | WAV (LPCM) |
| Frequence | 16 000 Hz |
| Canaux | Mono |
| Resolution | 16 bits |

Les fichiers sont generes dans `output/` (ou `%LOCALAPPDATA%/telephonIA/output`
sous Windows avec l'executable).

## Voix

### Edge TTS (gratuit — par defaut)

Voix par defaut : **Denise** (`fr-FR-DeniseNeural`).
Le selecteur de voix dans l'interface web liste toutes les voix francaises
disponibles.

### ElevenLabs (premium)

Voix par defaut : **Denise** (`XB0fDUnXU5powFXDhCwa`).
Le selecteur de voix liste toutes les voix du compte ElevenLabs.

> **Note** : si le selecteur de voix est vide, verifier qu'aucun VPN ou proxy
> d'entreprise ne bloque l'acces aux serveurs Microsoft (Edge TTS) ou
> ElevenLabs.

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
