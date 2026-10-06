import csv
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path
from random import Random

import pytest

from parcha.lab.echo import EchoRow
from parcha.lab.echo_review import (
    LABEL_FIELDS,
    append_label_rows,
    build_review_manifest_entry,
    build_review_label_rows,
    ensure_label_template,
    EchoReviewWriter,
    select_row_for_review,
)
from parcha.lab.amount_bench import HINDI_TIMBRE_VOICES
from scripts.run_echo_test import CONDITIONS as ECHO_CONDITIONS, STYLES, _read_screen_pairs, _stress_cards


CONDITIONS = ("control", "g711|clean", "amr_nb_4750|0")


def _case(passed=(True, True, True)):
    return tuple(
        EchoRow(
            card_id="s001",
            voice="Nalini",
            style="digits",
            condition=condition,
            expected_paise=(45000, 65000),
            heard_paise=(45000, 65000) if is_pass else (35000, 65000),
            transcript="read back",
            passed=is_pass,
            tts_ms=120.0,
        )
        for condition, is_pass in zip(CONDITIONS, passed, strict=True)
    )


def _write_complete_screen(tmp_path):
    screen_path = tmp_path / "echo_screen.jsonl"
    rows = []
    for voice, style in product(HINDI_TIMBRE_VOICES, STYLES):
        for card_id, card in _stress_cards().items():
            expected = [card.items[0].amount_paise, card.total_paise]
            for condition in ECHO_CONDITIONS:
                rows.append({
                    "card_id": card_id,
                    "voice": voice,
                    "style": style,
                    "condition": condition,
                    "expected_paise": expected,
                    "heard_paise": expected,
                    "transcript": "read back",
                    "passed": True,
                    "tts_ms": 120.0,
                })

    screen_path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    summary_path = screen_path.with_name(f"{screen_path.stem}_summary.json")
    summary_path.write_text(
        json.dumps({
            "output": str(screen_path),
            "status": "complete",
            "rows_written": len(rows),
            "stage": "screen",
        }),
        encoding="utf-8",
    )
    return screen_path, summary_path, rows


def test_review_selects_every_failed_row_and_a_reproducible_random_pass_sample():
    rng = Random(20261006)

    assert select_row_for_review(_case((True, False, True))[1], rng) == "failure"
    first = [select_row_for_review(_case()[0], rng) for _ in range(1000)]
    second_rng = Random(20261006)
    assert select_row_for_review(_case((True, False, True))[1], second_rng) == "failure"
    second = [select_row_for_review(_case()[0], second_rng) for _ in range(1000)]

    assert first == second
    assert 75 <= sum(selection == "pass_sample" for selection in first) <= 125


def test_review_manifest_links_each_condition_audio_and_label_rows_do_not_guess_failures():
    rows = _case((True, False, True))
    audio_paths = {condition: f"review/s001_Nalini_digits/{index}.wav" for index, condition in enumerate(CONDITIONS)}
    selections = ["pass_sample", "failure", None]

    entry = build_review_manifest_entry(
        rows,
        audio_paths,
        selections=selections,
        seed=20261006,
        run_id="run-abc",
        stage="screen",
    )
    labels = build_review_label_rows(entry)

    assert [item["condition"] for item in entry["conditions"]] == list(CONDITIONS)
    assert [item["audio_path"] for item in entry["conditions"]] == [audio_paths[c] for c in CONDITIONS]
    assert [item["selected"] for item in entry["conditions"]] == [True, True, False]
    assert entry["pass_sample_fraction"] == 0.10
    assert [item["label"] for item in labels] == ["pass", ""]
    assert labels[1]["allowed_labels"] == "timbre,line,prisma"
    assert labels[0]["allowed_labels"] == "pass"


