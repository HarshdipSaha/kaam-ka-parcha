from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import statistics
import sys
from typing import Any

import numpy as np

from parcha.lab.metrics import hallucinated_words

__all__ = [
    "FORBIDDEN_COMPETITORS",
    "main",
    "parse_args",
    "private_summary",
    "public_delta",
]

FORBIDDEN_COMPETITORS: list[str] = ["whisper", "google", "aws", "azure", "openai"]

_COMPETITOR_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(c) for c in FORBIDDEN_COMPETITORS) + r")\b",
    re.IGNORECASE,
)

_ABSOLUTE_METRIC_PATTERNS = [
    re.compile(r"\b(?:cer|wer)\s*[:=]\s*\d", re.IGNORECASE),
    re.compile(r"\b(?:cer|wer)\s+of\s+\d", re.IGNORECASE),
    re.compile(r"\b(?:cer|wer)\s*\(\s*%\s*\)\s*[:=]\s*\d", re.IGNORECASE),
    re.compile(r"\babsolute\s+(?:cer|wer)\b", re.IGNORECASE),
]


def _validate_competitor_free(data: Any, context: str = "data") -> None:
    """Validate that data does not contain competitor names, raising ValueError if found."""
    if isinstance(data, str):
        match = _COMPETITOR_REGEX.search(data)
        if match:
            found = match.group(0)
            raise ValueError(
                f"Competitor mention '{found}' is strictly forbidden in public delta export ({context})"
            )
    elif isinstance(data, dict):
        for k, v in data.items():
            _validate_competitor_free(k, context=f"dict key '{k}'")
            _validate_competitor_free(v, context=f"value of '{k}'")
    elif isinstance(data, (list, tuple, set)):
        for item in data:
            _validate_competitor_free(item, context=context)


def _validate_no_absolute_metrics(text: str) -> None:
    """Ensure text does not contain absolute CER/WER metrics."""
    for pattern in _ABSOLUTE_METRIC_PATTERNS:
        match = pattern.search(text)
        if match:
            raise ValueError(
                f"Absolute CER/WER metrics ('{match.group(0)}') are forbidden in public delta export"
            )


def _is_engine_row(r: dict[str, Any]) -> bool:
    """Determine whether a result row is an idle/ambient non-speech or engine clip."""
    clip_type = str(r.get("clip_type", "")).lower()
    kind = str(r.get("kind", "")).lower()
    clip_id = str(r.get("clip_id", "")).lower()
    return (
        clip_type in ("engine", "silence", "non_speech", "non-speech")
        or kind in ("engine", "silence", "non_speech", "non-speech")
        or clip_id.startswith("engine")
        or bool(r.get("is_engine"))
        or bool(r.get("is_non_speech"))
    )


def _is_part_matched(row: dict[str, Any]) -> bool | None:
    """Determine whether part name was recovered in hypothesis."""
    if "part_matched" in row:
        return bool(row["part_matched"])
    if "part_recovered" in row:
        return bool(row["part_recovered"])

    parts = row.get("target_parts") or row.get("parts")
    if not parts:
        ent = row.get("entities")
        if isinstance(ent, dict) and "part" in ent:
            parts = [ent["part"]]
        elif "part" in row:
            parts = [row["part"]]

    tx = row.get("transcript")
    if parts and tx is not None:
        tx_norm = str(tx).lower()
        return any(str(p).lower() in tx_norm for p in parts if p)

    if "baseline_matches" in row:
        return row.get("baseline_matches", 0) > 0
    if "biased_best_matches" in row:
        return row.get("biased_best_matches", 0) > 0

    return None


def _is_amount_matched(row: dict[str, Any]) -> bool | None:
    """Determine whether amount was matched in hypothesis."""
    if "amount_matched" in row:
        return bool(row["amount_matched"])
    if "amount_match" in row:
        return bool(row["amount_match"])
    if "expected_amount" in row and "predicted_amount" in row:
        exp = row.get("expected_amount")
        return exp is not None and exp == row.get("predicted_amount")
    return None


