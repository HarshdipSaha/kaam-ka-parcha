from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import inspect
import re
from typing import Literal
import unicodedata

from .audio import codec_round_trip, mix_at_snr, mulaw_to_wav, normalize_upload
from .extract import Extractor
from .gnani import GnaniError, PrismaClient, TimbreClient
from .money import AbstainReason, AmountDecision, confusable_amount, decide_amounts, settle_card_amounts, spoken_item_order
from .numerals import parse_amounts
from .schema import Evidence, JobCard, LineItem, TranscriptLog
from .session import Conflict, Session, SessionStore
from .vocabulary import AUTOMOTIVE_BIAS_WORDS

SMALL_AMOUNT_PAISE = 10_000   # ₹100
REASK_FIELD_PATTERN = re.compile(r"^items\.[a-z]+-[0-9]+\.(label|amount_paise)$")


class RepeatRequest(RuntimeError):
    """The speaker must say it again; nothing on the card was changed."""

    def __init__(self, reason: AbstainReason):
        super().__init__(reason)
        self.reason = reason


class NothingToConfirm(ValueError):
    """Every amount on the card is already settled; there is nothing for a whole-estimate repeat to do."""


def provider_reason(exc: GnaniError) -> AbstainReason | None:
    return {504: "provider_504", 429: "provider_429"}.get(exc.status)


def abstain_logs(abstentions: dict[str, AbstainReason], when: datetime) -> tuple[TranscriptLog, ...]:
    return tuple(TranscriptLog(role="system", mode=f"abstain:{field}", text=reason, recorded_at_utc=when)
                 for field, reason in sorted(abstentions.items()))

from .languages import DEFAULT_LANGUAGE, pack_for
from .readback import (
    DATE_WORDS,
    NO,
    PHRASAL_AFFIRMATION_PROMPT,
    YES,
    ReplyClass,
    classify_reply,
    format_rupees,
    make_readback,
)


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


@dataclass(frozen=True)
class Readback:
    text: str
    audio_wav: bytes
    manifest: dict
    revision: int
    readback_revision: int


@dataclass(frozen=True)
class ReplyResult:
    outcome: Literal["confirmed", "needs_readback", "ask_field", "retry", "fallback"]
    transcript: str
    session: Session
    message: str | None = None
    fallback_payload: dict | None = None



