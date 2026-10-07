from __future__ import annotations

import re
from typing import Literal
import unicodedata

from .languages import LanguagePack, pack_for
from .numerals import render_hindi_amount
from .schema import JobCard

PHRASAL_AFFIRMATION_PROMPT = (
    "Agar aapko yeh manzoor hai, toh boliye: 'Haan, theek hai'. Kuch galat ho toh bataiye."
)

STATUTORY_CONSENT_NOTICE = (
    "DPDP Act 2023 ke antargat yeh call service estimate confirmation hetu record ki ja rahi hai."
)

ReplyClass = Literal["accept", "correction", "reject", "unclear"]
YES = {"haan", "han", "हाँ", "हां"}
NO = {"nahi", "nahin", "नहीं", "ना"}
MANZOOR = {"manzoor", "मंज़ूर", "मंजूर"}
MODIFIERS = {"ji", "जी", "bilkul", "बिल्कुल"}
SAHI = {"sahi", "सही"}
DATE_WORDS = {
    "kal", "somvaar", "mangalvaar", "budhvaar", "guruvaar",
    "shukravaar", "shanivaar", "ravivaar", "shaam", "subah",
    "monday", "tuesday", "बुधवार", "मंगलवार", "सोमवार",
    "शाम", "सुबह", "तारीख", "कल",
}


def format_rupees(paise: int) -> str:
    """Format paise into rupee string with Indic currency symbol."""
    if paise % 100 == 0:
        return f"₹{paise // 100}"
    else:
        return f"₹{paise / 100:.2f}"


def make_readback(
    card: JobCard,
    *,
    include_consent: bool = False,
    amount_style: Literal["digits", "words"] = "words",
    language: str | None = None,
) -> str:
    """Synthesize structured read-back prompt with phrasal affirmation instructions.
    
    Itemized totals, delivery date, explicit verbal DPDP statutory consent, and phrasal
    affirmation elicit stable 3-word responses ('Haan, theek hai') over narrowband 8 kHz
    telephony channels, preventing Voice Activity Detector (VAD) endpointing truncation.
    """
    if amount_style not in {"digits", "words"}:
        raise ValueError(f"unsupported amount style: {amount_style}")
    pack = pack_for(language)
    if pack is not None:
        return _regional_readback(card, pack, include_consent=include_consent)

    def money(paise: int) -> str:
        if amount_style == "words":
            try:
                return render_hindi_amount(paise)
            except ValueError:
                # Zero, fractional-paise and over-range amounts have no Hindi
                # word rendering; keep them as digits rather than invent one.
                return format_rupees(paise)
        return format_rupees(paise)

    items_str = ", ".join(
        f"{item.label}: {money(item.amount_paise if item.amount_paise is not None else 0)}"
        for item in card.items
    )
    delivery_str = (
        f"डिलीवरी {card.delivery.spoken}. "
        if card.delivery and card.delivery.spoken
        else ""
    )
    consent_prefix = f"{STATUTORY_CONSENT_NOTICE} " if include_consent else ""
    prefix = f"{items_str}. " if items_str else ""
    return f"{consent_prefix}{prefix}कुल {money(card.total_paise)}. {delivery_str}{PHRASAL_AFFIRMATION_PROMPT}"



def _regional_readback(card: JobCard, pack: LanguagePack, *, include_consent: bool) -> str:
    """Fixed per-language strings with digit amounts; item labels are spoken as extracted (see languages.py)."""
    items = ", ".join(
        f"{item.label}: {format_rupees(item.amount_paise if item.amount_paise is not None else 0)}" for item in card.items
    )
    delivery = ""
    if card.delivery:
        d = card.delivery
        delivery = f"{pack.delivery_word} {d.date.day}/{d.date.month}/{d.date.year} {pack.windows[d.window]}. "
    consent = f"{pack.consent_notice} " if include_consent else ""
    prefix = f"{items}. " if items else ""
    return f"{consent}{prefix}{pack.total_word} {format_rupees(card.total_paise)}. {delivery}{pack.closing_prompt}"


def _regional_words(text: str) -> list[str]:
    """Whitespace tokens with punctuation and symbols stripped; combining vowel signs are kept."""
    out = []
    for token in unicodedata.normalize("NFKC", text).casefold().split():
        word = "".join(ch for ch in token if unicodedata.category(ch)[0] not in "PS")
        if word:
            out.append(word)
    return out


def _classify_regional(text: str, pack: LanguagePack) -> ReplyClass:
    """Accept only a clear yes ("yes", "yes, ok"); any negation is a reject; everything else is unclear."""
    words = _regional_words(text)
    if not words:
        return "unclear"
    if any(w in pack.no_words for w in words):
        return "reject"
    if words[0] in pack.yes_words:
        tail = [w for w in words[1:] if w not in pack.modifiers]
        if len(tail) <= 2 and all(w in pack.ok_words for w in tail):
            return "accept"
    return "unclear"


def classify_reply(text: str, language: str | None = None) -> ReplyClass:
    """Classify customer speech into accept, correction, reject, or unclear.
    
    Recognizes both elicited 3-word phrasal affirmations and legacy affirmations,
    while enforcing strict negation priority and refusing ambiguous discourse markers.
    """
    pack = pack_for(language)
    if pack is not None:
        return _classify_regional(text, pack)
    normalized = unicodedata.normalize("NFKC", text).casefold()
    words = re.findall(r"[a-z0-9\u0900-\u097f]+", normalized)
    if not words:
        return "unclear"
    
    # Strict negation priority
    if any(word in NO for word in words):
        remaining = [word for word in words if word not in NO]
        return "correction" if remaining else "reject"

    # 1. Affirmations starting with YES ("haan", "हाँ", etc.)
    if words[0] in YES:
        tail = words[1:]
        tail_stripped = [w for w in tail if w not in MODIFIERS]
        if tail_stripped in (
            [],
            ["theek", "hai"],
            ["ठीक", "है"],
            ["manzoor", "hai"],
            ["मंज़ूर", "है"],
            ["मंजूर", "है"],
            ["sahi", "hai"],
            ["सही", "है"],
            ["manzoor"],
            ["मंज़ूर"],
            ["मंजूर"],
        ):
            return "accept"
        return "unclear"

    # 2. Inverted phrasal affirmations ("theek hai haan", "theek hai haan ji")
    if any(w in YES for w in words):
        non_mod = [w for w in words if w not in MODIFIERS]
        if non_mod in (
            ["theek", "hai", "haan"],
            ["theek", "hai", "han"],
            ["ठीक", "है", "हाँ"],
            ["ठीक", "है", "हां"],
        ):
            return "accept"

    # 3. Direct explicit acceptance with manzoor ("manzoor hai", "मंज़ूर है")
    words_stripped = [w for w in words if w not in MODIFIERS]
    if words_stripped in (
        ["manzoor", "hai"],
        ["मंज़ूर", "है"],
        ["मंजूर", "है"],
        ["manzoor"],
        ["मंज़ूर"],
        ["मंजूर"],
    ):
        return "accept"

    return "unclear"
