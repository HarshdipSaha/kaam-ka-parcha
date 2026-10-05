"""Money path: amounts come only from the numeral grammar; the transcribe pass is a formatting cross-check."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Literal

from .numerals import MAX_ITEM_PAISE, parse_amounts
from .schema import Evidence, JobCard, LineItem

__all__ = ["AbstainReason", "AmountDecision", "decide_amounts", "settle_card_amounts", "spoken_item_order"]

AbstainReason = Literal["incomplete_number", "crosscheck_disagreement", "empty_transcript",
                        "provider_504", "provider_429", "ambiguous_attachment", "out_of_range"]


@dataclass(frozen=True)
class AmountDecision:
    paise: int | None
    reason: AbstainReason | None  # None means accepted
    quote: str


_TOTAL_MARKER = re.compile(r"(?:^|\s)(?:कुल|टोटल|kul|total)(?=\s|$)", re.IGNORECASE)


def _split_spoken_total(text: str) -> tuple[str, str | None]:
    match = _TOTAL_MARKER.search(text)
    return (text, None) if match is None else (text[: match.start()], text[match.end():])


def decide_amounts(verbatim: str, transcribe: str | None, *, expected_count: int) -> list[AmountDecision]:
    """One decision per expected slot. Never guesses: any doubt yields paise=None plus a reason."""
    if not verbatim.strip() or (transcribe is not None and not transcribe.strip()):
        return [AmountDecision(None, "empty_transcript", "")] * expected_count
    body, total_text = _split_spoken_total(verbatim)
    spoken = parse_amounts(body)
    if len(spoken) != expected_count:
        return [AmountDecision(None, "ambiguous_attachment", "")] * expected_count
    if total_text is not None:
        totals = [m.paise for m in parse_amounts(total_text) if m.status == "complete"]
        if totals[:1] != [sum(m.paise or 0 for m in spoken)] or any(m.status != "complete" for m in spoken):
            return [AmountDecision(None, "crosscheck_disagreement", m.text) for m in spoken]
    cross = parse_amounts(_split_spoken_total(transcribe)[0]) if transcribe is not None else None
    counts_differ = cross is not None and len(cross) != len(spoken)
    decisions: list[AmountDecision] = []
    for i, mention in enumerate(spoken):
        if mention.status != "complete" or mention.paise is None:
            decisions.append(AmountDecision(None, "incomplete_number", mention.text))
        elif mention.paise > MAX_ITEM_PAISE:
            decisions.append(AmountDecision(None, "out_of_range", mention.text))
        elif counts_differ or (cross is not None and cross[i].paise != mention.paise):
            decisions.append(AmountDecision(None, "crosscheck_disagreement", mention.text))
        else:
            decisions.append(AmountDecision(mention.paise, None, mention.text))
    return decisions


def _fold(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def spoken_item_order(card: JobCard, transcripts: list[str]) -> list[str] | None:
    """Item ids ordered by where their label-evidence quote first appears; None if any can't be located."""
    positions: list[tuple[float, str]] = []
    for item in card.items:
        quote = next((ev.quote for ev in card.evidence
                      if ev.field == f"items.{item.id}.label" and ev.quote.strip()), item.label or "")
        if not quote.strip():
            return None
        found = None
        for transcript in transcripts:
            text = _fold(transcript)
            at = text.find(_fold(quote))
            if at != -1 and text:
                found = at / len(text)
                break
        if found is None:
            return None
        positions.append((found, item.id))
    return [item_id for _, item_id in sorted(positions)]


def settle_card_amounts(card: JobCard, *, verbatim: str,
                        transcribe: str | None) -> tuple[JobCard, dict[str, AbstainReason]]:
    """Replace every item amount with the grammar's decision; return the new card and per-field abstentions."""
    order = spoken_item_order(card, [t for t in (transcribe, verbatim) if t])
    if order is None:
        decisions = [AmountDecision(None, "ambiguous_attachment", "")] * len(card.items)
        order = [item.id for item in card.items]
    else:
        decisions = decide_amounts(verbatim, transcribe, expected_count=len(card.items))
    by_id = dict(zip(order, decisions))
    items = tuple(LineItem(id=it.id, label=it.label, kind=it.kind, amount_paise=by_id[it.id].paise)
                  for it in card.items)
    evidence = [ev for ev in card.evidence if not ev.field.endswith(".amount_paise")]
    abstentions: dict[str, AbstainReason] = {}
    for item_id, decision in by_id.items():
        field = f"items.{item_id}.amount_paise"
        if decision.reason is None:
            evidence.append(Evidence(field=field, quote=decision.quote, review_score=1.0))
        else:
            abstentions[field] = decision.reason
    return JobCard(items=items, delivery=card.delivery, evidence=tuple(evidence)), abstentions
