"""Register owner extempore takes against benchmark prompt cards.

Kept internal (audio and manifest under var/); never committed.
Normalises takes to 8 kHz mono WAV using normalize_upload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Iterable

from parcha.audio import normalize_upload
from parcha.lab.dataset import Clip, save_manifest

_CARD_HEADER = re.compile(r"^###\s+([a-z0-9]+)\s*$")
_ITEMS_LINE = re.compile(r"^-\s*Items:\s*(.+)$", re.IGNORECASE)
_DELIVERY_LINE = re.compile(r"^-\s*Delivery:\s*(.+)$", re.IGNORECASE)
_AMOUNTS_LINE = re.compile(r"^-\s*Expected amounts(?:\s*\(paise\))?:\s*(.+)$", re.IGNORECASE)


def parse_prompt_sheet(path: str | Path) -> list[dict]:
    """Parse markdown prompt sheet containing 80 cards into prompt dictionaries."""
    content = Path(path).read_text(encoding="utf-8-sig")
    prompts: list[dict] = []
    current: dict | None = None

    for raw_line in content.splitlines():
        line = raw_line.strip()
        m_head = _CARD_HEADER.match(line)
        if m_head:
            if current and "id" in current:
                prompts.append(_finalize_prompt(current))
            current = {"id": m_head.group(1)}
            continue

        if not current:
            continue

        m_items = _ITEMS_LINE.match(line)
        if m_items:
            current["items"] = m_items.group(1).strip()
            continue

        m_deliv = _DELIVERY_LINE.match(line)
        if m_deliv:
            current["delivery"] = m_deliv.group(1).strip()
            continue

        m_amt = _AMOUNTS_LINE.match(line)
        if m_amt:
            raw_amt = m_amt.group(1).strip()
            if raw_amt.startswith("[") and raw_amt.endswith("]"):
                current["expected_amounts_paise"] = [int(x.strip()) for x in raw_amt[1:-1].split(",") if x.strip()]
            else:
                current["expected_amounts_paise"] = [int(x.strip()) for x in raw_amt.split(",") if x.strip()]
            continue

    if current and "id" in current:
        prompts.append(_finalize_prompt(current))

    return prompts


def _finalize_prompt(data: dict) -> dict:
    cid = data["id"]
    items = data.get("items", "")
    delivery = data.get("delivery", "")
    amounts = data.get("expected_amounts_paise", [])
    text = f"{items}, {delivery}" if delivery else items

    prompt_dict = {
        "id": cid,
        "text": text,
        "reference_transcribe": text,
        "entities": {"items": items, "delivery": delivery},
        "audio": f"{cid}.wav",
        "kind": "speech",
        "seed": 0,
        "expected_amounts_paise": amounts,
        "voice": None,
        "source": "consented_script",
        "stratum": "owner_extempore",
    }
    Clip.model_validate(prompt_dict)
    return prompt_dict


def register(prompt_rows: Iterable[dict], take_files: Iterable[str | Path]) -> list[dict]:
    """Map take audio files (e.g. o001.wav) to expected_amounts_paise of prompt o001.

    Sets source='consented_script', stratum='owner_extempore', voice=None.
    Raises ValueError for a take without a matching prompt.
    """
    prompts_by_id = {p["id"]: p for p in prompt_rows}
    registered: list[dict] = []

    for take in take_files:
        take_path = Path(take)
        cid = take_path.stem
        if cid not in prompts_by_id:
            raise ValueError(f"take without prompt: {take_path.name} (id {cid!r})")

        p = prompts_by_id[cid]
        row = {
            "id": p["id"],
            "text": p.get("text", ""),
            "reference_transcribe": p.get("reference_transcribe", p.get("text", "")),
            "entities": dict(p.get("entities", {})),
            "audio": take_path.name,
            "kind": p.get("kind", "speech"),
            "seed": p.get("seed", 0),
            "expected_amounts_paise": list(p.get("expected_amounts_paise", [])),
            "voice": None,
            "source": "consented_script",
            "stratum": "owner_extempore",
        }
        if "audio_sha256" in p and p["audio_sha256"]:
            row["audio_sha256"] = p["audio_sha256"]

        Clip.model_validate(row)
        registered.append(row)

    return registered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register owner extempore takes into a Line Noise Lab manifest.")
    parser.add_argument(
        "--prompts",
        type=Path,
        default=Path("data/benchmarks/amount_v2/owner_prompt_sheet.md"),
        help="Path to owner_prompt_sheet.md",
    )
    parser.add_argument(
        "--takes-dir",
        type=Path,
        default=Path("var/benchmark_audio/owner/takes"),
        help="Directory with raw takes (e.g. o001.wav, o001.m4a)",
    )
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=Path("var/benchmark_audio/owner"),
        help="Target directory for 8 kHz normalised WAV files",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("var/benchmark_audio/owner/manifest.jsonl"),
        help="Output manifest path",
    )
    args = parser.parse_args(argv)

    if not args.prompts.exists():
        sys.stderr.write(f"Error: Prompt sheet not found at {args.prompts}\n")
        return 1

    prompts = parse_prompt_sheet(args.prompts)
    print(f"Loaded {len(prompts)} prompts from {args.prompts}")

    # Look for audio files in takes-dir or audio-dir
    takes: list[Path] = []
    search_dirs = [d for d in [args.takes_dir, args.audio_dir] if d.exists()]
    for sdir in search_dirs:
        for ext in ("*.wav", "*.ogg", "*.mp4", "*.m4a", "*.webm"):
            for f in sorted(sdir.glob(ext)):
                if f.name != "manifest.jsonl" and f not in takes:
                    takes.append(f)

    if not takes:
        print(f"No audio takes found in {[str(d) for d in search_dirs]}. Waiting for recordings.")
        return 0

    args.audio_dir.mkdir(parents=True, exist_ok=True)
    rows_with_sha: list[dict] = []

    for take_path in takes:
        cid = take_path.stem
        norm_wav_path = args.audio_dir / f"{cid}.wav"

        # Normalise if not already normalised or different destination
        raw_bytes = take_path.read_bytes()
        mime = "audio/wav"
        if take_path.suffix.lower() in {".m4a", ".mp4"}:
            mime = "audio/mp4"
        elif take_path.suffix.lower() == ".ogg":
            mime = "audio/ogg"
        elif take_path.suffix.lower() == ".webm":
            mime = "audio/webm"

        try:
            norm_bytes = normalize_upload(raw_bytes, mime, sample_rate=8000)
        except Exception:
            # If normalize_upload fails on wav header or mime, try as audio/wav
            norm_bytes = normalize_upload(raw_bytes, "audio/wav", sample_rate=8000)

        norm_wav_path.write_bytes(norm_bytes)
        sha = hashlib.sha256(norm_bytes).hexdigest()

        # Update prompt with sha before registering
        matching_prompts = [p for p in prompts if p["id"] == cid]
        if not matching_prompts:
            raise ValueError(f"take without prompt: {take_path.name}")
        matching_prompts[0]["audio_sha256"] = sha

    registered = register(prompts, [args.audio_dir / f"{t.stem}.wav" for t in takes])
    save_manifest(registered, args.manifest)
    print(f"Registered {len(registered)} takes into {args.manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
