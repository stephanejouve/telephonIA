"""Mixage audio : voix + musique de fond."""

import io
import logging

from pydub import AudioSegment

logger = logging.getLogger(__name__)

_DEFAULT_BPM = 120.0
_CHUNK_MS = 50


def _estimate_bpm(music: AudioSegment) -> float:
    """Estime le BPM par autocorrelation de l'enveloppe d'energie.

    Analyse les 30 premieres secondes en mono, decoupe en chunks de 50ms,
    calcule la force des onsets, puis cherche la periodicite dominante.
    Fallback a 120 BPM si la detection echoue.
    """
    clip = music[:30000].set_channels(1)

    # Energie par chunk (dBFS, -inf pour silence → remplace par -100)
    energies = []
    for i in range(0, len(clip) - _CHUNK_MS, _CHUNK_MS):
        chunk = clip[i : i + _CHUNK_MS]
        try:
            energies.append(chunk.dBFS)
        except Exception:
            energies.append(-100.0)

    if len(energies) < 10:
        return _DEFAULT_BPM

    # Force des onsets (variations positives d'energie)
    onsets = [max(0.0, energies[i] - energies[i - 1]) for i in range(1, len(energies))]

    # Autocorrelation : chercher le lag dominant entre 250ms (240 BPM) et 1500ms (40 BPM)
    min_lag = max(1, int(250 / _CHUNK_MS))
    max_lag = min(int(1500 / _CHUNK_MS), len(onsets) // 2)

    if max_lag <= min_lag:
        return _DEFAULT_BPM

    best_lag = min_lag
    best_corr = 0.0
    for lag in range(min_lag, max_lag):
        corr = sum(onsets[i] * onsets[i + lag] for i in range(len(onsets) - lag))
        if corr > best_corr:
            best_corr = corr
            best_lag = lag

    beat_interval_ms = best_lag * _CHUNK_MS
    bpm = 60000.0 / beat_interval_ms

    # Normaliser dans une plage raisonnable (60-180 BPM)
    while bpm < 60:
        bpm *= 2
    while bpm > 180:
        bpm /= 2

    logger.info("BPM detecte : %.0f (intervalle %.0fms)", bpm, beat_interval_ms)
    return bpm


def mix_voice_with_music(
    voice_audio: bytes,
    music_path: str,
    music_volume_db: float = -15.0,
    fade_in_ms: int = 1000,
    fade_out_ms: int = 1500,
    voice_format: str = "mp3",
) -> AudioSegment:
    """Mixe un audio voix avec une musique de fond.

    La musique demarre seule pendant 1 mesure (intro), puis la voix
    entre sur le premier temps de la 2e mesure. Apres la voix,
    1 mesure de musique seule conclut le message (outro).

    Args:
        voice_audio: Audio de la voix en bytes.
        music_path: Chemin vers le fichier musique de fond.
        music_volume_db: Ajustement du volume de la musique en dB.
        fade_in_ms: Duree du fondu d'entree de la musique en ms.
        fade_out_ms: Duree du fondu de sortie de la musique en ms.
        voice_format: Format de l'audio voix (mp3, wav, etc.).

    Returns:
        AudioSegment du mix final.

    Raises:
        FileNotFoundError: Si le fichier musique est introuvable.
    """
    voice = AudioSegment.from_file(io.BytesIO(voice_audio), format=voice_format)

    try:
        music = AudioSegment.from_file(music_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Fichier musique introuvable : {music_path}")
    except Exception as exc:
        raise FileNotFoundError(
            f"Impossible de lire le fichier musique '{music_path}' : {exc}"
        ) from exc

    # Detecter le BPM et calculer intro/outro (1 mesure = 4 temps)
    bpm = _estimate_bpm(music)
    measure_ms = int(4 * 60 / bpm * 1000)
    logger.info("Intro/outro : %dms chacun (1 mesure a %.0f BPM)", measure_ms, bpm)

    # Duree totale = intro + voix + outro
    total_duration = measure_ms + len(voice) + measure_ms

    # Boucler la musique pour couvrir la duree totale
    while len(music) < total_duration:
        music = music + music
    music = music[:total_duration]

    # Appliquer le volume et les fondus
    music = music + music_volume_db
    music = music.fade_in(fade_in_ms).fade_out(fade_out_ms)

    # Voix encadree de silence (intro + outro)
    voice_padded = (
        AudioSegment.silent(duration=measure_ms) + voice + AudioSegment.silent(duration=measure_ms)
    )

    # Superposer voix (decalee) et musique
    return voice_padded.overlay(music)


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

    Raises:
        IOError: Si l'ecriture du fichier echoue.
    """
    try:
        audio.export(output_path, format=format, bitrate=bitrate)
    except (IOError, OSError) as exc:
        raise IOError(f"Impossible d'ecrire le fichier audio '{output_path}' : {exc}") from exc
    return output_path


def export_telephony(audio: AudioSegment, output_path: str) -> str:
    """Exporte en format telephonie standard : WAV 16kHz mono 16bit.

    Args:
        audio: Segment audio a exporter.
        output_path: Chemin du fichier de sortie.

    Returns:
        Chemin du fichier exporte.

    Raises:
        IOError: Si l'ecriture du fichier echoue.
    """
    telephony_audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    try:
        telephony_audio.export(output_path, format="wav")
    except (IOError, OSError) as exc:
        raise IOError(
            f"Impossible d'exporter en format telephonie '{output_path}' : {exc}"
        ) from exc
    return output_path
