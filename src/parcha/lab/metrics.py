from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
import unicodedata

from parcha.workflow import classify_reply

__all__ = [
    "amount_match",
    "cer",
    "hallucinated_words",
    "normalize",
    "short_reply_drop",
]

AMOUNT_PATTERN = re.compile(
    r"(?:₹\s*|rs\.?\s*|inr\s*)?([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)(?:\s*(?:रुपये|rupaye|rupees?|rs\.?|inr|/-|/))?",
    re.IGNORECASE,
)

HINDI_AMOUNT_WORDS = {
    "चार सौ पचास": 450,
    "छह सौ पचास": 650,
    "छः सौ पचास": 650,
    "दो सौ": 200,
    "तीन सौ": 300,
    "चार सौ": 400,
    "पाँच सौ": 500,
    "पांच सौ": 500,
    "छह सौ": 600,
    "सात सौ": 700,
    "सात सौ पचास": 750,
    "आठ सौ": 800,
    "नौ सौ": 900,
    "हज़ार": 1000,
    "हजार": 1000,
    "एक हज़ार": 1000,
    "एक हजार": 1000,
    "बारह सौ": 1200,
    "दो हज़ार पचास": 2050,
    "दो हजार पचास": 2050,
    "पचास": 50,
    "एक लाख": 100000,
    "एक करोड़": 10000000,
}

ROMAN_AMOUNT_WORDS = {
    "saade chaar sau": 450,
    "pachaas": 50,
    "do sau": 200,
    "saat sau pachaas": 750,
    "ek hazaar": 1000,
    "baarah sau": 1200,
    "do hazaar pachaas": 2050,
    "paanch sau": 500,
    "ek lakh": 100000,
    "ek crore": 10000000,
}


def normalize(text: str) -> str:
    """Normalize text using NFKC unicode normalization, casefolding and collapsing whitespace."""
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def cer(reference: str, hypothesis: str) -> float:
    """Calculate Character Error Rate (CER) using Levenshtein distance."""
    ref, hyp = normalize(reference), normalize(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    row = list(range(len(hyp) + 1))
    for i, char in enumerate(ref, 1):
        next_row = [i]
        for j, other in enumerate(hyp, 1):
            next_row.append(
                min(
                    next_row[-1] + 1,
                    row[j] + 1,
                    row[j - 1] + (char != other),
                )
            )
        row = next_row
    return row[-1] / len(ref)


def amount_match(expected_paise: int, hypothesis: str) -> bool:
    """Check if expected_paise matches any extracted rupee amount in hypothesis.

    Extracts rupee numbers from hypothesis (e.g. ₹450, 1,000, 450.50 rupaye),
    converts to paise, and returns True if expected_paise matches any extracted amount.
    """
    if not hypothesis or expected_paise is None:
        return False

    matches = AMOUNT_PATTERN.finditer(hypothesis)
    for m in matches:
        raw_num = m.group(1)
        if not raw_num:
            continue
        clean_num = raw_num.replace(",", "")
        try:
            dec = Decimal(clean_num)
            paise = int(round(dec * 100))
            if paise == expected_paise:
                return True
        except (InvalidOperation, ValueError):
            continue

    # Also check Devanagari Hindi number phrases
    for phrase, rupees in sorted(HINDI_AMOUNT_WORDS.items(), key=lambda x: -len(x[0])):
        if phrase in hypothesis:
            if rupees * 100 == expected_paise:
                return True

    # Also check Romanized Hindi phrases
    norm_hyp = normalize(hypothesis)
    for phrase, rupees in sorted(ROMAN_AMOUNT_WORDS.items(), key=lambda x: -len(x[0])):
        if phrase in norm_hyp:
            if rupees * 100 == expected_paise:
                return True

    return False


def short_reply_drop(expected_reply: str, hypothesis: str) -> bool:
    """Evaluate whether a short reply was dropped or misclassified.

    If expected_reply is acceptance (e.g. 'haan', 'accept'), returns True if
    classify_reply(hypothesis) != 'accept'.
    If expected_reply is rejection/correction, returns True if
    classify_reply(hypothesis) not in ('reject', 'correction').
    If hypothesis is empty, returns True.
    """
    if not hypothesis or not hypothesis.strip():
        return True

    hyp_class = classify_reply(hypothesis)
    exp_norm = normalize(expected_reply)

    # Check if expected reply is acceptance
    is_accept = (
        exp_norm in {"accept", "acceptance", "haan", "han", "हाँ", "हां", "yes"}
        or classify_reply(expected_reply) == "accept"
    )
    if is_accept:
        return hyp_class != "accept"

    # Check if expected reply is rejection or correction
    is_reject_or_correct = (
        exp_norm in {"reject", "rejection", "correction", "nahi", "nahin", "नहीं", "ना", "no"}
        or classify_reply(expected_reply) in {"reject", "correction"}
    )
    if is_reject_or_correct:
        return hyp_class not in ("reject", "correction")

    # Fallback to direct classification comparison
    return hyp_class != classify_reply(expected_reply)


def hallucinated_words(hypothesis: str | None) -> int:
    """Return count of words in hypothesis (used for silence/noise-only evaluation)."""
    if not hypothesis:
        return 0
    return len(hypothesis.strip().split())