def test_label_template_is_created_and_appended_without_overwriting_existing_rows(tmp_path):
    path = tmp_path / "echo_labels.csv"
    assert ensure_label_template(path) is True
    append_label_rows(path, [{field: "" for field in LABEL_FIELDS} | {"label": "pass"}])
    before = path.read_text(encoding="utf-8")

    assert ensure_label_template(path) is False
    assert path.read_text(encoding="utf-8") == before
    with path.open("r", encoding="utf-8", newline="") as stream:
        saved = list(csv.DictReader(stream))
    assert len(saved) == 1 and saved[0]["label"] == "pass"


def test_label_template_refuses_to_reuse_a_file_with_an_unexpected_header(tmp_path):
    path = tmp_path / "echo_labels.csv"
    path.write_text("other,data\nkeep,me\n", encoding="utf-8")

    with pytest.raises(ValueError, match="header"):
        ensure_label_template(path)

    assert path.read_text(encoding="utf-8") == "other,data\nkeep,me\n"


def test_writer_retains_all_case_audio_but_labels_only_selected_rows(tmp_path):
    audio_root = tmp_path / "review_audio"
    manifest_path = tmp_path / "review_manifest.jsonl"
    labels_path = tmp_path / "echo_labels.csv"
    audios = {condition: f"wav:{condition}".encode() for condition in CONDITIONS}
    rows = _case((True, False, True))

    writer = EchoReviewWriter(
        audio_root,
        manifest_path,
        labels_path,
        run_id="run-abc",
        stage="screen",
        seed=20261006,
        pass_fraction=0.0,
    )
    writer.begin_case("s001", "Nalini", "digits", audios)
    for row in rows:
        writer.record_row(row)
    writer.finish_case(rows, audios)
    writer.close()

    case_dir = audio_root / "s001_Nalini_digits"
    assert {path.name for path in case_dir.glob("*.wav")} == {
        "control.wav",
        "g711_clean.wav",
        "amr_nb_4750_0.wav",
    }
    assert [path.read_bytes() for path in sorted(case_dir.glob("*.wav"))] == [
        audios["amr_nb_4750|0"],
        audios["control"],
        audios["g711|clean"],
    ]
    with labels_path.open("r", encoding="utf-8-sig", newline="") as stream:
        labels = list(csv.DictReader(stream))
    assert [(row["condition"], row["label"]) for row in labels] == [("g711|clean", "")]
    assert writer.selected_failure_rows == 1
    assert writer.selected_pass_rows == 0
    events = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()]
    selection = events[0]
    assert selection["event"] == "selection"
    assert set(selection["audio_paths"]) == set(CONDITIONS)
    assert [row["selected"] for row in selection["conditions"]] == [False, True]


def test_writer_persists_all_audio_and_failed_label_before_case_completion(tmp_path):
    audio_root = tmp_path / "review_audio"
    manifest_path = tmp_path / "review_manifest.jsonl"
    labels_path = tmp_path / "echo_labels.csv"
    audios = {condition: f"wav:{condition}".encode() for condition in CONDITIONS}
    failed_first_row = _case((False, True, True))[0]

    writer = EchoReviewWriter(
        audio_root,
        manifest_path,
        labels_path,
        run_id="run-abc",
        stage="screen",
        pass_fraction=0.0,
    )
    writer.begin_case("s001", "Nalini", "digits", audios)
    writer.record_row(failed_first_row)

    assert len(list((audio_root / "s001_Nalini_digits").glob("*.wav"))) == 3
    entry = json.loads(manifest_path.read_text(encoding="utf-8").splitlines()[0])
    assert entry["status"] == "in_progress"
    assert entry["conditions"][0]["selected"] is True
    with labels_path.open("r", encoding="utf-8-sig", newline="") as stream:
        [label] = list(csv.DictReader(stream))
    assert label["label"] == ""

    writer.close()
    events = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()]
    interrupted = events[-1]
    assert interrupted["event"] == "case_interrupted"
    assert interrupted["case_id"] == "s001_Nalini_digits"
    assert interrupted["completed_conditions"] == ["control"]
    assert interrupted["audio_paths"] == entry["audio_paths"]
    assert Path(interrupted["audio_paths"]["control"]).read_bytes() == audios["control"]


