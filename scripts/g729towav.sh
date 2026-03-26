#!/bin/bash
# Convertisseur G.729 -> WAV telephonie (16kHz mono 16bit)
# Usage :
#   ./g729towav.sh fichier.g729                  # un fichier
#   ./g729towav.sh fichier.g729 sortie.wav       # un fichier, nom personnalise
#   ./g729towav.sh *.g729                        # batch (tous les .g729)

set -e

if [ $# -eq 0 ]; then
    echo "Usage : $0 <fichier.g729> [sortie.wav]"
    echo "        $0 *.g729  (conversion batch)"
    exit 1
fi

if ! command -v ffmpeg &>/dev/null; then
    echo "Erreur : ffmpeg non trouve."
    echo "  macOS  : brew install ffmpeg"
    echo "  Windows: winget install ffmpeg"
    echo "  Linux  : sudo apt-get install ffmpeg"
    exit 1
fi

# Un seul fichier avec sortie personnalisee
if [ $# -eq 2 ] && [[ "$1" == *.g729* ]]; then
    echo "Conversion : $1 -> $2"
    ffmpeg -y -i "$1" -ar 16000 -ac 1 -sample_fmt s16 "$2" 2>/dev/null
    echo "  OK ($(du -h "$2" | cut -f1))"
    exit 0
fi

# Un ou plusieurs fichiers
COUNT=0
for f in "$@"; do
    if [[ ! "$f" == *.g729* ]]; then
        echo "  [SKIP] $f (pas un fichier G.729)"
        continue
    fi
    if [ ! -f "$f" ]; then
        echo "  [ERREUR] $f introuvable"
        continue
    fi

    OUT="${f%.*}.wav"
    echo -n "  $f -> $OUT ... "
    if ffmpeg -y -i "$f" -ar 16000 -ac 1 -sample_fmt s16 "$OUT" 2>/dev/null; then
        echo "OK ($(du -h "$OUT" | cut -f1))"
        COUNT=$((COUNT + 1))
    else
        echo "ERREUR"
    fi
done

echo ""
echo "$COUNT fichier(s) converti(s)."
