import json
import csv
from dataclasses import asdict, replace
from pathlib import Path
from random import Random

import httpx
import pytest

from parcha.lab.echo import EchoRow, expected_sequence
from parcha.lab.echo_review import EchoReviewWriter, REVIEW_SAMPLE_SEED, select_row_for_review
from parcha.gnani import GnaniError
from parcha.readback import make_readback
from scripts.run_echo_test import CONDITIONS, _estimate_cards, _stress_cards


def _write_interrupted_run(
    root: Path,
    rows: tuple[EchoRow, ...] | None = None,
    *,
    pass_fraction: float = 0.0,
):
    lab_root = root / "var" / "lab"
    lab_root.mkdir(parents=True)
    output_path = lab_root / "echo_interrupted.jsonl"
    review_audio = lab_root / "echo_interrupted_review"
    review_manifest = lab_root / "echo_interrupted_review.jsonl"
    labels = lab_root / "echo_labels.csv"
    if rows is None:
        expected = expected_sequence(_stress_cards()["s001"])
        rows = tuple(
            EchoRow(
                card_id="s001",
                voice="Nalini",
                style="digits",
                condition=condition,
                expected_paise=expected,
                heard_paise=(),
                transcript="could not hear",
                passed=False,
                tts_ms=10.5,
            )
            for condition in CONDITIONS
        )

    writer = EchoReviewWriter(
        review_audio,
        review_manifest,
        labels,
        run_id="run-old",
        stage="screen",
        seed=REVIEW_SAMPLE_SEED,
        pass_fraction=pass_fraction,
    )
    case_audio = {
        condition: f"wav:{condition}".encode() for condition in CONDITIONS
    }
    writer.begin_case(rows[0].card_id, rows[0].voice, rows[0].style, case_audio)
    for row in rows:
        writer.record_row(row)
    writer.finish_case(rows, case_audio)
    writer.close()

    output_path.write_text(
        "".join(json.dumps(asdict(row), ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    summary_path = lab_root / "echo_interrupted_summary.json"
    summary_path.write_text(json.dumps({
        "output": str(output_path),
        "status": "interrupted",
        "rows_written": len(rows),
        "request_interval_seconds": 1.0,
        "stt_requests_attempted": len(rows),
        "stt_audio_seconds": 12.5,
        "prisma_credits_estimated": 2.5,
        "prisma_credits_per_audio_second": 0.2,
        "tts_chars": 999999,
        "tts_credits_estimated": 49999.95,
        "run_id": "run-old",
        "stage": "screen",
        "review_manifest": str(review_manifest),
        "review_audio_root": str(review_audio),
        "labels_csv": str(labels),
        "review_sampling_seed": REVIEW_SAMPLE_SEED,
        "review_pass_sample_fraction": pass_fraction,
        "review_selected_cases": writer.selected_cases,
        "review_selected_failure_rows": writer.selected_failure_rows,
        "review_selected_pass_rows": writer.selected_pass_rows,
    }), encoding="utf-8")
    return lab_root, output_path, summary_path, rows


def test_resume_loader_accepts_complete_cases_and_reconstructs_prior_tts_chars(tmp_path):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, _summary_path, rows = _write_interrupted_run(tmp_path)
    resumed = _load_screen_resume(output_path, lab_root=lab_root)

    assert resumed.rows == rows
    assert resumed.completed_cases == frozenset({("s001", "Nalini", "digits")})
    assert resumed.summary["stt_audio_seconds"] == 12.5
    expected_chars = len(make_readback(_stress_cards()["s001"], amount_style="digits"))
    assert resumed.prior_tts_chars == expected_chars
    assert resumed.possible_next_case == ("s002", "Nalini", "digits")
    assert resumed.possible_next_tts_chars == len(
        make_readback(_stress_cards()["s002"], amount_style="digits")
    )
    assert resumed.inferred_possible_cases == ({
        "card_id": "s002",
        "voice": "Nalini",
        "style": "digits",
        "characters": resumed.possible_next_tts_chars,
        "run_id": "run-old",
    },)


@pytest.mark.parametrize(
    ("field", "corrupt_value", "message"),
    [
        ("tts_chars_generated_new", 1, "TTS accounted lower bound does not match its components"),
        ("tts_credits_accounted_lower_bound_estimate", 0, "TTS credit estimate does not match accounted characters"),
    ],
)
def test_resume_loader_rejects_internally_inconsistent_tts_accounting(
    tmp_path, field, corrupt_value, message
):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, _rows = _write_interrupted_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    accounted = len(make_readback(_stress_cards()["s001"], amount_style="digits"))
    _write_current_summary(
        summary_path,
        summary,
        accounted_tts_chars=accounted,
        possible_cases=[],
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary[field] = corrupt_value
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        _load_screen_resume(output_path, lab_root=lab_root)


@pytest.mark.parametrize("mutation", ["wrong_characters", "duplicate_identity"])
def test_resume_loader_rejects_invalid_or_duplicate_inferred_tts_cases(tmp_path, mutation):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, _rows = _write_interrupted_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    expected_chars = len(make_readback(_stress_cards()["s002"], amount_style="words"))
    inferred = {
        "card_id": "s002",
        "voice": "Nalini",
        "style": "words",
        "characters": expected_chars,
        "run_id": "run-old",
    }
    cases = [dict(inferred)]
    if mutation == "wrong_characters":
        cases[0]["characters"] += 1
        message = "inferred TTS case is invalid"
    else:
        cases.append(dict(inferred))
        message = "duplicate inferred TTS case identity"
    accounted = len(make_readback(_stress_cards()["s001"], amount_style="digits"))
    _write_current_summary(
        summary_path,
        summary,
        accounted_tts_chars=accounted,
        possible_cases=cases,
    )

    with pytest.raises(ValueError, match=message):
        _load_screen_resume(output_path, lab_root=lab_root)


def test_resume_loader_allows_same_inferred_case_from_distinct_prior_runs(tmp_path):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, _rows = _write_interrupted_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    inferred = {
        "card_id": "s002",
        "voice": "Nalini",
        "style": "words",
        "characters": len(make_readback(_stress_cards()["s002"], amount_style="words")),
        "run_id": "run-old",
    }
    accounted = len(make_readback(_stress_cards()["s001"], amount_style="digits"))
    _write_current_summary(
        summary_path,
        summary,
        accounted_tts_chars=accounted,
        possible_cases=[inferred, {**inferred, "run_id": "run-older"}],
    )

    resumed = _load_screen_resume(output_path, lab_root=lab_root)

    assert resumed.inferred_possible_cases == (
        inferred,
        {**inferred, "run_id": "run-older"},
    )


@pytest.mark.parametrize(
    ("field", "mutate", "message"),
    [
        (
            "expected_paise",
            lambda row: [row[0] + 1, *row[1:]],
            "screen row expected_paise does not match stress card",
        ),
        ("passed", lambda _value: True, "screen row score does not match transcript"),
    ],
)
def test_resume_loader_rejects_tampered_echo_semantics(tmp_path, field, mutate, message):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, _summary_path, rows = _write_interrupted_run(tmp_path)
    encoded_rows = [asdict(row) for row in rows]
    encoded_rows[0][field] = mutate(encoded_rows[0][field])
    output_path.write_text(
        "".join(json.dumps(row) + "\n" for row in encoded_rows),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=message):
        _load_screen_resume(output_path, lab_root=lab_root)


def _write_current_summary(summary_path, summary, *, accounted_tts_chars, possible_cases):
    summary.pop("tts_chars", None)
    summary.pop("tts_credits_estimated", None)
    summary.update({
        "tts_chars_accounted_lower_bound": accounted_tts_chars,
        "tts_chars_completed_stage_forecast": accounted_tts_chars + 1000,
        "tts_chars_generated_new": accounted_tts_chars,
        "tts_chars_inferred_possible_unpersisted_cases": possible_cases,
        "tts_chars_pending_work_forecast": 1000,
        "tts_chars_reconstructed_prior_lower_bound": 0,
        "tts_chars_remaining_forecast": 1000,
        "tts_credits_accounted_lower_bound_estimate": round(accounted_tts_chars * 0.05, 2),
        "tts_credits_completed_stage_forecast": round((accounted_tts_chars + 1000) * 0.05, 2),
        "tts_credits_per_character": 0.05,
    })
    summary_path.write_text(json.dumps(summary), encoding="utf-8")


@pytest.mark.parametrize("characters", [True, 1])
def test_resume_loader_rejects_malformed_possible_tts_post_attempt_record(tmp_path, characters):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, _rows = _write_interrupted_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["tts_possible_unconfirmed_post_attempts"] = [{
        "attempt_number": 1,
        "card_id": "s001",
        "voice": "Nalini",
        "style": "digits",
        "characters": characters,
        "error_type": "RemoteProtocolError",
    }]
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(ValueError, match="possible unconfirmed TTS POST attempt"):
        _load_screen_resume(output_path, lab_root=lab_root)


@pytest.mark.parametrize("error_type", ["UnsupportedProtocol", "TransportError"])
def test_resume_loader_rejects_pre_dispatch_or_generic_tts_transport_error(tmp_path, error_type):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, _rows = _write_interrupted_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["tts_possible_unconfirmed_post_attempts"] = [{
        "attempt_number": 1,
        "card_id": "s001",
        "voice": "Nalini",
        "style": "digits",
        "characters": len(make_readback(_stress_cards()["s001"], amount_style="digits")),
        "error_type": error_type,
    }]
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(ValueError, match="possible unconfirmed TTS POST attempt"):
        _load_screen_resume(output_path, lab_root=lab_root)


def test_resume_loader_rolls_back_unselected_trailing_partial_and_uses_accounted_tts(tmp_path):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, completed_rows = _write_interrupted_run(tmp_path)
    partial_row = replace(
        completed_rows[0],
        card_id="s002",
        expected_paise=expected_sequence(_stress_cards()["s002"]),
    )
    source_rows = (*completed_rows, partial_row)
    output_path.write_text(
        "".join(json.dumps(asdict(row)) + "\n" for row in source_rows),
        encoding="utf-8",
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["rows_written"] = len(source_rows)
    summary["stt_requests_attempted"] = len(source_rows) + 1
    summary["stt_audio_seconds"] = 14.5
    partial_chars = len(make_readback(_stress_cards()["s002"], amount_style="digits"))
    completed_chars = len(make_readback(_stress_cards()["s001"], amount_style="digits"))
    accounted_chars = completed_chars + partial_chars
    possible_partial = {
        "card_id": "s002",
        "voice": "Nalini",
        "style": "digits",
        "characters": partial_chars,
        "run_id": "run-old",
    }
    earlier_possible = {
        "card_id": "s006",
        "voice": "Jwala",
        "style": "words",
        "characters": len(make_readback(_stress_cards()["s006"], amount_style="words")),
        "run_id": "run-old",
    }
    _write_current_summary(
        summary_path,
        summary,
        accounted_tts_chars=accounted_chars,
        possible_cases=[possible_partial, earlier_possible],
    )
    source_before = output_path.read_bytes()
    summary_before = summary_path.read_bytes()

    resumed = _load_screen_resume(output_path, lab_root=lab_root)

    assert resumed.rows == completed_rows
    assert resumed.completed_cases == frozenset({("s001", "Nalini", "digits")})
    assert resumed.partial_case_identity == ("s002", "Nalini", "digits")
    assert resumed.partial_case_rows_rolled_back == 1
    assert resumed.prior_tts_chars == accounted_chars
    assert resumed.summary["stt_requests_attempted"] == len(source_rows) + 1
    assert resumed.summary["stt_audio_seconds"] == 14.5
    assert resumed.inferred_possible_cases == (earlier_possible,)
    assert output_path.read_bytes() == source_before
    assert summary_path.read_bytes() == summary_before


def test_resume_loader_rejects_partial_case_with_review_selection_or_audio(tmp_path):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, completed_rows = _write_interrupted_run(tmp_path)
    partial_row = replace(
        completed_rows[0],
        card_id="s002",
        expected_paise=expected_sequence(_stress_cards()["s002"]),
    )
    source_rows = (*completed_rows, partial_row)
    output_path.write_text(
        "".join(json.dumps(asdict(row)) + "\n" for row in source_rows),
        encoding="utf-8",
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["rows_written"] = len(source_rows)
    summary["stt_requests_attempted"] = len(source_rows) + 1
    audio_paths = {
        condition: f"wav:partial:{condition}".encode() for condition in CONDITIONS
    }
    writer = EchoReviewWriter(
        Path(summary["review_audio_root"]),
        Path(summary["review_manifest"]),
        Path(summary["labels_csv"]),
        run_id=summary["run_id"],
        stage="screen",
        pass_fraction=0.0,
        resume=True,
    )
    writer.begin_case("s002", "Nalini", "digits", audio_paths)
    writer.record_row(replace(partial_row, passed=False))
    writer.close()
    summary["review_selected_cases"] += writer.selected_cases
    summary["review_selected_failure_rows"] += writer.selected_failure_rows
    summary["review_selected_pass_rows"] += writer.selected_pass_rows
    partial_chars = len(make_readback(_stress_cards()["s002"], amount_style="digits"))
    accounted_chars = len(make_readback(_stress_cards()["s001"], amount_style="digits")) + partial_chars
    _write_current_summary(
        summary_path,
        summary,
        accounted_tts_chars=accounted_chars,
        possible_cases=[],
    )

    with pytest.raises(ValueError, match="cannot safely replay partial case.*review selection or audio"):
        _load_screen_resume(output_path, lab_root=lab_root)


def test_resume_loader_rejects_partial_case_groups(tmp_path):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, rows = _write_interrupted_run(tmp_path)
    output_path.write_text(
        "".join(json.dumps(asdict(row)) + "\n" for row in rows[:2]),
        encoding="utf-8",
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["rows_written"] = 2
    summary["stt_requests_attempted"] = 2
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(ValueError, match="partial case"):
        _load_screen_resume(output_path, lab_root=lab_root)


def test_resume_loader_rejects_duplicate_or_unknown_rows(tmp_path):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, rows = _write_interrupted_run(tmp_path)
    output_path.write_text(
        "".join(json.dumps(asdict(row)) + "\n" for row in (*rows, rows[0])),
        encoding="utf-8",
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["rows_written"] = 4
    summary["stt_requests_attempted"] = 4
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate"):
        _load_screen_resume(output_path, lab_root=lab_root)


def test_resume_loader_rejects_duplicate_json_object_keys(tmp_path):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, _summary_path, rows = _write_interrupted_run(tmp_path)
    first = asdict(rows[0])
    encoded = json.dumps(first)
    output_path.write_text(
        encoded[:-1] + ',"passed":false}\n' + "".join(
            json.dumps(asdict(row)) + "\n" for row in rows[1:]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate JSON key"):
        _load_screen_resume(output_path, lab_root=lab_root)


def test_resume_loader_accepts_more_stt_attempts_than_result_rows(tmp_path):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, rows = _write_interrupted_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["stt_requests_attempted"] = len(rows) + 2
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    resumed = _load_screen_resume(output_path, lab_root=lab_root)

    assert resumed.summary["stt_requests_attempted"] == len(rows) + 2


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("voice", "UnlistedVoice", "unknown screen voice"),
        ("passed", "false", "passed must be bool"),
        ("unexpected", True, "invalid schema"),
    ],
)
def test_resume_loader_rejects_malformed_or_unknown_rows(tmp_path, field, value, message):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, rows = _write_interrupted_run(tmp_path)
    first = asdict(rows[0])
    first[field] = value
    output_path.write_text(
        "\n".join([json.dumps(first), *(json.dumps(asdict(row)) for row in rows[1:])]) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=message):
        _load_screen_resume(output_path, lab_root=lab_root)


@pytest.mark.parametrize("field", ["review_manifest", "review_audio_root", "labels_csv"])
def test_resume_loader_rejects_review_artifact_paths_outside_lab_root(tmp_path, field):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, _rows = _write_interrupted_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary[field] = str(tmp_path / "outside" / "artifact")
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(ValueError, match="beneath var/lab"):
        _load_screen_resume(output_path, lab_root=lab_root)


def test_resume_loader_validates_existing_label_header(tmp_path):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, _rows = _write_interrupted_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    Path(summary["labels_csv"]).write_text("wrong,header\n", encoding="utf-8")

    with pytest.raises(ValueError, match="labels CSV header"):
        _load_screen_resume(output_path, lab_root=lab_root)


def test_resume_writer_appends_manifest_and_restores_sampling_rng(tmp_path):
    lab_root = tmp_path / "var" / "lab"
    prior_rows = tuple(
        EchoRow(
            card_id="s001",
            voice="Nalini",
            style="digits",
            condition=condition,
            expected_paise=expected_sequence(_stress_cards()["s001"]),
            heard_paise=expected_sequence(_stress_cards()["s001"]),
            transcript=make_readback(_stress_cards()["s001"], amount_style="digits"),
            passed=True,
            tts_ms=10.5,
        )
        for condition in CONDITIONS
    )
    lab_root, output_path, _summary_path, _ = _write_interrupted_run(
        tmp_path,
        prior_rows,
        pass_fraction=0.5,
    )
    from scripts.run_echo_test import _load_screen_resume

    resumed = _load_screen_resume(output_path, lab_root=lab_root)
    manifest_path = resumed.artifact_paths["review_manifest"]
    labels_path = resumed.artifact_paths["labels"]
    before_manifest = manifest_path.read_bytes()

    expected_rng = Random(REVIEW_SAMPLE_SEED)
    for row in prior_rows:
        select_row_for_review(row, expected_rng, pass_fraction=0.5)
    expected_new_selection = [
        select_row_for_review(
            replace(row, card_id="s002"),
            expected_rng,
            pass_fraction=0.5,
        )
        for row in prior_rows
    ]
    new_rows = tuple(replace(row, card_id="s002") for row in prior_rows)
    new_audio = {condition: f"new:{condition}".encode() for condition in CONDITIONS}
    writer = EchoReviewWriter(
        resumed.artifact_paths["review_audio"],
        manifest_path,
        labels_path,
        run_id=resumed.summary["run_id"],
        stage="screen",
        seed=REVIEW_SAMPLE_SEED,
        pass_fraction=0.5,
        resume=True,
        rng_state=resumed.rng_state,
    )
    writer.begin_case("s002", "Nalini", "digits", new_audio)
    for row in new_rows:
        writer.record_row(row)
    writer.finish_case(new_rows, new_audio)
    writer.close()

    assert manifest_path.read_bytes().startswith(before_manifest)
    with labels_path.open("r", encoding="utf-8-sig", newline="") as stream:
        new_labels = [row for row in csv.DictReader(stream) if row["card_id"] == "s002"]
    assert [row["condition"] for row in new_labels] == [
        row.condition for row, selection in zip(new_rows, expected_new_selection, strict=True)
        if selection is not None
    ]


def test_live_resume_merges_prior_rows_and_aggregates_spend_without_repeating_cases(tmp_path, monkeypatch):
    from io import BytesIO
    import wave

    import scripts.run_echo_test as echo_script

    lab_root, source_path, source_summary_path, prior_rows = _write_interrupted_run(tmp_path)
    partial_card = _stress_cards()["s002"]
    partial_row = replace(
        prior_rows[0],
        card_id="s002",
        expected_paise=(partial_card.items[0].amount_paise, partial_card.total_paise),
    )
    source_rows = (*prior_rows, partial_row)
    source_path.write_text(
        "".join(json.dumps(asdict(row)) + "\n" for row in source_rows),
        encoding="utf-8",
    )
    source_summary = json.loads(source_summary_path.read_text(encoding="utf-8"))
    source_summary["rows_written"] = len(source_rows)
    source_summary["stt_requests_attempted"] = len(source_rows) + 1
    source_summary["stt_audio_seconds"] = 14.5
    previous_possible_attempt = {
        "attempt_number": 1,
        "card_id": "s006",
        "voice": "Jwala",
        "style": "words",
        "characters": len(make_readback(_stress_cards()["s006"], amount_style="words")),
        "error_type": "RemoteProtocolError",
    }
    source_summary["tts_possible_unconfirmed_post_attempts"] = [previous_possible_attempt]
    source_summary_path.write_text(json.dumps(source_summary), encoding="utf-8")
    resume = echo_script._load_screen_resume(source_path, lab_root=lab_root)
    source_bytes = source_path.read_bytes()

    pcm_buffer = BytesIO()
    with wave.open(pcm_buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 16000)
    pcm_wav = pcm_buffer.getvalue()
    noise_path = lab_root / "noise.wav"
    noise_path.write_bytes(b"noise")

    class FakeSettings:
        api_key = "offline-test-key"
        gnani_base_url = "https://invalid.example"

        @staticmethod
        def require_gnani():
            return None

    class FakeSettingsProvider:
        @staticmethod
        def load():
            return FakeSettings()

    class FakeHTTP:
        @staticmethod
        def close():
            return None

    ambiguous_text = make_readback(_stress_cards()["s003"], amount_style="digits")
    tts_attempt_texts = []

    class FakeTimbreClient:
        def __init__(self, *args, **kwargs):
            self.http = FakeHTTP()

        def synthesize(self, text):
            tts_attempt_texts.append(text)
            if text == ambiguous_text:
                raise httpx.RemoteProtocolError("server disconnected after POST")
            return b"mulaw-placeholder"

    class FakePrismaClient:
        def __init__(self, *args, **kwargs):
            self.http = FakeHTTP()
            self.calls = 0

        def transcribe(self, _wav, *, mode):
            self.calls += 1
            if self.calls == 1:
                raise httpx.ConnectError("temporary DNS failure")
            return "transcript"

    seen_cards = []

    def fake_run_echo(
        cards,
        voices,
        styles,
        conditions,
        *,
        synthesize,
        degrade,
        transcribe,
        on_row,
        on_case,
        on_case_audio,
        on_tts_attempt,
    ):
        seen_cards.extend(cards)
        for card_id, card in cards.items():
            voice, style = voices[0], styles[0]
            readback = make_readback(card, amount_style=style)
            on_tts_attempt(card_id, voice, style, len(readback))
            source_audio, tts_ms = synthesize(readback, voice)
            audios = {
                condition: source_audio if condition == "control" else degrade(source_audio, condition)
                for condition in conditions
            }
            on_case_audio(card_id, voice, style, audios)
            rows = []
            expected = (card.items[0].amount_paise, card.total_paise)
            for condition in conditions:
                transcript = transcribe(audios[condition])
                row = EchoRow(
                    card_id=card_id,
                    voice=voice,
                    style=style,
                    condition=condition,
                    expected_paise=expected,
                    heard_paise=(),
                    transcript=transcript,
                    passed=False,
                    tts_ms=tts_ms,
                )
                rows.append(row)
                on_row(row)
            on_case(tuple(rows), audios)
        attempt_text = ambiguous_text
        on_tts_attempt("s003", voices[0], "digits", len(attempt_text))
        synthesize(attempt_text, voices[0])

    monkeypatch.setattr(echo_script, "Settings", FakeSettingsProvider)
    monkeypatch.setattr(echo_script, "TimbreClient", FakeTimbreClient)
    monkeypatch.setattr(echo_script, "PrismaClient", FakePrismaClient)
    monkeypatch.setattr(echo_script, "DEFAULT_TELEPHONY_NOISE_PATH", noise_path)
    monkeypatch.setattr(echo_script, "normalize_upload", lambda *_args, **_kwargs: b"noise")
    monkeypatch.setattr(echo_script, "mulaw_to_wav", lambda _audio: pcm_wav)
    monkeypatch.setattr(echo_script, "codec_round_trip", lambda wav, _codec: wav)
    monkeypatch.setattr(echo_script, "mix_at_snr", lambda wav, _noise, _snr: (wav, 0.0))
    monkeypatch.setattr(echo_script, "run_echo", fake_run_echo)
    monkeypatch.setattr(echo_script.time, "sleep", lambda _seconds: None)

    output_path = lab_root / "echo_merged.jsonl"
    artifact_paths = echo_script._run_artifact_paths(
        output_path,
        resume.summary["run_id"],
        labels_path=resume.artifact_paths["labels"],
    )
    artifact_paths.update(resume.artifact_paths)
    stress_cards = _stress_cards()
    with pytest.raises(httpx.RemoteProtocolError, match="after POST"):
        echo_script._run_live(
            {"s001": stress_cards["s001"], "s002": stress_cards["s002"]},
            [("Nalini", "digits")],
            output_path,
            1.0,
            {"tts_chars": 100, "credits": 5.0},
            stage="screen",
            run_id=resume.summary["run_id"],
            artifact_paths=artifact_paths,
            resume=resume,
        )

    merged_rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    summary = json.loads(artifact_paths["summary"].read_text(encoding="utf-8"))
    assert source_path.read_bytes() == source_bytes
    assert merged_rows[:3] == [json.loads(json.dumps(asdict(row))) for row in prior_rows]
    assert seen_cards == ["s002"]
    assert [row["card_id"] for row in merged_rows[3:]] == ["s002"] * 3
    assert summary["status"] == "interrupted"
    assert summary["rows_written"] == 6
    assert summary["stt_requests_attempted"] == resume.summary["stt_requests_attempted"] + 4
    assert summary["stt_audio_seconds"] == 22.5
    assert len(tts_attempt_texts) == 2
    assert summary["partial_case_replay_history"] == [{
        "card_id": "s002",
        "voice": "Nalini",
        "style": "digits",
        "rows_rolled_back": 1,
        "replay_started": True,
        "replay_completed": True,
    }]
    assert summary["tts_chars_reconstructed_prior_lower_bound"] == resume.prior_tts_chars
    possible_current_chars = len(make_readback(stress_cards["s003"], amount_style="digits"))
    completed_new_chars = len(make_readback(stress_cards["s002"], amount_style="digits"))
    assert summary["tts_chars_generated_new"] == completed_new_chars
    assert summary["tts_chars_accounted_lower_bound"] == (
        resume.prior_tts_chars + completed_new_chars
    )
    assert summary["tts_chars_inferred_possible_unpersisted_cases"] == []
    assert summary["tts_possible_unconfirmed_post_attempts"] == [
        previous_possible_attempt,
        {
            "attempt_number": 2,
            "card_id": "s003",
            "voice": "Nalini",
            "style": "digits",
            "characters": possible_current_chars,
            "error_type": "RemoteProtocolError",
        },
    ]
    assert "tts_chars" not in summary
    assert summary["tts_chars_completed_stage_forecast"] == resume.prior_tts_chars + 100
    assert summary["tts_chars_remaining_forecast"] == 100
    assert summary["tts_credits_accounted_lower_bound_estimate"] == round(
        (resume.prior_tts_chars + completed_new_chars) * 0.05,
        2,
    )
    assert summary["request_interval_seconds"] == 1.0

    resumed_again = echo_script._load_screen_resume(output_path, lab_root=lab_root)
    assert len(resumed_again.rows) == 6
    assert resumed_again.summary["stt_requests_attempted"] == 9
    assert resumed_again.summary["tts_possible_unconfirmed_post_attempts"] == summary["tts_possible_unconfirmed_post_attempts"]
    assert resumed_again.inferred_possible_cases == tuple(summary["tts_chars_inferred_possible_unpersisted_cases"])


def test_successful_unrecorded_synthesis_reconciles_inferred_case_for_next_resume(tmp_path, monkeypatch):
    from io import BytesIO
    import wave

    import scripts.run_echo_test as echo_script

    lab_root, source_path, summary_path, prior_rows = _write_interrupted_run(tmp_path)
    first_case_chars = len(make_readback(_stress_cards()["s001"], amount_style="digits"))
    next_case = {
        "card_id": "s002",
        "voice": "Nalini",
        "style": "digits",
        "characters": len(make_readback(_stress_cards()["s002"], amount_style="digits")),
        "run_id": "run-old",
    }
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _write_current_summary(
        summary_path,
        summary,
        accounted_tts_chars=first_case_chars,
        possible_cases=[next_case],
    )
    resume = echo_script._load_screen_resume(source_path, lab_root=lab_root)

    pcm_buffer = BytesIO()
    with wave.open(pcm_buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 16000)
    pcm_wav = pcm_buffer.getvalue()
    noise_path = lab_root / "noise.wav"
    noise_path.write_bytes(b"noise")

    class FakeSettings:
        api_key = "offline-test-key"
        gnani_base_url = "https://invalid.example"

        @staticmethod
        def require_gnani():
            return None

    class FakeSettingsProvider:
        @staticmethod
        def load():
            return FakeSettings()

    class FakeHTTP:
        @staticmethod
        def close():
            return None

    class FakeTimbreClient:
        def __init__(self, *args, **kwargs):
            self.http = FakeHTTP()

        @staticmethod
        def synthesize(_text):
            return b"mulaw-placeholder"

    class FakePrismaClient:
        def __init__(self, *args, **kwargs):
            self.http = FakeHTTP()

        @staticmethod
        def transcribe(_wav, *, mode):
            raise httpx.ConnectError("offline STT failure before first row")

    monkeypatch.setattr(echo_script, "Settings", FakeSettingsProvider)
    monkeypatch.setattr(echo_script, "TimbreClient", FakeTimbreClient)
    monkeypatch.setattr(echo_script, "PrismaClient", FakePrismaClient)
    monkeypatch.setattr(echo_script, "DEFAULT_TELEPHONY_NOISE_PATH", noise_path)
    monkeypatch.setattr(echo_script, "normalize_upload", lambda *_args, **_kwargs: b"noise")
    monkeypatch.setattr(echo_script, "mulaw_to_wav", lambda _audio: pcm_wav)
    monkeypatch.setattr(echo_script, "codec_round_trip", lambda wav, _codec: wav)
    monkeypatch.setattr(echo_script, "mix_at_snr", lambda wav, _noise, _snr: (wav, 0.0))
    monkeypatch.setattr(echo_script.time, "sleep", lambda _seconds: None)

    output_path = lab_root / "echo_merged_after_stt_error.jsonl"
    artifact_paths = echo_script._run_artifact_paths(
        output_path,
        resume.summary["run_id"],
        labels_path=resume.artifact_paths["labels"],
    )
    artifact_paths.update(resume.artifact_paths)
    cards = _stress_cards()
    with pytest.raises(httpx.ConnectError, match="before first row"):
        echo_script._run_live(
            {"s001": cards["s001"], "s002": cards["s002"]},
            [("Nalini", "digits")],
            output_path,
            1.0,
            {"tts_chars": 100, "credits": 5.0},
            stage="screen",
            run_id=resume.summary["run_id"],
            artifact_paths=artifact_paths,
            resume=resume,
        )

    output_summary = json.loads(artifact_paths["summary"].read_text(encoding="utf-8"))
    assert output_summary["rows_written"] == len(prior_rows)
    assert output_summary["tts_chars_generated_new"] == next_case["characters"]
    assert output_summary["tts_chars_inferred_possible_unpersisted_cases"] == []

    resumed_again = echo_script._load_screen_resume(output_path, lab_root=lab_root)

    assert len(resumed_again.rows) == len(prior_rows)
    assert resumed_again.prior_tts_chars == first_case_chars + next_case["characters"]
    assert resumed_again.inferred_possible_cases == ()


@pytest.mark.parametrize(
    ("summary_update", "message"),
    [({"status": "complete"}, "interrupted"), ({"stage": "confirm"}, "screen")],
)
def test_resume_loader_requires_matching_interrupted_screen_summary(tmp_path, summary_update, message):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, _rows = _write_interrupted_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary.update(summary_update)
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        _load_screen_resume(output_path, lab_root=lab_root)


def test_resume_loader_rejects_unknown_summary_fields(tmp_path):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, _rows = _write_interrupted_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["unrecognized"] = "value"
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(ValueError, match="summary schema"):
        _load_screen_resume(output_path, lab_root=lab_root)


def test_resume_loader_rejects_duplicate_summary_keys(tmp_path):
    from scripts.run_echo_test import _load_screen_resume

    lab_root, output_path, summary_path, _rows = _write_interrupted_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary_path.write_text(
        json.dumps(summary)[:-1] + ',"status":"complete"}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate JSON key"):
        _load_screen_resume(output_path, lab_root=lab_root)


@pytest.mark.parametrize("failure_count", [0, 1, 2])
def test_connect_error_retry_is_bounded_with_exponential_backoff(monkeypatch, failure_count):
    from scripts.run_echo_test import _retry_connect_errors

    sleeps = []
    attempts = 0

    def fail_then_succeed():
        nonlocal attempts
        attempts += 1
        if attempts <= failure_count:
            raise httpx.ConnectError("temporary DNS failure")
        return "ok"

    monkeypatch.setattr("scripts.run_echo_test.time.sleep", sleeps.append)

    assert _retry_connect_errors(fail_then_succeed) == "ok"
    assert attempts == failure_count + 1
    assert sleeps == [1, 2][:failure_count]


def test_connect_error_retries_only_connect_errors(monkeypatch):
    from scripts.run_echo_test import _retry_connect_errors

    sleeps = []
    attempts = 0

    def provider_rejection():
        nonlocal attempts
        attempts += 1
        raise GnaniError("HTTP 429", status=429)

    monkeypatch.setattr("scripts.run_echo_test.time.sleep", sleeps.append)

    with pytest.raises(GnaniError, match="429"):
        _retry_connect_errors(provider_rejection)
    assert attempts == 1
    assert sleeps == []


def test_remote_protocol_error_is_not_retried_after_an_ambiguous_post(monkeypatch):
    from scripts.run_echo_test import _retry_connect_errors

    sleeps = []
    attempts = 0

    def disconnect_after_post():
        nonlocal attempts
        attempts += 1
        raise httpx.RemoteProtocolError("server disconnected after POST")

    monkeypatch.setattr("scripts.run_echo_test.time.sleep", sleeps.append)

    with pytest.raises(httpx.RemoteProtocolError, match="after POST"):
        _retry_connect_errors(disconnect_after_post)

    assert attempts == 1
    assert sleeps == []


def test_interrupted_confirm_run_writes_summary_for_estimate_card_ids(tmp_path, monkeypatch):
    from io import BytesIO
    import wave

    from scripts import run_echo_test as echo_script

    class FakeSettings:
        api_key = "offline-test-key"
        gnani_base_url = "https://invalid.example"

        @staticmethod
        def require_gnani():
            return None

    class FakeSettingsProvider:
        @staticmethod
        def load():
            return FakeSettings()

    class FakeHTTP:
        @staticmethod
        def close():
            return None

    class FakeTimbreClient:
        def __init__(self, *args, **kwargs):
            self.http = FakeHTTP()

        def synthesize(self, _text):
            return b"mulaw-placeholder"

    class FakePrismaClient:
        def __init__(self, *args, **kwargs):
            self.http = FakeHTTP()
            self.calls = 0

        def transcribe(self, _wav, *, mode):
            self.calls += 1
            if self.calls == len(CONDITIONS) + 1:
                raise GnaniError("HTTP 429", status=429)
            return ""

    estimate_cards = _estimate_cards()
    card_ids = list(estimate_cards)[:2]
    cards = {card_id: estimate_cards[card_id] for card_id in card_ids}
    first_card, second_card = (cards[card_id] for card_id in card_ids)
    voice, style = "Roopesh", "digits"
    pcm_buffer = BytesIO()
    with wave.open(pcm_buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 8000)
    pcm_wav = pcm_buffer.getvalue()

    noise_path = tmp_path / "noise.wav"
    noise_path.write_bytes(b"offline noise placeholder")
    monkeypatch.setattr(echo_script, "Settings", FakeSettingsProvider)
    monkeypatch.setattr(echo_script, "TimbreClient", FakeTimbreClient)
    monkeypatch.setattr(echo_script, "PrismaClient", FakePrismaClient)
    monkeypatch.setattr(echo_script, "DEFAULT_TELEPHONY_NOISE_PATH", noise_path)
    monkeypatch.setattr(echo_script, "normalize_upload", lambda *_args, **_kwargs: b"noise")
    monkeypatch.setattr(echo_script, "mulaw_to_wav", lambda _audio: pcm_wav)
    monkeypatch.setattr(echo_script, "codec_round_trip", lambda wav, _codec: wav)
    monkeypatch.setattr(echo_script, "mix_at_snr", lambda wav, _noise, _snr: (wav, 0.0))

    output_path = tmp_path / "echo_confirm.jsonl"
    run_id = "confirm-run"
    artifact_paths = echo_script._run_artifact_paths(
        output_path,
        run_id,
        labels_path=tmp_path / "confirm_labels.csv",
    )
    with pytest.raises(GnaniError, match="429"):
        echo_script._run_live(
            cards,
            [(voice, style)],
            output_path,
            1.0,
            {"tts_chars": 100, "credits": 5.0},
            stage="confirm",
            run_id=run_id,
            artifact_paths=artifact_paths,
        )

    summary = json.loads(artifact_paths["summary"].read_text(encoding="utf-8"))
    assert summary["status"] == "interrupted"
    assert summary["stage"] == "confirm"
    assert summary["rows_written"] == len(CONDITIONS)
    assert summary["stt_requests_attempted"] == len(CONDITIONS) + 1
    assert summary["stt_audio_seconds"] == len(CONDITIONS) + 1
    generated_tts_chars = sum(
        len(make_readback(card, amount_style=style))
        for card in (first_card, second_card)
    )
    assert summary["tts_chars_generated_new"] == generated_tts_chars
    assert summary["tts_chars_accounted_lower_bound"] == generated_tts_chars
    assert summary["tts_credits_accounted_lower_bound_estimate"] == round(
        generated_tts_chars * 0.05,
        2,
    )
    assert summary["tts_chars_inferred_possible_unpersisted_cases"] == []


@pytest.mark.parametrize("error", [httpx.UnsupportedProtocol("no scheme"), httpx.TransportError("unspecified")])
def test_only_allowlisted_post_dispatch_errors_are_possible_tts_attempts(error):
    from scripts.run_echo_test import _is_valid_possible_tts_error_type, _may_have_reached_timbre_post

    assert not _may_have_reached_timbre_post(error)
    assert not _is_valid_possible_tts_error_type(type(error).__name__)


@pytest.mark.parametrize(
    "error",
    [
        httpx.RemoteProtocolError("remote protocol"),
        httpx.ReadError("read failed"),
        httpx.WriteError("write failed"),
        httpx.ReadTimeout("read timed out"),
        httpx.WriteTimeout("write timed out"),
        httpx.CloseError("close failed"),
    ],
)
def test_allowlisted_post_dispatch_errors_are_valid_possible_tts_attempts(error):
    from scripts.run_echo_test import _is_valid_possible_tts_error_type, _may_have_reached_timbre_post

    assert _may_have_reached_timbre_post(error)
    assert _is_valid_possible_tts_error_type(type(error).__name__)


def test_connect_error_retry_counts_each_attempt(monkeypatch):
    from scripts.run_echo_test import _retry_connect_errors

    attempts_seen = []
    call_count = 0

    def fail_once_then_succeed():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.ConnectError("temporary DNS failure")
        return "ok"

    monkeypatch.setattr("scripts.run_echo_test.time.sleep", lambda _seconds: None)

    assert _retry_connect_errors(fail_once_then_succeed, on_attempt=lambda: attempts_seen.append(True)) == "ok"
    assert len(attempts_seen) == 2


def test_resume_preflight_rejects_output_collision_without_touching_source(tmp_path):
    import scripts.run_echo_test as echo_script

    lab_root, source_path, _summary_path, _rows = _write_interrupted_run(tmp_path)
    resume = echo_script._load_screen_resume(source_path, lab_root=lab_root)
    before_source = source_path.read_bytes()
    before_labels = resume.artifact_paths["labels"].read_bytes()
    paths = echo_script._run_artifact_paths(
        source_path,
        resume.summary["run_id"],
        labels_path=resume.artifact_paths["labels"],
    )
    paths.update(resume.artifact_paths)

    with pytest.raises(ValueError, match="collision"):
        echo_script._preflight_resume_artifacts(paths, resume, lab_root=lab_root)

    assert source_path.read_bytes() == before_source
    assert resume.artifact_paths["labels"].read_bytes() == before_labels


def test_resume_forecast_counts_only_pending_screen_cases(tmp_path):
    import scripts.run_echo_test as echo_script

    lab_root, source_path, _summary_path, _rows = _write_interrupted_run(tmp_path)
    resume = echo_script._load_screen_resume(source_path, lab_root=lab_root)
    cards = _stress_cards()
    pairs = [(voice, style) for voice in echo_script.HINDI_TIMBRE_VOICES for style in echo_script.STYLES]

    forecast = echo_script._forecast_resume(cards, pairs, resume)

    assert forecast["cards"] == len(cards)
    assert forecast["voice_style_pairs"] == len(pairs)
    assert forecast["completed_cases"] == 1
    assert forecast["remaining_cases"] == len(cards) * len(pairs) - 1
    assert forecast["tts_chars"] == sum(
        len(make_readback(card, amount_style=style))
        for card_id, card in cards.items()
        for voice, style in pairs
        if (card_id, voice, style) not in resume.completed_cases
    )


def test_live_resume_cli_passes_source_and_new_output_to_runner(tmp_path, monkeypatch, capsys):
    import scripts.run_echo_test as echo_script

    lab_root, source_path, _summary_path, prior_rows = _write_interrupted_run(tmp_path)
    source_bytes = source_path.read_bytes()
    output_path = lab_root / "echo_merged.jsonl"
    seen = {}

    def fake_run_live(cards, pairs, output, interval, forecast, **kwargs):
        seen.update(cards=cards, pairs=pairs, output=output, interval=interval, forecast=forecast, **kwargs)
        return list(prior_rows)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(echo_script, "_run_live", fake_run_live)

    result = echo_script.main([
        "--stage", "screen",
        "--resume-from", str(source_path),
        "--output", str(output_path),
        "--live",
    ])

    assert result == 0
    assert seen["output"] == output_path
    assert seen["resume"].source_path == source_path.resolve()
    assert seen["stage"] == "screen"
    assert seen["run_id"] == "run-old"
    assert source_path.read_bytes() == source_bytes
    assert "remaining_cases" in capsys.readouterr().out


def test_live_resume_cli_rejects_changed_request_interval_before_writes(tmp_path, monkeypatch, capsys):
    import scripts.run_echo_test as echo_script

    lab_root, source_path, _summary_path, _rows = _write_interrupted_run(tmp_path)
    labels_path = lab_root / "echo_labels.csv"
    labels_before = labels_path.read_bytes()
    output_path = lab_root / "echo_merged.jsonl"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        echo_script,
        "_run_live",
        lambda *_args, **_kwargs: pytest.fail("runner must not start with a changed interval"),
    )

    with pytest.raises(SystemExit):
        echo_script.main([
            "--stage", "screen",
            "--resume-from", str(source_path),
            "--output", str(output_path),
            "--request-interval-seconds", "0.75",
            "--live",
        ])

    assert "must match interrupted run interval" in capsys.readouterr().err
    assert not output_path.exists()
    assert labels_path.read_bytes() == labels_before


def _write_interrupted_confirm_run(
    root: Path,
    *,
    cards: dict,
    pairs: list[tuple[str, str]],
    complete_cases: int,
    extra_tts_chars: int = 0,
):
    from scripts.run_echo_test import _forecast
    from parcha.lab.echo_review import ensure_label_template

    lab_root = root / "var" / "lab"
    lab_root.mkdir(parents=True)
    output_path = lab_root / "echo_confirm_interrupted.jsonl"
    review_audio = lab_root / "echo_confirm_review"
    review_manifest = lab_root / "echo_confirm_review.jsonl"
    labels = lab_root / "echo_labels.csv"
    review_audio.mkdir()
    review_manifest.write_text("", encoding="utf-8")
    ensure_label_template(labels)

    all_cases = [
        (card_id, voice, style)
        for voice, style in pairs
        for card_id in cards
    ]
    selected_cases = all_cases[:complete_cases]
    rows = []
    for card_id, voice, style in selected_cases:
        card = cards[card_id]
        transcript = make_readback(card, amount_style=style)
        for condition in CONDITIONS:
            rows.append(EchoRow(
                card_id=card_id,
                voice=voice,
                style=style,
                condition=condition,
                expected_paise=expected_sequence(card),
                heard_paise=expected_sequence(card),
                transcript=transcript,
                passed=True,
                tts_ms=10.0,
            ))
    output_path.write_text(
        "".join(json.dumps(asdict(row), ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )

    known_tts_chars = sum(
        len(make_readback(cards[card_id], amount_style=style))
        for card_id, _voice, style in selected_cases
    )
    tts_chars = known_tts_chars + extra_tts_chars
    inferred_tts_cases = []
    if extra_tts_chars and len(selected_cases) < len(all_cases):
        next_card_id, next_voice, next_style = all_cases[len(selected_cases)]
        inferred_tts_cases.append({
            "card_id": next_card_id,
            "voice": next_voice,
            "style": next_style,
            "characters": len(make_readback(cards[next_card_id], amount_style=next_style)),
            "run_id": "confirm-run",
        })
    forecast = _forecast(cards, pairs)
    summary_path = output_path.with_name(f"{output_path.stem}_summary.json")
    summary_path.write_text(json.dumps({
        "output": str(output_path),
        "status": "interrupted",
        "rows_written": len(rows),
        "request_interval_seconds": 1.0,
        "stt_requests_attempted": len(rows) + 1,
        "stt_audio_seconds": 15323.92,
        "prisma_credits_estimated": 3064.78,
        "prisma_credits_per_audio_second": 0.2,
        "tts_chars_reconstructed_prior_lower_bound": 0,
        "tts_chars_generated_new": tts_chars,
        "tts_chars_accounted_lower_bound": tts_chars,
        "tts_chars_inferred_possible_unpersisted_cases": inferred_tts_cases,
        "tts_chars_pending_work_forecast": forecast["tts_chars"],
        "tts_chars_remaining_forecast": forecast["tts_chars"],
        "tts_chars_completed_stage_forecast": forecast["tts_chars"],
        "tts_credits_accounted_lower_bound_estimate": round(tts_chars * 0.05, 2),
        "tts_credits_completed_stage_forecast": forecast["credits"],
        "tts_credits_per_character": 0.05,
        "run_id": "confirm-run",
        "stage": "confirm",
        "review_manifest": str(review_manifest),
        "review_audio_root": str(review_audio),
        "labels_csv": str(labels),
        "review_sampling_seed": REVIEW_SAMPLE_SEED,
        "review_pass_sample_fraction": 0.0,
        "review_selected_cases": 0,
        "review_selected_failure_rows": 0,
        "review_selected_pass_rows": 0,
        "tts_possible_unconfirmed_post_attempts": [],
    }, indent=2), encoding="utf-8")
    return lab_root, output_path, summary_path, tuple(rows), selected_cases


def test_confirm_resume_validates_accounted_next_case_and_forecasts_remaining_work(tmp_path):
    from scripts.run_echo_test import _estimate_cards, _forecast_resume, _load_confirm_resume

    cards = _estimate_cards()
    pairs = [("Roopesh", "digits"), ("Vikrant", "words"), ("Chitra", "words")]
    ordered_cases = [
        (card_id, voice, style)
        for voice, style in pairs
        for card_id in cards
    ]
    next_case = ordered_cases[348]
    next_chars = len(make_readback(cards[next_case[0]], amount_style=next_case[2]))
    assert next_case == ("v109", "Chitra", "words")
    assert next_chars == 233

    lab_root, output_path, _summary_path, rows, _selected = _write_interrupted_confirm_run(
        tmp_path,
        cards=cards,
        pairs=pairs,
        complete_cases=348,
        extra_tts_chars=next_chars,
    )
    summary_path = output_path.with_name(f"{output_path.stem}_summary.json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["tts_chars_inferred_possible_unpersisted_cases"] = []
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    reconstructed_tts_chars = sum(
        len(make_readback(cards[card_id], amount_style=style))
        for card_id, _voice, style in ordered_cases[:348]
    )
    assert len(rows) == 1044
    assert summary["rows_written"] == 1044
    assert summary["stt_requests_attempted"] == 1045
    assert reconstructed_tts_chars == 67460
    assert summary["tts_chars_accounted_lower_bound"] == 67693

    resumed = _load_confirm_resume(output_path, pairs=pairs, lab_root=lab_root)
    forecast = _forecast_resume(cards, pairs, resumed)

    assert len(rows) == 1044
    assert resumed.stage == "confirm"
    assert resumed.completed_cases == frozenset(ordered_cases[:348])
    assert resumed.possible_next_case == next_case
    assert resumed.possible_next_tts_chars == next_chars
    assert resumed.prior_tts_chars == 67693
    assert resumed.possible_next_tts_already_accounted_chars == next_chars
    assert resumed.inferred_possible_cases == ({
        "card_id": "v109",
        "voice": "Chitra",
        "style": "words",
        "characters": 233,
        "run_id": "confirm-run",
    },)
    assert forecast["completed_cases"] == 348
    assert forecast["remaining_cases"] == 12
    assert forecast["next_case_tts_chars_already_accounted"] == next_chars
    assert forecast["tts_chars"] == 2531
    assert forecast["credits"] == 126.55


def test_confirm_resume_skips_persisted_cases_and_replays_only_next_case(tmp_path, monkeypatch):
    from io import BytesIO
    import wave

    from scripts import run_echo_test as echo_script

    cards_all = _estimate_cards()
    cards = {key: cards_all[key] for key in ("v001", "v002")}
    pairs = [("Roopesh", "digits")]
    next_chars = len(make_readback(cards["v002"], amount_style="digits"))
    lab_root, source_path, _summary_path, prior_rows, _selected = _write_interrupted_confirm_run(
        tmp_path,
        cards=cards,
        pairs=pairs,
        complete_cases=1,
        extra_tts_chars=next_chars,
    )
    resume = echo_script._load_confirm_resume(source_path, pairs=pairs, lab_root=lab_root)
    source_bytes = source_path.read_bytes()

    class FakeSettings:
        api_key = "offline-test-key"
        gnani_base_url = "https://invalid.example"

        @staticmethod
        def require_gnani():
            return None

    class FakeSettingsProvider:
        @staticmethod
        def load():
            return FakeSettings()

    class FakeHTTP:
        @staticmethod
        def close():
            return None

    last_text = {"value": ""}
    synthesized = []
    transcribed = []

    class FakeTimbreClient:
        def __init__(self, *args, **kwargs):
            self.http = FakeHTTP()

        def synthesize(self, text):
            last_text["value"] = text
            synthesized.append(text)
            return b"mulaw-placeholder"

    class FakePrismaClient:
        def __init__(self, *args, **kwargs):
            self.http = FakeHTTP()

        def transcribe(self, _wav, *, mode):
            transcribed.append(mode)
            return last_text["value"]

    pcm_buffer = BytesIO()
    with wave.open(pcm_buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 8000)
    pcm_wav = pcm_buffer.getvalue()
    noise_path = lab_root / "noise.wav"
    noise_path.write_bytes(b"offline noise placeholder")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(echo_script, "Settings", FakeSettingsProvider)
    monkeypatch.setattr(echo_script, "TimbreClient", FakeTimbreClient)
    monkeypatch.setattr(echo_script, "PrismaClient", FakePrismaClient)
    monkeypatch.setattr(echo_script, "DEFAULT_TELEPHONY_NOISE_PATH", noise_path)
    monkeypatch.setattr(echo_script, "normalize_upload", lambda *_args, **_kwargs: b"noise")
    monkeypatch.setattr(echo_script, "mulaw_to_wav", lambda _audio: pcm_wav)
    monkeypatch.setattr(echo_script, "codec_round_trip", lambda wav, _codec: wav)
    monkeypatch.setattr(echo_script, "mix_at_snr", lambda wav, _noise, _snr: (wav, 0.0))
    monkeypatch.setattr(echo_script.time, "sleep", lambda _seconds: None)

    output_path = lab_root / "echo_confirm_merged.jsonl"
    artifact_paths = echo_script._run_artifact_paths(
        output_path,
        resume.summary["run_id"],
        labels_path=resume.artifact_paths["labels"],
    )
    artifact_paths.update(resume.artifact_paths)
    echo_script._preflight_resume_artifacts(artifact_paths, resume, lab_root=lab_root)
    echo_script._run_live(
        cards,
        pairs,
        output_path,
        1.0,
        echo_script._forecast_resume(cards, pairs, resume),
        stage="confirm",
        run_id=resume.summary["run_id"],
        artifact_paths=artifact_paths,
        resume=resume,
    )

    merged_rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    summary = json.loads(artifact_paths["summary"].read_text(encoding="utf-8"))
    assert source_path.read_bytes() == source_bytes
    assert len(prior_rows) == 3
    assert [row["card_id"] for row in merged_rows] == ["v001"] * 3 + ["v002"] * 3
    assert synthesized == [make_readback(cards["v002"], amount_style="digits")]
    assert transcribed == ["verbatim"] * 3
    assert summary["status"] == "complete"
    assert summary["stage"] == "confirm"
    assert summary["rows_written"] == 6
    assert summary["tts_chars_accounted_lower_bound"] == next_chars * 2 + len(
        make_readback(cards["v001"], amount_style="digits")
    )


def test_confirm_resume_rejects_unreconciled_tts_accounting(tmp_path):
    from scripts.run_echo_test import _estimate_cards, _load_confirm_resume

    cards = {key: value for key, value in list(_estimate_cards().items())[:2]}
    pairs = [("Roopesh", "digits")]
    lab_root, output_path, summary_path, _rows, _selected = _write_interrupted_confirm_run(
        tmp_path, cards=cards, pairs=pairs, complete_cases=1, extra_tts_chars=1,
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["tts_chars_generated_new"] += 1
    summary["tts_chars_accounted_lower_bound"] += 1
    summary["tts_credits_accounted_lower_bound_estimate"] = round(
        summary["tts_chars_accounted_lower_bound"] * 0.05, 2,
    )
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(ValueError, match="cannot reconcile TTS accounting"):
        _load_confirm_resume(output_path, pairs=pairs, lab_root=lab_root)


def test_confirm_resume_requires_exactly_one_unpersisted_stt_attempt_for_tts_delta(tmp_path):
    from scripts.run_echo_test import _estimate_cards, _load_confirm_resume

    cards = _estimate_cards()
    pairs = [("Roopesh", "digits"), ("Vikrant", "words"), ("Chitra", "words")]
    ordered_cases = [
        (card_id, voice, style)
        for voice, style in pairs
        for card_id in cards
    ]
    next_case = ordered_cases[348]
    next_chars = len(make_readback(cards[next_case[0]], amount_style=next_case[2]))
    lab_root, output_path, summary_path, rows, _selected = _write_interrupted_confirm_run(
        tmp_path,
        cards=cards,
        pairs=pairs,
        complete_cases=348,
        extra_tts_chars=next_chars,
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["tts_chars_inferred_possible_unpersisted_cases"] = []
    summary["stt_requests_attempted"] = len(rows) + 2
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(ValueError, match="cannot reconcile TTS accounting"):
        _load_confirm_resume(output_path, pairs=pairs, lab_root=lab_root)


def test_confirm_resume_keeps_unbilled_next_case_as_possible_without_inflating_lower_bound(tmp_path):
    from scripts.run_echo_test import _estimate_cards, _load_confirm_resume

    cards = {key: value for key, value in list(_estimate_cards().items())[:2]}
    pairs = [("Roopesh", "digits")]
    lab_root, output_path, summary_path, _rows, _selected = _write_interrupted_confirm_run(
        tmp_path, cards=cards, pairs=pairs, complete_cases=1,
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["tts_chars_inferred_possible_unpersisted_cases"] = [{
        "card_id": "v002",
        "voice": "Roopesh",
        "style": "digits",
        "characters": len(make_readback(cards["v002"], amount_style="digits")),
        "run_id": summary["run_id"],
    }]
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    resume = _load_confirm_resume(output_path, pairs=pairs, lab_root=lab_root)

    assert resume.prior_tts_chars == len(make_readback(cards["v001"], amount_style="digits"))
    assert resume.possible_next_tts_already_accounted_chars == 0
    assert resume.inferred_possible_cases[0]["card_id"] == "v002"


def test_confirm_resume_cli_requires_screen_and_passes_confirm_cards(tmp_path, monkeypatch, capsys):
    import scripts.run_echo_test as echo_script

    cards = {key: value for key, value in list(_estimate_cards().items())[:2]}
    pairs = [("Roopesh", "digits")]
    lab_root, source_path, _summary_path, _rows, _selected = _write_interrupted_confirm_run(
        tmp_path, cards=cards, pairs=pairs, complete_cases=1,
    )
    screen_path = lab_root / "echo_screen.jsonl"
    screen_path.write_text("fixture screen rows", encoding="utf-8")
    output_path = lab_root / "echo_confirm_merged.jsonl"
    seen = {}

    def fake_run_live(cards_arg, pairs_arg, output, interval, forecast, **kwargs):
        seen.update(
            cards=cards_arg,
            pairs=pairs_arg,
            output=output,
            forecast=forecast,
            **kwargs,
        )
        return []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(echo_script, "_read_screen_pairs", lambda _path: pairs)
    monkeypatch.setattr(echo_script, "_run_live", fake_run_live)

    with pytest.raises(SystemExit):
        echo_script.main([
            "--stage", "confirm",
            "--resume-from", str(source_path),
            "--output", str(output_path),
            "--live",
        ])
    assert "--from is required with confirm --resume-from" in capsys.readouterr().err

    result = echo_script.main([
        "--stage", "confirm",
        "--from", str(screen_path),
        "--resume-from", str(source_path),
        "--output", str(output_path),
        "--live",
    ])

    assert result == 0
    assert seen["stage"] == "confirm"
    assert seen["resume"].stage == "confirm"
    assert seen["cards"] == _estimate_cards()
    assert seen["pairs"] == pairs
    assert seen["output"] == output_path
    assert not output_path.exists()
