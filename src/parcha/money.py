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
                        "provider_504", "provider_429", "ambiguous_attachment", "out_of_range",
                        "independent_confirmation_required", "recordings_disagree"]


@dataclass(frozen=True)
class AmountDecision:
    paise: int | None
    reason: AbstainReason | None  # None means accepted
    quote: str


_TOTAL_MARKER = re.compile(r"(?:^|\s)(?:कुल|टोटल|kul|total)(?=\s|$)", re.IGNORECASE)


def _split_spoken_total(text: str) -> tuple[str, str | None]:
    match = _TOTAL_MARKER.search(text)
    return (text, None) if match is None else (text[: match.start()], text[match.end():])


_RS = r"(?:₹\s?)?(\d[\d,]*)"
_CLOCK_FRACTION = re.compile(rf"(?<!\d)(\d{{1,2}}):30\s+{_RS}(?![\d,])")          # साढ़े H N is formatted as a clock time
_BIG_UNIT = {"हज़ार": 1000, "हजार": 1000, "लाख": 100000}
_CLOCK_WORD = re.compile(r"(?<!\d)(\d{1,2}):30\s+(हज़ार|हजार|लाख)")                     # साढ़े H हज़ार -> "H:30 हज़ार"
# A comma after the unit word ("साढ़े 30 हज़ार, सर्विस ...") separates items; only a digit group ("4,000") must not match
_SADHE_NUMBER = re.compile(rf"(?:^|(?<=\s))साढ़े\s+{_RS}(?:\s*(हज़ार|हजार|लाख))?(?!\d|,\d)")  # "साढ़े 4,000" / "साढ़े 23 हज़ार"
_WORD_FRACTION = re.compile(rf"(?:^|(?<=\s))(डेढ़|ढाई)\s+{_RS}(?![\d,])")
_QUARTER = re.compile(rf"(?:^|(?<=\s))(सवा|पौने)\s+{_RS}(?![\d,])")
# Prisma formats "एक हज़ार छह सौ पचास" as "1,600 पचास": digits ending in 00, then the word for 50 left unformatted
_TRAILING_FIFTY = re.compile(rf"(?:^|(?<=\s)){_RS}\s+पचास(?=\s|[,।.]|$)")


def _rupees(token: str) -> int | None:
    digits = token.replace(",", "")
    return int(digits) if digits.isdigit() else None


def _unit(rupees: int) -> int:
    return 1000 if rupees >= 1000 and rupees % 1000 == 0 else 100


def normalise_transcribe_fractions(text: str) -> str:
    """Rewrite how the transcribe pass formats colloquial fractions ("04:30 ₹100", "ढाई ₹100", "पौने ₹200").

    The result is the plain amount it denotes, so the cross-check compares values, not formatting. Only exact,
    whole-rupee readings are rewritten; anything else is left for the parser to disagree with.
    """
    def clock(m: re.Match) -> str:
        hours, unit = int(m.group(1)), _rupees(m.group(2))
        return f"₹{hours * unit + unit // 2}" if unit in (100, 1000) and 0 < hours < 100 else m.group(0)

    def clock_word(m: re.Match) -> str:
        unit = _BIG_UNIT[m.group(2)]
        return f"₹{int(m.group(1)) * unit + unit // 2}"

    def sadhe(m: re.Match) -> str:
        number, unit = _rupees(m.group(1)), _BIG_UNIT.get(m.group(2) or "")
        if number is None or number == 0:
            return m.group(0)
        if unit is not None:
            return f"₹{number * unit + unit // 2}"
        return f"₹{number + 500}" if number >= 1000 and number % 1000 == 0 else m.group(0)

    def word(m: re.Match) -> str:
        unit = _rupees(m.group(2))
        if unit not in (100, 1000):
            return m.group(0)
        return f"₹{unit * 3 // 2 if m.group(1) == 'डेढ़' else unit * 5 // 2}"

    def quarter(m: re.Match) -> str:
        base = _rupees(m.group(2))
        if base is None or base == 0:
            return m.group(0)
        step = _unit(base) // 4
        return f"₹{base + step if m.group(1) == 'सवा' else base - step}"

    def trailing_fifty(m: re.Match) -> str:
        number = _rupees(m.group(1))
        return f"₹{number + 50}" if number is not None and number >= 100 and number % 100 == 0 else m.group(0)

    text = _TRAILING_FIFTY.sub(trailing_fifty, text)
    text = _CLOCK_WORD.sub(clock_word, _CLOCK_FRACTION.sub(clock, text))
    return _QUARTER.sub(quarter, _WORD_FRACTION.sub(word, _SADHE_NUMBER.sub(sadhe, text)))


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
    cross = (parse_amounts(_split_spoken_total(normalise_transcribe_fractions(transcribe))[0])
             if transcribe is not None else None)
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
        # Two modes over one recording are correlated evidence. A numeric parse is
        # only a candidate until a deliberate repeat or customer confirmation.
        decisions = [
            AmountDecision(None, "independent_confirmation_required", decision.quote)
            if decision.reason is None else decision
            for decision in decisions
        ]
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
            if decision.quote.strip():
                # What was heard, shown to the mechanic; score 0 keeps the field in review.
                evidence.append(Evidence(field=field, quote=decision.quote, review_score=0.0))
    return JobCard(items=items, delivery=card.delivery, evidence=tuple(evidence)), abstentions
