from __future__ import annotations

from datetime import datetime, timezone
import json

from fastapi.testclient import TestClient
import httpx
import pytest

from parcha.app import create_app
from parcha.gnani import PrismaClient, TimbreClient
from parcha.languages import LANGUAGES, pack_for, supported_codes
from parcha.readback import classify_reply, make_readback
from parcha.session import SessionStore
from parcha.workflow import Workflow
from tests.conftest import FakeExtractor, make_test_card

ACCEPT = {"ta-IN": ["ஆமா", "ஆமா சரி", "ஆமாம், சரி", "ஆம்"], "bn-IN": ["হ্যাঁ", "হ্যাঁ, ঠিক আছে", "হ্যাঁ ঠিক আছে।"],
          "kn-IN": ["ಹೌದು", "ಹೌದು, ಸರಿ"]}
REJECT = {"ta-IN": ["இல்லை", "ஆமா இல்லை", "சரி இல்ல"], "bn-IN": ["না", "হ্যাঁ না", "ঠিক নেই না"],
          "kn-IN": ["ಇಲ್ಲ", "ಹೌದು ಬೇಡ"]}
UNCLEAR = {"ta-IN": ["", "சரி", "ஆமா ஆனால் இருநூறு", "haan theek hai"], "bn-IN": ["ঠিক আছে", "হ্যাঁ কিন্তু দাম বেশি"],
           "kn-IN": ["ಸರಿ", "ಹೌದು ಆದರೆ ಬೆಲೆ ಜಾಸ್ತಿ", "haan"]}


def test_supported_codes_and_unknown_language():
    assert supported_codes() == ("hi-IN", "ta-IN", "bn-IN", "kn-IN")
    assert pack_for("hi-IN") is None and pack_for(None) is None
    with pytest.raises(ValueError):
        pack_for("fr-FR")


@pytest.mark.parametrize("code", ["ta-IN", "bn-IN", "kn-IN"])
def test_regional_readback_uses_fixed_strings_and_digit_amounts(code):
    pack = LANGUAGES[code]
    text = make_readback(make_test_card(), include_consent=True, language=code)
    assert text.startswith(pack.consent_notice)
    assert "₹450" in text and "₹200" in text and f"{pack.total_word} ₹650" in text      # digits, never words
    assert pack.delivery_word in text and "5/10/2026" in text and pack.windows["evening"] in text
    assert text.endswith(pack.closing_prompt)
    assert make_readback(make_test_card(), language=code, include_consent=False).startswith("front brake pad:")


def test_hindi_readback_is_unchanged_by_the_language_parameter():
    card = make_test_card()
    assert make_readback(card, include_consent=True) == make_readback(card, include_consent=True, language="hi-IN")
    assert "कुल" in make_readback(card)


@pytest.mark.parametrize("code", ["ta-IN", "bn-IN", "kn-IN"])
def test_reply_classification_per_language(code):
    for phrase in ACCEPT[code]:
        assert classify_reply(phrase, code) == "accept", phrase
    for phrase in REJECT[code]:
        assert classify_reply(phrase, code) == "reject", phrase       # negation always wins, even after a yes
    for phrase in UNCLEAR[code]:
        assert classify_reply(phrase, code) == "unclear", phrase
    assert classify_reply("haan theek hai", code) == "unclear"       # a Hindi yes is not a regional yes
    assert classify_reply("haan theek hai") == "accept"              # and the Hindi default is untouched


class LangPrisma:
    def __init__(self, transcript):
        self.transcript, self.calls = transcript, []

    def transcribe(self, wav, *, mode, bias=None, score=1.0, language_code="hi-IN"):
        self.calls.append(language_code)
        return self.transcript


class LangTimbre:
    def __init__(self):
        self.calls = []

    def synthesize(self, text, *, language="hi-IN", voice=None):
        self.calls.append((language, voice))
        return b"RIFFfakeaudio"


