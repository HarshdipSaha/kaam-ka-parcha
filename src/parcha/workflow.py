from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import inspect
import re
from typing import Literal
import unicodedata

from .audio import codec_round_trip, mix_at_snr, mulaw_to_wav, normalize_upload
from .extract import Extractor
from .gnani import PrismaClient, TimbreClient
from .schema import JobCard, LineItem, TranscriptLog
from .session import Conflict, Session, SessionStore

REASK_FIELD_PATTERN = re.compile(r"^items\.[a-z]+-[0-9]+\.(label|amount_paise)$")

ReplyClass = Literal["accept", "correction", "reject", "unclear"]
YES = {"haan", "han", "हाँ", "हां"}
NO = {"nahi", "nahin", "नहीं", "ना"}
DATE_WORDS = {
    "kal", "somvaar", "mangalvaar", "budhvaar", "guruvaar",
    "shukravaar", "shanivaar", "ravivaar", "shaam", "subah",
    "monday", "tuesday", "बुधवार", "मंगलवार", "सोमवार",
    "शाम", "सुबह", "तारीख", "कल",
}


def classify_reply(text: str) -> ReplyClass:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    words = re.findall(r"[a-z0-9\u0900-\u097f]+", normalized)
    if not words:
        return "unclear"
    if any(word in NO for word in words):
        remaining = [word for word in words if word not in NO]
        return "correction" if remaining else "reject"
    if words[0] not in YES:
        return "unclear"
    tail = words[1:]
    if tail in ([], ["theek", "hai"], ["ठीक", "है"]):
        return "accept"
    return "unclear"


def _item_matches_transcript(item: LineItem, norm_transcript: str, transcript_words: set[str]) -> bool:
    if item.id.casefold() in norm_transcript or item.id.casefold() in transcript_words:
        return True
    if item.label:
        label_norm = unicodedata.normalize("NFKC", item.label).casefold()
        if label_norm in norm_transcript:
            return True
        label_words = [
            w for w in re.findall(r"[a-z0-9\u0900-\u097f]+", label_norm)
            if w not in NO and w not in YES
        ]
        if any(w in transcript_words for w in label_words):
            return True
    return False


def format_rupees(paise: int) -> str:
    if paise % 100 == 0:
        return f"₹{paise // 100}"
    else:
        return f"₹{paise / 100:.2f}"


def make_readback(card: JobCard) -> str:
    items_str = ", ".join(
        f"{item.label}: {format_rupees(item.amount_paise if item.amount_paise is not None else 0)}"
        for item in card.items
    )
    delivery_str = f"डिलीवरी {card.delivery.spoken if card.delivery else ''}"
    return f"{items_str}. कुल {format_rupees(card.total_paise)}. {delivery_str}. ठीक है? हाँ कहें, या सुधार बताएं।"


@dataclass(frozen=True)
class Readback:
    text: str
    audio_wav: bytes
    manifest: dict
    revision: int
    readback_revision: int


@dataclass(frozen=True)
class ReplyResult:
    outcome: Literal["confirmed", "needs_readback", "ask_field", "retry"]
    transcript: str
    session: Session
    message: str | None = None


