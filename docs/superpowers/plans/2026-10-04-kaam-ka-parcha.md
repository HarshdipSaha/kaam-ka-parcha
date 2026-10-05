# Kaam ka Parcha Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a two-browser demo in which a mechanic speaks a Hinglish estimate, a customer hears it through a measured simulated 8 kHz line, corrects or confirms the amount, and receives a confirmed PDF and WhatsApp-ready text; ship a budgeted Line Noise Lab that evaluates the same audio path.

**Architecture:** A local FastAPI service owns short-lived, revisioned sessions. Browser recordings are converted by FFmpeg, Prisma REST runs the two workshop transcription passes and the customer reply pass, and a schema-checked external extractor fills only spoken fields. A pure state machine guards confirmation; the shared audio module supplies both the product and the lab, while PDF/text render from a frozen confirmed snapshot.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, httpx, Jinja2, MediaRecorder, FFmpeg, NumPy, ReportLab, pypdf, pytest. PowerShell commands below assume Windows and this repository root.

**Spec:** `docs/ideas/spec.md` is authoritative. API details to verify live are in `docs/notes/02-speech-apis.md` and `docs/notes/03-sdks-and-integrations.md`.

---

## Scope and decisions to preserve

1. The call is simulated in a second browser/device. No PSTN, Twilio, Exotel, real WhatsApp sending, hosted audio link, or claim of legal signature. Show the spec's disclosure during the customer leg and in video.
2. Use Prisma REST `hi-IN`, `format=transcribe` for ITN and `format=verbatim` plus valid single-word `bias_list` for names. Do not attach a WebSocket VAD header to REST; the WS preset is an experiment in Task 18.
3. Use Timbre `timbre-v2.5`, `hi-IN`, `pcm_mulaw`/`mulaw`, 8 kHz. Degrade the rendered audio and the recorded customer response through the declared codec, SNR and optional frame erasure. A manifest records the *actual* chain.
4. The extractor is an external, configurable OpenAI-compatible API in development. Evon is an optional endpoint/model switch after demo-day testing. Offline tests use a fake; no deterministic fake is represented as live extraction.
5. Store money in paise. A draft line item may have a missing label or amount, and a draft delivery may be missing; the total exists only when every amount is present. A correction changes exactly one addressed line item or the delivery field. Ambiguous corrections trigger another question. A confirmation seals the exact revision last read aloud.
6. Scores are extraction review signals supplied with evidence, not calibrated Prisma probabilities. Missing evidence, score below 0.8, uncertain date, missing label/amount/delivery or invalid totals stop the workflow and ask again.
7. All demo identities and recordings are synthetic/scripted with consent. Raw recordings, private metrics, API keys and certificates live under ignored `var/` or `.env`.
8. Public numbers are only our own labelled pipeline deltas/end-to-end outcomes after a written organizer answer. Absolute WER/CER curves stay private/interview-only. Never include another vendor comparison.

The tracked spec differs from the untracked `aidlc-docs/inception/` notes on QR/audio hosting, real delivery, and "legally confirmed" wording. These are outside this implementation.

## File structure and contracts

```text
pyproject.toml                         package and pytest config
.env.example / .gitignore              safe config and generated-file exclusions
src/parcha/__init__.py
src/parcha/config.py                   Settings; no secret in logs
src/parcha/gnani.py                    Prisma/Timbre HTTP clients only
src/parcha/gnani_ws.py                 bounded 8 kHz telephony WS probe for gates
src/parcha/credits.py                  credit forecast and no-overspend guard
src/parcha/audio.py                    conversion, codec, noise, frame erasure
src/parcha/schema.py                   LineItem, Delivery, JobCard, evidence, logs
src/parcha/session.py                  in-memory optimistic revision store
src/parcha/extract.py                  OpenAI-compatible extraction and validation
src/parcha/workflow.py                 intake, read-back, correction, confirmation
src/parcha/artefact.py                 sealed PDF and text
src/parcha/app.py                      routes and dependency wiring
src/parcha/templates/workshop.html    workshop controls and review
src/parcha/templates/customer.html    customer playback and reply
src/parcha/static/app.js              MediaRecorder and small API helpers
src/parcha/lab/__init__.py
src/parcha/lab/dataset.py             validated JSONL manifest and audio paths
src/parcha/lab/metrics.py             CER, entity match, drop, hallucination
src/parcha/lab/runner.py              budgeted codec × SNR × loss sweep
src/parcha/lab/report.py              private tables and guarded public deltas
data/synthcall_manifest.jsonl          committed synthetic text/reference manifest
scripts/probe_api.py                   one paid STT and TTS call
scripts/early_gates.py                 Oct 7–10 bounded gate clips
scripts/ws_flush_probe.py              isolated 8 kHz WS experiment
assets/README.md / assets/street_noise.wav   attributed test ambience
assets/fonts/                         bundled licensed PDF font if needed
tests/test_*.py                        offline contract and state tests
docs/gates.md / docs/demo.md          measured decisions and 60-second script
```

`gnani.py` knows HTTP but no job-card concepts. `audio.py` knows PCM/FFmpeg but no HTTP. `schema.py` and `session.py` know neither. `workflow.py` composes them through injected objects. The lab imports `audio.py` and `gnani.py`, so it evaluates the actual chain rather than a second approximation.

## Execution rules

- Run commands from `H:\augsepthacks\gnani intern`. `$PY = '.\.venv\Scripts\python.exe'` is used in PowerShell snippets; invoke `& $PY ...`.
- Each code task follows @test-driven-development: paste the test shown, run the named test and observe the expected failure, paste the minimum implementation, run it green, then commit. Tests must never spend credits.
- The code blocks give exact contracts and representative complete functions. Where a task combines several files, finish one red/green pair at a time; do not copy all code before running the first test.
- Never run a live command without `--live`. Every paid loop uses measured rates and a `--max-credits` ceiling. If a gate fails, record raw numerator/denominator and take the spec's stated pivot.
- Use @verification-before-completion at the end. Do not claim an unrun live gate passed.

### Task 1: Package, configuration and offline health route

**Files:** Create `pyproject.toml`, `src/parcha/__init__.py`, `src/parcha/config.py`, `src/parcha/app.py`, `tests/test_config.py`; modify `.gitignore`, `.env.example`.

- [ ] **Step 1: Write `pyproject.toml`.** This is enough for editable installation and test discovery:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "kaam-ka-parcha"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.110", "uvicorn>=0.29", "pydantic>=2.6",
  "httpx>=0.27", "python-dotenv>=1.0", "python-multipart>=0.0.9",
  "jinja2>=3.1", "numpy>=1.26", "reportlab>=4.0", "pypdf>=4.0",
  "websockets>=13.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
