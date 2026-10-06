import io
import wave
import numpy as np
import pytest

from parcha.audio import _read_pcm
from parcha.lab.gramvaani import downsample_16k_to_8k, source_clipped, wav16k_to_wav8k


def wav_at(samples, rate=16000):
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples.astype("<i2").tobytes())
    return out.getvalue()


def tone(hz, amp=10000, n=16000):
    return (amp * np.sin(2 * np.pi * hz * np.arange(n) / 16000)).astype("<i2")


def rms(x):
    return float(np.sqrt(np.mean(x.astype(float) ** 2)))


def test_output_is_runner_ready_8k_and_keeps_duration():
    pcm = _read_pcm(wav16k_to_wav8k(wav_at(tone(1000))))   # raises unless 8 kHz mono 16-bit
    assert len(pcm) == 8000


def test_anti_alias_removes_6khz_and_keeps_1khz():
    assert rms(downsample_16k_to_8k(tone(6000))) < 50 < 5000 < rms(downsample_16k_to_8k(tone(1000)))


def test_overshoot_is_scaled_not_clipped_and_source_clipping_is_flagged():
    square = np.where(np.sin(2 * np.pi * 300 * np.arange(16000) / 16000) >= 0, 32767, -32767).astype("<i2")
    out = np.abs(downsample_16k_to_8k(square).astype(np.int32))
    assert int(out.max()) <= 32767
    flat_top = (out[1:] >= 32767) & (out[:-1] >= 32767)   # hard clipping = runs of full-scale samples
    assert int(flat_top.sum()) == 0                       # isolated equal peaks after scaling are fine
    assert source_clipped(wav_at(square)) and not source_clipped(wav_at(tone(1000)))


def test_rejects_non_16k_input():
    with pytest.raises(ValueError, match="expected 16 kHz mono 16-bit WAV"):
        wav16k_to_wav8k(wav_at(tone(1000)[:8000], rate=8000))