class Workflow:
    def __init__(
        self,
        store: SessionStore,
        prisma: PrismaClient,
        extractor: Extractor,
        normalize_audio: Callable[[bytes, str], bytes] | None = None,
        bias_words: tuple[str, ...] = ("brake", "clutch", "Honda"),
        use_bias: bool = False,
        timbre: TimbreClient | None = None,
        codec: str = "g711",
        target_snr_db: float | None = None,
        noise_wav: bytes | None = None,
    ):
        self.store = store
        self.prisma = prisma
        self.extractor = extractor
        self.normalize_audio = normalize_audio if normalize_audio is not None else normalize_upload
        self.bias_words = bias_words
        self.use_bias = use_bias
        self.timbre = timbre
        self.codec = codec
        self.target_snr_db = target_snr_db
        self.noise_wav = noise_wav

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

    def start_readback(
        self,
        session_id: str,
        expected_revision: int,
        recorded_at_utc: datetime | None = None,
    ) -> Readback:
        session = self.store.get(session_id)
        if session.card is None or session.card.needs_review:
            raise Conflict("card needs review")

        text = make_readback(session.card)

        if not self.timbre:
            raise ValueError("Timbre client required for readback")

        raw_mulaw = self.timbre.synthesize(text)
        wav = mulaw_to_wav(raw_mulaw)

        if self.noise_wav and self.target_snr_db is not None:
            degraded_wav, measured_snr = mix_at_snr(wav, self.noise_wav, self.target_snr_db)
        else:
            degraded_wav, measured_snr = wav, float("inf")

        final_wav = codec_round_trip(degraded_wav, self.codec)

        manifest = {
            "codec": self.codec,
            "sample_rate": 8000,
            "noise_source": "synthetic" if self.noise_wav else "none",
            "target_snr_db": self.target_snr_db,
            "measured_snr_db": measured_snr,
            "loss_percent": 0,
            "revision": expected_revision,
        }

        rec_time = recorded_at_utc or datetime.now(timezone.utc)
        if rec_time.tzinfo is None:
            rec_time = rec_time.replace(tzinfo=timezone.utc)

        log = TranscriptLog(
            role="system",
            mode="timbre_readback",
            text=text,
            recorded_at_utc=rec_time,
        )

        updated_session = self.store.start_readback(
            session_id, expected_revision=expected_revision, log=log
        )

        return Readback(
            text=text,
            audio_wav=final_wav,
            manifest=manifest,
            revision=updated_session.revision,
            readback_revision=(
                updated_session.readback_revision
                if updated_session.readback_revision is not None
                else expected_revision
            ),
        )

    def reply(
        self,
        session_id: str,
        blob: bytes,
        mime: str,
        *,
        expected_revision: int,
        readback_revision: int,
        recorded_at_utc: datetime | None = None,
    ) -> ReplyResult:
        session = self.store.get(session_id)
        if session.status != "awaiting_reply":
            raise Conflict("session not awaiting reply")
        if session.revision != expected_revision or session.readback_revision != readback_revision:
            raise Conflict("stale revision")

        try:
            wav = self.normalize_audio(blob, mime, sample_rate=8000)
        except TypeError:
            wav = self.normalize_audio(blob, mime)

        if self.noise_wav and self.target_snr_db is not None:
            wav, _ = mix_at_snr(wav, self.noise_wav, self.target_snr_db)
            wav = codec_round_trip(wav, self.codec)

        transcript = self.prisma.transcribe(wav, mode="transcribe")

        recorded_at_utc = recorded_at_utc or datetime.now(timezone.utc)
        if recorded_at_utc.tzinfo is None:
            recorded_at_utc = recorded_at_utc.replace(tzinfo=timezone.utc)

        customer_log = TranscriptLog(
            role="customer",
            mode="reply",
            text=transcript,
            recorded_at_utc=recorded_at_utc,
        )

        classification = classify_reply(transcript)

        if classification == "accept":
            updated_session = self.store.confirm(
                session_id,
                expected_revision=expected_revision,
                when=recorded_at_utc,
                log=customer_log,
            )
            return ReplyResult(
                outcome="confirmed",
                transcript=transcript,
                session=updated_session,
            )

        if classification == "correction":
            norm_transcript = unicodedata.normalize("NFKC", transcript).casefold()
            transcript_words = set(re.findall(r"[a-z0-9\u0900-\u097f]+", norm_transcript))

            if any(w in DATE_WORDS for w in transcript_words) or any(w in norm_transcript for w in DATE_WORDS):
                target = "delivery"
            else:
                card_items = session.card.items if session.card else ()
                matching_items = [
                    item
                    for item in card_items
                    if _item_matches_transcript(item, norm_transcript, transcript_words)
                ]
                if len(matching_items) == 1:
                    target = f"items.{matching_items[0].id}.amount_paise"
                elif len(card_items) == 1:
                    target = f"items.{card_items[0].id}.amount_paise"
                else:
                    # Ambiguous correction! Ask which item.
                    obs_log = TranscriptLog(
                        role="customer",
                        mode="unresolved_correction",
                        text=transcript,
                        recorded_at_utc=recorded_at_utc,
                    )
                    updated = self.store.record_observation(
                        session_id,
                        expected_revision=expected_revision,
                        readback_revision=readback_revision,
                        log=obs_log,
                    )
                    return ReplyResult(
                        outcome="ask_field",
                        transcript=transcript,
                        session=updated,
                        message="Which item would you like to correct?",
                    )

            # Having resolved target:
            sig = inspect.signature(self.extractor.extract_field)
            has_when = "when" in sig.parameters
            has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())

            if has_when:
                updated_card = self.extractor.extract_field(
                    target, transcript, session.card, when=recorded_at_utc
                )
            elif has_varkw:
                try:
                    updated_card = self.extractor.extract_field(
                        target, transcript, session.card, when=recorded_at_utc
                    )
                except TypeError:
                    updated_card = self.extractor.extract_field(target, transcript, session.card)
            else:
                updated_card = self.extractor.extract_field(target, transcript, session.card)

            updated_session = self.store.set_card(
                session_id,
                expected_revision=expected_revision,
                card=updated_card,
                logs=(customer_log,),
            )
            return ReplyResult(
                outcome="needs_readback",
                transcript=transcript,
                session=updated_session,
            )

        # classification in ("reject", "unclear")
        updated_session = self.store.record_observation(
            session_id,
            expected_revision=expected_revision,
            readback_revision=readback_revision,
            log=customer_log,
        )
        return ReplyResult(
            outcome="retry",
            transcript=transcript,
            session=updated_session,
            message="Could not recognize confirmation or correction",
        )
