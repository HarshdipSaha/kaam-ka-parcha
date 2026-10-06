import json
import re
from pathlib import Path

import pytest

from parcha.lab import bench_report
from parcha.lab import report
from parcha.lab.bench_report import build_report, main, _load_bias_target_labels, _render_bias


def test_default_echo_inputs_use_the_final_task13_continuation_paths():
    assert bench_report.DEFAULT_ECHO_FILES == (
        Path("var/lab/echo_screen_resumed4_20261006.jsonl"),
        Path("var/lab/echo_confirm_resumed2_20261006.jsonl"),
    )


def test_build_report_covers_money_gramvaani_echo_bias_latency_and_credits():
    money_eval = [{
        "slice": "scripted_estimate",
        "condition": "g711|clean",
        "amounts": 2,
        "wrong_accepted": 0,
        "wrong_amount_confirmed_upper95": 0.65,
        "abstain_rate": 0.5,
        "abstain_reasons": {"independent_confirmation_required": 1},
    }]
    gramvaani_rows = [
        {
            "clip_id": "g001", "stratum": "gramvaani_unclipped", "stt_mode": "transcribe",
            "reference": "450", "transcript": "450", "cer_canonical": 0.1,
            "outcome": "ok", "latency_ms": 100.0, "credits_spent": 0.2,
        },
        {
            "clip_id": "g002", "stratum": "gramvaani_clipped", "stt_mode": "transcribe",
            "reference": "450", "transcript": "350", "cer_canonical": 0.3,
            "outcome": "ok", "latency_ms": 200.0, "credits_spent": 0.4,
        },
        {
            "clip_id": "g003", "stratum": "gramvaani_clipped", "stt_mode": "verbatim",
            "reference": "450", "transcript": "", "cer_canonical": None,
            "outcome": "empty_transcript", "latency_ms": 300.0, "credits_spent": 0.6,
        },
    ]
    echo_rows = [
        {"voice": "Nalini", "style": "digits", "condition": "control", "passed": True},
        {"voice": "Nalini", "style": "digits", "condition": "control", "passed": False},
    ]
    bias_rows = [
        {
            "clip_id": "b001", "stt_mode": "verbatim", "codec": "none", "snr": None,
            "loss": 0.0, "impulse_profile": None, "seed": 1, "transcript": "clutch",
            "reference": "clutch plate", "bias_words": ["clutch"], "latency_ms": 400.0,
            "credits_spent": 0.8,
        },
        {
            "clip_id": "b001", "stt_mode": "verbatim_nobias", "codec": "none", "snr": None,
            "loss": 0.0, "impulse_profile": None, "seed": 1, "transcript": "clutch",
            "reference": "clutch plate", "bias_words": None, "latency_ms": 500.0,
            "credits_spent": 1.0,
        },
    ]

    markdown = build_report(money_eval, gramvaani_rows, echo_rows, bias_rows)

    assert "PRIVATE: absolute metrics \u2014 do not publish" in markdown
    assert "scripted_estimate \u00d7 g711|clean" in markdown
    assert "wrong_amount_confirmed_upper95" in markdown
    assert "independent_confirmation_required" in markdown
    assert "canonical CER (PRIVATE)" in markdown
    assert "clipped" in markdown and "unclipped" in markdown
    assert "matched / confident_wrong / abstain_equivalent" in markdown
    assert "silent-empty" in markdown and "1" in markdown
    assert "Nalini \u00d7 digits \u00d7 control" in markdown
    assert "50.0%" in markdown
    assert "Boosting not observable" in markdown
    assert "p50" in markdown and "p95" in markdown
    assert "Tracked estimated subtotal: 3.00 credits" in markdown
    assert "Full benchmark total: unavailable" in markdown
    assert "Task 10 renderer kept no retained live usage ledger" in markdown
    for competitor in report.FORBIDDEN_COMPETITORS:
        assert re.search(rf"\b{re.escape(competitor)}\b", markdown, re.IGNORECASE) is None


def test_build_report_does_not_invent_missing_echo_or_owner_values():
    markdown = build_report([], [], [], [])

    assert "Echo results: not available" in markdown
    assert "Owner takes: not available" in markdown
    assert "Boosting verdict: not available" in markdown
    assert "Tracked estimated subtotal: not available" in markdown
    assert "Full benchmark total: unavailable" in markdown
    assert "Task 10 renderer kept no retained live usage ledger" in markdown


