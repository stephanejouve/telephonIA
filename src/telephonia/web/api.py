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
from telephonia.generator import MESSAGES_INFO, GenerationError, SVIGenerator
from telephonia.paths import get_music_path, get_music_upload_dir, get_output_dir
from telephonia.tts_provider import create_tts_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

_VALID_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
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


class MessageUpdate(BaseModel):
    """Mise a jour du texte d'un message."""

    text: str


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
        self.messages: list[SVIMessage] = get_default_messages(music_path=self.music_path)
        self.load_saved_messages()

    def _messages_json_path(self) -> str:
        """Retourne le chemin du fichier de persistance JSON."""
        return os.path.join(self.output_dir, "messages.json")

    def save_messages(self) -> None:
        """Ecrit les textes des messages en JSON."""
        data = {msg.name: msg.text for msg in self.messages}
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
                if name in messages_by_name:
                    messages_by_name[name].text = text
                else:
                    logger.warning("Cle inconnue ignoree : %s", name)
        except (json.JSONDecodeError, PermissionError, OSError) as exc:
            logger.warning("Impossible de charger messages.json : %s", exc)

    def _wav_path(self, name: str) -> str:
        """Retourne le chemin WAV pour un nom de message."""
        return os.path.join(self.output_dir, f"{name}.wav")

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
    )


@router.post("/generate", response_model=GenerateResponse)
def generate_messages():
    """Lance la generation TTS pour tous les messages."""
    try:
        tts_provider = create_tts_provider()
        generator = SVIGenerator(
            tts=tts_provider,
            music_path=state.music_path,
            output_dir=state.output_dir,
            voice_format=tts_provider.voice_format,
        )
        results = generator.generate_all(messages=state.messages)
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

    return FileResponse(wav_path, media_type="audio/wav", filename=f"{name}.wav")


# --- Routes musique de fond ---


@router.get("/music")
def get_music_status():
    """Retourne le statut de la musique de fond."""
    music_path = get_music_path()
    return {
        "has_music": music_path is not None,
        "filename": os.path.basename(music_path) if music_path else None,
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
    logger.info("Musique de fond uploadee : %s (%d octets)", file.filename, len(content))
    return {"status": "ok", "message": "Musique uploadee"}


@router.delete("/music")
def delete_music():
    """Supprime la musique de fond uploadee."""
    upload_dir = get_music_upload_dir()
    dest = os.path.join(upload_dir, "musique_fond.mp3")
    if os.path.exists(dest):
        os.remove(dest)
        logger.info("Musique de fond supprimee")

    state.music_path = get_music_path()
    return {"status": "ok", "has_music": state.music_path is not None}
