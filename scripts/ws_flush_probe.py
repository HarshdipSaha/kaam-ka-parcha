import argparse
import asyncio
import io
import json
from pathlib import Path
import re
import sys
import time
from typing import Any
import wave

# Ensure src is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from parcha.config import Settings
from parcha.credits import BudgetExceeded
from parcha.gnani_ws import WS_URL, pcm_frames, silence_frames, telephony_headers

DEFAULT_MANIFEST = Path("var/gates/haan_ws.jsonl")
DEFAULT_OUTPUT = Path("var/gates/ws_flush_results.jsonl")
DEFAULT_MAX_CREDITS = 2000.0
DEFAULT_SILENCE_MS = [500]
PASS_THRESHOLD = 0.95

AFFIRMATIVE_MAPPINGS: dict[str, list[str]] = {
    "haan": ["haan", "ha", "haa", "han", "haanji", "हाँ", "हां", "हा", "हाँजी", "हांजी"],
    "हाँ": ["haan", "ha", "haa", "han", "haanji", "हाँ", "हां", "हा", "हाँजी", "हांजी"],
    "हां": ["haan", "ha", "haa", "han", "haanji", "हाँ", "हां", "हा", "हाँजी", "हांजी"],
    "theek": ["theek", "theek hai", "thik", "thik hai", "theekhai", "ठीक", "ठीक है", "ठिक"],
    "theek hai": ["theek", "theek hai", "thik", "thik hai", "theekhai", "ठीक", "ठीक है", "ठिक"],
    "ठीक": ["theek", "theek hai", "thik", "thik hai", "theekhai", "ठीक", "ठीक है", "ठिक"],
    "ठीक है": ["theek", "theek hai", "thik", "thik hai", "theekhai", "ठीक", "ठीक है", "ठिक"],
    "sahi": ["sahi", "sahi hai", "सही", "सही है"],
    "sahi hai": ["sahi", "sahi hai", "सही", "सही है"],
    "ji": ["ji", "ji haan", "जी", "जी हाँ", "जी हां"],
    "जी": ["ji", "ji haan", "जी", "जी हाँ", "जी हां"],
    "achha": ["achha", "achha hai", "अच्छा", "अच्छा है"],
    "yes": ["yes", "yep", "yeah", "ok", "okay"],
}


def parse_silence_ms(val: Any) -> list[int]:
    """Parse integer, comma-separated string, or list into a list of millisecond integers."""
    if val is None:
        return [500]
    if isinstance(val, int):
        return [val]
    if isinstance(val, list):
        out: list[int] = []
        for item in val:
            out.extend(parse_silence_ms(item))
        return out if out else [500]
    # String input e.g. "250,500,750" or "250 500"
    parts = re.split(r"[,\s]+", str(val).strip())
    results = [int(p) for p in parts if p]
    return results if results else [500]


def normalize_text(text: str) -> str:
    """Normalize text by lowering and removing punctuation."""
    if not text:
        return ""
    cleaned = re.sub(r"[।.,?!;:\"'()\[\]{}–—\-_/\\|]", " ", text.lower())
    return " ".join(cleaned.split())


def is_affirmative_recovered(transcript: str, target: str | None = None) -> bool:
    """Determine whether terminal affirmative token was recovered or cut off."""
    norm_tx = normalize_text(transcript)
    if not norm_tx:
        return False

    tokens = norm_tx.split()
    if target:
        norm_target = normalize_text(target)
        candidates = AFFIRMATIVE_MAPPINGS.get(norm_target, [norm_target])
        # Check phrase match or token match
        for cand in candidates:
            if cand in norm_tx:
                return True
        for token in tokens:
            if token in candidates:
                return True
        return False

    # No specific target specified: check against any recognized affirmative form
    for variants in AFFIRMATIVE_MAPPINGS.values():
        for variant in variants:
            if variant in norm_tx:
                return True
    return False


def calculate_recovery_rate(recovered: int, total: int) -> tuple[int, int]:
    """Return explicit (numerator, denominator) recovery tuple."""
    return (recovered, total)


