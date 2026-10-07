"""Forecast or run the per-language read-back echo benchmark (paid Timbre + Prisma calls only with --live).

Forecast first (the default), then add --live with a --max-credits cap. Resumes: finished rows are skipped.
Outputs stay under ignored var/lab/. Synthetic speech only; label it as such wherever results are reported.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import httpx

from parcha.audio import codec_round_trip, mix_at_snr, mulaw_to_wav, normalize_upload
from parcha.config import DEFAULT_TELEPHONY_NOISE_PATH, Settings
from parcha.gnani import GnaniError, PrismaClient, TimbreClient
from parcha.lab.language_echo import CONDITIONS, build_cards, readback_text, score, summarize
from parcha.languages import LANGUAGES

TTS_CREDITS_PER_CHAR = 0.05
PRISMA_CREDITS_PER_SECOND = 0.2
ASSUMED_CLIP_SECONDS = 18.0     # a regional read-back with the consent line is long; forecast only


def with_retries(call, *, attempts: int = 4, base_delay: float = 5.0):
    for attempt in range(attempts):
        try:
            return call()
        except (httpx.TimeoutException, httpx.TransportError, GnaniError):
            if attempt == attempts - 1:
                raise
            time.sleep(base_delay * (attempt + 1))


def forecast(languages, cards, max_credits: float) -> dict:
    chars = sum(len(readback_text(c, lang)) * len(LANGUAGES[lang].voices) for lang in languages for c in cards)
    clips = sum(len(cards) * len(LANGUAGES[lang].voices) * len(CONDITIONS) for lang in languages)
    total = chars * TTS_CREDITS_PER_CHAR + clips * ASSUMED_CLIP_SECONDS * PRISMA_CREDITS_PER_SECOND
    return {"languages": list(languages), "cards": len(cards), "conditions": len(CONDITIONS), "tts_chars": chars,
            "stt_clips": clips, "estimated_credits": round(total, 2), "credit_cap": max_credits,
            "within_cap": total <= max_credits}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--languages", default="ta-IN,bn-IN,kn-IN")
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--max-credits", type=float, default=5000.0)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=Path("var/lab/language_echo.jsonl"))
    parser.add_argument("--rescore", action="store_true", help="summarise saved rows (no API calls)")
    args = parser.parse_args(argv)
    languages = [code for code in args.languages.split(",") if code]
    unknown = [code for code in languages if code not in LANGUAGES]
    if unknown:
        parser.error(f"unsupported languages: {unknown}")
    cards = build_cards(args.count)
    by_id = {c.case_id: c for c in cards}

    if args.rescore:
        rows = [json.loads(line) for line in args.output.read_text(encoding="utf-8").splitlines()]
        report = summarize(rows)
        path = args.output.with_suffix(".summary.json")
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report["ranking_by_worst_condition"], ensure_ascii=False, indent=2))
        return 0

    plan = forecast(languages, cards, args.max_credits)
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
    timbre = TimbreClient(settings.api_key, base_url=settings.gnani_base_url)

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
            done.add((row["language"], row["voice"], row["case_id"], row["condition"]))
    with args.output.open("a", encoding="utf-8", newline="\n") as stream:
        for language in languages:
            for voice in LANGUAGES[language].voices:
                for card in cards:
                    if all((language, voice, card.case_id, cond) in done for cond in CONDITIONS):
                        continue
                    text = readback_text(card, language)
                    wav = mulaw_to_wav(with_retries(lambda: timbre.synthesize(text, language=language, voice=voice)))
                    for condition in CONDITIONS:
                        if (language, voice, card.case_id, condition) in done:
                            continue
                        audio = degrade(wav, condition)
                        transcript = with_retries(lambda: prisma.transcribe(audio, mode="transcribe", language_code=language))
                        time.sleep(args.interval)
                        row = {"language": language, "voice": voice, "case_id": card.case_id, "condition": condition,
                               "expected_paise": list(card.amounts), "transcript": transcript, **score(card, transcript)}
                        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                        stream.flush()
    rows = [json.loads(line) for line in args.output.read_text(encoding="utf-8").splitlines()]
    report = summarize(rows)
    summary_path = args.output.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows; summary at {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
