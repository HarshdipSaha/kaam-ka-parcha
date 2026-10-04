import argparse
import asyncio
import io
import json
from pathlib import Path
import re
import sys
from typing import Any
import wave

# Ensure src is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from parcha.audio import codec_round_trip, mulaw_to_wav
from parcha.config import Settings
from parcha.credits import (
    BudgetExceeded,
    count_exact_amounts,
    drop_rate,
    hallucinated_word_rate,
)
from parcha.gnani import GnaniError, PrismaClient, TimbreClient
from parcha.gnani_ws import transcribe_telephony


def extract_amount_from_text(text: str) -> int | None:
    if not text:
        return None
    match = re.search(r"\b(\d+)\b", text)
    if match:
        return int(match.group(1))

    hindi_map = {
        "चार सौ पचास": 450,
        "छह सौ पचास": 650,
        "छः सौ पचास": 650,
        "दो सौ": 200,
        "तीन सौ": 300,
        "चार सौ": 400,
        "पाँच सौ": 500,
        "पांच सौ": 500,
        "छह सौ": 600,
        "सात सौ": 700,
        "आठ सौ": 800,
        "नौ सौ": 900,
        "हज़ार": 1000,
        "हजार": 1000,
    }
    for phrase, val in sorted(hindi_map.items(), key=lambda x: -len(x[0])):
        if phrase in text:
            return val
    return None


def is_auth_or_rate_limit(exc: Exception) -> bool:
    msg = str(exc).lower()
    if "403" in msg or "429" in msg or "forbidden" in msg or "too many requests" in msg:
        return True
    resp = getattr(exc, "response", None)
    if resp is not None and getattr(resp, "status_code", None) in (403, 429):
        return True
    return False


def get_forecast(
    mode: str,
    manifest_path: Path | None,
    credits_per_second: float,
    max_credits: float,
    remaining_credits: float,
    tts_credit_reserve: float = 0.0,
    transport: str = "rest",
) -> dict[str, Any]:
    default_manifests = {
        "garage": (10, 6.0, 0.0),
        "tts-roundtrip": (10, 4.0, 10.0),
        "short-replies": (70, 2.3, 0.0),
        "bias-ab": (30, 18.0, 0.0),
    }

    items: list[dict] = []
    if manifest_path and manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    if items:
        item_count = len(items)
        if mode == "bias-ab":
            stt_seconds = sum(float(item.get("duration", 6.0)) * 3 for item in items)
            tts_credits = tts_credit_reserve
        elif mode == "tts-roundtrip":
            stt_seconds = sum(float(item.get("duration", 4.0)) for item in items)
            tts_credits = tts_credit_reserve if tts_credit_reserve > 0 else float(item_count)
        elif mode == "short-replies":
            stt_seconds = sum(
                float(item.get("duration", 3.0 if item.get("clip_type") == "engine" else 2.0))
                for item in items
            )
            tts_credits = tts_credit_reserve
        else:
            stt_seconds = sum(float(item.get("duration", 6.0)) for item in items)
            tts_credits = tts_credit_reserve
    else:
        def_count, def_dur, def_tts = default_manifests.get(mode, (10, 6.0, 0.0))
        item_count = def_count
        stt_seconds = def_count * def_dur
        tts_credits = tts_credit_reserve if tts_credit_reserve > 0 else def_tts

    stt_credits = stt_seconds * credits_per_second
    total_credits = stt_credits + tts_credits
    cap = min(max_credits, remaining_credits)
    is_under_cap = total_credits <= cap

    return {
        "mode": mode,
        "transport": transport,
        "manifest_path": str(manifest_path) if manifest_path else f"var/gates/{mode}.jsonl",
        "item_count": item_count,
        "stt_seconds": stt_seconds,
        "credits_per_second": credits_per_second,
        "stt_credits": stt_credits,
        "tts_credits": tts_credits,
        "total_credits": total_credits,
        "max_credits": max_credits,
        "remaining_credits": remaining_credits,
        "cap": cap,
        "is_under_cap": is_under_cap,
    }


