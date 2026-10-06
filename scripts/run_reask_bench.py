"""Forecast or run the re-ask recovery benchmark (paid Timbre + Prisma calls only with --live)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

from parcha.audio import codec_round_trip, mix_at_snr, mulaw_to_wav, normalize_upload
from parcha.config import DEFAULT_TELEPHONY_NOISE_PATH, Settings
from parcha.gnani import PrismaClient, TimbreClient
from parcha.lab.reask_bench import (CONDITIONS, VOICES, amount_pool, build_cases, paired_outcomes, rescore, score,
                                    summarize)

TTS_CREDITS_PER_CHAR = 0.05
PRISMA_CREDITS_PER_SECOND = 0.2
ASSUMED_CLIP_SECONDS = 3.0  # forecast only; live runs measure nothing here, the summary reports the assumption


def forecast(cases, max_credits: float) -> dict:
    chars = sum(len(c.utterance) for c in cases) * len(VOICES)
    clips = len(cases) * len(VOICES) * len(CONDITIONS)
    stt = clips * 2 * ASSUMED_CLIP_SECONDS * PRISMA_CREDITS_PER_SECOND
    total = chars * TTS_CREDITS_PER_CHAR + stt
    return {"cases": len(cases), "voices": len(VOICES), "conditions": len(CONDITIONS), "clips": clips,
            "stt_calls": clips * 2, "tts_chars": chars, "estimated_credits": round(total, 2),
            "credit_cap": max_credits, "within_cap": total <= max_credits}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--max-credits", type=float, default=3000.0)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=Path("var/lab/reask_recovery.jsonl"))
    parser.add_argument("--held-out", action="store_true", help="fresh amounts none of the default run used")
    parser.add_argument("--seed", type=int, default=20261007)
    parser.add_argument("--rescore", action="store_true", help="re-run today's decision on saved rows (no API calls)")
    args = parser.parse_args(argv)

    if args.rescore:
        rows = rescore(json.loads(line) for line in args.output.read_text(encoding="utf-8").splitlines())
        report = {"single_recording": summarize(rows), "two_recordings": paired_outcomes(rows)}
        path = args.output.with_suffix(".rescored.json")
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({k: v["ALL"] for k, v in report.items()}, ensure_ascii=False, indent=2))
        return 0

    cases = build_cases(amount_pool(args.count, seed=args.seed, held_out=args.held_out))
    plan = forecast(cases, args.max_credits)
    print(json.dumps(plan, indent=2))
    if not args.live:
        return 0
    if not plan["within_cap"]:
        parser.error("forecast exceeds --max-credits")
    resolved = args.output.resolve()
    if Path("var/lab").resolve() not in resolved.parents:
        parser.error("--output must stay beneath var/lab")

    settings = Settings.load()
    settings.require_gnani()
    noise8k = normalize_upload(DEFAULT_TELEPHONY_NOISE_PATH.read_bytes(), "audio/wav", sample_rate=8000)
    prisma = PrismaClient(settings.api_key, base_url=settings.gnani_base_url)
    timbre = {v: TimbreClient(settings.api_key, voice=v, base_url=settings.gnani_base_url) for v in VOICES}

    def degrade(wav: bytes, condition: str) -> bytes:
        if condition == "control":
            return wav
        codec, level = condition.split("|", maxsplit=1)
        mixed = wav if level == "clean" else mix_at_snr(wav, noise8k, float(level))[0]
        return codec_round_trip(mixed, codec)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if args.output.exists():
        for line in args.output.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            done.add((row["case_id"], row["voice"], row["condition"]))
    with args.output.open("a", encoding="utf-8", newline="\n") as stream:
        for case in cases:
            for voice in VOICES:
                if all((case.case_id, voice, cond) in done for cond in CONDITIONS):
                    continue
                wav = mulaw_to_wav(timbre[voice].synthesize(case.utterance))
                for condition in CONDITIONS:
                    if (case.case_id, voice, condition) in done:
                        continue
                    audio = degrade(wav, condition)
                    verbatim = prisma.transcribe(audio, mode="verbatim"); time.sleep(args.interval)
                    transcribe = prisma.transcribe(audio, mode="transcribe"); time.sleep(args.interval)
                    row = {"case_id": case.case_id, "voice": voice, "condition": condition,
                           "utterance": case.utterance, "expected_paise": case.expected_paise,
                           "verbatim": verbatim, "transcribe": transcribe, **score(case, verbatim, transcribe)}
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                    stream.flush()
    rows = [json.loads(line) for line in args.output.read_text(encoding="utf-8").splitlines()]
    summary_path = args.output.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summarize(rows), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows; summary at {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
