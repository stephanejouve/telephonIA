"""Configuration des messages SVI (Serveur Vocal Interactif)."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SVIMessage:
    """Definition d'un message SVI.

    Args:
        name: Identifiant du message (ex: "pre_decroche").
        text: Texte a synthetiser en voix.
        target_duration: Duree cible en secondes.
        background_music: Chemin vers le fichier musique de fond (None = sans musique).
        music_volume_db: Volume de la musique en dB relatif (ex: -15).
    """

    name: str
    text: str
    target_duration: int
    background_music: Optional[str] = None
    music_volume_db: float = -15.0


def get_default_messages(music_path: Optional[str] = None) -> list[SVIMessage]:
    """Retourne les 3 messages par defaut pour 'Les Saveurs du Terroir'.

    Args:
        music_path: Chemin vers le fichier musique de fond pour le message d'attente.

    Returns:
        Liste des 3 messages SVI.
    """
    return [
        SVIMessage(
            name="pre_decroche",
            text=(
                "Les Saveurs du Terroir, epicerie fine en ligne. "
                "Nous allons donner suite a votre appel."
            ),
            target_duration=10,
            background_music=music_path,
            music_volume_db=-15.0,
        ),
        SVIMessage(
            name="attente",
            text=(
                "Bienvenue chez Les Saveurs du Terroir, votre epicerie fine en ligne. "
                "Nous selectionnons pour vous les meilleurs produits de nos regions. "
                "Profitez en ce moment de notre coffret decouverte du Massif Central "
                "a 49,99 euros, une selection de fromages, charcuteries et miels "
                "d'exception livree chez vous sous 48 heures. "
                "Un conseiller va prendre votre appel."
            ),
            target_duration=50,
            background_music=music_path,
            music_volume_db=-15.0,
        ),
        SVIMessage(
            name="repondeur",
            text=(
                "Vous etes bien chez Les Saveurs du Terroir, epicerie fine en ligne. "
                "Nos conseillers sont disponibles du lundi au vendredi "
                "de 9 heures a 12 heures 30 et de 14 heures a 18 heures, "
                "et le samedi de 10 heures a 13 heures. "
                "Veuillez nous laisser un message avec vos coordonnees, "
                "nous vous rappellerons dans les plus brefs delais."
            ),
            target_duration=30,
            background_music=music_path,
            music_volume_db=-15.0,
        ),
    ]