def workflow_for(transcript, **kwargs):
    store = SessionStore()
    sid = store.create().id
    store.set_card(sid, expected_revision=0, card=make_test_card())
    wf = Workflow(store=store, prisma=LangPrisma(transcript), extractor=FakeExtractor(), timbre=LangTimbre(),
                  normalize_audio=lambda blob, mime, sample_rate=8000: b"RIFFpcm", **kwargs)
    return wf, store, sid


def test_regional_readback_picks_language_and_voice_and_logs_it():
    wf, store, sid = workflow_for("ஆமா சரி", language_voices={"ta-IN": "Trisha"})
    readback = wf.start_readback(sid, expected_revision=1, language="ta-IN")
    assert wf.timbre.calls == [("ta-IN", "Trisha")]
    assert LANGUAGES["ta-IN"].closing_prompt in readback.text
    session = store.get(sid)
    assert [log.text for log in session.logs if log.mode == "readback_language"] == ["ta-IN"]
    assert session.status == "awaiting_reply" and session.revision == 1 and session.readback_revision == 1


def test_default_voice_comes_from_the_pack():
    wf, _, sid = workflow_for("ஆமா")
    wf.start_readback(sid, expected_revision=1, language="kn-IN")
    assert wf.timbre.calls == [("kn-IN", LANGUAGES["kn-IN"].voices[0])]


def test_tamil_customer_confirms_by_voice_end_to_end():
    wf, store, sid = workflow_for("ஆமா சரி")
    wf.start_readback(sid, expected_revision=1, language="ta-IN")
    result = wf.reply(sid, b"audio", "audio/webm", expected_revision=1, readback_revision=1,
                      recorded_at_utc=datetime(2026, 10, 7, tzinfo=timezone.utc))
    assert result.outcome == "confirmed" and result.session.status == "confirmed"
    assert wf.prisma.calls == ["ta-IN"]                              # the reply was recognised as Tamil


def test_regional_negation_retries_and_never_confirms():
    wf, store, sid = workflow_for("இல்லை")
    wf.start_readback(sid, expected_revision=1, language="ta-IN")
    result = wf.reply(sid, b"audio", "audio/webm", expected_revision=1, readback_revision=1)
    assert result.outcome == "retry" and store.get(sid).status == "awaiting_reply"


def test_hindi_flow_never_sends_a_language_override(monkeypatch):
    wf, store, sid = workflow_for("haan theek hai")
    wf.start_readback(sid, expected_revision=1)
    assert wf.timbre.calls == [("hi-IN", None)]                  # a plain synthesize(text) call
    result = wf.reply(sid, b"audio", "audio/webm", expected_revision=1, readback_revision=1)
    assert result.outcome == "confirmed" and wf.prisma.calls == ["hi-IN"]


def test_clients_send_the_requested_language_and_voice():
    seen = []

    def handler(request):
        seen.append(request)
        if request.url.path == "/stt/v3":
            return httpx.Response(200, json={"success": True, "transcript": "ஆமா"})
        return httpx.Response(200, content=b"\xff" * 800)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    PrismaClient("k", http=http).transcribe(b"RIFF", mode="transcribe", language_code="ta-IN")
    TimbreClient("k", http=http).synthesize("மொத்தம் ₹650", language="ta-IN", voice="Brinda")
    assert b'name="language_code"\r\n\r\nta-IN' in seen[0].content
    body = json.loads(seen[1].content)
    assert (body["language"], body["voice"]) == ("ta-IN", "Brinda")
    TimbreClient("k", voice="Vikrant", http=http).synthesize("कुल ₹650")
    assert json.loads(seen[2].content)["language"] == "hi-IN" and json.loads(seen[2].content)["voice"] == "Vikrant"


def test_route_rejects_an_unsupported_language(fake_services):
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    res = client.post(f"/sessions/{sid}/readback", data={"expected_revision": 0, "language": "fr-FR"})
    assert res.status_code == 422