def print_forecast(fc: dict[str, Any]) -> None:
    print("==================================================")
    print("Early Gate Pre-Flight Credit Forecast")
    print("==================================================")
    print(f"Mode:                  {fc['mode']}")
    print(f"Transport:             {fc['transport']}")
    print(f"Manifest:              {fc['manifest_path']} ({fc['item_count']} items)")
    print(f"Audio Duration:        {fc['stt_seconds']:.2f} s")
    print(f"Burn Rate:             {fc['credits_per_second']:.4f} credits/s")
    print(f"STT Credits:           {fc['stt_credits']:.2f}")
    print(f"TTS Credits:           {fc['tts_credits']:.2f}")
    print(f"Total Forecast:        {fc['total_credits']:.2f} credits")
    print(f"Max Credit Cap:        {fc['max_credits']:.2f} credits")
    print(f"Remaining Dashboard:   {fc['remaining_credits']:.2f} credits")
    print(f"Effective Limit:       {fc['cap']:.2f} credits")
    status_str = "PASS (Forecast <= Limit)" if fc["is_under_cap"] else "FAIL (Forecast > Limit)"
    print(f"Budget Status:         {status_str}")
    print("==================================================")
    print("DRY RUN ONLY: No network calls executed. Pass --live to run.")


def load_manifest_items(manifest_path: Path) -> list[dict[str, Any]]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    items = []
    with manifest_path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON at {manifest_path}:{line_num}: {exc}") from exc
    return items


