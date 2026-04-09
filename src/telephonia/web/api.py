"""Routes REST pour le frontend telephonIA."""

import json
import logging
import os
import re
import signal

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from telephonia.config import SVIMessage, get_default_messages
from telephonia.converter import convert_g729_to_wav
from telephonia.generator import MESSAGES_INFO, GenerationError, SVIGenerator
from telephonia.mixer import export_telephony, mix_voice_with_music
from telephonia.paths import get_assets_dir, get_music_path, get_music_upload_dir, get_output_dir
from telephonia.tts_provider import create_tts_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

_VALID_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
_VALID_PREFIX_RE = re.compile(r"^[a-zA-Z0-9_-]{0,64}$")
_MAX_MUSIC_SIZE = 20 * 1024 * 1024  # 20 Mo


# --- Modeles Pydantic ---


class MessageResponse(BaseModel):
    """Reponse pour un message SVI."""

    name: str
    label: str
    description: str
    text: str
    has_music: bool
    has_audio: bool
    imported_g729: bool = False


class MessageUpdate(BaseModel):
    """Mise a jour du texte d'un message."""

    text: str


class VoiceUpdate(BaseModel):
    """Mise a jour de la voix selectionnee."""

    voice_id: str


class PrefixUpdate(BaseModel):
    """Mise a jour de l'identifiant de lot (prefixe des fichiers generes)."""

    prefix: str


class GenerateResult(BaseModel):
    """Resultat de generation d'un message."""

    name: str
    wav: str


class GenerateResponse(BaseModel):
    """Reponse de la generation TTS."""

    results: list[GenerateResult]
    status: str
    message: str = ""


# --- Etat applicatif ---


class AppState:
    """Etat en memoire de l'application."""

    def __init__(self):
        self.music_path = get_music_path()
        self.output_dir = get_output_dir()
        self.voice_id: str | None = None
        self.prefix: str = ""
        self.imported_g729: set[str] = set()
        self.messages: list[SVIMessage] = get_default_messages(music_path=self.music_path)
        self.load_saved_messages()

    def _messages_json_path(self) -> str:
        """Retourne le chemin du fichier de persistance JSON."""
        return os.path.join(self.output_dir, "messages.json")

    def save_messages(self) -> None:
        """Ecrit les textes, voix, musique et flags en JSON."""
        data = {msg.name: msg.text for msg in self.messages}
        if self.voice_id:
            data["_voice_id"] = self.voice_id
        if self.prefix:
            data["_prefix"] = self.prefix
        if self.imported_g729:
            data["_imported_g729"] = sorted(self.imported_g729)
        # Persister music_path (None = pas de musique)
        data["_music_path"] = self.music_path
        os.makedirs(self.output_dir, exist_ok=True)
        with open(self._messages_json_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_saved_messages(self) -> None:
        """Charge les textes depuis le JSON, ecrase les messages par defaut.

        Gere silencieusement : fichier absent, JSON corrompu,
        cles inconnues, erreurs de permissions.
        """
        path = self._messages_json_path()
        if not os.path.exists(path):
            return
        messages_by_name = {msg.name: msg for msg in self.messages}
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for name, text in data.items():
                if name == "_voice_id":
                    self.voice_id = text
                elif name == "_prefix":
                    if isinstance(text, str) and _VALID_PREFIX_RE.match(text):
                        self.prefix = text
                elif name == "_imported_g729":
                    self.imported_g729 = set(text) if isinstance(text, list) else set()
                elif name == "_music_path":
                    # Restaurer music_path (None = explicitement desactive)
                    if text is None:
                        self.music_path = None
                    elif isinstance(text, str) and os.path.exists(text):
                        self.music_path = text
                    else:
                        self.music_path = None
                elif name in messages_by_name:
                    messages_by_name[name].text = text
                else:
                    logger.warning("Cle inconnue ignoree : %s", name)
        except (json.JSONDecodeError, PermissionError, OSError) as exc:
            logger.warning("Impossible de charger messages.json : %s", exc)

    def _wav_filename(self, name: str) -> str:
        """Retourne le nom de fichier WAV (avec prefixe si defini)."""
        if self.prefix:
            return f"{self.prefix}_{name}.wav"
        return f"{name}.wav"

    def _wav_path(self, name: str) -> str:
        """Retourne le chemin WAV pour un nom de message."""
        return os.path.join(self.output_dir, self._wav_filename(name))

    def get_message(self, name: str) -> SVIMessage | None:
        for msg in self.messages:
            if msg.name == name:
                return msg
        return None

    def get_message_info(self, name: str) -> dict | None:
        for info in MESSAGES_INFO:
            if info["name"] == name:
                return info
        return None


state = AppState()


# --- Routes ---


@router.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}


