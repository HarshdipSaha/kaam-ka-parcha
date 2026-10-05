from __future__ import annotations

from datetime import date, datetime, timezone
import pytest
from fastapi.testclient import TestClient

from parcha.app import AppServices, create_app
from parcha.config import Settings
from parcha.schema import Delivery, Evidence, JobCard, LineItem
from parcha.session import SessionStore
from parcha.workflow import Workflow


def make_test_card() -> JobCard:
    return JobCard(
        items=[
            LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=45000),
            LineItem(id="labour-1", label="labour", kind="labour", amount_paise=20000),
        ],
        delivery=Delivery(date=date(2026, 10, 5), window="evening", spoken="Somvaar shaam tak"),
        evidence=[
            Evidence(field="items.part-1.label", quote="front brake pad", review_score=0.95),
            Evidence(field="items.part-1.amount_paise", quote="₹450", review_score=0.95),
            Evidence(field="items.labour-1.label", quote="labour", review_score=0.95),
            Evidence(field="items.labour-1.amount_paise", quote="₹200", review_score=0.95),
            Evidence(field="delivery", quote="Somvaar shaam tak", review_score=0.9),
        ],
    )


class FakePrisma:
    def __init__(self):
        self.calls: list[tuple[bytes, str, list[str] | None, float]] = []

    def transcribe(
        self,
        wav: bytes,
        *,
        mode: str,
        bias: list[str] | None = None,
        score: float = 1.0,
    ) -> str:
        self.calls.append((wav, mode, bias, score))
        if len(self.calls) > 2:
            return "₹500" if mode == "transcribe" else "paanch sau"
        return (
            "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
            if mode == "transcribe"
            else "front brake pad saade chaar sau labour do sau Somvaar shaam tak"
        )


class FakeExtractor:
    def extract_card(
        self, normalized: str, verbatim: str, recorded_at_utc: datetime
    ) -> JobCard:
        return make_test_card()

    def extract_field(
        self,
        field: str,
        transcript: str,
        old_card: JobCard,
        when: datetime | None = None,
    ) -> JobCard:
        if field == "items.part-1.amount_paise":
            new_items = []
            for item in old_card.items:
                if item.id == "part-1":
                    new_items.append(
                        LineItem(
                            id=item.id,
                            label=item.label,
                            kind=item.kind,
                            amount_paise=50000,
                        )
                    )
                else:
                    new_items.append(item)
            evidence = list(old_card.evidence)
            evidence.append(
                Evidence(
                    field="items.part-1.amount_paise",
                    quote="₹500",
                    review_score=0.95,
                )
            )
            return JobCard(
                items=tuple(new_items),
                delivery=old_card.delivery,
                evidence=tuple(evidence),
            )
        elif field == "items.part-1.label":
            new_items = []
            for item in old_card.items:
                if item.id == "part-1":
                    new_items.append(
                        LineItem(
                            id=item.id,
                            label="rear brake pad",
                            kind=item.kind,
                            amount_paise=item.amount_paise,
                        )
                    )
                else:
                    new_items.append(item)
            evidence = list(old_card.evidence)
            evidence.append(
                Evidence(
                    field="items.part-1.label",
                    quote="rear brake pad",
                    review_score=0.95,
                )
            )
            return JobCard(
                items=tuple(new_items),
                delivery=old_card.delivery,
                evidence=tuple(evidence),
            )
        elif field == "delivery":
            new_delivery = Delivery(
                date=date(2026, 10, 6),
                window="morning",
                spoken="Mangalvaar subah",
            )
            evidence = list(old_card.evidence)
            evidence.append(
                Evidence(
                    field="delivery",
                    quote="Mangalvaar subah",
                    review_score=0.95,
                )
            )
            return JobCard(
                items=old_card.items,
                delivery=new_delivery,
                evidence=tuple(evidence),
            )
        raise ValueError(f"Unexpected field: {field}")


class FakeTimbreClient:
    def __init__(self):
        self.calls: list[str] = []

    def synthesize(self, text: str) -> bytes:
        self.calls.append(text)
        return b"RIFFfakeaudio"


@pytest.fixture
def fake_services() -> AppServices:
    settings = Settings(
        api_key="test-api-key",
        extractor_base_url="https://api.groq.com/openai/v1",
        extractor_api_key="test-extractor-key",
        extractor_model="llama-3.3-70b-versatile",
        gnani_base_url="https://api.vachana.ai",
        tts_voice="Nalini",
    )
    store = SessionStore()
    prisma = FakePrisma()
    extractor = FakeExtractor()
    workflow = Workflow(
        store=store,
        prisma=prisma,
        extractor=extractor,
        normalize_audio=lambda blob, mime: b"RIFFfakepcm",
    )
    timbre = FakeTimbreClient()
    return AppServices(settings, store, workflow, timbre)


@pytest.fixture
def client(fake_services: AppServices) -> TestClient:
    app = create_app(fake_services)
    return TestClient(app)
