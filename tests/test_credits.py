from pathlib import Path
import sys
import wave
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parcha.config import Settings
from parcha.credits import CreditPlan, BudgetExceeded
import scripts.probe_api as probe_api


def create_dummy_wav(path: Path, duration_seconds: float, sample_rate: int = 8000) -> Path:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        num_frames = int(sample_rate * duration_seconds)
        wf.writeframes(b"\x00\x00" * num_frames)
    return path


def test_grid_calculation_includes_reserve():
    plan = CreditPlan(
        credits_per_stt_second=0.2,
        remaining_credits=5000,
        clips=100,
        codecs=3,
        snrs=3,
        seconds_per_clip=6,
        intake_seconds=60,
        reply_seconds=300,
        tts_credits=100,
    )
    assert plan.grid_credits == 1080
    assert plan.total_credits == 1252
    plan.require_under_cap(2000)


def test_overspend_fails_before_first_api_call():
    plan = CreditPlan(
        credits_per_stt_second=1,
        remaining_credits=5000,
        clips=100,
        codecs=3,
        snrs=3,
        seconds_per_clip=6,
    )
    with pytest.raises(BudgetExceeded):
        plan.require_under_cap(2000)


def test_probe_api_requires_live_flag(tmp_path):
    clip = create_dummy_wav(tmp_path / "valid.wav", 5.0)
    exit_code = probe_api.main(["--clip", str(clip)])
    assert exit_code == 1


def test_probe_api_rejects_short_clip(tmp_path):
    clip = create_dummy_wav(tmp_path / "short.wav", 3.0)
    with pytest.raises(ValueError, match="outside required range"):
        probe_api.validate_clip_duration(clip)

    exit_code = probe_api.main(["--live", "--clip", str(clip)])
    assert exit_code == 1


def test_probe_api_rejects_long_clip(tmp_path):
    clip = create_dummy_wav(tmp_path / "long.wav", 9.0)
    with pytest.raises(ValueError, match="outside required range"):
        probe_api.validate_clip_duration(clip)

    exit_code = probe_api.main(["--live", "--clip", str(clip)])
    assert exit_code == 1


def test_probe_api_accepts_valid_duration(tmp_path):
    clip = create_dummy_wav(tmp_path / "valid.wav", 5.5)
    duration = probe_api.validate_clip_duration(clip)
    assert duration == pytest.approx(5.5)


def test_probe_api_mock_run(monkeypatch, tmp_path):
    clip = create_dummy_wav(tmp_path / "valid.wav", 6.0)

    class FakePrisma:
        def __init__(self, key, base_url=""):
            pass

        def transcribe(self, wav, mode):
            return "परीक्षण"

    class FakeTimbre:
        def __init__(self, key, voice="", base_url=""):
            pass

        def synthesize(self, text):
            return b"fake-audio"

    monkeypatch.setattr(probe_api, "PrismaClient", FakePrisma)
    monkeypatch.setattr(probe_api, "TimbreClient", FakeTimbre)

    settings = Settings(api_key="valid-key")
    result = probe_api.run_probe(
        clip,
        initial_balance=100.0,
        mid_balance=98.8,
        final_balance=98.0,
        settings=settings,
    )
    assert result["duration"] == 6.0
    assert result["stt_delta"] == pytest.approx(1.2)
    assert result["credits_per_second"] == pytest.approx(0.2)
    assert result["tts_delta"] == pytest.approx(0.8)
    assert result["total_delta"] == pytest.approx(2.0)