def test_writer_refuses_existing_review_audio_without_replacing_it(tmp_path):
    audio_root = tmp_path / "review_audio"
    audio_root.mkdir()
    sentinel = audio_root / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="review audio directory"):
        EchoReviewWriter(
            audio_root,
            tmp_path / "review_manifest.jsonl",
            tmp_path / "echo_labels.csv",
            run_id="run-abc",
            stage="screen",
        )

    assert sentinel.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize(
    ("card_id", "voice", "style"),
    [
        ("../escape", "Nalini", "digits"),
        ("s001", "UnlistedVoice", "digits"),
        ("s001", "Nalini", "phonetic"),
    ],
)
def test_writer_rejects_unsafe_case_identity_before_persisting_audio(tmp_path, card_id, voice, style):
    audio_root = tmp_path / "review_audio"
    writer = EchoReviewWriter(
        audio_root,
        tmp_path / "review_manifest.jsonl",
        tmp_path / "echo_labels.csv",
        run_id="run-abc",
        stage="screen",
        pass_fraction=0.0,
    )
    try:
        with pytest.raises(ValueError, match="case identity"):
            writer.begin_case(card_id, voice, style, {
                condition: f"wav:{condition}".encode() for condition in CONDITIONS
            })
        assert not list(audio_root.rglob("*.wav"))
        assert not (tmp_path / "escape_Nalini_digits").exists()
    finally:
        writer.close()


def test_read_screen_pairs_rejects_a_partial_screen_jsonl(tmp_path):
    screen_path, _summary_path, rows = _write_complete_screen(tmp_path)
    rows.pop()
    screen_path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="coverage"):
        _read_screen_pairs(screen_path)


def test_read_screen_pairs_rejects_non_bool_pass_values(tmp_path):
    screen_path, _summary_path, rows = _write_complete_screen(tmp_path)
    rows[0]["passed"] = "false"
    screen_path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="passed.*bool"):
        _read_screen_pairs(screen_path)


def test_read_screen_pairs_rejects_unlisted_voices(tmp_path):
    screen_path, _summary_path, rows = _write_complete_screen(tmp_path)
    rows[0]["voice"] = "UnlistedVoice"
    screen_path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="voice"):
        _read_screen_pairs(screen_path)


def test_read_screen_pairs_rejects_incomplete_screen_summary(tmp_path):
    screen_path, summary_path, _rows = _write_complete_screen(tmp_path)
    assert len(_read_screen_pairs(screen_path)) == 3
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["status"] = "interrupted"
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(ValueError, match="summary.*complete"):
        _read_screen_pairs(screen_path)


def test_echo_stt_duration_counts_frames_read_from_ffmpeg_wav():
    from parcha.audio import mulaw_to_wav
    from scripts.run_echo_test import _measure_wav_duration_seconds

    wav = mulaw_to_wav(b"\xff" * 16000)

    assert _measure_wav_duration_seconds(wav) == 2.0


@pytest.mark.parametrize("first_call_raises", [False, True])
def test_echo_prisma_spacing_starts_next_call_after_prior_response(monkeypatch, first_call_raises):
    import scripts.run_echo_test as echo_script

    class FakeClock:
        now = 0.0

        def sleep(self, seconds):
            self.now += seconds

    class FakePrisma:
        def __init__(self, clock):
            self.clock = clock
            self.starts = []
            self.responses = []

        def transcribe(self, wav, *, mode):
            self.starts.append(self.clock.now)
            self.clock.now += 0.4
            self.responses.append(self.clock.now)
            if first_call_raises and len(self.starts) == 1:
                raise RuntimeError("simulated provider failure")
            return "heard"

    interval = 0.25
    clock = FakeClock()
    prisma = FakePrisma(clock)
    monkeypatch.setattr(echo_script.time, "sleep", clock.sleep)

    if first_call_raises:
        with pytest.raises(RuntimeError, match="simulated provider failure"):
            echo_script._transcribe_with_spacing(prisma, b"first", interval)
    else:
        assert echo_script._transcribe_with_spacing(prisma, b"first", interval) == "heard"
    assert echo_script._transcribe_with_spacing(prisma, b"second", interval) == "heard"

    assert prisma.starts[1] >= prisma.responses[0] + interval


