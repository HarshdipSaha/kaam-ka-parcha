from dataclasses import dataclass, replace
from datetime import datetime
from threading import RLock
from typing import Literal
import hashlib
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
    dpdp_consent_granted: bool = False
    dpdp_consent_at_utc: datetime | None = None
    dpdp_user_agent: str | None = None
    dpdp_consent_sha256: str | None = None


class SessionStore:
    def __init__(self, max_untouched: int = 500):
        self._lock = RLock()
        self._items: dict[str, Session] = {}
        self._max_untouched = max_untouched

    def create(self) -> Session:
        with self._lock:
            session = Session(id=secrets.token_urlsafe(18))
            self._items[session.id] = session
            self._evict_untouched()
            return session

    def _evict_untouched(self) -> None:
        """Bound memory from page loads and crawlers: drop the oldest sessions that never got a card."""
        untouched = [sid for sid, s in self._items.items() if s.card is None and s.status == "draft"]
        for sid in untouched[: max(0, len(untouched) - self._max_untouched)]:
            del self._items[sid]

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

    def record_dpdp_consent(
        self,
        session_id: str,
        *,
        expected_revision: int,
        when: datetime,
        user_agent: str | None = None,
        granted: bool = True,
    ) -> Session:
        with self._lock:
            current = self._editable(session_id, expected_revision)
            raw = f"DPDP_2023:{session_id}:{when.isoformat()}:{user_agent or ''}:{granted}"
            consent_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            log = TranscriptLog(
                role="customer",
                mode="dpdp_consent",
                text=f"DPDP Act 2023 statutory consent {'granted' if granted else 'withheld'} at {when.isoformat()} (User-Agent: {user_agent or 'unknown'})",
                recorded_at_utc=when,
            )
            updated = replace(
                current,
                dpdp_consent_granted=granted,
                dpdp_consent_at_utc=when if granted else None,
                dpdp_user_agent=user_agent,
                dpdp_consent_sha256=consent_hash if granted else None,
                logs=current.logs + (log,),
            )
            self._items[session_id] = updated
            return updated
