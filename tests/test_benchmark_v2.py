import json

from parcha.lab.money_eval import (
    score_number_agreement,
    score_rows,
    summarize,
    wilson_upper,
)


def _result(
    clip_id,
    mode,
    transcript,
    *,
    codec="g711",
    snr=None,
    loss=0.0,
    impulse_profile=None,
    error=None,
):
    return {
        "clip_id": clip_id,
        "stt_mode": mode,
        "codec": codec,
        "snr": snr,
        "loss": loss,
        "impulse_profile": impulse_profile,
        "transcript": transcript,
        "transcription_error": error,
    }


def _clip_manifest(clip_id, amount, stratum):
    return {
        "id": clip_id,
        "text": "estimate",
        "reference_transcribe": "estimate",
        "entities": {},
        "audio": f"{clip_id}.wav",
        "kind": "speech",
        "seed": 1,
        "expected_amounts_paise": [amount],
        "stratum": stratum,
    }


def test_money_eval_counts_identical_wrong_amounts_as_accepted():
    rows = [
        _result("v001", "verbatim", "ब्रेक पैड साढ़े चार सौ लेबर दो सौ"),
        _result("v002", "transcribe", "ब्रेक पैड 350 लेबर 200"),
        _result("v001", "transcribe", "ब्रेक पैड 450 लेबर 200"),
        _result("v002", "verbatim", "ब्रेक पैड साढ़े तीन सौ लेबर दो सौ"),
    ]

    outcomes = score_rows(
        rows,
        expected={"v001": [45000, 20000], "v002": [45000, 20000]},
        slices={"v001": "scripted_estimate", "v002": "scripted_estimate"},
    )
    [summary] = summarize(outcomes)

    assert [outcome.kind for outcome in outcomes].count("correct") == 3
    assert [outcome.kind for outcome in outcomes].count("wrong_accepted") == 1
    assert summary["amounts"] == 4
    assert summary["slice"] == "scripted_estimate"
    assert summary["condition"] == "g711|clean"
    assert summary["correct"] == 3
    assert summary["wrong_accepted"] == 1
    assert summary["wrong_amount_confirmed_rate"] == 0.25
    assert summary["wrong_amount_confirmed_upper95"] > summary["wrong_amount_confirmed_rate"]


def test_money_eval_provider_error_abstains_for_expected_amount():
    rows = [
        _result("c001", "transcribe", None, error="provider unavailable"),
        _result("c001", "verbatim", "साढ़े तीन सौ"),
    ]

    outcomes = score_rows(
        rows,
        expected={"c001": [35000]},
        slices={"c001": "correction"},
    )
    [outcome] = outcomes
    [summary] = summarize(outcomes)

    assert outcome.kind == "abstained"
    assert outcome.reason == "provider_error"
    assert outcome.decided_paise is None
    assert summary["abstain_reasons"] == {"provider_error": 1}


def test_money_eval_single_provider_error_row_abstains_for_every_expected_amount():
    rows = [
        _result("c002", "transcribe", None, error="provider unavailable", codec="amr_nb_4750", snr=5.0),
    ]

    outcomes = score_rows(
        rows,
        expected={"c002": [35000, 20000]},
        slices={"c002": "correction"},
    )

    assert len(outcomes) == 2
    assert [outcome.reason for outcome in outcomes] == ["provider_error", "provider_error"]
    assert [outcome.condition for outcome in outcomes] == ["amr_nb_4750|5", "amr_nb_4750|5"]
    assert all(outcome.kind == "abstained" for outcome in outcomes)


def test_fractional_snr_conditions_do_not_mispair_or_lose_decimal_precision():
    rows = [
        _result("c003", "transcribe", "450", snr=5.25),
        _result("c003", "verbatim", "450", snr=5.25),
        _result("c003", "transcribe", "350", snr=5.75),
        _result("c003", "verbatim", "350", snr=5.75),
    ]

    outcomes = score_rows(rows, expected={"c003": [45000]}, slices={"c003": "correction"})

    assert len(outcomes) == 2
    assert {outcome.condition for outcome in outcomes} == {"g711|5.25", "g711|5.75"}
    assert {summary["condition"] for summary in summarize(outcomes)} == {"g711|5.25", "g711|5.75"}
    assert {outcome.condition: outcome.kind for outcome in outcomes} == {
        "g711|5.25": "correct",
        "g711|5.75": "wrong_accepted",
    }


