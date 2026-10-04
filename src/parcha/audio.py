from __future__ import annotations

import io
import math
import subprocess
import wave

import numpy as np


class AudioError(RuntimeError):
    """Raised when an audio operation fails or inputs are invalid."""


ALLOWED_UPLOAD_MIMES = {
    "audio/webm",
    "audio/ogg",
    "audio/mp4",
    "audio/wav",
    "audio/x-wav",
}


def normalize_upload(blob: bytes, mime: str, sample_rate: int = 16000) -> bytes:
    """Normalize uploaded audio blob to 16-bit mono WAV at target sample rate."""
    clean_mime = mime.split(";")[0].strip().lower()
    if clean_mime not in ALLOWED_UPLOAD_MIMES:
        raise AudioError(f"unsupported audio mime type: {clean_mime}")

    if not blob or len(blob) > 8 * 1024 * 1024:
        raise AudioError("recording must be non-empty and under 8MB")

    out_wav = _ffmpeg(
        blob,
        [],
        ["-ar", str(sample_rate), "-ac", "1", "-c:a", "pcm_s16le", "-f", "wav"],
    )

    try:
        with wave.open(io.BytesIO(out_wav), "rb") as w:
            if w.getsampwidth() != 2:
                raise AudioError(f"Expected 16-bit PCM (2 bytes per sample), got {w.getsampwidth()} bytes")
            if w.getframerate() != sample_rate:
                raise AudioError(f"Expected {sample_rate} Hz sample rate, got {w.getframerate()} Hz")
            frames = w.readframes(w.getnframes())
    except wave.Error as exc:
        raise AudioError(f"Failed to read WAV data: {exc}") from exc
    except EOFError as exc:
        raise AudioError(f"Truncated WAV data: {exc}") from exc

    duration = len(frames) / (2 * sample_rate)
    if not (0.3 <= duration <= 60.0):
        raise AudioError(f"audio duration {duration:.2f}s outside bounds [0.3s, 60s]")

    return out_wav


def _ffmpeg(input_bytes: bytes, input_args: list[str], output_args: list[str]) -> bytes:
    """Run an FFmpeg conversion using stdin/stdout pipes."""
    cmd = ["ffmpeg", "-y", "-nostdin", *input_args, "-i", "pipe:0", *output_args, "pipe:1"]
    try:
        res = subprocess.run(
            cmd,
            input=input_bytes,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise AudioError("FFmpeg command timed out after 30s") from exc
    except FileNotFoundError as exc:
        raise AudioError("FFmpeg executable not found in PATH") from exc

    if res.returncode != 0:
        stderr = res.stderr.decode(errors="replace")
        raise AudioError(f"FFmpeg failed with exit code {res.returncode}: {stderr}")
    return res.stdout


def mulaw_to_wav(data: bytes) -> bytes:
    """Convert raw 8 kHz 8-bit mono mu-law audio to standard 16-bit mono 8 kHz WAV."""
    return _ffmpeg(
        data,
        ["-f", "mulaw", "-ar", "8000", "-ac", "1"],
        ["-acodec", "pcm_s16le", "-ar", "8000", "-ac", "1", "-f", "wav"],
    )


def codec_round_trip(wav: bytes, codec: str) -> bytes:
    """Perform a codec encode and decode round-trip on 8 kHz mono WAV audio."""
    if codec == "g711":
        mulaw = _ffmpeg(
            wav,
            [],
            ["-acodec", "pcm_mulaw", "-ar", "8000", "-ac", "1", "-f", "mulaw"],
        )
        return mulaw_to_wav(mulaw)
    elif codec == "amr_nb_4750":
        amr = _ffmpeg(
            wav,
            [],
            ["-acodec", "libopencore_amrnb", "-b:a", "4.75k", "-ar", "8000", "-ac", "1", "-f", "amr"],
        )
        return _ffmpeg(
            amr,
            ["-f", "amr"],
            ["-acodec", "pcm_s16le", "-ar", "8000", "-ac", "1", "-f", "wav"],
        )
    else:
        raise ValueError(f"Unsupported codec: {codec}")


def _read_pcm(blob: bytes) -> np.ndarray:
    """Read a 16-bit mono 8000 Hz WAV blob into a 1D int16 NumPy array."""
    try:
        with wave.open(io.BytesIO(blob), "rb") as wav:
            if wav.getnchannels() != 1:
                raise AudioError(f"Expected mono audio (1 channel), got {wav.getnchannels()} channels")
            if wav.getframerate() != 8000:
                raise AudioError(f"Expected 8000 Hz sample rate, got {wav.getframerate()} Hz")
            if wav.getsampwidth() != 2:
                raise AudioError(f"Expected 16-bit PCM (2 bytes per sample), got {wav.getsampwidth()} bytes")
            raw = wav.readframes(wav.getnframes())
    except wave.Error as exc:
        raise AudioError(f"Failed to read WAV data: {exc}") from exc
    except EOFError as exc:
        raise AudioError(f"Truncated WAV data: {exc}") from exc

    return np.frombuffer(raw, dtype="<i2")


def _write_pcm(samples: np.ndarray) -> bytes:
    """Write a 1D int16 NumPy array to 16-bit mono 8000 Hz WAV format."""
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(samples.astype("<i2").tobytes())
    return output.getvalue()


def mix_at_snr(speech_wav: bytes, noise_wav: bytes, target_db: float | None) -> tuple[bytes, float]:
    """Mix speech and noise WAV audio at a specified Signal-to-Noise Ratio (dB)."""
    speech_pcm = _read_pcm(speech_wav)
    noise_pcm = _read_pcm(noise_wav)

    if len(speech_pcm) == 0:
        raise AudioError("Speech audio must be non-empty")
    if len(noise_pcm) == 0:
        raise AudioError("Noise audio must be non-empty")

    if target_db is None or target_db == float("inf"):
        return speech_wav, float("inf")

    # Resize/tile noise to match speech length
    if len(noise_pcm) < len(speech_pcm):
        repeats = int(np.ceil(len(speech_pcm) / len(noise_pcm)))
        noise_pcm = np.tile(noise_pcm, repeats)[: len(speech_pcm)]
    else:
        noise_pcm = noise_pcm[: len(speech_pcm)]

    speech_f = speech_pcm.astype(np.float64)
    noise_f = noise_pcm.astype(np.float64)

    speech_rms = float(np.sqrt(np.mean(speech_f ** 2)))
    noise_rms = float(np.sqrt(np.mean(noise_f ** 2)))

    if speech_rms <= 0.0 or noise_rms <= 0.0:
        raise AudioError("Speech and noise RMS must be greater than zero")

    scaled = noise_f * (speech_rms / (noise_rms * (10.0 ** (target_db / 20.0))))
    mixed = speech_f + scaled

    if np.max(np.abs(mixed)) >= 32767:
        raise AudioError("noise mix clipped; lower level and rerun")

    scaled_rms = float(np.sqrt(np.mean(scaled ** 2)))
    measured_snr = 20.0 * math.log10(speech_rms / scaled_rms)

    mixed_pcm = np.rint(mixed).astype("<i2")
    return _write_pcm(mixed_pcm), measured_snr