def validate_wav_clip(clip_path: Path) -> dict[str, Any]:
    """Validate that WAV is 8 kHz mono 16-bit PCM and return duration."""
    if not clip_path.exists():
        raise FileNotFoundError(f"Audio clip not found: {clip_path}")
    with wave.open(str(clip_path), "rb") as wf:
        framerate = wf.getframerate()
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        nframes = wf.getnframes()
        if (framerate, nchannels, sampwidth) != (8000, 1, 2):
            raise ValueError(
                f"Clip {clip_path} format invalid: {framerate}Hz, {nchannels}ch, "
                f"{sampwidth * 8}bit. Expected 8000Hz mono 16-bit."
            )
        duration = nframes / float(framerate) if framerate > 0 else 0.0
    return {"duration": duration, "nframes": nframes, "valid": True}


async def probe_stream(
    wav_bytes: bytes,
    api_key: str,
    silence_ms: int = 500,
    timeout_s: float = 10.0,
    ws_url: str = WS_URL,
) -> dict[str, Any]:
    """Stream audio frames to Gnani WebSocket and concurrently receive transcripts.

    Never logs or exposes the API key. Records events and close codes cleanly.
    """
    import websockets

    events: list[dict[str, Any]] = []
    close_code: int | None = None
    transcript = ""
    error_msg: str | None = None

    headers = telephony_headers(api_key)

    try:
        async with websockets.connect(
            ws_url,
            additional_headers=headers,
            open_timeout=timeout_s,
        ) as socket:
            async def receive_events() -> str:
                final_text = ""
                while True:
                    raw_msg = await asyncio.wait_for(socket.recv(), timeout=timeout_s)
                    msg = json.loads(raw_msg)
                    # Safe recording: ensure no api_key exposure
                    events.append(msg)
                    if msg.get("type") == "transcript":
                        final_text = str(msg.get("text", ""))
                        return final_text
                    if msg.get("type") == "error":
                        err_text = msg.get("message", "Gnani WS error")
                        raise RuntimeError(f"Gnani WS returned error event: {err_text}")

            receiver = asyncio.create_task(receive_events())
            try:
                frames = pcm_frames(wav_bytes) + silence_frames(8000, silence_ms)
                for frame in frames:
                    await socket.send(frame)
                    await asyncio.sleep(0.064)
                transcript = await asyncio.wait_for(receiver, timeout=timeout_s)
            finally:
                if not receiver.done():
                    receiver.cancel()

            close_code = getattr(socket, "close_code", 1000)
            if close_code is None:
                close_code = 1000

    except Exception as exc:
        raw_err = str(exc)
        if api_key and api_key in raw_err:
            raw_err = raw_err.replace(api_key, "[REDACTED_API_KEY]")
        error_msg = raw_err

    return {
        "transcript": transcript,
        "events": events,
        "close_code": close_code,
        "error": error_msg,
    }


def get_probe_forecast(
    manifest_path: Path | None,
    silence_ms_list: list[int],
    max_credits: float = DEFAULT_MAX_CREDITS,
    credits_per_second: float = 0.2,
) -> dict[str, Any]:
    """Calculate pre-flight test plan and credit forecast."""
    items: list[dict[str, Any]] = []
    manifest_exists = manifest_path is not None and manifest_path.exists()
    clip_durations: list[float] = []

    if manifest_exists:
        with manifest_path.open("r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    items.append(item)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON at {manifest_path}:{line_idx}: {exc}") from exc

        for it in items:
            clip_ref = it.get("audio_path") or it.get("clip")
            if clip_ref:
                c_path = Path(clip_ref)
                if c_path.exists():
                    try:
                        v = validate_wav_clip(c_path)
                        clip_durations.append(v["duration"])
                        continue
                    except Exception:
                        pass
            clip_durations.append(float(it.get("duration", 1.5)))
    else:
        # Default test plan: 50 clips of 1.5 seconds each
        default_count = 50
        items = [{"index": i, "duration": 1.5, "target": "haan"} for i in range(default_count)]
        clip_durations = [1.5] * default_count

    item_count = len(items)
    probe_matrix_count = item_count * len(silence_ms_list)
    base_audio_seconds = sum(clip_durations)
    total_audio_seconds = base_audio_seconds * len(silence_ms_list)
    estimated_credits = total_audio_seconds * credits_per_second
    is_under_cap = estimated_credits <= max_credits

    return {
        "manifest_path": str(manifest_path) if manifest_path else str(DEFAULT_MANIFEST),
        "manifest_exists": manifest_exists,
        "item_count": item_count,
        "silence_ms_list": silence_ms_list,
        "silence_variations": len(silence_ms_list),
        "total_probes": probe_matrix_count,
        "total_audio_seconds": total_audio_seconds,
        "credits_per_second": credits_per_second,
        "estimated_credits": estimated_credits,
        "max_credits": max_credits,
        "is_under_cap": is_under_cap,
    }