def test_nonzero_loss_is_included_in_condition_without_changing_default_label():
    rows = [
        _result("c004", "transcribe", "450"),
        _result("c004", "verbatim", "450"),
        _result("c004", "transcribe", "450", snr=0.0),
        _result("c004", "verbatim", "450", snr=0.0),
        _result("c004", "transcribe", "350", loss=5.0),
        _result("c004", "verbatim", "350", loss=5.0),
    ]

    outcomes = score_rows(rows, expected={"c004": [45000]}, slices={"c004": "correction"})

    assert len(outcomes) == 3
    assert {summary["condition"] for summary in summarize(outcomes)} == {
        "g711|clean",
        "g711|0",
        "g711|clean|loss=5",
    }


def test_impulse_profile_is_included_in_condition_without_changing_default_label():
    rows = [
        _result("c005", "transcribe", "450"),
        _result("c005", "verbatim", "450"),
        _result("c005", "transcribe", "350", impulse_profile="impact_wrench"),
        _result("c005", "verbatim", "350", impulse_profile="impact_wrench"),
    ]

    outcomes = score_rows(rows, expected={"c005": [45000]}, slices={"c005": "correction"})

    assert len(outcomes) == 2
    assert {summary["condition"] for summary in summarize(outcomes)} == {
        "g711|clean",
        "g711|clean|profile=impact_wrench",
    }


def test_wilson_upper_handles_zero_failures_and_empty_sample():
    assert 0 < wilson_upper(0, 480) < 0.01
    assert wilson_upper(0, 0) == 1.0


def test_number_agreement_distinguishes_match_wrong_and_omitted_amount():
    reference = "लगभग ढाई सौ से अधिक बाल"

    assert score_number_agreement(reference, reference) == {
        "ref_numbers": 1,
        "matched": 1,
        "confident_wrong": 0,
        "abstain_equivalent": 0,
    }
    assert score_number_agreement(reference, "डेढ़ सौ") == {
        "ref_numbers": 1,
        "matched": 0,
        "confident_wrong": 1,
        "abstain_equivalent": 0,
    }
    assert score_number_agreement(reference, "बाल") == {
        "ref_numbers": 1,
        "matched": 0,
        "confident_wrong": 0,
        "abstain_equivalent": 1,
    }


def test_number_agreement_counts_aligned_incomplete_mentions_as_abstentions():
    assert score_number_agreement("साढ़े", "साढ़े") == {
        "ref_numbers": 1,
        "matched": 0,
        "confident_wrong": 0,
        "abstain_equivalent": 1,
    }


def test_money_eval_cli_reads_bom_manifests_skips_exclusions_and_creates_output(tmp_path):
    from parcha.lab.money_eval import main

    results = tmp_path / "results.jsonl"
    results.write_text(
        "\n".join(
            json.dumps(row, ensure_ascii=False)
            for row in [
                _result("c001", "transcribe", "ढाई सौ"),
                _result("c001", "verbatim", "ढाई सौ"),
                _result("y001", "transcribe", "ढाई सौ"),
                _result("y001", "verbatim", "ढाई सौ"),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    results2 = tmp_path / "results2.jsonl"
    results2.write_text(
        "\n".join(
            json.dumps(row, ensure_ascii=False)
            for row in [
                _result("v001", "transcribe", "\u0922\u093e\u0908 \u0938\u094c"),
                _result("v001", "verbatim", "\u0922\u093e\u0908 \u0938\u094c"),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest1 = tmp_path / "manifest1.jsonl"
    manifest1.write_text(
        "\ufeff" + json.dumps(_clip_manifest("c001", 25000, "correction"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    manifest2 = tmp_path / "manifest2.jsonl"
    manifest2.write_text(
        "\ufeff" + json.dumps(_clip_manifest("y001", 25000, "excluded"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    manifest3 = tmp_path / "manifest3.jsonl"
    manifest3.write_text(
        "\ufeff" + json.dumps(_clip_manifest("v001", 25000, "scripted_estimate"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "new" / "money-eval.json"

    assert main([
        "--results", str(results),
        "--results", str(results2),
        "--manifest", str(manifest1),
        "--manifest", str(manifest2),
        "--manifest", str(manifest3),
        "--out", str(output),
    ]) == 0

    summaries = json.loads(output.read_text(encoding="utf-8"))
    by_slice = {summary["slice"]: summary for summary in summaries}
    assert set(by_slice) == {"correction", "scripted_estimate"}
    assert by_slice["correction"]["amounts"] == 1
    assert by_slice["correction"]["correct"] == 1
    assert by_slice["scripted_estimate"]["amounts"] == 1
    assert by_slice["scripted_estimate"]["correct"] == 1