def run_early_gates(
    mode: str,
    manifest_path: Path,
    *,
    live: bool = False,
    max_credits: float = 2000.0,
    credits_per_second: float = 0.2,
    remaining_credits: float = 5000.0,
    tts_credit_reserve: float = 0.0,
    transport: str = "rest",
    output_path: Path | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    fc = get_forecast(
        mode=mode,
        manifest_path=manifest_path,
        credits_per_second=credits_per_second,
        max_credits=max_credits,
        remaining_credits=remaining_credits,
        tts_credit_reserve=tts_credit_reserve,
        transport=transport,
    )

    if not live:
        print_forecast(fc)
        return {"status": "dry_run", "forecast": fc}

    # Live execution validations
    if not fc["is_under_cap"]:
        raise BudgetExceeded(
            f"Forecast {fc['total_credits']:.2f} credits exceeds cap {fc['cap']:.2f}"
        )

    items = load_manifest_items(manifest_path)
    if not items:
        raise ValueError(f"Manifest {manifest_path} contains no evaluation items")

    if settings is None:
        settings = Settings.load()
    settings.require_gnani()

    prisma = PrismaClient(settings.api_key, base_url=settings.gnani_base_url)
    timbre = TimbreClient(
        settings.api_key, voice=settings.tts_voice, base_url=settings.gnani_base_url
    )

    remaining_allowance = fc["cap"]
    results: list[dict[str, Any]] = []
    halt_reason: str | None = None

    for idx, item in enumerate(items):
        item_dur = float(item.get("duration", 6.0))
        item_tts_cost = 1.0 if mode == "tts-roundtrip" else 0.0
        item_stt_cost = item_dur * credits_per_second * (3 if mode == "bias-ab" else 1)
        est_cost = item_stt_cost + item_tts_cost

        if remaining_allowance < est_cost:
            print(
                f"Budget limit reached before item {idx}: allowance {remaining_allowance:.2f} < estimated cost {est_cost:.2f}. Halting."
            )
            halt_reason = "budget_exhausted"
            break

        try:
            if mode == "garage":
                audio_path = Path(item.get("audio_path", item.get("clip", "")))
                wav_bytes = audio_path.read_bytes()
                if transport == "ws":
                    transcript, _ = asyncio.run(
                        transcribe_telephony(wav_bytes, settings.api_key)
                    )
                else:
                    transcript = prisma.transcribe(wav_bytes, mode="transcribe")
                expected = item.get("expected_amount")
                predicted = extract_amount_from_text(transcript)
                record = {
                    "index": idx,
                    "audio_path": str(audio_path),
                    "expected_amount": expected,
                    "predicted_amount": predicted,
                    "transcript": transcript,
                    "match": (expected is not None and expected == predicted),
                }

            elif mode == "tts-roundtrip":
                text = item.get("text", "कुल ₹650")
                expected = item.get("expected_amount")
                mulaw_raw = timbre.synthesize(text)
                wav = mulaw_to_wav(mulaw_raw)
                g711_wav = codec_round_trip(wav, "g711")
                if transport == "ws":
                    transcript, _ = asyncio.run(
                        transcribe_telephony(g711_wav, settings.api_key)
                    )
                else:
                    transcript = prisma.transcribe(g711_wav, mode="transcribe")
                predicted = extract_amount_from_text(transcript)
                record = {
                    "index": idx,
                    "text": text,
                    "expected_amount": expected,
                    "predicted_amount": predicted,
                    "transcript": transcript,
                    "match": (expected is not None and expected == predicted),
                }

            elif mode == "short-replies":
                audio_path = Path(item.get("audio_path", item.get("clip", "")))
                wav_bytes = audio_path.read_bytes()
                clip_type = item.get("clip_type", "speech")
                if transport == "ws":
                    transcript, _ = asyncio.run(
                        transcribe_telephony(wav_bytes, settings.api_key)
                    )
                else:
                    transcript = prisma.transcribe(wav_bytes, mode="transcribe")
                record = {
                    "index": idx,
                    "audio_path": str(audio_path),
                    "clip_type": clip_type,
                    "transcript": transcript,
                }

            elif mode == "bias-ab":
                audio_path = Path(item.get("audio_path", item.get("clip", "")))
                wav_bytes = audio_path.read_bytes()
                bias_list = item.get("bias_list", [])
                target_parts = item.get("target_parts", bias_list)

                base_tx = prisma.transcribe(wav_bytes, mode="verbatim", bias=None)
                b1_tx = prisma.transcribe(
                    wav_bytes, mode="verbatim", bias=bias_list, score=1.0
                )
                b15_tx = prisma.transcribe(
                    wav_bytes, mode="verbatim", bias=bias_list, score=1.5
                )

                base_matches = sum(1 for p in target_parts if p in base_tx)
                b1_matches = sum(1 for p in target_parts if p in b1_tx)
                b15_matches = sum(1 for p in target_parts if p in b15_tx)
                gain = max(b1_matches, b15_matches) - base_matches

                record = {
                    "index": idx,
                    "audio_path": str(audio_path),
                    "target_parts": target_parts,
                    "baseline_transcript": base_tx,
                    "biased_1_0_transcript": b1_tx,
                    "biased_1_5_transcript": b15_tx,
                    "baseline_matches": base_matches,
                    "biased_best_matches": max(b1_matches, b15_matches),
                    "gain": gain,
                }
            else:
                raise ValueError(f"Unknown mode: {mode}")

            remaining_allowance -= est_cost
            results.append(record)

        except Exception as exc:
            if is_auth_or_rate_limit(exc):
                print(f"HTTP 403/429 encountered: {exc}. Halting immediately.")
                halt_reason = f"http_{type(exc).__name__}"
                results.append({"index": idx, "error": str(exc), "status": "halted"})
                break
            raise

    # Calculate gate outcome
    if mode in ("garage", "tts-roundtrip"):
        expected_all = [r.get("expected_amount") for r in results if "expected_amount" in r]
        predicted_all = [r.get("predicted_amount") for r in results if "expected_amount" in r]
        num, den = count_exact_amounts(expected_all, predicted_all)
        threshold = 0.70 if mode == "garage" else 0.90
        pass_rate = (num / den) if den > 0 else 0.0
        passed = pass_rate >= threshold
        decision = "GO" if passed else "NO_GO"
        summary = {
            "mode": mode,
            "decision": decision,
            "passed": passed,
            "numerator": num,
            "denominator": den,
            "rate": pass_rate,
            "threshold": threshold,
            "halt_reason": halt_reason,
            "remaining_allowance": remaining_allowance,
        }

    elif mode == "short-replies":
        speech = [r["transcript"] for r in results if r.get("clip_type", "speech") == "speech"]
        engine = [r["transcript"] for r in results if r.get("clip_type") == "engine"]
        dropped, sp_total = drop_rate(speech)
        words, eng_total = hallucinated_word_rate(engine)
        drop_ok = (dropped / sp_total <= 0.10) if sp_total > 0 else True
        hallucination_ok = (words / eng_total <= 1.0) if eng_total > 0 else True
        passed = drop_ok and hallucination_ok
        decision = "GO" if passed else "NO_GO"
        summary = {
            "mode": mode,
            "decision": decision,
            "passed": passed,
            "dropped": dropped,
            "speech_total": sp_total,
            "hallucinated_words": words,
            "engine_total": eng_total,
            "halt_reason": halt_reason,
            "remaining_allowance": remaining_allowance,
        }

    elif mode == "bias-ab":
        total_gain = sum(r.get("gain", 0) for r in results if "gain" in r)
        passed = total_gain > 0
        decision = "GO" if passed else "NO_GO"
        summary = {
            "mode": mode,
            "decision": decision,
            "passed": passed,
            "total_gain": total_gain,
            "evaluated_clips": len(results),
            "halt_reason": halt_reason,
            "remaining_allowance": remaining_allowance,
        }

    # Save output jsonl
    out_file = output_path or Path(f"var/gates/{mode}-results.jsonl")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "summary", **summary}, ensure_ascii=False) + "\n")
        for r in results:
            f.write(json.dumps({"type": "item", **r}, ensure_ascii=False) + "\n")

    print("\n--- Early Gate Execution Result ---")
    print(f"Mode: {mode} | Decision: {summary['decision']} | Passed: {summary['passed']}")
    print(f"Remaining Allowance: {remaining_allowance:.2f}")
    print(f"Results written to: {out_file}")

    return {"status": "completed", "summary": summary, "results": results}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run early speech feasibility gates before product UI"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run live paid calls against Gnani APIs",
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["garage", "tts-roundtrip", "short-replies", "bias-ab"],
        help="Gate evaluation mode",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to jsonl manifest",
    )
    parser.add_argument(
        "--max-credits",
        type=float,
        default=2000.0,
        help="Maximum credit budget ceiling (default 2000.0)",
    )
    parser.add_argument(
        "--credits-per-second",
        type=float,
        default=0.2,
        help="STT credits per second (default 0.2)",
    )
    parser.add_argument(
        "--remaining-credits",
        type=float,
        default=5000.0,
        help="Current remaining dashboard credits (default 5000.0)",
    )
    parser.add_argument(
        "--tts-credit-reserve",
        type=float,
        default=0.0,
        help="Reserved credits for TTS",
    )
    parser.add_argument(
        "--transport",
        choices=["rest", "ws"],
        default="rest",
        help="STT transport (rest or ws)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output results jsonl path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = args.manifest or Path(f"var/gates/{args.mode}.jsonl")
    output_path = args.output or Path(f"var/gates/{args.mode}-results.jsonl")

    try:
        run_early_gates(
            mode=args.mode,
            manifest_path=manifest_path,
            live=args.live,
            max_credits=args.max_credits,
            credits_per_second=args.credits_per_second,
            remaining_credits=args.remaining_credits,
            tts_credit_reserve=args.tts_credit_reserve,
            transport=args.transport,
            output_path=output_path,
        )
        return 0
    except BudgetExceeded as exc:
        sys.stderr.write(f"Budget exceeded: {exc}\n")
        return 1
    except Exception as exc:
        sys.stderr.write(f"Gate execution failed: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