parcha = ["templates/*.html", "static/*.js"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Write ignore/config files.** Preserve existing `.gitignore` entries; append:

```gitignore
.venv/
.pytest_cache/
*.egg-info/
.env
*.pem
*.key
var/
```

Put placeholders only in `.env.example`:

```dotenv
API_KEY=replace_me
EXTRACTOR_BASE_URL=https://your-openai-compatible-host/v1
EXTRACTOR_API_KEY=replace_me
EXTRACTOR_MODEL=your-model
EXTRACTOR_PROVIDER=external
TTS_VOICE=Nalini
```

- [ ] **Step 3: Install and write a failing test.** Create empty `src/parcha/__init__.py`, then run:

```powershell
py -3.12 -m venv .venv
$PY = '.\.venv\Scripts\python.exe'
& $PY -m pip install -e '.[dev]'
```

Create `tests/test_config.py`:

```python
from fastapi.testclient import TestClient
from parcha.app import create_app
from parcha.config import Settings

def test_offline_health_does_not_need_credentials(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    response = TestClient(create_app()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

def test_settings_keep_rest_as_safe_default():
    settings = Settings.from_mapping({"API_KEY": "example"})
    assert settings.gnani_base_url == "https://api.vachana.ai"
    assert settings.reply_transport == "rest"
```

- [ ] **Step 4: Run red.** `& $PY -m pytest tests/test_config.py -q` → collection fails because `parcha.app` and `parcha.config` are absent.

- [ ] **Step 5: Implement configuration and the health route.** `config.py`:

```python
from dataclasses import dataclass
from os import environ
from typing import Mapping
from dotenv import dotenv_values

@dataclass(frozen=True)
class Settings:
    api_key: str = ""
    extractor_base_url: str = ""
    extractor_api_key: str = ""
    extractor_model: str = ""
    extractor_provider: str = "external"
    tts_voice: str = "Nalini"
    gnani_base_url: str = "https://api.vachana.ai"
    reply_transport: str = "rest"

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> "Settings":
        return cls(
            api_key=values.get("API_KEY", ""),
            extractor_base_url=values.get("EXTRACTOR_BASE_URL", ""),
            extractor_api_key=values.get("EXTRACTOR_API_KEY", ""),
            extractor_model=values.get("EXTRACTOR_MODEL", ""),
            extractor_provider=values.get("EXTRACTOR_PROVIDER", "external"),
            tts_voice=values.get("TTS_VOICE", "Nalini"),
        )

    @classmethod
    def load(cls) -> "Settings":
        return cls.from_mapping({**dotenv_values(".env"), **environ})

    def require_gnani(self) -> None:
        if not self.api_key or self.api_key == "replace_me":
            raise ValueError("API_KEY is required for live Gnani calls")

    def require_extractor(self) -> None:
        if not self.extractor_base_url or not self.extractor_model:
            raise ValueError("An extractor endpoint and model are required")
```

`app.py` initially contains:

```python
from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="Kaam ka Parcha")

    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    return app

app = create_app()
```

- [ ] **Step 6: Run green and commit.** `& $PY -m pytest tests/test_config.py -q` → 2 passed. `git add pyproject.toml .gitignore .env.example src/parcha tests/test_config.py; git commit -m "chore: scaffold local parcha service"`.

### Task 2: Prisma and Timbre REST boundaries

**Files:** Create `src/parcha/gnani.py`, `tests/test_gnani.py`.

- [ ] **Step 1: Write the failing request-contract tests.** Create `tests/test_gnani.py`:

```python
import json
import httpx
import pytest
from parcha.gnani import GnaniError, PrismaClient, TimbreClient

def test_prisma_dual_modes_use_documented_multipart_fields():
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"success": True, "transcript": "₹450"})
    http = httpx.Client(transport=httpx.MockTransport(handler))
    client = PrismaClient("test-key", http=http)
    assert client.transcribe(b"RIFFdemo", mode="transcribe") == "₹450"
    assert client.transcribe(b"RIFFdemo", mode="verbatim", bias=["brake"], score=1.0) == "₹450"
    assert all(r.url.path == "/stt/v3" for r in requests)
    assert all(r.headers["x-api-key-id"] == "test-key" for r in requests)
    first, second = (r.content.decode("utf-8", errors="replace") for r in requests)
    assert 'name="format"\r\n\r\ntranscribe' in first
    assert 'name="language_code"\r\n\r\nhi-IN' in first
    assert 'name="format"\r\n\r\nverbatim' in second
    assert 'name="bias_list"' in second and '["brake"]' in second

def test_invalid_bias_is_rejected_before_paid_call():
    client = PrismaClient("test-key", http=httpx.Client())
    with pytest.raises(ValueError, match="single words"):
        client.transcribe(b"RIFFdemo", mode="verbatim", bias=["brake pad"])

def test_timbre_requests_8k_mulaw_and_returns_bytes():
    def handler(request):
        body = json.loads(request.content)
        assert request.url.path == "/api/v1/tts/inference"
        assert body["model"] == "timbre-v2.5"
        assert body["language"] == "hi-IN"
        assert body["audio_config"]["container"] == "mulaw"
        assert body["audio_config"]["sample_rate"] == 8000
        return httpx.Response(200, content=b"\xff" * 8000)
    client = TimbreClient("test-key", http=httpx.Client(transport=httpx.MockTransport(handler)))
    assert len(client.synthesize("कुल ₹650")) == 8000

def test_error_redacts_key():
    http = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(403, json={"success": False})))
    with pytest.raises(GnaniError) as error:
        PrismaClient("secret-value", http=http).transcribe(b"x", mode="transcribe")
    assert "secret-value" not in str(error.value)
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_gnani.py -q` → import failure for `parcha.gnani`.

- [ ] **Step 3: Implement the typed HTTP boundary.** Create `src/parcha/gnani.py`:

```python
import json
import re
from typing import Literal
import httpx

class GnaniError(RuntimeError):
    pass

def _check_response(response: httpx.Response) -> None:
    if response.status_code != 200:
        raise GnaniError(f"Gnani request failed: HTTP {response.status_code}")

class PrismaClient:
    def __init__(self, api_key: str, http: httpx.Client | None = None,
                 base_url: str = "https://api.vachana.ai"):
        self.api_key = api_key
        self.http = http or httpx.Client(timeout=45)
        self.base_url = base_url.rstrip("/")

    def transcribe(self, wav: bytes, *, mode: Literal["transcribe", "verbatim"],
                   bias: list[str] | None = None, score: float = 1.0) -> str:
        words = bias or []
        if words and mode != "verbatim":
            raise ValueError("bias_list requires verbatim mode")
        if len(words) > 100 or any(not re.fullmatch(r"[^\W\d_]+", word, re.UNICODE) for word in words):
            raise ValueError("bias_list must contain at most 100 single words")
        if score not in {0.0, 0.5, 1.0, 1.5, 2.0}:
            raise ValueError("unsupported bias_score")
        data = {"language_code": "hi-IN", "format": mode}
        if words:
            data.update(bias_list=json.dumps(words, ensure_ascii=False), bias_score=str(score))
        response = self.http.post(
            f"{self.base_url}/stt/v3", headers={"X-API-Key-ID": self.api_key},
            data=data, files={"audio_file": ("clip.wav", wav, "audio/wav")})
        _check_response(response)
        payload = response.json()
        if payload.get("success") is not True or not isinstance(payload.get("transcript"), str):
            raise GnaniError("Gnani STT response lacked a transcript")
        return payload["transcript"].strip()  # empty is meaningful for silence tests

class TimbreClient:
    def __init__(self, api_key: str, voice: str = "Nalini", http: httpx.Client | None = None,
                 base_url: str = "https://api.vachana.ai"):
        self.api_key, self.voice = api_key, voice
        self.http = http or httpx.Client(timeout=45)
        self.base_url = base_url.rstrip("/")

    def synthesize(self, text: str) -> bytes:
        if not text.strip():
            raise ValueError("TTS text is empty")
        body = {"text": text, "voice": self.voice, "model": "timbre-v2.5",
                "language": "hi-IN", "speed": 1.0,
                "audio_config": {"sample_rate": 8000, "num_channels": 1,
                                 "sample_width": 2, "encoding": "pcm_mulaw",
                                 "container": "mulaw"}}
        response = self.http.post(f"{self.base_url}/api/v1/tts/inference",
                                  headers={"X-API-Key-ID": self.api_key}, json=body)
        _check_response(response)
        if not response.content or response.headers.get("content-type", "").startswith("application/json"):
            raise GnaniError("Gnani TTS response lacked raw audio")
        return response.content
```

The REST docs say invalid boosting can be silently ignored. Input validation prevents known invalid words, but Task 5 still measures whether the boost actually helps.

- [ ] **Step 4: Run green and commit.** `& $PY -m pytest tests/test_gnani.py -q` → 4 passed. `git add src/parcha/gnani.py tests/test_gnani.py; git commit -m "feat: add Gnani speech REST clients"`.

### Task 3: Credit calculator and single-call probe

**Files:** Create `src/parcha/credits.py`, `scripts/probe_api.py`, `tests/test_credits.py`, `docs/gates.md`.

- [ ] **Step 1: Write a failing credit test.** `tests/test_credits.py`:

```python
import pytest
from parcha.credits import CreditPlan, BudgetExceeded

def test_grid_calculation_includes_reserve():
    plan = CreditPlan(credits_per_stt_second=0.2, remaining_credits=5000,
                      clips=100, codecs=3, snrs=3, seconds_per_clip=6,
                      intake_seconds=60, reply_seconds=300, tts_credits=100)
    assert plan.grid_credits == 1080
    assert plan.total_credits == 1252
    plan.require_under_cap(2000)

def test_overspend_fails_before_first_api_call():
    plan = CreditPlan(credits_per_stt_second=1, remaining_credits=5000,
                      clips=100, codecs=3, snrs=3, seconds_per_clip=6)
    with pytest.raises(BudgetExceeded):
        plan.require_under_cap(2000)
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_credits.py -q` → import failure.

- [ ] **Step 3: Implement exact arithmetic.** `src/parcha/credits.py`:

```python
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
```

- [ ] **Step 4: Run green.** `& $PY -m pytest tests/test_credits.py -q` → 2 passed. If the arithmetic fails, fix it before any paid call.

- [ ] **Step 5: Implement the bounded probe CLI.** `scripts/probe_api.py` uses `argparse` with mandatory `--live` and `--clip`; otherwise it exits before instantiating clients. Validate a WAV duration of 4–8 seconds with `wave`, call `Settings.load().require_gnani()` (the extractor is irrelevant to this probe), prompt for dashboard balance, call Prisma once (`transcribe`), prompt for the next balance, call Timbre once (`कुल ₹650`), prompt for the final balance, and print two credit deltas. Do not write the key, response headers or raw user audio to a log. Errors stop immediately; no automatic retry.

```powershell
& $PY scripts/probe_api.py --live --clip var/gates/six_seconds.wav
```

Expected: two successful calls or a documented HTTP error; `docs/gates.md` receives actual date, clip duration, before/after balances, credits per STT second and per TTS prompt, response format, and unknowns. Never fill it with the test fixture rate `0.2`.

- [ ] **Step 6: Forecast the spec grids.** Run a `python -c` or CLI wrapper around `CreditPlan` using the observed rate for both `100 × 3 × 3` (Oct 6 credit gate) and the planned `100 × 2 × 4` baseline. If either exceeds 2,000 credits including reserved app calls, record the `60 × 2 × 3` reduced grid. Commit: `git add src/parcha/credits.py scripts/probe_api.py tests/test_credits.py docs/gates.md; git commit -m "feat: measure and cap speech credit use"`.

### Task 4: Shared 8 kHz audio conversion and codec chain

**Files:** Create `src/parcha/audio.py`, `tests/test_audio.py`, `assets/README.md`; add `assets/street_noise.wav` only after license/consent is recorded.

- [ ] **Step 1: Write a failing WAV/codec test.** Use a one-second 8 kHz sine generated in memory, not a paid TTS fixture:

```python
import io, wave
import numpy as np
import pytest
from parcha.audio import codec_round_trip, mulaw_to_wav, mix_at_snr

def wav_bytes(samples: np.ndarray) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(8000)
        wav.writeframes(samples.astype("<i2").tobytes())
    return output.getvalue()

def test_g711_roundtrip_is_mono_8k():
    samples = (8000 * np.sin(2 * np.pi * 440 * np.arange(8000) / 8000)).astype("<i2")
    output = codec_round_trip(wav_bytes(samples), "g711")
    with wave.open(io.BytesIO(output), "rb") as wav:
        assert wav.getframerate() == 8000
        assert wav.getnchannels() == 1
        assert len(wav.readframes(8000)) == 16000

def test_timbre_mulaw_decodes_as_8k():
    output = mulaw_to_wav(b"\xff" * 8000)
    with wave.open(io.BytesIO(output), "rb") as wav:
        assert wav.getframerate() == 8000
        assert len(wav.readframes(8000)) == 16000

def test_snr_is_measured_before_clipping():
    speech = wav_bytes(np.full(8000, 2000, dtype=np.int16))
    noise = wav_bytes(np.tile(np.array([-1000, 1000], dtype=np.int16), 4000))
    mixed, measured = mix_at_snr(speech, noise, 5.0)
    assert abs(measured - 5.0) < 0.5
    assert mixed.startswith(b"RIFF")
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_audio.py -q` → `parcha.audio` missing.

- [ ] **Step 3: Add one FFmpeg wrapper.** Use argument arrays, stdin/stdout pipes, a 30-second timeout and a short error message. Do not build a shell string:

```python
import subprocess

class AudioError(RuntimeError):
    pass

def _ffmpeg(input_bytes: bytes, input_args: list[str], output_args: list[str]) -> bytes:
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
               *input_args, "-i", "pipe:0", *output_args, "pipe:1"]
    try:
        result = subprocess.run(command, input=input_bytes, capture_output=True,
                                timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AudioError("FFmpeg unavailable or timed out") from exc
    if result.returncode or not result.stdout:
        raise AudioError(f"FFmpeg conversion failed: {result.stderr.decode(errors='replace')[:300]}")
    return result.stdout

def mulaw_to_wav(data: bytes) -> bytes:
    return _ffmpeg(data, ["-f", "mulaw", "-ar", "8000", "-ac", "1"],
                   ["-ar", "8000", "-ac", "1", "-c:a", "pcm_s16le", "-f", "wav"])

def codec_round_trip(wav: bytes, codec: str) -> bytes:
    if codec == "g711":
        encoded = _ffmpeg(wav, ["-f", "wav"],
                          ["-ar", "8000", "-ac", "1", "-c:a", "pcm_mulaw", "-f", "mulaw"])
        return mulaw_to_wav(encoded)
    if codec == "amr_nb_4750":
        encoded = _ffmpeg(wav, ["-f", "wav"],
                          ["-ar", "8000", "-ac", "1", "-c:a", "libopencore_amrnb",
                           "-b:a", "4.75k", "-f", "amr"])
        return _ffmpeg(encoded, ["-f", "amr"],
                       ["-ar", "8000", "-ac", "1", "-c:a", "pcm_s16le", "-f", "wav"])
    raise ValueError(f"unknown codec: {codec}")
```

- [ ] **Step 4: Add measured noise mixing.** `mix_at_snr(speech_wav, noise_wav, target_db)` decodes both to mono 8 kHz PCM arrays, tiles/crops noise to the speech length, computes `gain = rms(speech) / (rms(noise) * 10**(target_db/20))`, adds the scaled noise, rejects clipping, and writes 16-bit WAV. Return `(wav_bytes, 20*log10(rms_speech/rms_scaled_noise))`. Treat `clean` as no noise, not infinite/zero SNR. The measured SNR is of the added waveform, before codec/output gain; name it precisely in the manifest. Use a separate `_read_pcm(wav_bytes)`/`_write_pcm(samples)` helper that validates mono, 8 kHz and 16-bit PCM:

```python
import io, math, wave
import numpy as np

def _read_pcm(blob: bytes) -> np.ndarray:
    with wave.open(io.BytesIO(blob), "rb") as source:
        if (source.getnchannels(), source.getframerate(), source.getsampwidth()) != (1, 8000, 2):
            raise AudioError("expected mono 8 kHz 16-bit PCM WAV")
        return np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").astype(np.float64)

def _write_pcm(samples: np.ndarray) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as target:
        target.setnchannels(1); target.setframerate(8000); target.setsampwidth(2)
        target.writeframes(samples.astype("<i2").tobytes())
    return output.getvalue()

def mix_at_snr(speech_wav: bytes, noise_wav: bytes, target_db: float) -> tuple[bytes, float]:
    speech, noise = _read_pcm(speech_wav), _read_pcm(noise_wav)
    if not len(speech) or not len(noise):
        raise AudioError("empty speech/noise")
    noise = np.resize(noise, len(speech))
    speech_rms = float(np.sqrt(np.mean(speech ** 2)))
    noise_rms = float(np.sqrt(np.mean(noise ** 2)))
    if speech_rms == 0 or noise_rms == 0:
        raise AudioError("SNR undefined for silent speech/noise")
    scaled = noise * (speech_rms / (noise_rms * 10 ** (target_db / 20)))
    mixed = speech + scaled
    if np.max(np.abs(mixed)) >= 32767:
        raise AudioError("noise mix clipped; lower level and rerun")
    measured = 20 * math.log10(speech_rms / float(np.sqrt(np.mean(scaled ** 2))))
    return _write_pcm(np.rint(mixed)), measured
```

- [ ] **Step 5: Check codec availability and the street sample.** Run `ffmpeg -hide_banner -encoders | Select-String 'pcm_mulaw|libopencore_amrnb'`. Both encoders must be present for the AMR gate; otherwise install a build with AMR-NB support and rerun, or mark the AMR gate unrun. `assets/README.md` records sample origin, license or consent, duration, capture date and that names/plates are absent. Until `assets/street_noise.wav` exists, run unit tests with generated noise and do not claim a street-noise demo.

- [ ] **Step 6: Run green and commit.** `& $PY -m pytest tests/test_audio.py -q` → 3 passed. `git add src/parcha/audio.py tests/test_audio.py assets/README.md; git add assets/street_noise.wav` only if cleared; `git commit -m "feat: share measured telephony audio path"`.

### Task 5: Run the early go/no-go gates before product UI

**Files:** Create `src/parcha/gnani_ws.py`, `scripts/early_gates.py`, `tests/test_early_gates.py`; modify `docs/gates.md`.

- [ ] **Step 1: Write a failing gate-scoring test.** Keep gate arithmetic independent of paid calls:

```python
from parcha.credits import count_exact_amounts, drop_rate, hallucinated_word_rate

def test_gate_denominators_are_explicit():
    assert count_exact_amounts([450, 200, 650], [450, None, 650]) == (2, 3)
    assert drop_rate(["haan", "", "nahi", ""]) == (2, 4)
    assert hallucinated_word_rate(["", "engine", "two words"]) == (3, 3)
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_early_gates.py -q` → missing functions.

- [ ] **Step 3: Add these functions to `credits.py`.** `count_exact_amounts` compares each expected amount against the parsed hypothesis; `drop_rate` counts empty or unclassifiable replies; `hallucinated_word_rate` returns `(total_whitespace_words_on_non_speech, number_of_clips)`. A `None`/empty clip counts in the denominator. Run the test green before writing CLI code.

- [ ] **Step 4: Write the gate CLI with explicit input manifests.** `scripts/early_gates.py --live --mode garage --manifest var/gates/garage.jsonl --max-credits 2000` reads exactly ten rows `{audio, expected_amount_paise, part, delivery}` and runs `PrismaClient.transcribe(..., mode="transcribe")` once per row. It emits `var/gates/garage-results.jsonl` with raw transcript and exact-match, then prints `correct/10`. Do not silently parse a guessed amount: ask the operator to enter a normalized amount or mark it unrecognized in the result file.

- [ ] **Step 5: Add the TTS mode and a bounded WS telephony preset client.** `--mode tts-roundtrip --manifest var/gates/tts.jsonl` takes ten synthetic `{text, amount_paise}` prompts, calls Timbre, decodes μ-law to 8 kHz WAV, runs the chosen codec/noise chain, sends to Prisma REST, and records amount recovery; obtain three *separate* listener judgments without exposing identity. In `gnani_ws.py`, implement `transcribe_telephony(wav)` for 8 kHz mono signed-16-bit PCM using `wss://api.vachana.ai/stt/v3/stream` and `websockets.connect(..., additional_headers=headers)`. Send `x-api-key-id: <API_KEY>` plus `lang_code: hi-IN`, `x-sample-rate: 8000`, `x-vad-threshold: 0.7`, `x-min-speech-ms: 200`, `x-min-silence-ms: 500`, `x-min-segment-ms: 100`. Send exactly 1024-byte frames at 64 ms intervals, append ≥500 ms of zero frames and await a final `transcript` within a bounded timeout. A receiver runs while frames are sent. Task 18 tests this flush more extensively, but this first bounded version is required for the Oct 10 preset gate. Unit-test the exact URL, auth/header names, frame sizes and pacing with a fake socket before running clips; never print the key.

Implementation for `src/parcha/gnani_ws.py`:

```python
import asyncio
import io
import json
import wave
import websockets

WS_URL = "wss://api.vachana.ai/stt/v3/stream"

def pcm_frames(wav_bytes: bytes) -> list[bytes]:
    with wave.open(io.BytesIO(wav_bytes), "rb") as source:
        if (source.getframerate(), source.getnchannels(), source.getsampwidth()) != (8000, 1, 2):
            raise ValueError("WS input must be mono 8 kHz signed-16-bit WAV")
        pcm = source.readframes(source.getnframes())
    if not pcm:
        raise ValueError("empty WS input")
    chunks = [pcm[i:i + 1024] for i in range(0, len(pcm), 1024)]
    return [chunk.ljust(1024, b"\x00") for chunk in chunks]

def silence_frames(sample_rate: int = 8000, minimum_ms: int = 500) -> list[bytes]:
    frame_ms = 512 / sample_rate * 1000
    count = int(-(-minimum_ms // frame_ms))  # ceiling, no fractional frame
    return [b"\x00" * 1024 for _ in range(count)]

def telephony_headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key-id": api_key,
        "lang_code": "hi-IN",
        "x-sample-rate": "8000",
        "x-vad-threshold": "0.7",
        "x-min-speech-ms": "200",
        "x-min-silence-ms": "500",
        "x-min-segment-ms": "100",
    }

async def transcribe_telephony(wav_bytes: bytes, api_key: str,
                               timeout_s: float = 10.0) -> tuple[str, list[dict]]:
    events: list[dict] = []
    async with websockets.connect(WS_URL, additional_headers=telephony_headers(api_key),
                                  open_timeout=timeout_s) as socket:
        async def receive_final() -> str:
            while True:
                message = json.loads(await asyncio.wait_for(socket.recv(), timeout=timeout_s))
                events.append(message)
                if message.get("type") == "transcript":
                    return str(message.get("text", ""))
                if message.get("type") == "error":
                    raise RuntimeError("Gnani WS returned an error event")
        receiver = asyncio.create_task(receive_final())
        try:
            for frame in pcm_frames(wav_bytes) + silence_frames():
                await socket.send(frame)
                await asyncio.sleep(0.064)
            transcript = await asyncio.wait_for(receiver, timeout=timeout_s)
        finally:
            if not receiver.done():
                receiver.cancel()
        return transcript, events
```

The real API may finalize an utterance before all zero frames are sent. Keep sending the bounded tail and record that event order. A timeout is a dropped final transcript for the gate, not an empty correct transcript. In tests, monkeypatch `websockets.connect` and `asyncio.sleep`; verify the URL, header names and exactly 1024-byte frames without opening a socket.

- [ ] **Step 6: Run short-reply and bias gates.** `--mode short-replies --manifest var/gates/replies.jsonl --transport ws` takes 50 consented reply recordings and 20 engine-only recordings, applies `amr_nb_4750` + 5 dB measured street noise, passes each through `transcribe_telephony`, and records drop/hallucinated words. Label each row with the exact VAD headers and whether a final WS transcript arrived. A failed flush counts as an end-to-end drop; do not relabel the result as an acoustic-only VAD score. If the WS path is unusable, separately measure REST and label it `REST fallback`, not `telephony preset`. By Oct 15, `--mode bias-ab --manifest var/gates/bias.jsonl` runs 30 scripted part/brand clips in `verbatim` with no bias, score 1.0 and score 1.5, recording per-name exact matches; the manifest can be hand-written before Task 15's 100-row dataset exists. Require `--max-credits`, `--credits-per-second` and `--remaining-credits` before the first paid call; decrement the forecast, reserve TTS credits for TTS mode, and stop on 403/429 without retry.

Use the measured credit rate and current dashboard balance from Task 3 for *each* command; the TTS mode also needs a reserve based on the observed TTS call:

```powershell
$CPS = [double](Read-Host 'Measured credits per STT second from Task 3')
$BAL = [double](Read-Host 'Current dashboard balance')
$TTSRESERVE = [double](Read-Host 'Forecast credits for 10 TTS prompts, measured from Task 3')
& $PY scripts/early_gates.py --live --mode garage --manifest var/gates/garage.jsonl --max-credits 2000 --credits-per-second $CPS --remaining-credits $BAL
& $PY scripts/early_gates.py --live --mode tts-roundtrip --manifest var/gates/tts.jsonl --max-credits 2000 --credits-per-second $CPS --remaining-credits $BAL --tts-credit-reserve $TTSRESERVE
& $PY scripts/early_gates.py --live --mode short-replies --transport ws --manifest var/gates/replies.jsonl --max-credits 2000 --credits-per-second $CPS --remaining-credits $BAL
& $PY scripts/early_gates.py --live --mode bias-ab --manifest var/gates/bias.jsonl --max-credits 2000 --credits-per-second $CPS --remaining-credits $BAL
```

Refresh `$BAL` from the dashboard before each run. Record these inputs alongside the actual dashboard deltas in `docs/gates.md`. The TTS mode stops if the estimated remaining reserve would be exceeded.

Expected: machine-readable result files, actual numerators/denominators, and credit tally; no assertion of passing until the clips run. The test suite never calls these `--live` commands.

- [ ] **Step 7: Record decisions.** In `docs/gates.md`, use a table with `date`, `input manifest/hash`, `settings`, `credits before/after`, `numerator/denominator`, `decision`, `fallback`. Oct 6: full grid ≤40% of 5,000 credits or reduced grid. Oct 7: ≥7/10 garage amounts or drop walk-up. Oct 8: ≥9/10 TTS amounts and three intelligible listeners or sweep voice/pre-normalize. Oct 10: with the WS telephony preset, ≤5/50 short replies dropped and ≤1 hallucinated word/engine-only clip; try `haan theek hai`, then walk-up fallback if still >25% drop. Oct 15: 30-name verbatim bias A/B at 1.0 and 1.5, retain boost only if it improves names. Also record the organizer's written answer about filming and public deltas; if absent, public output has no numbers.

- [ ] **Step 8: Commit only code and aggregate evidence.** `& $PY -m pytest tests/test_early_gates.py -q` → all pass. `git add scripts/early_gates.py src/parcha/gnani_ws.py src/parcha/credits.py tests/test_early_gates.py docs/gates.md; git commit -m "feat: run bounded speech feasibility gates"`. Do not commit raw private clips.

### Task 6: Job-card schema with computed rupee total

**Files:** Create `src/parcha/schema.py`, `tests/test_schema.py`.

- [ ] **Step 1: Write failing invariants.** `tests/test_schema.py`:

```python
from datetime import date
import pytest
from pydantic import ValidationError
from parcha.schema import Delivery, Evidence, JobCard, LineItem

def sample_card():
    return JobCard(
        items=[LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=45000),
               LineItem(id="labour-1", label="labour", kind="labour", amount_paise=20000)],
        delivery=Delivery(date=date(2026, 10, 5), window="evening", spoken="Somvaar shaam tak"),
        evidence=[Evidence(field="items.part-1.label", quote="front brake pad", review_score=0.95),
                  Evidence(field="items.part-1.amount_paise", quote="₹450", review_score=0.95),
                  Evidence(field="items.labour-1.label", quote="labour", review_score=0.95),
                  Evidence(field="items.labour-1.amount_paise", quote="₹200", review_score=0.95),
                  Evidence(field="delivery", quote="Somvaar shaam tak", review_score=0.9)],
    )

def test_total_is_computed_and_not_input():
    assert sample_card().total_paise == 65000
    with pytest.raises(ValidationError):
        JobCard.model_validate({**sample_card().model_dump(), "total_paise": 123})

def test_negative_amount_and_duplicate_id_are_rejected():
    with pytest.raises(ValidationError):
        LineItem(id="part-1", label="pad", kind="part", amount_paise=-1)
    with pytest.raises(ValidationError):
        JobCard(items=[sample_card().items[0], sample_card().items[0]],
                delivery=sample_card().delivery, evidence=[])

def test_review_flag_is_derived_from_evidence():
    card = sample_card().model_copy(update={"evidence": [Evidence(
        field="delivery", quote="Somvaar", review_score=0.3)]})
    assert card.needs_review

def test_missing_amount_and_delivery_can_be_reasked():
    draft = JobCard(items=[LineItem(id="part-1", label="front brake pad", kind="part",
                                    amount_paise=None)], delivery=None, evidence=[])
    assert draft.needs_review
    assert draft.maybe_total_paise is None
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_schema.py -q` → missing module.

- [ ] **Step 3: Implement the models.** `src/parcha/schema.py`:

```python
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
    def unique_ids(self):
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
    evidenced = {item.field for item in card.evidence
                 if item.quote.strip() and item.review_score >= 0.8}
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
```

Do not accept `total_paise` from an LLM or HTTP body; the Pydantic model forbids it.

- [ ] **Step 4: Run green and commit.** `& $PY -m pytest tests/test_schema.py -q` → 4 passed. `git add src/parcha/schema.py tests/test_schema.py; git commit -m "feat: define validated job card"`.

### Task 7: Revisioned in-memory session and seal invariant

**Files:** Create `src/parcha/session.py`, `tests/test_session.py`.

- [ ] **Step 1: Write the failing tests.** `tests/test_session.py`:

```python
from datetime import datetime, timezone
import pytest
from parcha.session import Conflict, SessionStore
from tests.test_schema import sample_card

NOW = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)

def test_stale_readback_cannot_confirm_new_revision():
    store = SessionStore()
    session = store.create()
    session = store.set_card(session.id, expected_revision=0, card=sample_card())
    session = store.start_readback(session.id, expected_revision=1)
    store.set_card(session.id, expected_revision=1, card=sample_card())
    with pytest.raises(Conflict, match="stale read-back"):
        store.confirm(session.id, expected_revision=2, when=NOW)

def test_review_needed_card_cannot_be_read_back():
    store = SessionStore()
    session = store.create()
    card = sample_card().model_copy(update={"evidence": []})
    store.set_card(session.id, expected_revision=0, card=card)
    with pytest.raises(Conflict, match="review"):
        store.start_readback(session.id, expected_revision=1)

def test_confirmed_session_rejects_mutation():
    store = SessionStore()
    session = store.create()
    store.set_card(session.id, expected_revision=0, card=sample_card())
    store.start_readback(session.id, expected_revision=1)
    store.confirm(session.id, expected_revision=1, when=NOW)
    with pytest.raises(Conflict, match="confirmed"):
        store.set_card(session.id, expected_revision=1, card=sample_card())
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_session.py -q` → `parcha.session` missing. Add `tests/__init__.py` so importing the reusable `sample_card` fixture works, or move the fixture into `tests/conftest.py` before rerunning.

- [ ] **Step 3: Implement a lock-protected store.** Keep the state object immutable to callers: Task 6 uses tuples for `JobCard.items` and `JobCard.evidence`, and each nested model is frozen. `Session` contains `id`, `revision`, `status` (`draft`, `review`, `awaiting_reply`, `confirmed`), `card`, `logs`, `readback_revision`, `confirmed_at_utc`. `create()` uses `secrets.token_urlsafe(18)` and returns revision 0. All read/modify/write methods hold `threading.RLock`, compare `expected_revision`, and reject confirmed sessions. `set_card(..., logs=())` increments revision and appends only the logs for that accepted card update *inside the same lock*. `start_readback(..., log=...)` stores the marker and system text log together. `confirm(..., log=...)` checks the expected/read-back revision and appends the accepted customer transcript in the same lock. A retry/clarification log uses a separate guarded `record_observation` that checks current revision and awaiting-reply status atomically. A stale or missing session returns a typed `Conflict`/`KeyError` and never adds a log. Add a regression test that mutating an original input list after `JobCard` creation cannot change a confirmed card/PDF total.

```python
from dataclasses import dataclass, replace
from datetime import datetime
from threading import RLock
from typing import Literal
import secrets
from .schema import JobCard, TranscriptLog

class Conflict(RuntimeError):
    pass

@dataclass(frozen=True)
class Session:
    id: str
    revision: int = 0
    status: Literal["draft", "review", "awaiting_reply", "confirmed"] = "draft"
    card: JobCard | None = None
    logs: tuple[TranscriptLog, ...] = ()
    readback_revision: int | None = None
    confirmed_at_utc: datetime | None = None

class SessionStore:
    def __init__(self):
        self._lock = RLock()
        self._items: dict[str, Session] = {}

    def create(self) -> Session:
        with self._lock:
            session = Session(id=secrets.token_urlsafe(18))
            self._items[session.id] = session
            return session

    def get(self, session_id: str) -> Session:
        with self._lock:
            return self._items[session_id]

    def _editable(self, session_id: str, expected_revision: int) -> Session:
        current = self._items[session_id]
        if current.status == "confirmed":
            raise Conflict("confirmed session is immutable")
        if current.revision != expected_revision:
            raise Conflict("stale revision")
        return current

    def set_card(self, session_id: str, *, expected_revision: int, card: JobCard,
                 logs: tuple[TranscriptLog, ...] = ()) -> Session:
        with self._lock:
            current = self._editable(session_id, expected_revision)
            card = JobCard.model_validate(card.model_dump())  # copy into canonical frozen/tuple types
            updated = replace(current, revision=current.revision + 1, status="review",
                              card=card, readback_revision=None, logs=current.logs + logs)
            self._items[session_id] = updated
            return updated

    def start_readback(self, session_id: str, *, expected_revision: int,
                       log: TranscriptLog | None = None) -> Session:
        with self._lock:
            current = self._editable(session_id, expected_revision)
            if current.card is None or current.card.needs_review:
                raise Conflict("card needs review")
            updated = replace(current, status="awaiting_reply",
                              readback_revision=current.revision,
                              logs=current.logs + ((log,) if log else ()))
            self._items[session_id] = updated
            return updated

    def confirm(self, session_id: str, *, expected_revision: int, when: datetime,
                log: TranscriptLog | None = None) -> Session:
        with self._lock:
            current = self._editable(session_id, expected_revision)
            if current.status != "awaiting_reply" or current.readback_revision != current.revision:
                raise Conflict("stale read-back")
            updated = replace(current, status="confirmed", confirmed_at_utc=when,
                              logs=current.logs + ((log,) if log else ()))
            self._items[session_id] = updated
            return updated

    def record_observation(self, session_id: str, *, expected_revision: int,
                           readback_revision: int, log: TranscriptLog) -> Session:
        with self._lock:
            current = self._editable(session_id, expected_revision)
            if current.status != "awaiting_reply" or current.readback_revision != readback_revision:
                raise Conflict("stale reply")
            updated = replace(current, logs=current.logs + (log,))
            self._items[session_id] = updated
            return updated
```

- [ ] **Step 4: Run green.** `& $PY -m pytest tests/test_session.py -q` → 3 passed. Add one test for two concurrent updates using the same expected revision: exactly one succeeds and one raises `Conflict`.
- [ ] **Step 5: Commit.** `git add src/parcha/session.py tests/test_session.py tests/__init__.py; git commit -m "feat: guard card revisions and confirmation"`.

### Task 8: Schema-checked external extraction and targeted correction

**Files:** Create `src/parcha/extract.py`, `tests/test_extract.py`; modify `src/parcha/config.py` only if an extractor setting is missing.

- [ ] **Step 1: Write failing tests with a fake HTTP response.** No real LLM call:

```python
import json
from datetime import datetime, timezone
import httpx, pytest
from parcha.extract import ExtractionError, Extractor

WHEN = datetime(2026, 10, 4, 10, tzinfo=timezone.utc)

def fake_chat(content):
    return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(content)}}]})

def test_valid_card_uses_both_transcripts_and_computes_total():
    payload = {"items": [
        {"id": "part-1", "label": "front brake pad", "kind": "part", "amount_paise": 45000},
        {"id": "labour-1", "label": "labour", "kind": "labour", "amount_paise": 20000}],
        "delivery": {"date": "2026-10-05", "window": "evening", "spoken": "Somvaar shaam tak"},
        "evidence": [
            {"field": "items.part-1.label", "quote": "front brake pad", "review_score": 0.95},
            {"field": "items.part-1.amount_paise", "quote": "₹450", "review_score": 0.95},
            {"field": "items.labour-1.label", "quote": "labour", "review_score": 0.95},
            {"field": "items.labour-1.amount_paise", "quote": "₹200", "review_score": 0.95},
            {"field": "delivery", "quote": "Somvaar shaam tak", "review_score": 0.9}]}
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card(
        "front brake pad ₹450, labour ₹200, Somvaar shaam tak",
        "front brake pad saade chaar sau, labour do sau, Somvaar shaam tak", WHEN)
    assert card.total_paise == 65000
    assert not card.needs_review

def test_unquoted_evidence_blocks_dispatch():
    payload = {"items": [{"id":"part-1","label":"pad","kind":"part","amount_paise":45000}],
               "delivery":{"date":"2026-10-05","window":"evening","spoken":"Somvaar"},
               "evidence":[{"field":"items.part-1.amount_paise","quote":"₹999","review_score":0.99}]}
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card("₹450 Somvaar", "", WHEN)
    assert card.needs_review

def test_missing_amount_is_a_reaskable_draft():
    payload = {"items": [{"id":"part-1","label":"front brake pad","kind":"part",
                          "amount_paise":None}], "delivery":None,
               "evidence":[{"field":"items.part-1.label","quote":"front brake pad",
                            "review_score":0.9}]}
    http = httpx.Client(transport=httpx.MockTransport(lambda _: fake_chat(payload)))
    card = Extractor("http://test/v1", "key", "model", http).extract_card(
        "front brake pad", "front brake pad", WHEN)
    assert card.needs_review and card.maybe_total_paise is None
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_extract.py -q` → missing module.

- [ ] **Step 3: Define the exact extraction request.** `Extractor.extract_card(normalized, verbatim, recorded_at_utc)` POSTs to `{base_url}/chat/completions` with a system message and a user JSON payload. The system message is:

```text
Extract only explicitly spoken workshop facts from the two transcripts. Return JSON with
items [{id,label,kind,amount_paise}], delivery {date,window,spoken} or null, evidence
[{field,quote,review_score}]. Use item ids part-1, part-2, labour-1, etc. A missing
item label or amount is null, not a guess. Provide separate evidence for every label,
amount and delivery; each quote must be contiguous in either transcript. Use the
provided Asia/Kolkata recording date to resolve a weekday. Do not guess a missing
number/date, vehicle registration, customer name, or total. Score each field 0..1
for human review, not statistical confidence. Return JSON only.
```

The request body uses `model`, `temperature: 0`, `messages`, and `response_format: {"type":"json_object"}`. `json_object` is more widely supported by OpenAI-compatible endpoints than an enforced schema; Pydantic remains the authority. If Evon serving does not support `response_format`, the adapter may omit it *only after a live compatibility check* while retaining validation.

- [ ] **Step 4: Implement response validation.** Parse only `choices[0].message.content`. Reject empty content, markdown fences, missing keys and extra keys; call `JobCard.model_validate`. Explicit JSON `null` is allowed for a *missing* item label, amount or delivery so the result remains a re-askable draft. For each `Evidence`, normalize Unicode with `unicodedata.normalize("NFKC", text).casefold()` and collapse whitespace; if its quote is absent from both transcripts, replace the evidence with score 0 so the card needs review. Require evidence for each *present* label, amount and delivery. Resolve a named weekday from the **actual transcript** and the `Asia/Kolkata` recording date; if the proposed date is not that next occurrence, zero the delivery review score. No weekday, several weekdays, `kal`, a same-day weekday or an otherwise ambiguous relative date forces review instead of sealing. Retry invalid JSON once; return a typed `ExtractionError` after the second invalid response. Never include secrets or complete raw audio in error logs. Add a test where Oct 4 `Somvaar` plus an extracted Oct 12 delivery remains review-required; Oct 5 passes.

Core of `src/parcha/extract.py` (use the same validation for correction replies in Step 5):

```python
import json
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import httpx
from .schema import JobCard

class ExtractionError(RuntimeError):
    pass

def _normal(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())

WEEKDAY_WORDS = {
    "somvaar": 0, "सोमवार": 0, "mangalvaar": 1, "मंगलवार": 1,
    "budhvaar": 2, "बुधवार": 2, "guruvaar": 3, "गुरुवार": 3,
    "shukravaar": 4, "शुक्रवार": 4, "shanivaar": 5, "शनिवार": 5,
    "ravivaar": 6, "रविवार": 6,
}

class Extractor:
    def __init__(self, base_url: str, api_key: str, model: str,
                 http: httpx.Client | None = None):
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.api_key, self.model = api_key, model
        self.http = http or httpx.Client(timeout=30)

    def _chat(self, system: str, user: dict) -> str:
        response = self.http.post(
            self.url, headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "temperature": 0,
                  "response_format": {"type": "json_object"},
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": json.dumps(user, ensure_ascii=False)}]})
        if response.status_code != 200:
            raise ExtractionError(f"extractor HTTP {response.status_code}")
        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ExtractionError("extractor response lacked message content") from exc
        if not isinstance(content, str) or not content.strip() or "```" in content:
            raise ExtractionError("extractor did not return plain JSON")
        return content

    def extract_card(self, normalized: str, verbatim: str,
                     recorded_at_utc: datetime) -> JobCard:
        if recorded_at_utc.tzinfo is None:
            raise ValueError("recording timestamp must be timezone-aware")
        local_date = recorded_at_utc.astimezone(ZoneInfo("Asia/Kolkata")).date()
        user = {"transcribe": normalized, "verbatim": verbatim,
                "recorded_local_date": local_date.isoformat()}
        last_error: Exception | None = None
        for _ in range(2):
            try:
                raw = json.loads(self._chat(CARD_SYSTEM_PROMPT, user))
                card = JobCard.model_validate(raw)
                transcript = _normal(normalized + " " + verbatim)
                data = card.model_dump()
                for evidence in data["evidence"]:
                    if _normal(evidence["quote"]) not in transcript:
                        evidence["review_score"] = 0.0
                if card.delivery is not None:
                    mentioned = {day for word, day in WEEKDAY_WORDS.items()
                                 if word in transcript}
                    unambiguous = len(mentioned) == 1 and "kal" not in transcript and "कल" not in transcript
                    if unambiguous:
                        weekday = next(iter(mentioned))
                        days_ahead = (weekday - local_date.weekday()) % 7
                        expected_date = local_date + timedelta(days=days_ahead)
                        unambiguous = days_ahead > 0 and card.delivery.date == expected_date
                    if not unambiguous:
                        for evidence in data["evidence"]:
                            if evidence["field"] == "delivery":
                                evidence["review_score"] = 0.0
                return JobCard.model_validate(data)
            except (ExtractionError, ValueError, TypeError) as exc:
                last_error = exc
        raise ExtractionError("extractor returned invalid card twice") from last_error
```

Define `CARD_SYSTEM_PROMPT` as the exact instruction in Step 3. If a specific Evon endpoint rejects `response_format`, test and configure that adapter explicitly; do not catch a 400 and silently retry with a different request shape during the live demo.

- [ ] **Step 5: Write and implement correction tests.** Add a test where `extract_field("items.part-1.amount_paise", "front brake pad saade chaar sau", old_card)` returns exactly `45000` paise; the adapter rejects a response for `labour-1` or for `total_paise`. The correction request names the allowed `field` and asks for `{field,value,evidence_quote,review_score}` only; `value` is paise for an amount, text for a label, or a validated `Delivery` for delivery. Validate the quote against the correction transcript and replace only that field. Add tests that a missing label and a missing delivery can each be filled by re-ask. If the customer merely says `nahi, saade chaar sau` and more than one amount is on the card, raise `ExtractionError("which item?")` and prompt for its name. Test that labour and delivery remain byte-for-byte identical after an amount patch.

- [ ] **Step 6: Run green and commit.** `& $PY -m pytest tests/test_extract.py -q` → all pass. `git add src/parcha/extract.py src/parcha/config.py tests/test_extract.py; git commit -m "feat: validate spoken field extraction"`.

### Task 9: Workshop intake and targeted voice re-ask

**Files:** Create `src/parcha/workflow.py`, `tests/test_workflow.py`; modify `src/parcha/audio.py`, `src/parcha/session.py`.

- [ ] **Step 1: Write a failing workflow test with fakes.** No HTTP client and no FFmpeg run in this test:

```python
from parcha.session import SessionStore
from parcha.workflow import Workflow
from tests.test_schema import sample_card

class FakePrisma:
    def __init__(self): self.calls = []
    def transcribe(self, wav, *, mode, bias=None, score=1.0):
        self.calls.append((wav, mode, bias, score))
        return "front brake pad ₹450, labour ₹200, Somvaar shaam tak" if mode == "transcribe" else "front brake pad saade chaar sau"

class FakeExtractor:
    def extract_card(self, normalized, verbatim, recorded_at_utc):
        assert "₹450" in normalized and "brake pad" in verbatim
        return sample_card()

def test_intake_uses_same_recording_for_two_prisma_passes():
    prisma, store = FakePrisma(), SessionStore()
    session = store.create()
    service = Workflow(store=store, prisma=prisma, extractor=FakeExtractor(),
                       normalize_audio=lambda blob, mime: b"RIFFpcm")
    result = service.intake(session.id, b"recorded", "audio/webm", expected_revision=0)
    assert [call[1] for call in prisma.calls] == ["transcribe", "verbatim"]
    assert prisma.calls[0][0] == prisma.calls[1][0] == b"RIFFpcm"
    assert result.card.total_paise == 65000
    assert result.revision == 1
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_workflow.py -q` → missing `Workflow`.

- [ ] **Step 3: Implement audio intake guard.** In `audio.py`, `normalize_upload(blob, mime, sample_rate=16000)` parses the media type before `;` (`audio/webm;codecs=opus` becomes `audio/webm`), lowercases it and permits `audio/webm`, `audio/ogg`, `audio/mp4`, `audio/wav`, and `audio/x-wav`; reject zero bytes and >8 MB before FFmpeg. Use `_ffmpeg(blob, [], ["-ar",str(sample_rate),"-ac","1","-c:a","pcm_s16le","-f","wav"])`, then calculate duration from the *decoded PCM bytes actually read*, not `wave.getnframes()` alone: FFmpeg may put an unknown length in a piped WAV header. Require `0.3 <= decoded_frame_count / sample_rate <= 60`. For a customer reply, call with `sample_rate=8000`; inject a separate `normalize_reply_audio` closure into the workflow so the workshop callable still takes two arguments. Do not trust the MIME type to prove content; FFmpeg must decode it. Add `test_browser_mime_with_codecs_is_accepted` and `test_bad_or_long_upload_is_rejected_before_prisma` using a fake Prisma that raises if called.

- [ ] **Step 4: Prepare logs for one atomic store update.** Build the two `TranscriptLog` values with role `mechanic`, mode `transcribe`/`verbatim`, text and the same UTC recording timestamp. Pass them to `SessionStore.set_card(..., logs=...)`; do not call a separate `append_logs`. A failed extraction leaves `card=None` and no accepted logs. Add a concurrent intake test: two requests use the same expected revision; one card/log pair commits and the other gets 409 with no transcript from the rejected attempt in the session.

- [ ] **Step 5: Implement `Workflow.intake`.** Constructor injections: `store`, `prisma`, `extractor`, `normalize_audio`, plus optional `bias_words=("brake", "clutch", "Honda")`. `intake` validates audio once; calls `prisma.transcribe(wav, mode="transcribe")`, then `verbatim` with a bias list only if Oct 15 A/B gate later shows gain. During initial live development, pass `bias_words` to the second call and record an unboosted A/B separately; switching the runtime bias setting remains one configuration flag. Call `extract_card` with both texts and a timezone-aware timestamp; append both logs; `set_card`. Return the updated session. Never swallow a failed Prisma call by creating an empty confirmed card.

```python
def intake(self, session_id, blob, mime, *, expected_revision, recorded_at_utc=None):
    recorded_at_utc = recorded_at_utc or datetime.now(timezone.utc)
    wav = self.normalize_audio(blob, mime)
    normalized = self.prisma.transcribe(wav, mode="transcribe")
    verbatim = self.prisma.transcribe(wav, mode="verbatim",
                                      bias=list(self.bias_words) if self.use_bias else None)
    card = self.extractor.extract_card(normalized, verbatim, recorded_at_utc)
    logs = (TranscriptLog(role="mechanic", mode="transcribe", text=normalized,
                          recorded_at_utc=recorded_at_utc),
            TranscriptLog(role="mechanic", mode="verbatim", text=verbatim,
                          recorded_at_utc=recorded_at_utc))
    return self.store.set_card(session_id, expected_revision=expected_revision,
                               card=card, logs=logs)
```

- [ ] **Step 6: Add targeted re-ask behavior.** `Workflow.reask(session_id, field, blob, mime, expected_revision)` permits only `items.<id>.label`, `items.<id>.amount_paise`, or `delivery` for an existing item; it must work even when that field is `None` and has no earlier evidence. Transcribe the short clip, call `extractor.extract_field`, replace that one field, update its evidence and increment revision. A new amount must leave all other item IDs/amounts and delivery unchanged. Add tests for wrong field, repeated stale revision, missing amount filled, missing delivery filled, unsupported label repaired, and a still-low score. Return `review_fields` instead of pretending the card is complete.

- [ ] **Step 7: Run green and commit.** `& $PY -m pytest tests/test_workflow.py tests/test_session.py -q` → all pass. `git add src/parcha/workflow.py src/parcha/audio.py src/parcha/session.py tests/test_workflow.py; git commit -m "feat: turn workshop speech into a reviewable card"`.

### Task 10: Workshop HTTP API and recording page

**Files:** Modify `src/parcha/app.py`; create `src/parcha/templates/workshop.html`, `src/parcha/static/app.js`, `tests/test_app.py`.

- [ ] **Step 1: Write failing HTTP tests.** Inject fake `Workflow`/`SessionStore` through an `AppServices` object passed to `create_app(services=...)`:

```python
from fastapi.testclient import TestClient
from parcha.app import create_app

def test_create_session_and_reject_empty_intake(fake_services):
    client = TestClient(create_app(fake_services))
    created = client.post("/sessions").json()
    assert created["revision"] == 0
    response = client.post(f"/sessions/{created['id']}/intake",
                           data={"expected_revision": "0"},
                           files={"audio": ("empty.webm", b"", "audio/webm")})
    assert response.status_code == 422

def test_workshop_page_has_record_and_review_controls(fake_services):
    response = TestClient(create_app(fake_services)).get("/workshop")
    assert response.status_code == 200
    assert 'id="record"' in response.text
    assert 'id="start-readback"' in response.text
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_app.py -q` → route not found/constructor mismatch.

- [ ] **Step 3: Wire explicit service dependencies.** `AppServices` has `settings`, `store`, `workflow`, and `timbre`; the workflow owns the injected audio functions. `create_app(services=None)` builds live objects lazily and serves `/health` even if keys are absent. Add `GET /workshop` from Jinja2, `POST /sessions`, `GET /sessions/{id}`, `POST /sessions/{id}/intake`, `POST /sessions/{id}/reask/{field}`. `SessionStore.get` `KeyError` maps to 404, `Conflict` to 409, invalid upload/extraction to 422, missing live credentials to 503. Use `fastapi.UploadFile`, `Form`, `File` and `Response`. Return serialized `card` plus `maybe_total_paise` (JSON null while an amount is missing), `review_fields`, revision and status; do not leak `Settings` or API keys. Keep the customer routes for Task 13.

The route skeleton below shows the exact dependency boundary; extend the same app in Tasks 11–14:

```python
from dataclasses import dataclass
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from .config import Settings
from .session import Conflict, SessionStore
from .workflow import Workflow
from .audio import AudioError, normalize_upload
from .extract import ExtractionError, Extractor
from .gnani import PrismaClient, TimbreClient, GnaniError
from .schema import review_fields

ROOT = Path(__file__).parent

@dataclass
class AppServices:
    settings: Settings
    store: SessionStore
    workflow: Workflow
    timbre: TimbreClient | None = None

def default_services() -> AppServices:
    settings = Settings.load()
    store = SessionStore()
    prisma = PrismaClient(settings.api_key)
    extractor = Extractor(settings.extractor_base_url, settings.extractor_api_key,
                          settings.extractor_model)
    timbre = TimbreClient(settings.api_key, voice=settings.tts_voice)
    workflow = Workflow(store=store, prisma=prisma, extractor=extractor,
                        normalize_audio=normalize_upload)
    return AppServices(settings, store, workflow, timbre)

def session_payload(session) -> dict:
    card = session.card
    return {"id": session.id, "revision": session.revision, "status": session.status,
            "card": card.model_dump(mode="json") if card else None,
            "total_paise": card.maybe_total_paise if card else None,
            "review_fields": review_fields(card) if card else []}

def create_app(services: AppServices | None = None) -> FastAPI:
    services = services or default_services()
    app = FastAPI(title="Kaam ka Parcha")
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    templates = Jinja2Templates(directory=ROOT / "templates")

    @app.get("/health")
    def health(): return {"ok": True}

    @app.get("/workshop", response_class=HTMLResponse)
    def workshop(request: Request):
        return templates.TemplateResponse(request, "workshop.html", {})

    @app.post("/sessions")
    def create_session(): return session_payload(services.store.create())

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str):
        try: return session_payload(services.store.get(session_id))
        except KeyError: raise HTTPException(404, "unknown session")

    @app.post("/sessions/{session_id}/intake")
    async def intake(session_id: str, expected_revision: int = Form(...),
                     audio: UploadFile = File(...)):
        try:
            blob = await audio.read()
            if not blob:
                raise AudioError("empty recording")
            services.settings.require_gnani()
            services.settings.require_extractor()
            result = services.workflow.intake(session_id, blob, audio.content_type or "",
                                              expected_revision=expected_revision)
            return session_payload(result)
        except KeyError: raise HTTPException(404, "unknown session")
        except Conflict as exc: raise HTTPException(409, str(exc))
        except (AudioError, ExtractionError) as exc: raise HTTPException(422, str(exc))
        except ValueError as exc: raise HTTPException(503, str(exc))
        except GnaniError as exc: raise HTTPException(502, str(exc))

    return app

