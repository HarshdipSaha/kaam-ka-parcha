"""Mask personal identifiers before text leaves the process for an external language model.

Only identifiers a job card never needs are masked: Indian mobile numbers, 12-digit Aadhaar numbers and PAN codes.
Rupee amounts, item labels and dates pass through untouched. A digit run directly after a rupee sign or "Rs" is
left alone, so an amount is never rewritten. Number plates are NOT masked: they can be card evidence.
"""
from __future__ import annotations

import re

_MONEY_PREFIX = r"(?<![₹\d])(?<!Rs )(?<!Rs\.)(?<!Rs)"
_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), "[PAN]"),
    (re.compile(_MONEY_PREFIX + r"\b\d{4}[ -]\d{4}[ -]\d{4}\b"), "[AADHAAR]"),
    (re.compile(_MONEY_PREFIX + r"\b\d{12}\b"), "[AADHAAR]"),
    (re.compile(_MONEY_PREFIX + r"(?:\+?91[ -]?)?\b[6-9]\d{4}[ -]?\d{5}\b"), "[PHONE]"),
)


def mask_pii(text: str) -> str:
    for pattern, token in _PATTERNS:
        text = pattern.sub(token, text)
    return text
