"""Gramvaani real-telephone slice: Vistaar test parquet -> 8 kHz mono WAVs + Line Noise Lab manifest rows.
Evaluation only; audio and reference text stay in ignored var/.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import wave

import numpy as np

SOURCE_DATASET = "Trelis/vistaar-hi-gramvaani-test"
SOURCE_LICENSE = "gramvaani-asr-2022: academic use; commercial use by permission (contact@gramvaani.org)"
_TAPS = 63


def _lowpass_taps(cutoff_ratio: float = 0.45) -> np.ndarray:
    """Windowed-sinc low-pass; cutoff as a fraction of the output Nyquist (8 kHz output -> 3.6 kHz)."""
    n = np.arange(_TAPS) - (_TAPS - 1) / 2
    taps = np.sinc(cutoff_ratio * n) * np.hamming(_TAPS)
    return taps / taps.sum()


def downsample_16k_to_8k(samples: np.ndarray) -> np.ndarray:
    """Factor-2 decimation after anti-alias filtering; never upsamples. Overshoot scales the clip, never clips."""
    decimated = np.convolve(samples.astype(np.float64), _lowpass_taps(), mode="same")[::2]
    peak = float(np.max(np.abs(decimated))) if len(decimated) else 0.0
    if peak > 32767:
        decimated *= 32767 / peak
    return np.rint(decimated).astype("<i2")


def source_clipped(blob: bytes) -> bool:
    """True when the 16 kHz source already has full-scale samples (authentic IVR clipping: 291/1,032 clips)."""
    with wave.open(io.BytesIO(blob)) as w:
        s = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    return bool(len(s)) and int(np.max(np.abs(s.astype(np.int32)))) >= 32767


def wav16k_to_wav8k(blob: bytes) -> bytes:
    with wave.open(io.BytesIO(blob)) as w:
        if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (16000, 1, 2):
            raise ValueError("expected 16 kHz mono 16-bit WAV")
        samples = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(downsample_16k_to_8k(samples).tobytes())
    return out.getvalue()


def prepare(parquet_path: Path, audio_dir: Path) -> list[dict]:
    """Write g0001.wav … and return Clip-compatible manifest rows."""
    import pyarrow.parquet as pq

    table = pq.read_table(parquet_path)
    audio_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for k, (audio, text) in enumerate(zip(table.column("audio").to_pylist(), table.column("text").to_pylist()), 1):
        clip_id = f"g{k:04d}"
        wav8k = wav16k_to_wav8k(audio["bytes"])
        (audio_dir / f"{clip_id}.wav").write_bytes(wav8k)
        rows.append({
            "id": clip_id,
            "text": text,
            "reference_transcribe": text,
            "entities": {},
            "audio": f"{clip_id}.wav",
            "kind": "speech",
            "seed": 0,
            "source": "open_dataset",
            "source_dataset": SOURCE_DATASET,
            "source_license": SOURCE_LICENSE,
            "source_row": audio["path"],
            "stratum": "gramvaani_clipped" if source_clipped(audio["bytes"]) else "gramvaani_unclipped",
            "reference_type": "dataset_reference",
            "audio_sha256": hashlib.sha256(wav8k).hexdigest(),
        })
    return rows