@router.get("/voices")
def get_voices():
    """Liste les voix disponibles pour le provider TTS actif."""
    try:
        provider = create_tts_provider(voice=state.voice_id)
        voices = provider.list_voices()
        is_elevenlabs = hasattr(provider, "client")
        current = state.voice_id
        if current is None:
            current = provider.client.voice_id if is_elevenlabs else provider.voice
        return {
            "provider": "elevenlabs" if is_elevenlabs else "edge",
            "current": current,
            "voices": voices,
        }
    except Exception as exc:
        logger.error("Erreur lors de la recuperation des voix : %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/voice")
def set_voice(body: VoiceUpdate):
    """Selectionne la voix TTS a utiliser."""
    state.voice_id = body.voice_id
    state.save_messages()
    return {"status": "ok", "voice_id": state.voice_id}


@router.get("/prefix")
def get_prefix():
    """Retourne l'identifiant de lot courant."""
    return {"prefix": state.prefix}


@router.put("/prefix")
def set_prefix(body: PrefixUpdate):
    """Definit l'identifiant de lot prefixant les fichiers generes."""
    prefix = body.prefix.strip()
    if not _VALID_PREFIX_RE.match(prefix):
        raise HTTPException(
            status_code=400,
            detail="Prefixe invalide. Caracteres autorises : a-z, A-Z, 0-9, _, - (64 max)",
        )
    state.prefix = prefix
    state.save_messages()
    return {"status": "ok", "prefix": state.prefix}


@router.get("/messages", response_model=list[MessageResponse])
def get_messages():
    """Liste les 3 messages avec textes et metadata."""
    result = []
    for msg in state.messages:
        info = state.get_message_info(msg.name) or {}
        result.append(
            MessageResponse(
                name=msg.name,
                label=info.get("label", msg.name),
                description=info.get("description", ""),
                text=msg.text,
                has_music=info.get("has_music", False),
                has_audio=os.path.exists(state._wav_path(msg.name)),
                imported_g729=msg.name in state.imported_g729,
            )
        )
    return result


@router.put("/messages/{name}", response_model=MessageResponse)
def update_message(name: str, body: MessageUpdate):
    """Met a jour le texte d'un message."""
    msg = state.get_message(name)
    if msg is None:
        raise HTTPException(status_code=404, detail=f"Message '{name}' introuvable")

    msg.text = body.text
    state.save_messages()

    info = state.get_message_info(name) or {}
    return MessageResponse(
        name=msg.name,
        label=info.get("label", msg.name),
        description=info.get("description", ""),
        text=msg.text,
        has_music=info.get("has_music", False),
        has_audio=os.path.exists(state._wav_path(name)),
        imported_g729=name in state.imported_g729,
    )


@router.post("/generate", response_model=GenerateResponse)
def generate_messages():
    """Lance la generation TTS pour les messages non importes en G.729."""
    messages_to_generate = [msg for msg in state.messages if msg.name not in state.imported_g729]
    if not messages_to_generate:
        return GenerateResponse(results=[], status="ok", message="Aucun message a generer")

    try:
        tts_provider = create_tts_provider(voice=state.voice_id)
        generator = SVIGenerator(
            tts=tts_provider,
            music_path=state.music_path,
            output_dir=state.output_dir,
            voice_format=tts_provider.voice_format,
            filename_prefix=state.prefix,
        )
        results = generator.generate_all(messages=messages_to_generate)
    except GenerationError as exc:
        logger.error("Erreur generation TTS : %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": str(exc)},
        ) from exc
    except Exception as exc:
        logger.exception("Erreur inattendue lors de la generation")
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Erreur interne : {exc}"},
        ) from exc

    return GenerateResponse(
        results=[GenerateResult(name=r["name"], wav=r["wav"]) for r in results],
        status="ok",
    )


@router.post("/shutdown")
def shutdown():
    """Arrete proprement le serveur."""
    logger.info("Arret du serveur demande via /api/shutdown")
    os.kill(os.getpid(), signal.SIGINT)
    return {"status": "ok", "message": "Arret en cours..."}


@router.get("/audio/{name}")
def get_audio(name: str):
    """Sert le fichier WAV genere."""
    if not _VALID_NAME_RE.match(name):
        raise HTTPException(status_code=400, detail="Nom de message invalide")

    wav_path = state._wav_path(name)
    if not os.path.exists(wav_path):
        raise HTTPException(status_code=404, detail=f"Audio '{name}' non trouve")

    return FileResponse(
        wav_path,
        media_type="audio/wav",
        filename=state._wav_filename(name),
        headers={"Cache-Control": "no-store"},
    )