def private_summary(rows: list[dict[str, Any]]) -> str:
    """Summarize private lab evaluation results into a Markdown report with tables.

    Aggregates by (codec, snr, loss):
      - total clips (N)
      - mean CER and character counts
      - amount exact-match count & percentage
      - latency statistics (mean, p50, p90)
      - estimated credits spent
    If engine-only rows are present, counts hallucinated words per non-speech clip.
    Never includes competitor benchmarks or comparisons.
    """
    clean_rows: list[dict[str, Any]] = []
    engine_rows: list[dict[str, Any]] = []

    for r in rows:
        # Filter competitor comparison fields or skip competitor benchmark rows
        if any(c in str(r.get("competitor", "")).lower() for c in FORBIDDEN_COMPETITORS):
            continue
        if any(c in str(r.get("model", "")).lower() for c in FORBIDDEN_COMPETITORS):
            continue

        if _is_engine_row(r):
            engine_rows.append(r)
        else:
            clean_rows.append(r)

    # Group clean rows by (codec, snr, loss)
    groups: dict[tuple[str, Any, float], list[dict[str, Any]]] = {}
    for r in clean_rows:
        codec = r.get("codec")
        codec_str = str(codec) if codec is not None else "default"
        snr = r.get("snr")
        loss = float(r.get("loss", 0.0))
        key = (codec_str, snr, loss)
        if key not in groups:
            groups[key] = []
        groups[key].append(r)

    lines: list[str] = [
        "# Private Lab Evaluation Summary",
        "",
        "> **Internal Notice**: Confidential private evaluation results. Competitor benchmarks and comparisons are strictly omitted under the zero-leak policy.",
        "",
        "## Summary of Conditions Evaluated",
        "",
    ]

    if not groups and not engine_rows:
        lines.append("No evaluation rows provided.\n")
        return "\n".join(lines)

    if groups:
        lines.extend([
            "| Codec | SNR | Loss | N | Mean CER | Total Chars | Amount Match (%) | Latency Mean (ms) | Latency p50 (ms) | Latency p90 (ms) | Est. Credits Spent |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ])

        total_clips = 0
        total_credits = 0.0
        all_cers: list[float] = []
        total_amt_matched = 0
        total_amt_evaluated = 0

        # Sort groups deterministically: codec, snr (clean first, then descending), loss
        def sort_key(k: tuple[str, Any, float]) -> tuple[str, float, float]:
            c, s, l = k
            snr_val = -1000.0 if s is None or s == "clean" else float(s)
            return (c, -snr_val, l)

        for key in sorted(groups.keys(), key=sort_key):
            group_items = groups[key]
            n = len(group_items)
            total_clips += n

            # CER
            cers = [float(item["cer"]) for item in group_items if item.get("cer") is not None]
            all_cers.extend(cers)
            mean_cer = sum(cers) / len(cers) if cers else 0.0

            # Character counts
            chars = sum(
                len(str(item.get("reference") or item.get("reference_transcribe") or item.get("text") or ""))
                for item in group_items
            )

            # Amount exact match
            amt_evaluated = sum(1 for item in group_items if _is_amount_matched(item) is not None)
            amt_matched = sum(1 for item in group_items if _is_amount_matched(item) is True)
            total_amt_matched += amt_matched
            total_amt_evaluated += amt_evaluated
            if amt_evaluated > 0:
                amt_pct = (amt_matched / amt_evaluated) * 100.0
                amt_str = f"{amt_matched}/{amt_evaluated} ({amt_pct:.1f}%)"
            else:
                amt_str = "N/A"

            # Latencies
            lats = [float(item["latency_ms"]) for item in group_items if item.get("latency_ms") is not None]
            if lats:
                mean_lat = statistics.mean(lats)
                p50_lat = statistics.median(lats)
                p90_lat = float(np.percentile(lats, 90)) if len(lats) > 1 else lats[0]
            else:
                mean_lat, p50_lat, p90_lat = 0.0, 0.0, 0.0

            # Credits
            spent = sum(float(item.get("credits_spent", 0.0)) for item in group_items)
            total_credits += spent

            # Format fields
            codec_disp = key[0]
            snr_disp = "clean" if key[1] is None or key[1] == "clean" else f"{key[1]} dB"
            loss_disp = f"{key[2]:.1f}%" if isinstance(key[2], float) else f"{key[2]}%"

            lines.append(
                f"| {codec_disp} | {snr_disp} | {loss_disp} | {n} | {mean_cer:.4f} | {chars} | {amt_str} | {mean_lat:.1f} | {p50_lat:.1f} | {p90_lat:.1f} | {spent:.2f} |"
            )

        lines.extend([
            "",
            "### Aggregate Metrics",
            f"- **Total Clips Evaluated**: {total_clips}",
            f"- **Overall Mean CER**: {(sum(all_cers) / len(all_cers) if all_cers else 0.0):.4f}",
            f"- **Overall Amount Match**: {total_amt_matched}/{total_amt_evaluated} "
            + (f"({(total_amt_matched / total_amt_evaluated * 100.0):.1f}%)" if total_amt_evaluated > 0 else "(N/A)"),
            f"- **Total Estimated Credits Spent**: {total_credits:.2f}",
            "",
        ])

    # Non-speech / engine hallucination section
    if engine_rows:
        total_engine = len(engine_rows)
        words = [hallucinated_words(r.get("transcript", "")) for r in engine_rows]
        total_words = sum(words)
        rate = total_words / total_engine if total_engine > 0 else 0.0

        lines.extend([
            "## Non-Speech / Engine Idle Evaluation",
            "",
            f"- **Total Non-Speech Clips Evaluated**: {total_engine}",
            f"- **Total Hallucinated Words Emitted**: {total_words}",
            f"- **Mean Hallucinated Words per Clip**: {rate:.2f}",
            "",
            "| Clip ID | Transcript | Hallucinated Word Count |",
            "|---|---|---|",
        ])
        for r, w in zip(engine_rows, words):
            cid = r.get("clip_id") or r.get("id") or "unnamed"
            tx = str(r.get("transcript", "")).replace("|", "\\|")
            lines.append(f"| {cid} | {tx} | {w} |")
        lines.append("")

    return "\n".join(lines)


def public_delta(
    rows: list[dict[str, Any]],
    organizer_consent: bool,
    consent_ref: str | None = None,
    date: str = "2026-10-19",
) -> str:
    """Export guarded public relative evaluation deltas.

    Enforces fail-closed consent guard:
      if not organizer_consent or not consent_ref:
          raise PermissionError("Public delta export requires written organizer consent and reference")

    Pairs rows by (clip_id, codec, snr, loss, seed).
    Looks for paired variant == "bias_off" and variant == "bias_1_0" (or verbatim bias A/B).
    Strictly guards against competitor names and absolute CER/WER metrics.
    """
    # 1. Fail-closed guard
    if not organizer_consent or not consent_ref or not consent_ref.strip():
        raise PermissionError(
            "Public delta export requires written organizer consent and reference"
        )

    # 2. Guard input rows and reference against competitor names
    _validate_competitor_free(consent_ref, context="consent_ref")
    _validate_competitor_free(rows, context="input rows")

    # 3. Pair rows by (clip_id, codec, snr, loss, seed)
    grouped: dict[tuple[Any, Any, Any, Any, Any], dict[str, dict[str, Any]]] = {}

    for r in rows:
        cid = r.get("clip_id") or r.get("id") or r.get("index")
        codec = r.get("codec")
        snr = r.get("snr")
        loss = r.get("loss")
        seed = r.get("seed")
        key = (cid, codec, snr, loss, seed)

        if key not in grouped:
            grouped[key] = {}

        variant = str(r.get("variant", "")).strip().lower()
        if (
            variant in ("bias_off", "baseline", "base", "unbiased", "off")
            or variant.endswith("_bias_off")
            or variant.endswith("_clean")
        ):
            grouped[key]["baseline"] = r
        elif (
            variant in ("bias_1_0", "bias_1.0", "biased_1_0", "biased", "bias_on", "on")
            or variant.endswith("_bias_1_0")
            or variant.endswith("_biased")
        ):
            grouped[key]["biased"] = r

    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for g in grouped.values():
        if "baseline" in g and "biased" in g:
            pairs.append((g["baseline"], g["biased"]))

    # Fallback for single-row pre-paired items (e.g. from bias-ab gate)
    if not pairs:
        for r in rows:
            if ("baseline_matches" in r and "biased_best_matches" in r) or (
                "baseline_transcript" in r and "biased_1_0_transcript" in r
            ):
                pairs.append((r, r))

    if not pairs:
        raise ValueError("No paired baseline/biased variants found in rows for public delta export")

    # 4. Compute recovery deltas
    base_parts = 0
    bias_parts = 0
    part_pairs_count = 0

    base_amts = 0
    bias_amts = 0
    amt_pairs_count = 0

    total_gain_sum = 0
    gain_present = False

    for base, biased in pairs:
        # Check gain attribute directly if present
        if "gain" in biased:
            gain_present = True
            total_gain_sum += int(biased.get("gain", 0))

        bp = _is_part_matched(base)
        bi_p = _is_part_matched(biased)
        if bp is not None and bi_p is not None:
            part_pairs_count += 1
            if bp:
                base_parts += 1
            if bi_p:
                bias_parts += 1

        ba = _is_amount_matched(base)
        bi_a = _is_amount_matched(biased)
        if ba is not None and bi_a is not None:
            amt_pairs_count += 1
            if ba:
                base_amts += 1
            if bi_a:
                bias_amts += 1

    # Extract operational settings from pairs
    codecs_set = {str(b.get("codec")) for b, _ in pairs if b.get("codec") is not None}
    codec_str = ", ".join(sorted(codecs_set)) if codecs_set else "g711"

    snrs_set = {
        "clean" if b.get("snr") is None or b.get("snr") == "clean" else f"{b.get('snr')} dB"
        for b, _ in pairs
    }
    snr_str = ", ".join(sorted(snrs_set)) if snrs_set else "10.0 dB"

    models_set = {str(b.get("model")) for b, _ in pairs if b.get("model")}
    model_str = ", ".join(sorted(models_set)) if models_set else "Prisma REST verbatim"

    scores_set = {
        str(bi.get("score") or bi.get("bias_score"))
        for _, bi in pairs
        if bi.get("score") is not None or bi.get("bias_score") is not None
    }
    score_str = ", ".join(sorted(scores_set)) if scores_set else "1.0"

    n_pairs = len(pairs)

    lines = [
        "# Public Speech Feasibility Delta Export",
        "",
        "## Methodology & Governance",
        "- **Evaluation Methodology**: measured by us",
        f"- **Sample Size**: N={n_pairs}",
        f"- **Evaluation Date**: {date}",
        f"- **Organizer Written Consent Reference**: {consent_ref}",
        "",
        "## Operational Pipeline Settings",
        f"- **Codec**: {codec_str}",
        f"- **SNR**: {snr_str}",
        f"- **Model**: {model_str}",
        f"- **Biasing Score**: {score_str}",
        "",
        "## Paired Recovery Deltas",
        "",
    ]

    has_delta = False
    if part_pairs_count > 0:
        has_delta = True
        delta_count = bias_parts - base_parts
        delta_pct = (delta_count / part_pairs_count) * 100.0
        sign = "+" if delta_count > 0 else ""
        lines.extend([
            f"### Exact Part-Name Recovery Delta",
            f"- **Net Part Recovery Delta**: {sign}{delta_count} ({sign}{delta_pct:.1f}%)",
            f"- **Baseline Recovery (`bias_off`)**: {base_parts}/{part_pairs_count} ({(base_parts / part_pairs_count * 100.0):.1f}%)",
            f"- **Biased Recovery (`bias_1_0`)**: {bias_parts}/{part_pairs_count} ({(bias_parts / part_pairs_count * 100.0):.1f}%)",
            "",
        ])

    if amt_pairs_count > 0:
        has_delta = True
        delta_amt = bias_amts - base_amts
        delta_amt_pct = (delta_amt / amt_pairs_count) * 100.0
        sign = "+" if delta_amt > 0 else ""
        lines.extend([
            f"### Exact Amount Recovery Delta",
            f"- **Net Amount Recovery Delta**: {sign}{delta_amt} ({sign}{delta_amt_pct:.1f}%)",
            f"- **Baseline Amount Recovery**: {base_amts}/{amt_pairs_count} ({(base_amts / amt_pairs_count * 100.0):.1f}%)",
            f"- **Biased Amount Recovery**: {bias_amts}/{amt_pairs_count} ({(bias_amts / amt_pairs_count * 100.0):.1f}%)",
            "",
        ])

    if not has_delta and gain_present:
        sign = "+" if total_gain_sum > 0 else ""
        lines.extend([
            f"### Exact Part-Name Recovery Gain",
            f"- **Total Gain**: {sign}{total_gain_sum}",
            f"- **Evaluated Pairs**: N={n_pairs}",
            "",
        ])

    lines.extend([
        "> **Publication Policy Notice**: All reported figures are own-pipeline relative deltas measured by us on matched audio pairs. In compliance with platform EULA and organizer consent requirements, no absolute error rates or competitor comparisons are included.",
        "",
    ])

    output_text = "\n".join(lines)

    # 5. Strict post-generation guard on public output text
    _validate_competitor_free(output_text, context="rendered public output")
    _validate_no_absolute_metrics(output_text)

    return output_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate private lab summary report and guarded public delta export"
    )
    parser.add_argument(
        "--results-file",
        type=Path,
        required=True,
        help="Path to results JSONL file",
    )
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path("var/lab/private/report.md"),
        help="Destination path for private Markdown report (default: var/lab/private/report.md)",
    )
    parser.add_argument(
        "--public-output",
        type=Path,
        default=None,
        help="Destination path for public delta export Markdown",
    )
    parser.add_argument(
        "--organizer-consent-recorded",
        action="store_true",
        default=False,
        help="Flag indicating written organizer consent has been recorded",
    )
    parser.add_argument(
        "--consent-ref",
        type=str,
        default=None,
        help="Written organizer clarification reference identifier",
    )
    parser.add_argument(
        "--date",
        type=str,
        default="2026-10-19",
        help="Evaluation / report date string (default: 2026-10-19)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.results_file.exists():
        sys.stderr.write(f"Results file not found: {args.results_file}\n")
        return 1

    rows: list[dict[str, Any]] = []
    with args.results_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if isinstance(data, dict):
                    if data.get("type") == "summary":
                        continue
                    rows.append(data)
            except json.JSONDecodeError:
                continue

    # 1. Generate and write private summary
    priv_md = private_summary(rows)
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    args.private_output.write_text(priv_md, encoding="utf-8")
    print(f"Private summary written to: {args.private_output}")

    # 2. If public output specified, export public delta
    if args.public_output is not None:
        pub_md = public_delta(
            rows,
            organizer_consent=args.organizer_consent_recorded,
            consent_ref=args.consent_ref,
            date=args.date,
        )
        args.public_output.parent.mkdir(parents=True, exist_ok=True)
        args.public_output.write_text(pub_md, encoding="utf-8")
        print(f"Public delta export written to: {args.public_output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
