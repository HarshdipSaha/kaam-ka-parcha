"""Score annotated rupee amounts against Prisma transcripts of long, real workshop speech.

The videos are public YouTube mechanic walk-throughs (private audio under var/, never committed). Annotations list the
prices a viewer is told, not every number spoken, so this reports recall of annotated amounts plus counts, never a
precision or an absolute error rate.
"""

from __future__ import annotations

from dataclasses import dataclass
import io
from typing import Iterable, Mapping, Sequence
import wave

from parcha.money import normalise_transcribe_fractions
from parcha.numerals import parse_amounts

CHUNK_SECONDS = 25.0
OVERLAP_SECONDS = 2.0


def split_wav(wav: bytes, chunk_seconds: float = CHUNK_SECONDS, overlap_seconds: float = OVERLAP_SECONDS) -> list[bytes]:
    """REST-safe PCM chunks with a short overlap so an amount spoken on a boundary survives in one chunk."""
    with wave.open(io.BytesIO(wav), "rb") as src:
        rate, width, channels = src.getframerate(), src.getsampwidth(), src.getnchannels()
        frames = src.readframes(src.getnframes())
    step = int((chunk_seconds - overlap_seconds) * rate) * width * channels
    size = int(chunk_seconds * rate) * width * channels
    chunks = []
    for start in range(0, max(len(frames), 1), step):
        piece = frames[start : start + size]
        if not piece:
            break
        out = io.BytesIO()
        with wave.open(out, "wb") as dst:
            dst.setnchannels(channels)
            dst.setsampwidth(width)
            dst.setframerate(rate)
            dst.writeframes(piece)
        chunks.append(out.getvalue())
        if start + size >= len(frames):
            break
    return chunks


def amounts(text: str, *, transcribe_pass: bool = False) -> set[int]:
    """Complete rupee amounts in a transcript, in paise."""
    if transcribe_pass:
        text = normalise_transcribe_fractions(text)
    return {m.paise for m in parse_amounts(text) if m.status == "complete" and m.paise}


@dataclass(frozen=True)
class ChunkResult:
    verbatim: str
    transcribe: str

    def heard(self) -> set[int]:
        return amounts(self.verbatim)

    def agreed(self) -> set[int]:
        """Amounts both passes hear in this chunk: the strongest single-recording evidence available."""
        return amounts(self.verbatim) & amounts(self.transcribe, transcribe_pass=True)


def score_case(expected_paise: Iterable[int], chunks: Sequence[ChunkResult]) -> dict:
    expected = sorted({p for p in expected_paise if p})
    heard_verbatim: set[int] = set().union(*[c.heard() for c in chunks]) if chunks else set()
    heard_transcribe: set[int] = set().union(*[amounts(c.transcribe, transcribe_pass=True) for c in chunks]) if chunks else set()
    agreed: set[int] = set().union(*[c.agreed() for c in chunks]) if chunks else set()
    return {
        "expected": len(expected),
        "recovered_verbatim": sum(p in heard_verbatim for p in expected),
        "recovered_transcribe": sum(p in heard_transcribe for p in expected),
        "recovered_agreed": sum(p in agreed for p in expected),
        "missed": [p for p in expected if p not in heard_verbatim and p not in heard_transcribe],
        "distinct_amounts_heard_verbatim": len(heard_verbatim),
        "distinct_amounts_agreed": len(agreed),
        "chunks": len(chunks),
    }


def summarize(cases: Iterable[Mapping]) -> dict:
    cases = list(cases)
    total = sum(c["expected"] for c in cases)
    return {
        "cases": len(cases),
        "expected_amounts": total,
        **{key: sum(c[key] for c in cases) for key in ("recovered_verbatim", "recovered_transcribe", "recovered_agreed")},
    }