def test_gramvaani_number_agreement_excludes_errors_and_treats_empty_outcome_as_abstain():
    grouped = bench_report._gramvaani_group([
        {
            "stt_mode": "verbatim", "stratum": "gramvaani_unclipped",
            "reference": "450", "transcript": "450", "outcome": "ok",
        },
        {
            "stt_mode": "verbatim", "stratum": "gramvaani_unclipped",
            "reference": "450", "transcript": "350", "outcome": "provider_error",
            "transcription_error": "later chunk failed after partial transcript",
        },
        {
            "stt_mode": "verbatim", "stratum": "gramvaani_unclipped",
            "reference": "450", "transcript": "350", "outcome": "empty_transcript",
        },
    ])

    assert grouped == [{
        "mode": "verbatim",
        "clip_group": "unclipped",
        "rows": 3,
        "cer": None,
        "matched": 1,
        "wrong": 0,
        "abstain": 1,
        "silent_empty": 1,
    }]


def test_cli_writes_private_report_and_ignores_interrupted_echo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    lab = tmp_path / "var" / "lab"
    lab.mkdir(parents=True)
    echo_path = lab / "echo_screen.jsonl"
    echo_path.write_text(json.dumps({
        "card_id": "partial", "voice": "Nalini", "style": "digits",
        "condition": "control", "passed": True,
    }) + "\n", encoding="utf-8")
    (lab / "echo_screen_summary.json").write_text(json.dumps({
        "status": "interrupted", "output": str(echo_path), "rows_written": 1,
    }), encoding="utf-8")

    assert main(["--echo", str(echo_path)]) == 0

    output = (lab / "benchmark_report.md").read_text(encoding="utf-8")
    assert "PRIVATE: absolute metrics \u2014 do not publish" in output
    assert "Echo results: not available" in output
    assert "partial \u00d7" not in output

    (lab / "echo_screen_summary.json").write_text(json.dumps({
        "status": "complete", "stage": "screen", "output": str(echo_path),
        "rows_written": 1, "prisma_credits_estimated": 2.0,
        "tts_credits_accounted_lower_bound_estimate": 1.0,
        "tts_credits_completed_stage_forecast": 1000.0,
    }), encoding="utf-8")
    assert main(["--echo", str(echo_path)]) == 0

    output = (lab / "benchmark_report.md").read_text(encoding="utf-8")
    assert "Nalini \u00d7 digits \u00d7 control" in output
    assert "Tracked estimated subtotal: 3.00 credits" in output
    assert "Full benchmark total: unavailable" in output
    assert "1000.00" not in output


def test_credit_total_uses_echo_accounting_lower_bound_not_forecast():
    markdown = build_report(
        [], [], [], [],
        usage_rows=[{"credits_spent": 1.25}],
        echo_summaries=[{
            "status": "complete",
            "prisma_credits_estimated": 2.0,
            "tts_credits_accounted_lower_bound_estimate": 0.75,
            "tts_credits_completed_stage_forecast": 999.0,
        }],
    )

    assert "Tracked estimated subtotal: 4.00 credits" in markdown
    assert "Full benchmark total: unavailable" in markdown
    assert "999.00" not in markdown


def test_cli_refuses_to_write_private_report_outside_var_lab(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="beneath var/lab"):
        main(["--out", str(tmp_path / "docs" / "public.md")])


def test_benchmark_card_uses_a_fresh_console_balance_for_forecasts():
    card = Path("docs/benchmarks/BENCHMARK_CARD.md").read_text(encoding="utf-8")
    normalized_card = " ".join(card.split())

    assert "235000" not in card
    assert card.count('Read-Host "Current credits shown by account console"') == 3
    assert "does not query or verify the account balance" in normalized_card


