from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import inspect
import re

from .audio import normalize_upload
from .extract import Extractor
from .gnani import PrismaClient
from .schema import JobCard, TranscriptLog
from .session import Session, SessionStore

REASK_FIELD_PATTERN = re.compile(r"^items\.[a-z]+-[0-9]+\.(label|amount_paise)$")


class Workflow:
    def __init__(
        self,
        store: SessionStore,
        prisma: PrismaClient,
        extractor: Extractor,
        normalize_audio: Callable[[bytes, str], bytes] | None = None,
        bias_words: tuple[str, ...] = ("brake", "clutch", "Honda"),
        use_bias: bool = False,
    ):
        self.store = store
        self.prisma = prisma
        self.extractor = extractor
        self.normalize_audio = normalize_audio if normalize_audio is not None else normalize_upload
        self.bias_words = bias_words
        self.use_bias = use_bias

    def intake(
        self,
        session_id: str,
        blob: bytes,
        mime: str,
        *,
        expected_revision: int,
        recorded_at_utc: datetime | None = None,
    ) -> Session:
        recorded_at_utc = recorded_at_utc or datetime.now(timezone.utc)
        if recorded_at_utc.tzinfo is None:
            recorded_at_utc = recorded_at_utc.replace(tzinfo=timezone.utc)

        wav = self.normalize_audio(blob, mime)
        normalized = self.prisma.transcribe(wav, mode="transcribe")
        verbatim = self.prisma.transcribe(
            wav,
            mode="verbatim",
            bias=list(self.bias_words) if self.use_bias else None,
        )
        card = self.extractor.extract_card(normalized, verbatim, recorded_at_utc)
        logs = (
            TranscriptLog(
                role="mechanic",
                mode="transcribe",
                text=normalized,
                recorded_at_utc=recorded_at_utc,
            ),
            TranscriptLog(
                role="mechanic",
                mode="verbatim",
                text=verbatim,
                recorded_at_utc=recorded_at_utc,
            ),
        )
        return self.store.set_card(
            session_id,
            expected_revision=expected_revision,
            card=card,
            logs=logs,
        )

    def reask(
        self,
        session_id: str,
        field: str,
        blob: bytes,
        mime: str,
        *,
        expected_revision: int,
        recorded_at_utc: datetime | None = None,
    ) -> Session:
        if field != "delivery" and not REASK_FIELD_PATTERN.match(field):
            raise ValueError(f"invalid re-ask field: {field}")

        session = self.store.get(session_id)
        if session.card is None:
            raise ValueError("cannot re-ask field on session without card")

        if field != "delivery":
            item_id = field.split(".")[1]
            if not any(it.id == item_id for it in session.card.items):
                raise ValueError(f"item {item_id} not found on card")

        recorded_at_utc = recorded_at_utc or datetime.now(timezone.utc)
        if recorded_at_utc.tzinfo is None:
            recorded_at_utc = recorded_at_utc.replace(tzinfo=timezone.utc)

        wav = self.normalize_audio(blob, mime)
        transcript = self.prisma.transcribe(wav, mode="transcribe")

        sig = inspect.signature(self.extractor.extract_field)
        has_when = "when" in sig.parameters
        has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())

        if has_when:
            updated_card = self.extractor.extract_field(
                field, transcript, session.card, when=recorded_at_utc
            )
        elif has_varkw:
            try:
                updated_card = self.extractor.extract_field(
                    field, transcript, session.card, when=recorded_at_utc
                )
            except TypeError:
                updated_card = self.extractor.extract_field(field, transcript, session.card)
        else:
            updated_card = self.extractor.extract_field(field, transcript, session.card)

        log = TranscriptLog(
            role="mechanic",
            mode=f"reask:{field}",
            text=transcript,
            recorded_at_utc=recorded_at_utc,
        )
        return self.store.set_card(
            session_id,
            expected_revision=expected_revision,
            card=updated_card,
            logs=(log,),
        )
