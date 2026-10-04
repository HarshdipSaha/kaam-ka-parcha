import json
from pathlib import Path
import pytest

from parcha.lab.report import (
    main,
    private_summary,
    public_delta,
)


def test_public_export_fails_closed_without_written_answer():
    rows = [
        {
            "clip_id": "c1",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 1,
            "variant": "bias_off",
            "part_matched": False,
        },
        {
            "clip_id": "c1",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 1,
            "variant": "bias_1_0",
            "part_matched": True,
        },
    ]

    expected_msg = "Public delta export requires written organizer consent and reference"

    # 1. organizer_consent is False
    with pytest.raises(PermissionError, match=expected_msg):
        public_delta(rows, organizer_consent=False, consent_ref="organizer-reply-2026-10-10")

    # 2. consent_ref is None
    with pytest.raises(PermissionError, match=expected_msg):
        public_delta(rows, organizer_consent=True, consent_ref=None)

    # 3. consent_ref is empty string
    with pytest.raises(PermissionError, match=expected_msg):
        public_delta(rows, organizer_consent=True, consent_ref="   ")

    # 4. Both missing
    with pytest.raises(PermissionError, match=expected_msg):
        public_delta(rows, organizer_consent=False, consent_ref=None)


def test_delta_is_paired_and_labelled():
    rows = []
    # 30 clips with paired bias_off and bias_1_0
    for i in range(30):
        rows.append({
            "clip_id": f"s{i:03d}",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 20261004,
            "variant": "bias_off",
            "model": "Prisma REST verbatim",
            "part_matched": i < 10,  # 10 / 30 baseline matches
            "amount_matched": i < 15,
            "transcript": "kuch part",
        })
        rows.append({
            "clip_id": f"s{i:03d}",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 20261004,
            "variant": "bias_1_0",
            "model": "Prisma REST verbatim",
            "bias_score": 1.0,
            "part_matched": i < 20,  # 20 / 30 biased matches (+10 delta)
            "amount_matched": i < 25,  # 25 / 30 biased matches (+10 delta)
            "transcript": "brake part",
        })

    out = public_delta(
        rows,
        organizer_consent=True,
        consent_ref="organizer-reply-2026-10-10",
        date="2026-10-19",
    )

    # Check required labels and substrings
    assert "measured by us" in out
    assert "N=30" in out
    assert "2026-10-19" in out
    assert "organizer-reply-2026-10-10" in out

    # Check operational settings
    assert "g711" in out.lower()
    assert "10.0 db" in out.lower() or "10 db" in out.lower()
    assert "prisma rest verbatim" in out.lower()
    assert "1.0" in out

    # Check recovery deltas
    assert "+10" in out
    assert "33.3%" in out or "+33.3%" in out
    assert "10/30" in out
    assert "20/30" in out


def test_private_summary_aggregates_metrics_correctly():
    rows = [
        # Group 1: g711, clean (snr=None), loss=0.0
        {
            "clip_id": "c1",
            "codec": "g711",
            "snr": None,
            "loss": 0.0,
            "cer": 0.10,
            "reference": "brake part ₹450",  # 15 chars
            "amount_matched": True,
            "latency_ms": 100.0,
            "credits_spent": 1.0,
        },
        {
            "clip_id": "c2",
            "codec": "g711",
            "snr": None,
            "loss": 0.0,
            "cer": 0.20,
            "reference": "clutch part ₹50",  # 15 chars
            "amount_matched": False,
            "latency_ms": 200.0,
            "credits_spent": 1.0,
        },
        # Group 2: amr_nb_4750, 5.0 dB, loss=1.0
        {
            "clip_id": "c3",
            "codec": "amr_nb_4750",
            "snr": 5.0,
            "loss": 1.0,
            "cer": 0.30,
            "reference": "plug ₹200",  # 10 chars
            "amount_matched": True,
            "latency_ms": 150.0,
            "credits_spent": 1.2,
        },
        # Engine / non-speech rows
        {
            "clip_id": "engine_01",
            "clip_type": "engine",
            "transcript": "haan nahi theek",  # 3 hallucinated words
        },
        {
            "clip_id": "engine_02",
            "clip_type": "engine",
            "transcript": "kuch",  # 1 hallucinated word
        },
    ]

    summary = private_summary(rows)

    # Check Markdown tables and structure
    assert "# Private Lab Evaluation Summary" in summary
    assert "| Codec | SNR | Loss | N | Mean CER | Total Chars | Amount Match (%) | Latency Mean (ms) | Latency p50 (ms) | Latency p90 (ms) | Est. Credits Spent |" in summary
    assert "g711" in summary
    assert "amr_nb_4750" in summary

    # Group 1: 2 clips, mean CER = 0.1500, total chars = 30, amount = 1/2 (50.0%)
    assert "0.1500" in summary
    assert "30" in summary
    assert "1/2 (50.0%)" in summary
    # Group 1 latencies: 100.0 & 200.0 -> mean 150.0, p50 150.0
    assert "150.0" in summary
    # Group 1 credits: 2.00
    assert "2.00" in summary

    # Group 2: 1 clip, mean CER = 0.3000, total chars = 9, amount = 1/1 (100.0%)
    assert "0.3000" in summary
    assert "9" in summary
    assert "1/1 (100.0%)" in summary
    assert "1.20" in summary

    # Non-speech / engine hallucination check
    assert "Non-Speech / Engine Idle Evaluation" in summary
    assert "**Total Non-Speech Clips Evaluated**: 2" in summary
    assert "**Total Hallucinated Words Emitted**: 4" in summary
    assert "**Mean Hallucinated Words per Clip**: 2.00" in summary
    assert "engine_01" in summary
    assert "engine_02" in summary

    # Verify no competitor mentions
    for comp in ["whisper", "google", "aws", "azure", "openai"]:
        assert comp not in summary.lower()


