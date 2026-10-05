"""Turn already-provided workshop WAV/VTT pairs into short private pseudo-reference clips."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
import wave

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from parcha.lab.dataset import save_manifest


TIMESTAMP = re.compile(r"(\d{2,}):(\d{2}):(\d{2}(?:\.\d+)?)")
TAG = re.compile(r"<[^>]*>")
REPAIR_TERMS = re.compile(
    r"\b(clutch|bearing|plate|labou?r|price|cost|service|brake|oil|filter|part|gearbox)\b|"
    r"रुप(?:ये|ए)?|₹|\b\d{2,}\b",
    re.IGNORECASE,
)


def _seconds(timestamp: str) -> float:
    match = TIMESTAMP.match(timestamp.strip())
    if not match:
        raise ValueError(f"invalid WebVTT timestamp: {timestamp!r}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def parse_vtt(text: str) -> list[dict[str, Any]]:
    """Parse and de-duplicate adjacent WebVTT captions without rewriting their words."""
    lines = text.splitlines()
    cues: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        timing = lines[index]
        if "-->" not in timing:
            index += 1
            continue
        start_raw, end_raw = timing.split("-->", 1)
        start = _seconds(start_raw)
        end = _seconds(end_raw.strip().split()[0])
        index += 1
        caption: list[str] = []
        while index < len(lines) and lines[index].strip():
            line = TAG.sub("", lines[index]).strip()
            if line and (not caption or caption[-1] != line):
                caption.append(line)
            index += 1
        joined = " ".join(caption).strip()
        if joined and end > start:
            if cues and cues[-1]["text"] == joined:
                cues[-1]["end"] = end
            else:
                cues.append({"start": start, "end": end, "text": joined})
        index += 1
    return cues


def select_caption_windows(
    cues: list[dict[str, Any]], *, per_video: int = 2, min_seconds: float = 8.0, max_seconds: float = 18.0
) -> list[dict[str, Any]]:
    """Prefer repair/amount-related subtitle spans and return non-overlapping windows."""
    if per_video < 1:
        raise ValueError("per_video must be positive")
    candidates: list[tuple[float, dict[str, Any]]] = []
    for first in range(len(cues)):
        for last in range(first, len(cues)):
            start = float(cues[first]["start"])
            end = float(cues[last]["end"])
            duration = end - start
            if duration > max_seconds:
                break
            if duration < min_seconds:
                continue
            text = " ".join(str(cue["text"]) for cue in cues[first : last + 1]).strip()
            words = text.split()
            if len(words) < 4:
                continue
            topic_hits = len(REPAIR_TERMS.findall(text))
            score = topic_hits * 4.0 + min(len(words), 60) / 20 - abs(duration - 12.0) / 4
            candidates.append((score, {"start": start, "end": end, "duration": duration, "text": text}))

    candidates.sort(key=lambda item: (-item[0], item[1]["start"], item[1]["end"]))
    selected: list[dict[str, Any]] = []
    for _, candidate in candidates:
        overlaps = any(
            min(candidate["end"], chosen["end"]) - max(candidate["start"], chosen["start"])
            > min(candidate["duration"], chosen["duration"]) * 0.25
            for chosen in selected
        )
        if not overlaps:
            selected.append(candidate)
            if len(selected) == per_video:
                break
    return sorted(selected, key=lambda item: item["start"])


def _actual_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 8000):
            raise ValueError(f"unexpected normalized WAV format: {path.name}")
        frame_size = audio.getnchannels() * audio.getsampwidth()
        frames = audio.readframes(audio.getnframes())
        return len(frames) / frame_size / audio.getframerate()


def prepare_segments(
    *, input_dir: Path, audio_root: Path, manifest_path: Path, per_video: int = 2
) -> dict[str, Any]:
    sources: list[tuple[Path, Path]] = []
    for source_wav in sorted(input_dir.glob("*_16k.wav")):
        video_id = source_wav.name.removesuffix("_16k.wav")
        captions = input_dir / f"{video_id}.hi.vtt"
        if not captions.is_file():
            captions = input_dir / f"{video_id}.hi-orig.vtt"
        if captions.is_file():
            sources.append((source_wav, captions))
    if not sources:
        raise FileNotFoundError(f"no matching *_16k.wav and Hindi VTT pairs in {input_dir}")

    audio_root.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, Any]] = []
    durations: list[float] = []
    segment_index = 1
    for source_wav, captions_path in sources:
        cues = parse_vtt(captions_path.read_text(encoding="utf-8", errors="replace"))
        windows = select_caption_windows(cues, per_video=per_video)
        if not windows:
            continue
        video_id = source_wav.name.removesuffix("_16k.wav")
        for window in windows:
            clip_id = f"y{segment_index:03d}"
            output = audio_root / f"{clip_id}.wav"
            command = [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-ss", f"{window['start']:.3f}", "-i", str(source_wav),
                "-t", f"{window['duration']:.3f}", "-ar", "8000", "-ac", "1",
                "-c:a", "pcm_s16le", str(output),
            ]
            result = subprocess.run(command, capture_output=True, check=False)
            if result.returncode:
                raise RuntimeError(f"FFmpeg could not extract private sample {clip_id}")
            actual = _actual_duration(output)
            if not 7.5 <= actual <= 18.5:
                raise ValueError(f"caption window {clip_id} has an invalid duration")
            durations.append(actual)
            manifest_rows.append({
                "id": clip_id,
                "text": window["text"],
                "reference_transcribe": window["text"],
                "entities": {},
                "audio": output.name,
                "kind": "speech",
                "seed": segment_index,
                "source": "user_provided_youtube",
                "source_dataset": "user-provided YouTube-source workshop clips",
                "source_license": None,
                "source_row": video_id,
                "stratum": "mechanic_workshop|caption_reference",
                "reference_type": "auto_caption",
            })
            segment_index += 1
    if not manifest_rows:
        raise RuntimeError("no repair-relevant caption windows met the selection constraints")
    save_manifest(manifest_rows, manifest_path)
    return {
        "segments": len(manifest_rows),
        "videos": len({row["source_row"] for row in manifest_rows}),
        "durations": durations,
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("var/benchmark_audio"))
    parser.add_argument("--audio-root", type=Path, default=Path("var/lab/audio/youtube"))
    parser.add_argument("--manifest", type=Path, default=Path("var/lab/youtube_manifest.jsonl"))
    parser.add_argument("--per-video", type=int, default=2)
    args = parser.parse_args(argv)
    result = prepare_segments(
        input_dir=args.input_dir, audio_root=args.audio_root,
        manifest_path=args.manifest, per_video=args.per_video,
    )
    durations = result["durations"]
    print(f"Private user-provided clip subset: {result['segments']} segments from {result['videos']} videos")
    print(f"Duration seconds: min={min(durations):.2f}, mean={sum(durations) / len(durations):.2f}, max={max(durations):.2f}")
    print(f"Reference type: YouTube auto-captions (pseudo-reference); no trusted amount labels")
    print(f"Manifest SHA-256: {result['manifest_sha256']}; manifest: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
