"""Forecast or run the whole-estimate repeat benchmark (paid Timbre + Prisma calls only with --live).

Forecast first (the default), then add --live with a --max-credits cap. Resumes: finished rows are skipped.
Outputs stay under ignored var/lab/. Synthetic speech only; see docs/gates.md for how results are reported.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

from parcha.audio import codec_round_trip, mix_at_snr, mulaw_to_wav, normalize_upload
from parcha.config import DEFAULT_TELEPHONY_NOISE_PATH, Settings
from parcha.gnani import PrismaClient, TimbreClient
from parcha.lab.estimate_repeat_bench import CONDITIONS, VOICES, build_cases, paired_estimates, summarize_pairs

TTS_CREDITS_PER_CHAR = 0.05
PRISMA_CREDITS_PER_SECOND = 0.2
ASSUMED_SECONDS_PER_ITEM = 3.0  # forecast only


def forecast(cases, max_credits: float) -> dict:
    chars = sum(len(c.utterance) for c in cases) * len(VOICES)
    seconds = sum(len(c.items) for c in cases) * ASSUMED_SECONDS_PER_ITEM * len(VOICES) * len(CONDITIONS) * 2
    total = chars * TTS_CREDITS_PER_CHAR + seconds * PRISMA_CREDITS_PER_SECOND
    clips = len(cases) * len(VOICES) * len(CONDITIONS)
    return {"cases": len(cases), "voices": len(VOICES), "conditions": len(CONDITIONS), "clips": clips,
            "stt_calls": clips * 2, "tts_chars": chars, "estimated_credits": round(total, 2),
            "credit_cap": max_credits, "within_cap": total <= max_credits}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--max-credits", type=float, default=5000.0)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=Path("var/lab/estimate_repeat.jsonl"))
    parser.add_argument("--held-out", action="store_true", help="fresh amounts the default run did not use")
    parser.add_argument("--seed", type=int, default=20261007)
    parser.add_argument("--rescore", action="store_true", help="replay saved transcripts (no API calls)")
    args = parser.parse_args(argv)

    cases = build_cases(args.count, seed=args.seed, held_out=args.held_out)
    by_id = {c.case_id: c for c in cases}

    if args.rescore:
        rows = [json.loads(line) for line in args.output.read_text(encoding="utf-8").splitlines()]
        report = summarize_pairs(paired_estimates(rows, by_id))
        path = args.output.with_suffix(".rescored.json")
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report["ALL"], ensure_ascii=False, indent=2))
        return 0

    plan = forecast(cases, args.max_credits)
    print(json.dumps(plan, indent=2))
    if not args.live:
        return 0
    if not plan["within_cap"]:
        parser.error("forecast exceeds --max-credits")
    if Path("var/lab").resolve() not in args.output.resolve().parents:
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
                           "utterance": case.utterance, "expected_paise": case.expected,
                           "verbatim": verbatim, "transcribe": transcribe}
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                    stream.flush()
    rows = [json.loads(line) for line in args.output.read_text(encoding="utf-8").splitlines()]
    report = summarize_pairs(paired_estimates(rows, by_id))
    summary_path = args.output.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows; summary at {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
