"""Prepare Gramvaani real-telephone slice from Vistaar test parquet.

Extracts audio, downsamples to 8 kHz mono WAV, writes full manifest to var/
and committed index (without text or audio) to data/benchmarks/gramvaani/index.jsonl.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import wave

from parcha.lab.dataset import Clip, save_manifest
from parcha.lab.gramvaani import prepare


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare Gramvaani real-telephone slice for Line Noise Lab.")
    parser.add_argument(
        "--parquet",
        type=Path,
        required=True,
        help="Path to Vistaar Gramvaani test.parquet",
    )
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=Path("var/benchmark_audio/gramvaani"),
        help="Directory to save 8 kHz WAVs and full manifest (default: var/benchmark_audio/gramvaani)",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("data/benchmarks/gramvaani/index.jsonl"),
        help="Path to output committed index (default: data/benchmarks/gramvaani/index.jsonl)",
    )
    args = parser.parse_args(argv)

    if not args.parquet.exists():
        sys.stderr.write(f"Error: parquet file not found at {args.parquet}\n")
        return 1

    args.audio_dir.mkdir(parents=True, exist_ok=True)
    rows = prepare(args.parquet, args.audio_dir)

    total_s = 0.0
    index_rows = []

    for r in rows:
        Clip.model_validate(r)
        wav_path = args.audio_dir / r["audio"]
        with wave.open(str(wav_path), "rb") as w:
            dur = w.getnframes() / float(w.getframerate())
        total_s += dur
        index_rows.append({
            "id": r["id"],
            "source_row": r["source_row"],
            "audio_sha256": r["audio_sha256"],
            "stratum": r["stratum"],
            "duration_s": round(dur, 2),
        })

    # Write full manifest next to the audio
    manifest_path = args.audio_dir / "manifest.jsonl"
    save_manifest(rows, manifest_path)

    # Write committed index (no text, no audio)
    args.index.parent.mkdir(parents=True, exist_ok=True)
    with args.index.open("w", encoding="utf-8", newline="\n") as f:
        for idx_row in index_rows:
            f.write(json.dumps(idx_row, ensure_ascii=False) + "\n")

    total_h = total_s / 3600.0
    forecast_credits = total_s * 0.20 * 2.0
    print(f"clips={len(rows)} total_s={total_s:.1f} ({total_h:.2f} h) forecast_credits_both_passes={forecast_credits:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
