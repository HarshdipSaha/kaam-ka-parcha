from __future__ import annotations

import hashlib
import hmac
import base64

import httpx
import pytest
from fastapi.testclient import TestClient

from parcha import telephony
from parcha.app import AppServices, create_app


# ---- TwiML builders ---------------------------------------------------------------------

def test_twiml_wraps_body_in_a_response_envelope():
    body = telephony.say("namaste") + telephony.hangup()
    xml = telephony.twiml(body)
    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?><Response>')
    assert xml.endswith("</Response>")
    assert "<Say" in xml and "<Hangup/>" in xml


def test_say_escapes_text_and_sets_language():
    xml = telephony.say("Tom & Jerry's <estimate>", language="hi-IN")
    assert 'language="hi-IN"' in xml
    assert "&amp;" in xml and "&lt;estimate&gt;" in xml and "<estimate>" not in xml


def test_record_has_a_beep_and_trims_silence():
    xml = telephony.record("https://example.com/action?x=1&y=2", max_length=15, timeout=3)
    assert 'maxLength="15"' in xml and 'timeout="3"' in xml and 'playBeep="true"' in xml
    assert "x=1&amp;y=2" in xml  # the action URL is escaped too


# ---- Signature validation ----------------------------------------------------------------

def test_signature_matches_twilio_pythons_own_test_vector():
    # twilio/twilio-python tests/unit/test_request_validator.py — verified against the official SDK (2026-10-07).
    token = "12345"
    url = "https://mycompany.com/myapp.php?foo=1&bar=2"
    params = {
        "CallSid": "CA1234567890ABCDE",
        "Digits": "1234",
        "From": "+14158675309",
        "To": "+18005551212",
        "Caller": "+14158675309",
    }
    expected = "RSOYDt4T1cUTdK1PDd93/VVr8B8="
    assert telephony.signature_valid(token, url, params, expected)
    assert not telephony.signature_valid(token, url, params, "RSOYDt4T1cUTdK1PDd93/VVr8B9=")
    assert not telephony.signature_valid(token, url, {**params, "Digits": "9999"}, expected)


def test_signature_rejects_a_missing_token_or_signature():
    assert not telephony.signature_valid("", "https://x", {}, "sig")
    assert not telephony.signature_valid("token", "https://x", {}, None)
    assert not telephony.signature_valid("token", "https://x", {}, "")


def _sign(token: str, url: str, params: dict) -> str:
    base = url + "".join(f"{k}{v}" for k, v in sorted(params.items()))
    return base64.b64encode(hmac.new(token.encode(), base.encode(), hashlib.sha1).digest()).decode()


# ---- place_call / download_recording (unit, mocked transport) ---------------------------

def test_place_call_posts_the_documented_fields_and_returns_the_sid():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["authorization"]
        seen["body"] = dict(p.split("=") for p in request.content.decode().split("&"))
        return httpx.Response(201, json={"sid": "CA_new"})

    http = httpx.Client(transport=httpx.MockTransport(handler))
    sid = telephony.place_call(
        account_sid="AC_x", auth_token="tok", to="%2B919999999999", from_="%2B15550001234",
        voice_url="https%3A%2F%2Fexample.com%2Fv", http=http,
    )
    assert sid == "CA_new"
    assert "Basic" in seen["auth"]


def test_place_call_raises_on_an_error_response():
    http = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(400, text="bad request")))
    with pytest.raises(telephony.TwilioError, match="400"):
        telephony.place_call(account_sid="AC", auth_token="t", to="+1", from_="+1", voice_url="https://x", http=http)


def test_download_recording_appends_wav_and_authenticates():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        return httpx.Response(200, content=b"RIFFfakeaudio")

    http = httpx.Client(transport=httpx.MockTransport(handler))
    blob = telephony.download_recording(
        account_sid="AC", auth_token="tok", recording_url="https://api.twilio.com/.../RE123", http=http
    )
    assert blob == b"RIFFfakeaudio"
    assert seen["url"].endswith("RE123.wav") and "Basic" in seen["auth"]