def test_bias_report_excludes_one_sided_provider_error_pairs():
    bias_rows = [
        {
            "clip_id": "failed", "stt_mode": "verbatim", "outcome": "provider_error",
            "codec": "none", "snr": None, "loss": 0.0, "impulse_profile": None,
            "seed": 1, "transcript": "clutch", "reference": "clutch plate",
            "bias_words": ["clutch"],
        },
        {
            "clip_id": "failed", "stt_mode": "verbatim_nobias", "outcome": "ok",
            "codec": "none", "snr": None, "loss": 0.0, "impulse_profile": None,
            "seed": 1, "transcript": "brake", "reference": "clutch plate",
        },
        {
            "clip_id": "success", "stt_mode": "verbatim", "outcome": "ok",
            "codec": "none", "snr": None, "loss": 0.0, "impulse_profile": None,
            "seed": 2, "transcript": "clutch", "reference": "clutch plate",
            "bias_words": ["clutch"],
        },
        {
            "clip_id": "success", "stt_mode": "verbatim_nobias", "outcome": "ok",
            "codec": "none", "snr": None, "loss": 0.0, "impulse_profile": None,
            "seed": 2, "transcript": "clutch", "reference": "clutch plate",
        },
    ]

    rendered = "\n".join(_render_bias(bias_rows))

    assert "Boosting not observable" in rendered
    assert "paired outputs were identical on 1/1 clips" in rendered
    assert "excluded/incomplete pair count: 1" in rendered


def test_bias_report_returns_not_available_when_both_rows_are_provider_errors():
    bias_rows = [
        {
            "clip_id": "failed", "stt_mode": "verbatim", "outcome": "provider_error",
            "codec": "none", "snr": None, "loss": 0.0, "impulse_profile": None,
            "seed": 1, "transcript": "clutch", "reference": "clutch plate",
            "bias_words": ["clutch"],
        },
        {
            "clip_id": "failed", "stt_mode": "verbatim_nobias", "outcome": "provider_error",
            "codec": "none", "snr": None, "loss": 0.0, "impulse_profile": None,
            "seed": 1, "transcript": "brake", "reference": "clutch plate",
        },
    ]

    rendered = "\n".join(_render_bias(bias_rows))

    assert "Boosting verdict: not available." in rendered
    assert "no valid successful pairs" in rendered
    assert "excluded/incomplete pair count: 1" in rendered


def test_bias_report_requires_usable_transcripts_for_legacy_rows():
    bias_rows = [
        {
            "clip_id": "legacy", "stt_mode": "verbatim", "codec": "none", "snr": None,
            "loss": 0.0, "impulse_profile": None, "seed": 1, "transcript": "clutch",
            "reference": "clutch plate", "bias_words": ["clutch"],
        },
        {
            "clip_id": "legacy", "stt_mode": "verbatim_nobias", "codec": "none", "snr": None,
            "loss": 0.0, "impulse_profile": None, "seed": 1, "transcript": "brake",
            "transcription_error": "provider error", "reference": "clutch plate",
        },
    ]

    rendered = "\n".join(_render_bias(bias_rows))

    assert "Boosting verdict: not available." in rendered
    assert "excluded/incomplete pair count: 1" in rendered


def test_bias_report_counts_unpaired_rows_as_incomplete():
    bias_rows = [{
        "clip_id": "orphan", "stt_mode": "verbatim", "outcome": "ok",
        "codec": "none", "snr": None, "loss": 0.0, "impulse_profile": None,
        "seed": 1, "transcript": "clutch", "reference": "clutch plate",
        "bias_words": ["clutch"],
    }]

    rendered = "\n".join(_render_bias(bias_rows))

    assert "Boosting verdict: not available." in rendered
    assert "excluded/incomplete pair count: 1" in rendered


def test_bias_report_maps_gold_english_label_to_spoken_hindi_target():
    bias_rows = [
        {
            "clip_id": "b001", "stt_mode": "verbatim", "outcome": "ok",
            "codec": "none", "snr": None, "loss": 0.0, "impulse_profile": None,
            "seed": 1, "transcript": "अल्टरनेटर बदलना पड़ेगा।",
            "reference": "अल्टरनेटर बदलना पड़ेगा", "bias_words": ["alternator", "clutch"],
        },
        {
            "clip_id": "b001", "stt_mode": "verbatim_nobias", "outcome": "ok",
            "codec": "none", "snr": None, "loss": 0.0, "impulse_profile": None,
            "seed": 1, "transcript": "अल्टरनेटर बदलना पड़ेगा।",
            "reference": "अल्टरनेटर बदलना पड़ेगा",
        },
    ]

    rendered = "\n".join(_render_bias(
        bias_rows,
        _load_bias_target_labels(bench_report.DEFAULT_BIAS_MANIFEST),
    ))

    assert "target-term recovery 1/1 biased vs 1/1 unbiased" in rendered
    assert "target recovery unavailable" not in rendered


