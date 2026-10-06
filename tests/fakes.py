from parcha.config import Settings

INTAKE_T = "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
INTAKE_V = "front brake pad saade chaar sau labour do sau Somvaar shaam tak"


class ScriptedPrisma:
    """Fake Prisma returning scripted outputs in call order; an Exception entry is raised instead."""

    def __init__(self, script):
        self.script, self.calls = list(script), []

    def transcribe(self, wav, *, mode, bias=None, score=1.0):
        self.calls.append((wav, mode, bias, score))
        if not self.script:
            raise AssertionError(f"unexpected extra Prisma call (mode={mode})")
        out = self.script.pop(0)
        if isinstance(out, Exception):
            raise out
        return out


def fake_settings() -> Settings:
    """Offline Settings for every app fixture, unit and browser."""
    return Settings(
        api_key="test-api-key",
        extractor_base_url="http://localhost:8080/v1",
        extractor_api_key="test-extractor-key",
        extractor_model="gnani-evon-v3.3",
        extractor_provider="evon",
        gnani_base_url="https://api.vachana.ai",
        tts_voice="Nalini",
    )


class SilentTimbre:
    """Fake Timbre: one second of 8 kHz mu-law silence, so browsers get a playable WAV."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def synthesize(self, text: str) -> bytes:
        self.calls.append(text)
        return bytes([0xFF]) * 8000


class StagePrisma:
    """Fake Prisma for browser tests: answers by pass mode, not by call order.

    Every intake makes a transcribe and a verbatim pass, and browser flows can retry, so call-order
    scripts are brittle here. `say()` makes every pass hear the same words, which is what a customer
    reply or a mechanic re-ask needs.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[bytes, str]] = []
        self.reset()

    def reset(self) -> None:
        self.by_mode = {"transcribe": INTAKE_T, "verbatim": INTAKE_V}
        self.heard: str | None = None

    def script_intake(self, *, transcribe: str, verbatim: str) -> None:
        self.by_mode = {"transcribe": transcribe, "verbatim": verbatim}

    def say(self, text: str) -> None:
        self.heard = text

    def transcribe(self, wav: bytes, *, mode: str, bias=None, score: float = 1.0) -> str:
        self.calls.append((wav, mode))
        if self.heard is not None:
            return self.heard
        return self.by_mode.get(mode, self.by_mode["verbatim"])
