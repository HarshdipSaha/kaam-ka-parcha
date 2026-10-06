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


def test_money_eval_requires_independent_confirmation_for_agreed_amounts():
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

    assert [outcome.kind for outcome in outcomes].count("abstained") == 4
    assert all(outcome.reason == "independent_confirmation_required" for outcome in outcomes)
    assert all(outcome.decided_paise is None for outcome in outcomes)
    assert summary["amounts"] == 4
    assert summary["slice"] == "scripted_estimate"
    assert summary["condition"] == "g711|clean"
    assert summary["correct"] == 0
    assert summary["abstained"] == 4
    assert summary["wrong_accepted"] == 0
    assert summary["wrong_amount_confirmed_rate"] == 0
    assert summary["abstain_reasons"] == {"independent_confirmation_required": 4}


def test_money_eval_preserves_parser_abstain_reason():
    rows = [
        _result("c000", "transcribe", "450"),
        _result("c000", "verbatim", "saade"),
    ]

    [outcome] = score_rows(rows, expected={"c000": [45000]}, slices={"c000": "correction"})

    assert outcome.kind == "abstained"
    assert outcome.reason == "incomplete_number"
    assert outcome.decided_paise is None


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
        "g711|5.25": "abstained",
        "g711|5.75": "abstained",
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
    assert by_slice["correction"]["correct"] == 0
    assert by_slice["correction"]["abstained"] == 1
    assert by_slice["correction"]["abstain_reasons"] == {"independent_confirmation_required": 1}
    assert by_slice["scripted_estimate"]["amounts"] == 1
    assert by_slice["scripted_estimate"]["correct"] == 0
    assert by_slice["scripted_estimate"]["abstained"] == 1


def test_colloquial_amount_renderer_covers_gold_first_amount_phrasings():
    from parcha.numerals import render_colloquial_amount

    expected = {
        450: "साढ़े चार सौ",
        150: "डेढ़ सौ",
        250: "ढाई सौ",
        125: "सवा सौ",
        175: "पौने दो सौ",
        1500: "डेढ़ हज़ार",
        1250: "सवा हज़ार",
        1750: "पौने दो हज़ार",
        1200: "बारह सौ",
        3500: "साढ़े तीन हज़ार",
        2050: "दो हज़ार पचास",
        75: "पचहत्तर",
    }

    assert {rupees: render_colloquial_amount(rupees * 100) for rupees in expected} == expected


def test_every_distinct_stress_amount_round_trips_through_colloquial_parser():
    from parcha.lab.amount_bench import STRESS_RUPEES
    from parcha.numerals import parse_amounts, render_colloquial_amount

    for rupees in dict.fromkeys(STRESS_RUPEES):
        mentions = parse_amounts(render_colloquial_amount(rupees * 100))
        assert [mention.paise for mention in mentions if mention.status == "complete"] == [rupees * 100]


def test_gold_first_estimates_are_deterministic_and_have_296_ordered_labels():
    from parcha.lab.amount_bench import HINDI_TIMBRE_VOICES, make_estimates
    from parcha.numerals import parse_amounts

    rows = make_estimates()
    assert rows == make_estimates()
    assert len(rows) == 120
    assert sum(len(row["expected_amounts_paise"]) for row in rows) == 296
    assert len({row["voice"] for row in rows}) >= 10
    for row in rows:
        assert row["voice"] in HINDI_TIMBRE_VOICES
        assert row["source"] == "timbre"
        assert row["stratum"] == "scripted_estimate"
        assert row["text"] == row["reference_transcribe"]
        assert [mention.paise for mention in parse_amounts(row["text"]) if mention.status == "complete"] == row[
            "expected_amounts_paise"
        ]


def test_corrections_are_reply_clips_with_one_parseable_expected_amount():
    from parcha.lab.amount_bench import make_corrections
    from parcha.numerals import parse_amounts

    rows = make_corrections()
    assert len(rows) == 40
    for row in rows:
        assert row["kind"] == "reply"
        assert row["stratum"] == "correction"
        assert len(row["expected_amounts_paise"]) == 1
        assert [mention.paise for mention in parse_amounts(row["text"]) if mention.status == "complete"] == row[
            "expected_amounts_paise"
        ]


def test_bias_control_clips_use_automotive_bias_words_and_validate_as_clips():
    from parcha.lab.amount_bench import BIAS_CONTROL_WORDS, make_bias_control
    from parcha.lab.dataset import Clip
    from parcha.vocabulary import AUTOMOTIVE_BIAS_WORDS

    rows = make_bias_control()
    assert len(rows) == 20
    assert all(row["stratum"] == "bias_control" for row in rows)
    assert {row["entities"]["bias_word"] for row in rows} <= set(AUTOMOTIVE_BIAS_WORDS)
    assert [row["entities"]["bias_word"] for row in rows[: len(BIAS_CONTROL_WORDS)]] == [
        word for word, _ in BIAS_CONTROL_WORDS
    ]
    assert all(Clip.model_validate(row) for row in rows)