app = create_app()
```

`review_fields(card)` returns only the missing/low-evidence field paths from Task 6. Before copying this skeleton, add `src/parcha/templates/workshop.html` and `src/parcha/static/app.js` so `StaticFiles` can mount; Task 1's earlier health-only `app.py` remains valid until this task. For tests, `tests/conftest.py` can provide `AppServices(Settings.from_mapping({}), SessionStore(), fake_workflow, None)`; keep `GET /health` free of live credential checks. Add `tests/conftest.py` to this task's commit.

- [ ] **Step 4: Implement the minimal workshop HTML.** Include `<meta name="viewport" content="width=device-width, initial-scale=1">`, a `<button id="record">Record estimate</button>`, `<button id="stop" disabled>Stop</button>`, `<output id="message">`, `<section id="transcript">`, `<section id="card">`, `<button id="start-readback" disabled>Read estimate to customer</button>`, `<a id="customer-link">`, and a persistent `Synthetic demo data` badge. Render item amount as `₹${(amount_paise/100).toFixed(0)}` only if whole rupees; otherwise two decimals. Show exact delivery date/window and list each field needing re-ask. A re-ask button records a new short clip for that field.

- [ ] **Step 5: Implement the MediaRecorder helper in `app.js`.** Use a supported MIME in this order: `audio/webm;codecs=opus`, `audio/mp4`, `audio/ogg;codecs=opus`; if none is supported, show a clear error. `navigator.mediaDevices.getUserMedia({audio:true})` starts capture; `MediaRecorder` chunks are joined into a `Blob`, tracks are stopped on Stop, and `FormData` sends `audio` plus `expected_revision`. Do not retain microphone tracks after a completed upload. This same helper will serve the customer page.

```javascript
async function recordOnce(startButton, stopButton) {
  const formats = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/ogg;codecs=opus'];
  const mimeType = formats.find(x => MediaRecorder.isTypeSupported(x));
  if (!navigator.mediaDevices || !mimeType) throw new Error('Microphone recording unavailable');
  const stream = await navigator.mediaDevices.getUserMedia({audio: true});
  const chunks = [];
  const recorder = new MediaRecorder(stream, {mimeType});
  recorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
  const done = new Promise(resolve => recorder.onstop = () => {
    stream.getTracks().forEach(track => track.stop());
    resolve(new Blob(chunks, {type: mimeType}));
  });
  recorder.start();
  startButton.disabled = true; stopButton.disabled = false;
  stopButton.onclick = () => recorder.stop();
  return await done;
}
```

Wire page events to the named routes and update `revision` only from server responses. Disable read-back if `review_fields` is nonempty. The UI cannot itself seal a session.

- [ ] **Step 6: Run green and local smoke.** `& $PY -m pytest tests/test_app.py -q` → all pass. Run `& $PY -m uvicorn parcha.app:app --reload`, open `http://localhost:8000/workshop`, confirm the empty state and microphone permission without making a Gnani call. Commit: `git add src/parcha/app.py src/parcha/templates/workshop.html src/parcha/static/app.js tests/test_app.py; git commit -m "feat: add workshop recording page"`.

