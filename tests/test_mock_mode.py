import io
import math
import shutil
import struct
import wave

from fastapi.testclient import TestClient
import pytest

from parcha.app import create_app, default_services

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is needed to normalise audio")


def tiny_wav() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(i / 20))) for i in range(16000)))
    return buf.getvalue()


def test_mock_mode_runs_a_whole_parcha_with_no_keys(monkeypatch):
    for name in ("API_KEY", "EXTRACTOR_BASE_URL", "EXTRACTOR_MODEL", "EXTRACTOR_API_KEY"):
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("PARCHA_MOCK", "1")
    client = TestClient(create_app(default_services()))

    sid = client.post("/sessions").json()["id"]
    assert client.post(f"/sessions/{sid}/consent", data={"expected_revision": 0, "granted": "true"}).status_code == 200
    rev = client.get(f"/sessions/{sid}").json()["revision"]
    card = client.post(f"/sessions/{sid}/intake", data={"expected_revision": rev}, files={"audio": ("a.wav", tiny_wav(), "audio/wav")})
    assert card.status_code == 200 and card.json()["total_paise"] is None   # amounts wait for a second agreeing recording

    second = client.post(f"/sessions/{sid}/confirm-estimate", data={"expected_revision": card.json()["revision"]},
                         files={"audio": ("b.wav", tiny_wav(), "audio/wav")})
    assert second.status_code == 200 and second.json()["total_paise"] == 65000 and second.json()["review_fields"] == []

    rev = second.json()["revision"]
    rb = client.post(f"/sessions/{sid}/readback", data={"expected_revision": rev})
    assert rb.status_code == 200
    reply = client.post(
        f"/sessions/{sid}/reply",
        data={"expected_revision": rb.json()["revision"], "readback_revision": rb.json()["readback_revision"]},
        files={"audio": ("r.wav", tiny_wav(), "audio/wav")},
    )
    assert reply.status_code == 200 and reply.json()["outcome"] == "confirmed"
    assert client.get(f"/sessions/{sid}/pdf").headers["content-type"] == "application/pdf"
    assert "₹650" in client.get(f"/sessions/{sid}/whatsapp.txt").text


def test_mock_is_off_by_default():
    from parcha.config import Settings

    assert Settings().mock is False and Settings.from_mapping({}).mock is False
    assert Settings.from_mapping({"PARCHA_MOCK": "1"}).mock is True