def print_test_plan_and_forecast(fc: dict[str, Any]) -> None:
    """Print human-readable dry-run test plan and credit forecast."""
    print("==================================================================")
    print("WebSocket Telephony Flush Experiment - Test Plan & Credit Forecast")
    print("==================================================================")
    print(f"Manifest:              {fc['manifest_path']}")
    print(f"Manifest On Disk:      {'YES' if fc['manifest_exists'] else 'NO (using default 50-clip matrix)'}")
    print(f"Utterances / Clips:    {fc['item_count']}")
    print(f"Silence Tails to Test: {fc['silence_ms_list']} ms ({fc['silence_variations']} variants)")
    print(f"Total Stream Probes:   {fc['total_probes']}")
    print(f"Audio Volume:          {fc['total_audio_seconds']:.2f} seconds")
    print(f"Burn Rate:             {fc['credits_per_second']:.4f} credits/s")
    print(f"Forecast Cost:         {fc['estimated_credits']:.2f} credits")
    print(f"Budget Ceiling:        {fc['max_credits']:.2f} credits")
    status_label = "PASS (Forecast <= Limit)" if fc["is_under_cap"] else "EXCEEDS CAP (Forecast > Limit)"
    print(f"Budget Gate Status:    {status_label}")
    print("==================================================================")
    print("DRY RUN ONLY: No live WebSocket calls executed. Pass --live to run.")