_ALLOWED_AUDIO_EXT = {
    ".mp3",
    ".wav",
    ".ogg",
    ".flac",
    ".m4a",
    ".aac",
    ".wma",
    ".g729",
}


@router.post("/audio/{name}/upload")
async def upload_audio(name: str, file: UploadFile):
    """Importe un fichier audio existant et le convertit en WAV telephonie."""
    if not _VALID_NAME_RE.match(name):
        raise HTTPException(status_code=400, detail="Nom de message invalide")

    if state.get_message(name) is None:
        raise HTTPException(status_code=404, detail=f"Message '{name}' introuvable")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_AUDIO_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporte. Extensions acceptees : "
            f"{', '.join(sorted(_ALLOWED_AUDIO_EXT))}",
        )

    content = await file.read()
    if len(content) > _MAX_MUSIC_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux (max {_MAX_MUSIC_SIZE // (1024 * 1024)} Mo)",
        )

    os.makedirs(state.output_dir, exist_ok=True)
    wav_path = state._wav_path(name)

    if ext == ".g729":
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".g729", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            convert_g729_to_wav(tmp_path, wav_path)
        except (RuntimeError, FileNotFoundError) as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de convertir le fichier G.729 : {exc}",
            ) from exc
        finally:
            os.unlink(tmp_path)
        state.imported_g729.add(name)
        state.save_messages()
    else:
        state.imported_g729.discard(name)
        state.save_messages()
        msg_info = state.get_message_info(name) or {}
        has_music = msg_info.get("has_music", False) and state.music_path

        if has_music:
            voice_format = ext.lstrip(".")  # ".mp3" → "mp3"
            try:
                mixed = mix_voice_with_music(content, state.music_path, voice_format=voice_format)
            except (FileNotFoundError, Exception) as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"Impossible de mixer l'audio : {exc}",
                ) from exc
            export_telephony(mixed, wav_path)
        else:
            import io

            from pydub import AudioSegment

            try:
                audio = AudioSegment.from_file(io.BytesIO(content))
            except Exception as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"Impossible de lire le fichier audio : {exc}",
                ) from exc
            export_telephony(audio, wav_path)

    logger.info(
        "Audio importe pour '%s' (ext=%s, %d octets, music_path=%s)",
        name,
        ext,
        len(content),
        state.music_path,
    )
    return {"status": "ok", "name": name, "ext": ext}


@router.delete("/audio/{name}")
def delete_audio(name: str):
    """Supprime le fichier WAV d'un message."""
    if not _VALID_NAME_RE.match(name):
        raise HTTPException(status_code=400, detail="Nom de message invalide")

    wav_path = state._wav_path(name)
    if not os.path.exists(wav_path):
        raise HTTPException(status_code=404, detail=f"Audio '{name}' non trouve")

    os.remove(wav_path)
    state.imported_g729.discard(name)
    state.save_messages()
    logger.info("Audio supprime pour '%s'", name)
    return {"status": "ok", "name": name}


# --- Routes musique de fond ---


@router.get("/music")
def get_music_status():
    """Retourne le statut de la musique de fond (depuis le state, pas le disque)."""
    return {
        "has_music": state.music_path is not None,
        "filename": os.path.basename(state.music_path) if state.music_path else None,
    }


@router.post("/music")
async def upload_music(file: UploadFile):
    """Upload un fichier MP3 comme musique de fond."""
    if not file.filename or not file.filename.lower().endswith(".mp3"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers MP3 sont acceptes")

    content = await file.read()
    if len(content) > _MAX_MUSIC_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux (max {_MAX_MUSIC_SIZE // (1024 * 1024)} Mo)",
        )

    upload_dir = get_music_upload_dir()
    os.makedirs(upload_dir, exist_ok=True)
    dest = os.path.join(upload_dir, "musique_fond.mp3")

    with open(dest, "wb") as f:
        f.write(content)

    state.music_path = dest
    state.save_messages()
    logger.info("Musique uploadee : %s -> %s (%d octets)", file.filename, dest, len(content))
    return {"status": "ok", "message": "Musique uploadee"}


@router.delete("/music")
def delete_music():
    """Supprime la musique de fond."""
    # Supprimer le fichier physique (best-effort dans tous les emplacements)
    for music_dir in (get_music_upload_dir(), get_assets_dir()):
        music_file = os.path.join(music_dir, "musique_fond.mp3")
        try:
            if os.path.exists(music_file):
                os.remove(music_file)
                logger.info("Musique supprimee : %s", music_file)
        except OSError as exc:
            logger.warning("Impossible de supprimer %s : %s", music_file, exc)
    state.music_path = None
    state.save_messages()
    return {"status": "ok", "has_music": False}