### Task 11: Read-back text, audio and revision marker

**Files:** Modify `src/parcha/workflow.py`, `src/parcha/session.py`, `src/parcha/app.py`; create `tests/test_readback.py`.

- [ ] **Step 1: Write a failing read-back test.** Given `sample_card()`, `make_readback(card)` must contain both item labels, each amount, the computed total `₹650`, the delivery date/window and a confirmation/correction question. A fake Timbre returns `b"\xff" * 8000`; a fake codec yields WAV bytes. `Workflow.start_readback` calls Timbre once, stores `readback_revision == session.revision`, and returns the playable WAV plus chain manifest. A review-needed card raises `Conflict` before calling Timbre.

```python
def test_readback_uses_derived_total_and_marks_revision(service, reviewed_session):
    result = service.start_readback(reviewed_session.id, expected_revision=1)
    assert "₹650" in result.text
    assert result.readback_revision == 1
    assert result.audio_wav.startswith(b"RIFF")
    assert result.manifest["sample_rate"] == 8000
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_readback.py -q` → `start_readback` absent.

- [ ] **Step 3: Implement text from a single frozen snapshot.** `make_readback(card)` formats each item as `<label>: ₹<amount>`, says `कुल ₹<computed_total>`, then delivery date/window and `ठीक है? हाँ कहें, या सुधार बताएं।`. A small rupee formatter handles paise without floating point. Do not paste an extractor-supplied total. If the Oct 8 round-trip shows Timbre misreads digits, implement `rupees_to_hindi_words` with tests for 0, 1, 49, 450, 650, 1,00,000 and reject out-of-range values; rerun the round-trip gate before using it. Record which wording actually passed.

