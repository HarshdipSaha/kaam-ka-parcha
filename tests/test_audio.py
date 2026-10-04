import io
import wave
import numpy as np
import pytest

from parcha.audio import codec_round_trip, mulaw_to_wav, mix_at_snr, AudioError


def wav_bytes(samples: np.ndarray) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(samples.astype("<i2").tobytes())
    return output.getvalue()


def test_g711_roundtrip_is_mono_8k():
    samples = (8000 * np.sin(2 * np.pi * 440 * np.arange(8000) / 8000)).astype("<i2")
    output = codec_round_trip(wav_bytes(samples), "g711")
    with wave.open(io.BytesIO(output), "rb") as wav:
        assert wav.getframerate() == 8000
        assert wav.getnchannels() == 1
        assert len(wav.readframes(8000)) == 16000


def test_amr_nb_roundtrip_is_mono_8k():
    samples = (8000 * np.sin(2 * np.pi * 440 * np.arange(8000) / 8000)).astype("<i2")
    output = codec_round_trip(wav_bytes(samples), "amr_nb_4750")
    with wave.open(io.BytesIO(output), "rb") as wav:
        assert wav.getframerate() == 8000
        assert wav.getnchannels() == 1
        assert len(wav.readframes(8000)) == 16000


def test_timbre_mulaw_decodes_as_8k():
    output = mulaw_to_wav(b"\xff" * 8000)
    with wave.open(io.BytesIO(output), "rb") as wav:
        assert wav.getframerate() == 8000
        assert len(wav.readframes(8000)) == 16000


def test_snr_is_measured_before_clipping():
    speech = wav_bytes(np.full(8000, 2000, dtype=np.int16))
    noise = wav_bytes(np.tile(np.array([-1000, 1000], dtype=np.int16), 4000))
    mixed, measured = mix_at_snr(speech, noise, 5.0)
    assert abs(measured - 5.0) < 0.5
    assert mixed.startswith(b"RIFF")


def test_clean_target_db_returns_original_audio():
    speech = wav_bytes(np.full(8000, 2000, dtype=np.int16))
    noise = wav_bytes(np.tile(np.array([-1000, 1000], dtype=np.int16), 4000))
    mixed, measured = mix_at_snr(speech, noise, float("inf"))
    assert mixed == speech
    assert measured == float("inf")


def test_noise_mix_clipped_raises_audio_error():
    speech = wav_bytes(np.full(8000, 30000, dtype=np.int16))
    noise = wav_bytes(np.full(8000, 30000, dtype=np.int16))
    with pytest.raises(AudioError, match="noise mix clipped; lower level and rerun"):
        mix_at_snr(speech, noise, 0.0)


def test_unknown_codec_raises_value_error():
    speech = wav_bytes(np.full(8000, 2000, dtype=np.int16))
    with pytest.raises(ValueError, match="Unsupported codec"):
        codec_round_trip(speech, "unsupported_codec")


def test_empty_speech_or_noise_raises_audio_error():
    empty_speech = wav_bytes(np.array([], dtype=np.int16))
    noise = wav_bytes(np.full(8000, 1000, dtype=np.int16))
    with pytest.raises(AudioError, match="non-empty"):
        mix_at_snr(empty_speech, noise, 10.0)

    speech = wav_bytes(np.full(8000, 1000, dtype=np.int16))
    empty_noise = wav_bytes(np.array([], dtype=np.int16))
    with pytest.raises(AudioError, match="non-empty"):
        mix_at_snr(speech, empty_noise, 10.0)


def test_zero_rms_raises_audio_error():
    speech = wav_bytes(np.zeros(8000, dtype=np.int16))
    noise = wav_bytes(np.full(8000, 1000, dtype=np.int16))
    with pytest.raises(AudioError, match="RMS"):
        mix_at_snr(speech, noise, 10.0)


def test_invalid_pcm_parameters_raises_audio_error():
    # 16000 Hz instead of 8000 Hz
    out16 = io.BytesIO()
    with wave.open(out16, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(np.full(16000, 2000, dtype="<i2").tobytes())

    noise = wav_bytes(np.full(8000, 1000, dtype=np.int16))
    with pytest.raises(AudioError, match="8000 Hz"):
        mix_at_snr(out16.getvalue(), noise, 10.0)
