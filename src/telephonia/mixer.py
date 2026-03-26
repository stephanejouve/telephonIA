"""Mixage audio : voix + musique de fond."""

import io

from pydub import AudioSegment


def mix_voice_with_music(
    voice_audio: bytes,
    music_path: str,
    music_volume_db: float = -15.0,
    fade_in_ms: int = 1000,
    fade_out_ms: int = 1500,
    voice_format: str = "mp3",
) -> AudioSegment:
    """Mixe un audio voix avec une musique de fond.

    La musique est bouclée si nécessaire pour couvrir la durée de la voix,
    puis superposée avec le volume spécifié.

    Args:
        voice_audio: Audio de la voix en bytes.
        music_path: Chemin vers le fichier musique de fond.
        music_volume_db: Ajustement du volume de la musique en dB.
        fade_in_ms: Durée du fondu d'entrée de la musique en ms.
        fade_out_ms: Durée du fondu de sortie de la musique en ms.
        voice_format: Format de l'audio voix (mp3, wav, etc.).

    Returns:
        AudioSegment du mix final.
    """
    voice = AudioSegment.from_file(io.BytesIO(voice_audio), format=voice_format)
    music = AudioSegment.from_file(music_path)

    # Boucler la musique si elle est plus courte que la voix
    voice_duration = len(voice)
    while len(music) < voice_duration:
        music = music + music

    # Couper la musique a la duree de la voix
    music = music[:voice_duration]

    # Appliquer le volume et les fondus
    music = music + music_volume_db
    music = music.fade_in(fade_in_ms).fade_out(fade_out_ms)

    # Superposer voix et musique
    return voice.overlay(music)


def export_audio(
    audio: AudioSegment,
    output_path: str,
    format: str = "mp3",
    bitrate: str = "192k",
) -> str:
    """Exporte un AudioSegment vers un fichier.

    Args:
        audio: Segment audio a exporter.
        output_path: Chemin du fichier de sortie.
        format: Format de sortie (mp3, wav, etc.).
        bitrate: Bitrate pour l'encodage (MP3).

    Returns:
        Chemin du fichier exporte.
    """
    audio.export(output_path, format=format, bitrate=bitrate)
    return output_path


def export_telephony(audio: AudioSegment, output_path: str) -> str:
    """Exporte en format telephonie standard : WAV 16kHz mono 16bit.

    Args:
        audio: Segment audio a exporter.
        output_path: Chemin du fichier de sortie.

    Returns:
        Chemin du fichier exporte.
    """
    telephony_audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    telephony_audio.export(output_path, format="wav")
    return output_path
