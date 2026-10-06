"""Score whether Prisma hears the amounts spoken in a Timbre read-back."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Mapping, Sequence

from parcha.numerals import parse_amounts
from parcha.readback import make_readback
from parcha.schema import JobCard

AmountStyle = Literal["digits", "words"]


@dataclass(frozen=True)
class EchoRow:
    card_id: str
    voice: str
    style: AmountStyle
    condition: str
    expected_paise: tuple[int, ...]
    heard_paise: tuple[int, ...]
    transcript: str
    passed: bool
    tts_ms: float


def expected_sequence(card: JobCard) -> tuple[int, ...]:
    """Return item amounts followed by their computed total, in spoken order."""
    item_amounts = tuple(item.amount_paise for item in card.items)
    if any(amount is None for amount in item_amounts):
        raise ValueError("echo cards must have an amount for every item")
    return (*item_amounts, card.total_paise)  # type: ignore[misc]


def score_echo(card: JobCard, transcript: str | None) -> tuple[tuple[int, ...], bool]:
    """Parse a transcript and pass only when every amount matches the read-back."""
    if not transcript or not transcript.strip():
        return (), False

    mentions = parse_amounts(transcript)
    heard = tuple(mention.paise for mention in mentions if mention.status == "complete")
    has_incomplete = any(mention.status != "complete" for mention in mentions)
    return heard, not has_incomplete and heard == expected_sequence(card)


def run_echo(
    cards: Mapping[str, JobCard],
    voices: list[str] | tuple[str, ...],
    styles: list[AmountStyle] | tuple[AmountStyle, ...],
    conditions: list[str] | tuple[str, ...],
    *,
    synthesize: Callable[[str, str], tuple[bytes, float]],
    degrade: Callable[[bytes, str], bytes],
    transcribe: Callable[[bytes], str],
    on_row: Callable[[EchoRow], None] | None = None,
    on_case: Callable[[Sequence[EchoRow], Mapping[str, bytes]], None] | None = None,
    on_case_audio: Callable[[str, str, AmountStyle, Mapping[str, bytes]], None] | None = None,
    on_tts_attempt: Callable[[str, str, AmountStyle, int], None] | None = None,
) -> list[EchoRow]:
    """Synthesize once per card/voice/style and score each audio condition."""
    rows: list[EchoRow] = []
    for card_id, card in cards.items():
        expected = expected_sequence(card)
        for voice in voices:
            for style in styles:
                text = make_readback(card, amount_style=style)
                if on_tts_attempt is not None:
                    on_tts_attempt(card_id, voice, style, len(text))
                original_audio, tts_ms = synthesize(text, voice)
                case_rows: list[EchoRow] = []
                case_audio = {
                    condition: original_audio if condition == "control" else degrade(original_audio, condition)
                    for condition in conditions
                }
                if on_case_audio is not None:
                    on_case_audio(card_id, voice, style, case_audio)
                for condition in conditions:
                    audio = case_audio[condition]
                    transcript = transcribe(audio)
                    heard, passed = score_echo(card, transcript)
                    row = EchoRow(
                        card_id=card_id,
                        voice=voice,
                        style=style,
                        condition=condition,
                        expected_paise=expected,
                        heard_paise=heard,
                        transcript=transcript,
                        passed=passed,
                        tts_ms=tts_ms,
                    )
                    rows.append(row)
                    case_rows.append(row)
                    if on_row is not None:
                        on_row(row)
                if on_case is not None:
                    on_case(tuple(case_rows), case_audio)
    return rows
