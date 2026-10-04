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