- [ ] **Step 4: Implement audio generation.** `Workflow.start_readback` obtains the reviewed card, creates text, calls Timbre once, decodes the raw μ-law, applies the selected codec (`g711` or `amr_nb_4750`) and measured noise, then calls `SessionStore.start_readback(..., log=TranscriptLog(role="system", mode="timbre_readback", text=text, recorded_at_utc=now))` so the read-back marker and spoken text are recorded together. Store the exact `readback_revision`; return `Readback(text, audio_wav, manifest, revision)`. Manifest keys: `codec`, `sample_rate:8000`, `noise_source`, `target_snr_db`, `measured_snr_db`, `loss_percent:0`, `ffmpeg_version`, `revision`. If audio generation fails, leave the session in review, without a read-back marker/log.

- [ ] **Step 5: Add two HTTP routes.** `POST /sessions/{id}/readback` returns JSON `{revision, audio_url, text, manifest}` after storing the WAV under ignored `var/sessions/<id>/<revision>.wav`; `GET /sessions/{id}/readback.wav?revision=N` serves that file only while it is the current read-back revision. Use random session IDs and no guessable directory traversal. Clear old read-back files when a revision changes. The browser sets `<audio src=audio_url controls>`.

- [ ] **Step 6: Run green and commit.** `& $PY -m pytest tests/test_readback.py tests/test_app.py -q` → all pass. `git add src/parcha/workflow.py src/parcha/session.py src/parcha/app.py tests/test_readback.py; git commit -m "feat: read reviewed bill through simulated line"`.