class Workflow:
    def __init__(
        self,
        store: SessionStore,
        prisma: PrismaClient,
        extractor: Extractor,
        normalize_audio: Callable[[bytes, str], bytes] | None = None,
        bias_words: tuple[str, ...] = AUTOMOTIVE_BIAS_WORDS,
        use_bias: bool = True,
        timbre: TimbreClient | None = None,
        codec: str = "g711",
        target_snr_db: float | None = None,
        noise_wav: bytes | None = None,
        noise_source: str = "synthetic",
        language_voices: dict[str, str] | None = None,
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
        self.noise_source = noise_source if noise_wav else "none"
        self.language_voices = dict(language_voices or {})

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
        audio_sha256 = hashlib.sha256(wav).hexdigest()
        normalized, verbatim = self._two_passes(wav)
        if not normalized.strip() and not verbatim.strip():
            raise RepeatRequest("empty_transcript")
        card = self.extractor.extract_card(normalized, verbatim, recorded_at_utc)
        card, abstentions = settle_card_amounts(card, verbatim=verbatim, transcribe=normalized)
        logs = (
            TranscriptLog(
                role="mechanic",
                mode="transcribe",
                text=normalized,
                recorded_at_utc=recorded_at_utc,
                audio_sha256=audio_sha256,
            ),
            TranscriptLog(
                role="mechanic",
                mode="verbatim",
                text=verbatim,
                recorded_at_utc=recorded_at_utc,
                audio_sha256=audio_sha256,
            ),
        ) + abstain_logs(abstentions, recorded_at_utc)
        return self.store.set_card(
            session_id,
            expected_revision=expected_revision,
            card=card,
            logs=logs,
        )

    def _two_passes(self, wav: bytes) -> tuple[str, str]:
        """Transcribe pass then verbatim pass on the same audio; 504/429 become RepeatRequest."""
        try:
            normalized = self.prisma.transcribe(wav, mode="transcribe")
            verbatim = self.prisma.transcribe(
                wav, mode="verbatim", bias=list(self.bias_words) if self.use_bias else None)
        except GnaniError as exc:
            reason = provider_reason(exc)
            if reason is None:
                raise
            raise RepeatRequest(reason) from exc
        return normalized, verbatim

    @staticmethod
    def _require_agreeing_recordings(session: Session, field: str, decision: AmountDecision) -> AmountDecision:
        """A flagged amount is settled only when two consecutive recordings agree.

        The candidate is what the previous recording heard (kept as zero-score evidence). A recording with no
        candidate, or one that differs from it, becomes the new candidate instead of the amount. An amount with
        look-alike number words (see `money.confusable_amount`) needs a third agreeing recording.
        """
        item_id = field.split(".")[1]
        if decision.reason is not None or any(
            it.id == item_id and it.amount_paise is not None for it in session.card.items
        ):
            return decision
        quote = next((ev.quote for ev in session.card.evidence if ev.field == field and ev.review_score == 0.0), "")
        heard = [m.paise for m in parse_amounts(quote) if m.status == "complete"]
        if len(heard) != 1:
            return AmountDecision(None, "independent_confirmation_required", decision.quote)
        if heard[0] != decision.paise:
            return AmountDecision(None, "recordings_disagree", decision.quote)
        if confusable_amount(decision.quote) or decision.paise < SMALL_AMOUNT_PAISE:
            # Look-alike number words can fool two recordings the same way, and so can a lost tail: "तेरह सौ" and "तेईस सौ"
            # heard twice as "तेरह" / "तेईस" (₹13, ₹23) at 0 dB. A repair line under ₹100 is rare, so it also gets a
            # third look. Settle only on a third agreeing recording, i.e. when the previous recording ended in this state.
            last = next((log.text for log in reversed(session.logs) if log.mode == f"abstain:{field}"), None)
            if last != "confusable_needs_third":
                return AmountDecision(None, "confusable_needs_third", decision.quote)
        return decision

    def _reask_amount(
        self,
        session: Session,
        field: str,
        wav: bytes,
        audio_sha256: str,
        expected_revision: int,
        recorded_at_utc: datetime,
    ) -> Session:
        try:
            normalized, verbatim = self._two_passes(wav)
            if not normalized.strip() and not verbatim.strip():
                raise RepeatRequest("empty_transcript")
        except RepeatRequest as exc:
            decision = AmountDecision(None, exc.reason, "")
            logs = abstain_logs({field: exc.reason}, recorded_at_utc)
        else:
            reask_log = TranscriptLog(
                role="mechanic",
                mode=f"reask:{field}",
                text=verbatim,
                recorded_at_utc=recorded_at_utc,
                audio_sha256=audio_sha256,
            )
            decision = self._require_agreeing_recordings(
                session, field, decide_amounts(verbatim, normalized, expected_count=1)[0]
            )
            if decision.reason is None:
                logs = (reask_log,)
            else:
                logs = (reask_log,) + abstain_logs({field: decision.reason}, recorded_at_utc)

        item_id = field.split(".")[1]
        items = tuple(
            LineItem(
                id=it.id,
                label=it.label,
                kind=it.kind,
                amount_paise=decision.paise if it.id == item_id else it.amount_paise,
            )
            for it in session.card.items
        )
        evidence = [ev for ev in session.card.evidence if ev.field != field]
        if decision.reason is None:
            evidence.append(Evidence(field=field, quote=decision.quote, review_score=1.0))
        elif decision.quote.strip():
            evidence.append(Evidence(field=field, quote=decision.quote, review_score=0.0))
        new_card = JobCard(items=items, delivery=session.card.delivery, evidence=tuple(evidence))
        return self.store.set_card(
            session.id,
            expected_revision=expected_revision,
            card=new_card,
            logs=logs,
        )

    def confirm_estimate(
        self,
        session_id: str,
        blob: bytes,
        mime: str,
        *,
        expected_revision: int,
        recorded_at_utc: datetime | None = None,
    ) -> Session:
        """One repeat of the whole estimate settles every flagged amount whose value both recordings agree on.

        Same two-recording rule as a per-amount re-ask, applied per item in spoken order. Settled items are
        left untouched; a flagged item that disagrees (or has no candidate yet) stays flagged and keeps what
        this recording heard as its new candidate.
        """
        session = self.store.get(session_id)
        if session.card is None:
            raise ValueError("cannot confirm estimate on session without card")
        if session.status == "confirmed":
            raise Conflict("confirmed session is immutable")
        if session.revision != expected_revision:
            raise Conflict(f"stale revision: expected {expected_revision}, current {session.revision}")
        card = session.card
        flagged = [it.id for it in card.items if it.amount_paise is None]
        if not flagged:
            raise NothingToConfirm("no flagged amount to confirm")

        recorded_at_utc = recorded_at_utc or datetime.now(timezone.utc)
        if recorded_at_utc.tzinfo is None:
            recorded_at_utc = recorded_at_utc.replace(tzinfo=timezone.utc)
        wav = self.normalize_audio(blob, mime)
        audio_sha256 = hashlib.sha256(wav).hexdigest()

        by_id: dict[str, AmountDecision] = {}
        log_text = ""
        try:
            normalized, verbatim = self._two_passes(wav)
            if not normalized.strip() and not verbatim.strip():
                raise RepeatRequest("empty_transcript")
        except RepeatRequest as exc:
            by_id = {item_id: AmountDecision(None, exc.reason, "") for item_id in flagged}
        else:
            log_text = verbatim
            order = spoken_item_order(card, [t for t in (normalized, verbatim) if t]) or [it.id for it in card.items]
            decisions = decide_amounts(verbatim, normalized, expected_count=len(card.items))
            for item_id, decision in zip(order, decisions):
                if item_id in flagged:
                    by_id[item_id] = self._require_agreeing_recordings(
                        session, f"items.{item_id}.amount_paise", decision
                    )

        items = tuple(
            LineItem(id=it.id, label=it.label, kind=it.kind,
                     amount_paise=by_id[it.id].paise if it.id in by_id else it.amount_paise)
            for it in card.items
        )
        evidence = list(card.evidence)
        abstentions: dict[str, AbstainReason] = {}
        for item_id, decision in by_id.items():
            field = f"items.{item_id}.amount_paise"
            if decision.reason is None:
                evidence = [ev for ev in evidence if ev.field != field]
                evidence.append(Evidence(field=field, quote=decision.quote, review_score=1.0))
            else:
                abstentions[field] = decision.reason
                if decision.quote.strip():
                    evidence = [ev for ev in evidence if ev.field != field]
                    evidence.append(Evidence(field=field, quote=decision.quote, review_score=0.0))
        logs = (
            TranscriptLog(role="mechanic", mode="confirm_estimate", text=log_text,
                          recorded_at_utc=recorded_at_utc, audio_sha256=audio_sha256),
        ) + abstain_logs(abstentions, recorded_at_utc)
        new_card = JobCard(items=items, delivery=card.delivery, evidence=tuple(evidence))
        return self.store.set_card(session_id, expected_revision=expected_revision, card=new_card, logs=logs)

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
        audio_sha256 = hashlib.sha256(wav).hexdigest()

        if field.endswith(".amount_paise"):
            return self._reask_amount(session, field, wav, audio_sha256, expected_revision, recorded_at_utc)

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
            audio_sha256=audio_sha256,
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
        *,
        include_consent: bool = True,
        language: str | None = None,
        degrade: bool = True,
    ) -> Readback:
        session = self.store.get(session_id)
        if session.card is None or session.card.needs_review:
            raise Conflict("card needs review")

        pack = pack_for(language)          # None: Hindi, the original path
        text = make_readback(session.card, include_consent=include_consent, language=language)

        if not self.timbre:
            raise ValueError("Timbre client required for readback")

        if pack is None:
            raw_mulaw = self.timbre.synthesize(text)
        else:
            voice = self.language_voices.get(pack.code, pack.voices[0])
            raw_mulaw = self.timbre.synthesize(text, language=pack.code, voice=voice)
        wav = mulaw_to_wav(raw_mulaw)

        if degrade and self.noise_wav and self.target_snr_db is not None:
            degraded_wav, measured_snr = mix_at_snr(wav, self.noise_wav, self.target_snr_db)
        else:
            degraded_wav, measured_snr = wav, float("inf")

        # A real telephone call (Twilio) already degrades audio on its own codec; our simulated
        # degradation is for the in-browser line only, so a real call skips this second pass.
        final_wav = codec_round_trip(degraded_wav, self.codec) if degrade else degraded_wav

        manifest = {
            "codec": self.codec if degrade else "none (real telephone call; not simulated)",
            "sample_rate": 8000,
            "noise_source": self.noise_source,
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
            audio_sha256=hashlib.sha256(final_wav).hexdigest(),
        )

        updated_session = self.store.start_readback(
            session_id, expected_revision=expected_revision, log=log
        )
        if pack is not None:
            # The reply is recognised and classified in the language that was read back; the audit trail records it.
            updated_session = self.store.record_observation(
                session_id,
                expected_revision=updated_session.revision,
                readback_revision=updated_session.readback_revision,
                log=TranscriptLog(role="system", mode="readback_language", text=pack.code, recorded_at_utc=rec_time),
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
        degrade: bool = True,
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

        if degrade and self.noise_wav and self.target_snr_db is not None:
            wav, _ = mix_at_snr(wav, self.noise_wav, self.target_snr_db)
            wav = codec_round_trip(wav, self.codec)

        language = next((log.text for log in reversed(session.logs) if log.mode == "readback_language"), DEFAULT_LANGUAGE)
        stt_options = {} if language == DEFAULT_LANGUAGE else {"language_code": language}
        confidence = 1.0
        if hasattr(self.prisma, "transcribe_detailed"):
            transcript, confidence = self.prisma.transcribe_detailed(wav, mode="transcribe", **stt_options)
        else:
            transcript = self.prisma.transcribe(wav, mode="transcribe", **stt_options)
            if hasattr(self.prisma, "confidence"):
                confidence = float(self.prisma.confidence)
            elif hasattr(self.prisma, "last_confidence"):
                confidence = float(self.prisma.last_confidence)

        audio_sha256 = hashlib.sha256(wav).hexdigest()

        recorded_at_utc = recorded_at_utc or datetime.now(timezone.utc)
        if recorded_at_utc.tzinfo is None:
            recorded_at_utc = recorded_at_utc.replace(tzinfo=timezone.utc)

        customer_log = TranscriptLog(
            role="customer",
            mode="reply",
            text=transcript,
            recorded_at_utc=recorded_at_utc,
            audio_sha256=audio_sha256,
        )

        # Count prior retry attempts during this readback cycle
        prior_retries = sum(
            1 for log in session.logs
            if log.role == "customer" and log.mode in ("reply", "unclear", "unresolved_correction")
        )

        # 1. Confidence threshold evaluation (< 0.65 triggers digital fallback)
        if confidence < 0.65:
            fallback_log = TranscriptLog(
                role="customer",
                mode="low_confidence_fallback",
                text=transcript,
                recorded_at_utc=recorded_at_utc,
                audio_sha256=audio_sha256,
            )
            updated_session = self.store.trigger_fallback(
                session_id,
                expected_revision=expected_revision,
                log=fallback_log,
            )
            return ReplyResult(
                outcome="fallback",
                transcript=transcript,
                session=updated_session,
                message="Speech confidence below 0.65. Switched to digital confirmation fallback.",
                fallback_payload={
                    "session_id": session_id,
                    "confidence": confidence,
                    "actions": [
                        {"label": "Approve Estimate", "action": "approve"},
                        {"label": "Request Changes", "action": "request_changes"},
                    ],
                },
            )

        classification = classify_reply(transcript, None if language == DEFAULT_LANGUAGE else language)

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
                        audio_sha256=audio_sha256,
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
        # Check if 2 retries have already occurred (prior_retries >= 2 -> fallback)
        if prior_retries >= 2:
            updated_session = self.store.trigger_fallback(
                session_id,
                expected_revision=expected_revision,
                log=customer_log,
            )
            return ReplyResult(
                outcome="fallback",
                transcript=transcript,
                session=updated_session,
                message="Repeated retries encountered on voice line. Switched to digital confirmation fallback.",
                fallback_payload={
                    "session_id": session_id,
                    "retries": prior_retries + 1,
                    "actions": [
                        {"label": "Approve Estimate", "action": "approve"},
                        {"label": "Request Changes", "action": "request_changes"},
                    ],
                },
            )

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