def run_ws_probe(
    manifest_path: Path,
    output_path: Path,
    *,
    live: bool = False,
    max_credits: float = DEFAULT_MAX_CREDITS,
    silence_ms: list[int] | int = 500,
    credits_per_second: float = 0.2,
    timeout_s: float = 10.0,
    ws_url: str = WS_URL,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Execute dry-run forecast or live WebSocket flush probe."""
    silence_list = parse_silence_ms(silence_ms)
    forecast = get_probe_forecast(
        manifest_path=manifest_path,
        silence_ms_list=silence_list,
        max_credits=max_credits,
        credits_per_second=credits_per_second,
    )

    if not live:
        print_test_plan_and_forecast(forecast)
        return {"status": "dry_run", "forecast": forecast}

    # Live execution validations
    if not forecast["is_under_cap"]:
        raise BudgetExceeded(
            f"Forecasted credits {forecast['estimated_credits']:.2f} exceed "
            f"max limit {forecast['max_credits']:.2f}"
        )

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found for live run: {manifest_path}")

    if settings is None:
        settings = Settings.load()
    settings.require_gnani()

    items: list[dict[str, Any]] = []
    with manifest_path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON at {manifest_path}:{line_num}: {exc}") from exc

    if not items:
        raise ValueError(f"Manifest {manifest_path} contains no utterances")

    results: list[dict[str, Any]] = []
    recovered_count = 0
    total_count = 0
    remaining_allowance = max_credits
    halt_reason: str | None = None

    for item_idx, item in enumerate(items):
        clip_path_str = item.get("audio_path") or item.get("clip")
        if not clip_path_str:
            raise ValueError(f"Manifest item {item_idx} missing 'audio_path' or 'clip'")
        clip_path = Path(clip_path_str)
        wav_bytes = clip_path.read_bytes()
        target = item.get("expected") or item.get("expected_word") or item.get("target")

        for sil_ms in silence_list:
            est_cost = (len(wav_bytes) / 16000.0) * credits_per_second
            if remaining_allowance < est_cost:
                halt_reason = "budget_exhausted"
                break

            probe_res = asyncio.run(
                probe_stream(
                    wav_bytes=wav_bytes,
                    api_key=settings.api_key,
                    silence_ms=sil_ms,
                    timeout_s=timeout_s,
                    ws_url=ws_url,
                )
            )

            transcript = probe_res["transcript"]
            recovered = is_affirmative_recovered(transcript, target)
            total_count += 1
            if recovered:
                recovered_count += 1

            remaining_allowance -= est_cost

            # Clean record without sensitive keys
            record = {
                "index": item_idx,
                "audio_path": str(clip_path),
                "silence_ms": sil_ms,
                "target": target,
                "transcript": transcript,
                "recovered": recovered,
                "close_code": probe_res["close_code"],
                "events_count": len(probe_res["events"]),
                "events": probe_res["events"],
                "error": probe_res["error"],
            }
            results.append(record)

            # Check for auth/quota halt
            err = probe_res["error"]
            if err and any(code in err for code in ["403", "429", "Forbidden", "Unauthorized"]):
                halt_reason = f"auth_or_quota_error: {err}"
                break

        if halt_reason:
            break

    rate_tuple = calculate_recovery_rate(recovered_count, total_count)
    recovery_fraction = (recovered_count / total_count) if total_count > 0 else 0.0
    passed = recovery_fraction >= PASS_THRESHOLD
    decision = "GO" if passed else "NO_GO"

    summary = {
        "gate": "ws_telephony_flush_experiment",
        "decision": decision,
        "passed": passed,
        "recovered_count": recovered_count,
        "total_count": total_count,
        "recovery_fraction": recovery_fraction,
        "recovery_rate": f"{recovered_count}/{total_count}",
        "threshold": PASS_THRESHOLD,
        "silence_ms_tested": silence_list,
        "halt_reason": halt_reason,
        "remaining_allowance": remaining_allowance,
    }

    # Ensure output parent directory exists and write results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out_f:
        out_f.write(json.dumps({"type": "summary", **summary}, ensure_ascii=False) + "\n")
        for rec in results:
            out_f.write(json.dumps({"type": "item", **rec}, ensure_ascii=False) + "\n")

    print("\n--- WebSocket Telephony Flush Probe Result ---")
    print(f"Decision:              {decision} (Passed: {passed})")
    print(f"Recovery Rate:         {recovered_count}/{total_count} ({recovery_fraction * 100:.1f}%)")
    print(f"Gate Pass Threshold:   >= {PASS_THRESHOLD * 100:.0f}%")
    print(f"Results Written To:    {output_path}")

    return {"status": "completed", "summary": summary, "results": results}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run 8 kHz WebSocket Telephony Flush Experiment"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Execute live calls against Gnani WebSocket STT. If omitted, dry run exits 0.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to JSONL manifest of test utterances (default: var/gates/haan_ws.jsonl)",
    )
    parser.add_argument(
        "--max-credits",
        type=float,
        default=DEFAULT_MAX_CREDITS,
        help="Maximum STT credit ceiling (default: 2000)",
    )
    parser.add_argument(
        "--silence-ms",
        nargs="*",
        default=[500],
        help="Silence padding tail in ms (default: 500, or list e.g. 250,500,750)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destination path for output JSONL (default: var/gates/ws_flush_results.jsonl)",
    )
    parser.add_argument(
        "--credits-per-second",
        type=float,
        default=0.2,
        help="STT credit burn rate per second (default: 0.2)",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=10.0,
        help="Timeout in seconds for stream responses (default: 10.0)",
    )
    parser.add_argument(
        "--ws-url",
        type=str,
        default=WS_URL,
        help=f"WebSocket endpoint URL (default: {WS_URL})",
    )
    args = parser.parse_args(argv)
    args.silence_ms = parse_silence_ms(args.silence_ms)
    return args


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    args = parse_args(argv)
    try:
        run_ws_probe(
            manifest_path=args.manifest,
            output_path=args.output,
            live=args.live,
            max_credits=args.max_credits,
            silence_ms=args.silence_ms,
            credits_per_second=args.credits_per_second,
            timeout_s=args.timeout_s,
            ws_url=args.ws_url,
        )
        return 0
    except BudgetExceeded as exc:
        sys.stderr.write(f"Budget exceeded: {exc}\n")
        return 1
    except Exception as exc:
        sys.stderr.write(f"WebSocket probe execution failed: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
