from dataclasses import dataclass


class BudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class CreditPlan:
    credits_per_stt_second: float
    remaining_credits: float
    clips: int
    codecs: int
    snrs: int
    seconds_per_clip: float
    intake_seconds: float = 0
    reply_seconds: float = 0
    tts_credits: float = 0

    @property
    def grid_credits(self) -> float:
        return self.clips * self.codecs * self.snrs * self.seconds_per_clip * self.credits_per_stt_second

    @property
    def total_credits(self) -> float:
        extra = (self.intake_seconds + self.reply_seconds) * self.credits_per_stt_second
        return self.grid_credits + extra + self.tts_credits

    def require_under_cap(self, cap: float) -> None:
        if min(cap, self.remaining_credits) < self.total_credits:
            raise BudgetExceeded(f"forecast {self.total_credits:.1f} exceeds cap/remaining credits")


def count_exact_amounts(
    expected: list[int | None], predicted: list[int | None]
) -> tuple[int, int]:
    matches = 0
    total = 0
    for i, exp in enumerate(expected):
        if exp is not None:
            total += 1
            if i < len(predicted) and exp == predicted[i]:
                matches += 1
    return (matches, total)


def drop_rate(replies: list[str]) -> tuple[int, int]:
    dropped = sum(1 for r in replies if r is None or not str(r).strip())
    return (dropped, len(replies))


def hallucinated_word_rate(transcripts: list[str]) -> tuple[int, int]:
    total_words = sum(len(str(t).split()) for t in transcripts if t)
    return (total_words, len(transcripts))
