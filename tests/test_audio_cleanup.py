import io
import shutil
import wave

import numpy as np
import pytest

from parcha.audio import normalize_upload
from parcha.config import Settings

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is needed")


def rumbling_wav(rate: int = 16000) -> bytes:
    """One second of 60 Hz engine rumble under a 1 kHz tone."""
    t = np.arange(rate) / rate
    pcm = (0.5 * np.sin(2 * np.pi * 60 * t) + 0.2 * np.sin(2 * np.pi * 1000 * t)) * 32767
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.astype("<i2").tobytes())
    return buf.getvalue()


def rumble_energy(wav: bytes) -> float:
    with wave.open(io.BytesIO(wav)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float)
    spectrum = np.abs(np.fft.rfft(x))
    return float(spectrum[55:66].sum() / spectrum.sum())   # share of energy near 60 Hz (1 Hz bins for one second)


def test_cleanup_removes_low_rumble_and_keeps_a_valid_wav():
    raw = rumbling_wav()
    plain = normalize_upload(raw, "audio/wav")
    cleaned = normalize_upload(raw, "audio/wav", cleanup=True)
    with wave.open(io.BytesIO(cleaned)) as w:
        assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (16000, 1, 2)
    assert rumble_energy(cleaned) < 0.5 * rumble_energy(plain)   # a measured ~4x drop on this signal; not a recognition claim


def test_cleanup_is_off_unless_asked():
    assert Settings().audio_cleanup is False
    assert Settings.from_mapping({"AUDIO_CLEANUP": "1"}).audio_cleanup is True


def silent_wav(seconds: float, rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x01\x00" * int(rate * seconds))
    return buf.getvalue()


def test_recordings_for_prisma_are_refused_at_thirty_seconds_with_a_clear_message():
    from parcha.audio import AudioError, stt_normalizer

    normalize = stt_normalizer()
    assert normalize(silent_wav(5), "audio/wav")
    with pytest.raises(AudioError, match=r"outside bounds \[0.3s, 29.5s\]"):
        normalize(silent_wav(31), "audio/wav")
    assert normalize_upload(silent_wav(31), "audio/wav")   # the general helper keeps its 60 s bound
