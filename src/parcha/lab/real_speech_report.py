"""Licensed real-speech robustness: relative degradation of transcript quality from clean to noisy phone lines.

Input is the IndicContextEval (AI4Bharat, CC BY 4.0) sweep rows. Only licensed dataset rows are used; any other
source in the file is dropped. Metrics are reported as *relative* change against the same clips on a clean line
(own pipeline, paired by clip), split by the dataset's code-mix flag. The public form is fail-closed like
`parcha.lab.report.public_delta`: it needs a recorded organiser consent reference and never prints absolute
CER/WER or competitor names.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from random import Random
import statistics
import sys
from typing import Any, Iterable, Mapping

from parcha.lab.report import _validate_competitor_free, _validate_no_absolute_metrics

__all__ = ["licensed_rows", "public_summary", "private_summary", "relative_degradation"]

ATTRIBUTION = (
    "Speech data: AI4Bharat IndicContextEval (Hindi), licensed CC BY 4.0 "
    "(https://huggingface.co/datasets/ai4bharat/IndicContextEval). No endorsement by AI4Bharat is implied."
)
SNR_ORDER = ("10dB", "5dB", "0dB")
METRICS = ("cer", "wer")


def licensed_rows(rows: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Licensed dataset rows only: anything not from the CC BY 4.0 open dataset is excluded."""
    return [r for r in rows if r.get("source") == "open_dataset" and r.get("source_license") == "CC BY 4.0"
            and r.get("clip_type", "speech") == "speech" and r.get("cer") is not None]


def _snr_label(snr: float | None) -> str:
    return "clean" if snr is None else f"{int(snr)}dB"


def _code_mix(row: Mapping[str, Any]) -> str:
    stratum = str(row.get("stratum", ""))
    return "code_mixed" if stratum.endswith("code_mixed=true") else "monolingual"


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else float("nan")


def relative_degradation(rows: Iterable[Mapping[str, Any]], *, bootstrap: int = 1000, seed: int = 20261007) -> list[dict]:
    """One entry per (slice, mode, codec, snr, metric): relative change vs clean on the same clips, 95% CI over clips."""
    by_clip: dict[tuple, dict[str, float]] = defaultdict(dict)
    meta: dict[str, str] = {}
    for r in licensed_rows(rows):
        label = _snr_label(r.get("snr"))
        for metric in METRICS:
            by_clip[(r["stt_mode"], r["codec"], metric, r["clip_id"])][label] = float(r[metric])
        meta[r["clip_id"]] = _code_mix(r)
    rng = Random(seed)
    out = []
    keys = sorted({(m, c, k) for (m, c, k, _) in by_clip})
    for mode, codec, metric in keys:
        clips = sorted(cid for (m, c, k, cid) in by_clip if (m, c, k) == (mode, codec, metric))
        for slice_name in ("all", "code_mixed", "monolingual"):
            members = [cid for cid in clips if slice_name == "all" or meta[cid] == slice_name]
            for snr in SNR_ORDER:
                paired = [(by_clip[(mode, codec, metric, cid)]["clean"], by_clip[(mode, codec, metric, cid)][snr])
                          for cid in members
                          if "clean" in by_clip[(mode, codec, metric, cid)] and snr in by_clip[(mode, codec, metric, cid)]]
                if not paired:
                    continue

                def rel(sample: list[tuple[float, float]]) -> float:
                    base = _mean([a for a, _ in sample])
                    return (_mean([b for _, b in sample]) - base) / base * 100 if base else float("nan")

                boots = sorted(rel([rng.choice(paired) for _ in paired]) for _ in range(bootstrap))
                out.append({"slice": slice_name, "mode": mode, "codec": codec, "snr": snr, "metric": metric,
                            "clips": len(paired), "relative_change_pct": rel(paired),
                            "ci95_low": boots[int(0.025 * bootstrap)], "ci95_high": boots[int(0.975 * bootstrap) - 1]})
    return out


def _table(entries: list[dict], metric: str, slice_name: str) -> list[str]:
    lines = ["| mode | codec | 10 dB | 5 dB | 0 dB |", "|---|---|---|---|---|"]
    index = {(e["mode"], e["codec"], e["snr"]): e for e in entries if e["metric"] == metric and e["slice"] == slice_name}
    for mode, codec in sorted({(m, c) for (m, c, _) in index}):
        cells = []
        for snr in SNR_ORDER:
            e = index.get((mode, codec, snr))
            cells.append(f"{e['relative_change_pct']:+.0f}% [{e['ci95_low']:+.0f}, {e['ci95_high']:+.0f}]" if e else "n/a")
        lines.append(f"| {mode} | {codec} | " + " | ".join(cells) + " |")
    return lines


def _render(entries: list[dict], title: str, intro: str, clip_count: int) -> str:
    lines = [f"# {title}", "", intro, "", f"Clips: {clip_count} licensed speakers, one Prisma recogniser, Hindi. "
             "Cells are the relative change in error versus the same clips on a clean line, with a 95% bootstrap interval over clips.", ""]
    for slice_name in ("all", "code_mixed", "monolingual"):
        for metric in METRICS:
            lines += [f"## {metric.upper()} relative change, {slice_name.replace('_', '-')} clips", ""]
            lines += _table(entries, metric, slice_name) + [""]
    lines += [ATTRIBUTION, ""]
    return "\n".join(lines)


def private_summary(rows: Iterable[Mapping[str, Any]]) -> str:
    rows = list(rows)
    kept = licensed_rows(rows)
    entries = relative_degradation(kept)
    clip_count = len({r["clip_id"] for r in kept})
    dropped = len(rows) - len(kept)
    intro = f"Private run summary. {dropped} non-licensed or unscored rows were excluded before analysis."
    return _render(entries, "Licensed real-speech robustness (private)", intro, clip_count)


def public_summary(rows: Iterable[Mapping[str, Any]], *, organizer_consent: bool, consent_ref: str | None) -> str:
    if not organizer_consent or not consent_ref or not consent_ref.strip():
        raise PermissionError("Public report requires written organizer consent and reference")
    _validate_competitor_free(consent_ref, context="consent_ref")
    kept = licensed_rows(rows)
    entries = relative_degradation(kept)
    intro = (f"Own-pipeline relative deltas on matched clips, measured on 8 kHz phone-line simulation. "
             f"Organizer written consent reference: {consent_ref}.")
    text = _render(entries, "Phone-line robustness on licensed Hindi speech", intro, len({r["clip_id"] for r in kept}))
    _validate_competitor_free(text, context="rendered report")
    _validate_no_absolute_metrics(text)
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("var/lab/real_audio_results.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("var/lab/real_speech_private.md"))
    parser.add_argument("--public", action="store_true", help="write the guarded public summary instead")
    parser.add_argument("--organizer-consent-recorded", action="store_true")
    parser.add_argument("--consent-ref", default=None)
    args = parser.parse_args(argv)
    rows = [json.loads(line) for line in args.results.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.public:
        try:
            text = public_summary(rows, organizer_consent=args.organizer_consent_recorded, consent_ref=args.consent_ref)
        except PermissionError as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 2
    else:
        if Path("var/lab").resolve() not in args.out.resolve().parents:
            parser.error("the private report must stay beneath var/lab")
        text = private_summary(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
