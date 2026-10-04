import asyncio
import io
import json
from pathlib import Path
import sys
import wave
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parcha.config import Settings
from parcha.credits import count_exact_amounts, drop_rate, hallucinated_word_rate, BudgetExceeded
from parcha.gnani import GnaniError
from parcha.gnani_ws import pcm_frames, silence_frames, telephony_headers, WS_URL, transcribe_telephony
import scripts.early_gates as early_gates


def create_dummy_wav(path: Path, duration_s: float = 1.0) -> Path:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        num_frames = int(8000 * duration_s)
        w.writeframes(b"\x01\x00" * num_frames)
    return path


def test_gate_denominators_are_explicit():
    assert count_exact_amounts([450, 200, 650], [450, None, 650]) == (2, 3)
    assert drop_rate(["haan", "", "nahi", ""]) == (2, 4)
    assert hallucinated_word_rate(["", "engine", "two words"]) == (3, 3)


def test_telephony_headers_redacts_and_contains_vad():
    headers = telephony_headers("test-key")
    assert headers["x-api-key-id"] == "test-key"
    assert headers["lang_code"] == "hi-IN"
    assert headers["x-sample-rate"] == "8000"
    assert headers["x-vad-threshold"] == "0.7"
    assert headers["x-min-silence-ms"] == "500"


