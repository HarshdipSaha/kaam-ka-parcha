"""Browser-test seam: one in-process server on the offline fakes; Chromium with a fake microphone."""
from __future__ import annotations

import socket
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

try:
    import playwright  # noqa: F401
    import uvicorn
except ImportError:  # the e2e extra is not installed: skip this folder entirely
    collect_ignore_glob = ["test_*.py"]
else:
    from parcha.app import AppServices, create_app
    from parcha.schema import Evidence, JobCard, LineItem
    from parcha.session import SessionStore
    from parcha.workflow import Workflow
    from tests.conftest import FakeExtractor
    from tests.fakes import SilentTimbre, StagePrisma, fake_settings

    class StageExtractor(FakeExtractor):
        """FakeExtractor whose first label a browser test can make hostile or very long."""

        LABELS = {
            "hostile_label": '<img src=x onerror="window.__xss=1">front brake pad',
            "long_label": "फ्रंट सस्पेंशन शॉक एब्ज़ॉर्बर असेंबली (बायाँ) front brake pad",
        }

        def __init__(self) -> None:
            self.mode = "complete"

        def extract_card(self, normalized, verbatim, recorded_at_utc):
            card = super().extract_card(normalized, verbatim, recorded_at_utc)
            label = self.LABELS.get(self.mode)
            if label is None:
                return card
            items = tuple(
                LineItem(id=i.id, label=label if i.id == "part-1" else i.label, kind=i.kind, amount_paise=i.amount_paise)
                for i in card.items
            )
            evidence = tuple(
                Evidence(field=e.field, quote=label if e.field == "items.part-1.label" else e.quote,
                         review_score=e.review_score)
                for e in card.evidence
            )
            return JobCard(items=items, delivery=card.delivery, evidence=evidence)

FAKE_MEDIA = [
    "--use-fake-ui-for-media-stream",
    "--use-fake-device-for-media-stream",
    "--autoplay-policy=no-user-gesture-required",
]


@dataclass
class World:
    url: str
    services: object
    prisma: object
    extractor: object


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def world():
    prisma, extractor, store = StagePrisma(), StageExtractor(), SessionStore()
    timbre = SilentTimbre()
    workflow = Workflow(
        store=store, prisma=prisma, extractor=extractor, timbre=timbre,
        normalize_audio=lambda blob, mime, sample_rate=8000: b"RIFFfakepcm",
    )
    services = AppServices(fake_settings(), store, workflow, timbre)
    app = create_app(services)
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("e2e server did not start")
        time.sleep(0.05)
    yield World(f"http://127.0.0.1:{port}", services, prisma, extractor)
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(scope="session")
def base_url(world):  # overrides pytest-base-url, so page.goto("/workshop") works
    return world.url


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {**browser_type_launch_args, "args": [*browser_type_launch_args.get("args", []), *FAKE_MEDIA]}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 360, "height": 800},
        "has_touch": True,
        "locale": "hi-IN",
        "permissions": ["microphone", "clipboard-read", "clipboard-write"],
    }


@pytest.fixture(autouse=True)
def fresh_world(world):
    world.prisma.reset()
    world.extractor.mode = "complete"
    Path("var/e2e").mkdir(parents=True, exist_ok=True)
    yield