### Task 12: Customer reply, field correction and exact-revision confirmation

**Files:** Modify `src/parcha/workflow.py`, `src/parcha/session.py`; create `tests/test_reply.py`.

- [ ] **Step 1: Write failing classifier tests.** Customer confirmation semantics follow the locked spec:

```python
import pytest
from parcha.workflow import classify_reply

@pytest.mark.parametrize("text", ["haan", "हाँ", "haan theek hai", "हाँ ठीक है"])
def test_clear_acceptance(text):
    assert classify_reply(text) == "accept"

@pytest.mark.parametrize("text", ["", "haan nahi", "नहीं, साढ़े चार सौ", "haan 450"])
def test_uncertain_or_correction_never_accepts(text):
    assert classify_reply(text) != "accept"

def test_date_only_negation_routes_to_delivery_correction():
    assert classify_reply("nahi, Mangalvaar shaam tak") == "correction"
    assert classify_reply("नहीं, मंगलवार शाम तक") == "correction"
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_reply.py -q` → classifier missing.

- [ ] **Step 3: Implement conservative classification.** Normalize Unicode NFKC, lowercase Latin, strip punctuation and collapse whitespace. Check negation tokens (`nahi`, `nahin`, `नहीं`, `ना`) *before* acceptance. Accept only an otherwise empty reply after removing `haan`/`हाँ` and optional `theek hai`/`ठीक है`; never accept a sentence with an amount or extra instruction. `nahi` with amount, item, date or time words (`kal`, weekday names in Latin/Devanagari, `shaam`, `सुबह`, `तारीख`, etc.) becomes `correction`; standalone `nahi` becomes `reject`; empty/unrecognized becomes `unclear`. The confirmation result includes the raw Prisma transcript, not a classifier-invented phrase.

Use this narrow classifier in `workflow.py`; the extractor handles the actual corrected field only after classification:

```python
import re
import unicodedata
from typing import Literal

ReplyClass = Literal["accept", "correction", "reject", "unclear"]
YES = {"haan", "han", "हाँ", "हां"}
NO = {"nahi", "nahin", "नहीं", "ना"}
DATE_WORDS = {"kal", "somvaar", "mangalvaar", "budhvaar", "guruvaar",
              "shukravaar", "shanivaar", "ravivaar", "shaam", "subah",
              "monday", "tuesday", "बुधवार", "मंगलवार", "सोमवार",
              "शाम", "सुबह", "तारीख", "कल"}

def classify_reply(text: str) -> ReplyClass:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    words = re.findall(r"[a-z0-9\u0900-\u097f]+", normalized)
    if not words:
        return "unclear"
    if any(word in NO for word in words):
        remaining = [word for word in words if word not in NO]
        return "correction" if remaining else "reject"
    if words[0] not in YES:
        return "unclear"
    tail = words[1:]
    if tail in ([], ["theek", "hai"], ["ठीक", "है"]):
        return "accept"
    return "unclear"
```

The explicit date-word set guides target resolution after a `correction` classification. An extra word after `haan` makes the reply unclear, so a phrase like `haan ₹450` never seals. Add a test for negation precedence (`haan nahi` is not accepted) and for an amount-only correction that asks which item.

- [ ] **Step 4: Write the state-machine tests.** A fake Prisma returns `haan`, then `nahi front brake pad saade chaar sau`, then `haan`. Verify: first seals the revision it heard; for the second scenario, correction changes only `part-1.amount_paise`, increments revision, invalidates the old read-back, requires a new read-back, then confirmation seals the new total. `nahi, saade chaar sau` without an item name asks `Which item?` and does not change an amount. A date-only `nahi, Mangalvaar shaam tak` calls `extract_field("delivery", ...)`, preserves all amounts and requires a new read-back. A stale reply with old revision gets 409. An engine-only empty transcript cannot seal.

- [ ] **Step 5: Implement reply orchestration.** `Workflow.reply(session_id, blob, mime, expected_revision, readback_revision)` converts the browser recording to 8 kHz WAV, applies *the same declared codec and noise settings* as the read-back chain, and calls `PrismaClient.transcribe(..., mode="transcribe")` through REST. REST accepts 8 kHz audio but does not expose documented telephony VAD headers; the product stays on REST unless the Task 18 WS experiment justifies a separate switch. Build a customer `TranscriptLog` with UTC timestamp but do **not** append it yet. If `accept`, call `SessionStore.confirm(..., log=customer_log)`; the store checks and logs the same revision atomically. If `correction`, resolve a unique item amount/label or `delivery` target, call `Extractor.extract_field` on only that target, then `SessionStore.set_card(..., logs=(customer_log,))` atomically and return `needs_readback`. If no unique target, call `record_observation` only after it checks the still-current awaiting-reply revision under lock, then return `ask_field`. `reject` or `unclear` similarly records only a guarded observation and returns `retry`. A stale reply gets 409 and cannot enter the PDF evidence. Cap replies at 60 seconds before API call.

- [ ] **Step 6: Run green and commit.** `& $PY -m pytest tests/test_reply.py tests/test_session.py -q` → all pass. `git add src/parcha/workflow.py src/parcha/session.py tests/test_reply.py; git commit -m "feat: confirm only the read-back card revision"`.

### Task 13: Customer page and browser-safe simulated call

**Files:** Create `src/parcha/templates/customer.html`; modify `src/parcha/app.py`, `src/parcha/static/app.js`, `tests/test_app.py`.

- [ ] **Step 1: Write failing customer-route tests.** `GET /customer/{id}` must include the card and disclosure; `POST /sessions/{id}/reply` accepts a recorded blob and expected/read-back revisions; `GET /sessions/{id}` reflects `needs_readback`, `retry`, or `confirmed`. Unknown session returns 404. A route test asserts the Gnani key string is absent from every HTML/JSON response. Unconfirmed artifact links remain disabled.

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_app.py -q` → customer route missing.

- [ ] **Step 3: Add customer HTTP contract.** `GET /customer/{id}` renders only the session card, revision, and a media player. `POST /sessions/{id}/reply` takes `audio: UploadFile`, `expected_revision: int`, `readback_revision: int`; calls `Workflow.reply`; returns `{outcome, transcript, revision, total_paise, review_fields, audio_url?}`. `outcome` is one of `confirmed`, `needs_readback`, `ask_field`, `retry`. Never return 200/`confirmed` before `SessionStore.confirm` succeeds.

- [ ] **Step 4: Write the customer page.** Include `<audio id="readback" controls>`, Record/Stop buttons, displayed itemized amounts and promised date, status output, and a visible disclosure while the customer leg is open:

```text
Simulated phone line: audio passed through G.711 / AMR-NB 4.75 kbps + street
noise at 5 dB. No call was placed. All names and amounts are synthetic.
```

If the actual manifest uses one codec or a different SNR, generate the badge from those values instead of falsely claiming both codecs/5 dB. On `needs_readback`, show the corrected card, call `POST /sessions/{id}/readback` for its new revision, replace the player URL, and enable reply recording only after that new audio completes playback. On `ask_field`, show the exact question. Keep the mechanic and customer pages on separate URLs with the same session ID; no fake ringing animation or call timer implying PSTN.

- [ ] **Step 5: Verify microphone secure context.** First smoke two browser windows on the same computer at `http://localhost:8000` (localhost is a secure context). For an actual phone, create `var/certs/`, run `mkcert -install` and `mkcert -cert-file var/certs/lan-cert.pem -key-file var/certs/lan-key.pem <LAN-IP>`, trust mkcert's root CA on the phone, then start Uvicorn with `--host 0.0.0.0 --ssl-keyfile var/certs/lan-key.pem --ssl-certfile var/certs/lan-cert.pem`. Open `https://<LAN-IP>:8000/customer/<id>` and verify `navigator.mediaDevices` exists. If certificate trust fails, film the customer at the second localhost browser and disclose that arrangement. Certificates stay in ignored `var/`.

- [ ] **Step 6: Run a full synthetic browser smoke through confirmation.** Workshop records a scripted estimate; customer plays degraded audio; replies with a targeted correction; receives updated read-back; replies `haan`; session status becomes `confirmed`. Task 14 adds the PDF link and checks it separately. Record actual browser MIME types, codec, SNR, elapsed time and credits in `docs/gates.md`. Run `& $PY -m pytest tests/test_app.py -q` → all pass. Commit: `git add src/parcha/templates/customer.html src/parcha/app.py src/parcha/static/app.js tests/test_app.py; git commit -m "feat: add customer simulated-call page"`.

### Task 14: Confirmed PDF and WhatsApp-ready text

**Files:** Create `src/parcha/artefact.py`, `tests/test_artefact.py`; modify `src/parcha/app.py`; add a licensed `assets/fonts/NotoSansDevanagari-Regular.ttf` and `assets/fonts/OFL.txt` if used.

- [ ] **Step 1: Write failing artifact tests.** A confirmed session from Task 12 is the fixture. Before confirmation both routes return 409. Add a concurrent-intake/stale-reply regression: the attached logs contain only the accepted mechanic transcription pair, system read-back and accepted customer events, never the transcripts from a rejected 409 request:

