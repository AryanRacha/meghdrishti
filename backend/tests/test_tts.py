from fastapi.testclient import TestClient

from app.main import app
from app.services.tts_engine import EDGE_VOICES, MMS_MODELS, normalize_for_mms

client = TestClient(app)


def test_all_twelve_languages_have_a_voice() -> None:
    assert len(EDGE_VOICES.keys() | MMS_MODELS.keys()) == 12


def test_mms_normalizer_spells_digits_and_units() -> None:
    assert normalize_for_mms("112 ମି.ମି.", "or") == "ଏକ ଏକ ଦୁଇ ମିଲିମିଟର"
    # Native-script digits are not in the MMS vocabulary either
    assert normalize_for_mms("੨ 30", "pa") == "ਦੋ ਤਿੰਨ ਸਿਫ਼ਰ"


def test_rejects_unsupported_language() -> None:
    assert client.post("/api/v1/tts", json={"text": "hello", "lang": "fr"}).status_code == 422


def test_rejects_empty_text() -> None:
    assert client.post("/api/v1/tts", json={"text": "", "lang": "en"}).status_code == 422
