"""Run an auditable live Timbre v3 benchmark against synthetic repair estimates."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import time
from typing import Any, Sequence

from parcha.config import Settings
from parcha.gnani import GnaniError, TimbreClient


TTS_CREDITS_PER_CHAR = 0.05
DEFAULT_MANIFEST = Path("data/benchmarks/timbre_v3.jsonl")
DEFAULT_OUTPUT_ROOT = Path("var/timbre_v3")
DEFAULT_MODELS = ("timbre-v3.0",)
TRANSIENT_RETRY_DELAYS = (1.0, 2.5)


def _read_manifest(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"manifest file not found: {path}")
    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on line {line_number}: {exc}") from exc
        if not isinstance(row, dict) or set(row) != {"id", "text", "voice"}:
            raise ValueError(f"manifest row {line_number} must contain only id, text, and voice")
        if any(not isinstance(row[field], str) or not row[field].strip() for field in row):
            raise ValueError(f"manifest row {line_number} values must be non-empty strings")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", row["id"]):
            raise ValueError(f"manifest row {line_number} has an unsafe id")
        rows.append(row)
    if not rows:
        raise ValueError("manifest contains no benchmark cases")
    if len({row['id'] for row in rows}) != len(rows):
        raise ValueError('manifest contains duplicate case ids')
    if any(len(row['text']) > 1000 for row in rows):
        raise ValueError('benchmark text must fit one TTS request (1000 characters)')
    return rows


def forecast(rows: Sequence[dict[str, str]], models: Sequence[str]) -> dict[str, int | float]:
    characters = sum(len(row["text"]) for row in rows) * len(models)
    return {
        "cases": len(rows),
        "requests": len(rows) * len(models),
        "characters": characters,
        "estimated_credits": round(characters * TTS_CREDITS_PER_CHAR, 2),
    }


def ensure_within_cap(estimate: dict[str, int | float], max_credits: float) -> None:
    if not math.isfinite(max_credits) or max_credits <= 0:
        raise ValueError("max credits must be positive")
    if float(estimate["estimated_credits"]) > max_credits:
        raise ValueError(
            f"forecast {estimate['estimated_credits']} credits exceeds cap {max_credits}"
        )


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _close(client: TimbreClient) -> None:
    close = getattr(client, "close", None)
    if close is None:
        close = getattr(getattr(client, "http", None), "close", None)
    if close is not None:
        close()


def _safe_error_message(exc: Exception, api_keys: str) -> str:
    message = str(exc)
    for key in api_keys.split(","):
        key = key.strip()
        if key:
            message = message.replace(key, "[REDACTED]")
    return message


def _synthesize_with_retry(client: TimbreClient, text: str) -> tuple[bytes, int]:
    for attempt, delay in enumerate((*TRANSIENT_RETRY_DELAYS, None), start=1):
        try:
            return client.synthesize(text), attempt
        except GnaniError as exc:
            exc.benchmark_attempts = attempt
            if exc.status != 500 or delay is None:
                raise
            time.sleep(delay)
    raise AssertionError("unreachable")


def run_live(
    rows: Sequence[dict[str, str]],
    models: Sequence[str],
    output: Path,
    *,
    max_credits: float,
) -> Path:
    if not models or any(model not in {'timbre-v2.5', 'timbre-v3.0'} for model in models):
        raise ValueError('unsupported benchmark model')
    if len(set(models)) != len(models) or len({row['id'] for row in rows}) != len(rows):
        raise ValueError('duplicate models or case ids')
    if any(not re.fullmatch(r'[A-Za-z0-9_-]+', row['id']) or len(row['text']) > 1000 for row in rows):
        raise ValueError('unsafe case id or overlong text')
    estimate = forecast(rows, models)
    retry_estimate = dict(estimate, estimated_credits=round(float(estimate['estimated_credits']) * 3, 2))
    ensure_within_cap(retry_estimate, max_credits)
    settings = Settings.load()
    settings.require_gnani()
    output.mkdir(parents=True, exist_ok=False)
    (output / "audio").mkdir()
    (output / "manifest.json").write_text(json.dumps({
        "started_at_utc": _timestamp(),
        "models": list(models),
        "max_credits": max_credits,
        "forecast": estimate,
        "estimated_credits_with_500_retries": retry_estimate['estimated_credits'],
        "api_endpoint": f"{settings.gnani_base_url.rstrip('/')}/api/v1/tts/inference",
        "credential_logging": "excluded",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with (output / "results.jsonl").open("w", encoding="utf-8") as log:
        for model in models:
            for row in rows:
                record: dict[str, Any] = {
                    "timestamp_utc": _timestamp(),
                    "case_id": row["id"],
                    "model": model,
                    "voice": row["voice"],
                    "text": row["text"],
                    "language": "hi-IN",
                    "audio_format": "pcm_mulaw/8000Hz/mono",
                    "api_key": None,
                }
                client = TimbreClient(
                    settings.api_key, voice=row["voice"], model=model, base_url=settings.gnani_base_url
                )
                try:
                    audio, attempts = _synthesize_with_retry(client, row["text"])
                    filename = f"audio/{row['id']}--{model}.mulaw"
                    (output / filename).write_bytes(audio)
                    record.update({
                        "status": "success",
                        "audio_file": filename,
                        "audio_bytes": len(audio),
                        "audio_sha256": hashlib.sha256(audio).hexdigest(),
                        "estimated_duration_seconds": round(len(audio) / 8000, 4),
                        "attempts": attempts,
                    })
                except Exception as exc:
                    record.update({
                        "status": "error",
                        "error_type": type(exc).__name__,
                        "error_message": _safe_error_message(exc, settings.api_key),
                        "attempts": getattr(exc, 'benchmark_attempts', 1),
                        "http_status": getattr(exc, 'status', None),
                    })
                finally:
                    try:
                        _close(client)
                    except Exception as exc:
                        record["close_error_type"] = type(exc).__name__
                log.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                log.flush()
    return output


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    parser.add_argument("--max-credits", type=float, default=100_000)
    parser.add_argument("--live", action="store_true", help="make live, credit-consuming requests")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    rows = _read_manifest(args.manifest)
    estimate = forecast(rows, args.models)
    ensure_within_cap(estimate, args.max_credits)
    if not args.live:
        print(json.dumps(estimate, ensure_ascii=False, indent=2))
        return 0
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = run_live(rows, args.models, args.output_root / run_id, max_credits=args.max_credits)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
