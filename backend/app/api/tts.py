import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.tts_engine import TtsLang, tts_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["tts"])


class TtsRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    lang: TtsLang


@router.post("", response_class=Response, responses={200: {"content": {"audio/mpeg": {}, "audio/wav": {}}}})
async def synthesize(req: TtsRequest) -> Response:
    """Spoken audio for a public warning (MP3 or WAV depending on the language)."""
    try:
        speech = await tts_engine.synthesize(req.text, req.lang)
    except Exception as exc:
        logger.warning("TTS failed for %s: %s", req.lang, exc)
        raise HTTPException(status_code=503, detail="Speech synthesis unavailable") from exc
    return Response(content=speech.audio, media_type=speech.media_type, headers={"Cache-Control": "no-store"})