```python
from io import BytesIO
import json
from pypdf import PdfReader
from parcha.artefact import render_pdf, whatsapp_text

def test_pdf_embeds_exact_transcripts(confirmed_session):
    data = render_pdf(confirmed_session)
    assert data.startswith(b"%PDF")
    reader = PdfReader(BytesIO(data))
    attached = reader.attachments["transcripts.json"]
    payload = json.loads(attached[0] if isinstance(attached, list) else attached)
    assert payload["revision"] == confirmed_session.revision
    assert [log["role"] for log in payload["logs"]].count("customer") >= 1
    assert any("₹" in log["text"] for log in payload["logs"])

def test_whatsapp_text_has_derived_total_and_no_delivery_claim(confirmed_session):
    message = whatsapp_text(confirmed_session)
    assert "₹650" in message
    assert "2026-10-05" in message
    assert "No real call was placed" in message
    assert "sent" not in message.lower()
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_artefact.py -q` → `parcha.artefact` missing.

- [ ] **Step 3: Implement a sealed snapshot guard and PDF.** `render_pdf(session)` requires `status == "confirmed"`, `confirmed_at_utc` set, and `card` non-null; otherwise raise `Conflict`. Build a visible one-page ReportLab card containing fixed synthetic workshop name/vehicle registration, itemized labels and costs, derived total, delivery date/window, UTC confirmation time, `Session <id>/rev <revision>`, and `Simulated phone line; no call placed`. Use a bundled OFL font that covers ₹. Keep visible labels in Latin if Devanagari shaping is faulty; the exact UTF-8 transcripts live in the attachment.

```python
from io import BytesIO
import json
from reportlab.pdfgen.canvas import Canvas
from pypdf import PdfReader, PdfWriter

def attach_transcripts(pdf_bytes: bytes, session) -> bytes:
    evidence = {"session_id": session.id, "revision": session.revision,
                "confirmed_at_utc": session.confirmed_at_utc.isoformat(),
                "logs": [{"role": log.role, "mode": log.mode, "text": log.text,
                          "recorded_at_utc": log.recorded_at_utc.isoformat()}
                         for log in session.logs]}
    writer = PdfWriter()
    writer.append_pages_from_reader(PdfReader(BytesIO(pdf_bytes)))
    writer.add_attachment("transcripts.json",
                          json.dumps(evidence, ensure_ascii=False, indent=2).encode("utf-8"))
    output = BytesIO(); writer.write(output)
    return output.getvalue()
```

Use `Canvas(BytesIO(), pagesize=A4)` for the visible page, draw item lines using the same `format_rupees` helper as read-back, `save()`, then call `attach_transcripts`. PDF attachments are local evidence; do not invent a remote verification link or QR to nonexistent audio.

- [ ] **Step 4: Implement text from the same snapshot.** `whatsapp_text(session)` returns a string headed `Kaam ka Parcha — confirmed`, session reference, item list, total, promised date/window, UTC confirmation time and simulated-line disclosure. It is shown in a copy button and downloadable as `.txt`; no messaging API is called.

- [ ] **Step 5: Add routes and check the visible document.** `GET /sessions/{id}/parcha.pdf` returns `application/pdf` with a safe filename; `GET /sessions/{id}/whatsapp.txt` returns `text/plain; charset=utf-8`. Both return 409 before confirmation. Add confirmed-session PDF/text links to both browser pages. Run `& $PY -m pytest tests/test_artefact.py tests/test_app.py -q` → all pass. Repeat Task 13's browser smoke and click the PDF link; verify ₹, each amount, total, delivery date, timestamp and the embedded attachment. Copy the WhatsApp text into a plain editor and compare. If the font does not display ₹, fix the font rather than silently changing amounts.

- [ ] **Step 6: Commit.** `git add src/parcha/artefact.py src/parcha/app.py tests/test_artefact.py assets/fonts; git commit -m "feat: issue customer-confirmed parcha"`.

### Task 15: Seeded SynthCall-IN manifest

**Files:** Create `src/parcha/lab/__init__.py`, `src/parcha/lab/dataset.py`, `scripts/make_synthcall.py`, `tests/test_dataset.py`; modify `.gitignore`.

- [ ] **Step 1: Write failing manifest tests.** `tests/test_dataset.py` checks a valid row round trip, duplicate IDs rejected, missing audio rejected before any STT call, and non-synthetic identifiers rejected. The last check uses a strict *allowlist* of the prewritten synthetic names/plates in the manifest, not an unreliable detector of real names.

```python
import pytest
from parcha.lab.dataset import Clip, load_manifest, make_prompts

def test_100_seeded_prompts_are_stable():
    first = make_prompts(seed=20261004)
    second = make_prompts(seed=20261004)
    assert first == second
    assert len(first) == 100
    assert len({row["id"] for row in first}) == 100
    assert all("amount_paise" in row["entities"] for row in first)
    assert all("reference_transcribe" in row for row in first)

def test_manifest_rejects_duplicate_id(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    line = '{"id":"s001","text":"pad saade chaar sau","reference_transcribe":"pad ₹450","entities":{"amount_paise":45000},"audio":"s001.wav","kind":"speech","seed":1}'
    manifest.write_text(line + "\n" + line + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_manifest(manifest, require_audio=False)
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_dataset.py -q` → missing lab module.

- [ ] **Step 3: Define a strict JSONL row.** Use Pydantic:

```python
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class Clip(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z][0-9]{3}$")
    text: str
    reference_transcribe: str  # fixed before inference; same ITN/script form expected from Prisma transcribe
    entities: dict[str, str | int]
    audio: str
    kind: Literal["speech", "reply", "engine_only"]
    seed: int
    source: Literal["timbre", "consented_script", "synthetic_noise"] = "timbre"
```

`load_manifest(path, require_audio=True)` resolves each `audio` against a single allowed `var/lab/audio/` root, rejects path escape/duplicate IDs and requires files when `require_audio`. `text` is the spoken prompt; `reference_transcribe` is a separately curated, locked `format=transcribe` reference with the expected ITN and script conventions. CER uses only `reference_transcribe` against Prisma's `transcribe` output. Keep both fields, and never rewrite the reference from a hypothesis after running the model.

- [ ] **Step 4: Generate and lock the 100 utterance *text* manifest.** `make_prompts(seed)` uses a table of at least 30 synthetic automotive part/brand *single words* and ten amount/date patterns including `saade chaar sau`, `pachaas`, `lakh`, `crore`, Monday evening and other windows. Cycle the 30 terms across 100 rows so each appears at least once, and make the first 30 rows the Oct 15 bias A/B sample; multiword names are split into valid single-word boost terms. Store both the spoken prompt and a separately curated ITN-form `reference_transcribe` with the expected script/numerals; do not compare a spoken `saade chaar sau` reference directly with a legitimate `₹450` hypothesis. Audit the reference format on ten probes, correct the manifest **before** the sweep, hash/lock it, and never edit it based on scored outputs. Store structured amounts/dates/part names explicitly. A fixed seed determines ordering, not the facts. Check in the text manifest at `data/synthcall_manifest.jsonl`.

Start `make_prompts` with this deterministic structure; expand the amount/date table with validated Hindi forms before producing audio:

```python
from random import Random

PART_WORDS = (
    "brake", "clutch", "piston", "chain", "sprocket", "bearing",
    "filter", "plug", "cable", "tyre", "tube", "rim", "fork", "shock",
    "battery", "starter", "alternator", "radiator", "coolant", "gasket",
    "valve", "camshaft", "carburetor", "injector", "silencer", "exhaust",
    "mirror", "headlamp", "indicator", "mudguard",
)
AMOUNTS = (
    ("saade chaar sau", 45000), ("pachaas", 5000),
    ("do sau", 20000), ("saat sau pachaas", 75000),
    ("ek hazaar", 100000), ("baarah sau", 120000),
    ("do hazaar pachaas", 205000), ("paanch sau", 50000),
    ("ek lakh", 10000000), ("ek crore", 1000000000),
)
DELIVERIES = (
    ("Somvaar shaam tak", "2026-10-05", "evening"),
    ("Mangalvaar subah tak", "2026-10-06", "morning"),
)

def make_prompts(seed: int) -> list[dict]:
    terms = list(PART_WORDS)
    Random(seed).shuffle(terms)
    rows = []
    for index in range(100):
        part = terms[index % len(terms)]
        spoken_amount, paise = AMOUNTS[index % len(AMOUNTS)]
        spoken_delivery, iso_date, window = DELIVERIES[index % len(DELIVERIES)]
        rows.append({
            "id": f"s{index + 1:03d}",
            "text": f"{part} ka part {spoken_amount} rupaye, {spoken_delivery}",
            "reference_transcribe": f"{part} ka part ₹{paise // 100:,}, {spoken_delivery}",
            "entities": {"part": part, "amount_paise": paise,
                         "delivery_date": iso_date, "delivery_window": window},
            "audio": f"s{index + 1:03d}.wav", "kind": "speech",
            "seed": seed, "source": "timbre",
        })
    return rows
```

`₹1 crore` exceeds the card's Task 6 per-item limit; it is a *lab-only* ITN stress line and must never be fed to the product extractor as a valid workshop estimate. Keep the lab entity bound separate from the product card bound and record the deliberate out-of-domain example in the manifest.

The generated `reference_transcribe` is only a starting template. The script and date wording may be normalized differently by `hi-IN`; curate all 100 fixed references from the intended utterance/ITN convention before running the scored grid, record the curator and manifest hash, then freeze the file. A pilot may reveal the convention but must not be used to copy model errors into the reference.

- [ ] **Step 5: Make audio only after budget check.** `scripts/make_synthcall.py --live --manifest data/synthcall_manifest.jsonl --max-credits 2000` calls Timbre once per unique text, saves raw μ-law and decoded 8 kHz WAV under ignored `var/lab/audio/`, and records voice, model, request timestamp, sample rate and text hash. Before call 1, forecast TTS cost using Task 3's observed per-character or per-call rate; stop if the balance would breach the reserved cap. For 50 short replies, record scripted/consented humans or synthesize voices and label source truthfully; create 20 engine-only clips from the consented/synthetic ambience. Do not imply Timbre speech is a real garage recording.

- [ ] **Step 6: Run green and commit.** `& $PY -m pytest tests/test_dataset.py -q` → all pass. `git add src/parcha/lab data/synthcall_manifest.jsonl scripts/make_synthcall.py tests/test_dataset.py .gitignore; git commit -m "feat: create seeded synthetic call manifest"`. Audio remains ignored.

### Task 16: Lab metrics, frame erasure and budgeted runner

**Files:** Create `src/parcha/lab/metrics.py`, `src/parcha/lab/runner.py`, `tests/test_lab_metrics.py`, `tests/test_lab_runner.py`; modify `src/parcha/audio.py`.

- [ ] **Step 1: Write failing metric tests.** Use tiny strings and explicit denominators:

```python
from parcha.lab.metrics import cer, amount_match, short_reply_drop, hallucinated_words

def test_cer_and_empty_reference():
    assert cer("haan", "han") == 0.25
    assert cer("", "") == 0.0
    assert cer("", "engine") == 1.0  # non-speech hallucination is also counted separately
    assert cer("pad ₹450", "pad ₹450") == 0.0  # not compared to spoken "saade chaar sau"

def test_amount_match_uses_rupees_not_string_format():
    assert amount_match(45000, "₹450")
    assert amount_match(45000, "450 रुपये")
    assert not amount_match(45000, "₹400")

def test_reply_and_non_speech_metrics():
    assert short_reply_drop("haan", "") is True
    assert short_reply_drop("nahi", "नहीं") is False
    assert hallucinated_words("engine start") == 2
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_lab_metrics.py -q` → missing module.

- [ ] **Step 3: Implement metrics with documented normalization.** NFKC Unicode normalize, casefold Latin and collapse whitespace; keep Hindi letters. Levenshtein character distance uses a one-row dynamic program and `max(1, len(reference))` denominator, with the special empty-reference rule above. The runner must pass `clip.reference_transcribe` (locked ITN form), never `clip.text` (spoken form), as the CER reference for a Prisma `transcribe` hypothesis. `amount_match` extracts a numeric rupee amount, converts to paise and compares; if the transcript has only worded Hindi with no normalized digits, return `False` and record an ITN failure rather than guessing. `short_reply_drop` accepts only clear yes/no variants; `hallucinated_words` counts whitespace tokens on engine-only clips. For per-entity rates, store `{correct, total}`, never only percentages. Add tests for `₹3.50`, Indian commas and a missing amount.

```python
def cer(reference: str, hypothesis: str) -> float:
    ref, hyp = normalize(reference), normalize(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    row = list(range(len(hyp) + 1))
    for i, char in enumerate(ref, 1):
        next_row = [i]
        for j, other in enumerate(hyp, 1):
            next_row.append(min(next_row[-1] + 1, row[j] + 1,
                                row[j-1] + (char != other)))
        row = next_row
    return row[-1] / len(ref)
```

- [ ] **Step 4: Write and implement deterministic loss test.** In `audio.py`, `erase_frames(wav, loss_percent, seed)` divides decoded mono 8 kHz PCM into 160-sample (20 ms) frames, uses `random.Random(seed)` to replace a measured fraction with zero samples, and returns WAV plus `erased_frames/total_frames`. This is *post-decode frame erasure*, not a claim of actual carrier packet-loss concealment. Test `0%` returns identical PCM and `100%` returns silence; same seed gives same selected frames.

