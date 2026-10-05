from dataclasses import dataclass, replace
from datetime import datetime
from threading import RLock
from typing import Literal
import secrets
from .schema import JobCard, TranscriptLog


class Conflict(RuntimeError):
    pass


@dataclass(frozen=True)
class Session:
    id: str
    revision: int = 0
    status: Literal["draft", "review", "awaiting_reply", "fallback_ready", "confirmed"] = "draft"
    card: JobCard | None = None
    logs: tuple[TranscriptLog, ...] = ()
    readback_revision: int | None = None
    confirmed_at_utc: datetime | None = None


class SessionStore:
    def __init__(self):
        self._lock = RLock()
        self._items: dict[str, Session] = {}

    def create(self) -> Session:
        with self._lock:
            session = Session(id=secrets.token_urlsafe(18))
            self._items[session.id] = session
            return session

    def get(self, session_id: str) -> Session:
        with self._lock:
            return self._items[session_id]

    def _editable(self, session_id: str, expected_revision: int) -> Session:
        current = self._items[session_id]
        if current.status == "confirmed":
            raise Conflict("confirmed session is immutable")
        if current.revision != expected_revision:
            raise Conflict("stale revision")
        return current

    def set_card(
        self,
        session_id: str,
        *,
        expected_revision: int,
        card: JobCard,
        logs: tuple[TranscriptLog, ...] = (),
    ) -> Session:
        with self._lock:
            current = self._editable(session_id, expected_revision)
            card = JobCard.model_validate(card.model_dump())  # copy into canonical frozen/tuple types
            updated = replace(
                current,
                revision=current.revision + 1,
                status="review",
                card=card,
                readback_revision=None,
                logs=current.logs + tuple(logs),
            )
            self._items[session_id] = updated
            return updated

    def start_readback(
        self, session_id: str, *, expected_revision: int, log: TranscriptLog | None = None
    ) -> Session:
        with self._lock:
            current = self._editable(session_id, expected_revision)
            if current.card is None or current.card.needs_review:
                raise Conflict("card needs review")
            updated = replace(
                current,
                status="awaiting_reply",
                readback_revision=current.revision,
                logs=current.logs + ((log,) if log else ()),
            )
            self._items[session_id] = updated
            return updated

    def trigger_fallback(
        self,
        session_id: str,
        *,
        expected_revision: int,
        log: TranscriptLog | None = None,
    ) -> Session:
        with self._lock:
            current = self._editable(session_id, expected_revision)
            if current.status not in ("awaiting_reply", "fallback_ready"):
                raise Conflict("session not in reply state")
            updated = replace(
                current,
                status="fallback_ready",
                logs=current.logs + ((log,) if log else ()),
            )
            self._items[session_id] = updated
            return updated

    def request_changes(
        self,
        session_id: str,
        *,
        expected_revision: int,
        log: TranscriptLog | None = None,
    ) -> Session:
        with self._lock:
            current = self._editable(session_id, expected_revision)
            if current.status not in ("awaiting_reply", "fallback_ready"):
                raise Conflict("session not in reply or fallback state")
            updated = replace(
                current,
                status="review",
                readback_revision=None,
                logs=current.logs + ((log,) if log else ()),
            )
            self._items[session_id] = updated
            return updated

    def confirm(
        self,
        session_id: str,
        *,
        expected_revision: int,
        when: datetime,
        log: TranscriptLog | None = None,
    ) -> Session:
        with self._lock:
            current = self._editable(session_id, expected_revision)
            if current.status not in ("awaiting_reply", "fallback_ready") or current.readback_revision != current.revision:
                raise Conflict("stale read-back")
            updated = replace(
                current,
                status="confirmed",
                confirmed_at_utc=when,
                logs=current.logs + ((log,) if log else ()),
            )
            self._items[session_id] = updated
            return updated

    def record_observation(
        self,
        session_id: str,
        *,
        expected_revision: int,
        readback_revision: int,
        log: TranscriptLog,
    ) -> Session:
        with self._lock:
            current = self._editable(session_id, expected_revision)
            if current.status != "awaiting_reply" or current.readback_revision != readback_revision:
                raise Conflict("stale reply")
            updated = replace(current, logs=current.logs + (log,))
            self._items[session_id] = updated
            return updated
