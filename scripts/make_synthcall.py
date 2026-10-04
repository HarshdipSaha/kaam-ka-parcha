#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

# Ensure src is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from parcha.audio import mulaw_to_wav
from parcha.config import Settings
from parcha.gnani import TimbreClient
from parcha.lab.dataset import Clip, load_manifest


def compute_forecast(clips: list[Clip], max_credits: float) -> dict[str, object]:
    total_clips = len(clips)
    unique_texts = sorted({clip.text for clip in clips})
    unique_count = len(unique_texts)
    total_chars = sum(len(clip.text) for clip in clips)
    unique_chars = sum(len(text) for text in unique_texts)

    # 1 credit per TTS synthesis call (each unique text synthesized once)
    estimated_calls = unique_count
    estimated_credits = float(estimated_calls)
    is_under_cap = estimated_credits <= max_credits

    return {
        "total_clips": total_clips,
        "unique_texts_count": unique_count,
        "unique_texts": unique_texts,
        "total_chars": total_chars,
        "unique_chars": unique_chars,
        "estimated_calls": estimated_calls,
        "estimated_credits": estimated_credits,
        "max_credits": max_credits,
        "is_under_cap": is_under_cap,
    }


def print_forecast(fc: dict[str, object], manifest_path: Path, output_dir: Path) -> None:
    print("==================================================")
    print("SynthCall-IN Pre-Flight TTS Forecast")
    print("==================================================")
    print(f"Manifest:          {manifest_path}")
    print(f"Output Directory:  {output_dir}")
    print(f"Total Clips:       {fc['total_clips']}")
    print(f"Unique Texts:      {fc['unique_texts_count']}")
    print(f"Total Characters:  {fc['total_chars']}")
    print(f"Unique Characters: {fc['unique_chars']}")
    print(f"Forecast Calls:    {fc['estimated_calls']}")
    print(f"Estimated Credits: {fc['estimated_credits']:.1f}")
    print(f"Max Credits Cap:   {fc['max_credits']:.1f}")
    if fc["is_under_cap"]:
        print("Status:            PASS (Within budget cap)")
    else:
        print("Status:            EXCEEDS CAP")
    print("==================================================")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate seeded SynthCall-IN dataset via Gnani Timbre TTS"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/synthcall_manifest.jsonl",
        help="Path to SynthCall JSONL manifest (default: data/synthcall_manifest.jsonl)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="var/lab/audio",
        help="Target audio directory (default: var/lab/audio)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Execute live Timbre synthesis calls",
    )
    parser.add_argument(
        "--max-credits",
        type=float,
        default=2000.0,
        help="Maximum credits allocated for synthesis (default: 2000)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest)
    output_dir = Path(args.output_dir)

    # Validate manifest by loading clips without requiring audio on disk yet
    clips = load_manifest(manifest_path, require_audio=False)

    forecast = compute_forecast(clips, args.max_credits)

    if not args.live:
        print_forecast(forecast, manifest_path, output_dir)
        return 0

    # Live synthesis mode
    if not forecast["is_under_cap"]:
        raise RuntimeError(
            f"Forecasted credits {forecast['estimated_credits']:.1f} exceed max cap {args.max_credits:.1f}"
        )

    settings = Settings.load()
    settings.require_gnani()

    output_dir.mkdir(parents=True, exist_ok=True)
    timbre = TimbreClient(
        api_key=settings.api_key,
        voice=settings.tts_voice,
        base_url=settings.gnani_base_url,
    )

    unique_texts: list[str] = forecast["unique_texts"]  # type: ignore[assignment]
    print(f"Synthesizing {len(unique_texts)} unique texts using voice '{settings.tts_voice}'...")

    audio_cache: dict[str, bytes] = {}
    for i, text in enumerate(unique_texts, 1):
        print(f"[{i}/{len(unique_texts)}] Synthesizing: {text[:45]}...")
        mulaw = timbre.synthesize(text)
        audio_cache[text] = mulaw

    for clip in clips:
        mulaw_data = audio_cache[clip.text]
        wav_data = mulaw_to_wav(mulaw_data)

        clip_stem = Path(clip.audio).stem
        mulaw_file = output_dir / f"{clip_stem}.mulaw"
        wav_file = output_dir / clip.audio

        mulaw_file.write_bytes(mulaw_data)
        wav_file.write_bytes(wav_data)

    print(f"Generated {len(clips)} audio files in {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
