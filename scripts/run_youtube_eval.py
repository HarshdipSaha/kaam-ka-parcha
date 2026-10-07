"""Forecast or run Prisma over the real YouTube workshop recordings and score annotated amounts.

Dry-run forecast by default; --live makes paid Prisma calls (audio stays under var/, results under var/lab/).
Resumable: transcripts already in the output JSONL are not requested again.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
import wave

from parcha.audio import codec_round_trip, normalize_upload
from parcha.config import Settings
from parcha.gnani import GnaniError, PrismaClient
from parcha.lab.youtube_eval import ChunkResult, score_case, split_wav, summarize
from parcha.vocabulary import AUTOMOTIVE_BIAS_WORDS

MANIFEST = Path("var/benchmark_audio/youtube_mechanic_benchmark.json")
CONDITIONS = ("control", "g711|clean")
PRISMA_CREDITS_PER_SECOND = 0.2


def condition_audio(chunk: bytes, condition: str) -> bytes:
    if condition == "control":
        return chunk
    codec = condition.split("|", maxsplit=1)[0]
    return codec_round_trip(normalize_upload(chunk, "audio/wav", sample_rate=8000), codec)


def duration(wav: bytes) -> float:
    import io

    with wave.open(io.BytesIO(wav), "rb") as w:
        return w.getnframes() / w.getframerate()


def load_cases() -> list[dict]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["cases"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--max-credits", type=float, default=3000.0)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=Path("var/lab/youtube_eval.jsonl"))
    args = parser.parse_args(argv)

    cases = load_cases()
    chunked = {c["id"]: split_wav(Path(c["audio_16k_wav"]).read_bytes()) for c in cases}
    seconds = sum(duration(chunk) for chunks in chunked.values() for chunk in chunks)
    credits = seconds * len(CONDITIONS) * 2 * PRISMA_CREDITS_PER_SECOND
    plan = {"cases": len(cases), "chunks": sum(len(v) for v in chunked.values()), "audio_seconds": round(seconds, 1),
            "conditions": len(CONDITIONS), "stt_calls": sum(len(v) for v in chunked.values()) * len(CONDITIONS) * 2,
            "estimated_credits": round(credits, 2), "credit_cap": args.max_credits, "within_cap": credits <= args.max_credits}
    print(json.dumps(plan, indent=2))
    if not args.live:
        return 0
    if not plan["within_cap"]:
        parser.error("forecast exceeds --max-credits")
    if Path("var/lab").resolve() not in args.output.resolve().parents:
        parser.error("--output must stay beneath var/lab")

    settings = Settings.load()
    settings.require_gnani()
    prisma = PrismaClient(settings.api_key, base_url=settings.gnani_base_url)
    done: dict[tuple, str] = {}
    if args.output.exists():
        for line in args.output.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            done[(row["case"], row["condition"], row["chunk"], row["mode"])] = row["text"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a", encoding="utf-8", newline="\n") as stream:
        for case in cases:
            for condition in CONDITIONS:
                for index, chunk in enumerate(chunked[case["id"]]):
                    audio = None
                    for mode in ("verbatim", "transcribe"):
                        key = (case["id"], condition, index, mode)
                        if key in done:
                            continue
                        audio = audio or condition_audio(chunk, condition)
                        for attempt in range(4):
                            try:
                                text = prisma.transcribe(
                                    audio, mode=mode,
                                    bias=list(AUTOMOTIVE_BIAS_WORDS) if mode == "verbatim" else None)
                                break
                            except GnaniError as exc:
                                if exc.status not in (429, 503, 504) or attempt == 3:
                                    raise
                                time.sleep(10 * (attempt + 1))
                        row = {"case": case["id"], "condition": condition, "chunk": index, "mode": mode, "text": text}
                        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                        stream.flush()
                        done[key] = text
                        time.sleep(args.interval)
    report = {}
    for condition in CONDITIONS:
        per_case = {}
        for case in cases:
            n = len(chunked[case["id"]])
            chunks = [ChunkResult(done[(case["id"], condition, i, "verbatim")], done[(case["id"], condition, i, "transcribe")])
                      for i in range(n)]
            per_case[case["id"]] = score_case([it["amount_paise"] or 0 for it in case["expected_items"]], chunks)
        report[condition] = {"cases": per_case, "total": summarize(per_case.values())}
    out = args.output.with_suffix(".report.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({c: r["total"] for c, r in report.items()}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
