"""Build a private, fail-closed summary of the money-path benchmark."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable

from parcha.lab import report as report_guards
from parcha.lab.amount_bench import BIAS_CONTROL_WORDS
from parcha.lab.money_eval import score_number_agreement


DEFAULT_MONEY_EVAL = Path("var/lab/money_eval_after_repeat_gate.json")
DEFAULT_GRAMVAANI = Path("var/lab/gramvaani_resumed.jsonl")
DEFAULT_BIAS = Path("var/lab/bias_control.jsonl")
DEFAULT_BIAS_MANIFEST = Path("data/benchmarks/amount_v2/bias_control.jsonl")
BIAS_SPOKEN_BY_ENGLISH = {english.casefold(): spoken for english, spoken in BIAS_CONTROL_WORDS}
PRIVATE_OUTPUT_ROOT = Path("var/lab")
DEFAULT_ECHO_FILES = (
    Path("var/lab/echo_screen_resumed4_20261006.jsonl"),
    Path("var/lab/echo_confirm_prompt2_20261007.jsonl"),
)
DEFAULT_USAGE_FILES = (
    Path("var/lab/v2_estimates.jsonl"),
    Path("var/lab/v2_corrections.jsonl"),
    DEFAULT_GRAMVAANI,
    DEFAULT_BIAS,
    Path("var/lab/v2_owner.jsonl"),
)
PRIVATE_NOTICE = "PRIVATE: absolute metrics — do not publish"


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    converted = float(value)
    return converted if math.isfinite(converted) else None


def _percent(value: Any) -> str:
    number = _number(value)
    return "not reported" if number is None else f"{number * 100:.1f}%"


def _value(value: Any, digits: int = 3) -> str:
    number = _number(value)
    return "not reported" if number is None else f"{number:.{digits}f}"


def _percentile(values: list[float], q: float) -> float:
    """Linear-interpolated percentile, matching common inclusive percentile tools."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile requires at least one value")
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _escape_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _render_money_eval(summaries: list[dict[str, Any]]) -> list[str]:
    lines = ["## Amount safety by slice and condition", ""]
    if not summaries:
        lines.extend(["Amount evaluation: not available (no summary rows supplied).", ""])
        return lines

    for row in sorted(summaries, key=lambda item: (str(item.get("slice", "")), str(item.get("condition", "")))):
        slice_name = str(row.get("slice", "unspecified")).replace("\n", " ").replace("\r", " ")
        condition = str(row.get("condition", "unspecified")).replace("\n", " ").replace("\r", " ")
        lines.extend([
            f"### {slice_name} × {condition}",
            "",
            "| amounts | wrong_accepted | wrong_amount_confirmed_upper95 | abstain_rate | top abstain reasons |",
            "|---:|---:|---:|---:|---|",
            "| " + " | ".join((
                _escape_cell(row.get("amounts", "not reported")),
                _escape_cell(row.get("wrong_accepted", "not reported")),
                _percent(row.get("wrong_amount_confirmed_upper95")),
                _percent(row.get("abstain_rate")),
                _escape_cell(_top_reasons(row.get("abstain_reasons"))),
            )) + " |",
            "",
        ])
    return lines


def _top_reasons(raw: Any) -> str:
    if not isinstance(raw, dict) or not raw:
        return "none recorded"
    reasons: list[tuple[str, int]] = []
    for reason, count in raw.items():
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            continue
        reasons.append((str(reason), count))
    reasons.sort(key=lambda pair: (-pair[1], pair[0]))
    return ", ".join(f"{name}: {count}" for name, count in reasons[:5]) or "none recorded"


def _clip_group(row: dict[str, Any]) -> str:
    stratum = str(row.get("stratum", "")).casefold()
    if "unclipped" in stratum:
        return "unclipped"
    if "clipped" in stratum:
        return "clipped"
    return "unspecified"