def test_readback_words_style_speaks_amounts_as_hindi_words():
    from parcha.numerals import parse_amounts
    from parcha.readback import make_readback
    from tests.test_schema import sample_card

    text = make_readback(sample_card(), amount_style="words")

    assert "\u091a\u093e\u0930 \u0938\u094c \u092a\u091a\u093e\u0938 \u0930\u0941\u092a\u092f\u0947" in text
    assert "\u20b9" not in text
    assert [mention.paise for mention in parse_amounts(text)] == [45000, 20000, 65000]


def test_echo_scores_each_voice_style_condition_and_reuses_one_synthesis():
    from parcha.lab.echo import expected_sequence, run_echo, score_echo
    from tests.test_schema import sample_card

    calls = {"tts": 0}

    def synthesize(text, voice):
        calls["tts"] += 1
        return text.encode(), 120.0

    def degrade(wav, condition):
        return wav.replace("\u20b9450".encode(), "\u20b9350".encode()) if condition == "amr_nb_4750|0" else wav

    rows = run_echo(
        {"k1": sample_card()},
        ["Nalini", "Deepak"],
        ["digits"],
        ["control", "g711|clean", "amr_nb_4750|0"],
        synthesize=synthesize,
        degrade=degrade,
        transcribe=lambda wav: wav.decode(),
    )

    assert calls["tts"] == 2 and len(rows) == 6
    assert [row.passed for row in rows if row.condition == "amr_nb_4750|0"] == [False, False]
    assert expected_sequence(sample_card()) == (45000, 20000, 65000)
    assert score_echo(sample_card(), "")[1] is False


def test_run_echo_reports_tts_attempt_context_before_synthesis():
    from parcha.lab.echo import run_echo
    from parcha.readback import make_readback
    from tests.test_schema import sample_card

    attempts = []
    card = sample_card()
    readback = make_readback(card, amount_style="words")

    run_echo(
        {"k1": card},
        ["Nalini"],
        ["words"],
        ["control"],
        synthesize=lambda text, voice: (text.encode(), 10.0),
        degrade=lambda wav, condition: wav,
        transcribe=lambda wav: wav.decode(),
        on_tts_attempt=lambda card_id, voice, style, characters: attempts.append(
            (card_id, voice, style, characters)
        ),
    )

    assert attempts == [("k1", "Nalini", "words", len(readback))]


def test_run_echo_emits_completed_rows_before_a_later_transcription_failure():
    from pytest import raises
    from parcha.lab.echo import run_echo
    from tests.test_schema import sample_card

    emitted = []
    transcriptions = 0

    def transcribe(wav):
        nonlocal transcriptions
        transcriptions += 1
        if transcriptions == 2:
            raise RuntimeError("provider unavailable")
        return wav.decode()

    with raises(RuntimeError, match="provider unavailable"):
        run_echo(
            {"k1": sample_card()},
            ["Nalini"],
            ["digits"],
            ["control", "amr_nb_4750|0"],
            synthesize=lambda text, voice: (text.encode(), 120.0),
            degrade=lambda wav, condition: wav,
            transcribe=transcribe,
            on_row=emitted.append,
        )

    assert len(emitted) == 1
    assert emitted[0].condition == "control"


def test_run_echo_emits_all_three_audio_conditions_after_each_case():
    from parcha.lab.echo import run_echo
    from tests.test_schema import sample_card

    completed_cases = []
    trace = []

    run_echo(
        {"k1": sample_card()},
        ["Nalini"],
        ["digits"],
        ["control", "g711|clean", "amr_nb_4750|0"],
        synthesize=lambda text, voice: (b"tts", 120.0),
        degrade=lambda wav, condition: wav + condition.encode(),
        transcribe=lambda wav: (trace.append("transcribe") or ""),
        on_case=lambda rows, audios: completed_cases.append((rows, audios)),
        on_case_audio=lambda card_id, voice, style, audios: trace.append(("audio", audios)),
    )

    assert len(completed_cases) == 1
    assert trace[0][0] == "audio" and trace[1:] == ["transcribe"] * 3
    rows, audios = completed_cases[0]
    assert [row.condition for row in rows] == ["control", "g711|clean", "amr_nb_4750|0"]
    assert audios == {
        "control": b"tts",
        "g711|clean": b"tts" + b"g711|clean",
        "amr_nb_4750|0": b"tts" + b"amr_nb_4750|0",
    }