# ---- App routes --------------------------------------------------------------------------

def _ready_session(client: TestClient) -> tuple[str, int]:
    """Intake, then settle both flagged amounts with a deliberate repeat each — mirrors
    test_app.py::test_customer_reply_endpoint_confirms_session."""
    sid = client.post("/sessions").json()["id"]
    client.post(f"/sessions/{sid}/intake", data={"expected_revision": 0}, files={"audio": ("a.wav", b"x", "audio/wav")})
    client.post(f"/sessions/{sid}/reask/items.part-1.amount_paise", data={"expected_revision": 1}, files={"audio": ("p.wav", b"x", "audio/wav")})
    r = client.post(f"/sessions/{sid}/reask/items.labour-1.amount_paise", data={"expected_revision": 2}, files={"audio": ("l.wav", b"x", "audio/wav")})
    assert r.status_code == 200 and r.json()["review_fields"] == []
    return sid, r.json()["revision"]


def test_place_call_endpoint_validates_number_and_card_readiness(fake_services):
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]

    bad_number = client.post(f"/sessions/{sid}/telephony/call", data={"expected_revision": 0, "to_number": "9876543210"})
    assert bad_number.status_code == 422

    not_ready = client.post(f"/sessions/{sid}/telephony/call", data={"expected_revision": 0, "to_number": "+919876543210"})
    assert not_ready.status_code == 409  # no card yet


def test_place_call_endpoint_dials_out_once_the_card_is_ready(fake_services):
    calls = []
    fake_services.place_call = lambda **kw: calls.append(kw) or "CA_fake_sid"
    client = TestClient(create_app(fake_services))
    sid, rev = _ready_session(client)

    res = client.post(f"/sessions/{sid}/telephony/call", data={"expected_revision": rev, "to_number": "+919876543210"})
    assert res.status_code == 200 and res.json() == {"call_sid": "CA_fake_sid"}
    assert calls[0]["to"] == "+919876543210" and f"session_id={sid}" in calls[0]["voice_url"]


def _twilio_post(client: TestClient, path: str, query: str, form: dict):
    url = f"https://test.example{path}?{query}" if query else f"https://test.example{path}"
    sig = _sign("test-twilio-token", url, form)
    return client.post(f"{path}?{query}" if query else path, data=form, headers={"X-Twilio-Signature": sig})


def test_voice_webhook_rejects_an_unsigned_or_tampered_request(fake_services):
    client = TestClient(create_app(fake_services))
    sid, rev = _ready_session(client)
    r = client.post(f"/telephony/twilio/voice?session_id={sid}&revision={rev}")
    assert r.status_code == 403
    r = client.post(f"/telephony/twilio/voice?session_id={sid}&revision={rev}", headers={"X-Twilio-Signature": "wrong"})
    assert r.status_code == 403