def test_pcm_frames_and_silence_padding():
    # 8000 Hz, 1 channel, 2 bytes per sample = 16000 bytes per second
    # 1024 bytes per frame = 512 samples = 64ms per frame
    # Generate 1500 bytes of dummy PCM (should be padded to 2 chunks of 1024 bytes)
    # create a valid 8kHz 16-bit mono wav
    bio = io.BytesIO()
    with wave.open(bio, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\x01\x00" * 1000)  # 2000 bytes
    frames = pcm_frames(bio.getvalue())
    assert all(len(f) == 1024 for f in frames)
    assert len(frames) == 2  # 2000 bytes ceiling to 1024 chunks is 2 chunks

    silence = silence_frames(8000, 500)
    assert all(len(f) == 1024 for f in silence)
    assert all(f == b"\x00" * 1024 for f in silence)
    # 500ms at 64ms per frame is ceil(500/64) = 8 frames
    assert len(silence) == 8


def test_pcm_frames_validation():
    # Non-8kHz or stereo WAV should raise ValueError
    bio = io.BytesIO()
    with wave.open(bio, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 100)
    with pytest.raises(ValueError, match="mono 8 kHz"):
        pcm_frames(bio.getvalue())

    # Empty WAV should raise ValueError
    bio_empty = io.BytesIO()
    with wave.open(bio_empty, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
    with pytest.raises(ValueError, match="empty WS input"):
        pcm_frames(bio_empty.getvalue())


def test_transcribe_telephony_mock(monkeypatch):
    class FakeWebSocket:
        def __init__(self):
            self.sent_frames = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def send(self, data):
            self.sent_frames.append(data)

        async def recv(self):
            await asyncio.sleep(0.01)
            return json.dumps({"type": "transcript", "text": "हाँ"})

    fake_ws = FakeWebSocket()

    def fake_connect(url, **kwargs):
        assert url == WS_URL
        assert kwargs["additional_headers"]["x-api-key-id"] == "dummy-key"
        return fake_ws

    monkeypatch.setattr("websockets.connect", fake_connect)

    bio = io.BytesIO()
    with wave.open(bio, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\x01\x00" * 512)

    transcript, events = asyncio.run(transcribe_telephony(bio.getvalue(), "dummy-key"))
    assert transcript == "हाँ"
    assert len(events) == 1
    assert len(fake_ws.sent_frames) > 0


def test_transcribe_telephony_error_event(monkeypatch):
    class FakeWebSocketError:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def send(self, data):
            pass

        async def recv(self):
            await asyncio.sleep(0.01)
            return json.dumps({"type": "error", "message": "bad token"})

    fake_ws = FakeWebSocketError()
    monkeypatch.setattr("websockets.connect", lambda url, **kwargs: fake_ws)

    bio = io.BytesIO()
    with wave.open(bio, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\x01\x00" * 512)

    with pytest.raises(RuntimeError, match="error event"):
        asyncio.run(transcribe_telephony(bio.getvalue(), "dummy-key"))


def test_early_gates_dry_run_exits_zero(capsys):
    ret = early_gates.main(["--mode", "garage"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Pre-Flight Credit Forecast" in captured.out
    assert "garage" in captured.out
    assert "PASS" in captured.out


def test_early_gates_dry_run_with_custom_manifest(tmp_path, capsys):
    manifest = tmp_path / "custom_manifest.jsonl"
    manifest.write_text(
        json.dumps({"audio_path": "clip1.wav", "duration": 5.0, "expected_amount": 450}) + "\n" +
        json.dumps({"audio_path": "clip2.wav", "duration": 7.0, "expected_amount": 650}) + "\n",
        encoding="utf-8"
    )

    ret = early_gates.main([
        "--mode", "garage",
        "--manifest", str(manifest),
        "--max-credits", "500",
        "--credits-per-second", "0.25",
        "--remaining-credits", "1000",
    ])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Total Forecast:" in captured.out
    # 12 seconds * 0.25 = 3.0 credits
    assert "3.00 credits" in captured.out


def test_early_gates_live_fails_if_budget_exceeded(monkeypatch, tmp_path):
    manifest = tmp_path / "custom_manifest.jsonl"
    manifest.write_text(
        json.dumps({"audio_path": "clip1.wav", "duration": 100.0, "expected_amount": 450}) + "\n",
        encoding="utf-8"
    )

    monkeypatch.setenv("GNANI_API_KEY", "test-key")

    ret = early_gates.main([
        "--live",
        "--mode", "garage",
        "--manifest", str(manifest),
        "--max-credits", "5",  # 100s * 0.2 = 20 credits > 5
        "--credits-per-second", "0.2",
    ])
    assert ret == 1


def test_early_gates_live_garage_mock(monkeypatch, tmp_path):
    clip1 = create_dummy_wav(tmp_path / "c1.wav", 2.0)
    clip2 = create_dummy_wav(tmp_path / "c2.wav", 2.0)
    manifest = tmp_path / "garage_manifest.jsonl"
    manifest.write_text(
        json.dumps({"audio_path": str(clip1), "duration": 2.0, "expected_amount": 450}) + "\n" +
        json.dumps({"audio_path": str(clip2), "duration": 2.0, "expected_amount": 650}) + "\n",
        encoding="utf-8"
    )
    out_file = tmp_path / "results.jsonl"

    class FakePrisma:
        def __init__(self, key, base_url=""):
            pass

        def transcribe(self, wav, mode, bias=None, score=1.0):
            return "कुल 450 रुपये हुआ"

    monkeypatch.setenv("GNANI_API_KEY", "test-key")
    monkeypatch.setattr(early_gates, "PrismaClient", FakePrisma)

    ret = early_gates.main([
        "--live",
        "--mode", "garage",
        "--manifest", str(manifest),
        "--output", str(out_file),
    ])
    assert ret == 0
    assert out_file.exists()
    lines = [json.loads(line) for line in out_file.read_text(encoding="utf-8").splitlines() if line]
    summary = lines[0]
    assert summary["type"] == "summary"
    assert summary["mode"] == "garage"
    assert summary["numerator"] == 1  # 450 matches, 650 predicted as 450 doesn't match
    assert summary["denominator"] == 2
    assert summary["passed"] is False  # 1/2 = 50% < 70% threshold


def test_early_gates_live_stops_on_403(monkeypatch, tmp_path):
    clip1 = create_dummy_wav(tmp_path / "c1.wav", 1.0)
    clip2 = create_dummy_wav(tmp_path / "c2.wav", 1.0)
    manifest = tmp_path / "garage_manifest.jsonl"
    manifest.write_text(
        json.dumps({"audio_path": str(clip1), "duration": 1.0, "expected_amount": 450}) + "\n" +
        json.dumps({"audio_path": str(clip2), "duration": 1.0, "expected_amount": 650}) + "\n",
        encoding="utf-8"
    )
    out_file = tmp_path / "results.jsonl"

    class FailingPrisma:
        def __init__(self, key, base_url=""):
            pass

        def transcribe(self, wav, mode, bias=None, score=1.0):
            raise GnaniError("Gnani request failed: HTTP 403 Forbidden")

    monkeypatch.setenv("GNANI_API_KEY", "test-key")
    monkeypatch.setattr(early_gates, "PrismaClient", FailingPrisma)

    ret = early_gates.main([
        "--live",
        "--mode", "garage",
        "--manifest", str(manifest),
        "--output", str(out_file),
    ])
    assert ret == 0  # Completed with halted results written
    lines = [json.loads(line) for line in out_file.read_text(encoding="utf-8").splitlines() if line]
    summary = lines[0]
    assert "GnaniError" in summary["halt_reason"]
    # Only 1 item attempted before break
    item_lines = [l for l in lines if l.get("type") == "item"]
    assert len(item_lines) == 1
    assert item_lines[0]["status"] == "halted"


def test_early_gates_live_short_replies_mock(monkeypatch, tmp_path):
    clip1 = create_dummy_wav(tmp_path / "s1.wav", 1.0)
    clip2 = create_dummy_wav(tmp_path / "e1.wav", 1.0)
    manifest = tmp_path / "short_manifest.jsonl"
    manifest.write_text(
        json.dumps({"audio_path": str(clip1), "duration": 1.0, "clip_type": "speech"}) + "\n" +
        json.dumps({"audio_path": str(clip2), "duration": 1.0, "clip_type": "engine"}) + "\n",
        encoding="utf-8"
    )
    out_file = tmp_path / "results.jsonl"

    class FakePrisma:
        def __init__(self, key, base_url=""):
            pass

        def transcribe(self, wav, mode, bias=None, score=1.0):
            return "हाँ"

    monkeypatch.setenv("GNANI_API_KEY", "test-key")
    monkeypatch.setattr(early_gates, "PrismaClient", FakePrisma)

    ret = early_gates.main([
        "--live",
        "--mode", "short-replies",
        "--manifest", str(manifest),
        "--output", str(out_file),
    ])
    assert ret == 0
    lines = [json.loads(line) for line in out_file.read_text(encoding="utf-8").splitlines() if line]
    summary = lines[0]
    assert summary["mode"] == "short-replies"
    assert summary["dropped"] == 0
    assert summary["speech_total"] == 1
    assert summary["hallucinated_words"] == 1
    assert summary["engine_total"] == 1
    assert summary["passed"] is True  # drop 0 <= 10%, hallucination 1.0 <= 1.0