def _gramvaani_group(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        mode = str(row.get("stt_mode") or "unspecified")
        groups.setdefault((mode, _clip_group(row)), []).append(row)

    result = []
    for (mode, clip_group), group in sorted(groups.items()):
        cer_values = [
            value for row in group
            if (value := _number(row.get("cer_canonical"))) is not None
            and row.get("outcome") == "ok"
        ]
        matched = wrong = abstain = 0
        for row in group:
            outcome = row.get("outcome")
            if (
                (outcome is not None and outcome not in ("ok", "empty_transcript"))
                or row.get("transcription_error")
            ):
                continue
            reference = row.get("reference_canonical", row.get("reference"))
            transcript = row.get("transcript")
            if not isinstance(reference, str) or not reference.strip():
                continue
            if outcome == "empty_transcript":
                hypothesis = ""
            elif isinstance(transcript, str):
                hypothesis = transcript
            else:
                continue
            counts = score_number_agreement(reference, hypothesis)
            matched += counts["matched"]
            wrong += counts["confident_wrong"]
            abstain += counts["abstain_equivalent"]
        empty_count = sum(
            row.get("outcome") == "empty_transcript"
            or (
                row.get("outcome") != "provider_error"
                and not row.get("transcription_error")
                and not str(row.get("transcript") or "").strip()
            )
            for row in group
        )
        result.append({
            "mode": mode,
            "clip_group": clip_group,
            "rows": len(group),
            "cer": sum(cer_values) / len(cer_values) if cer_values else None,
            "matched": matched,
            "wrong": wrong,
            "abstain": abstain,
            "silent_empty": empty_count,
        })
    return result


def _render_gramvaani(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["## Gramvaani speech diagnostics (PRIVATE)", ""]
    if not rows:
        lines.extend(["Gramvaani diagnostics: not available (no result rows supplied).", ""])
        return lines

    grouped = _gramvaani_group(rows)
    lines.extend([
        "Canonical CER is the arithmetic mean over successful rows that include a canonical CER value. "
        "Number agreement is reported as matched / confident_wrong / abstain_equivalent.",
        "",
        "| pass | source audio | result rows | mean canonical CER (PRIVATE) | number agreement | silent-empty |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for group in grouped:
        agreement = f"{group['matched']} / {group['wrong']} / {group['abstain']}"
        lines.append(
            f"| {_escape_cell(group['mode'])} | {_escape_cell(group['clip_group'])} | "
            f"{group['rows']} | {_value(group['cer'])} | {agreement} | {group['silent_empty']} |"
        )

    represented = {group["clip_group"] for group in grouped}
    absent = [label for label in ("clipped", "unclipped") if label not in represented]
    if absent:
        lines.extend(["", "Source clipping groups not represented in supplied rows: " + ", ".join(absent) + "."])
    lines.append("")
    return lines


def _render_echo(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["## Read-back echo pass rates", ""]
    groups: dict[tuple[str, str, str], list[bool]] = {}
    for row in rows:
        if type(row.get("passed")) is not bool:
            continue
        key = (str(row.get("voice", "unspecified")), str(row.get("style", "unspecified")), str(row.get("condition", "unspecified")))
        groups.setdefault(key, []).append(row["passed"])
    if not groups:
        lines.extend(["Echo results: not available (no complete echo rows supplied).", ""])
        return lines

    lines.extend([
        "| voice × style × condition | passed | rows | pass rate |",
        "|---|---:|---:|---:|",
    ])
    for (voice, style, condition), outcomes in sorted(groups.items()):
        passed = sum(outcomes)
        lines.append(
            f"| {_escape_cell(voice)} × {_escape_cell(style)} × {_escape_cell(condition)} | "
            f"{passed} | {len(outcomes)} | {passed / len(outcomes) * 100:.1f}% |"
        )
    lines.append("")
    return lines


def _bias_row_succeeded(row: dict[str, Any]) -> bool:
    if "outcome" in row:
        return row.get("outcome") == "ok"
    transcript = row.get("transcript")
    return (
        isinstance(transcript, str)
        and bool(transcript.strip())
        and "transcription_error" not in row
    )


def _source_bias_target(pair: dict[str, dict[str, Any]]) -> str | None:
    targets = set()
    for row in pair.values():
        entities = row.get("entities")
        english = entities.get("bias_word") if isinstance(entities, dict) else row.get("bias_word")
        if isinstance(english, str):
            spoken = BIAS_SPOKEN_BY_ENGLISH.get(english.casefold())
            if spoken:
                targets.add(spoken)
    return next(iter(targets)) if len(targets) == 1 else None


def _load_bias_target_labels(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}

    labels: dict[str, str] = {}
    for row in _read_jsonl(path):
        clip_id = row.get("id")
        entities = row.get("entities")
        english = entities.get("bias_word") if isinstance(entities, dict) else None
        spoken = BIAS_SPOKEN_BY_ENGLISH.get(english.casefold()) if isinstance(english, str) else None
        if isinstance(clip_id, str) and clip_id and spoken:
            labels[clip_id] = spoken
    return labels


def _bias_result(
    rows: list[dict[str, Any]],
    target_labels: dict[str, str] | None = None,
) -> tuple[str, str]:
    target_labels = target_labels or {}
    grouped: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
    for row in rows:
        mode = row.get("stt_mode")
        if mode not in {"verbatim", "verbatim_nobias"}:
            continue
        key = (
            row.get("clip_id"), row.get("codec"), row.get("snr"), row.get("loss"),
            row.get("impulse_profile"), row.get("seed"),
        )
        grouped.setdefault(key, {})[mode] = row

    pairs = []
    excluded_incomplete = 0
    for pair in grouped.values():
        if (
            "verbatim" not in pair
            or "verbatim_nobias" not in pair
            or not _bias_row_succeeded(pair["verbatim"])
            or not _bias_row_succeeded(pair["verbatim_nobias"])
        ):
            excluded_incomplete += 1
            continue
        pairs.append(pair)

    exclusion_detail = f"excluded/incomplete pair count: {excluded_incomplete}"
    if not pairs:
        return "not available", f"no valid successful pairs were supplied; {exclusion_detail}"

    changed = 0
    bias_hits = baseline_hits = 0
    labeled_pairs = 0
    missing_target_labels = 0
    for pair in pairs:
        biased = pair["verbatim"]
        baseline = pair["verbatim_nobias"]
        biased_text = str(biased.get("transcript") or "")
        baseline_text = str(baseline.get("transcript") or "")
        if biased_text != baseline_text:
            changed += 1

        target = target_labels.get(str(biased.get("clip_id")))
        if not isinstance(target, str) or not target.strip():
            target = _source_bias_target(pair)
        if not isinstance(target, str) or not target.strip():
            missing_target_labels += 1
            continue
        labeled_pairs += 1
        bias_hits += _contains_term(biased_text, target)
        baseline_hits += _contains_term(baseline_text, target)

    if labeled_pairs:
        target_recovery = (
            f"target-term recovery {bias_hits}/{labeled_pairs} biased vs "
            f"{baseline_hits}/{labeled_pairs} unbiased on labeled pairs"
        )
        if missing_target_labels:
            target_recovery += (
                f"; target recovery unavailable for {missing_target_labels} pairs with missing gold labels"
            )
    else:
        target_recovery = f"target recovery unavailable (gold labels missing for {len(pairs)} valid pairs)"

    if changed:
        return (
            f"paired outputs differed on {changed}/{len(pairs)} clips (planned positive-control criterion met)",
            f"{changed} paired transcript differences; {target_recovery}; {exclusion_detail}",
        )
    if labeled_pairs and bias_hits > baseline_hits:
        return (
            f"boosting observable: {target_recovery}",
            f"transcripts were identical on {len(pairs) - changed}/{len(pairs)} paired clips; "
            f"{target_recovery}; {exclusion_detail}",
        )
    return (
        "Boosting not observable",
        f"paired outputs were identical on {len(pairs)}/{len(pairs)} clips; "
        f"{target_recovery}; {exclusion_detail}",
    )


def _contains_term(text: str, term: str) -> bool:
    # Token boundaries avoid counting a short part name inside a longer English word.
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, flags=re.IGNORECASE) is not None


def _render_bias(
    rows: list[dict[str, Any]],
    target_labels: dict[str, str] | None = None,
) -> list[str]:
    verdict, detail = _bias_result(rows, target_labels)
    label = "Boosting verdict" if verdict == "not available" else "Bias-control verdict"
    return ["## Bias control", "", f"{label}: {verdict}.", detail + ".", ""]


def _render_latency(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["## STT latency by pass", ""]
    groups: dict[str, list[float]] = {}
    for row in rows:
        mode = str(row.get("stt_mode") or "unspecified")
        latency = _number(row.get("latency_ms"))
        if latency is not None and latency >= 0:
            groups.setdefault(mode, []).append(latency)
    if not groups:
        lines.extend(["Latency: not available (no runner latency values supplied).", ""])
        return lines

    lines.extend(["| pass | rows | p50 latency (ms) | p95 latency (ms) |", "|---|---:|---:|---:|"])
    for mode, values in sorted(groups.items()):
        lines.append(
            f"| {_escape_cell(mode)} | {len(values)} | {_percentile(values, 0.50):.2f} | "
            f"{_percentile(values, 0.95):.2f} |"
        )
    lines.append("")
    return lines


def _render_credits(
    runner_rows: list[dict[str, Any]],
    echo_summaries: list[dict[str, Any]],
) -> list[str]:
    runner_values = [
        value for row in runner_rows
        if (value := _number(row.get("credits_spent"))) is not None and value >= 0
    ]
    echo_prisma = [
        value for summary in echo_summaries
        if summary.get("status") == "complete"
        and (value := _number(summary.get("prisma_credits_estimated"))) is not None
        and value >= 0
    ]
    echo_tts_lower = [
        value for summary in echo_summaries
        if summary.get("status") == "complete"
        and (value := _number(summary.get("tts_credits_accounted_lower_bound_estimate"))) is not None
        and value >= 0
    ]
    if not runner_values and not echo_prisma and not echo_tts_lower:
        return [
            "## Credit accounting",
            "",
            "Tracked estimated subtotal: not available (no supplied usage-ledger rows).",
            "Full benchmark total: unavailable because Task 10 renderer kept no retained live usage ledger.",
            "The Task 10 character-based render forecast is excluded; it is not recorded spend.",
            "",
        ]

    runner_total = sum(runner_values)
    echo_prisma_total = sum(echo_prisma)
    echo_tts_total = sum(echo_tts_lower)
    total = runner_total + echo_prisma_total + echo_tts_total
    lines = [
        "## Credit accounting",
        "",
        f"Tracked estimated subtotal: {total:.2f} credits (supplied runner rows and complete echo ledgers only).",
        "Full benchmark total: unavailable because Task 10 renderer kept no retained live usage ledger.",
        f"- Runner rows: {runner_total:.2f} across {len(runner_values)} rows.",
        f"- Complete echo summaries: Prisma {echo_prisma_total:.2f}; Timbre accounted lower-bound estimate {echo_tts_total:.2f}.",
        "- These are estimates represented by the supplied artifacts; console billed totals were not captured.",
        "- The Task 10 character-based render forecast is excluded; it is not recorded spend.",
        "",
    ]
    return lines


def _owner_status(money_eval: list[dict[str, Any]], runner_rows: list[dict[str, Any]]) -> str:
    labels = [str(row.get("slice", "")).casefold() for row in money_eval]
    labels.extend(str(row.get("stratum", "")).casefold() for row in runner_rows)
    if any("owner" in value for value in labels):
        return "owner-labelled rows are present in supplied inputs; inspect the slice tables for coverage"
    return "not available (owner-takes recording manifest/results were not supplied)"


def build_report(
    money_eval: list[dict],
    gramvaani_rows: list[dict],
    echo_rows: list[dict],
    bias_rows: list[dict],
    *,
    usage_rows: list[dict] | None = None,
    echo_summaries: list[dict] | None = None,
    bias_target_labels: dict[str, str] | None = None,
) -> str:
    """Render private Markdown from supplied result summaries and raw result rows.

    ``usage_rows`` optionally supplies all runner rows for complete latency and
    credit accounting. ``echo_summaries`` contains only complete, matching echo
    stage summaries; forecast fields are intentionally excluded from spend.
    """
    runner_rows = usage_rows if usage_rows is not None else [*gramvaani_rows, *bias_rows]
    completed_echo_summaries = [
        summary for summary in (echo_summaries or [])
        if isinstance(summary, dict) and summary.get("status") == "complete"
    ]

    lines = [
        "# Private Money-Path Benchmark Report",
        "",
        f"> **{PRIVATE_NOTICE}**. Keep this file under ignored `var/`; it is not a publication artifact.",
        "> Results are limited to supplied files. Estimated credits are not console-billed totals.",
        "",
    ]
    lines.extend(_render_money_eval(money_eval))
    lines.extend(_render_gramvaani(gramvaani_rows))
    lines.extend(_render_echo(echo_rows))
    lines.extend(_render_bias(bias_rows, bias_target_labels))
    lines.extend(_render_latency(runner_rows))
    lines.extend(_render_credits(runner_rows, completed_echo_summaries))
    lines.extend([
        "## Coverage gaps",
        "",
        f"- Owner takes: {_owner_status(money_eval, runner_rows)}.",
        "- Echo results are absent unless a complete screen or confirm result file is supplied.",
        "- Human listening labels are not inferred from ASR pass flags.",
        "- No Gramvaani publication permission is implied by this private report.",
        "",
    ])
    rendered = "\n".join(lines)
    report_guards._validate_competitor_free(rendered, context="private benchmark report")
    return rendered


def _read_json(path: Path) -> Any:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON in {path} line {line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"expected an object in {path} line {line_number}")
            rows.append(row)
    return rows


def _load_optional_jsonl(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in paths:
        if path.is_file():
            rows.extend(_read_jsonl(path))
    return rows


def _load_complete_echo(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Ignore partial rows unless the adjacent summary confirms a complete run."""
    summary_path = path.with_name(f"{path.stem}_summary.json")
    if not path.is_file() or not summary_path.is_file():
        return [], None
    summary = _read_json(summary_path)
    if not isinstance(summary, dict) or summary.get("status") != "complete":
        return [], None
    if summary.get("stage") not in {"screen", "confirm"}:
        return [], None
    if Path(str(summary.get("output", ""))).resolve() != path.resolve():
        return [], None
    if type(summary.get("rows_written")) is not int or summary["rows_written"] < 0:
        return [], None
    rows = _read_jsonl(path)
    if summary.get("rows_written") != len(rows):
        return [], None
    return rows, summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--money-eval", type=Path, default=DEFAULT_MONEY_EVAL)
    parser.add_argument("--gramvaani", type=Path, default=DEFAULT_GRAMVAANI)
    parser.add_argument("--bias", type=Path, default=DEFAULT_BIAS)
    parser.add_argument(
        "--bias-manifest", type=Path, default=None,
        help="gold bias-control JSONL to join with --bias results; defaults to the canonical manifest only with the canonical result path",
    )
    parser.add_argument(
        "--echo", type=Path, action="append", default=None,
        help="completed echo JSONL path; may be supplied more than once",
    )
    parser.add_argument(
        "--usage-row", type=Path, action="append", default=None,
        help="runner result JSONL for latency/credit aggregation; may be supplied more than once",
    )
    parser.add_argument("--out", type=Path, default=Path("var/lab/benchmark_report.md"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    private_root = PRIVATE_OUTPUT_ROOT.resolve()
    output_path = args.out.resolve()
    try:
        output_path.relative_to(private_root)
    except ValueError as exc:
        raise ValueError("private benchmark reports must be written beneath var/lab") from exc
    if output_path == private_root:
        raise ValueError("private benchmark report output must be a file beneath var/lab")

    eval_data = _read_json(args.money_eval)
    if eval_data is None:
        money_eval: list[dict[str, Any]] = []
    elif isinstance(eval_data, list) and all(isinstance(row, dict) for row in eval_data):
        money_eval = eval_data
    else:
        raise ValueError(f"money-eval input must contain a JSON array of objects: {args.money_eval}")

    gramvaani_rows = _read_jsonl(args.gramvaani) if args.gramvaani.is_file() else []
    bias_rows = _read_jsonl(args.bias) if args.bias.is_file() else []
    if args.bias_manifest is not None:
        bias_target_labels = _load_bias_target_labels(args.bias_manifest)
    elif args.bias.resolve() == DEFAULT_BIAS.resolve():
        bias_target_labels = _load_bias_target_labels(DEFAULT_BIAS_MANIFEST)
    else:
        bias_target_labels = None
    echo_paths = args.echo if args.echo is not None else list(DEFAULT_ECHO_FILES)
    echo_rows: list[dict[str, Any]] = []
    echo_summaries: list[dict[str, Any]] = []
    for path in echo_paths:
        rows, summary = _load_complete_echo(path)
        echo_rows.extend(rows)
        if summary is not None:
            echo_summaries.append(summary)

    usage_paths = args.usage_row if args.usage_row is not None else list(DEFAULT_USAGE_FILES)
    usage_rows = _load_optional_jsonl(usage_paths)
    rendered = build_report(
        money_eval,
        gramvaani_rows,
        echo_rows,
        bias_rows,
        usage_rows=usage_rows,
        echo_summaries=echo_summaries,
        bias_target_labels=bias_target_labels,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Private benchmark report written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