def test_voice_webhook_plays_the_readback_and_records_a_reply(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    client = TestClient(create_app(fake_services))
    sid, rev = _ready_session(client)
    r = _twilio_post(client, "/telephony/twilio/voice", f"session_id={sid}&revision={rev}&language=hi-IN", {})
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/xml")
    assert "<Play>" in r.text and "readback.wav" in r.text and "<Record" in r.text

    # The <Play> URL must actually be fetchable — a real Twilio call failed with "an application error has
    # occurred" because this earlier returned 404 (the voice webhook built the readback but never saved the
    # WAV to disk; only the browser-facing /sessions/{id}/readback route did that).
    import re
    play_url = re.search(r"<Play>(.*?)</Play>", r.text).group(1).replace("&amp;", "&")
    audio_path = play_url.removeprefix("https://test.example")
    audio = client.get(audio_path)
    assert audio.status_code == 200 and audio.headers["content-type"] == "audio/wav" and len(audio.content) > 0


def test_voice_webhook_apologizes_when_the_card_still_needs_review(fake_services):
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    r = _twilio_post(client, "/telephony/twilio/voice", f"session_id={sid}&revision=0&language=hi-IN", {})
    assert r.status_code == 200 and "<Hangup/>" in r.text and "<Play>" not in r.text


def test_recording_webhook_confirms_on_a_clear_yes_and_hangs_up(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    client = TestClient(create_app(fake_services))
    sid, rev = _ready_session(client)
    rb = client.post(f"/sessions/{sid}/readback", data={"expected_revision": rev})
    rev, readback_rev = rb.json()["revision"], rb.json()["readback_revision"]

    fake_services.workflow.prisma.transcribe = lambda wav, mode, **kw: "हाँ ठीक है"
    fake_services.download_recording = lambda **kw: b"fake-recording-bytes"
    query = f"session_id={sid}&expected_revision={rev}&readback_revision={readback_rev}&language=hi-IN"
    r = _twilio_post(client, "/telephony/twilio/recording", query, {"RecordingUrl": "https://api.twilio.com/REC1"})
    assert r.status_code == 200 and "<Hangup/>" in r.text and "<Redirect" not in r.text
    assert client.get(f"/sessions/{sid}").json()["status"] == "confirmed"


def test_recording_webhook_redirects_back_to_voice_after_a_correction(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    client = TestClient(create_app(fake_services))
    sid, rev = _ready_session(client)
    rb = client.post(f"/sessions/{sid}/readback", data={"expected_revision": rev})
    rev, readback_rev = rb.json()["revision"], rb.json()["readback_revision"]

    fake_services.workflow.prisma.transcribe = lambda wav, mode, **kw: "nahi, rear brake pad"
    fake_services.download_recording = lambda **kw: b"fake-recording-bytes"
    query = f"session_id={sid}&expected_revision={rev}&readback_revision={readback_rev}&language=hi-IN"
    r = _twilio_post(client, "/telephony/twilio/recording", query, {"RecordingUrl": "https://api.twilio.com/REC2"})
    assert r.status_code == 200
    assert "<Redirect" in r.text and "/telephony/twilio/voice" in r.text


def test_recording_webhook_handles_an_empty_recording_by_asking_again(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    client = TestClient(create_app(fake_services))
    sid, rev = _ready_session(client)
    rb = client.post(f"/sessions/{sid}/readback", data={"expected_revision": rev})
    rev, readback_rev = rb.json()["revision"], rb.json()["readback_revision"]

    query = f"session_id={sid}&expected_revision={rev}&readback_revision={readback_rev}&language=hi-IN"
    r = _twilio_post(client, "/telephony/twilio/recording", query, {})  # Twilio posts no RecordingUrl
    assert r.status_code == 200 and "<Record" in r.text and "<Hangup/>" not in r.text


def test_status_webhook_accepts_signed_posts_and_204s(fake_services):
    client = TestClient(create_app(fake_services))
    r = _twilio_post(client, "/telephony/twilio/status", "", {"CallStatus": "completed"})
    assert r.status_code == 204


def test_demo_access_code_never_gates_twilio_webhooks(fake_services):
    from dataclasses import replace

    fake_services.workflow.timbre = fake_services.timbre
    services = AppServices(
        replace(fake_services.settings, demo_access_code="secret"),
        fake_services.store, fake_services.workflow, fake_services.timbre,
    )
    client = TestClient(create_app(services))
    gate = client.post("/gate", data={"code": "secret"}, follow_redirects=False)  # logs in once, as a person would
    assert gate.status_code == 303
    sid, rev = _ready_session(client)

    unauth_client = TestClient(create_app(services))  # a fresh client, no cookie, no code
    r = _twilio_post(unauth_client, "/telephony/twilio/voice", f"session_id={sid}&revision={rev}", {})
    assert r.status_code == 200 and "<Play>" in r.text  # the Twilio path only needs its own signature