def test_public_delta_refuses_competitor_names():
    # 1. Competitor in transcript
    rows_whisper = [
        {
            "clip_id": "c1",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 1,
            "variant": "bias_off",
            "transcript": "compared against Whisper model",
            "part_matched": False,
        },
        {
            "clip_id": "c1",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 1,
            "variant": "bias_1_0",
            "transcript": "brake part",
            "part_matched": True,
        },
    ]
    with pytest.raises(ValueError, match="[Cc]ompetitor mention '.*' is strictly forbidden"):
        public_delta(
            rows_whisper,
            organizer_consent=True,
            consent_ref="organizer-reply-2026-10-10",
        )

    # 2. Competitor in custom field
    rows_google = [
        {
            "clip_id": "c1",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 1,
            "variant": "bias_off",
            "competitor": "Google Speech",
        },
        {
            "clip_id": "c1",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 1,
            "variant": "bias_1_0",
        },
    ]
    with pytest.raises(ValueError, match="[Cc]ompetitor mention '.*' is strictly forbidden"):
        public_delta(
            rows_google,
            organizer_consent=True,
            consent_ref="organizer-reply-2026-10-10",
        )

    # 3. Competitor in consent reference
    rows_clean = [
        {
            "clip_id": "c1",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 1,
            "variant": "bias_off",
            "part_matched": False,
        },
        {
            "clip_id": "c1",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 1,
            "variant": "bias_1_0",
            "part_matched": True,
        },
    ]
    with pytest.raises(ValueError, match="[Cc]ompetitor mention '.*' is strictly forbidden"):
        public_delta(
            rows_clean,
            organizer_consent=True,
            consent_ref="tested with AWS and Azure",
        )


def test_public_delta_refuses_absolute_metrics(monkeypatch):
    # Verify absolute CER or WER rejection guard
    rows = [
        {
            "clip_id": "c1",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 1,
            "variant": "bias_off",
            "part_matched": False,
        },
        {
            "clip_id": "c1",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 1,
            "variant": "bias_1_0",
            "part_matched": True,
        },
    ]

    from parcha.lab import report

    # Inject an absolute CER string into the template logic to verify post-generation guard
    orig_is_part = report._is_part_matched
    try:
        # If output contains "CER: 15.0%", guard should raise ValueError
        monkeypatch.setattr(
            report,
            "_is_part_matched",
            lambda r: True if r.get("variant") == "bias_1_0" else False,
        )
        # Normal call passes
        res = public_delta(rows, organizer_consent=True, consent_ref="consent-2026")
        assert "N=1" in res

        # Validate _validate_no_absolute_metrics directly
        with pytest.raises(ValueError, match="Absolute CER/WER metrics"):
            report._validate_no_absolute_metrics("Baseline CER: 0.12")
        with pytest.raises(ValueError, match="Absolute CER/WER metrics"):
            report._validate_no_absolute_metrics("Achieved WER = 5.0%")
        with pytest.raises(ValueError, match="Absolute CER/WER metrics"):
            report._validate_no_absolute_metrics("absolute CER of 10%")
    finally:
        monkeypatch.setattr(report, "_is_part_matched", orig_is_part)


def test_lab_report_cli(tmp_path):
    results_file = tmp_path / "results.jsonl"
    rows = [
        {
            "clip_id": "c1",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 42,
            "variant": "bias_off",
            "cer": 0.10,
            "reference": "brake ₹450",
            "part_matched": False,
            "amount_matched": True,
            "latency_ms": 120.0,
            "credits_spent": 0.5,
        },
        {
            "clip_id": "c1",
            "codec": "g711",
            "snr": 10.0,
            "loss": 0.0,
            "seed": 42,
            "variant": "bias_1_0",
            "cer": 0.05,
            "reference": "brake ₹450",
            "part_matched": True,
            "amount_matched": True,
            "latency_ms": 110.0,
            "credits_spent": 0.5,
        },
    ]
    with results_file.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "summary", "total": 2}) + "\n")
        for r in rows:
            f.write(json.dumps(r) + "\n")

    priv_out = tmp_path / "private_report.md"
    pub_out = tmp_path / "public_delta.md"

    # Test full CLI with consent and public output
    rc = main([
        "--results-file", str(results_file),
        "--private-output", str(priv_out),
        "--public-output", str(pub_out),
        "--organizer-consent-recorded",
        "--consent-ref", "organizer-reply-2026-10-10",
        "--date", "2026-10-19",
    ])
    assert rc == 0
    assert priv_out.exists()
    assert pub_out.exists()

    priv_content = priv_out.read_text(encoding="utf-8")
    assert "# Private Lab Evaluation Summary" in priv_content
    assert "g711" in priv_content

    pub_content = pub_out.read_text(encoding="utf-8")
    assert "measured by us" in pub_content
    assert "N=1" in pub_content
    assert "organizer-reply-2026-10-10" in pub_content