def test_echo_live_summary_records_configured_request_interval(tmp_path, monkeypatch):
    from io import BytesIO
    import wave

    import scripts.run_echo_test as echo_script
    from parcha.schema import JobCard, LineItem

    wav_buffer = BytesIO()
    with wave.open(wav_buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 16000)
    pcm_wav = wav_buffer.getvalue()

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
        def synthesize(text):
            return b"mulaw-placeholder"

    class FakePrismaClient:
        def __init__(self, *args, **kwargs):
            self.http = FakeHTTP()

        @staticmethod
        def transcribe(wav, *, mode):
            return "fake transcript"

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
        card_id, card = next(iter(cards.items()))
        voice, style = voices[0], styles[0]
        on_tts_attempt(card_id, voice, style, len("read-back"))
        source_audio, tts_ms = synthesize("read-back", voice)
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
        return rows

    monkeypatch.setattr(echo_script, "Settings", FakeSettingsProvider)
    monkeypatch.setattr(echo_script, "TimbreClient", FakeTimbreClient)
    monkeypatch.setattr(echo_script, "PrismaClient", FakePrismaClient)
    monkeypatch.setattr(echo_script, "mulaw_to_wav", lambda _audio: pcm_wav)
    monkeypatch.setattr(echo_script, "normalize_upload", lambda *_args, **_kwargs: b"noise")
    monkeypatch.setattr(echo_script, "codec_round_trip", lambda wav, _codec: wav)
    monkeypatch.setattr(echo_script, "mix_at_snr", lambda wav, _noise, _snr: (wav, 0.0))
    monkeypatch.setattr(echo_script, "run_echo", fake_run_echo)
    monkeypatch.setattr(echo_script.time, "sleep", lambda _seconds: None)

    output_path = tmp_path / "echo_test.jsonl"
    artifact_paths = echo_script._run_artifact_paths(
        output_path,
        "run-abc",
        labels_path=tmp_path / "echo_labels.csv",
    )
    card = JobCard(
        items=(LineItem(id="part-1", label="service", kind="part", amount_paise=45000),),
        delivery=None,
        evidence=(),
    )
    echo_script._run_live(
        {"s001": card},
        [("Nalini", "digits")],
        output_path,
        0.75,
        {"tts_chars": 12, "credits": 0.6},
        stage="screen",
        run_id="run-abc",
        artifact_paths=artifact_paths,
    )

    summary = json.loads(artifact_paths["summary"].read_text(encoding="utf-8"))
    assert summary["request_interval_seconds"] == 0.75


def test_live_artifact_preflight_refuses_existing_run_outputs(tmp_path):
    from scripts.run_echo_test import _preflight_run_artifacts, _run_artifact_paths

    lab_root = tmp_path / "var" / "lab"
    output = lab_root / "echo_screen.jsonl"
    paths = _run_artifact_paths(
        output,
        "run-abc",
        labels_path=lab_root / "echo_labels.csv",
    )
    _preflight_run_artifacts(paths, lab_root=lab_root)
    output.write_text("previous run\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        _preflight_run_artifacts(paths, lab_root=lab_root)

    assert output.read_text(encoding="utf-8") == "previous run\n"


def test_live_artifact_preflight_rejects_path_collisions_without_creating_labels(tmp_path):
    from scripts.run_echo_test import _preflight_run_artifacts, _run_artifact_paths

    lab_root = tmp_path / "var" / "lab"
    colliding_path = lab_root / "echo_labels.csv"
    paths = _run_artifact_paths(
        colliding_path,
        "run-abc",
        labels_path=colliding_path,
    )

    with pytest.raises(ValueError, match="artifact path collision"):
        _preflight_run_artifacts(paths, lab_root=lab_root)

    assert not lab_root.exists()
