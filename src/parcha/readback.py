from __future__ import annotations

import re
from typing import Literal
import unicodedata

from .schema import JobCard

PHRASAL_AFFIRMATION_PROMPT = (
    "Agar aapko yeh manzoor hai, toh boliye: 'Haan, theek hai'. Koi badlaav chahiye toh rate batayein."
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


def make_readback(card: JobCard) -> str:
    """Synthesize structured read-back prompt with phrasal affirmation instructions.
    
    Itemized totals, delivery date, and explicit phrasal affirmation elicit stable
    3-word responses ('Haan, theek hai') over narrowband 8 kHz telephony channels,
    preventing Voice Activity Detector (VAD) endpointing truncation.
    """
    items_str = ", ".join(
        f"{item.label}: {format_rupees(item.amount_paise if item.amount_paise is not None else 0)}"
        for item in card.items
    )
    delivery_str = (
        f"डिलीवरी {card.delivery.spoken}. "
        if card.delivery and card.delivery.spoken
        else ""
    )
    prefix = f"{items_str}. " if items_str else ""
    return f"{prefix}कुल {format_rupees(card.total_paise)}. {delivery_str}{PHRASAL_AFFIRMATION_PROMPT}"


def classify_reply(text: str) -> ReplyClass:
    """Classify customer speech into accept, correction, reject, or unclear.
    
    Recognizes both elicited 3-word phrasal affirmations and legacy affirmations,
    while enforcing strict negation priority and refusing ambiguous discourse markers.
    """
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
