"""Combine prepared private audio manifests under a single Runner audio root."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from parcha.lab.dataset import load_manifest, save_manifest


def combine_manifests(
    inputs: list[tuple[Path, Path]], *, audio_root: Path, output: Path
) -> tuple[int, str]:
    root = audio_root.resolve()
    rows: list[dict] = []
    ids: set[str] = set()
    for manifest_path, source_audio_root in inputs:
        clips = load_manifest(manifest_path, audio_root=source_audio_root, require_audio=True)
        source_root = source_audio_root.resolve()
        prefix = source_root.relative_to(root)
        for clip in clips:
            if clip.id in ids:
                raise ValueError(f"duplicate clip ID while combining manifests: {clip.id}")
            ids.add(clip.id)
            row = clip.model_dump()
            row["audio"] = (prefix / clip.audio).as_posix()
            rows.append(row)
    save_manifest(rows, output)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return len(rows), digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-root", type=Path, default=Path("var/lab/audio"))
    parser.add_argument("--indic-manifest", type=Path, default=Path("var/lab/indiccontext_manifest.jsonl"))
    parser.add_argument("--youtube-manifest", type=Path, default=Path("var/lab/youtube_manifest.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("var/lab/real_audio_manifest.jsonl"))
    args = parser.parse_args(argv)
    count, digest = combine_manifests(
        [
            (args.indic_manifest, args.audio_root / "indiccontext"),
            (args.youtube_manifest, args.audio_root / "youtube"),
        ],
        audio_root=args.audio_root,
        output=args.output,
    )
    # Reload the combined manifest and resolve every path before a live forecast.
    clips = load_manifest(args.output, audio_root=args.audio_root, require_audio=True)
    private = sum(clip.reference_type == "auto_caption" for clip in clips)
    print(f"Combined private manifest: {count} clips ({count - private} dataset references, {private} auto-caption references)")
    print(f"Manifest SHA-256: {digest}; all audio paths validated under {args.audio_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