- [ ] **Step 5: Write a failing runner test with fake Prisma.** Two manifest clips × two codecs × two SNRs × one loss rate yield eight baseline rows. Each row includes the frozen `reference_transcribe`, input hash, codec, target/measured SNR, loss percent, `variant="baseline"`, model settings, transcript, duration, latency and credit forecast. A test clip whose spoken `text` says `saade chaar sau` but whose `reference_transcribe` and fake hypothesis both say `₹450` must have CER 0. A budget that fits seven rows must stop *before* the eighth paid call and write a resumable checkpoint. Caching the degraded WAV must depend on source/noise hashes + FFmpeg version + codec + SNR + loss + seed. Add a second test for one-clip `bias` ablation: it yields paired `bias_off` and `bias_1_0` rows with identical clip/codec/SNR/loss/seed and `mode="verbatim"`; those rows use a separately frozen `reference_verbatim` for any CER, or omit CER and score only part names.

- [ ] **Step 6: Implement the runner.** The default baseline grid is 100 speech utterances × `{g711, amr_nb_4750}` × `{clean, 10, 5, 0 dB}` × `0% loss` = 800 STT requests. Run the loss dimension on a bounded 5 dB subset at `{0, 2, 5}%` erasure only if the observed credit rate permits it; the smaller spec fallback is 60 × 2 × 3 baseline. Add reply/engine-only clips as separately budgeted slices. Implement `--ablation bias` on the same first 30 clips at one fixed codec/SNR/loss setting: for each clip call Prisma in `verbatim` once without bias and once with the validated single-word list at score 1.0 (optionally score 1.5 in a separately budgeted third row). Record `variant="bias_off"` or `"bias_1_0"` with the same pairing key and compute exact part-name recovery. CLI requires `--live --manifest --credits-per-second --remaining-credits --max-credits --output`; with no `--live`, print the forecast and exit. Before each STT request, calculate the forecast for that clip duration, check remaining allowance, then call Prisma once. A 403/429 stops, writes a checkpoint, and does not auto-retry. Store private rows under `var/lab/private/results.jsonl`. Include the street-noise file hash and FFmpeg version in each cache key and row so a changed source/encoder cannot reuse old audio.

```python
for clip in clips:
    for codec, snr, loss in settings:
        cache_key = sha256(f"{source_hash}:{noise_hash}:{ffmpeg_version}:{codec}:{snr}:{loss}:{clip.seed}".encode()).hexdigest()
        degraded = cache_or_build(cache_key, clip, codec, snr, loss)
        projected = duration_seconds(degraded) * credits_per_second
        if spent + projected > max_credits or projected > remaining_credits - spent:
            save_checkpoint(); raise BudgetExceeded("stopped before paid call")
        started = monotonic()
        hypothesis = prisma.transcribe(degraded, mode="transcribe")
        latency_ms = round((monotonic() - started) * 1000)
        append_private_row(clip, codec, snr, loss, "baseline", hypothesis, latency_ms,
                           projected, reference=clip.reference_transcribe,
                           cer_value=cer(clip.reference_transcribe, hypothesis))
        spent += projected
```

- [ ] **Step 7: Run green and commit.** `& $PY -m pytest tests/test_lab_metrics.py tests/test_lab_runner.py -q` → all pass. `git add src/parcha/audio.py src/parcha/lab/metrics.py src/parcha/lab/runner.py tests/test_lab_metrics.py tests/test_lab_runner.py; git commit -m "feat: run budgeted line noise sweep"`.

### Task 17: Private report and guarded public delta export

**Files:** Create `src/parcha/lab/report.py`, `tests/test_lab_report.py`; modify `docs/gates.md`.

- [ ] **Step 1: Write failing report tests.** Feed three synthetic result rows: `bias_off` and `bias_1_0` for the *same* clip/codec/SNR/loss/seed, plus one engine-only row. Private output must include absolute CER/entity accuracy by codec/SNR/loss with counts and settings. Public candidate must contain only the paired part-name exact-match delta, `measured by us`, N, date and settings; no other vendor name and no standalone absolute Prisma CER/WER. With no recorded organizer permission, public export must raise an error.

```python
import pytest
from parcha.lab.report import public_delta, private_summary

def test_public_export_fails_closed_without_written_answer(rows):
    with pytest.raises(PermissionError):
        public_delta(rows, organizer_consent=False, consent_ref=None, date="2026-10-19")

def test_delta_is_paired_and_labelled(rows):
    text = public_delta(rows, organizer_consent=True,
                        consent_ref="docs/gates.md#organizer-reply-2026-10-10",
                        date="2026-10-19")
    assert "measured by us" in text.lower()
    assert "N=" in text
    assert "2026-10-19" in text
    assert "Whisper" not in text and "Google" not in text
```

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_lab_report.py -q` → missing module.

- [ ] **Step 3: Implement pairing and private output.** Group rows by `(clip_id, codec, snr, loss, seed)` for same-clip A/B; require exactly one `bias_off` and one `bias_1_0` row per pair. `private_summary` records raw counts, failures, total requests, estimated and dashboard-observed credits, CER (including denominator), amount/part/date exact-match, short-reply drop, engine-only hallucination, latency percentiles, FFmpeg version and model settings. Write `var/lab/private/report.md` and CSV curves there only. Label each number `N utterances`, settings and date; do not include a benchmark against another vendor.

- [ ] **Step 4: Implement guarded public export.** `public_delta` requires a reference to the written organizer answer in `docs/gates.md` and an explicit `--organizer-consent-recorded` CLI switch. The implemented first export is Task 16's `bias_off` versus `bias_1_0` verbatim part-name exact-match gain on paired clips. Compute the percentage-point difference with numerator, denominator, N, settings and date; refuse unmatched rows, competitor model names and any absolute WER/CER value in the output. Other ablations (denoise, read-back, VAD preset, latency decomposition) can be added only after their paired runs exist. A single own-system end-to-end outcome is allowed only if the organizer response explicitly permits it; otherwise leave it private. The public candidate is a Markdown/PNG draft for human review, never auto-posted.

- [ ] **Step 5: Run green and commit.** `& $PY -m pytest tests/test_lab_report.py -q` → all pass. Generate a private report from fake rows; inspect that `var/lab/private/` is ignored with `git status --short`. `git add src/parcha/lab/report.py tests/test_lab_report.py docs/gates.md; git commit -m "feat: report lab deltas with publication guard"`.

### Task 18: Isolated WebSocket flush experiment

**Files:** Create `scripts/ws_flush_probe.py`, `tests/test_ws_frames.py`; modify `docs/gates.md`.

- [ ] **Step 1: Write a failing frame test.** `pcm_frames(wav)` yields exactly 1024-byte signed 16-bit little-endian mono chunks, including zero padding in its last chunk. `silence_frames(8000, 500)` yields at least 500 ms of 1024-byte zero frames. Test frame count, byte count and all-zero tail with a 1.03-second WAV; no socket is opened in tests.

- [ ] **Step 2: Run red.** `& $PY -m pytest tests/test_ws_frames.py -q` → helper missing.

- [ ] **Step 3: Reuse Task 5's framing and run a larger bounded flush probe.** Read 8 kHz mono 16-bit PCM from WAV and split in 512-sample chunks via `parcha.gnani_ws.pcm_frames`. Send frames at 64 ms cadence. Use the same documented telephony headers as Task 5. After each utterance, send at least eight zero frames (512 ms), wait for a `transcript` message with a bounded timeout, then close. A receiver task must run while the sender sends to avoid missing server messages. `ws_flush_probe.py` sweeps silence tail lengths around the 500 ms preset and measures final `haan` recovery independently of the Oct 10 short-reply gate; it does not redefine that earlier result. Record close codes, `processing` and `transcript` events and last-word recovery. Do not log the API key.

```python
async with websockets.connect(url, additional_headers=headers, open_timeout=10) as ws:
    receiver = asyncio.create_task(collect_events(ws))
    for frame in pcm_frames(wav) + silence_frames(8000, 500):
        await ws.send(frame)
        await asyncio.sleep(0.064)
    events = await asyncio.wait_for(receiver, timeout=10)
```

`pcm_frames`/`silence_frames` can return lists for this short probe. The collector must stop after a final transcript or a bounded deadline; it must not await socket close forever.

- [ ] **Step 4: Measure the gate and keep REST safe.** `& $PY scripts/ws_flush_probe.py --live --manifest var/gates/haan_ws.jsonl --max-credits 2000` runs a bounded list of short clips only after Task 3's credit rate is known. If final `haan` recovery is ≥95%, document it; if lower or inconclusive, keep the product's REST reply path. Passing this experiment does not automatically switch the app to WS, because a browser/WS proxy and realtime pacing would require a separate implementation and review. Record the result by Oct 19.

- [ ] **Step 5: Run green and commit.** `& $PY -m pytest tests/test_ws_frames.py -q` → all pass. `git add scripts/ws_flush_probe.py tests/test_ws_frames.py docs/gates.md; git commit -m "test: measure 8k websocket end-of-turn recovery"`.

### Task 19: Full demo rehearsal, documentation and final verification

**Files:** Modify `README.md`, `docs/gates.md`; create `docs/demo.md`; inspect all changed files and private outputs.

- [ ] **Step 1: Write the 60-second demo run sheet.** `docs/demo.md` follows the locked storyboard: customer reaction 0–3 s; workshop and problem 3–8 s; noisy dictation/card 8–12 s; simulated read-back, correction and confirmation 12–40 s; human reaction 40–46 s; own labelled proof card 46–53 s only if permitted; customer line/hashtags 53–60 s. During the call display the exact simulation disclosure with the *actual* codec/SNR. Scripted actors and synthetic data are disclosed. Obtain filming consent by Oct 12 or use the spec's classmate/own-scooter fallback.

- [ ] **Step 2: Update README from observed behavior.** Provide Python/FFmpeg prerequisites, `py -3.12 -m venv .venv`, `pip install -e '.[dev]'`, `.env.example` copy instructions, how to start Uvicorn, two-browser localhost flow, optional trusted HTTPS phone flow, tests, lab `--live` flag and credit cap, PDF/text outputs, and no-PSTN/no-real-message scope. Remove existing `legally confirmed` wording and any claim that an actual call is placed.

- [ ] **Step 3: Complete the remaining dated gates.** Oct 12 casting decision. Oct 15 run 30 part/brand names with `format=verbatim` and bias scores 1.0 and 1.5 against no bias; keep bias only if measured gain. Oct 19 finish the budgeted 100 × 2 × 4 baseline (or documented 60 × 2 × 3 reduction), loss subset, private curves and one permitted delta candidate; record WS result. If a gate was missed or blocked, mark it `not run` with reason, not `pass`.

- [ ] **Step 4: Run offline verification.** From repo root:

```powershell
$PY = '.\.venv\Scripts\python.exe'
& $PY -m pytest -q
git diff --check
git status --short
```

Expected: all offline tests pass, no whitespace errors, and only intended tracked files. Do not call live APIs from pytest. Inspect `.gitignore` behavior for `.env`, `var/`, certificates and private reports.

- [ ] **Step 5: Run one live synthetic end-to-end rehearsal.** With observed credits still under cap: mechanic records near the engine or a disclosed synthetic-noise playback; Prisma dual-pass creates a reviewed card; customer hears Timbre 8 kHz through declared degradation, gives one targeted correction, hears the revised total, says a clear `haan`, and downloads PDF/text. Check computed money, date, revision, transcripts, timestamps, disclosure, browser MIME types and displayed PDF. Measure end-to-end latency; compare to any latency target as an observation, not an invented pass. Stop if audio/amount is wrong.

- [ ] **Step 6: Audit claims and commit docs.** Public assets mention only measured own-system deltas with N/settings/date after the organizer's written permission; absolute CER/SNR curves stay private. Check no real names/plates, raw clips, keys, certificates or private metrics appear in `git status`. Use @verification-before-completion, then `git add README.md docs/demo.md docs/gates.md; git commit -m "docs: verify honest demo and gate evidence"`.

## Milestones and decision order

| Date | Required outcome | Work order |
|---|---|---|
| Oct 6–10 | Credit, workshop-amount, TTS round-trip and short-reply gates | Tasks 1–5, before building the UI |
| Oct 11–17 | Reviewable card, explicit read-back and guarded correction | Tasks 6–12 |
| Oct 18–22 | Customer page, confirmed outputs, lab and filming | Tasks 13–19 |
| Oct 25–Nov 9 | Public posts and replies from the separate social plan in the spec | Reserve 20–30 h; no unbudgeted speech grid |

The build budget is approximately 45–55 hours of the 75-hour project allocation. The 40% speech-credit ceiling is measured with Task 3 before the 100-utterance sweep. If the Oct 10 reply gate fails, shorten the prompt only after measuring the longer phrase; if it still fails, switch the demo to the spec's walk-up mode. Do not add a new subsystem to conceal a failed gate.

