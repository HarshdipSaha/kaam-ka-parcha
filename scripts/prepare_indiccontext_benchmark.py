"""Fetch a reproducible, stratified IndicContextEval Hindi sample into ignored var/."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import wave

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from parcha.audio import normalize_upload
from parcha.lab.dataset import save_manifest
from parcha.lab.real_audio import select_indiccontext_rows


DATASET = "ai4bharat/IndicContextEval"
LICENSE = "CC BY 4.0"
ROWS_ENDPOINT = "https://datasets-server.huggingface.co/rows"
PAGE_SIZE = 100
USER_AGENT = "KaamKaParcha-Benchmark/1.0 (dataset metadata/audio download)"


def _fresh_audio_links(payload: dict[str, Any], *, margin_seconds: int = 300) -> bool:
    now = int(time.time()) + margin_seconds
    for entry in payload.get("rows", []):
        audio = entry.get("row", {}).get("audio") or []
        for item in audio:
            src = item.get("src", "")
            if "Expires=" not in src:
                continue
            try:
                expires = int(src.split("Expires=", 1)[1].split("&", 1)[0])
            except ValueError:
                return False
            if expires <= now:
                return False
    return True


def _request_json(url: str, *, retries: int = 3) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries):
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            status = getattr(exc, "code", None)
            if status is not None and status < 500 and status != 429:
                raise
            if attempt + 1 < retries:
                time.sleep(2**attempt)
    raise RuntimeError(f"Hugging Face dataset request failed after {retries} attempts") from last_error


def fetch_hindi_rows(cache_dir: Path) -> list[dict[str, Any]]:
    """Fetch/cache metadata pages, refreshing expired signed audio links."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    total: int | None = None
    for offset in range(0, 100_000, PAGE_SIZE):
        cache_path = cache_dir / f"hindi_{offset:04d}.json"
        payload: dict[str, Any] | None = None
        if cache_path.is_file():
            try:
                cached = json.loads(cache_path.read_text(encoding="utf-8"))
                if _fresh_audio_links(cached):
                    payload = cached
            except (OSError, json.JSONDecodeError):
                payload = None
        if payload is None:
            query = urlencode({
                "dataset": DATASET,
                "config": "default",
                "split": "Hindi",
                "offset": offset,
                "length": PAGE_SIZE,
            })
            payload = _request_json(f"{ROWS_ENDPOINT}?{query}")
            cache_path.write_text(json.dumps(payload), encoding="utf-8")
        if total is None:
            total = int(payload["num_rows_total"])
        entries = payload.get("rows", [])
        rows.extend(entry["row"] for entry in entries)
        if not entries or offset + len(entries) >= total:
            break
    if total is None or len(rows) != total:
        raise RuntimeError(f"Expected {total} Hindi rows from the dataset viewer; received {len(rows)}")
    return rows


def _download(url: str, *, max_bytes: int = 8 * 1024 * 1024) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:
        data = response.read(max_bytes + 1)
    if not data or len(data) > max_bytes:
        raise ValueError("dataset audio is empty or exceeds the 8 MiB download limit")
    return data


def _duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getframerate() != 8000:
            raise ValueError(f"normalized sample has unexpected WAV format: {path.name}")
        frame_bytes = wav.getnchannels() * wav.getsampwidth()
        frame_data = wav.readframes(wav.getnframes())
        if len(frame_data) % frame_bytes:
            raise ValueError(f"normalized sample ends with a partial PCM frame: {path.name}")
        return len(frame_data) / frame_bytes / float(wav.getframerate())


def prepare_sample(
    rows: list[dict[str, Any]], *, limit: int, seed: int, audio_root: Path, manifest_path: Path
) -> dict[str, Any]:
    selected = select_indiccontext_rows(rows, limit=limit, seed=seed)
    if len(selected) < limit:
        raise RuntimeError(f"Only {len(selected)} eligible speaker-distinct rows; requested {limit}")

    manifest_rows: list[dict[str, Any]] = []
    durations: list[float] = []
    downloads = 0
    for index, row in enumerate(selected, 1):
        clip_id = f"i{index:03d}"
        audio_path = audio_root / f"{clip_id}.wav"
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        if not audio_path.is_file():
            source = _download(row["audio"][0]["src"])
            normalized = normalize_upload(source, "audio/wav", sample_rate=8000)
            temporary = audio_path.with_suffix(".wav.part")
            temporary.write_bytes(normalized)
            temporary.replace(audio_path)
            downloads += 1
        duration = _duration(audio_path)
        if not 6.0 <= duration <= 22.0:
            raise ValueError(f"selected clip {clip_id} is outside the six-to-22-second band")
        durations.append(duration)
        speaker_id = str(row.get("speaker_id") or row.get("file_name") or "")
        speaker_hash = hashlib.sha256(speaker_id.encode("utf-8")).hexdigest()[:16]
        domain = str(row["domain_name"])
        style = str(row["speech_style"])
        mixed = bool(row["code_mixing"])
        text = row["reference_text_no_brackets"].strip()
        manifest_rows.append({
            "id": clip_id,
            "text": text,
            "reference_transcribe": text,
            "entities": {},
            "audio": audio_path.name,
            "kind": "speech",
            "seed": seed,
            "source": "open_dataset",
            "source_dataset": f"{DATASET}:Hindi",
            "source_license": LICENSE,
            "source_row": str(row.get("file_name") or index),
            "speaker_hash": speaker_hash,
            "stratum": f"{domain}|{style}|code_mixed={str(mixed).lower()}",
            "reference_type": "dataset_reference",
        })
    save_manifest(manifest_rows, manifest_path)

    return {
        "selected": selected,
        "downloads": downloads,
        "manifest_rows": manifest_rows,
        "durations": durations,
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=96)
    parser.add_argument("--seed", type=int, default=20261005)
    parser.add_argument("--cache-dir", type=Path, default=Path("var/benchmark_audio/indiccontext/pages"))
    parser.add_argument("--audio-root", type=Path, default=Path("var/lab/audio/indiccontext"))
    parser.add_argument("--manifest", type=Path, default=Path("var/lab/indiccontext_manifest.jsonl"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rows = fetch_hindi_rows(args.cache_dir)
    result = prepare_sample(
        rows, limit=args.limit, seed=args.seed, audio_root=args.audio_root, manifest_path=args.manifest
    )
    selected = result["selected"]
    domains = {str(row["domain_name"]) for row in selected}
    styles = {str(row["speech_style"]) for row in selected}
    mixing = {bool(row["code_mixing"]) for row in selected}
    print(f"Dataset: {DATASET} Hindi ({LICENSE}); metadata rows checked: {len(rows)}")
    print(f"Sample: {len(selected)} clips, {len({row.get('speaker_id') for row in selected})} speakers, {len(domains)} domains")
    print(f"Styles: {', '.join(sorted(styles))}; code_mixing values: {', '.join(str(value).lower() for value in sorted(mixing))}")
    print(f"Duration seconds: min={min(result['durations']):.2f}, mean={sum(result['durations']) / len(result['durations']):.2f}, max={max(result['durations']):.2f}")
    print(f"New audio downloads: {result['downloads']}; manifest SHA-256: {result['manifest_sha256']}")
    print(f"Manifest: {args.manifest}; audio root: {args.audio_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
