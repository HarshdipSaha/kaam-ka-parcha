"""Forecast or render the amount benchmark with Timbre voices."""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path
from typing import Sequence

from parcha.audio import mulaw_to_wav
from parcha.config import Settings
from parcha.gnani import TimbreClient

TTS_CREDITS_PER_CHAR = 0.05
DEFAULT_AUDIO_DIR = Path("var/benchmark_audio/amount_v2")


def forecast(rows: Sequence[dict]) -> dict:
    """Return row, character, credit, and voice totals for a manifest."""
    chars = sum(len(row["text"]) for row in rows)
    return {
        "rows": len(rows),
        "chars": chars,
        "credits": round(chars * TTS_CREDITS_PER_CHAR, 2),
        "voices": sorted({row["voice"] for row in rows}),
    }


def _read_manifest(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"manifest file not found: {path}")

    rows: list[dict] = []
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"manifest row on line {line_number} must be a JSON object")
            rows.append(row)
    return rows


def _close_client(client: TimbreClient) -> None:
    close = getattr(client, "close", None)
    if close is None:
        close = getattr(getattr(client, "http", None), "close", None)
    if close is not None:
        close()


def _close_clients(clients: dict[str, TimbreClient]) -> list[tuple[str, Exception]]:
    errors: list[tuple[str, Exception]] = []
    for voice, client in clients.items():
        try:
            _close_client(client)
        except Exception as exc:
            errors.append((voice, exc))
    return errors


def _preflight_live_rows(rows: Sequence[dict], audio_dir: Path) -> list[Path]:
    audio_root = audio_dir.resolve()
    if audio_root.exists() and not audio_root.is_dir():
        raise ValueError(f"audio output root is not a directory: {audio_root}")

    destinations: list[Path] = []
    seen_destinations: dict[str, int] = {}
    for row_number, row in enumerate(rows, start=1):
        for field in ("text", "voice", "audio"):
            if field not in row:
                raise ValueError(f"manifest row {row_number} is missing required field {field!r}")
            value = row[field]
            if not isinstance(value, str):
                raise ValueError(f"manifest row {row_number} field {field!r} must be a string")
            if not value.strip():
                raise ValueError(f"manifest row {row_number} field {field!r} must not be empty")

        try:
            destination = (audio_root / Path(row["audio"])).resolve()
        except (OSError, RuntimeError, ValueError) as exc:
            raise ValueError(
                f"manifest row {row_number} has an invalid audio path: {row['audio']!r}"
            ) from exc

        if destination == audio_root:
            raise ValueError(f"manifest row {row_number} audio path resolves to the output root")
        try:
            destination.relative_to(audio_root)
        except ValueError as exc:
            raise ValueError(
                f"manifest row {row_number} audio path resolves outside the output root: "
                f"{row['audio']!r}"
            ) from exc

        destination_key = os.path.normcase(os.path.normpath(str(destination)))
        previous_row = seen_destinations.get(destination_key)
        if previous_row is not None:
            raise ValueError(
                f"manifest row {row_number} has duplicate audio destination from row {previous_row}"
            )
        seen_destinations[destination_key] = row_number

        if destination.exists() and not destination.is_file():
            raise ValueError(
                f"manifest row {row_number} audio destination is not a file: {destination}"
            )
        destinations.append(destination)

    return destinations


def _render(
    rows: Sequence[dict],
    destinations: Sequence[Path],
    settings: Settings,
    request_interval_seconds: float,
) -> None:
    clients: dict[str, TimbreClient] = {}
    requests_sent = 0
    render_error: BaseException | None = None
    try:
        for row, output_path in zip(rows, destinations, strict=True):
            if output_path.is_file():
                continue

            voice = row["voice"]
            client = clients.get(voice)
            if client is None:
                client = TimbreClient(
                    settings.api_key,
                    voice=voice,
                    base_url=settings.gnani_base_url,
                )
                clients[voice] = client

            if requests_sent:
                time.sleep(request_interval_seconds)
            mulaw_audio = client.synthesize(row["text"])
            wav_audio = mulaw_to_wav(mulaw_audio)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(wav_audio)
            requests_sent += 1
    except BaseException as exc:
        render_error = exc
        raise
    finally:
        close_errors = _close_clients(clients)
        if close_errors:
            if render_error is not None:
                for voice, exc in close_errors:
                    render_error.add_note(
                        f"Failed to close Timbre client for voice {voice!r}: {exc!r}"
                    )
            else:
                _, first_error = close_errors[0]
                for voice, exc in close_errors[1:]:
                    first_error.add_note(
                        f"Also failed to close Timbre client for voice {voice!r}: {exc!r}"
                    )
                raise first_error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="UTF-8 JSONL input manifest")
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=DEFAULT_AUDIO_DIR,
        help=f"WAV output directory (default: {DEFAULT_AUDIO_DIR})",
    )
    parser.add_argument("--live", action="store_true", help="synthesize missing audio with Timbre")
    parser.add_argument(
        "--request-interval-seconds",
        type=float,
        default=1.0,
        help="minimum pause between noncached TTS requests",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not math.isfinite(args.request_interval_seconds) or args.request_interval_seconds < 0:
        parser.error("--request-interval-seconds must be finite and non-negative")

    rows = _read_manifest(args.manifest)
    if args.live:
        destinations = _preflight_live_rows(rows, args.audio_dir)
        estimate = forecast(rows)
        settings = Settings.load()
        settings.require_gnani()
        print(json.dumps(estimate, ensure_ascii=False, indent=2))
        _render(rows, destinations, settings, args.request_interval_seconds)
    else:
        estimate = forecast(rows)
        print(json.dumps(estimate, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