def test_bias_report_says_target_recovery_unavailable_without_gold_label():
    bias_rows = [
        {
            "clip_id": "synthetic-without-label", "stt_mode": "verbatim", "outcome": "ok",
            "codec": "none", "snr": None, "loss": 0.0, "impulse_profile": None,
            "seed": 1, "transcript": "अल्टरनेटर बदलना पड़ेगा।",
            "reference": "अल्टरनेटर बदलना पड़ेगा", "bias_words": ["alternator"],
        },
        {
            "clip_id": "synthetic-without-label", "stt_mode": "verbatim_nobias", "outcome": "ok",
            "codec": "none", "snr": None, "loss": 0.0, "impulse_profile": None,
            "seed": 1, "transcript": "अल्टरनेटर बदलना पड़ेगा।",
            "reference": "अल्टरनेटर बदलना पड़ेगा",
        },
    ]

    rendered = "\n".join(_render_bias(bias_rows))

    assert "target recovery unavailable" in rendered
    assert "target-term recovery 0/0" not in rendered


def _hindi_bias_pair(clip_id="b001"):
    common = {
        "clip_id": clip_id, "codec": "none", "snr": None, "loss": 0.0,
        "impulse_profile": None, "seed": 1, "outcome": "ok",
        "transcript": "अल्टरनेटर बदलना पड़ेगा।",
        "reference": "अल्टरनेटर बदलना पड़ेगा",
    }
    return [
        {**common, "stt_mode": "verbatim", "bias_words": ["alternator"]},
        {**common, "stt_mode": "verbatim_nobias", "bias_words": None},
    ]


def test_build_report_direct_rows_do_not_inherit_canonical_clip_labels():
    rendered = build_report([], [], [], _hindi_bias_pair())

    assert "target recovery unavailable" in rendered
    assert "target-term recovery 1/1" not in rendered


def test_build_report_can_fall_back_to_inline_source_target_labels():
    bias_rows = _hindi_bias_pair("inline-labelled-clip")
    for row in bias_rows:
        row["entities"] = {"bias_word": "alternator"}

    rendered = build_report([], [], [], bias_rows)

    assert "target-term recovery 1/1 biased vs 1/1 unbiased" in rendered


def test_cli_custom_bias_path_does_not_join_canonical_labels(tmp_path, monkeypatch):
    monkeypatch.setattr(bench_report, "PRIVATE_OUTPUT_ROOT", tmp_path / "var" / "lab")
    custom_bias = tmp_path / "custom_bias.jsonl"
    custom_bias.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in _hindi_bias_pair()) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "var" / "lab" / "custom_report.md"

    assert main([
        "--money-eval", str(tmp_path / "missing_money_eval.json"),
        "--gramvaani", str(tmp_path / "missing_gramvaani.jsonl"),
        "--bias", str(custom_bias), "--echo", str(tmp_path / "missing_echo.jsonl"),
        "--usage-row", str(tmp_path / "missing_usage.jsonl"), "--out", str(output),
    ]) == 0

    rendered = output.read_text(encoding="utf-8")
    assert "target recovery unavailable" in rendered
    assert "target-term recovery 1/1" not in rendered


def test_cli_custom_bias_path_can_use_an_explicit_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(bench_report, "PRIVATE_OUTPUT_ROOT", tmp_path / "var" / "lab")
    custom_bias = tmp_path / "custom_bias.jsonl"
    custom_bias.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in _hindi_bias_pair("custom-clip")) + "\n",
        encoding="utf-8",
    )
    custom_manifest = tmp_path / "custom_manifest.jsonl"
    custom_manifest.write_text(json.dumps({
        "id": "custom-clip", "entities": {"bias_word": "alternator"},
    }) + "\n", encoding="utf-8")
    output = tmp_path / "var" / "lab" / "custom_report.md"

    assert main([
        "--money-eval", str(tmp_path / "missing_money_eval.json"),
        "--gramvaani", str(tmp_path / "missing_gramvaani.jsonl"),
        "--bias", str(custom_bias), "--bias-manifest", str(custom_manifest),
        "--echo", str(tmp_path / "missing_echo.jsonl"),
        "--usage-row", str(tmp_path / "missing_usage.jsonl"), "--out", str(output),
    ]) == 0

    rendered = output.read_text(encoding="utf-8")
    assert "target-term recovery 1/1 biased vs 1/1 unbiased" in rendered
