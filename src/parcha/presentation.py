"""Display helpers for templates and the session payload. Display only: money stays integer paise."""
from __future__ import annotations

import hashlib
from collections.abc import Sequence

from .schema import Delivery, TranscriptLog

HINDI_WEEKDAYS = ("सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार")  # date.weekday() order
HINDI_MONTHS = ("जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून",
                "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर")
WINDOW_HI = {"morning": "सुबह", "afternoon": "दोपहर", "evening": "शाम"}
KIND_HI = {"part": "पार्ट", "labour": "लेबर"}
STATUS_HI = {
    "draft": "कच्चा पर्चा",
    "review": "जाँच बाकी",
    "awaiting_reply": "ग्राहक का जवाब बाकी",
    "fallback_ready": "बटन से पुष्टि",
    "confirmed": "मंज़ूर",
}


def _group_indian(n: int) -> str:
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    groups: list[str] = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return ",".join([*groups, tail])


def format_inr(paise: int | None) -> str:
    if paise is None:
        return "₹ —"
    if isinstance(paise, bool) or not isinstance(paise, int):
        raise TypeError("amount must be integer paise")
    sign = "-" if paise < 0 else ""
    rupees, rem = divmod(abs(paise), 100)
    text = f"{sign}₹{_group_indian(rupees)}"
    return f"{text}.{rem:02d}" if rem else text


def hindi_delivery(delivery: Delivery | None) -> str:
    if delivery is None:
        return "अभी तय नहीं"
    d = delivery.date
    return f"{HINDI_WEEKDAYS[d.weekday()]}, {d.day} {HINDI_MONTHS[d.month - 1]} · {WINDOW_HI[delivery.window]}"


def kind_label(kind: str) -> str:
    return KIND_HI.get(kind, kind)


def status_label(status: str) -> str:
    return STATUS_HI.get(status, status)


def parcha_no(session_id: str) -> str:
    """Six-digit serial for the slip, like the red number on a bill book. Stable per session."""
    return f"{int(hashlib.sha256(session_id.encode('utf-8')).hexdigest(), 16) % 1_000_000:06d}"


def latest_log_text(logs: Sequence[TranscriptLog], *, role: str, mode: str | None = None) -> str | None:
    for log in reversed(logs):
        if log.role == role and (mode is None or log.mode == mode):
            return log.text
    return None


def register_filters(env) -> None:
    env.filters.update(inr=format_inr, hindi_delivery=hindi_delivery, kind_hi=kind_label, status_hi=status_label)
