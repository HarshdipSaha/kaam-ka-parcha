from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LineItem(StrictModel):
    id: str = Field(pattern=r"^[a-z]+-[0-9]+$")
    label: str | None = Field(default=None, max_length=80)
    kind: Literal["part", "labour"]
    amount_paise: int | None = Field(default=None, ge=0, le=10_000_000)

    @field_validator("amount_paise", mode="before")
    @classmethod
    def amount_must_be_an_integer(cls, value: object) -> object:
        """Reject JSON coercions so an extractor typo cannot change a total."""
        if value is None:
            return value
        if type(value) is not int:
            raise ValueError("amount_paise must be an integer")
        return value

    @field_validator("label")
    @classmethod
    def nonblank_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("blank item label")
        return value


class Delivery(StrictModel):
    date: date
    window: Literal["morning", "afternoon", "evening"]
    spoken: str = Field(min_length=1)


class Evidence(StrictModel):
    field: str
    quote: str
    review_score: float = Field(ge=0, le=1)


class JobCard(StrictModel):
    items: tuple[LineItem, ...] = Field(min_length=1)
    delivery: Delivery | None = None
    evidence: tuple[Evidence, ...]

    @model_validator(mode="after")
    def unique_ids(self) -> "JobCard":
        if len({item.id for item in self.items}) != len(self.items):
            raise ValueError("duplicate item id")
        return self

    @property
    def maybe_total_paise(self) -> int | None:
        if any(item.amount_paise is None for item in self.items):
            return None
        return sum(item.amount_paise for item in self.items if item.amount_paise is not None)

    @property
    def total_paise(self) -> int:
        value = self.maybe_total_paise
        if value is None:
            raise ValueError("total unavailable until all amounts are present")
        return value

    @property
    def needs_review(self) -> bool:
        return bool(review_fields(self))


def review_fields(card: JobCard) -> list[str]:
    evidenced = {
        item.field
        for item in card.evidence
        if item.quote.strip() and item.review_score >= 0.8
    }
    missing: list[str] = []
    for item in card.items:
        for field in ("label", "amount_paise"):
            path = f"items.{item.id}.{field}"
            if getattr(item, field) is None or path not in evidenced:
                missing.append(path)
    if card.delivery is None or "delivery" not in evidenced:
        missing.append("delivery")
    return missing


class TranscriptLog(StrictModel):
    role: Literal["mechanic", "customer", "system"]
    mode: str
    text: str
    recorded_at_utc: datetime
    audio_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
