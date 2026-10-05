"""Deterministic transient workshop-noise generators for lab evaluation."""

from __future__ import annotations

import numpy as np

from parcha.audio import _read_pcm, _write_pcm

IMPULSE_PROFILES = ("impact_wrench", "metal_spanner", "compressor_exhaust")


def _burst(length: int, sample_rate: int, profile: str, rng: np.random.Generator) -> np.ndarray:
    time = np.arange(length, dtype=np.float64) / sample_rate
    if profile == "impact_wrench":
        carrier = np.sin(2 * np.pi * 1_800 * time) + 0.35 * rng.normal(size=length)
        return carrier * np.exp(-time * 70)
    if profile == "metal_spanner":
        carrier = np.sin(2 * np.pi * 3_300 * time) + 0.5 * np.sin(2 * np.pi * 5_100 * time)
        return carrier * np.exp(-time * 220)
    if profile == "compressor_exhaust":
        envelope = np.sin(np.pi * np.minimum(time / 0.22, 1.0))
        return rng.normal(size=length) * envelope
    raise ValueError(f"Unknown impulse profile: {profile}")


def inject_impulses(wav: bytes, profile: str, *, seed: int = 0) -> bytes:
    """Overlay repeatable non-stationary workshop transients on 8 kHz PCM WAV.

    The profiles model an impact wrench, a dropped metal spanner, and a compressor
    exhaust burst. They are synthetic test signals, not recordings or performance
    claims about a physical tool.
    """
    if profile not in IMPULSE_PROFILES:
        raise ValueError(f"Unknown impulse profile: {profile}")
    source = _read_pcm(wav).astype(np.float64)
    if len(source) == 0:
        return wav

    rng = np.random.default_rng(seed)
    sample_rate = 8_000
    event_count, duration = {
        "impact_wrench": (4, 0.045),
        "metal_spanner": (3, 0.018),
        "compressor_exhaust": (2, 0.24),
    }[profile]
    burst_length = min(len(source), max(1, int(duration * sample_rate)))
    amplitude = max(2_500.0, float(np.sqrt(np.mean(source**2))) * 5.0)
    output = source.copy()
    starts = np.linspace(0, max(0, len(source) - burst_length), event_count, dtype=int)
    jitter = rng.integers(-sample_rate // 12, sample_rate // 12 + 1, size=event_count)
    for start, offset in zip(starts, jitter):
        position = int(np.clip(start + offset, 0, len(source) - burst_length))
        burst = _burst(burst_length, sample_rate, profile, rng)
        peak = float(np.max(np.abs(burst))) or 1.0
        output[position : position + burst_length] += burst * (amplitude / peak)

    return _write_pcm(np.clip(np.rint(output), -32768, 32767).astype("<i2"))
