from __future__ import annotations

from collections import defaultdict, deque
from random import Random
from typing import Any


MIN_UTTERANCE_SECONDS = 6.0
MAX_UTTERANCE_SECONDS = 22.0


def select_indiccontext_rows(
    rows: list[dict[str, Any]], *, limit: int, seed: int = 20261005
) -> list[dict[str, Any]]:
    """Select a duration-bounded, speaker-disjoint sample across domain/style/mixing strata."""
    if limit < 1:
        raise ValueError("limit must be positive")

    grouped: dict[tuple[str, str, bool], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        try:
            duration = float(row.get("duration"))
        except (TypeError, ValueError):
            continue
        audio = row.get("audio")
        if not MIN_UTTERANCE_SECONDS <= duration <= MAX_UTTERANCE_SECONDS:
            continue
        if not isinstance(audio, list) or not audio or not audio[0].get("src"):
            continue
        if not (row.get("reference_text_no_brackets") or "").strip():
            continue
        domain = row.get("domain_name")
        style = row.get("speech_style")
        mixing = row.get("code_mixing")
        if not isinstance(domain, str) or not isinstance(style, str) or not isinstance(mixing, bool):
            continue
        grouped[(domain, style, mixing)].append(row)

    rng = Random(seed)
    buckets: dict[tuple[str, str, bool], deque[dict[str, Any]]] = {}
    for key in sorted(grouped):
        candidates = list(grouped[key])
        rng.shuffle(candidates)
        buckets[key] = deque(candidates)

    selected: list[dict[str, Any]] = []
    seen_speakers: set[str] = set()
    keys = list(buckets)
    while len(selected) < limit and keys:
        progressed = False
        for key in list(keys):
            bucket = buckets[key]
            while bucket:
                row = bucket.popleft()
                speaker = str(row.get("speaker_id") or row.get("file_name") or "")
                if not speaker or speaker in seen_speakers:
                    continue
                seen_speakers.add(speaker)
                selected.append(row)
                progressed = True
                break
            if not bucket:
                keys.remove(key)
            if len(selected) >= limit:
                break
        if not progressed:
            break

    return selected
