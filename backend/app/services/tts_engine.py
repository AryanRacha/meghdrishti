"""Server-side text-to-speech for public warnings in all 12 supported languages.

Browsers (notably Brave and Firefox) ship few or no Indian-language voices, so the
dashboard asks the backend for audio instead of relying on `speechSynthesis`.

- 9 languages use Microsoft neural voices via `edge-tts` (online, MP3).
- Assamese, Punjabi and Odia have no edge voice and use Meta MMS-TTS (local VITS, WAV).
"""

import io
import logging
import re
import threading
from collections import OrderedDict
from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.io import wavfile

logger = logging.getLogger(__name__)

TtsLang = Literal["en", "hi", "mr", "bn", "as", "ta", "te", "kn", "ml", "gu", "pa", "or"]

EDGE_VOICES: dict[str, str] = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "mr": "mr-IN-AarohiNeural",
    "bn": "bn-IN-TanishaaNeural",
    "ta": "ta-IN-PallaviNeural",
    "te": "te-IN-ShrutiNeural",
    "kn": "kn-IN-SapnaNeural",
    "ml": "ml-IN-SobhanaNeural",
    "gu": "gu-IN-DhwaniNeural",
}

MMS_MODELS: dict[str, str] = {"as": "facebook/mms-tts-asm", "pa": "facebook/mms-tts-pan", "or": "facebook/mms-tts-ory"}

# MMS vocabularies contain no digits: read numbers digit by digit (correct for helplines)
DIGIT_WORDS: dict[str, list[str]] = {
    "as": ["শূন্য", "এক", "দুই", "তিনি", "চাৰি", "পাঁচ", "ছয়", "সাত", "আঠ", "ন"],
    "pa": ["ਸਿਫ਼ਰ", "ਇੱਕ", "ਦੋ", "ਤਿੰਨ", "ਚਾਰ", "ਪੰਜ", "ਛੇ", "ਸੱਤ", "ਅੱਠ", "ਨੌਂ"],
    "or": ["ଶୂନ", "ଏକ", "ଦୁଇ", "ତିନି", "ଚାରି", "ପାଞ୍ଚ", "ଛଅ", "ସାତ", "ଆଠ", "ନଅ"],
}

# Abbreviations MMS would spell out letter by letter, and the warning's fixed "24 hours"
MMS_EXPANSIONS: dict[str, dict[str, str]] = {
    "as": {"মি.মি.": "মিলিমিটাৰ", "কি.মি.": "কিলোমিটাৰ", "°C": " ডিগ্ৰী চেলছিয়াছ", "24 ঘণ্টা": "চৌবিশ ঘণ্টা"},
    "pa": {"ਮਿ.ਮੀ.": "ਮਿਲੀਮੀਟਰ", "ਕਿ.ਮੀ.": "ਕਿਲੋਮੀਟਰ", "°C": " ਡਿਗਰੀ ਸੈਲਸੀਅਸ", "24 ਘੰਟ": "ਚੌਵੀ ਘੰਟ"},
    "or": {"ମି.ମି.": "ମିଲିମିଟର", "କି.ମି.": "କିଲୋମିଟର", "°C": " ଡିଗ୍ରୀ ସେଲସିୟସ", "24 ଘଣ୍ଟା": "ଚବିଶ ଘଣ୍ଟା"},
}

CACHE_SIZE = 64


@dataclass(frozen=True)
class Speech:
    audio: bytes
    media_type: str


def normalize_for_mms(text: str, lang: str) -> str:
    for short, full in MMS_EXPANSIONS[lang].items():
        text = text.replace(short, full)
    words = DIGIT_WORDS[lang]
    text = re.sub(r"\d+", lambda m: " ".join(words[int(d)] for d in m.group()), text)
    return re.sub(r"\s+", " ", text).strip()


class TtsEngine:
    """Synthesizes speech; MMS models load lazily and results are LRU-cached."""

    def __init__(self) -> None:
        self._models: dict[str, tuple[object, object]] = {}
        # transformers patches torch tensor creation while loading, so loading and inference
        # must never overlap (concurrent use fails with "narrow(): length must be non-negative")
        self._torch_lock = threading.RLock()
        self._cache: OrderedDict[tuple[str, str], Speech] = OrderedDict()

    async def synthesize(self, text: str, lang: TtsLang) -> Speech:
        key = (lang, text)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        if lang in EDGE_VOICES:
            speech = await self._edge(text, EDGE_VOICES[lang])
        else:
            from starlette.concurrency import run_in_threadpool

            speech = await run_in_threadpool(self._mms, text, lang)

        self._cache[key] = speech
        if len(self._cache) > CACHE_SIZE:
            self._cache.popitem(last=False)
        return speech

    @staticmethod
    async def _edge(text: str, voice: str) -> Speech:
        import edge_tts

        chunks: list[bytes] = []
        async for part in edge_tts.Communicate(text, voice, rate="-5%").stream():
            if part["type"] == "audio":
                chunks.append(part["data"])
        if not chunks:
            raise RuntimeError(f"edge-tts returned no audio for voice {voice}")
        return Speech(b"".join(chunks), "audio/mpeg")

    def _mms(self, text: str, lang: str) -> Speech:
        import torch

        with self._torch_lock:
            tokenizer, model = self._load_mms(lang)
            inputs = tokenizer(normalize_for_mms(text, lang), return_tensors="pt")  # type: ignore[operator]
            with torch.no_grad():
                waveform = model(**inputs).waveform[0].numpy()  # type: ignore[operator]
        buffer = io.BytesIO()
        pcm = (np.clip(waveform, -1.0, 1.0) * 32767).astype(np.int16)
        wavfile.write(buffer, model.config.sampling_rate, pcm)  # type: ignore[attr-defined]
        return Speech(buffer.getvalue(), "audio/wav")

    def warm_up(self) -> None:
        """Load cached MMS models at startup (blocking, cache only) so the first warning plays at once.

        Runs before requests are served because model loading must not overlap any torch inference,
        including the forecast U-Net. Uncached models download on first use instead.
        """
        for lang in MMS_MODELS:
            try:
                self._load_mms(lang, local_only=True)
            except Exception:
                logger.info("TTS model for %s not cached; it will download on first use", lang)

    def _load_mms(self, lang: str, local_only: bool = False) -> tuple[object, object]:
        with self._torch_lock:
            if lang not in self._models:
                from transformers import AutoTokenizer, VitsModel

                name = MMS_MODELS[lang]
                logger.info("Loading TTS model %s", name)
                tokenizer = AutoTokenizer.from_pretrained(name, local_files_only=local_only)
                model = VitsModel.from_pretrained(name, local_files_only=local_only).eval()
                self._models[lang] = (tokenizer, model)
            return self._models[lang]


tts_engine = TtsEngine()
