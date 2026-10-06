"""Forecast or run the Timbre read-back echo benchmark."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from io import BytesIO
import json
import math
from pathlib import Path
from random import Random
import time
from typing import Any, Callable, Mapping, Sequence, TypeVar
from uuid import uuid4
import wave

import httpx
from parcha.audio import codec_round_trip, mix_at_snr, mulaw_to_wav, normalize_upload
from parcha.config import DEFAULT_TELEPHONY_NOISE_PATH, Settings
from parcha.gnani import PrismaClient, TimbreClient
from parcha.lab.amount_bench import HINDI_TIMBRE_VOICES, STRESS_RUPEES, make_estimates
from parcha.lab.echo import EchoRow, expected_sequence, run_echo, score_echo
from parcha.lab.echo_review import (
    EchoReviewWriter,
    LABEL_FIELDS,
    PASS_SAMPLE_FRACTION,
    REVIEW_SAMPLE_SEED,
    ensure_label_template,
    select_row_for_review,
)
from parcha.readback import make_readback
from parcha.schema import Delivery, JobCard, LineItem

TTS_CREDITS_PER_CHAR = 0.05
CONDITIONS = ("control", "g711|clean", "amr_nb_4750|0")
STYLES = ("digits", "words")
_RETRY_ATTEMPTS = 3
_T = TypeVar("_T")


def _measure_wav_duration_seconds(wav: bytes) -> float:
    """Measure decoded audio length from bytes rather than the WAV frame-count header."""
    with wave.open(BytesIO(wav), "rb") as audio:
        if (
            audio.getnchannels() != 1
            or audio.getframerate() != 8000
            or audio.getsampwidth() != 2
            or audio.getcomptype() != "NONE"
        ):
            raise ValueError("Prisma audio must be mono 8 kHz 16-bit PCM WAV")

        frame_size = audio.getnchannels() * audio.getsampwidth()
        actual_bytes = 0
        while frames := audio.readframes(8192):
            actual_bytes += len(frames)
        if actual_bytes % frame_size:
            raise ValueError("WAV data ends with an incomplete PCM frame")
        return (actual_bytes // frame_size) / audio.getframerate()


def _transcribe_with_spacing(
    prisma: PrismaClient,
    wav: bytes,
    request_interval_seconds: float,
    *,
    on_attempt: Callable[[], None] | None = None,
) -> str:
    """Wait the configured interval after each Prisma response or failure."""
    def attempt() -> str:
        try:
            return prisma.transcribe(wav, mode="verbatim")
        finally:
            if request_interval_seconds:
                time.sleep(request_interval_seconds)

    return _retry_connect_errors(attempt, on_attempt=on_attempt)


def _retry_connect_errors(
    operation: Callable[[], _T],
    *,
    on_attempt: Callable[[], None] | None = None,
) -> _T:
    """Retry only transport connection failures, with three total attempts."""
    for attempt in range(_RETRY_ATTEMPTS):
        try:
            if on_attempt is not None:
                on_attempt()
            return operation()
        except httpx.ConnectError:
            if attempt == _RETRY_ATTEMPTS - 1:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def _stress_cards() -> dict[str, JobCard]:
    cards: dict[str, JobCard] = {}
    for index, rupees in enumerate(dict.fromkeys(STRESS_RUPEES), start=1):
        card_id = f"s{index:03d}"
        cards[card_id] = JobCard(
            items=(LineItem(id="part-1", label="service", kind="part", amount_paise=rupees * 100),),
            delivery=None,
            evidence=(),
        )
    return cards


def _estimate_cards() -> dict[str, JobCard]:
    cards: dict[str, JobCard] = {}
    for row in make_estimates():
        amounts = row["expected_amounts_paise"]
        part_count = int(row["entities"]["item_count"])
        items = tuple(
            LineItem(
                id=f"{'part' if index < part_count else 'labour'}-{index + 1}",
                label=f"part {index + 1}" if index < part_count else "labour",
                kind="part" if index < part_count else "labour",
                amount_paise=amount,
            )
            for index, amount in enumerate(amounts)
        )
        cards[row["id"]] = JobCard(
            items=items,
            delivery=Delivery(
                date=date(2026, 10, 5),
                window="evening",
                spoken=row["entities"]["delivery"],
            ),
            evidence=(),
        )
    return cards


_SCREEN_ROW_FIELDS = {
    "card_id",
    "voice",
    "style",
    "condition",
    "expected_paise",
    "heard_paise",
    "transcript",
    "passed",
    "tts_ms",
}
_LEGACY_INTERRUPTED_SUMMARY_FIELDS = {
    "labels_csv",
    "output",
    "prisma_credits_estimated",
    "prisma_credits_per_audio_second",
    "request_interval_seconds",
    "review_audio_root",
    "review_manifest",
    "review_pass_sample_fraction",
    "review_sampling_seed",
    "review_selected_cases",
    "review_selected_failure_rows",
    "review_selected_pass_rows",
    "rows_written",
    "run_id",
    "stage",
    "status",
    "stt_audio_seconds",
    "stt_requests_attempted",
    "tts_chars",
    "tts_credits_estimated",
}
_CURRENT_INTERRUPTED_SUMMARY_FIELDS = {
    "labels_csv",
    "output",
    "prisma_credits_estimated",
    "prisma_credits_per_audio_second",
    "request_interval_seconds",
    "review_audio_root",
    "review_manifest",
    "review_pass_sample_fraction",
    "review_sampling_seed",
    "review_selected_cases",
    "review_selected_failure_rows",
    "review_selected_pass_rows",
    "rows_written",
    "run_id",
    "stage",
    "status",
    "stt_audio_seconds",
    "stt_requests_attempted",
    "tts_chars_accounted_lower_bound",
    "tts_chars_completed_stage_forecast",
    "tts_chars_generated_new",
    "tts_chars_inferred_possible_unpersisted_case",
    "tts_chars_pending_work_forecast",
    "tts_chars_reconstructed_prior_lower_bound",
    "tts_chars_remaining_forecast",
    "tts_credits_accounted_lower_bound_estimate",
    "tts_credits_completed_stage_forecast",
    "tts_credits_per_character",
}
_HISTORY_INTERRUPTED_SUMMARY_FIELDS = (
    _CURRENT_INTERRUPTED_SUMMARY_FIELDS
    - {"tts_chars_inferred_possible_unpersisted_case"}
) | {"tts_chars_inferred_possible_unpersisted_cases"}
_PARTIAL_REPLAY_HISTORY_FIELD = "partial_case_replay_history"
_POSSIBLE_TTS_POST_ATTEMPTS_FIELD = "tts_possible_unconfirmed_post_attempts"
_AMBIGUOUS_TTS_POST_ERROR_CLASSES = (
    httpx.RemoteProtocolError,
    httpx.ReadError,
    httpx.WriteError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.CloseError,
)
_AMBIGUOUS_TTS_POST_ERROR_TYPES = frozenset(
    error_class.__name__ for error_class in _AMBIGUOUS_TTS_POST_ERROR_CLASSES
)
_INTERRUPTED_SUMMARY_BASES = (
    _LEGACY_INTERRUPTED_SUMMARY_FIELDS,
    _CURRENT_INTERRUPTED_SUMMARY_FIELDS,
    _HISTORY_INTERRUPTED_SUMMARY_FIELDS,
)
_SUPPORTED_INTERRUPTED_SUMMARY_FIELDS = tuple(
    base | optional
    for base in _INTERRUPTED_SUMMARY_BASES
    for optional in (
        set(),
        {_PARTIAL_REPLAY_HISTORY_FIELD},
        {_POSSIBLE_TTS_POST_ATTEMPTS_FIELD},
        {_PARTIAL_REPLAY_HISTORY_FIELD, _POSSIBLE_TTS_POST_ATTEMPTS_FIELD},
    )
)


def _may_have_reached_timbre_post(error: BaseException) -> bool:
    """Classify transport errors that may follow a submitted synthesis POST."""
    return type(error) in _AMBIGUOUS_TTS_POST_ERROR_CLASSES


def _is_valid_possible_tts_error_type(error_type: Any) -> bool:
    return type(error_type) is str and error_type in _AMBIGUOUS_TTS_POST_ERROR_TYPES


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


@dataclass(frozen=True)
class ScreenResume:
    source_path: Path
    rows: tuple[EchoRow, ...]
    summary: dict[str, Any]
    completed_cases: frozenset[tuple[str, str, str]]
    partial_case_identity: tuple[str, str, str] | None
    partial_case_rows_rolled_back: int
    prior_tts_chars: int
    possible_next_case: tuple[str, str, str] | None
    possible_next_tts_chars: int | None
    inferred_possible_cases: tuple[dict[str, Any], ...]
    rng_state: object
    artifact_paths: dict[str, Path]
    stage: str = "screen"
    possible_next_tts_already_accounted_chars: int = 0


def _parse_echo_row(value: Any, line_number: int, cards: dict[str, JobCard]) -> EchoRow:
    if type(value) is not dict or set(value) != _SCREEN_ROW_FIELDS:
        raise ValueError(f"screen row at line {line_number} has an invalid schema")
    for field in ("card_id", "voice", "style", "condition", "transcript"):
        if type(value[field]) is not str:
            raise ValueError(f"screen row {field} must be a string at line {line_number}")
    if value["voice"] not in HINDI_TIMBRE_VOICES:
        raise ValueError(f"unknown screen voice at line {line_number}: {value['voice']}")
    if value["style"] not in STYLES:
        raise ValueError(f"unknown screen style at line {line_number}: {value['style']}")
    if value["card_id"] not in cards:
        raise ValueError(f"unknown stress card id at line {line_number}: {value['card_id']}")
    if value["condition"] not in CONDITIONS:
        raise ValueError(f"unknown screen condition at line {line_number}: {value['condition']}")
    if type(value["passed"]) is not bool:
        raise ValueError(f"screen row passed must be bool at line {line_number}")
    for field in ("expected_paise", "heard_paise"):
        numbers = value[field]
        if type(numbers) is not list or any(type(number) is not int for number in numbers):
            raise ValueError(f"screen row {field} must be a list of integers at line {line_number}")
    card = cards[value["card_id"]]
    expected = tuple(value["expected_paise"])
    if expected != expected_sequence(card):
        raise ValueError(f"screen row expected_paise does not match stress card at line {line_number}")
    heard, passed = score_echo(card, value["transcript"])
    if tuple(value["heard_paise"]) != heard or value["passed"] is not passed:
        raise ValueError(f"screen row score does not match transcript at line {line_number}")
    if type(value["tts_ms"]) is not float or not math.isfinite(value["tts_ms"]):
        raise ValueError(f"screen row tts_ms must be a finite float at line {line_number}")
    return EchoRow(
        card_id=value["card_id"],
        voice=value["voice"],
        style=value["style"],
        condition=value["condition"],
        expected_paise=tuple(value["expected_paise"]),
        heard_paise=tuple(value["heard_paise"]),
        transcript=value["transcript"],
        passed=value["passed"],
        tts_ms=value["tts_ms"],
    )


def _validate_inferred_case(
    value: Any,
    *,
    include_run_id: bool,
    cards: Mapping[str, JobCard] | None = None,
) -> dict[str, Any]:
    cards = cards or _stress_cards()
    fields = {"card_id", "voice", "style", "characters"}
    if include_run_id:
        fields.add("run_id")
    if type(value) is not dict or set(value) != fields:
        raise ValueError("resume summary inferred TTS case has an invalid schema")
    if (
        type(value["card_id"]) is not str
        or value["card_id"] not in cards
        or type(value["voice"]) is not str
        or value["voice"] not in HINDI_TIMBRE_VOICES
        or type(value["style"]) is not str
        or value["style"] not in STYLES
        or type(value["characters"]) is not int
        or value["characters"] < 0
        or (include_run_id and (type(value["run_id"]) is not str or not value["run_id"]))
    ):
        raise ValueError("resume summary inferred TTS case is invalid")
    expected_characters = len(
        make_readback(cards[value["card_id"]], amount_style=value["style"])
    )
    if value["characters"] != expected_characters:
        raise ValueError("resume summary inferred TTS case is invalid")
    return dict(value)


def _completed_cases(rows: Sequence[EchoRow]) -> set[tuple[str, str, str]]:
    grouped: dict[tuple[str, str, str], list[str]] = {}
    for row in rows:
        identity = (row.card_id, row.voice, row.style)
        grouped.setdefault(identity, []).append(row.condition)
    return {identity for identity, conditions in grouped.items() if tuple(conditions) == CONDITIONS}


def _first_incomplete_case(
    rows: Sequence[EchoRow],
    cards: Mapping[str, JobCard],
    pairs: Sequence[tuple[str, str]],
) -> tuple[str, str, str] | None:
    completed = _completed_cases(rows)
    for voice, style in pairs:
        for card_id in cards:
            identity = (card_id, voice, style)
            if identity not in completed:
                return identity
    return None


def _inferred_case_record(
    identity: tuple[str, str, str],
    cards: dict[str, JobCard],
    run_id: str,
) -> dict[str, Any]:
    card_id, voice, style = identity
    return {
        "card_id": card_id,
        "voice": voice,
        "style": style,
        "characters": len(make_readback(cards[card_id], amount_style=style)),
        "run_id": run_id,
    }


def _read_echo_rows(
    path: Path,
    cards: Mapping[str, JobCard] | None = None,
) -> tuple[EchoRow, ...]:
    cards = cards or _stress_cards()
    rows: list[EchoRow] = []
    seen: set[tuple[str, str, str, str]] = set()
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                raise ValueError(f"blank row in screen JSONL at line {line_number}")
            try:
                value = json.loads(line, object_pairs_hook=_unique_json_object)
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed screen JSONL at line {line_number}") from exc
            except ValueError as exc:
                if "duplicate JSON key" in str(exc):
                    raise ValueError(f"{exc} at screen JSONL line {line_number}") from exc
                raise
            row = _parse_echo_row(value, line_number, cards)
            key = (row.voice, row.style, row.card_id, row.condition)
            if key in seen:
                raise ValueError(f"duplicate screen result row at line {line_number}: {key}")
            seen.add(key)
            rows.append(row)
    return tuple(rows)


def _require_private_path(path_value: Any, label: str, lab_root: Path, *, kind: str) -> Path:
    if type(path_value) is not str or not path_value:
        raise ValueError(f"resume summary {label} must be a path string")
    path = Path(path_value).resolve()
    try:
        path.relative_to(lab_root)
    except ValueError as exc:
        raise ValueError(f"resume {label} must stay beneath var/lab") from exc
    exists = path.is_dir() if kind == "directory" else path.is_file()
    if not exists:
        raise ValueError(f"resume {label} does not exist: {path}")
    return path


def _validate_resume_manifest(
    path: Path,
    audio_root: Path,
    summary: dict[str, Any],
    *,
    stage: str = "screen",
    reject_case_id: str | None = None,
) -> None:
    selected_cases: set[str] = set()
    selected_failures = 0
    selected_passes = 0
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                raise ValueError(f"blank review manifest row at line {line_number}")
            try:
                event = json.loads(line, object_pairs_hook=_unique_json_object)
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed review manifest at line {line_number}") from exc
            except ValueError as exc:
                if "duplicate JSON key" in str(exc):
                    raise ValueError(f"{exc} at review manifest line {line_number}") from exc
                raise
            if type(event) is not dict:
                raise ValueError(f"review manifest event must be an object at line {line_number}")
            if event.get("run_id") != summary["run_id"] or event.get("stage") != stage:
                raise ValueError(f"review manifest run mismatch at line {line_number}")
            event_type = event.get("event")
            if event_type not in ("selection", "result", "case_complete", "case_interrupted"):
                raise ValueError(f"unsupported review manifest event at line {line_number}")
            case_id = event.get("case_id")
            if type(case_id) is not str or not case_id:
                raise ValueError(f"review manifest case_id missing at line {line_number}")
            if reject_case_id is not None and case_id == reject_case_id:
                raise ValueError(
                    f"cannot safely replay partial case {case_id}: review selection or audio exists"
                )

            audio_paths = event.get("audio_paths")
            if event_type in ("selection", "result", "case_interrupted"):
                if type(audio_paths) is not dict or set(audio_paths) != set(CONDITIONS):
                    raise ValueError(f"review manifest audio paths invalid at line {line_number}")
                for condition, audio_value in audio_paths.items():
                    if type(audio_value) is not str:
                        raise ValueError(f"review audio path must be a string at line {line_number}")
                    audio_path = Path(audio_value).resolve()
                    try:
                        audio_path.relative_to(audio_root)
                    except ValueError as exc:
                        raise ValueError("review audio path escapes the review audio root") from exc
                    if not audio_path.is_file():
                        raise ValueError(f"review audio file is missing: {audio_path}")

            if event_type in ("selection", "result"):
                conditions = event.get("conditions")
                if type(conditions) is not list or not conditions:
                    raise ValueError(f"review manifest conditions invalid at line {line_number}")
                if event_type == "selection":
                    if case_id in selected_cases:
                        raise ValueError(f"duplicate review selection event for {case_id}")
                    selected_cases.add(case_id)
                for condition_row in conditions:
                    if type(condition_row) is not dict:
                        raise ValueError(f"review condition must be an object at line {line_number}")
                    if condition_row.get("condition") not in CONDITIONS:
                        raise ValueError(f"review condition unknown at line {line_number}")
                    if type(condition_row.get("selected")) is not bool:
                        raise ValueError(f"review selected flag must be bool at line {line_number}")
                    if condition_row["selected"]:
                        selection = condition_row.get("selection")
                        if selection == "failure":
                            selected_failures += 1
                        elif selection == "pass_sample":
                            selected_passes += 1
                        else:
                            raise ValueError(f"review selection value invalid at line {line_number}")

    expected = (
        len(selected_cases),
        selected_failures,
        selected_passes,
    )
    actual = (
        summary["review_selected_cases"],
        summary["review_selected_failure_rows"],
        summary["review_selected_pass_rows"],
    )
    if expected != actual:
        raise ValueError(f"review manifest selection counts do not match summary: {expected} != {actual}")


def _load_echo_resume(
    path: Path,
    *,
    stage: str,
    cards: dict[str, JobCard],
    pairs: Sequence[tuple[str, str]],
    lab_root: Path = Path("var/lab"),
) -> ScreenResume:
    if stage not in ("screen", "confirm"):
        raise ValueError(f"unsupported resume stage: {stage}")
    if not cards or len(set(cards)) != len(cards):
        raise ValueError("resume cards must have unique ids")
    if not pairs or any(
        type(pair) not in (tuple, list)
        or len(pair) != 2
        or type(pair[0]) is not str
        or pair[0] not in HINDI_TIMBRE_VOICES
        or type(pair[1]) is not str
        or pair[1] not in STYLES
        for pair in pairs
    ) or len(set(pairs)) != len(pairs):
        raise ValueError("resume voice/style pairs are invalid or duplicated")
    lab_root = lab_root.resolve()
    source_path = path.resolve()
    try:
        source_path.relative_to(lab_root)
    except ValueError as exc:
        raise ValueError("resume input must stay beneath var/lab") from exc
    if not source_path.is_file():
        raise ValueError(f"resume input does not exist: {source_path}")

    rows = _read_echo_rows(source_path, cards)
    if not rows:
        raise ValueError("resume input has no completed screen rows")

    expected_order = [
        (card_id, voice, style)
        for voice, style in pairs
        for card_id in cards
    ]
    groups: list[tuple[str, str, str]] = []
    current_identity: tuple[str, str, str] | None = None
    current_conditions: list[str] = []
    seen_cases: set[tuple[str, str, str]] = set()
    partial_case_identity: tuple[str, str, str] | None = None
    partial_case_rows_rolled_back = 0
    for row in rows:
        identity = (row.card_id, row.voice, row.style)
        if identity != current_identity:
            if current_identity is not None:
                if tuple(current_conditions) != CONDITIONS:
                    raise ValueError(f"partial case is not the trailing case in resume input: {current_identity}")
                groups.append(current_identity)
            if identity in seen_cases:
                raise ValueError(f"duplicate/non-contiguous case in resume input: {identity}")
            seen_cases.add(identity)
            current_identity = identity
            current_conditions = []
        current_conditions.append(row.condition)
        if len(current_conditions) > len(CONDITIONS):
            raise ValueError(f"partial case or extra rows in resume input: {identity}")
    if current_identity is not None:
        if tuple(current_conditions) != CONDITIONS:
            if tuple(current_conditions) != CONDITIONS[:len(current_conditions)]:
                raise ValueError(f"partial case conditions are not an ordered prefix: {current_identity}")
            partial_case_identity = current_identity
            partial_case_rows_rolled_back = len(current_conditions)
        else:
            groups.append(current_identity)
    if groups != expected_order[:len(groups)]:
        raise ValueError("resume cases must be a unique prefix of the screen case order")
    if partial_case_identity is not None and (
        len(groups) >= len(expected_order)
        or partial_case_identity != expected_order[len(groups)]
    ):
        raise ValueError("partial case must be the expected next case in the screen case order")
    possible_next_case = expected_order[len(groups)] if len(groups) < len(expected_order) else None

    summary_path = source_path.with_name(f"{source_path.stem}_summary.json")
    try:
        summary = json.loads(
            summary_path.read_text(encoding="utf-8-sig"),
            object_pairs_hook=_unique_json_object,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read resume summary: {summary_path}") from exc
    if type(summary) is not dict or summary.get("status") != "interrupted":
        raise ValueError("resume summary must report interrupted status")
    if set(summary) not in _SUPPORTED_INTERRUPTED_SUMMARY_FIELDS:
        raise ValueError("resume summary schema has missing or unknown fields")
    if summary.get("stage") != stage:
        raise ValueError(f"resume summary must have stage '{stage}'")
    if type(summary.get("output")) is not str or Path(summary["output"]).resolve() != source_path:
        raise ValueError("resume summary output path does not match the input JSONL")
    if type(summary.get("rows_written")) is not int or summary["rows_written"] != len(rows):
        raise ValueError("resume summary row count does not match input JSONL")
    if type(summary.get("stt_requests_attempted")) is not int or summary["stt_requests_attempted"] < len(rows):
        raise ValueError("resume summary STT request count is lower than input JSONL rows")
    interval = summary.get("request_interval_seconds")
    if type(interval) not in (int, float) or not math.isfinite(interval) or interval < 0:
        raise ValueError("resume summary request interval is invalid")
    duration = summary.get("stt_audio_seconds")
    if type(duration) not in (int, float) or not math.isfinite(duration) or duration < 0:
        raise ValueError("resume summary STT duration is invalid")
    run_id = summary.get("run_id")
    if type(run_id) is not str or not run_id:
        raise ValueError("resume summary run_id is invalid")
    if summary.get("review_sampling_seed") != REVIEW_SAMPLE_SEED:
        raise ValueError("resume review sampling seed does not match this runner")
    fraction = summary.get("review_pass_sample_fraction")
    if type(fraction) not in (int, float) or not math.isfinite(fraction) or not 0 <= fraction <= 1:
        raise ValueError("resume review pass fraction is invalid")
    for field in (
        "review_selected_cases",
        "review_selected_failure_rows",
        "review_selected_pass_rows",
    ):
        if type(summary.get(field)) is not int or summary[field] < 0:
            raise ValueError(f"resume summary {field} is invalid")
    for field in (
        "tts_chars",
        "tts_chars_accounted_lower_bound",
        "tts_chars_completed_stage_forecast",
        "tts_chars_generated_new",
        "tts_chars_pending_work_forecast",
        "tts_chars_reconstructed_prior_lower_bound",
        "tts_chars_remaining_forecast",
    ):
        if field in summary and (type(summary[field]) is not int or summary[field] < 0):
            raise ValueError(f"resume summary {field} is invalid")
    for field in (
        "prisma_credits_estimated",
        "prisma_credits_per_audio_second",
        "tts_credits_estimated",
        "tts_credits_accounted_lower_bound_estimate",
        "tts_credits_completed_stage_forecast",
        "tts_credits_per_character",
    ):
        if field in summary and (
            type(summary[field]) not in (int, float)
            or not math.isfinite(summary[field])
            or summary[field] < 0
        ):
            raise ValueError(f"resume summary {field} is invalid")
    accounted_tts_fields = {
        "tts_chars_accounted_lower_bound",
        "tts_chars_reconstructed_prior_lower_bound",
        "tts_chars_generated_new",
    }
    if accounted_tts_fields.issubset(summary):
        accounted_chars = summary["tts_chars_accounted_lower_bound"]
        component_chars = (
            summary["tts_chars_reconstructed_prior_lower_bound"]
            + summary["tts_chars_generated_new"]
        )
        if accounted_chars != component_chars:
            raise ValueError("resume summary TTS accounted lower bound does not match its components")
        accounted_credit_fields = {
            "tts_credits_accounted_lower_bound_estimate",
            "tts_credits_per_character",
        }
        if accounted_credit_fields.issubset(summary) and summary[
            "tts_credits_accounted_lower_bound_estimate"
        ] != round(accounted_chars * summary["tts_credits_per_character"], 2):
            raise ValueError("resume summary TTS credit estimate does not match accounted characters")
    if "tts_chars_inferred_possible_unpersisted_case" in summary:
        possible = summary["tts_chars_inferred_possible_unpersisted_case"]
        if possible is not None:
            _validate_inferred_case(possible, include_run_id=False, cards=cards)
    if "tts_chars_inferred_possible_unpersisted_cases" in summary:
        possible_cases = summary["tts_chars_inferred_possible_unpersisted_cases"]
        if type(possible_cases) is not list:
            raise ValueError("resume summary inferred TTS cases must be a list")
        inferred_case_identities: set[tuple[str, str, str, str]] = set()
        for possible in possible_cases:
            inferred = _validate_inferred_case(possible, include_run_id=True, cards=cards)
            identity = (
                inferred["card_id"],
                inferred["voice"],
                inferred["style"],
                inferred["run_id"],
            )
            if identity in inferred_case_identities:
                raise ValueError("resume summary has a duplicate inferred TTS case identity")
            inferred_case_identities.add(identity)
    replay_history = summary.get(_PARTIAL_REPLAY_HISTORY_FIELD, [])
    if type(replay_history) is not list:
        raise ValueError("resume summary partial case replay history must be a list")
    for record in replay_history:
        if (
            type(record) is not dict
            or set(record) != {
                "card_id", "voice", "style", "rows_rolled_back", "replay_started", "replay_completed"
            }
            or type(record.get("card_id")) is not str
            or record["card_id"] not in cards
            or type(record.get("voice")) is not str
            or record["voice"] not in HINDI_TIMBRE_VOICES
            or type(record.get("style")) is not str
            or record["style"] not in STYLES
            or type(record.get("rows_rolled_back")) is not int
            or record["rows_rolled_back"] < 1
            or type(record.get("replay_started")) is not bool
            or type(record.get("replay_completed")) is not bool
            or (record["replay_completed"] and not record["replay_started"])
        ):
            raise ValueError("resume summary partial case replay record is invalid")
    possible_tts_attempts = summary.get(_POSSIBLE_TTS_POST_ATTEMPTS_FIELD, [])
    if type(possible_tts_attempts) is not list:
        raise ValueError("resume summary possible unconfirmed TTS POST attempts must be a list")
    for attempt_number, attempt in enumerate(possible_tts_attempts, start=1):
        if (
            type(attempt) is not dict
            or set(attempt) != {
                "attempt_number", "card_id", "voice", "style", "characters", "error_type"
            }
            or type(attempt.get("attempt_number")) is not int
            or attempt["attempt_number"] != attempt_number
            or type(attempt.get("card_id")) is not str
            or attempt["card_id"] not in cards
            or type(attempt.get("voice")) is not str
            or attempt["voice"] not in HINDI_TIMBRE_VOICES
            or type(attempt.get("style")) is not str
            or attempt["style"] not in STYLES
            or type(attempt.get("characters")) is not int
            or attempt["characters"] < 1
            or attempt["characters"]
            != len(make_readback(cards[attempt["card_id"]], amount_style=attempt["style"]))
            or not _is_valid_possible_tts_error_type(attempt.get("error_type"))
        ):
            raise ValueError("resume summary possible unconfirmed TTS POST attempt is invalid")

    review_manifest = _require_private_path(summary.get("review_manifest"), "review manifest", lab_root, kind="file")
    review_audio = _require_private_path(summary.get("review_audio_root"), "review audio root", lab_root, kind="directory")
    labels = _require_private_path(summary.get("labels_csv"), "labels CSV", lab_root, kind="file")
    with labels.open("r", encoding="utf-8-sig", newline="") as stream:
        if tuple(next(csv.reader(stream), ()) or ()) != LABEL_FIELDS:
            raise ValueError("resume labels CSV header is invalid")
    partial_review_case_id = None
    if partial_case_identity is not None:
        card_id, voice, style = partial_case_identity
        partial_review_case_id = f"{card_id}_{voice}_{style}"
        case_audio_dir = (review_audio / partial_review_case_id).resolve()
        try:
            case_audio_dir.relative_to(review_audio)
        except ValueError as exc:
            raise ValueError("partial case review audio path escapes the review audio root") from exc
        if case_audio_dir.exists():
            raise ValueError(
                f"cannot safely replay partial case {partial_review_case_id}: review selection or audio exists"
            )
    _validate_resume_manifest(
        review_manifest,
        review_audio,
        summary,
        stage=stage,
        reject_case_id=partial_review_case_id,
    )

    rng = Random(REVIEW_SAMPLE_SEED)
    reconstructed_tts_chars = 0
    completed_rows = rows[:len(groups) * len(CONDITIONS)]
    for row in completed_rows:
        select_row_for_review(row, rng, pass_fraction=float(fraction))
    for card_id, voice, style in groups:
        reconstructed_tts_chars += len(make_readback(cards[card_id], amount_style=style))
    if partial_case_identity is not None:
        card_id, _voice, style = partial_case_identity
        reconstructed_tts_chars += len(make_readback(cards[card_id], amount_style=style))
    prior_tts_chars = summary.get("tts_chars_accounted_lower_bound", reconstructed_tts_chars)
    if prior_tts_chars < reconstructed_tts_chars:
        raise ValueError("resume summary TTS accounted lower bound is below persisted case evidence")
    possible_next_tts_chars = (
        len(make_readback(cards[possible_next_case[0]], amount_style=possible_next_case[2]))
        if possible_next_case is not None
        else None
    )
    possible_next_tts_already_accounted_chars = 0
    if "tts_chars_inferred_possible_unpersisted_cases" in summary:
        inherited_possible_cases = tuple(
            dict(item)
            for item in summary["tts_chars_inferred_possible_unpersisted_cases"]
            if partial_case_identity is None
            or (item["card_id"], item["voice"], item["style"]) != partial_case_identity
        )
    elif summary.get("tts_chars_inferred_possible_unpersisted_case") is not None:
        legacy_possible = _validate_inferred_case(
            summary["tts_chars_inferred_possible_unpersisted_case"],
            include_run_id=False,
            cards=cards,
        )
        inherited_possible_cases = (
            ({**legacy_possible, "run_id": run_id},)
            if partial_case_identity is None
            or (legacy_possible["card_id"], legacy_possible["voice"], legacy_possible["style"])
            != partial_case_identity
            else ()
        )
    elif possible_next_case is not None and partial_case_identity is None:
        inferred = _inferred_case_record(possible_next_case, cards, run_id)
        inherited_possible_cases = (inferred,)
    else:
        inherited_possible_cases = ()
    if stage == "confirm":
        # A confirm resume may replay one uncertain next case after a successful
        # synthesis whose STT rows were not persisted. Require the summary's
        # inferred-case record to explain the exact difference from persisted
        # rows; arbitrary credit deltas are not safe to carry forward.
        unexplained_tts_chars = prior_tts_chars - reconstructed_tts_chars
        explicit_accounting_records = (
            inherited_possible_cases
            if (
                "tts_chars_inferred_possible_unpersisted_cases" in summary
                or summary.get("tts_chars_inferred_possible_unpersisted_case") is not None
            )
            else ()
        )
        accounting_records = [
            item for item in explicit_accounting_records
            if partial_case_identity is None
            or (item["card_id"], item["voice"], item["style"]) != partial_case_identity
        ]
        if unexplained_tts_chars:
            if (
                unexplained_tts_chars < 0
                or possible_next_case is None
                or partial_case_identity is not None
                or unexplained_tts_chars != possible_next_tts_chars
                or summary["stt_requests_attempted"] != len(rows) + 1
                or (
                    accounting_records
                    and (
                        len(accounting_records) != 1
                        or (
                            accounting_records[0]["card_id"],
                            accounting_records[0]["voice"],
                            accounting_records[0]["style"],
                        ) != possible_next_case
                        or accounting_records[0]["characters"] != unexplained_tts_chars
                    )
                )
            ):
                raise ValueError("cannot reconcile TTS accounting with the next uncertain confirm case")
            possible_next_tts_already_accounted_chars = unexplained_tts_chars
            if not accounting_records:
                # Some interrupted summaries have no inferred-case entry even
                # though one extra STT attempt and the exact next-case TTS
                # character delta establish that synthesis occurred. Carry the
                # attribution into the new summary so another resume can audit it.
                inferred_next = _inferred_case_record(possible_next_case, cards, run_id)
                if inferred_next not in inherited_possible_cases:
                    inherited_possible_cases = (*inherited_possible_cases, inferred_next)
        elif accounting_records and (
            possible_next_case is None
            or len(accounting_records) != 1
            or (accounting_records[0]["card_id"], accounting_records[0]["voice"], accounting_records[0]["style"])
            != possible_next_case
            or accounting_records[0]["characters"] != possible_next_tts_chars
        ):
            # A summary may carry a possible case that was never billed (for
            # example, synthesis failed before dispatch). It is safe only when
            # it identifies exactly the deterministic next case; it does not
            # increase the confirmed lower-bound accounting.
            raise ValueError("cannot reconcile TTS accounting with inferred confirm cases")
    return ScreenResume(
        source_path=source_path,
        rows=completed_rows,
        summary=summary,
        completed_cases=frozenset(groups),
        partial_case_identity=partial_case_identity,
        partial_case_rows_rolled_back=partial_case_rows_rolled_back,
        prior_tts_chars=prior_tts_chars,
        possible_next_case=possible_next_case,
        possible_next_tts_chars=possible_next_tts_chars,
        inferred_possible_cases=inherited_possible_cases,
        rng_state=rng.getstate(),
        artifact_paths={
            "review_manifest": review_manifest,
            "review_audio": review_audio,
            "labels": labels,
        },
        stage=stage,
        possible_next_tts_already_accounted_chars=possible_next_tts_already_accounted_chars,
    )


def _load_screen_resume(path: Path, *, lab_root: Path = Path("var/lab")) -> ScreenResume:
    cards = _stress_cards()
    pairs = [(voice, style) for voice in HINDI_TIMBRE_VOICES for style in STYLES]
    return _load_echo_resume(
        path,
        stage="screen",
        cards=cards,
        pairs=pairs,
        lab_root=lab_root,
    )


def _load_confirm_resume(
    path: Path,
    *,
    pairs: Sequence[tuple[str, str]],
    lab_root: Path = Path("var/lab"),
) -> ScreenResume:
    return _load_echo_resume(
        path,
        stage="confirm",
        cards=_estimate_cards(),
        pairs=pairs,
        lab_root=lab_root,
    )


def _read_screen_pairs(path: Path) -> list[tuple[str, str]]:
    stress_cards = _stress_cards()
    expected_keys = {
        (voice, style, card_id, condition)
        for voice in HINDI_TIMBRE_VOICES
        for style in STYLES
        for card_id in stress_cards
        for condition in CONDITIONS
    }
    seen_keys: set[tuple[str, str, str, str]] = set()
    rates: dict[tuple[str, str], list[bool]] = {}
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                raise ValueError(f"blank row in screen JSONL at line {line_number}")
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed screen JSONL at line {line_number}") from exc
            if type(row) is not dict or set(row) != _SCREEN_ROW_FIELDS:
                raise ValueError(f"screen row at line {line_number} has an invalid schema")

            for field in ("card_id", "voice", "style", "condition", "transcript"):
                if type(row[field]) is not str:
                    raise ValueError(f"screen row {field} must be a string at line {line_number}")
            if row["voice"] not in HINDI_TIMBRE_VOICES:
                raise ValueError(f"unknown screen voice at line {line_number}: {row['voice']}")
            if row["style"] not in STYLES:
                raise ValueError(f"unknown screen style at line {line_number}: {row['style']}")
            if row["card_id"] not in stress_cards:
                raise ValueError(f"unknown stress card id at line {line_number}: {row['card_id']}")
            if row["condition"] not in CONDITIONS:
                raise ValueError(f"unknown screen condition at line {line_number}: {row['condition']}")
            if type(row["passed"]) is not bool:
                raise ValueError(f"screen row passed must be bool at line {line_number}")
            for field in ("expected_paise", "heard_paise"):
                values = row[field]
                if type(values) is not list or any(type(value) is not int for value in values):
                    raise ValueError(f"screen row {field} must be a list of integers at line {line_number}")
            if type(row["tts_ms"]) is not float or not math.isfinite(row["tts_ms"]):
                raise ValueError(f"screen row tts_ms must be a finite float at line {line_number}")

            pair = (row["voice"], row["style"])
            key = (*pair, row["card_id"], row["condition"])
            if key in seen_keys:
                raise ValueError(f"duplicate screen result row at line {line_number}: {key}")
            seen_keys.add(key)
            if row["condition"] == "amr_nb_4750|0":
                rates.setdefault(pair, []).append(row["passed"])

    missing = expected_keys - seen_keys
    if missing:
        voice, style, card_id, condition = sorted(missing)[0]
        raise ValueError(
            "screen JSONL has incomplete coverage; missing "
            f"{voice}/{style}/{card_id}/{condition}"
        )

    summary_path = path.with_name(f"{path.stem}_summary.json")
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read matching screen summary: {summary_path}") from exc
    expected_rows = len(expected_keys)
    if type(summary) is not dict or summary.get("status") != "complete":
        raise ValueError("matching screen summary must report complete status")
    if summary.get("stage") != "screen":
        raise ValueError("matching screen summary must have stage 'screen'")
    if type(summary.get("rows_written")) is not int or summary["rows_written"] != expected_rows:
        raise ValueError(f"matching screen summary must report {expected_rows} rows_written")
    summary_output = summary.get("output")
    if type(summary_output) is not str or Path(summary_output).resolve() != path.resolve():
        raise ValueError("matching screen summary output path does not match the screen JSONL")

    ranked = sorted(
        rates,
        key=lambda pair: (
            -sum(rates[pair]) / len(rates[pair]),
            pair[0],
            pair[1],
        ),
    )
    expected_pairs = len(HINDI_TIMBRE_VOICES) * len(STYLES)
    if len(ranked) != expected_pairs:
        raise ValueError(f"expected {expected_pairs} voice/style pairs in {path}; found {len(ranked)}")
    return ranked[:3]


def _forecast(cards: dict[str, JobCard], pairs: Sequence[tuple[str, str]]) -> dict[str, int | float | str | None]:
    tts_chars = sum(
        len(make_readback(cards[card_id], amount_style=style))
        for card_id in cards
        for _voice, style in pairs
    )
    tts_credits = round(tts_chars * TTS_CREDITS_PER_CHAR, 2)
    return {
        "cards": len(cards),
        "voice_style_pairs": len(pairs),
        "tts_chars": tts_chars,
        "credits": tts_credits,
        "credits_basis": "TTS only at 0.05 credits/character; Prisma STT excluded",
        "prisma_credits_estimate": None,
    }


def _forecast_resume(
    cards: dict[str, JobCard],
    pairs: Sequence[tuple[str, str]],
    resume: ScreenResume,
) -> dict[str, int | float | str | None]:
    remaining = [
        (card_id, card, voice, style)
        for voice, style in pairs
        for card_id, card in cards.items()
        if (card_id, voice, style) not in resume.completed_cases
    ]
    tts_chars = sum(
        len(make_readback(card, amount_style=style))
        for _card_id, card, _voice, style in remaining
    )
    return {
        "cards": len(cards),
        "voice_style_pairs": len(pairs),
        "completed_cases": len(resume.completed_cases),
        "remaining_cases": len(remaining),
        "resumed_rows": len(resume.rows),
        "next_case_tts_chars_already_accounted": resume.possible_next_tts_already_accounted_chars,
        "tts_chars": tts_chars,
        "credits": round(tts_chars * TTS_CREDITS_PER_CHAR, 2),
        "credits_basis": "remaining TTS only at 0.05 credits/character; Prisma STT excluded",
        "prisma_credits_estimate": None,
    }


def _run_artifact_paths(
    output_path: Path,
    run_id: str,
    *,
    labels_path: Path = Path("var/lab/echo_labels.csv"),
) -> dict[str, Path]:
    return {
        "output": output_path,
        "summary": output_path.with_name(f"{output_path.stem}_summary.json"),
        "review_manifest": output_path.with_name(f"{output_path.stem}_review_{run_id}.jsonl"),
        "review_audio": output_path.with_name(f"{output_path.stem}_review_{run_id}"),
        "labels": labels_path,
    }


def _preflight_run_artifacts(paths: dict[str, Path], *, lab_root: Path = Path("var/lab")) -> None:
    lab_root = lab_root.resolve()
    resolved_paths: dict[str, Path] = {}
    for name, path in paths.items():
        resolved = path.resolve()
        try:
            resolved.relative_to(lab_root)
        except ValueError as exc:
            raise ValueError(f"{name} artifact must stay under var/lab: {path}") from exc
        resolved_paths[name] = resolved

    names = list(resolved_paths)
    for index, left_name in enumerate(names):
        left = resolved_paths[left_name]
        for right_name in names[index + 1 :]:
            right = resolved_paths[right_name]
            if left == right or left in right.parents or right in left.parents:
                raise ValueError(
                    "artifact path collision after resolution: "
                    f"{left_name}={left} and {right_name}={right}"
                )

    for name, path in resolved_paths.items():
        if name != "labels" and path.exists():
            raise FileExistsError(f"refusing to overwrite existing {name} artifact: {path}")
    ensure_label_template(resolved_paths["labels"])


def _preflight_resume_artifacts(
    paths: dict[str, Path],
    resume: ScreenResume,
    *,
    lab_root: Path = Path("var/lab"),
) -> None:
    """Validate merged output paths before opening any source or review artifact."""
    required = {"output", "summary", "review_manifest", "review_audio", "labels"}
    if set(paths) != required:
        raise ValueError("resume artifact paths have an invalid schema")
    lab_root = lab_root.resolve()
    resolved_paths: dict[str, Path] = {}
    for name, path in paths.items():
        resolved = path.resolve()
        try:
            resolved.relative_to(lab_root)
        except ValueError as exc:
            raise ValueError(f"{name} artifact must stay under var/lab: {path}") from exc
        resolved_paths[name] = resolved

    for name in ("review_manifest", "review_audio", "labels"):
        expected = resume.artifact_paths[name].resolve()
        if resolved_paths[name] != expected:
            raise ValueError(f"resume {name} must reuse the validated source artifact")

    source_summary = resume.source_path.with_name(f"{resume.source_path.stem}_summary.json").resolve()
    protected = {
        "resume input": resume.source_path.resolve(),
        "resume summary": source_summary,
        **resolved_paths,
    }
    entries = list(protected.items())
    for index, (left_name, left) in enumerate(entries):
        for right_name, right in entries[index + 1 :]:
            if left == right or left in right.parents or right in left.parents:
                raise ValueError(
                    "resume artifact path collision after resolution: "
                    f"{left_name}={left} and {right_name}={right}"
                )

    for name in ("output", "summary"):
        path = resolved_paths[name]
        if path.exists():
            raise FileExistsError(f"refusing to overwrite existing {name} artifact: {path}")
    for name, kind in (("review_manifest", "file"), ("review_audio", "directory"), ("labels", "file")):
        path = resolved_paths[name]
        exists = path.is_dir() if kind == "directory" else path.is_file()
        if not exists:
            raise FileNotFoundError(f"resume {name} artifact does not exist: {path}")


def _new_run_id() -> str:
    started = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{started}-{uuid4().hex[:8]}"


def _run_live(
    cards: dict[str, JobCard],
    pairs: Sequence[tuple[str, str]],
    output_path: Path,
    request_interval_seconds: float,
    forecast: dict[str, int | float | str | None],
    *,
    stage: str,
    run_id: str,
    artifact_paths: dict[str, Path],
    resume: ScreenResume | None = None,
) -> list[EchoRow]:
    if resume is not None and resume.stage != stage:
        raise ValueError("resume artifact stage does not match the requested run stage")
    if resume is not None and request_interval_seconds != float(resume.summary["request_interval_seconds"]):
        raise ValueError("resume request interval must match the interrupted run interval")
    settings = Settings.load()
    settings.require_gnani()
    noise8k = normalize_upload(
        DEFAULT_TELEPHONY_NOISE_PATH.read_bytes(),
        "audio/wav",
        sample_rate=8000,
    )

    timbre_clients: dict[str, TimbreClient] = {}
    prisma = PrismaClient(settings.api_key, base_url=settings.gnani_base_url)
    prior_summary = resume.summary if resume is not None else {}
    prior_tts_chars = resume.prior_tts_chars if resume is not None else 0
    new_tts_chars = 0
    new_tts_case_identities: set[tuple[str, str, str, str]] = set()
    stt_audio_seconds = float(prior_summary.get("stt_audio_seconds", 0.0))
    stt_requests = int(prior_summary.get("stt_requests_attempted", 0))
    rows_written = len(resume.rows) if resume is not None else 0
    completed = False
    rows: list[EchoRow] = list(resume.rows) if resume is not None else []
    review_writer: EchoReviewWriter | None = None
    partial_replay_started = False
    partial_replay_completed = False
    partial_replay_history = [
        dict(record) for record in prior_summary.get(_PARTIAL_REPLAY_HISTORY_FIELD, [])
    ]
    possible_tts_post_attempts = [
        dict(attempt) for attempt in prior_summary.get(_POSSIBLE_TTS_POST_ATTEMPTS_FIELD, [])
    ]
    next_tts_post_attempt_number = len(possible_tts_post_attempts) + 1
    active_tts_attempt: dict[str, Any] | None = None

    def note_tts_attempt(card_id: str, voice: str, style: str, characters: int) -> None:
        nonlocal active_tts_attempt
        active_tts_attempt = {
            "card_id": card_id,
            "voice": voice,
            "style": style,
            "characters": characters,
        }

    def synthesize(text: str, voice: str) -> tuple[bytes, float]:
        nonlocal new_tts_chars, next_tts_post_attempt_number, active_tts_attempt
        context = active_tts_attempt
        if (
            context is None
            or context["voice"] != voice
            or context["characters"] != len(text)
        ):
            raise RuntimeError("TTS attempt context does not match the active echo case")
        client = timbre_clients.get(voice)
        if client is None:
            client = TimbreClient(settings.api_key, voice=voice, base_url=settings.gnani_base_url)
            timbre_clients[voice] = client
        started = time.perf_counter()
        try:
            mulaw_audio = _retry_connect_errors(lambda: client.synthesize(text))
        except Exception as exc:
            if _may_have_reached_timbre_post(exc):
                possible_tts_post_attempts.append({
                    "attempt_number": next_tts_post_attempt_number,
                    **context,
                    "error_type": type(exc).__name__,
                })
                next_tts_post_attempt_number += 1
            raise
        finally:
            active_tts_attempt = None
        new_tts_chars += len(text)
        new_tts_case_identities.add(
            (context["card_id"], context["voice"], context["style"], run_id)
        )
        tts_ms = round((time.perf_counter() - started) * 1000.0, 2)
        return mulaw_to_wav(mulaw_audio), tts_ms

    def degrade(wav: bytes, condition: str) -> bytes:
        codec, level = condition.split("|", maxsplit=1)
        processed = wav
        if level != "clean":
            processed, _measured_snr = mix_at_snr(processed, noise8k, float(level))
        return codec_round_trip(processed, codec)

    def transcribe(wav: bytes) -> str:
        nonlocal stt_audio_seconds, stt_requests
        audio_seconds = _measure_wav_duration_seconds(wav)

        def count_attempt() -> None:
            nonlocal stt_audio_seconds, stt_requests
            stt_audio_seconds += audio_seconds
            stt_requests += 1

        return _transcribe_with_spacing(
            prisma,
            wav,
            request_interval_seconds,
            on_attempt=count_attempt,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    review_writer = EchoReviewWriter(
        artifact_paths["review_audio"],
        artifact_paths["review_manifest"],
        artifact_paths["labels"],
        run_id=run_id,
        stage=stage,
        seed=prior_summary.get("review_sampling_seed", REVIEW_SAMPLE_SEED),
        pass_fraction=prior_summary.get("review_pass_sample_fraction", PASS_SAMPLE_FRACTION),
        resume=resume is not None,
        rng_state=resume.rng_state if resume is not None else None,
    )
    try:
        with output_path.open("x", encoding="utf-8", newline="\n") as stream:
            if resume is not None:
                for row in resume.rows:
                    stream.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")
                stream.flush()

            def record(row: EchoRow) -> None:
                nonlocal rows_written
                stream.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")
                stream.flush()
                rows.append(row)
                rows_written += 1
                assert review_writer is not None
                review_writer.record_row(row)

            def begin_review_case(card_id, voice, style, audios):
                nonlocal partial_replay_started
                assert review_writer is not None
                review_writer.begin_case(card_id, voice, style, audios)
                if resume is not None and resume.partial_case_identity == (card_id, voice, style):
                    partial_replay_started = True

            def finish_review_case(case_rows, audios):
                nonlocal partial_replay_completed
                assert review_writer is not None
                review_writer.finish_case(case_rows, audios)
                if (
                    resume is not None
                    and resume.partial_case_identity is not None
                    and (case_rows[0].card_id, case_rows[0].voice, case_rows[0].style)
                    == resume.partial_case_identity
                ):
                    partial_replay_completed = True

            for voice, style in pairs:
                pending_cards = {
                    card_id: card
                    for card_id, card in cards.items()
                    if resume is None or (card_id, voice, style) not in resume.completed_cases
                }
                if not pending_cards:
                    continue
                run_echo(
                    pending_cards,
                    [voice],
                    [style],
                    CONDITIONS,
                    synthesize=synthesize,
                    degrade=degrade,
                    transcribe=transcribe,
                    on_row=record,
                    on_case=finish_review_case,
                    on_case_audio=begin_review_case,
                    on_tts_attempt=note_tts_attempt,
                )
        completed = True
        return rows
    finally:
        try:
            if review_writer is not None:
                review_writer.close()
        finally:
            try:
                for client in timbre_clients.values():
                    client.http.close()
                prisma.http.close()
            finally:
                inferred_possible_cases = [
                    item
                    for item in (resume.inferred_possible_cases if resume is not None else ())
                    if (
                        item["card_id"], item["voice"], item["style"], item["run_id"]
                    ) not in new_tts_case_identities
                ]
                if not completed:
                    prior_completed = resume.completed_cases if resume is not None else set()
                    newly_completed = _completed_cases(rows) - set(prior_completed)
                    completed_tts_chars = sum(
                        len(make_readback(cards[card_id], amount_style=style))
                        for card_id, _voice, style in newly_completed
                    )
                    if new_tts_chars > completed_tts_chars:
                        possible_case = _first_incomplete_case(rows, cards, pairs)
                        if (
                            possible_case is not None
                            and (*possible_case, run_id) not in new_tts_case_identities
                        ):
                            inferred_possible_cases.append(
                                _inferred_case_record(possible_case, cards, run_id)
                            )
                summary = {
                    "output": str(output_path),
                    "status": "complete" if completed else "interrupted",
                    "rows_written": rows_written,
                    "request_interval_seconds": request_interval_seconds,
                    "stt_requests_attempted": stt_requests,
                    "stt_audio_seconds": round(stt_audio_seconds, 3),
                    "prisma_credits_estimated": round(stt_audio_seconds * 0.2, 2),
                    "prisma_credits_per_audio_second": 0.2,
                    "tts_chars_reconstructed_prior_lower_bound": prior_tts_chars,
                    "tts_chars_generated_new": new_tts_chars,
                    "tts_chars_accounted_lower_bound": prior_tts_chars + new_tts_chars,
                    "tts_chars_inferred_possible_unpersisted_cases": inferred_possible_cases,
                    "tts_chars_pending_work_forecast": forecast["tts_chars"],
                    "tts_chars_remaining_forecast": forecast["tts_chars"],
                    "tts_chars_completed_stage_forecast": prior_tts_chars + forecast["tts_chars"],
                    "tts_credits_accounted_lower_bound_estimate": round(
                        (prior_tts_chars + new_tts_chars) * TTS_CREDITS_PER_CHAR,
                        2,
                    ),
                    "tts_credits_completed_stage_forecast": round(
                        (prior_tts_chars + forecast["tts_chars"]) * TTS_CREDITS_PER_CHAR,
                        2,
                    ),
                    "tts_credits_per_character": TTS_CREDITS_PER_CHAR,
                    "run_id": run_id,
                    "stage": stage,
                    "review_manifest": str(artifact_paths["review_manifest"]),
                    "review_audio_root": str(artifact_paths["review_audio"]),
                    "labels_csv": str(artifact_paths["labels"]),
                    "review_sampling_seed": prior_summary.get("review_sampling_seed", REVIEW_SAMPLE_SEED),
                    "review_pass_sample_fraction": prior_summary.get(
                        "review_pass_sample_fraction",
                        PASS_SAMPLE_FRACTION,
                    ),
                    "review_selected_cases": prior_summary.get("review_selected_cases", 0)
                    + (review_writer.selected_cases if review_writer else 0),
                    "review_selected_failure_rows": prior_summary.get("review_selected_failure_rows", 0)
                    + (review_writer.selected_failure_rows if review_writer else 0),
                    "review_selected_pass_rows": prior_summary.get("review_selected_pass_rows", 0)
                    + (review_writer.selected_pass_rows if review_writer else 0),
                }
                if resume is not None and resume.partial_case_identity is not None:
                    card_id, voice, style = resume.partial_case_identity
                    partial_replay_history.append({
                        "card_id": card_id,
                        "voice": voice,
                        "style": style,
                        "rows_rolled_back": resume.partial_case_rows_rolled_back,
                        "replay_started": partial_replay_started,
                        "replay_completed": partial_replay_completed,
                    })
                if partial_replay_history:
                    summary[_PARTIAL_REPLAY_HISTORY_FIELD] = partial_replay_history
                if (
                    possible_tts_post_attempts
                    or _POSSIBLE_TTS_POST_ATTEMPTS_FIELD in prior_summary
                ):
                    summary[_POSSIBLE_TTS_POST_ATTEMPTS_FIELD] = possible_tts_post_attempts
                with artifact_paths["summary"].open("x", encoding="utf-8") as stream:
                    stream.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("screen", "confirm"), default="screen")
    parser.add_argument("--from", dest="from_path", type=Path, help="screen JSONL used to select confirm pairs")
    parser.add_argument(
        "--resume-from",
        type=Path,
        help="interrupted screen or confirm JSONL to resume into a new output",
    )
    parser.add_argument("--live", action="store_true", help="make paid Timbre and Prisma calls")
    parser.add_argument("--output", type=Path, help="JSONL output path (default: var/lab/echo_{stage}.jsonl)")
    parser.add_argument("--request-interval-seconds", type=float, default=1.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not math.isfinite(args.request_interval_seconds) or args.request_interval_seconds < 0:
        parser.error("--request-interval-seconds must be finite and non-negative")

    resume: ScreenResume | None = None
    if args.resume_from is not None:
        if args.stage == "screen" and args.from_path is not None:
            parser.error("--from cannot be used with screen --resume-from")
        if args.stage == "confirm" and args.from_path is None:
            parser.error("--from is required with confirm --resume-from to validate the selected pairs")
        if args.live and args.output is None:
            parser.error("--output is required with --live --resume-from so the source remains unchanged")
        try:
            if args.stage == "screen":
                resume = _load_screen_resume(args.resume_from)
                cards = _stress_cards()
                pairs = [(voice, style) for voice in HINDI_TIMBRE_VOICES for style in STYLES]
            else:
                screen_path = args.from_path.resolve()
                lab_root = Path("var/lab").resolve()
                try:
                    screen_path.relative_to(lab_root)
                except ValueError as exc:
                    raise ValueError("confirm resume --from screen input must stay beneath var/lab") from exc
                if not screen_path.is_file():
                    raise ValueError(f"confirm resume --from screen input does not exist: {screen_path}")
                cards = _estimate_cards()
                pairs = _read_screen_pairs(screen_path)
                resume = _load_confirm_resume(args.resume_from, pairs=pairs)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        if args.live and args.request_interval_seconds != float(resume.summary["request_interval_seconds"]):
            parser.error("resume request interval must match interrupted run interval")
        forecast = _forecast_resume(cards, pairs, resume)
    elif args.stage == "screen":
        cards = _stress_cards()
        pairs = [(voice, style) for voice in HINDI_TIMBRE_VOICES for style in STYLES]
        forecast = _forecast(cards, pairs)
    else:
        if args.from_path is None:
            parser.error("--from is required for the confirm stage")
        cards = _estimate_cards()
        pairs = _read_screen_pairs(args.from_path)
        forecast = _forecast(cards, pairs)

    print(json.dumps(forecast, ensure_ascii=False, indent=2))
    if not args.live:
        return 0

    output_path = args.output or Path(f"var/lab/echo_{args.stage}.jsonl")
    run_id = resume.summary["run_id"] if resume is not None else _new_run_id()
    artifact_paths = _run_artifact_paths(
        output_path,
        run_id,
        labels_path=resume.artifact_paths["labels"] if resume is not None else Path("var/lab/echo_labels.csv"),
    )
    if resume is not None:
        artifact_paths.update(resume.artifact_paths)
        try:
            _preflight_resume_artifacts(artifact_paths, resume)
        except (FileExistsError, FileNotFoundError, ValueError) as exc:
            parser.error(str(exc))
    else:
        try:
            _preflight_run_artifacts(artifact_paths)
        except (FileExistsError, ValueError) as exc:
            parser.error(str(exc))
    rows = _run_live(
        cards,
        pairs,
        output_path,
        args.request_interval_seconds,
        forecast,
        stage=args.stage,
        run_id=run_id,
        artifact_paths=artifact_paths,
        resume=resume,
    )
    print(f"Echo run complete. Recorded {len(rows)} rows in {output_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
