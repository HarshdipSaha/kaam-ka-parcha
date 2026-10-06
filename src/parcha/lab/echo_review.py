"""Deterministic row sampling and human-label artifacts for echo runs."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import re
from random import Random
from typing import Literal, Mapping, Sequence

from parcha.lab.amount_bench import HINDI_TIMBRE_VOICES
from parcha.lab.echo import EchoRow

REVIEW_CONDITIONS = ("control", "g711|clean", "amr_nb_4750|0")
REVIEW_SAMPLE_SEED = 20261006
PASS_SAMPLE_FRACTION = 0.10
REVIEW_STYLES = ("digits", "words")
_SAFE_CARD_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
ReviewSelection = Literal["failure", "pass_sample"]

LABEL_FIELDS = (
    "run_id",
    "stage",
    "case_id",
    "card_id",
    "voice",
    "style",
    "selection",
    "condition",
    "passed",
    "expected_paise",
    "heard_paise",
    "transcript",
    "audio_path",
    "label",
    "allowed_labels",
)


def _validate_case(rows: Sequence[EchoRow], *, complete: bool = False) -> None:
    conditions = tuple(row.condition for row in rows)
    if not conditions or len(set(conditions)) != len(conditions):
        raise ValueError("review case must contain unique condition rows")
    if any(condition not in REVIEW_CONDITIONS for condition in conditions):
        raise ValueError(f"unsupported review condition in {conditions}")
    if tuple(condition for condition in REVIEW_CONDITIONS if condition in conditions) != conditions:
        raise ValueError("review condition rows must preserve condition order")
    if complete and conditions != REVIEW_CONDITIONS:
        raise ValueError(f"review cases must contain conditions in order: {REVIEW_CONDITIONS}")
    identity = {(row.card_id, row.voice, row.style) for row in rows}
    if len(identity) != 1:
        raise ValueError("review case rows must share card_id, voice, and style")
    card_id, voice, style = next(iter(identity))
    _validate_case_identity(card_id, voice, style)


def _validate_case_identity(card_id: str, voice: str, style: str) -> None:
    if (
        type(card_id) is not str
        or _SAFE_CARD_ID.fullmatch(card_id) is None
        or type(voice) is not str
        or voice not in HINDI_TIMBRE_VOICES
        or type(style) is not str
        or style not in REVIEW_STYLES
    ):
        raise ValueError("invalid review case identity")


def review_case_id(rows: Sequence[EchoRow]) -> str:
    _validate_case(rows)
    row = rows[0]
    return f"{row.card_id}_{row.voice}_{row.style}"


def select_row_for_review(
    row: EchoRow,
    rng: Random,
    *,
    pass_fraction: float = PASS_SAMPLE_FRACTION,
) -> ReviewSelection | None:
    """Select every failed row and a seeded Bernoulli sample of passing rows."""
    if not math.isfinite(pass_fraction) or not 0.0 <= pass_fraction <= 1.0:
        raise ValueError("pass_fraction must be finite and between 0 and 1")
    if not row.passed:
        return "failure"
    return "pass_sample" if rng.random() < pass_fraction else None


def build_review_manifest_entry(
    rows: Sequence[EchoRow],
    audio_paths: Mapping[str, str],
    *,
    selections: Sequence[ReviewSelection | None],
    seed: int,
    run_id: str,
    stage: str,
    pass_fraction: float = PASS_SAMPLE_FRACTION,
) -> dict:
    """Build a case snapshot linking each completed condition to all case WAVs."""
    _validate_case(rows)
    if not math.isfinite(pass_fraction) or not 0.0 <= pass_fraction <= 1.0:
        raise ValueError("pass_fraction must be finite and between 0 and 1")
    if len(rows) != len(selections):
        raise ValueError("one review selection is required for each result row")
    if set(audio_paths) != set(REVIEW_CONDITIONS):
        raise ValueError("review manifest requires an audio path for each echo condition")
    first = rows[0]
    case_id = review_case_id(rows)
    return {
        "event": "case_snapshot",
        "status": "complete" if tuple(row.condition for row in rows) == REVIEW_CONDITIONS else "in_progress",
        "run_id": run_id,
        "stage": stage,
        "case_id": case_id,
        "card_id": first.card_id,
        "voice": first.voice,
        "style": first.style,
        "sampling_seed": seed,
        "pass_sample_fraction": pass_fraction,
        "audio_paths": dict(audio_paths),
        "conditions": [
            {
                "condition": row.condition,
                "passed": row.passed,
                "selected": selection is not None,
                "selection": selection,
                "expected_paise": list(row.expected_paise),
                "heard_paise": list(row.heard_paise),
                "transcript": row.transcript,
                "audio_path": audio_paths[row.condition],
            }
            for row, selection in zip(rows, selections, strict=True)
        ],
    }


def build_review_label_rows(entry: Mapping) -> list[dict[str, str]]:
    """Return only selected result rows, leaving failure causes for a human."""
    case_fields = {
        "run_id": str(entry["run_id"]),
        "stage": str(entry["stage"]),
        "case_id": str(entry["case_id"]),
        "card_id": str(entry["card_id"]),
        "voice": str(entry["voice"]),
        "style": str(entry["style"]),
    }
    result: list[dict[str, str]] = []
    for condition in entry["conditions"]:
        selection = condition["selection"]
        if selection is None:
            continue
        passed = bool(condition["passed"])
        row = {
            **case_fields,
            "selection": str(selection),
            "condition": str(condition["condition"]),
            "passed": str(passed).lower(),
            "expected_paise": ",".join(str(value) for value in condition["expected_paise"]),
            "heard_paise": ",".join(str(value) for value in condition["heard_paise"]),
            "transcript": str(condition["transcript"]),
            "audio_path": str(condition["audio_path"]),
            "label": "pass" if passed else "",
            "allowed_labels": "pass" if passed else "timbre,line,prisma",
        }
        result.append(row)
    return result


def ensure_label_template(path: Path) -> bool:
    """Create the CSV header once; validate an existing file without replacing it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            header = next(csv.reader(stream), None)
        if tuple(header or ()) != LABEL_FIELDS:
            raise ValueError(f"unexpected echo label CSV header in {path}")
        return False

    try:
        with path.open("x", encoding="utf-8-sig", newline="") as stream:
            csv.DictWriter(stream, fieldnames=LABEL_FIELDS).writeheader()
    except FileExistsError:
        return ensure_label_template(path)
    return True


