"""
scripts/benchmark_youtube_samples.py - Real-world Hindi automotive workshop benchmark downloader & evaluator.
Uses yt-dlp / vtd logic to standardize audio into 16kHz mono WAV, cleans VTT transcripts into paragraphs,
and builds an authentic benchmark dataset validating Kaam Ka Parcha job card extraction & customer confirmation.
"""
from datetime import date
import json
import os
from pathlib import Path
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AUDIO_DIR = Path("var/benchmark_audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

CASES_PATH = Path(os.environ.get("YOUTUBE_CASES_MANIFEST", "var/benchmark_audio/youtube_cases.json"))


def load_cases(path: Path = CASES_PATH) -> list[dict]:
    """Load the internal case list from a local, git-ignored manifest.

    Third-party video URLs, titles and spoken quotes are never committed: this set is an
    internal diagnostic and is not part of the contest submission (see docs/gates.md).
    """
    if not path.exists():
        raise SystemExit(f"Local case manifest not found: {path} (internal-only; not tracked in git)")
    return json.loads(path.read_text(encoding="utf-8"))


def clean_vtt_to_text(vtt_path: Path) -> str:
    """Clean VTT subtitle cues into coherent paragraph text."""
    if not vtt_path.exists():
        return ""
    lines = vtt_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    text_lines = []
    for line in lines:
        if (
            "-->" in line
            or line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
            or not line.strip()
        ):
            continue
        cleaned = re.sub(r"<[^>]+>", "", line).strip()
        if cleaned and (not text_lines or cleaned != text_lines[-1]):
            text_lines.append(cleaned)

    # Simple dedup of adjacent repeated phrases common in YouTube auto-captions
    deduped = []
    for phrase in text_lines:
        if not deduped or phrase != deduped[-1]:
            deduped.append(phrase)
    return " ".join(deduped)


def convert_audio_to_16k_wav(mp3_path: Path, wav_path: Path) -> bool:
    """Transcode MP3 to standardized 16kHz mono 16-bit PCM WAV for Prisma/Timbre pipeline."""
    if wav_path.exists() and wav_path.stat().st_size > 0:
        return True
    if not mp3_path.exists():
        return False
    cmd = [
        "ffmpeg", "-y", "-i", str(mp3_path),
        "-ar", "16000", "-ac", "1",
        "-c:a", "pcm_s16le",
        str(wav_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0


def main():
    print("=" * 60)
    print("Kaam Ka Parcha - YouTube Mechanic Benchmark Processor")
    print("=" * 60)

    manifest_cases = []

    cases = load_cases()
    for case in cases:
        vid = case["video_id"]
        mp3_file = AUDIO_DIR / f"{vid}.mp3"
        wav_file = AUDIO_DIR / f"{vid}_16k.wav"
        vtt_file = AUDIO_DIR / f"{vid}.hi.vtt"
        if not vtt_file.exists():
            vtt_file = AUDIO_DIR / f"{vid}.hi-orig.vtt"
        txt_file = AUDIO_DIR / f"{vid}_transcript.txt"

        print(f"\nProcessing [{case['id']}] {case['title'][:45]}...")

        # 1. Transcode audio
        if mp3_file.exists():
            ok = convert_audio_to_16k_wav(mp3_file, wav_file)
            if ok:
                print(f"  -> Converted to 16kHz WAV: {wav_file.name} ({wav_file.stat().st_size:,} bytes)")
            else:
                print(f"  -> WAV conversion failed for {mp3_file.name}")
        else:
            print(f"  -> MP3 not found: {mp3_file.name}")

        # 2. Clean transcript
        transcript_text = clean_vtt_to_text(vtt_file)
        if transcript_text:
            txt_file.write_text(transcript_text, encoding="utf-8")
            print(f"  -> Cleaned transcript saved: {txt_file.name} ({len(transcript_text.split()):,} words)")
        else:
            print(f"  -> Subtitles not found for {vid}")

        # 3. Assemble case record
        record = dict(case)
        record["audio_mp3"] = str(mp3_file.as_posix())
        record["audio_16k_wav"] = str(wav_file.as_posix())
        record["transcript_txt"] = str(txt_file.as_posix())
        record["word_count"] = len(transcript_text.split()) if transcript_text else 0
        record["has_audio_wav"] = wav_file.exists()
        manifest_cases.append(record)

    manifest_output = AUDIO_DIR / "youtube_mechanic_benchmark.json"
    with open(manifest_output, "w", encoding="utf-8") as f:
        json.dump(
            {
                "description": "Internal-only mechanic-video diagnostic (not part of the submission)",
                "dataset_version": "v1.0",
                "created_at": str(date.today()),
                "total_cases": len(manifest_cases),
                "cases": manifest_cases
            },
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"\nBenchmark manifest successfully written to: {manifest_output}")
    print(f"Total benchmark cases: {len(manifest_cases)}")


if __name__ == "__main__":
    main()