def append_label_rows(path: Path, rows: Sequence[Mapping[str, str]]) -> None:
    """Append selected result rows without replacing prior labels."""
    ensure_label_template(path)
    with path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=LABEL_FIELDS, extrasaction="raise")
        for row in rows:
            writer.writerow(row)
        stream.flush()


class EchoReviewWriter:
    """Retain all case WAVs when any result row is selected for review."""

    def __init__(
        self,
        audio_root: Path,
        manifest_path: Path,
        labels_path: Path,
        *,
        run_id: str,
        stage: str,
        seed: int = REVIEW_SAMPLE_SEED,
        pass_fraction: float = PASS_SAMPLE_FRACTION,
        resume: bool = False,
        rng_state: object | None = None,
    ):
        if not math.isfinite(pass_fraction) or not 0.0 <= pass_fraction <= 1.0:
            raise ValueError("pass_fraction must be finite and between 0 and 1")
        if resume:
            if not audio_root.is_dir():
                raise FileNotFoundError(f"resume review audio directory does not exist: {audio_root}")
            if not manifest_path.is_file():
                raise FileNotFoundError(f"resume review manifest does not exist: {manifest_path}")
            if not labels_path.is_file():
                raise FileNotFoundError(f"resume labels CSV does not exist: {labels_path}")
            ensure_label_template(labels_path)
        else:
            if audio_root.exists():
                raise FileExistsError(f"refusing to reuse review audio directory: {audio_root}")
            if manifest_path.exists():
                raise FileExistsError(f"refusing to overwrite review manifest: {manifest_path}")
            ensure_label_template(labels_path)
            audio_root.mkdir(parents=True, exist_ok=False)
        self.audio_root = audio_root
        self.run_id = run_id
        self.stage = stage
        self.seed = seed
        self.rng = Random(seed)
        if rng_state is not None:
            self.rng.setstate(rng_state)
        self.pass_fraction = pass_fraction
        self.manifest_stream = manifest_path.open("a" if resume else "x", encoding="utf-8", newline="\n")
        self.selected_failure_rows = 0
        self.selected_pass_rows = 0
        self.selected_cases = 0
        self._labels_path = labels_path
        self._active_identity: tuple[str, str, str] | None = None
        self._active_case_dir: Path | None = None
        self._active_audio: Mapping[str, bytes] = {}
        self._active_rows: list[EchoRow] = []
        self._active_selections: list[ReviewSelection | None] = []
        self._active_paths: dict[str, str] = {}
        self._closed = False

    def begin_case(
        self,
        card_id: str,
        voice: str,
        style: str,
        audio: Mapping[str, bytes],
    ) -> None:
        if self._active_identity is not None:
            raise RuntimeError("previous review case has not finished")
        _validate_case_identity(card_id, voice, style)
        if set(audio) != set(REVIEW_CONDITIONS):
            raise ValueError("review case audio must include all three conditions")
        case_dir = self._resolve_case_dir(card_id, voice, style)
        self._active_identity = (card_id, voice, style)
        self._active_case_dir = case_dir
        self._active_audio = dict(audio)
        self._active_rows = []
        self._active_selections = []
        self._active_paths = {}

    def record_row(self, row: EchoRow) -> None:
        if self._active_identity != (row.card_id, row.voice, row.style):
            raise RuntimeError("echo row does not belong to the active review case")
        selection = select_row_for_review(row, self.rng, pass_fraction=self.pass_fraction)
        self._active_rows.append(row)
        self._active_selections.append(selection)

        if selection is not None:
            if not self._active_paths:
                self._persist_audio()
                self.selected_cases += 1
                self._write_manifest_rows(
                    self._active_rows,
                    self._active_selections,
                    event="selection",
                    status="in_progress",
                )
                self._write_labels(self._active_rows, self._active_selections)
            else:
                self._write_manifest_rows([row], [selection], event="result")
                self._write_labels([row], [selection])
            if selection == "failure":
                self.selected_failure_rows += 1
            else:
                self.selected_pass_rows += 1
        elif self._active_paths:
            self._write_manifest_rows([row], [None], event="result")

    def finish_case(self, rows: Sequence[EchoRow], audio: Mapping[str, bytes]) -> None:
        if self._active_identity is None:
            raise RuntimeError("no active review case")
        if list(rows) != self._active_rows or dict(audio) != dict(self._active_audio):
            raise ValueError("completed case does not match the active rows and audio")
        if self._active_paths:
            self._write_event({
                "event": "case_complete",
                "run_id": self.run_id,
                "stage": self.stage,
                "case_id": self._case_id(),
            })
        self._clear_active()

    def close(self) -> None:
        if self._closed:
            return
        try:
            if self._active_identity is not None and self._active_paths:
                self._write_event({
                    "event": "case_interrupted",
                    "run_id": self.run_id,
                    "stage": self.stage,
                    "case_id": self._case_id(),
                    "completed_conditions": [row.condition for row in self._active_rows],
                    "audio_paths": self._active_paths,
                })
        finally:
            self.manifest_stream.close()
            self._closed = True

    def _case_id(self) -> str:
        assert self._active_identity is not None
        card_id, voice, style = self._active_identity
        return f"{card_id}_{voice}_{style}"

    def _persist_audio(self) -> None:
        if self._active_identity is None or self._active_case_dir is None:
            raise RuntimeError("no active review case")
        card_id, voice, style = self._active_identity
        case_dir = self._resolve_case_dir(card_id, voice, style)
        if case_dir != self._active_case_dir:
            raise ValueError("review case directory changed after validation")
        case_dir.mkdir(exist_ok=False)
        paths: dict[str, str] = {}
        for condition in REVIEW_CONDITIONS:
            filename = condition.replace("|", "_").replace(".", "_") + ".wav"
            path = case_dir / filename
            with path.open("xb") as stream:
                stream.write(self._active_audio[condition])
            paths[condition] = path.as_posix()
        self._active_paths = paths

    def _write_manifest_rows(
        self,
        rows: Sequence[EchoRow],
        selections: Sequence[ReviewSelection | None],
        *,
        event: str,
        status: str | None = None,
    ) -> None:
        entry = build_review_manifest_entry(
            rows,
            self._active_paths,
            selections=selections,
            seed=self.seed,
            pass_fraction=self.pass_fraction,
            run_id=self.run_id,
            stage=self.stage,
        )
        entry["event"] = event
        if status is not None:
            entry["status"] = status
        self._write_event(entry)

    def _write_labels(
        self,
        rows: Sequence[EchoRow],
        selections: Sequence[ReviewSelection | None],
    ) -> None:
        entry = build_review_manifest_entry(
            rows,
            self._active_paths,
            selections=selections,
            seed=self.seed,
            pass_fraction=self.pass_fraction,
            run_id=self.run_id,
            stage=self.stage,
        )
        append_label_rows(self._labels_path, build_review_label_rows(entry))

    def _write_event(self, entry: Mapping) -> None:
        self.manifest_stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.manifest_stream.flush()

    def _clear_active(self) -> None:
        self._active_identity = None
        self._active_case_dir = None
        self._active_audio = {}
        self._active_rows = []
        self._active_selections = []
        self._active_paths = {}

    def _resolve_case_dir(self, card_id: str, voice: str, style: str) -> Path:
        _validate_case_identity(card_id, voice, style)
        root = self.audio_root.resolve()
        case_dir = (root / f"{card_id}_{voice}_{style}").resolve()
        try:
            case_dir.relative_to(root)
        except ValueError as exc:
            raise ValueError("review case directory must stay beneath the review audio root") from exc
        return case_dir
