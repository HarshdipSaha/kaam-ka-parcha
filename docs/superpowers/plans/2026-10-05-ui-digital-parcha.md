# UI Redesign "Digital Parcha" Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the dark English developer-dashboard pages with a Hindi-first "digital parcha":
- **Mechanic:** one big mic and a bill-book slip that asks for re-checks row by row.
- **Vehicle owner:** a call-style page that ends in a UPI-receipt seal.
- **Verify:** a DigiLocker-style page.
- **Stage:** a side-by-side view for the 60-second demo.

All of it is covered by offline Playwright tests.

**Architecture:** FastAPI + Jinja + vanilla JS stays, with no build step:
- One shared stylesheet holds the design tokens and components.
- An SVG icon sprite is shared by the templates and the JS.
- A base template and a slip macro render the first paint on the server.
- `ui.js` (`window.ParchaUI`) holds pure helpers and DOM components and only ever writes text nodes.
- `app.js` keeps today's endpoint and revision flow and renders through `ParchaUI`.
- A small server module, `presentation.py`, formats rupees and Hindi labels for templates and the payload.
- A new browser-test seam runs an in-process uvicorn on the offline fakes with Chromium's fake microphone.

**Tech Stack:** Python 3.12+, FastAPI, Jinja2, vanilla ES2020 JavaScript, CSS custom properties, Google Fonts (Mukta, Baloo 2), pytest, Playwright for Python + pytest-playwright (new `e2e` extra), uvicorn, httpx, FFmpeg.

**Spec:** [`docs/specs/ui-digital-parcha-spec.md`](../../specs/ui-digital-parcha-spec.md) is authoritative. Research: `docs/research/R10`–`R14`. **Prerequisite plan:** [`2026-10-05-money-path-safety.md`](2026-10-05-money-path-safety.md) is executed **first**; this plan starts from its finished state.

## Global Constraints

- **Order:** run this plan only after the money-path plan's Tasks 1–6 are merged. Task 0 checks this.
- **Money-path contracts stay unchanged:**
  - HTTP 422 `detail == {"repeat": true, "reason": …}` from intake and re-ask;
  - `session_payload["abstentions"]`;
  - the strings `REPEAT_MESSAGE` and `ABSTAIN_LABELS`;
  - `describeHttpError(detail, status)` behaviour;
  - the `.abstain-reason` class;
  - amounts only from the grammar, so the UI offers no typed or tapped amount entry.
- Money is integer paise. Display goes through `format_inr` (Python) or `ParchaUI.formatRupees` (JS) only:
  - Latin digits, en-IN grouping (`₹1,23,456`);
  - paise only when non-zero (`₹45.50`);
  - unknown amount `₹ —`, incomplete total `अधूरा`.
- State names are unchanged (`draft`, `review`, `awaiting_reply`, `fallback_ready`, `confirmed`), as are the revision rules, consent logging, fallback rules and artefact sealing.
- **Tokens:**
  - `--counter #F3EEE3`, `--paper #FFFDF6`, `--paper-pink #FCE4EC`, `--paper-yellow #FFF3C4`;
  - `--ink #1B2433`, `--ink-muted #5B6472`, `--neela #1F3A8A`, `--haldi #F2B705` (fill only);
  - `--hara #0E7A41`, `--amber #B45309`, `--sindoor #B3261E` (errors only), `--serial #C0262D`, `--jamuni #5B2E91`;
  - `--rule #D9CFBC`, `--wa #008069`.
- **Type:** Mukta 400/600/800 (UI and amounts, `tabular-nums`) and Baloo 2 800 (brand and stamp only). Body 18 px, line-height 1.6, slip rows 20 px, total 44 px.
- **Sizes:** mic 96 px; primary actions 64 px tall and full width; every other control ≥ 48 px with 8 px gaps; no swipe or long-press. Single column, max 480 px; sticky bottom dock with safe-area inset. Light theme only. `prefers-reduced-motion` disables animation.
- **Copy:** Hindi in Devanagari is primary, with an English sub-line in `.en`. Exact strings come from the spec's "Fixed strings" table. The sealed word is **मंज़ूर**, never "पक्का बिल".
- **Kept verbatim:**
  - the English simulation disclosure sentence (with its Hindi translation added above it);
  - the titles `Kaam ka Parcha — Workshop Estimate` and `Kaam ka Parcha — Customer Estimate Review`;
  - the badge `Synthetic demo data`;
  - the legal strings on `/verify` (`Audit Verification`, `BSA 2023 §§ 61–63 Compliant`, `DPDP Act 2023`, the vehicle).
- **Preserved element ids:**
  - workshop: `record`, `stop`, `message`, `transcript`, `card`, `start-readback`, `customer-link`, `review-section`, `review-count`;
  - customer: `disclosure`, `readback-player`, `customer-record`, `customer-stop`, `customer-status`, `customer-message`, `confirmed-banner`, `fallback-banner`, `fallback-approve`, `fallback-reject`, `download-pdf-link`, `whatsapp-link`, `dpdp-consent-checkbox`, `items-tbody`, `total-cell`, `delivery-info`, `card-status-badge`, `card-revision-badge`;
  - verify: `manifest-digest`, `dpdp-consent-digest`, `dpdp-compliance-panel`.
- Server-derived text (labels, quotes, transcripts, messages) is inserted as text nodes only. No `innerHTML` anywhere in `static/`.
- Budget: our own CSS + JS + SVG ≤ 60 KB unminified; no framework, bundler or Node.
- Ordinary tests consume **no credits**. Browser tests are opt-in (`-m e2e`), offline, and write screenshots only under the ignored `var/e2e/`.
- Consent starts unticked, and ticking it calls `POST /sessions/{id}/consent`. The reply mic is disabled until consent is given. Hint chips are never buttons.

## Review Focus

These are inputs the spec implies but no headline flow exercises, most likely first. Each has a test in the owning task.

1. **The browser blocks the microphone** (permission denied or no `MediaRecorder`). Expected: Hindi guidance ("माइक की इजाज़त दें…"), with the mic usable again rather than stuck. *Test: Task 6, `test_mic_blocked_shows_hindi_guidance`.*
2. **An extracted label contains markup** (`<img onerror>` from a hostile or garbled LLM output). Expected: it shows literally as text and never runs. *Test: Task 6, `test_hostile_label_renders_as_text`.*
3. **The read-back audio fails to load** (404, stale revision or codec). Expected: the slip and caption stay; the call status says the audio didn't play; the reply mic is still available after consent. *Test: Task 7, `test_audio_failure_keeps_reply_available`.*
4. **The parcha changed while the owner was replying** (HTTP 409). Expected: "पर्चा बदल गया है — पेज ताज़ा करें।" plus a reload button, with no half-updated state. *Test: Task 7, `test_stale_reply_offers_reload`.*
5. **A 360 px phone with a very long Devanagari label and an abstained amount.** Expected: no sideways scroll; every control ≥ 48 px; mic ≥ 88 px. *Test: Task 9, `test_layout_fits_and_targets_are_thumb_sized[360x800]`.*

---

## Task 0: Pre-flight (no code)

- [ ] **Step 1: Confirm the money-path plan has landed.**
  Run: `git log --oneline -15` and `Select-String -Path src\parcha\app.py,src\parcha\static\app.js,tests\fakes.py -Pattern "abstention_reasons","describeHttpError","ABSTAIN_LABELS","INTAKE_V","class ScriptedPrisma"`
  Expected: all five patterns found. **If any is missing, stop and finish the money-path plan first.**
- [ ] **Step 2: Baseline.**
  ```powershell
  .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
  ffmpeg -hide_banner -encoders | findstr /i "pcm_mulaw"     # must print
  .\.venv\Scripts\python.exe -m pytest -q                      # green, as the money-path plan left it
  ```
- [ ] **Step 3: Note** the current `git rev-parse HEAD` in `aidlc-docs/efforts/010-ui-digital-parcha-plan/construction.md` as the starting point.

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `src/parcha/presentation.py` | create | `format_inr`, `hindi_delivery`, `kind_label`, `status_label`, `parcha_no`, `latest_log_text`, `register_filters` |
| `src/parcha/app.py` | modify | Jinja filters; payload fields `parcha_no`, `status_label`, `mechanic_transcript`, `readback_text`; strict-JSON read-back; template contexts; `GET /stage` |
| `src/parcha/static/parcha.css` | create | All tokens and components (replaces three inline `<style>` blocks) |
| `src/parcha/static/icons.svg` | create | Icon sprite (`mic`, `stop`, `play`, `pause`, `check`, `part`, `labour`, `copy`, `chat`) |
| `src/parcha/static/ui.js` | create | `window.ParchaUI`: formatting, field questions, stage, diff, safe DOM, slip, stepper, mic dock, toast, clipboard, poll, API errors; also hosts `REPEAT_MESSAGE` / `ABSTAIN_LABELS` / `describeHttpError` moved from `app.js` |
| `src/parcha/static/app.js` | rewrite | Workshop and customer flows on top of `ParchaUI`; same endpoints and window exports |
| `src/parcha/templates/base.html` | create | `lang="hi"`, viewport, fonts, stylesheet, blocks |
| `src/parcha/templates/_slip.html` | create | `slip(card, total_paise, parcha_no, copy, stamp)` macro (same markup as `ParchaUI.renderSlip`) |
| `src/parcha/templates/workshop.html`, `customer.html`, `verify.html` | rewrite | Pages extending `base.html` |
| `src/parcha/templates/stage.html` | create | Two phone frames for the demo |
| `pyproject.toml` | modify | `e2e` extra; `e2e` marker deselected by default; package data `static/*.css`, `static/*.svg` |
| `tests/fakes.py` | modify | `fake_settings()`, `SilentTimbre`, `StagePrisma` |
| `tests/conftest.py` | modify | `fake_services` uses `fake_settings()` |
| `tests/test_presentation.py`, `tests/test_ui_contract.py`, `tests/test_pages.py` | create | Unit and HTTP-seam tests |
| `tests/e2e/__init__.py`, `conftest.py`, `helpers.py` | create | Browser seam |
| `tests/e2e/test_harness.py`, `test_ui_helpers.py`, `test_verify_page.py`, `test_workshop_flow.py`, `test_customer_flow.py`, `test_stage.py`, `test_responsive.py` | create | Browser tests |
| `README.md`, `docs/ui/*.png`, AIDLC effort 010 | modify/create | Walkthrough screenshots and records |

---

### Task 1: Presentation helpers (server)

**Files:**
- Create: `src/parcha/presentation.py`
- Test: `tests/test_presentation.py`

**Interfaces:**
- Consumes: `parcha.schema.Delivery`, `parcha.schema.TranscriptLog`.
- Produces:
  - `format_inr(paise: int | None) -> str`
  - `hindi_delivery(delivery: Delivery | None) -> str`
  - `kind_label(kind: str) -> str`
  - `status_label(status: str) -> str`
  - `parcha_no(session_id: str) -> str`
  - `latest_log_text(logs, *, role: str, mode: str | None = None) -> str | None`
  - `register_filters(env) -> None`, which adds the filters `inr`, `hindi_delivery`, `kind_hi`, `status_hi`.

- [ ] **Step 1: Write the failing tests** in `tests/test_presentation.py`:

```python
from datetime import date, datetime, timezone

import pytest

from parcha.presentation import (
    format_inr, hindi_delivery, kind_label, latest_log_text, parcha_no, status_label,
)
from parcha.schema import Delivery, TranscriptLog


@pytest.mark.parametrize("paise, text", [
    (0, "₹0"), (65000, "₹650"), (4550, "₹45.50"), (125000, "₹1,250"),
    (12345600, "₹1,23,456"), (10000000, "₹1,00,000"), (10000000000, "₹10,00,00,000"),
    (None, "₹ —"),
])
def test_format_inr_groups_the_indian_way(paise, text):
    assert format_inr(paise) == text


@pytest.mark.parametrize("bad", [True, 450.0, "450"])
def test_format_inr_rejects_non_integer_paise(bad):
    with pytest.raises(TypeError):
        format_inr(bad)


def test_hindi_delivery_names_weekday_date_and_window():
    d = Delivery(date=date(2026, 10, 6), window="evening", spoken="Mangalvaar shaam tak")
    assert hindi_delivery(d) == "मंगलवार, 6 अक्टूबर · शाम"
    assert hindi_delivery(Delivery(date=date(2026, 10, 5), window="morning", spoken="x")) == "सोमवार, 5 अक्टूबर · सुबह"


def test_hindi_delivery_when_missing():
    assert hindi_delivery(None) == "अभी तय नहीं"


def test_kind_and_status_labels_are_hindi():
    assert kind_label("part") == "पार्ट"
    assert kind_label("labour") == "लेबर"
    assert status_label("review") == "जाँच बाकी"
    assert status_label("awaiting_reply") == "ग्राहक का जवाब बाकी"
    assert status_label("fallback_ready") == "बटन से पुष्टि"
    assert status_label("confirmed") == "मंज़ूर"


def test_parcha_no_is_six_digits_and_deterministic():
    assert parcha_no("abc") == parcha_no("abc")
    assert len(parcha_no("abc")) == 6 and parcha_no("abc").isdigit()
    assert parcha_no("abc") != parcha_no("abd")


def test_latest_log_text_picks_the_newest_matching_log():
    when = datetime(2026, 10, 5, tzinfo=timezone.utc)
    logs = (
        TranscriptLog(role="mechanic", mode="verbatim", text="pehla", recorded_at_utc=when),
        TranscriptLog(role="system", mode="timbre_readback", text="aapki gaadi", recorded_at_utc=when),
        TranscriptLog(role="mechanic", mode="reask:items.part-1.amount_paise", text="paanch sau", recorded_at_utc=when),
    )
    assert latest_log_text(logs, role="mechanic") == "paanch sau"
    assert latest_log_text(logs, role="system", mode="timbre_readback") == "aapki gaadi"
    assert latest_log_text(logs, role="customer") is None
```

- [ ] **Step 2: Run it to see it fail.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_presentation.py`. Expected: `ModuleNotFoundError: No module named 'parcha.presentation'`.

- [ ] **Step 3: Implement** `src/parcha/presentation.py`:

```python
"""Display helpers for templates and the session payload. Display only: money stays integer paise."""
from __future__ import annotations

import hashlib
from collections.abc import Sequence

from .schema import Delivery, TranscriptLog

HINDI_WEEKDAYS = ("सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार")  # date.weekday() order
HINDI_MONTHS = ("जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून",
                "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर")
WINDOW_HI = {"morning": "सुबह", "afternoon": "दोपहर", "evening": "शाम"}
KIND_HI = {"part": "पार्ट", "labour": "लेबर"}
STATUS_HI = {
    "draft": "कच्चा पर्चा",
    "review": "जाँच बाकी",
    "awaiting_reply": "ग्राहक का जवाब बाकी",
    "fallback_ready": "बटन से पुष्टि",
    "confirmed": "मंज़ूर",
}


def _group_indian(n: int) -> str:
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    groups: list[str] = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return ",".join([*groups, tail])


def format_inr(paise: int | None) -> str:
    if paise is None:
        return "₹ —"
    if isinstance(paise, bool) or not isinstance(paise, int):
        raise TypeError("amount must be integer paise")
    sign = "-" if paise < 0 else ""
    rupees, rem = divmod(abs(paise), 100)
    text = f"{sign}₹{_group_indian(rupees)}"
    return f"{text}.{rem:02d}" if rem else text


def hindi_delivery(delivery: Delivery | None) -> str:
    if delivery is None:
        return "अभी तय नहीं"
    d = delivery.date
    return f"{HINDI_WEEKDAYS[d.weekday()]}, {d.day} {HINDI_MONTHS[d.month - 1]} · {WINDOW_HI[delivery.window]}"


def kind_label(kind: str) -> str:
    return KIND_HI.get(kind, kind)


def status_label(status: str) -> str:
    return STATUS_HI.get(status, status)


def parcha_no(session_id: str) -> str:
    """Six-digit serial for the slip, like the red number on a bill book. Stable per session."""
    return f"{int(hashlib.sha256(session_id.encode('utf-8')).hexdigest(), 16) % 1_000_000:06d}"


def latest_log_text(logs: Sequence[TranscriptLog], *, role: str, mode: str | None = None) -> str | None:
    for log in reversed(logs):
        if log.role == role and (mode is None or log.mode == mode):
            return log.text
    return None


def register_filters(env) -> None:
    env.filters.update(inr=format_inr, hindi_delivery=hindi_delivery, kind_hi=kind_label, status_hi=status_label)
```

- [ ] **Step 4: Run the tests.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_presentation.py`. Expected: 16 passed.
- [ ] **Step 5: Commit.**
  `git add src/parcha/presentation.py tests/test_presentation.py` then `git commit -m "feat(ui): presentation helpers for Indian rupees and Hindi labels"`

---

### Task 2: Payload and route contract for the redesign

**Files:**
- Modify: `src/parcha/app.py` (imports; `session_payload`; `create_app`; `customer_view` context; `start_readback` response; `verify_session` HTML context)
- Test: `tests/test_ui_contract.py`

**Interfaces:**
- Consumes: Task 1 functions, and `abstention_reasons(session)` from the money-path plan (already in `app.py`).
- Produces:
  - `session_payload(session)` keys, all kept, plus `parcha_no: str`, `status_label: str`, `mechanic_transcript: str | None`, `readback_text: str | None`;
  - `json_safe(value) -> value` (non-finite floats become `None`);
  - template filters `inr`, `hindi_delivery`, `kind_hi`, `status_hi`;
  - template context `parcha_no` and `readback_text` on `customer.html`, and `parcha_no` on `verify.html`.

- [ ] **Step 1: Write the failing tests** in `tests/test_ui_contract.py`:

```python
import json

from fastapi.testclient import TestClient

from parcha.app import create_app


def _reject_constant(name):
    raise ValueError(f"non-JSON constant {name}")


def _intake(client, sid, rev=0):
    return client.post(f"/sessions/{sid}/intake", data={"expected_revision": rev},
                       files={"audio": ("a.wav", b"bytes", "audio/wav")})


def test_payload_carries_display_fields(fake_services):
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    body = _intake(client, sid).json()
    assert len(body["parcha_no"]) == 6 and body["parcha_no"].isdigit()
    assert body["status_label"] == "जाँच बाकी"
    assert "front brake pad" in body["mechanic_transcript"]
    assert body["readback_text"] is None
    assert body["abstentions"] == {}          # money-path key still present


def test_readback_response_is_strict_json_when_no_noise_is_mixed(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    fake_services.workflow.noise_wav = None   # measured SNR becomes +inf
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    rev = _intake(client, sid).json()["revision"]
    res = client.post(f"/sessions/{sid}/readback", data={"expected_revision": rev})
    assert res.status_code == 200
    body = json.loads(res.text, parse_constant=_reject_constant)
    assert body["manifest"]["measured_snr_db"] is None
    assert client.get(f"/sessions/{sid}").json()["readback_text"] == body["text"]
```

- [ ] **Step 2: Run it to see it fail.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_ui_contract.py`. Expected: `KeyError: 'parcha_no'` and `ValueError: non-JSON constant Infinity`.

- [ ] **Step 3: Implement in `src/parcha/app.py`.**
  - Imports: `import math` and `from .presentation import latest_log_text, parcha_no, register_filters, status_label`.
  - Add the helper:

    ```python
    def json_safe(value):
        """Non-finite floats (SNR = inf when no noise is mixed) become None, so the body stays valid JSON."""
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, dict):
            return {k: json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [json_safe(v) for v in value]
        return value
    ```

  - Append to the dict that `session_payload` returns, after `"abstentions"`:

    ```python
            "parcha_no": parcha_no(session.id),
            "status_label": status_label(session.status),
            "mechanic_transcript": latest_log_text(session.logs, role="mechanic"),
            "readback_text": latest_log_text(session.logs, role="system", mode="timbre_readback"),
    ```

  - In `create_app`, right after `templates = Jinja2Templates(...)`: `register_filters(templates.env)`.
  - In `start_readback`: `content=json.dumps(json_safe(payload), ensure_ascii=False, allow_nan=False)`.
  - In the `customer_view` context, add `"parcha_no": parcha_no(session.id)` and `"readback_text": latest_log_text(session.logs, role="system", mode="timbre_readback")`.
  - In the `verify_session` HTML context, add `"parcha_no": parcha_no(session.id)`.

- [ ] **Step 4: Run the tests.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_ui_contract.py tests/test_app.py tests/test_app_repeat.py`. Expected: all pass.
- [ ] **Step 5: Commit.**
  `git add src/parcha/app.py tests/test_ui_contract.py` then `git commit -m "feat(api): display fields in session payload; strict-JSON read-back"`

---

### Task 3: Browser-test seam (offline, zero credits)

**Files:**
- Modify: `pyproject.toml`, `tests/fakes.py`, `tests/conftest.py` (`fake_services`)
- Create: `tests/e2e/__init__.py` (empty), `tests/e2e/conftest.py`, `tests/e2e/helpers.py`, `tests/e2e/test_harness.py`

**Interfaces:**
- Consumes: the money-path plan's `tests/fakes.py` (`INTAKE_T`, `INTAKE_V`) and `tests/conftest.py::FakeExtractor`.
- Produces:
  - `tests.fakes.fake_settings() -> Settings`;
  - `SilentTimbre` with `.calls` and `synthesize(text) -> bytes`;
  - `StagePrisma` with `.reset()`, `.script_intake(*, transcribe, verbatim)`, `.say(text)` and `.calls`;
  - `StageExtractor` (defined in `tests/e2e/conftest.py`) with `.mode`, one of `"complete" | "hostile_label" | "long_label"`;
  - session fixture `world` → `World(url, services, prisma, extractor)`;
  - pytest-playwright `page` bound to `world.url` at 360×800, touch, `hi-IN`, microphone and clipboard granted;
  - helpers `speak(surface, start, stop, seconds=0.8)`, `new_parcha(base_url, *, read_back=True) -> dict`, `reply_by_api(base_url, session) -> dict`;
  - the constant `SCREENS = Path("var/e2e")`.

- [ ] **Step 1: Packaging and markers** in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0"]
e2e = ["pytest>=8.0", "playwright>=1.45", "pytest-playwright>=0.5"]

[tool.setuptools.package-data]
parcha = ["templates/*.html", "static/*.js", "static/*.css", "static/*.svg", "assets/*.wav"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["e2e: browser tests (Playwright on offline fakes, zero credits)"]
addopts = "-m 'not e2e'"
```

  Keep any other keys the money-path plan added, such as a `bench` extra. Install: `.\.venv\Scripts\python.exe -m pip install -e ".[dev,e2e]"` then `.\.venv\Scripts\python.exe -m playwright install chromium`. A later `-m e2e` on the command line overrides `addopts`.

- [ ] **Step 2: Shared fakes.** Append to `tests/fakes.py`, then make `tests/conftest.py::fake_services` call `fake_settings()` instead of its inline `Settings(...)`:

```python
from parcha.config import Settings


def fake_settings() -> Settings:
    """Offline Settings for every app fixture, unit and browser."""
    return Settings(...)  # move the exact Settings(...) arguments from tests/conftest.py::fake_services here


class SilentTimbre:
    """Fake Timbre: one second of 8 kHz mu-law silence, so browsers get a playable WAV."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def synthesize(self, text: str) -> bytes:
        self.calls.append(text)
        return b"\xff" * 8000


class StagePrisma:
    """Fake Prisma for browser tests: answers by pass mode, not by call order.

    Every intake makes a transcribe and a verbatim pass (money-path plan), and browser flows can retry,
    so call-order scripts are brittle here. `say()` makes every pass hear the same words, which is what a
    customer reply or a mechanic re-ask needs.
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
```

  Only `fake_settings`, `SilentTimbre` and `StagePrisma` go in `tests/fakes.py`. They depend on nothing in `conftest.py`, so `conftest.py` can import `fake_settings` from it without a cycle. Drop the `Evidence, JobCard, LineItem` import if nothing else in the file uses it. `StageExtractor` lives in `tests/e2e/conftest.py` (Step 3), because it subclasses `conftest.py`'s `FakeExtractor`. If the money-path plan moved `FakeExtractor`, import it from its new home.

- [ ] **Step 3: The seam** in `tests/e2e/conftest.py`:

```python
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
```

  `tests/e2e/helpers.py`:

```python
"""Helpers shared by the browser tests."""
from __future__ import annotations

import time
from pathlib import Path

import httpx

SCREENS = Path("var/e2e")


def speak(surface, start, stop, seconds: float = 0.8) -> None:
    """Tap the mic, let Chromium's fake microphone record, then tap stop. surface: Page or FrameLocator."""
    start_loc = surface.locator(start) if isinstance(start, str) else start
    stop_loc = surface.locator(stop) if isinstance(stop, str) else stop
    start_loc.click()
    stop_loc.wait_for(state="visible")
    time.sleep(seconds)
    stop_loc.click()


def new_parcha(base_url: str, *, read_back: bool = True) -> dict:
    """Create a session through the public API, optionally up to awaiting_reply."""
    with httpx.Client(base_url=base_url, timeout=30) as http:
        sid = http.post("/sessions").json()["id"]
        body = http.post(f"/sessions/{sid}/intake", data={"expected_revision": 0},
                         files={"audio": ("estimate.wav", b"audio", "audio/wav")})
        body.raise_for_status()
        if read_back:
            http.post(f"/sessions/{sid}/readback", data={"expected_revision": body.json()["revision"]}).raise_for_status()
        return http.get(f"/sessions/{sid}").json()


def reply_by_api(base_url: str, session: dict) -> dict:
    """Post one customer reply; the words come from StagePrisma.say()."""
    with httpx.Client(base_url=base_url, timeout=30) as http:
        res = http.post(
            f"/sessions/{session['id']}/reply",
            data={"expected_revision": session["revision"], "readback_revision": session["readback_revision"],
                  "dpdp_consent": "true"},
            files={"audio": ("reply.wav", b"reply", "audio/wav")},
        )
        res.raise_for_status()
        return res.json()
```

- [ ] **Step 4: A smoke test that works against today's page and the redesign alike.** `tests/e2e/test_harness.py`:

```python
import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import speak

pytestmark = pytest.mark.e2e


def test_workshop_dictation_reaches_a_complete_parcha(page):
    page.goto("/workshop")
    speak(page, "#record", "#stop")
    expect(page.locator("#card")).to_contain_text("front brake pad", timeout=15000)
    expect(page.locator("#start-readback")).to_be_enabled()
```

- [ ] **Step 5: Run.** `.\.venv\Scripts\python.exe -m pytest -q -m e2e tests/e2e/test_harness.py`. Expected: 1 passed. Then `.\.venv\Scripts\python.exe -m pytest -q`. Expected: the same count as Task 0, plus Tasks 1–2's tests; e2e tests are deselected.
- [ ] **Step 6: Commit.**
  `git add pyproject.toml tests/fakes.py tests/conftest.py tests/e2e` then `git commit -m "test(e2e): offline Playwright seam with fake microphone and mode-keyed Prisma"`

---

### Task 4: Design system, slip macro, and the verify page

**Files:**
- Create: `src/parcha/static/parcha.css`, `src/parcha/static/icons.svg`, `src/parcha/templates/base.html`, `src/parcha/templates/_slip.html`
- Rewrite: `src/parcha/templates/verify.html`
- Test: `tests/test_pages.py` (new), `tests/e2e/test_verify_page.py`

**Interfaces:**
- Consumes: Task 1 filters and Task 2 contexts (`parcha_no`).
- Produces:
  - **CSS class contract** used by Tasks 5–8: `.page`, `.sheet`, `.topbar`, `.brand`, `.en`, `.pill(--demo|--ok|--wait|--warn)`, `.notice[data-tone]`, `.stepper li[data-step][data-state]`, `.heard`, `.slip(--original|--duplicate)`, `.slip__head`, `.slip__serial`, `.slip__rows`, `.row(--flagged|--changed)`, `.row__icon`, `.row__label`, `.row__meta`, `.chip`, `.row__heard`, `.row__amount`, `.row__was`, `.row__ask`, `.row__question`, `.abstain-reason`, `.reask`, `.slip__total`, `.slip__total-v[data-incomplete]`, `.slip__delivery`, `.stamp`, `.empty`, `.flagbar`, `.dock[data-mic]`, `.dock__row`, `.dock__status`, `.mic(--stop)`, `.meter`, `.timer`, `.btn(--primary|--haan|--change|--wa|--ghost)`, `.share`, `.fineprint`, `.toast`, `.disclosure`, `.call[data-call]`, `.play`, `.call__progress`, `.call__caption .said`, `.consent`, `.hints`, `.hint(--haan|--change)`, `.fallback`, `.receipt`, `.status-line`, `.verdict(--ok|--pending)`, `.voice(--customer)`, `.tech`, `.kv`, `.hash`, `.phone`, `.stage`;
  - icon ids `mic`, `stop`, `play`, `pause`, `check`, `part`, `labour`, `copy`, `chat`, used as `/static/icons.svg#<id>`;
  - Jinja macro `slip(card, total_paise, parcha_no, copy="original", stamp=False)` emitting the ids `slip`, `parcha-no`, `items-tbody`, `total-cell`, `delivery-info`.

- [ ] **Step 1: Write the failing tests.** `tests/test_pages.py`:

```python
import re

from fastapi.testclient import TestClient

from parcha.app import create_app


def awaiting(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    rev = client.post(f"/sessions/{sid}/intake", data={"expected_revision": 0},
                      files={"audio": ("a.wav", b"x", "audio/wav")}).json()["revision"]
    client.post(f"/sessions/{sid}/readback", data={"expected_revision": rev})
    return client, sid, rev


def confirm(fake_services, client, sid, rev):
    fake_services.workflow.prisma.transcribe = lambda wav, mode, **kw: "हाँ ठीक है"
    res = client.post(f"/sessions/{sid}/reply", data={"expected_revision": rev, "readback_revision": rev},
                      files={"audio": ("r.wav", b"haan", "audio/wav")})
    assert res.json()["outcome"] == "confirmed"


def test_static_design_system_is_served(fake_services):
    client = TestClient(create_app(fake_services))
    css = client.get("/static/parcha.css")
    assert css.status_code == 200 and "--counter: #F3EEE3" in css.text and "prefers-reduced-motion" in css.text
    assert 'id="mic"' in client.get("/static/icons.svg").text


def test_unconfirmed_parcha_is_not_called_verified(fake_services):
    client, sid, _ = awaiting(fake_services)
    html = client.get(f"/verify/{sid}").text
    assert '<html lang="hi">' in html and "/static/parcha.css" in html
    assert "अभी मंज़ूर नहीं" in html and "असली पर्चा" not in html
    assert "Audit Verification" in html and "BSA 2023" in html and "Compliant" in html
    assert "var(--danger)" not in html


def test_confirmed_parcha_shows_verdict_slip_and_evidence(fake_services):
    client, sid, rev = awaiting(fake_services)
    confirm(fake_services, client, sid, rev)
    html = client.get(f"/verify/{sid}").text
    assert "असली पर्चा" in html and "Verified electronic record" in html
    assert "₹650" in html and "₹450" in html and "पार्ट" in html and "लेबर" in html
    assert "front brake pad" in html and "KA-01-AB-1234" in html and "DPDP Act 2023" in html
    assert re.search(r'id="manifest-digest"[^>]*>[0-9a-f]{64}<', html)
    assert "मंज़ूर" in html                     # the stamp
```

  `tests/e2e/test_verify_page.py`:

```python
import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import SCREENS, new_parcha, reply_by_api

pytestmark = pytest.mark.e2e


def test_verify_shows_a_big_verdict_and_folds_the_hashes(page, world):
    session = new_parcha(world.url)
    world.prisma.say("हाँ ठीक है")
    reply_by_api(world.url, session)
    page.goto(f"/verify/{session['id']}")
    expect(page.get_by_role("heading", name="असली पर्चा")).to_be_visible()
    expect(page.locator("#manifest-digest")).to_be_hidden()          # folded under "तकनीकी सबूत"
    page.get_by_text("तकनीकी सबूत").click()
    expect(page.locator("#manifest-digest")).to_be_visible()
    expect(page.get_by_role("img", name="मंज़ूर — Approved")).to_be_visible()
    page.screenshot(path=str(SCREENS / "verify-360.png"), full_page=True)
```

- [ ] **Step 2: Run them to see them fail.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_pages.py`. Expected: 404 on `/static/parcha.css`, and the old verify page lacks `lang="hi"`.

- [ ] **Step 3: Create `src/parcha/static/parcha.css`.**

```css
/* Kaam ka Parcha: "Digital Parcha" design system. Source of truth: docs/specs/ui-digital-parcha-spec.md */
:root {
  --counter: #F3EEE3; --paper: #FFFDF6; --paper-pink: #FCE4EC; --paper-yellow: #FFF3C4; --bubble: #E3F4E8;
  --ink: #1B2433; --ink-muted: #5B6472; --neela: #1F3A8A; --haldi: #F2B705; --hara: #0E7A41;
  --amber: #B45309; --sindoor: #B3261E; --serial: #C0262D; --jamuni: #5B2E91; --rule: #D9CFBC; --wa: #008069;
  --font: "Mukta", "Nirmala UI", "Noto Sans Devanagari", system-ui, sans-serif;
  --font-display: "Baloo 2", "Mukta", "Nirmala UI", sans-serif;
  --r-card: 6px; --r-btn: 12px; --r-pill: 999px; --r-sheet: 20px;
  --shadow-paper: 0 1px 0 rgba(27,36,51,.06), 0 8px 18px -8px rgba(27,36,51,.22);
  --shadow-dock: 0 -6px 16px rgba(27,36,51,.10);
  --tap: 48px; --tap-primary: 64px; --mic: 96px; --dock-h: 150px;
  --ease: cubic-bezier(.22,.8,.24,1); --spring: cubic-bezier(.34,1.56,.64,1);
}
*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--counter); color: var(--ink); font: 400 18px/1.6 var(--font); font-variant-numeric: tabular-nums; }
[hidden] { display: none !important; }
h1, h2, p { margin: 0; }
.page { min-height: 100dvh; padding-bottom: calc(var(--dock-h) + env(safe-area-inset-bottom)); }
.page--verify, .page--stage { padding-bottom: 24px; }
.sheet { max-width: 480px; margin: 0 auto; padding: 12px 16px 24px; display: grid; gap: 14px; }
.en { display: block; font-size: .78em; font-weight: 400; line-height: 1.35; color: var(--ink-muted); }
.btn .en, .mic .en, .call .en, .verdict .en { color: inherit; opacity: .85; }
:focus-visible { outline: 3px solid var(--neela); outline-offset: 3px; }

/* top bar, pills, notices */
.topbar { max-width: 480px; margin: 0 auto; padding: 12px 16px 0; display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.brand { font: 800 22px/1.1 var(--font-display); color: var(--neela); }
.brand .en { font: 600 13px/1.3 var(--font); }
.pill { display: inline-flex; align-items: center; gap: 6px; min-height: 28px; padding: 2px 12px; border-radius: var(--r-pill); background: var(--paper); border: 1px solid var(--rule); font-size: 14px; font-weight: 600; white-space: nowrap; }
.pill::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.pill--demo, .pill--warn { color: var(--amber); } .pill--ok { color: var(--hara); } .pill--wait { color: var(--neela); }
.notice { display: block; padding: 10px 14px; border-radius: var(--r-btn); background: var(--paper); border: 1px solid var(--rule); font-size: 17px; }
.notice[data-tone="error"] { border-color: var(--sindoor); color: var(--sindoor); }
.notice[data-tone="ok"] { border-color: var(--hara); color: var(--hara); }
.notice[data-tone="warn"] { border-color: var(--amber); }
.notice small { display: block; margin-top: 2px; font-size: 13px; color: var(--ink-muted); }
.notice .btn { margin-top: 8px; }
.status-line { min-height: 1.6em; font-weight: 800; font-size: 18px; color: var(--neela); }

/* stepper: बोलो → पर्चा → सुनाओ → हाँ → मंज़ूर */
.stepper { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px; counter-reset: step; }
.stepper li { position: relative; padding-top: 30px; text-align: center; font-weight: 700; font-size: 15px; line-height: 1.2; color: var(--ink-muted); }
.stepper li::before { counter-increment: step; content: counter(step); position: absolute; top: 0; left: 50%; translate: -50% 0; width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; background: var(--paper); border: 2px solid var(--rule); font-size: 14px; }
.stepper li .en { font-size: 11px; }
.stepper li[data-state="current"] { color: var(--ink); }
.stepper li[data-state="current"]::before { background: var(--neela); border-color: var(--neela); color: #fff; }
.stepper li[data-state="done"]::before { content: "✓"; background: var(--hara); border-color: var(--hara); color: #fff; }

/* what Prisma heard, as a WhatsApp-like bubble */
.heard { background: var(--bubble); border-radius: 4px 16px 16px 16px; padding: 10px 14px; box-shadow: 0 1px 0 rgba(27,36,51,.08); }
.heard__k { font-weight: 700; font-size: 14px; color: var(--hara); }
.heard__k .en { display: inline; margin-left: 6px; }
.heard__text { margin-top: 2px; font-size: 18px; overflow-wrap: anywhere; }

/* the parcha slip: perforated top, red serial, ruled rows, double-ruled total */
.slip { position: relative; overflow: hidden; background: var(--paper); border-radius: var(--r-card); box-shadow: var(--shadow-paper); padding: 22px 16px 16px; }
.slip--duplicate { background: var(--paper-pink); }
.slip::before { content: ""; position: absolute; inset: 0 0 auto 0; height: 10px; background: radial-gradient(circle at 6px 0, var(--counter) 5px, transparent 5.5px) 0 0 / 12px 10px repeat-x; }
.slip__head { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; padding-bottom: 8px; border-bottom: 2px solid var(--ink); }
.slip__title { font: 800 20px/1.2 var(--font-display); }
.slip__serial { font-weight: 800; font-size: 18px; color: var(--serial); letter-spacing: .04em; white-space: nowrap; }
.slip__rows { list-style: none; margin: 0; padding: 0; }
.row { display: grid; grid-template-columns: 32px minmax(0, 1fr) auto; gap: 10px; align-items: start; padding: 12px 0; border-bottom: 1px solid var(--rule); }
.row--empty { display: block; color: var(--ink-muted); text-align: center; }
.row__icon svg { width: 28px; height: 28px; color: var(--neela); }
.row__label { font-size: 20px; font-weight: 600; line-height: 1.35; overflow-wrap: anywhere; }
.row__meta { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 2px; font-size: 14px; color: var(--ink-muted); }
.chip { display: inline-flex; align-items: center; min-height: 24px; padding: 0 8px; border-radius: var(--r-pill); background: var(--counter); color: var(--ink); font-size: 13px; font-weight: 700; }
.row__heard { font-style: italic; overflow-wrap: anywhere; }
.row__amount { font-size: 22px; font-weight: 800; text-align: right; white-space: nowrap; }
.row__was { display: block; font-size: 15px; font-weight: 600; color: var(--ink-muted); text-decoration: line-through 2px var(--sindoor); }
.row--changed { animation: flash 1.4s var(--ease); }
@keyframes flash { 0%, 40% { background: var(--paper-yellow); } 100% { background: transparent; } }
.row--flagged { margin: 0 -16px; padding: 12px 16px 12px 10px; background: var(--paper-yellow); border-left: 6px solid var(--haldi); }
.row__ask { grid-column: 2 / -1; display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; margin-top: 6px; }
.row__question { font-weight: 700; font-size: 18px; }
.abstain-reason { font-size: 15px; font-weight: 600; color: var(--amber); }
.reask { display: inline-flex; align-items: center; gap: 8px; min-height: var(--tap); padding: 6px 16px; border-radius: var(--r-pill); border: 2px solid var(--ink); background: var(--haldi); color: var(--ink); font: 700 17px/1.1 var(--font); cursor: pointer; touch-action: manipulation; }
.reask svg { width: 22px; height: 22px; }
.slip__total { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; padding: 14px 0 4px; border-bottom: 4px double var(--ink); }
.slip__total-k { font-weight: 800; font-size: 20px; }
.slip__total-v { font-size: 44px; font-weight: 800; line-height: 1; white-space: nowrap; }
.slip__total-v[data-incomplete] { font-size: 28px; color: var(--amber); }
.slip__delivery { display: grid; gap: 2px; padding-top: 12px; }
.slip__k { font-size: 15px; font-weight: 700; color: var(--ink-muted); }
.slip__delivery strong { font-size: 20px; }
.slip__delivery q { font-size: 14px; font-style: italic; color: var(--ink-muted); }
.stamp { position: absolute; right: 14px; top: 34%; width: 132px; height: 132px; border-radius: 50%; border: 5px double var(--jamuni); color: var(--jamuni); display: grid; place-content: center; text-align: center; font: 800 30px/1 var(--font-display); transform: rotate(-12deg); mix-blend-mode: multiply; opacity: .9; pointer-events: none; animation: stamp .35s var(--spring) both; }
.stamp small { display: block; margin-top: 4px; font: 700 11px/1.2 var(--font); letter-spacing: .12em; }
@keyframes stamp { from { transform: scale(2.4) rotate(-24deg); opacity: 0; } to { transform: scale(1) rotate(-12deg); opacity: .9; } }
.empty { padding: 28px 16px; text-align: center; background: var(--paper); border: 2px dashed var(--rule); border-radius: var(--r-card); display: grid; gap: 8px; }
.empty__title { font-weight: 800; font-size: 20px; }
.empty__example { font-style: italic; color: var(--ink-muted); }
.flagbar { display: flex; align-items: center; gap: 8px; padding: 10px 14px; border-radius: var(--r-btn); background: var(--paper-yellow); border-left: 6px solid var(--haldi); font-weight: 700; }

/* sticky bottom dock with the big mic */
.dock { position: fixed; inset: auto 0 0 0; z-index: 10; background: var(--paper); box-shadow: var(--shadow-dock); border-radius: var(--r-sheet) var(--r-sheet) 0 0; padding: 12px 16px calc(12px + env(safe-area-inset-bottom)); }
.dock__inner { max-width: 480px; margin: 0 auto; display: grid; gap: 10px; }
.dock__row { display: flex; align-items: center; gap: 14px; }
.dock__status { min-width: 0; display: grid; gap: 2px; }
.dock__title { font-weight: 800; font-size: 22px; line-height: 1.2; }
.timer { font-weight: 700; font-size: 18px; color: var(--sindoor); min-height: 1.2em; }
.meter { height: 8px; border-radius: 4px; background: var(--counter); overflow: hidden; }
.meter > span { display: block; height: 100%; width: calc(var(--level, 0) * 100%); background: var(--hara); transition: width 80ms linear; }
.mic { position: relative; flex: none; width: var(--mic); height: var(--mic); border-radius: 50%; border: 3px solid var(--ink); background: var(--haldi); color: var(--ink); display: grid; place-items: center; cursor: pointer; touch-action: manipulation; }
.mic svg { width: 44px; height: 44px; }
.mic:active:not(:disabled) { transform: scale(.96); }
.mic:disabled { background: var(--counter); border-color: var(--rule); color: var(--ink-muted); cursor: not-allowed; }
.mic--stop { background: var(--sindoor); border-color: var(--sindoor); color: #fff; box-shadow: 0 0 0 calc(var(--level, 0) * 18px) rgba(179,38,30,.25); transition: box-shadow 80ms linear; }
.mic--stop::before, .mic--stop::after { content: ""; position: absolute; inset: -6px; border-radius: 50%; border: 3px solid var(--sindoor); opacity: .5; animation: ring 1.6s var(--ease) infinite; }
.mic--stop::after { animation-delay: .8s; }
@keyframes ring { from { transform: scale(1); opacity: .55; } to { transform: scale(1.45); opacity: 0; } }
.dock[data-mic="processing"] .mic { opacity: .6; }

/* buttons */
.btn { display: inline-flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; min-height: var(--tap-primary); padding: 8px 18px; border-radius: var(--r-btn); border: 2px solid transparent; font: 800 20px/1.2 var(--font); text-align: center; text-decoration: none; cursor: pointer; touch-action: manipulation; }
.btn .en { font-size: 13px; font-weight: 600; }
.btn--primary { background: var(--neela); color: #fff; }
.btn--haan { background: var(--hara); color: #fff; }
.btn--change { background: var(--paper); color: var(--amber); border-color: var(--amber); }
.btn--wa { background: var(--paper); color: var(--wa); border-color: var(--wa); }
.btn--ghost { min-height: var(--tap); background: transparent; color: var(--neela); border-color: var(--rule); font-size: 17px; }
.btn:disabled { background: var(--counter); color: var(--ink-muted); border-color: var(--rule); cursor: not-allowed; }

/* share sheet, toast, disclosure */
.share { display: grid; gap: 10px; padding: 16px; background: var(--paper); border-radius: var(--r-card); box-shadow: var(--shadow-paper); }
.share__title { font-weight: 800; font-size: 20px; }
.fineprint { font-size: 14px; color: var(--ink-muted); }
.toast { position: fixed; left: 50%; bottom: calc(var(--dock-h) + 16px); translate: -50% 0; z-index: 20; padding: 10px 18px; border-radius: var(--r-pill); background: var(--ink); color: #fff; font-weight: 700; box-shadow: var(--shadow-paper); }
.disclosure { max-width: 448px; margin: 8px auto 0; padding: 8px 14px; border-radius: var(--r-btn); background: var(--paper-yellow); font-size: 14px; line-height: 1.45; }
.disclosure .en { font-size: 12px; }

/* customer: the call card */
.call { display: grid; gap: 12px; padding: 16px; border-radius: var(--r-sheet); background: var(--ink); color: #fff; }
.call__who { display: flex; align-items: center; gap: 12px; }
.call__avatar { position: relative; flex: none; width: 56px; height: 56px; border-radius: 50%; background: var(--haldi); color: var(--ink); display: grid; place-items: center; font: 800 22px/1 var(--font-display); }
.call[data-call="talking"] .call__avatar::after { content: ""; position: absolute; inset: -6px; border-radius: 50%; border: 3px solid var(--haldi); animation: ring 1.6s var(--ease) infinite; }
.call__title { font-weight: 800; font-size: 20px; }
.call__status { font-size: 15px; color: rgba(255,255,255,.85); }
.call__controls { display: flex; align-items: center; gap: 14px; }
.play { flex: none; width: 72px; height: 72px; border-radius: 50%; border: 0; background: var(--hara); color: #fff; display: grid; place-items: center; cursor: pointer; }
.play svg { width: 32px; height: 32px; }
.play:disabled { background: rgba(255,255,255,.2); cursor: not-allowed; }
.call__progress { flex: 1; height: 6px; border-radius: 3px; background: rgba(255,255,255,.2); overflow: hidden; }
.call__progress > span { display: block; width: 0; height: 100%; background: var(--haldi); }
.call__caption { font-size: 18px; line-height: 1.6; color: rgba(255,255,255,.55); overflow-wrap: anywhere; }
.call__caption .said { color: #fff; }

/* customer: consent, hints, fallback, receipt */
.consent { padding: 10px 14px; background: var(--paper); border: 1px solid var(--rule); border-radius: var(--r-btn); }
.consent__row { display: flex; align-items: flex-start; gap: 12px; min-height: var(--tap); font-weight: 600; cursor: pointer; }
.consent__row input { flex: none; width: 28px; height: 28px; margin: 2px 0 0; accent-color: var(--hara); }
.consent__full summary { display: flex; align-items: center; gap: 6px; min-height: var(--tap); color: var(--neela); font-weight: 700; cursor: pointer; }
.consent__full p { margin-bottom: 6px; font-size: 14px; color: var(--ink-muted); }
.hints { display: flex; flex-wrap: wrap; gap: 8px; }
.hint { padding: 4px 12px; border-radius: var(--r-pill); border: 2px dashed currentColor; font-weight: 700; font-size: 16px; }
.hint--haan { color: var(--hara); } .hint--change { color: var(--amber); }
.fallback { display: grid; gap: 10px; padding: 16px; background: var(--paper); border: 2px solid var(--amber); border-radius: var(--r-card); }
.fallback h2 { font-size: 20px; }
.fallback__actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.receipt { display: grid; justify-items: center; gap: 8px; padding: 22px 16px; text-align: center; background: var(--paper); border-radius: var(--r-sheet); box-shadow: var(--shadow-paper); }
.receipt__tick { width: 84px; height: 84px; border-radius: 50%; background: var(--hara); color: #fff; display: grid; place-items: center; animation: pop .45s var(--spring) both; }
.receipt__tick svg { width: 46px; height: 46px; }
@keyframes pop { from { transform: scale(.4); opacity: 0; } to { transform: scale(1); opacity: 1; } }
.receipt__title { font-size: 24px; font-weight: 800; color: var(--hara); }
.receipt__total { font-size: 48px; font-weight: 800; line-height: 1.05; }
.receipt__said { font-size: 18px; } .receipt__meta { font-size: 15px; color: var(--ink-muted); }
.receipt__actions { display: grid; gap: 10px; width: 100%; margin-top: 8px; }

/* verify */
.verdict { display: grid; justify-items: center; gap: 4px; padding: 22px 16px; border-radius: var(--r-sheet); color: #fff; text-align: center; }
.verdict--ok { background: var(--hara); } .verdict--pending { background: var(--amber); }
.verdict__icon { width: 64px; height: 64px; border-radius: 50%; background: rgba(255,255,255,.2); display: grid; place-items: center; font-size: 36px; font-weight: 800; }
.verdict__title { font-size: 28px; font-weight: 800; } .verdict__meta { font-weight: 700; }
.section-title { font-size: 20px; font-weight: 800; }
.voices { display: grid; gap: 10px; }
.voice { display: grid; gap: 6px; padding: 12px 14px; background: var(--bubble); border-radius: 4px 16px 16px 16px; }
.voice--customer { background: var(--paper); border: 1px solid var(--rule); border-radius: 16px 4px 16px 16px; }
.voice__who { font-weight: 800; } .voice__text { font-style: italic; overflow-wrap: anywhere; }
.voice audio { width: 100%; height: 40px; }
.tech { padding: 4px 14px; background: var(--paper); border: 1px solid var(--rule); border-radius: var(--r-btn); }
.tech summary { display: flex; align-items: center; gap: 6px; min-height: var(--tap); font-weight: 800; cursor: pointer; }
.kv { display: grid; gap: 2px; margin: 8px 0 12px; } .kv dt { margin-top: 8px; font-size: 14px; font-weight: 700; color: var(--ink-muted); } .kv dd { margin: 0; overflow-wrap: anywhere; }
.hash { padding: 6px 8px; border-radius: 6px; background: var(--counter); font: 600 13px/1.4 ui-monospace, Consolas, monospace; word-break: break-all; }
.actions { display: grid; gap: 10px; }

/* stage view: two phones side by side */
.stage__head { max-width: 1100px; margin: 0 auto; padding: 20px 16px 8px; text-align: center; display: grid; gap: 4px; }
.stage__head p { font-size: 20px; font-weight: 700; }
.stage { display: flex; flex-wrap: wrap; justify-content: center; gap: 32px; padding: 8px 16px 24px; }
.phone { margin: 0; display: grid; justify-items: center; gap: 8px; }
.phone figcaption { font-weight: 800; font-size: 20px; }
.phone iframe { width: 360px; height: 760px; border: 10px solid var(--ink); border-radius: 36px; background: var(--counter); box-shadow: var(--shadow-paper); }

@media (min-width: 768px) { body { font-size: 19px; } }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .001ms !important; animation-iteration-count: 1 !important; transition-duration: .001ms !important; }
}
```

- [ ] **Step 4: Create `src/parcha/static/icons.svg`.** The paths are Feather Icons (MIT), except `part` (a nut: hexagon plus hole).

```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <symbol id="mic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><path d="M12 19v4M8 23h8"/></symbol>
  <symbol id="stop" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor"/></symbol>
  <symbol id="play" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="currentColor"/></symbol>
  <symbol id="pause" viewBox="0 0 24 24"><path d="M6 4h4v16H6zM14 4h4v16h-4z" fill="currentColor"/></symbol>
  <symbol id="check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></symbol>
  <symbol id="part" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 2l8.66 5v10L12 22l-8.66-5V7z"/><circle cx="12" cy="12" r="3.5"/></symbol>
  <symbol id="labour" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></symbol>
  <symbol id="copy" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></symbol>
  <symbol id="chat" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></symbol>
</svg>
```

- [ ] **Step 5: Create `src/parcha/templates/base.html`.**

```html
<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <meta name="theme-color" content="#F3EEE3">
  <title>{% block title %}Kaam ka Parcha{% endblock %}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@800&family=Mukta:wght@400;600;800&display=swap">
  <link rel="stylesheet" href="/static/parcha.css">
</head>
<body class="page {% block body_class %}{% endblock %}">
{% block body %}{% endblock %}
{% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 6: Create `src/parcha/templates/_slip.html`.** Its markup must stay identical to `ParchaUI.renderSlip` (Task 5).

```html
{% macro slip(card, total_paise, parcha_no, copy="original", stamp=False) -%}
<article class="slip slip--{{ copy }}" id="slip" aria-label="पर्चा № {{ parcha_no }}">
  <header class="slip__head">
    <div class="slip__title">काम का पर्चा<span class="en">Job estimate</span></div>
    <div class="slip__serial">№ <span id="parcha-no">{{ parcha_no }}</span></div>
  </header>
  <ol class="slip__rows" id="items-tbody">
    {% for item in (card.items if card else []) %}
    {% set heard = card.evidence | selectattr("field", "equalto", "items." ~ item.id ~ ".amount_paise") | map(attribute="quote") | first %}
    <li class="row" data-item="{{ item.id }}">
      <span class="row__icon" aria-hidden="true"><svg focusable="false"><use href="/static/icons.svg#{{ item.kind }}"/></svg></span>
      <div class="row__main">
        <div class="row__label">{{ item.label or "—" }}</div>
        <div class="row__meta"><span class="chip">{{ item.kind | kind_hi }}</span>{% if heard %}<q class="row__heard">{{ heard }}</q>{% endif %}</div>
      </div>
      <div class="row__amount">{{ item.amount_paise | inr }}</div>
    </li>
    {% else %}
    <li class="row row--empty">अभी कोई चीज़ नहीं<span class="en">No items yet</span></li>
    {% endfor %}
  </ol>
  <div class="slip__total">
    <span class="slip__total-k">कुल<span class="en">Total</span></span>
    <strong class="slip__total-v" id="total-cell"{% if total_paise is none %} data-incomplete{% endif %}>{{ total_paise | inr if total_paise is not none else "अधूरा" }}</strong>
  </div>
  <div class="slip__delivery" id="delivery-info">
    <span class="slip__k">गाड़ी कब मिलेगी<span class="en">Vehicle ready</span></span>
    <strong>{{ (card.delivery if card else none) | hindi_delivery }}</strong>
    {% if card and card.delivery %}<q>{{ card.delivery.spoken }}</q>{% endif %}
  </div>
  {% if stamp %}<div class="stamp" role="img" aria-label="मंज़ूर — Approved">मंज़ूर<small>APPROVED</small></div>{% endif %}
</article>
{%- endmacro %}
```

- [ ] **Step 7: Rewrite `src/parcha/templates/verify.html`.**

```html
{% extends "base.html" %}
{% from "_slip.html" import slip %}
{% block title %}Kaam ka Parcha — Electronic Record Verification{% endblock %}
{% block body_class %}page--verify{% endblock %}
{% block body %}
{% set sealed = session.status == "confirmed" %}
<header class="topbar"><div class="brand">काम का पर्चा<span class="en">Kaam ka Parcha — Audit Verification &amp; Audio Replay</span></div></header>
<main class="sheet">
  <section class="verdict {{ 'verdict--ok' if sealed else 'verdict--pending' }}" id="verify-verdict" role="status">
    <div class="verdict__icon" aria-hidden="true">{{ "✓" if sealed else "!" }}</div>
    <h1 class="verdict__title">{{ "असली पर्चा" if sealed else "अभी मंज़ूर नहीं" }}</h1>
    <p class="en">{{ "Verified electronic record" if sealed else "Not yet confirmed by the customer" }}</p>
    <p class="verdict__meta">№ {{ parcha_no }} · {{ vehicle }}</p>
  </section>

  {{ slip(session.card, total_paise, parcha_no, copy="original", stamp=sealed) }}

  <section class="voices" aria-label="रिकॉर्डिंग">
    <h2 class="section-title">किसने क्या कहा<span class="en">Who said what</span></h2>
    <div class="voice">
      <div class="voice__who">मिस्त्री<span class="en">Mechanic intake — Gnani Prisma heard</span></div>
      <p class="voice__text">“{{ intake.transcript }}”</p>
      <audio controls preload="metadata" src="{{ intake.audio_url }}"></audio>
    </div>
    <div class="voice voice--customer">
      <div class="voice__who">ग्राहक<span class="en">Customer confirmation</span></div>
      <p class="voice__text">“{{ confirmation.transcript }}”</p>
      <audio controls preload="metadata" src="{{ confirmation.audio_url }}"></audio>
    </div>
  </section>

  <details class="tech" id="dpdp-compliance-panel">
    <summary>तकनीकी सबूत<span class="en">Technical evidence</span></summary>
    <dl class="kv">
      <dt>Legal basis</dt><dd>{{ legal_compliance }} — <strong>BSA 2023 §§ 61–63 Compliant</strong></dd>
      <dt>Session ID</dt><dd>{{ session.id }}</dd>
      <dt>Status · Revision</dt><dd>{{ session.status }} · Rev {{ session.revision }}</dd>
      <dt>Confirmed At (UTC)</dt><dd>{{ confirmed_at_utc or "Pending" }}</dd>
      <dt>Canonical Audit Manifest SHA-256</dt><dd class="hash" id="manifest-digest">{{ audit_manifest_sha256 }}</dd>
      <dt>Intake Audio SHA-256</dt><dd class="hash">{{ intake.audio_sha256 or "N/A" }}</dd>
      <dt>Confirmation Audio SHA-256</dt><dd class="hash">{{ confirmation.audio_sha256 or "N/A" }}</dd>
      <dt>DPDP Act 2023 Statutory Consent</dt>
      <dd>{{ "Granted & Verified" if (dpdp_consent and dpdp_consent.granted) else "Not Logged" }}{% if dpdp_consent and dpdp_consent.recorded_at_utc %} · {{ dpdp_consent.recorded_at_utc }}{% endif %}</dd>
      {% if dpdp_consent and dpdp_consent.user_agent %}<dt>Client User-Agent</dt><dd>{{ dpdp_consent.user_agent }}</dd>{% endif %}
      {% if dpdp_consent and dpdp_consent.consent_sha256 %}<dt>Consent SHA-256</dt><dd class="hash" id="dpdp-consent-digest">{{ dpdp_consent.consent_sha256 }}</dd>{% endif %}
    </dl>
  </details>

  {% if sealed %}
  <div class="actions">
    <a class="btn btn--primary" href="/sessions/{{ session.id }}/pdf" download>PDF डाउनलोड करें<span class="en">Download certified PDF</span></a>
    <a class="btn btn--ghost" href="/sessions/{{ session.id }}/whatsapp" target="_blank" rel="noopener">WhatsApp टेक्स्ट<span class="en">View WhatsApp text</span></a>
  </div>
  {% endif %}
</main>
{% endblock %}
```

- [ ] **Step 8: Run.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_pages.py tests/test_verify.py tests/test_consent.py`. Expected: pass. Then `.\.venv\Scripts\python.exe -m pytest -q -m e2e tests/e2e/test_verify_page.py`. Expected: pass; open `var/e2e/verify-360.png` and check the slip, stamp and folded evidence by eye.
- [ ] **Step 9: Commit.**
  `git add src/parcha/static/parcha.css src/parcha/static/icons.svg src/parcha/templates/base.html src/parcha/templates/_slip.html src/parcha/templates/verify.html tests/test_pages.py tests/e2e/test_verify_page.py` then `git commit -m "feat(ui): digital-parcha design system and verify page"`

---

### Task 5: `ui.js`: helpers and components (`window.ParchaUI`)

**Files:**
- Create: `src/parcha/static/ui.js`
- Modify:
  - `src/parcha/static/app.js`: replace its `REPEAT_MESSAGE`, `ABSTAIN_LABELS` and `describeHttpError` definitions (from the money-path plan's Task 5) with one line, `const { REPEAT_MESSAGE, ABSTAIN_LABELS, describeHttpError } = window.ParchaUI;`. The strings now live in `ui.js`, unchanged, so the old page code keeps working until Tasks 6–7 replace it.
  - The **old** `workshop.html` and `customer.html`: add `<script src="/static/ui.js"></script>` immediately before the `app.js` script tag.
- Test: `tests/e2e/test_ui_helpers.py`

**Interfaces:**
- Consumes: the Task 4 CSS class contract and icon ids.
- Produces `window.ParchaUI` with:
  - **copy and errors:** `COPY`, `REPEAT_MESSAGE`, `ABSTAIN_LABELS`, `describeHttpError(detail, status) -> string`, `HttpError(status, detail)` (`.status`, `.detail`, `.repeat`, `.reason`), `MicError(kind)` (`.kind` ∈ `blocked|unsupported|unavailable`), `api.get(url)`, `api.post(url, formData)` (both resolve to JSON or throw `HttpError`);
  - **pure helpers:** `formatRupees(paise) -> string`, `hindiDelivery(delivery) -> string`, `kindLabel(kind) -> string`, `describeField(path, card) -> {hi, en}`, `stageFor(session) -> "bolo"|"parcha"|"sunao"|"haan"|"manzoor"`, `flagCount(n) -> {hi, en}`, `diffItems(prevCard, nextCard) -> Map<id, {amountFrom?, labelFrom?}>`, `heardQuote(card, field) -> string|null`;
  - **DOM builders:** `el(tag, attrs, ...children) -> Element` (text only), `icon(name) -> SVGElement`, `setIcon(button, name)`, `renderSlip(target, session, {copy, flags, onReask, previous, stamp})`, `renderStepper(ol, stage)`, `emptyWorkshop() -> Element`, `setCaption(node, text, progress)`, `say(target, hi, en, tone, detail)`, `stale(target)`;
  - **feedback and sharing:** `toast(text)`, `copyText(text) -> Promise<boolean>`, `shareMessage(session, url) -> string`, `whatsappHref(text) -> string`;
  - **mic and sound:** `micDock(dock) -> {listening(stream), processing(), idle()}`, `startLevelMeter(stream, node) -> stop()`, `chime()`, `buzz()`;
  - **timing:** `poll(fetchOnce, {every, maxMs, until, onData, onDone}) -> stop()`, `timeNow() -> string`;
  - also `window.describeHttpError` (kept for callers from the money-path plan).

- [ ] **Step 1: Write the failing tests** in `tests/e2e/test_ui_helpers.py`. They load the page that includes `ui.js` and call the public helpers:

```python
import pytest

pytestmark = pytest.mark.e2e


@pytest.fixture
def ui(page):
    page.goto("/workshop")
    page.wait_for_function("() => window.ParchaUI !== undefined")
    return lambda js, arg=None: page.evaluate(f"(arg) => {{ const UI = window.ParchaUI; return {js}; }}", arg)


@pytest.mark.parametrize("paise, text", [
    (0, "₹0"), (65000, "₹650"), (4550, "₹45.50"), (125000, "₹1,250"),
    (12345600, "₹1,23,456"), (10000000, "₹1,00,000"), (None, "₹ —"),
])
def test_format_rupees_matches_the_server(ui, paise, text):
    assert ui("UI.formatRupees(arg)", paise) == text


def test_hindi_delivery_matches_the_server(ui):
    assert ui('UI.hindiDelivery({date: "2026-10-06", window: "evening", spoken: "x"})') == "मंगलवार, 6 अक्टूबर · शाम"
    assert ui("UI.hindiDelivery(null)") == "अभी तय नहीं"


def test_field_paths_become_plain_questions(ui):
    card = {"items": [{"id": "part-1", "label": "front brake pad", "kind": "part", "amount_paise": None}]}
    assert ui("UI.describeField('items.part-1.amount_paise', arg)", card) == {"hi": "front brake pad का दाम?", "en": "Price of front brake pad?"}
    assert ui("UI.describeField('items.part-1.label', arg)", card) == {"hi": "यह पार्ट क्या है?", "en": "Which part is this?"}
    assert ui("UI.describeField('delivery', arg)", card) == {"hi": "गाड़ी कब मिलेगी?", "en": "When will the vehicle be ready?"}


@pytest.mark.parametrize("session, stage", [
    ({"card": None, "status": "draft"}, "bolo"),
    ({"card": {"items": []}, "status": "review", "review_fields": ["delivery"]}, "parcha"),
    ({"card": {"items": []}, "status": "review", "review_fields": []}, "sunao"),
    ({"card": {"items": []}, "status": "awaiting_reply", "review_fields": []}, "haan"),
    ({"card": {"items": []}, "status": "fallback_ready", "review_fields": []}, "haan"),
    ({"card": {"items": []}, "status": "confirmed", "review_fields": []}, "manzoor"),
])
def test_stage_follows_the_decision_table(ui, session, stage):
    assert ui("UI.stageFor(arg)", session) == stage


def test_diff_reports_changed_amounts_and_labels_only(ui):
    prev = {"items": [{"id": "part-1", "label": "a", "amount_paise": 45000}, {"id": "labour-1", "label": "l", "amount_paise": 20000}]}
    nxt = {"items": [{"id": "part-1", "label": "a", "amount_paise": 50000}, {"id": "labour-1", "label": "l", "amount_paise": 20000}]}
    assert ui("Object.fromEntries(UI.diffItems(arg[0], arg[1]))", [prev, nxt]) == {"part-1": {"amountFrom": 45000}}


def test_el_never_parses_markup(ui):
    assert ui("UI.el('div', {}, '<img src=x>').querySelector('img') === null") is True
    assert ui("UI.el('div', {}, '<b>x</b>').textContent") == "<b>x</b>"


def test_flag_count_is_grammatical(ui):
    assert ui("UI.flagCount(1)") == {"hi": "1 चीज़ जाँचनी है", "en": "1 to check"}
    assert ui("UI.flagCount(3)") == {"hi": "3 चीज़ें जाँचनी हैं", "en": "3 to check"}


def test_repeat_detail_keeps_the_money_path_message(ui):
    assert ui("UI.describeHttpError({repeat: true, reason: 'empty_transcript'}, 422)") == "आवाज़ साफ़ नहीं आई — कृपया फिर से बोलिए (Please say it again)"
    assert ui("new UI.HttpError(422, {repeat: true, reason: 'provider_429'}).reason") == "provider_429"
    assert ui("window.describeHttpError('stale revision', 409)") == "stale revision"


def test_whatsapp_share_message_is_hindi_with_total_and_link(ui):
    text = ui("UI.shareMessage({parcha_no: '004217', total_paise: 65000}, 'http://x/customer/abc')")
    assert text.startswith("नमस्ते!") and "№ 004217" in text and "₹650" in text and text.endswith("http://x/customer/abc")
    assert ui("UI.whatsappHref('हाँ ठीक है')") == "https://wa.me/?text=%E0%A4%B9%E0%A4%BE%E0%A4%81%20%E0%A4%A0%E0%A5%80%E0%A4%95%20%E0%A4%B9%E0%A5%88"
```

- [ ] **Step 2: Run to see it fail.** `.\.venv\Scripts\python.exe -m pytest -q -m e2e tests/e2e/test_ui_helpers.py`. Expected: a timeout waiting for `window.ParchaUI`, because `ui.js` doesn't exist yet.

- [ ] **Step 3: Create `src/parcha/static/ui.js`.**

```js
// Kaam ka Parcha UI helpers and components. Rule: server-derived text is only ever set as text, never parsed as HTML.
(function () {
  "use strict";

  const COPY = {
    micIdle: { hi: "बोलिए", en: "Tap to speak" },
    customerMicIdle: { hi: "बोलकर जवाब दें", en: "Speak your answer" },
    listening: { hi: "सुन रहा हूँ", en: "Listening — tap to stop" },
    processing: { hi: "समझ रहे हैं…", en: "Understanding…" },
    reask: { hi: "दोबारा बोलें", en: "Say again" },
    deliveryQ: { hi: "गाड़ी कब मिलेगी?", en: "When will the vehicle be ready?" },
    ready: { hi: "पर्चा तैयार है — नीचे “ग्राहक को सुनाएँ” दबाइए।", en: "The parcha is ready — tap “Read to customer”." },
    checkRows: { hi: "पीली लाइन पर “दोबारा बोलें” दबाकर ठीक कीजिए।", en: "Fix each yellow row with “Say again”." },
    sendLink: { hi: "ग्राहक को लिंक भेजिए — वो सुनकर “हाँ” बोलेगा।", en: "Send the link — the customer listens and says “haan”." },
    waiting: { hi: "ग्राहक का जवाब बाकी", en: "Waiting for customer" },
    workshopSealed: { hi: "ग्राहक ने मंज़ूर किया", en: "Customer approved" },
    changesAsked: { hi: "ग्राहक ने बदलाव माँगा है", en: "Customer asked for changes" },
    copied: { hi: "कॉपी हुआ", en: "Copied" },
    micBlocked: { hi: "माइक की इजाज़त दें — ऊपर ताले 🔒 पर टैप करके \"Allow\" चुनें।", en: "Allow the microphone in your browser." },
    micUnsupported: { hi: "यह ब्राउज़र रिकॉर्ड नहीं कर सकता — Chrome में खोलें।", en: "This browser can't record — open in Chrome." },
    failed: { hi: "कुछ गड़बड़ हुई — फिर से कोशिश करें।", en: "Something went wrong — try again." },
    stale: { hi: "पर्चा बदल गया है — पेज ताज़ा करें।", en: "The parcha changed — reload." },
    reload: { hi: "ताज़ा करें", en: "Reload" },
    consentNeeded: { hi: "पहले ऊपर सहमति पर ✓ लगाइए।", en: "Tick the consent box first." },
    consentSaved: { hi: "सहमति दर्ज हुई", en: "Consent recorded" },
  };
  // From the money-path plan (Task 5): strings unchanged.
  const REPEAT_MESSAGE = "आवाज़ साफ़ नहीं आई — कृपया फिर से बोलिए (Please say it again)";
  const ABSTAIN_LABELS = {
    incomplete_number: "अधूरी रकम — फिर से पूछेंगे",
    crosscheck_disagreement: "रकम पक्की नहीं — फिर से पूछेंगे",
    ambiguous_attachment: "कौन सी रकम किस आइटम की — साफ़ नहीं",
    empty_transcript: "आवाज़ नहीं आई",
    provider_504: "नेटवर्क रुका — फिर से बोलिए",
    provider_429: "बहुत जल्दी-जल्दी — थोड़ा रुककर बोलिए",
    out_of_range: "रकम सीमा से बाहर",
  };
  const WEEKDAYS_SUN0 = ["रविवार", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"];
  const MONTHS = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"];
  const WINDOW_HI = { morning: "सुबह", afternoon: "दोपहर", evening: "शाम" };
  const KIND_HI = { part: "पार्ट", labour: "लेबर" };
  const STAGES = ["bolo", "parcha", "sunao", "haan", "manzoor"];
  const SVG_NS = "http://www.w3.org/2000/svg";
  const INR = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

  function describeHttpError(detail, status) {
    if (detail && typeof detail === "object" && detail.repeat) return REPEAT_MESSAGE;
    return (typeof detail === "string" && detail) || `Server returned HTTP ${status}`;
  }

  class HttpError extends Error {
    constructor(status, detail) {
      super(describeHttpError(detail, status));
      this.status = status;
      this.detail = detail;
      this.repeat = Boolean(detail && typeof detail === "object" && detail.repeat);
      this.reason = this.repeat ? detail.reason : null;
    }
  }

  class MicError extends Error {
    constructor(kind) { super(`microphone ${kind}`); this.kind = kind; }
  }

  async function parse(res) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    if (!res.ok) throw new HttpError(res.status, body.detail);
    return body;
  }
  const api = {
    get: async (url) => parse(await fetch(url, { headers: { Accept: "application/json" } })),
    post: async (url, body) => parse(await fetch(url, { method: "POST", body })),
  };

  function formatRupees(paise) {
    if (paise === null || paise === undefined) return "₹ —";
    const sign = paise < 0 ? "-" : "";
    const abs = Math.abs(paise);
    const rupees = Math.floor(abs / 100);
    const rem = abs % 100;
    return `${sign}₹${INR.format(rupees)}${rem ? "." + String(rem).padStart(2, "0") : ""}`;
  }

  function hindiDelivery(delivery) {
    if (!delivery) return "अभी तय नहीं";
    const [y, m, d] = delivery.date.split("-").map(Number);
    const weekday = new Date(Date.UTC(y, m - 1, d)).getUTCDay();
    return `${WEEKDAYS_SUN0[weekday]}, ${d} ${MONTHS[m - 1]} · ${WINDOW_HI[delivery.window] || delivery.window}`;
  }

  const kindLabel = (kind) => KIND_HI[kind] || kind || "चीज़";

  function describeField(path, card) {
    if (path === "delivery") return { ...COPY.deliveryQ };
    const match = /^items\.([^.]+)\.(label|amount_paise)$/.exec(path);
    const item = match && ((card && card.items) || []).find((it) => it.id === match[1]);
    if (match && match[2] === "amount_paise") {
      const label = (item && item.label) || kindLabel(item && item.kind);
      return { hi: `${label} का दाम?`, en: `Price of ${label}?` };
    }
    if (match && match[2] === "label") {
      return { hi: `यह ${kindLabel(item && item.kind)} क्या है?`, en: `Which ${(item && item.kind) || "item"} is this?` };
    }
    return { hi: path, en: path };
  }

  function stageFor(s) {
    if (!s || !s.card) return "bolo";
    if (s.status === "confirmed") return "manzoor";
    if (s.status === "awaiting_reply" || s.status === "fallback_ready") return "haan";
    if ((s.review_fields || []).length) return "parcha";
    return "sunao";
  }

  const flagCount = (n) => ({ hi: n === 1 ? "1 चीज़ जाँचनी है" : `${n} चीज़ें जाँचनी हैं`, en: `${n} to check` });

  function diffItems(prev, next) {
    const before = new Map(((prev && prev.items) || []).map((it) => [it.id, it]));
    const changes = new Map();
    for (const it of (next && next.items) || []) {
      const old = before.get(it.id);
      if (!old) continue;
      const change = {};
      if (old.amount_paise !== it.amount_paise) change.amountFrom = old.amount_paise;
      if (old.label !== it.label) change.labelFrom = old.label;
      if (Object.keys(change).length) changes.set(it.id, change);
    }
    return changes;
  }

  function heardQuote(card, field) {
    const ev = ((card && card.evidence) || []).find((e) => e.field === field);
    return ev ? ev.quote : null;
  }

  function el(tag, attrs, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs || {})) {
      if (value === null || value === undefined || value === false) continue;
      node.setAttribute(key, value === true ? "" : String(value));
    }
    for (const child of children.flat()) {
      if (child === null || child === undefined || child === false) continue;
      node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return node;
  }

  function icon(name) {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    const use = document.createElementNS(SVG_NS, "use");
    use.setAttribute("href", `/static/icons.svg#${name}`);
    svg.append(use);
    return svg;
  }
  function setIcon(button, name) {
    const use = button && button.querySelector("use");
    if (use) use.setAttribute("href", `/static/icons.svg#${name}`);
  }

  function askBlock(field, card, reason, onReask) {
    const q = describeField(field, card);
    const chip = el("button", { class: "reask", type: "button", "data-field": field, "aria-label": `${COPY.reask.hi} — ${q.en}` },
      icon("mic"), el("span", {}, COPY.reask.hi));
    if (onReask) chip.addEventListener("click", () => onReask(field, chip));
    return el("div", { class: "row__ask" },
      el("span", { class: "row__question" }, q.hi, el("span", { class: "en" }, q.en)),
      reason ? el("span", { class: "abstain-reason" }, ABSTAIN_LABELS[reason] || reason) : null,
      chip);
  }

  // Same markup as templates/_slip.html; keep the two in step.
  function renderSlip(target, session, opts = {}) {
    if (!target) return;
    const card = session.card || { items: [], evidence: [] };
    const flags = new Set(opts.flags ? session.review_fields || [] : []);
    const reasons = session.abstentions || {};
    const changes = opts.previous ? diffItems(opts.previous, card) : new Map();
    const rows = (card.items || []).map((item) => {
      const amountField = `items.${item.id}.amount_paise`;
      const labelField = `items.${item.id}.label`;
      const flagged = [labelField, amountField].filter((f) => flags.has(f));
      const change = changes.get(item.id);
      const heard = heardQuote(card, amountField);
      const row = el("li", { class: ["row", flagged.length && "row--flagged", change && "row--changed"].filter(Boolean).join(" "), "data-item": item.id },
        el("span", { class: "row__icon", "aria-hidden": "true" }, icon(item.kind)),
        el("div", { class: "row__main" },
          el("div", { class: "row__label" },
            change && change.labelFrom !== undefined ? el("s", { class: "row__was" }, change.labelFrom || "—") : null,
            item.label || "—"),
          el("div", { class: "row__meta" }, el("span", { class: "chip" }, kindLabel(item.kind)), heard ? el("q", { class: "row__heard" }, heard) : null)),
        el("div", { class: "row__amount" },
          change && change.amountFrom !== undefined ? el("s", { class: "row__was" }, formatRupees(change.amountFrom)) : null,
          formatRupees(item.amount_paise)));
      flagged.forEach((field) => row.append(askBlock(field, card, reasons[field], opts.onReask)));
      return row;
    });
    if (!rows.length) rows.push(el("li", { class: "row row--empty" }, "अभी कोई चीज़ नहीं", el("span", { class: "en" }, "No items yet")));

    const total = session.total_paise;
    const delivery = el("div", { class: "slip__delivery", id: "delivery-info" },
      el("span", { class: "slip__k" }, "गाड़ी कब मिलेगी", el("span", { class: "en" }, "Vehicle ready")),
      el("strong", {}, hindiDelivery(card.delivery)),
      card.delivery ? el("q", {}, card.delivery.spoken) : null);
    if (flags.has("delivery")) delivery.append(askBlock("delivery", card, reasons.delivery, opts.onReask));

    target.replaceChildren(el("article", { class: `slip slip--${opts.copy || "original"}`, id: "slip", "aria-label": `पर्चा № ${session.parcha_no || ""}` },
      el("header", { class: "slip__head" },
        el("div", { class: "slip__title" }, "काम का पर्चा", el("span", { class: "en" }, "Job estimate")),
        el("div", { class: "slip__serial" }, "№ ", el("span", { id: "parcha-no" }, session.parcha_no || ""))),
      el("ol", { class: "slip__rows", id: "items-tbody" }, rows),
      el("div", { class: "slip__total" },
        el("span", { class: "slip__total-k" }, "कुल", el("span", { class: "en" }, "Total")),
        el("strong", { class: "slip__total-v", id: "total-cell", "data-incomplete": total === null || total === undefined },
          total === null || total === undefined ? "अधूरा" : formatRupees(total))),
      delivery,
      opts.stamp ? el("div", { class: "stamp", role: "img", "aria-label": "मंज़ूर — Approved" }, "मंज़ूर", el("small", {}, "APPROVED")) : null));
  }

  function renderStepper(ol, stage) {
    if (!ol) return;
    const at = STAGES.indexOf(stage);
    ol.querySelectorAll("li[data-step]").forEach((li) => {
      const i = STAGES.indexOf(li.dataset.step);
      li.dataset.state = stage === "manzoor" || i < at ? "done" : i === at ? "current" : "todo";
      if (i === at) li.setAttribute("aria-current", "step"); else li.removeAttribute("aria-current");
    });
  }

  const emptyWorkshop = () => el("div", { class: "empty" },
    el("p", { class: "empty__title" }, "अभी कोई पर्चा नहीं", el("span", { class: "en" }, "No estimate yet")),
    el("p", {}, "नीचे पीला माइक दबाइए और काम, पार्ट, दाम और गाड़ी कब मिलेगी — बोलिए।",
      el("span", { class: "en" }, "Tap the yellow mic and say the work, parts, prices and the ready day.")),
    el("p", { class: "empty__example" }, "“फ्रंट ब्रेक पैड बदला, पार्ट साढ़े चार सौ, लेबर दो सौ, सोमवार शाम तक”"));

  function setCaption(node, text, progress) {
    if (!node) return;
    const words = (text || "").split(/\s+/).filter(Boolean);
    const n = Math.round(Math.max(0, Math.min(1, progress || 0)) * words.length);
    node.replaceChildren(el("span", { class: "said" }, words.slice(0, n).join(" ")), n < words.length ? " " + words.slice(n).join(" ") : "");
  }

  function say(target, hi, en = "", tone = "info", detail = "") {
    if (!target) return;
    target.dataset.tone = tone;
    target.replaceChildren(document.createTextNode(hi), en ? el("span", { class: "en" }, en) : "", detail ? el("small", {}, detail) : "");
  }

  function stale(target) {
    say(target, COPY.stale.hi, COPY.stale.en, "error");
    const btn = el("button", { class: "btn btn--ghost", type: "button", id: "reload" }, COPY.reload.hi, el("span", { class: "en" }, COPY.reload.en));
    btn.addEventListener("click", () => window.location.reload());
    target.append(btn);
  }

  let toastTimer = 0;
  function toast(text) {
    const node = document.getElementById("toast");
    if (!node) return;
    node.textContent = text;
    node.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { node.hidden = true; }, 2500);
  }

  async function copyText(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) { await navigator.clipboard.writeText(text); return true; }
    } catch (_) { /* fall through to the legacy path (plain-http LAN demos) */ }
    const area = el("textarea", { readonly: true, "aria-hidden": "true", style: "position:fixed;top:0;opacity:0" });
    area.value = text;
    document.body.append(area);
    area.select();
    let ok = false;
    try { ok = document.execCommand("copy"); } catch (_) { ok = false; }
    area.remove();
    return ok;
  }

  const shareMessage = (s, url) =>
    `नमस्ते! आपकी गाड़ी का पर्चा № ${s.parcha_no} तैयार है — कुल ${formatRupees(s.total_paise)}। सुनकर “हाँ, ठीक है” बोलिए: ${url}`;
  const whatsappHref = (text) => `https://wa.me/?text=${encodeURIComponent(text)}`;

  function startLevelMeter(stream, node) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC || !stream || !node) return () => {};
    const ctx = new AC();
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 512;
    ctx.createMediaStreamSource(stream).connect(analyser);
    const buf = new Uint8Array(analyser.fftSize);
    let frame = 0;
    const tick = () => {
      analyser.getByteTimeDomainData(buf);
      let sum = 0;
      for (const v of buf) { const x = (v - 128) / 128; sum += x * x; }
      node.style.setProperty("--level", Math.min(1, Math.sqrt(sum / buf.length) * 4).toFixed(3));
      frame = requestAnimationFrame(tick);
    };
    tick();
    return () => { cancelAnimationFrame(frame); node.style.setProperty("--level", "0"); ctx.close(); };
  }

  function startTimer(node) {
    if (!node) return () => {};
    const t0 = Date.now();
    const tick = () => {
      const s = Math.floor((Date.now() - t0) / 1000);
      node.textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
    };
    tick();
    const id = setInterval(tick, 500);
    return () => clearInterval(id);
  }

  function micDock(dock) {
    let stopMeter = () => {};
    let stopTimer = () => {};
    const title = dock.querySelector("[data-mic-title]");
    const sub = dock.querySelector("[data-mic-sub]");
    const timer = dock.querySelector("[data-mic-timer]");
    const set = (state, copy) => {
      dock.dataset.mic = state;
      if (title) title.textContent = copy.hi;
      if (sub) sub.textContent = copy.en;
    };
    return {
      listening(stream) { set("listening", COPY.listening); stopMeter = startLevelMeter(stream, dock); stopTimer = startTimer(timer); },
      processing() { stopMeter(); stopTimer(); set("processing", COPY.processing); },
      idle() { stopMeter(); stopTimer(); set("idle", { hi: dock.dataset.idleHi, en: dock.dataset.idleEn }); if (timer) timer.textContent = ""; },
    };
  }

  function chime() {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    const ctx = new AC();
    const now = ctx.currentTime;
    [[880, 0], [1320, 0.16]].forEach(([freq, at]) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.0001, now + at);
      gain.gain.exponentialRampToValueAtTime(0.3, now + at + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + at + 0.35);
      osc.connect(gain).connect(ctx.destination);
      osc.start(now + at);
      osc.stop(now + at + 0.4);
    });
    setTimeout(() => ctx.close(), 900);
  }
  const buzz = () => { if (navigator.vibrate) navigator.vibrate([80, 40, 80]); };

  function poll(fetchOnce, { every = 3000, maxMs = 600000, until, onData, onDone } = {}) {
    const started = Date.now();
    let timer = 0;
    let stopped = false;
    const stop = () => { stopped = true; clearTimeout(timer); };
    const tick = async () => {
      if (stopped) return;
      try {
        const data = await fetchOnce();
        if (onData) onData(data);
        if (until && until(data)) { stop(); if (onDone) onDone(data); return; }
      } catch (_) { /* transient network error: keep polling */ }
      if (Date.now() - started > maxMs) { stop(); return; }
      timer = setTimeout(tick, every);
    };
    timer = setTimeout(tick, every);
    return stop;
  }

  const timeNow = () => new Intl.DateTimeFormat("hi-IN", { hour: "numeric", minute: "2-digit" }).format(new Date());

  window.ParchaUI = {
    COPY, REPEAT_MESSAGE, ABSTAIN_LABELS, describeHttpError, HttpError, MicError, api,
    formatRupees, hindiDelivery, kindLabel, describeField, stageFor, flagCount, diffItems, heardQuote,
    el, icon, setIcon, renderSlip, renderStepper, emptyWorkshop, setCaption, say, stale, toast, copyText,
    shareMessage, whatsappHref, startLevelMeter, micDock, chime, buzz, poll, timeNow,
  };
  window.describeHttpError = describeHttpError;
})();
```

- [ ] **Step 4: Run.** `.\.venv\Scripts\python.exe -m pytest -q -m e2e tests/e2e/test_ui_helpers.py`. Expected: all pass. Run `Select-String -Path src\parcha\static\*.js -Pattern "innerHTML"`. Expected: no matches in `ui.js`; `app.js` is cleaned in Task 6.
- [ ] **Step 5: Check that nothing regressed.** `.\.venv\Scripts\python.exe -m pytest -q -m e2e tests/e2e/test_harness.py`. Expected: pass; the old pages still work with `ui.js` loaded.
- [ ] **Step 6: Commit.**
  `git add src/parcha/static/ui.js src/parcha/static/app.js src/parcha/templates/workshop.html src/parcha/templates/customer.html tests/e2e/test_ui_helpers.py` then `git commit -m "feat(ui): ParchaUI helpers and safe DOM components"`

---

### Task 6: Workshop page (mechanic)

**Files:**
- Rewrite: `src/parcha/templates/workshop.html`
- Modify: `src/parcha/static/app.js`. Replace everything **above** `let currentCustomerSession = null;`, plus the window exports and the `DOMContentLoaded` block at the bottom. The old customer functions stay until Task 7.
- Test: `tests/test_pages.py` (append), `tests/e2e/test_workshop_flow.py`

**Interfaces:**
- Consumes: `ParchaUI` (Task 5), the payload fields (Task 2), and the money-path 422 repeat and `abstentions`.
- Produces:
  - `recordOnce(startButton, stopButton, hooks = {onStart(stream), onEnd()}) -> Promise<Blob>`, which throws `ParchaUI.MicError`;
  - `getOrCreateSession()`, `renderSession(session)`, `handleRecordEstimate()`, `handleReask(field, chip)`, `handleStartReadback()`;
  - `showError(target, err)`;
  - `window.getCurrentSession()` for tests;
  - workshop element ids `stepper`, `transcript-content`, `share`, `copy-link`, `whatsapp-open`, `dock`, `toast`, plus every preserved id.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_pages.py`:

```python
def test_workshop_page_is_hindi_first_and_keeps_its_contract(fake_services):
    html = TestClient(create_app(fake_services)).get("/workshop").text
    assert '<html lang="hi">' in html and "/static/ui.js" in html and "/static/parcha.css" in html
    assert "बोलिए" in html and "Synthetic demo data" in html and "Kaam ka Parcha — Workshop Estimate" in html
    assert "<style>" not in html and ">Kind<" not in html
    for element_id in ("record", "stop", "message", "transcript", "card", "start-readback",
                       "customer-link", "review-section", "review-count"):
        assert f'id="{element_id}"' in html
```

  `tests/e2e/test_workshop_flow.py`:

```python
import re
from urllib.parse import unquote

import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import SCREENS, reply_by_api, speak

pytestmark = pytest.mark.e2e
INTAKE_T = "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
INCOMPLETE_V = "front brake pad saade labour do sau Somvaar shaam tak"


def dictate(page):
    page.goto("/workshop")
    speak(page, "#record", "#stop")
    expect(page.locator("#slip")).to_be_visible(timeout=15000)


def test_dictation_builds_a_hindi_first_parcha(page):
    dictate(page)
    slip = page.locator("#slip")
    for text in ("front brake pad", "₹450", "₹200", "पार्ट", "लेबर"):
        expect(slip).to_contain_text(text)
    expect(page.locator("#total-cell")).to_have_text("₹650")
    expect(page.locator("#delivery-info")).to_contain_text("सोमवार, 5 अक्टूबर · शाम")
    expect(page.locator("#parcha-no")).to_have_text(re.compile(r"^\d{6}$"))
    expect(page.locator("#transcript")).to_contain_text("आपने कहा")
    expect(page.locator("#transcript-content")).to_contain_text("front brake pad")
    expect(page.locator('#stepper [aria-current="step"]')).to_contain_text("सुनाओ")
    expect(page.locator("#start-readback")).to_be_enabled()
    expect(page.locator("body")).not_to_contain_text("items.part-1")
    expect(page.locator("body")).not_to_contain_text("part-1")
    page.screenshot(path=str(SCREENS / "workshop-slip-360.png"), full_page=True)


def test_listening_swaps_the_mic_for_a_stop_button_in_the_same_place(page):
    page.goto("/workshop")
    mic_box = page.locator("#record").bounding_box()
    assert mic_box["width"] >= 88 and mic_box["height"] >= 88
    page.locator("#record").click()
    stop = page.locator("#stop")
    expect(stop).to_be_visible()
    expect(page.locator("#record")).to_be_hidden()
    expect(page.locator("#dock")).to_have_attribute("data-mic", "listening")
    expect(page.locator("[data-mic-timer]")).to_have_text(re.compile(r"^\d:\d\d$"))
    stop_box = stop.bounding_box()
    assert abs(stop_box["x"] - mic_box["x"]) < 4 and abs(stop_box["y"] - mic_box["y"]) < 4
    stop.click()
    expect(page.locator("#slip")).to_be_visible(timeout=15000)
    expect(page.locator("#dock")).to_have_attribute("data-mic", "idle")


def test_flagged_amount_is_asked_on_its_row_and_fixed_by_voice(page, world):
    world.prisma.script_intake(transcribe=INTAKE_T, verbatim=INCOMPLETE_V)
    dictate(page)
    row = page.locator('[data-item="part-1"]')
    expect(row).to_contain_text("front brake pad का दाम?")
    expect(row).to_contain_text("अधूरी रकम — फिर से पूछेंगे")          # money-path abstain label
    expect(page.locator("#review-count")).to_contain_text("1 चीज़ जाँचनी है")
    expect(page.locator("#total-cell")).to_have_text("अधूरा")
    expect(page.locator("#start-readback")).to_be_hidden()
    page.screenshot(path=str(SCREENS / "workshop-flagged-360.png"), full_page=True)
    world.prisma.say("paanch sau")
    speak(page, row.get_by_role("button", name=re.compile("दोबारा बोलें")), "#stop")
    expect(page.locator('[data-item="part-1"] .row__amount')).to_have_text("₹500", timeout=15000)
    expect(page.locator("#total-cell")).to_have_text("₹700")
    expect(page.locator("#review-section")).to_be_hidden()
    expect(page.locator("#start-readback")).to_be_enabled()


def test_repeat_request_is_a_friendly_state(page, world):
    world.prisma.script_intake(transcribe="", verbatim="")
    page.goto("/workshop")
    speak(page, "#record", "#stop")
    expect(page.locator("#message")).to_contain_text("कृपया फिर से बोलिए", timeout=15000)
    expect(page.locator("#message")).not_to_contain_text("HTTP")
    expect(page.locator("#record")).to_be_visible()
    expect(page.locator("#record")).to_be_enabled()


def test_mic_blocked_shows_hindi_guidance(page):
    page.add_init_script(
        'navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException("blocked", "NotAllowedError"));'
    )
    page.goto("/workshop")
    page.locator("#record").click()
    expect(page.locator("#message")).to_contain_text("माइक की इजाज़त दें")
    expect(page.locator("#record")).to_be_enabled()
    expect(page.locator("#stop")).to_be_hidden()


def test_hostile_label_renders_as_text(page, world):
    world.extractor.mode = "hostile_label"
    dictate(page)
    expect(page.locator("#card img")).to_have_count(0)
    expect(page.locator("#card")).to_contain_text('<img src=x onerror="window.__xss=1">')
    assert page.evaluate("window.__xss") is None


def test_read_back_opens_a_share_sheet_with_copy_and_whatsapp(page):
    dictate(page)
    page.locator("#start-readback").click()
    share = page.locator("#share")
    expect(share).to_be_visible(timeout=15000)
    expect(page.locator('#stepper [aria-current="step"]')).to_contain_text("हाँ")
    session = page.evaluate("window.getCurrentSession()")
    customer_url = f"{page.url.split('/workshop')[0]}/customer/{session['id']}"
    expect(page.locator("#customer-link")).to_have_attribute("href", f"/customer/{session['id']}")
    page.locator("#copy-link").click()
    expect(page.locator("#toast")).to_contain_text("कॉपी हुआ")
    assert page.evaluate("navigator.clipboard.readText()") == customer_url
    wa = unquote(page.locator("#whatsapp-open").get_attribute("href"))
    assert wa.startswith("https://wa.me/?text=नमस्ते!") and "₹650" in wa and wa.endswith(customer_url)
    expect(share).to_contain_text("अपने आप कुछ नहीं भेजा जाता")
    page.screenshot(path=str(SCREENS / "workshop-share-360.png"), full_page=True)


def test_customer_approval_stamps_the_mechanics_slip(page, world):
    dictate(page)
    page.locator("#start-readback").click()
    expect(page.locator("#share")).to_be_visible(timeout=15000)
    world.prisma.say("हाँ ठीक है")
    reply_by_api(world.url, page.evaluate("window.getCurrentSession()"))
    expect(page.get_by_role("img", name="मंज़ूर — Approved")).to_be_visible(timeout=10000)
    expect(page.locator("#message")).to_contain_text("ग्राहक ने मंज़ूर किया")
    expect(page.locator('#stepper li[data-step="manzoor"]')).to_have_attribute("data-state", "done")
    page.screenshot(path=str(SCREENS / "workshop-sealed-360.png"), full_page=True)
```

- [ ] **Step 2: Run them to see them fail.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_pages.py -k workshop` and `.\.venv\Scripts\python.exe -m pytest -q -m e2e tests/e2e/test_workshop_flow.py`. Expected: the old page has no `lang="hi"`, `#slip` or `#stepper`.

- [ ] **Step 3: Rewrite `src/parcha/templates/workshop.html`.**

```html
{% extends "base.html" %}
{% block title %}Kaam ka Parcha — Workshop Estimate{% endblock %}
{% block body_class %}page--workshop{% endblock %}
{% block body %}
<header class="topbar">
  <div class="brand">काम का पर्चा<span class="en">Kaam ka Parcha</span></div>
  <span class="pill pill--demo">Synthetic demo data</span>
</header>
<main class="sheet" id="workshop" data-stage="bolo">
  <ol class="stepper" id="stepper" aria-label="काम कहाँ तक पहुँचा">
    <li data-step="bolo" data-state="current" aria-current="step">बोलो<span class="en">Speak</span></li>
    <li data-step="parcha">पर्चा<span class="en">Check</span></li>
    <li data-step="sunao">सुनाओ<span class="en">Read</span></li>
    <li data-step="haan">हाँ<span class="en">Customer</span></li>
    <li data-step="manzoor">मंज़ूर<span class="en">Approved</span></li>
  </ol>
  <output id="message" class="notice" role="status" aria-live="polite">पीला माइक दबाइए और पर्चा बोलिए।<span class="en">Tap the yellow mic and speak the estimate.</span></output>
  <section id="transcript" class="heard" hidden>
    <div class="heard__k">आपने कहा<span class="en">You said — Gnani Prisma heard</span></div>
    <p class="heard__text" id="transcript-content"></p>
  </section>
  <section id="review-section" class="flagbar" hidden aria-live="polite"><span id="review-count"></span></section>
  <section id="card">
    <div class="empty">
      <p class="empty__title">अभी कोई पर्चा नहीं<span class="en">No estimate yet</span></p>
      <p>नीचे पीला माइक दबाइए और काम, पार्ट, दाम और गाड़ी कब मिलेगी — बोलिए।<span class="en">Tap the yellow mic and say the work, parts, prices and the ready day.</span></p>
      <p class="empty__example">“फ्रंट ब्रेक पैड बदला, पार्ट साढ़े चार सौ, लेबर दो सौ, सोमवार शाम तक”</p>
    </div>
  </section>
  <section id="share" class="share" hidden>
    <h2 class="share__title">ग्राहक को भेजिए<span class="en">Send to the customer</span></h2>
    <button id="copy-link" class="btn btn--primary" type="button">लिंक कॉपी करें<span class="en">Copy link</span></button>
    <a id="whatsapp-open" class="btn btn--wa" href="#" target="_blank" rel="noopener">WhatsApp खोलें<span class="en">Open WhatsApp</span></a>
    <a id="customer-link" class="btn btn--ghost" href="#" target="_blank" rel="noopener" hidden>ग्राहक वाला पेज खोलें<span class="en">Open customer page</span></a>
    <p class="fineprint">अपने आप कुछ नहीं भेजा जाता — भेजना आपके हाथ में है।<span class="en">Nothing is sent automatically.</span></p>
  </section>
</main>
<nav class="dock" id="dock" data-mic="idle" data-idle-hi="बोलिए" data-idle-en="Tap to speak" aria-label="माइक">
  <div class="dock__inner">
    <div class="dock__row">
      <button id="record" class="mic" type="button" aria-label="बोलिए — Tap to speak"><svg aria-hidden="true" focusable="false"><use href="/static/icons.svg#mic"/></svg></button>
      <button id="stop" class="mic mic--stop" type="button" disabled hidden aria-label="रोकें — Stop"><svg aria-hidden="true" focusable="false"><use href="/static/icons.svg#stop"/></svg></button>
      <div class="dock__status">
        <span class="dock__title" data-mic-title>बोलिए</span>
        <span class="en" data-mic-sub>Tap to speak</span>
        <span class="timer" data-mic-timer></span>
        <div class="meter" aria-hidden="true"><span></span></div>
      </div>
    </div>
    <button id="start-readback" class="btn btn--primary" type="button" disabled hidden>ग्राहक को सुनाएँ<span class="en">Read to customer</span></button>
  </div>
</nav>
<div id="toast" class="toast" role="status" aria-live="polite" hidden></div>
{% endblock %}
{% block scripts %}<script src="/static/ui.js"></script><script src="/static/app.js"></script>{% endblock %}
```

- [ ] **Step 4: Rewrite the shared and workshop part of `src/parcha/static/app.js`.** Keep `getSupportedMimeType()` exactly as it is today.

```js
// Kaam ka Parcha page flows. Copy, formatting and rendering live in ui.js (window.ParchaUI).
const UI = window.ParchaUI;
const $ = (id) => document.getElementById(id);

/* getSupportedMimeType(): unchanged from the current file */

async function recordOnce(startButton, stopButton, hooks = {}) {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || typeof MediaRecorder === "undefined") {
    throw new UI.MicError("unsupported");
  }
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (err) {
    throw new UI.MicError(err && err.name === "NotAllowedError" ? "blocked" : "unavailable");
  }
  const mimeType = getSupportedMimeType();
  const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
  const chunks = [];
  recorder.ondataavailable = (event) => { if (event.data && event.data.size > 0) chunks.push(event.data); };
  if (startButton) startButton.disabled = true;
  if (stopButton) stopButton.disabled = false;
  if (hooks.onStart) hooks.onStart(stream);

  return new Promise((resolve, reject) => {
    let stopped = false;
    const cleanup = () => {
      stream.getTracks().forEach((track) => track.stop());
      if (startButton) startButton.disabled = false;
      if (stopButton) stopButton.disabled = true;
      if (hooks.onEnd) hooks.onEnd();
    };
    recorder.onerror = (event) => { cleanup(); reject(event.error || new Error("Recording error")); };
    recorder.onstop = () => { cleanup(); resolve(new Blob(chunks, { type: recorder.mimeType || mimeType || "audio/webm" })); };
    if (stopButton) {
      stopButton.addEventListener("click", () => {
        if (!stopped) { stopped = true; if (recorder.state !== "inactive") recorder.stop(); }
      }, { once: true });
    }
    recorder.start(100);
  });
}

function audioPart(blob, name) {
  const ext = blob.type.includes("wav") ? "wav" : blob.type.includes("ogg") ? "ogg" : "webm";
  return [blob, `${name}.${ext}`];
}

function formatRupees(paise) {
  return UI.formatRupees(paise);
}

function showError(target, err) {
  if (err instanceof UI.MicError) {
    const copy = err.kind === "unsupported" ? UI.COPY.micUnsupported : UI.COPY.micBlocked;
    UI.say(target, copy.hi, copy.en, "error");
  } else if (err instanceof UI.HttpError && err.repeat) {
    UI.say(target, UI.REPEAT_MESSAGE, "", "warn", UI.ABSTAIN_LABELS[err.reason] || "");
  } else if (err instanceof UI.HttpError && err.status === 409) {
    UI.stale(target);
  } else {
    UI.say(target, UI.COPY.failed.hi, UI.COPY.failed.en, "error", err && err.message);
  }
}

/* ---------- workshop (mechanic) ---------- */
let currentSession = null;
let stopWaiting = null;

async function getOrCreateSession() {
  if (currentSession && currentSession.id) return currentSession;
  const existingId = new URLSearchParams(window.location.search).get("session_id");
  if (existingId) {
    try {
      renderSession(await UI.api.get(`/sessions/${existingId}`));
      return currentSession;
    } catch (err) {
      console.warn("Failed to load existing session:", err);
    }
  }
  const created = await UI.api.post("/sessions");
  const url = new URL(window.location);
  url.searchParams.set("session_id", created.id);
  window.history.replaceState({}, "", url);
  renderSession(created);
  return currentSession;
}

function toggleListening(on) {
  $("record").hidden = on;
  $("stop").hidden = !on;
}

function renderSession(data) {
  const previousStatus = currentSession ? currentSession.status : null;
  currentSession = data;
  if (!$("workshop")) return;
  const stage = UI.stageFor(data);
  $("workshop").dataset.stage = stage;
  UI.renderStepper($("stepper"), stage);

  $("transcript").hidden = !data.mechanic_transcript;
  $("transcript-content").textContent = data.mechanic_transcript || "";

  const flags = data.review_fields || [];
  const count = UI.flagCount(flags.length);
  $("review-section").hidden = flags.length === 0;
  $("review-count").replaceChildren(count.hi, UI.el("span", { class: "en" }, count.en));

  if (data.card) {
    UI.renderSlip($("card"), data, { copy: "duplicate", flags: true, onReask: handleReask, stamp: stage === "manzoor" });
  } else {
    $("card").replaceChildren(UI.emptyWorkshop());
  }

  $("dock").hidden = !["bolo", "parcha", "sunao"].includes(stage);
  $("start-readback").hidden = stage !== "sunao";
  $("start-readback").disabled = stage !== "sunao";

  const shareOpen = stage === "haan" || stage === "manzoor";
  const customerUrl = `${window.location.origin}/customer/${data.id}`;
  $("share").hidden = !shareOpen;
  $("customer-link").hidden = !shareOpen;
  $("customer-link").href = `/customer/${data.id}`;
  $("whatsapp-open").href = UI.whatsappHref(UI.shareMessage(data, customerUrl));
  $("copy-link").dataset.url = customerUrl;

  if (stage === "haan") startWaiting();
  if (stage === "manzoor" && previousStatus && previousStatus !== "confirmed") celebrate();
  if (previousStatus === "awaiting_reply" && data.status === "review") {
    UI.say($("message"), UI.COPY.changesAsked.hi, UI.COPY.changesAsked.en, "warn");
  }
}

function startWaiting() {
  if (stopWaiting) return;
  UI.say($("message"), UI.COPY.waiting.hi, UI.COPY.waiting.en);
  stopWaiting = UI.poll(() => UI.api.get(`/sessions/${currentSession.id}`), {
    every: 3000,
    onData: (s) => { if (s.status !== currentSession.status || s.revision !== currentSession.revision) renderSession(s); },
    until: (s) => s.status !== "awaiting_reply" && s.status !== "fallback_ready",
    onDone: () => { stopWaiting = null; },
  });
}

function celebrate() {
  UI.say($("message"), UI.COPY.workshopSealed.hi, UI.COPY.workshopSealed.en, "ok");
  UI.chime();
  UI.buzz();
}

async function recordAndPost(startButton, url, name) {
  const mic = UI.micDock($("dock"));
  const message = $("message");
  try {
    const session = await getOrCreateSession();
    $("record").disabled = true;
    const blob = await recordOnce(startButton, $("stop"), {
      onStart: (stream) => { toggleListening(true); mic.listening(stream); },
      onEnd: () => toggleListening(false),
    });
    mic.processing();
    UI.say(message, UI.COPY.processing.hi, UI.COPY.processing.en);
    const form = new FormData();
    form.append("expected_revision", session.revision);
    form.append("audio", ...audioPart(blob, name));
    renderSession(await UI.api.post(url(session), form));
    const pending = currentSession.review_fields.length > 0;
    const next = pending ? UI.COPY.checkRows : UI.COPY.ready;
    UI.say(message, next.hi, next.en, pending ? "warn" : "ok");
  } catch (err) {
    console.error(`${name} failed:`, err);
    showError(message, err);
  } finally {
    mic.idle();
    toggleListening(false);
    $("record").disabled = false;
    $("stop").disabled = true;
  }
}

function handleRecordEstimate() {
  return recordAndPost($("record"), (s) => `/sessions/${s.id}/intake`, "estimate");
}

function handleReask(field, chip) {
  return recordAndPost(chip, (s) => `/sessions/${s.id}/reask/${field}`, "reask");
}

async function handleStartReadback() {
  if (!currentSession) return;
  const button = $("start-readback");
  const message = $("message");
  try {
    button.disabled = true;
    UI.say(message, "ग्राहक के लिए आवाज़ बन रही है…", "Preparing the customer read-back…");
    const form = new FormData();
    form.append("expected_revision", currentSession.revision);
    await UI.api.post(`/sessions/${currentSession.id}/readback`, form);
    renderSession(await UI.api.get(`/sessions/${currentSession.id}`));
    UI.say(message, UI.COPY.sendLink.hi, UI.COPY.sendLink.en, "ok");
  } catch (err) {
    console.error("Readback failed:", err);
    showError(message, err);
    button.disabled = UI.stageFor(currentSession) !== "sunao";
  }
}

function initWorkshopPage() {
  $("record").addEventListener("click", handleRecordEstimate);
  $("start-readback").addEventListener("click", handleStartReadback);
  $("copy-link").addEventListener("click", async (event) => {
    if (await UI.copyText(event.currentTarget.dataset.url)) UI.toast(`${UI.COPY.copied.hi} · ${UI.COPY.copied.en}`);
  });
  if (new URLSearchParams(window.location.search).get("session_id")) {
    getOrCreateSession().catch((err) => showError($("message"), err));
  }
}
```

  Bottom of the file (replacing the old exports and `DOMContentLoaded`):

```js
Object.assign(window, {
  recordOnce, formatRupees, getSupportedMimeType, getOrCreateSession, renderSession,
  handleRecordEstimate, handleReask, handleStartReadback,
  renderCustomerCard, initCustomerPage, handleCustomerRecord,
  getCurrentSession: () => currentSession,
});

document.addEventListener("DOMContentLoaded", () => {
  if ($("workshop")) initWorkshopPage();
  if (window.location.pathname.startsWith("/customer/")) initCustomerPage();
});
```

- [ ] **Step 5: Run.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_pages.py tests/test_app.py` and `.\.venv\Scripts\python.exe -m pytest -q -m e2e tests/e2e/test_harness.py tests/e2e/test_ui_helpers.py tests/e2e/test_workshop_flow.py`. Expected: all pass. Look over `var/e2e/workshop-*.png` at 360 px.
- [ ] **Step 6: Commit.**
  `git add src/parcha/templates/workshop.html src/parcha/static/app.js tests/test_pages.py tests/e2e/test_workshop_flow.py` then `git commit -m "feat(ui): Hindi-first workshop page with big mic, row-level re-ask and approval stamp"`

---

### Task 7: Customer page (vehicle owner)

**Files:**
- Rewrite: `src/parcha/templates/customer.html`
- Modify: `src/parcha/static/app.js` (replace everything from `let currentCustomerSession = null;` down to the window exports); `src/parcha/static/parcha.css` (append `.card-head`)
- Test: `tests/test_pages.py` (append), `tests/e2e/test_customer_flow.py`

**Interfaces:**
- Consumes: Task 5 (`renderSlip` with `previous`, `setCaption`, `micDock`, `poll`, `say`, `stale`, `copyText`, `toast`) and Task 6 (`recordOnce`, `audioPart`, `showError`, `$`).
- Produces:
  - `renderCustomerCard(session, {previous})`, `initCustomerPage()`, `handleCustomerRecord(sessionId)`;
  - `handleReplyOutcome(sessionId, reply, previousCard)`, `showReceipt({words, how})`;
  - customer element ids `play-readback`, `call-status`, `call-progress`, `readback-caption`, `slip-slot`, `receipt-total`, `receipt-said`, `receipt-words`, `receipt-how`, `receipt-time`, `whatsapp-copy`, `verify-link`, `dock`, `toast`, plus every preserved id.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_pages.py`:

```python
SIM = ("Simulated phone line: audio passed through G.711 + recorded engine ambience at 5 dB. "
       "No call was placed. All names and amounts are synthetic.")


def test_customer_page_is_a_call_with_unticked_consent(fake_services):
    client, sid, _ = awaiting(fake_services)
    html = client.get(f"/customer/{sid}").text
    assert "यह नकली फ़ोन लाइन है" in html and SIM in html
    assert "गैराज से कॉल" in html and "₹650" in html and "पार्ट" in html and "Kaam ka Parcha — Customer Estimate Review" in html
    box = re.search(r'<input[^>]*id="dpdp-consent-checkbox"[^>]*>', html).group(0)
    assert "checked" not in box
    assert re.search(r'id="readback-caption"[^>]*>\s*\S', html)
    assert "DPDP Act 2023" in html and "<style>" not in html
```

  `tests/e2e/test_customer_flow.py`:

```python
import re

import httpx
import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import SCREENS, new_parcha, speak

pytestmark = pytest.mark.e2e


def open_customer(page, world, *, consent=True, read_back=True):
    session = new_parcha(world.url, read_back=read_back)
    page.goto(f"/customer/{session['id']}")
    if consent:
        page.locator("#dpdp-consent-checkbox").check()
        expect(page.locator("#customer-record")).to_be_enabled()
    return session


def answer(page, world, words):
    world.prisma.say(words)
    speak(page, "#customer-record", "#customer-stop")


def test_customer_page_opens_like_a_call_with_the_slip(page, world):
    open_customer(page, world, consent=False)
    expect(page.locator("#disclosure")).to_contain_text("यह नकली फ़ोन लाइन है")
    expect(page.locator("#disclosure")).to_contain_text("No call was placed.")
    expect(page.locator("#audio-panel")).to_contain_text("गैराज से कॉल")
    expect(page.locator("#readback-caption")).not_to_be_empty()
    expect(page.locator("#total-cell")).to_have_text("₹650")
    expect(page.locator("#dpdp-consent-checkbox")).not_to_be_checked()
    expect(page.locator("#customer-record")).to_be_disabled()
    expect(page.locator("#play-readback")).to_be_enabled(timeout=10000)
    page.screenshot(path=str(SCREENS / "customer-call-360.png"), full_page=True)


def test_consent_gates_the_reply_mic_and_is_recorded(page, world):
    session = open_customer(page, world, consent=False)
    page.locator("#dpdp-consent-checkbox").check()
    expect(page.locator("#customer-record")).to_be_enabled()
    expect(page.locator("#toast")).to_contain_text("सहमति दर्ज हुई")
    assert httpx.get(f"{world.url}/sessions/{session['id']}").json()["dpdp_consent_granted"] is True
    page.locator("#dpdp-consent-checkbox").uncheck()
    expect(page.locator("#customer-record")).to_be_disabled()


def test_haan_seals_with_a_upi_style_receipt_and_stamp(page, world):
    open_customer(page, world)
    answer(page, world, "हाँ ठीक है")
    receipt = page.locator("#confirmed-banner")
    expect(receipt).to_be_visible(timeout=15000)
    expect(receipt).to_contain_text("पर्चा मंज़ूर हुआ")
    expect(page.locator("#receipt-total")).to_have_text("₹650")
    expect(page.locator("#receipt-said")).to_contain_text("हाँ ठीक है")
    expect(page.get_by_role("img", name="मंज़ूर — Approved")).to_be_visible()
    expect(page.locator("#dock")).to_be_hidden()
    expect(page.locator("#verify-link")).to_have_attribute("href", re.compile(r"^/verify/"))
    page.locator("#whatsapp-copy").click()
    expect(page.locator("#toast")).to_contain_text("कॉपी हुआ")
    assert "650" in page.evaluate("navigator.clipboard.readText()")
    page.screenshot(path=str(SCREENS / "customer-sealed-360.png"), full_page=True)


def test_correction_shows_the_old_amount_struck_and_a_fresh_call(page, world):
    open_customer(page, world)
    answer(page, world, "nahi front brake pad 500")
    row = page.locator('[data-item="part-1"]')
    expect(row.locator("s")).to_have_text("₹450", timeout=15000)
    expect(row).to_contain_text("₹500")
    expect(page.locator("#total-cell")).to_have_text("₹700")
    expect(page.locator("#readback-player")).to_have_attribute("src", re.compile(r"revision=2"))
    expect(page.locator("#customer-status")).to_contain_text("नया पर्चा")
    page.screenshot(path=str(SCREENS / "customer-correction-360.png"), full_page=True)


def test_three_unclear_replies_offer_tap_fallback(page, world):
    open_customer(page, world)
    for _ in range(2):
        answer(page, world, "kya bola aapne")
        expect(page.locator("#customer-status")).to_contain_text("समझ नहीं आया", timeout=15000)
        expect(page.locator("#customer-record")).to_be_enabled()
    answer(page, world, "kya bola aapne")
    expect(page.locator("#fallback-banner")).to_be_visible(timeout=15000)
    page.locator("#fallback-approve").click()
    expect(page.locator("#confirmed-banner")).to_be_visible()
    expect(page.locator("#receipt-how")).to_contain_text("बटन से मंज़ूर")


def test_audio_failure_keeps_reply_available(page, world):
    page.route("**/readback.wav*", lambda route: route.fulfill(status=404, body="missing"))
    open_customer(page, world)
    expect(page.locator("#call-status")).to_contain_text("आवाज़ नहीं चली", timeout=10000)
    expect(page.locator("#readback-caption")).not_to_be_empty()
    expect(page.locator("#customer-record")).to_be_enabled()


def test_stale_reply_offers_reload(page, world):
    page.route("**/sessions/*/reply", lambda route: route.fulfill(
        status=409, content_type="application/json", body='{"detail": "stale revision"}'))
    open_customer(page, world)
    answer(page, world, "हाँ ठीक है")
    expect(page.locator("#customer-message")).to_contain_text("पर्चा बदल गया है", timeout=15000)
    expect(page.get_by_role("button", name=re.compile("ताज़ा करें"))).to_be_visible()


def test_page_waits_for_the_read_back_then_updates_itself(page, world):
    session = open_customer(page, world, consent=False, read_back=False)
    expect(page.locator("#customer-status")).to_contain_text("गैराज पर्चा तैयार कर रहा है")
    httpx.post(f"{world.url}/sessions/{session['id']}/readback",
               data={"expected_revision": session["revision"]}).raise_for_status()
    expect(page.locator("#readback-caption")).not_to_be_empty(timeout=10000)
    expect(page.locator("#readback-player")).to_have_attribute("src", re.compile(r"readback\.wav\?revision=\d+"))
```

- [ ] **Step 2: Run them to see them fail.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_pages.py -k customer`. Expected: the old page has no Hindi disclosure and its checkbox is `checked`.

- [ ] **Step 3: Append to `parcha.css`:** `.card-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 8px; }`

- [ ] **Step 4: Rewrite `src/parcha/templates/customer.html`.**

```html
{% extends "base.html" %}
{% from "_slip.html" import slip %}
{% block title %}Kaam ka Parcha — Customer Estimate Review{% endblock %}
{% block body_class %}page--customer{% endblock %}
{% block body %}
<div class="disclosure" id="disclosure" role="note">
  <span>यह नकली फ़ोन लाइन है — कोई कॉल नहीं हुई। सभी नाम और रकम डेमो के हैं।</span>
  <span class="en" lang="en">Simulated phone line: audio passed through G.711 + recorded engine ambience at 5 dB. No call was placed. All names and amounts are synthetic.</span>
</div>
<main class="sheet" id="customer-container" data-session-id="{{ session.id }}" data-revision="{{ revision }}" data-readback-revision="{{ readback_revision if readback_revision is not none else '' }}" data-status="{{ status }}">
  <section class="receipt" id="confirmed-banner" role="status"{% if status != "confirmed" %} hidden{% endif %}>
    <div class="receipt__tick" aria-hidden="true"><svg focusable="false"><use href="/static/icons.svg#check"/></svg></div>
    <h1 class="receipt__title">पर्चा मंज़ूर हुआ<span class="en">Estimate Confirmed</span></h1>
    <p class="receipt__total" id="receipt-total">{{ card.maybe_total_paise | inr if card else "₹ —" }}</p>
    <p class="receipt__said" id="receipt-said" hidden>आपने कहा: “<span id="receipt-words"></span>”</p>
    <p class="receipt__meta"><span id="receipt-how">फ़ोन पर आवाज़ से मंज़ूर</span> · № {{ parcha_no }} <span id="receipt-time"></span></p>
    <div class="receipt__actions">
      <a id="download-pdf-link" class="btn btn--primary" href="/sessions/{{ session.id }}/pdf" download>PDF डाउनलोड करें<span class="en">Download sealed PDF</span></a>
      <button id="whatsapp-copy" class="btn btn--wa" type="button">WhatsApp टेक्स्ट कॉपी करें<span class="en">Copy WhatsApp text</span></button>
      <a id="verify-link" class="btn btn--ghost" href="/verify/{{ session.id }}">असली है? जाँचें<span class="en">Verify</span></a>
      <a id="whatsapp-link" class="btn btn--ghost" href="/sessions/{{ session.id }}/whatsapp" target="_blank" rel="noopener">टेक्स्ट फ़ाइल<span class="en">Text file</span></a>
    </div>
    <p class="fineprint">कॉपी करने से कुछ अपने आप नहीं भेजा जाता।<span class="en">Copying sends nothing by itself.</span></p>
  </section>

  <section class="call" id="audio-panel" data-call="idle" aria-label="गैराज से कॉल">
    <div class="call__who">
      <div class="call__avatar" aria-hidden="true">गै</div>
      <div>
        <div class="call__title">गैराज से कॉल<span class="en">Call from workshop</span></div>
        <div class="call__status" id="call-status">{% if readback_revision is not none %}पर्चा सुनने के लिए ▶ दबाइए{% else %}गैराज पर्चा तैयार कर रहा है…{% endif %}</div>
      </div>
    </div>
    <div class="call__controls">
      <button id="play-readback" class="play" type="button" aria-label="सुनें — Listen" disabled><svg aria-hidden="true" focusable="false"><use href="/static/icons.svg#play"/></svg></button>
      <div class="call__progress" aria-hidden="true"><span id="call-progress"></span></div>
    </div>
    <p class="call__caption" id="readback-caption" aria-live="polite">{{ readback_text or "" }}</p>
    <audio id="readback-player" preload="auto"{% if readback_revision is not none %} src="/sessions/{{ session.id }}/readback.wav?revision={{ readback_revision }}"{% endif %}></audio>
  </section>

  <section id="estimate-card" aria-label="आपका पर्चा">
    <div class="card-head">
      <span id="card-status-badge" class="pill {{ 'pill--ok' if status == 'confirmed' else ('pill--wait' if status == 'awaiting_reply' else 'pill--warn') }}">{{ status | status_hi }}</span>
      <span id="card-revision-badge" class="pill">Rev {{ revision }}</span>
    </div>
    <div id="slip-slot">{{ slip(card, card.maybe_total_paise if card else none, parcha_no, copy="original", stamp=(status == "confirmed")) }}</div>
  </section>

  <section class="consent" id="dpdp-consent-box"{% if status == "confirmed" %} hidden{% endif %}>
    <label class="consent__row"><input type="checkbox" id="dpdp-consent-checkbox"{% if dpdp_consent_granted %} checked{% endif %}>
      <span>मेरी आवाज़ रिकॉर्ड होकर इस पर्चे के सबूत के तौर पर रखी जाए — मैं सहमत हूँ।<span class="en">I agree my voice is recorded as proof for this parcha.</span></span></label>
    <details class="consent__full">
      <summary>पूरा नोटिस<span class="en">Full notice (DPDP Act 2023)</span></summary>
      <p><strong>DPDP Act 2023 Statutory Privacy Notice:</strong> I understand and give consent that my spoken voice reply will be recorded, processed, and cryptographically hashed as an electronic biometric confirmation record under the <em>Digital Personal Data Protection Act, 2023</em> and <em>Bharatiya Sakshya Adhiniyam, 2023</em>.</p>
    </details>
  </section>

  <section class="fallback" id="fallback-banner"{% if status != "fallback_ready" %} hidden{% endif %}>
    <h2>लाइन साफ़ नहीं है<span class="en">Voice line unclear</span></h2>
    <p>बटन से जवाब दीजिए।<span class="en">Answer with a button instead.</span></p>
    <div class="fallback__actions">
      <button id="fallback-approve" class="btn btn--haan" type="button">मंज़ूर करें<span class="en">Approve</span></button>
      <button id="fallback-reject" class="btn btn--change" type="button">बदलाव चाहिए<span class="en">Request changes</span></button>
    </div>
  </section>

  <div id="customer-status" class="status-line" role="status" aria-live="polite"></div>
  <output id="customer-message" class="notice">पहले ऊपर पर्चा सुनिए, फिर नीचे माइक दबाकर जवाब दीजिए।<span class="en">Listen first, then tap the mic to answer.</span></output>
</main>

<nav class="dock" id="dock" data-mic="idle" data-idle-hi="बोलकर जवाब दें" data-idle-en="Speak your answer" aria-label="जवाब"{% if status in ("confirmed", "fallback_ready") %} hidden{% endif %}>
  <div class="dock__inner">
    <div class="hints"><span class="hint hint--haan">“हाँ, ठीक है”</span><span class="hint hint--change">“नहीं, ब्रेक पैड 500 था”</span></div>
    <div class="dock__row">
      <button id="customer-record" class="mic" type="button" disabled aria-label="बोलकर जवाब दें — Speak your answer"><svg aria-hidden="true" focusable="false"><use href="/static/icons.svg#mic"/></svg></button>
      <button id="customer-stop" class="mic mic--stop" type="button" disabled hidden aria-label="रोकें — Stop"><svg aria-hidden="true" focusable="false"><use href="/static/icons.svg#stop"/></svg></button>
      <div class="dock__status">
        <span class="dock__title" data-mic-title>बोलकर जवाब दें</span>
        <span class="en" data-mic-sub>Speak your answer</span>
        <span class="timer" data-mic-timer></span>
        <div class="meter" aria-hidden="true"><span></span></div>
      </div>
    </div>
  </div>
</nav>
<div id="toast" class="toast" role="status" aria-live="polite" hidden></div>
{% endblock %}
{% block scripts %}<script src="/static/ui.js"></script><script src="/static/app.js"></script>{% endblock %}
```

- [ ] **Step 5: Replace the customer part of `app.js`.**

```js
/* ---------- customer (vehicle owner) ---------- */
let currentCustomerSession = null;
let isCustomerRecording = false;

function renderCustomerCard(data, opts = {}) {
  currentCustomerSession = data;
  const sealed = data.status === "confirmed";
  UI.renderSlip($("slip-slot"), data, { copy: "original", previous: opts.previous, stamp: sealed });
  const badge = $("card-status-badge");
  badge.textContent = data.status_label || data.status;
  badge.className = `pill ${sealed ? "pill--ok" : data.status === "awaiting_reply" ? "pill--wait" : "pill--warn"}`;
  $("card-revision-badge").textContent = `Rev ${data.revision}`;
  $("confirmed-banner").hidden = !sealed;
  $("receipt-total").textContent = UI.formatRupees(data.total_paise);
  $("fallback-banner").hidden = data.status !== "fallback_ready";
  $("dock").hidden = sealed || data.status === "fallback_ready";
  $("dpdp-consent-box").hidden = sealed;
  if (data.readback_text) UI.setCaption($("readback-caption"), data.readback_text, 0);
  enableRecordIfReady();
}

function describeCustomerState() {
  const s = currentCustomerSession;
  const status = $("customer-status");
  const message = $("customer-message");
  if (!s) return;
  if (s.status === "confirmed") {
    status.textContent = "पर्चा मंज़ूर हो चुका है";
    UI.say(message, "PDF और WhatsApp टेक्स्ट ऊपर हैं।", "The PDF and WhatsApp text are above.", "ok");
  } else if (s.status === "fallback_ready") {
    status.textContent = "लाइन साफ़ नहीं है";
    UI.say(message, "नीचे बटन से जवाब दीजिए।", "Answer with the buttons.", "warn");
  } else if (s.readback_revision === null || s.readback_revision === undefined) {
    status.textContent = "गैराज पर्चा तैयार कर रहा है…";
    UI.say(message, "तैयार होते ही यहाँ अपने आप दिखेगा।", "It will appear here by itself.");
  } else {
    status.textContent = "पर्चा सुनिए, फिर जवाब दीजिए";
    UI.say(message, "सुनने के बाद ✓ सहमति दीजिए और माइक दबाकर बोलिए।", "Listen, tick consent, then tap the mic and answer.");
  }
}

function enableRecordIfReady() {
  const s = currentCustomerSession;
  const button = $("customer-record");
  const consent = $("dpdp-consent-checkbox");
  if (!button) return;
  button.disabled = !(s && s.status === "awaiting_reply" && s.readback_revision !== null && s.readback_revision !== undefined
    && consent && consent.checked && !isCustomerRecording);
}

function loadReadback(url) {
  const player = $("readback-player");
  player.src = url;
  player.load();
  $("play-readback").disabled = true;
  $("audio-panel").dataset.call = "idle";
  $("call-progress").style.width = "0%";
}

function audioFailed() {
  if (!$("readback-player").getAttribute("src")) return;
  $("play-readback").disabled = true;
  $("call-status").textContent = "आवाज़ नहीं चली — नीचे लिखा पर्चा पढ़कर जवाब दीजिए।";
  enableRecordIfReady();
}

function wireCall() {
  const player = $("readback-player");
  const play = $("play-readback");
  const call = $("audio-panel");
  const caption = () => (currentCustomerSession && currentCustomerSession.readback_text) || "";
  player.addEventListener("canplay", () => { play.disabled = false; });
  play.addEventListener("click", () => { if (player.paused) player.play().catch(audioFailed); else player.pause(); });
  player.addEventListener("play", () => { call.dataset.call = "talking"; UI.setIcon(play, "pause"); $("call-status").textContent = "बात चल रही है…"; });
  player.addEventListener("pause", () => { if (!player.ended) call.dataset.call = "idle"; UI.setIcon(play, "play"); });
  player.addEventListener("timeupdate", () => {
    const progress = player.duration ? player.currentTime / player.duration : 0;
    $("call-progress").style.width = `${Math.round(progress * 100)}%`;
    UI.setCaption($("readback-caption"), caption(), progress);
  });
  player.addEventListener("ended", () => {
    call.dataset.call = "ended";
    UI.setCaption($("readback-caption"), caption(), 1);
    $("call-status").textContent = "अब नीचे माइक दबाकर जवाब दीजिए";
  });
  player.addEventListener("error", audioFailed);
}

function wireConsent(sessionId) {
  const box = $("dpdp-consent-checkbox");
  box.addEventListener("change", async () => {
    if (box.checked && currentCustomerSession && !currentCustomerSession.dpdp_consent_granted) {
      try {
        const form = new FormData();
        form.append("expected_revision", currentCustomerSession.revision);
        form.append("granted", "true");
        await UI.api.post(`/sessions/${sessionId}/consent`, form);
        currentCustomerSession.dpdp_consent_granted = true;
        UI.toast(`${UI.COPY.consentSaved.hi} · ${UI.COPY.consentSaved.en}`);
      } catch (err) {
        box.checked = false;
        showError($("customer-message"), err);
      }
    }
    enableRecordIfReady();
  });
}

function showReceipt({ words = "", how = "फ़ोन पर आवाज़ से मंज़ूर" } = {}) {
  $("receipt-said").hidden = !words;
  $("receipt-words").textContent = words;
  $("receipt-how").textContent = how;
  $("receipt-time").textContent = `· ${UI.timeNow()}`;
  $("confirmed-banner").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function handleCustomerRecord(sessionId) {
  const s = currentCustomerSession;
  const message = $("customer-message");
  if (!s) return;
  if (!$("dpdp-consent-checkbox").checked) {
    UI.say(message, UI.COPY.consentNeeded.hi, UI.COPY.consentNeeded.en, "warn");
    return;
  }
  const player = $("readback-player");
  if (!player.paused) player.pause();
  const record = $("customer-record");
  const stop = $("customer-stop");
  const mic = UI.micDock($("dock"));
  isCustomerRecording = true;
  try {
    const blob = await recordOnce(record, stop, {
      onStart: (stream) => { record.hidden = true; stop.hidden = false; mic.listening(stream); },
      onEnd: () => { record.hidden = false; stop.hidden = true; },
    });
    mic.processing();
    UI.say(message, UI.COPY.processing.hi, UI.COPY.processing.en);
    const form = new FormData();
    form.append("expected_revision", s.revision);
    form.append("readback_revision", s.readback_revision);
    form.append("dpdp_consent", "true");
    form.append("audio", ...audioPart(blob, "reply"));
    const reply = await UI.api.post(`/sessions/${sessionId}/reply`, form);
    await handleReplyOutcome(sessionId, reply, s.card);
  } catch (err) {
    console.error("Customer reply failed:", err);
    showError(message, err);
  } finally {
    isCustomerRecording = false;
    mic.idle();
    record.hidden = false;
    stop.hidden = true;
    stop.disabled = true;
    enableRecordIfReady();
  }
}

async function handleReplyOutcome(sessionId, reply, previousCard) {
  const status = $("customer-status");
  const message = $("customer-message");
  const fresh = () => UI.api.get(`/sessions/${sessionId}`);
  if (reply.outcome === "confirmed") {
    renderCustomerCard(await fresh());
    showReceipt({ words: reply.transcript || "" });
    status.textContent = "पर्चा मंज़ूर हुआ";
    UI.say(message, "धन्यवाद! गैराज को पता चल गया है।", "Thank you — the workshop has been told.", "ok");
  } else if (reply.outcome === "needs_readback") {
    UI.say(message, "बदलाव दर्ज हुआ — नया पर्चा बन रहा है…", "Change noted — preparing the new estimate…");
    const form = new FormData();
    form.append("expected_revision", reply.revision);
    const readback = await UI.api.post(`/sessions/${sessionId}/readback`, form);
    renderCustomerCard(await fresh(), { previous: previousCard });
    loadReadback(readback.audio_url);
    status.textContent = "नया पर्चा तैयार — फिर से सुनिए";
    UI.say(message, "ऊपर नया पर्चा सुनिए, फिर जवाब दीजिए।", "Listen to the updated estimate, then answer.");
  } else if (reply.outcome === "ask_field") {
    renderCustomerCard(await fresh());
    status.textContent = "किस चीज़ को बदलना है?";
    UI.say(message, "चीज़ का नाम लेकर बोलिए, जैसे “ब्रेक पैड 500”।", reply.message || "Name the item you want to change.", "warn");
  } else if (reply.outcome === "fallback") {
    renderCustomerCard(await fresh());
    status.textContent = "लाइन साफ़ नहीं है";
    UI.say(message, "नीचे बटन से जवाब दीजिए।", reply.message || "Answer with the buttons.", "warn");
  } else {
    status.textContent = "समझ नहीं आया";
    UI.say(message, "साफ़ बोलिए: “हाँ, ठीक है” — या क्या बदलना है।", reply.message || "Say yes, or say what to change.", "warn");
  }
}

function wireFallback(sessionId) {
  const send = async (action) => {
    const form = new FormData();
    form.append("action", action);
    form.append("expected_revision", currentCustomerSession.revision);
    try {
      await UI.api.post(`/sessions/${sessionId}/fallback`, form);
      renderCustomerCard(await UI.api.get(`/sessions/${sessionId}`));
      if (action === "approve") {
        showReceipt({ how: "बटन से मंज़ूर" });
        $("customer-status").textContent = "पर्चा मंज़ूर हुआ";
      } else {
        $("customer-status").textContent = "गैराज को बता दिया गया है";
        UI.say($("customer-message"), "गैराज आपका बदलाव देखकर नया पर्चा भेजेगा।", "The workshop will send an updated estimate.");
      }
    } catch (err) {
      showError($("customer-message"), err);
    }
  };
  $("fallback-approve").addEventListener("click", () => send("approve"));
  $("fallback-reject").addEventListener("click", () => send("request_changes"));
}

async function copyWhatsapp(sessionId) {
  try {
    const res = await fetch(`/sessions/${sessionId}/whatsapp`);
    if (!res.ok) throw new UI.HttpError(res.status, res.statusText);
    if (await UI.copyText(await res.text())) UI.toast(`${UI.COPY.copied.hi} · ${UI.COPY.copied.en}`);
  } catch (err) {
    showError($("customer-message"), err);
  }
}

function waitForReadback(sessionId) {
  UI.poll(() => UI.api.get(`/sessions/${sessionId}`), {
    every: 3000,
    until: (s) => (s.readback_revision !== null && s.readback_revision !== undefined) || s.status === "confirmed",
    onDone: (s) => {
      renderCustomerCard(s);
      if (s.readback_revision !== null && s.readback_revision !== undefined) {
        loadReadback(`/sessions/${sessionId}/readback.wav?revision=${s.readback_revision}`);
        $("call-status").textContent = "पर्चा सुनने के लिए ▶ दबाइए";
      }
      describeCustomerState();
    },
  });
}

async function initCustomerPage() {
  const root = $("customer-container");
  if (!root) return;
  const sessionId = root.dataset.sessionId;
  wireCall();
  wireConsent(sessionId);
  wireFallback(sessionId);
  $("customer-record").addEventListener("click", () => handleCustomerRecord(sessionId));
  $("whatsapp-copy").addEventListener("click", () => copyWhatsapp(sessionId));
  try {
    renderCustomerCard(await UI.api.get(`/sessions/${sessionId}`));
  } catch (err) {
    showError($("customer-message"), err);
    return;
  }
  describeCustomerState();
  const s = currentCustomerSession;
  if ((s.readback_revision === null || s.readback_revision === undefined) && s.status !== "confirmed") waitForReadback(sessionId);
}
```

  In the `DOMContentLoaded` block, change the customer condition to `if ($("customer-container")) initCustomerPage();`.

- [ ] **Step 6: Run.** `.\.venv\Scripts\python.exe -m pytest -q` (whole offline suite), then `.\.venv\Scripts\python.exe -m pytest -q -m e2e tests/e2e`. Expected: all pass. Run `Select-String -Path src\parcha\static\*.js -Pattern "innerHTML"`. Expected: **no matches**.
- [ ] **Step 7: Commit.**
  `git add src/parcha/templates/customer.html src/parcha/static/app.js src/parcha/static/parcha.css tests/test_pages.py tests/e2e/test_customer_flow.py` then `git commit -m "feat(ui): call-style customer page with explicit consent, correction diff and UPI-style seal"`

---

### Task 8: Stage view for the 60-second demo

**Files:**
- Modify: `src/parcha/app.py` (new route)
- Create: `src/parcha/templates/stage.html`
- Test: `tests/test_pages.py` (append), `tests/e2e/test_stage.py`

**Interfaces:**
- Consumes: `services.store.create()`, Task 1's `parcha_no`, and the Task 6 and Task 7 pages.
- Produces: `GET /stage` (HTML). It creates one session and renders `#stage-workshop` → `/workshop?session_id={id}` and `#stage-customer` → `/customer/{id}`.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_pages.py`:

```python
def test_stage_creates_one_session_and_frames_both_phones(fake_services):
    client = TestClient(create_app(fake_services))
    html = client.get("/stage").text
    sid = re.search(r'src="/customer/([A-Za-z0-9_-]+)"', html).group(1)
    assert f'src="/workshop?session_id={sid}"' in html
    assert client.get(f"/sessions/{sid}").status_code == 200
    assert html.count('allow="microphone; autoplay; clipboard-write"') == 2
    assert "Gnani Prisma" in html and "Gnani Timbre" in html
```

  `tests/e2e/test_stage.py`:

```python
import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import SCREENS, speak

pytestmark = pytest.mark.e2e


def test_stage_runs_the_whole_loop_on_one_screen(page, world):
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto("/stage")
    shop = page.frame_locator("#stage-workshop")
    owner = page.frame_locator("#stage-customer")
    speak(shop, "#record", "#stop")
    expect(shop.locator("#total-cell")).to_have_text("₹650", timeout=15000)
    shop.locator("#start-readback").click()
    expect(owner.locator("#readback-caption")).not_to_be_empty(timeout=10000)
    owner.locator("#dpdp-consent-checkbox").check()
    world.prisma.say("हाँ ठीक है")
    speak(owner, "#customer-record", "#customer-stop")
    expect(owner.locator("#confirmed-banner")).to_be_visible(timeout=15000)
    expect(shop.get_by_role("img", name="मंज़ूर — Approved")).to_be_visible(timeout=10000)
    page.screenshot(path=str(SCREENS / "stage-sealed-1440.png"), full_page=True)
```

- [ ] **Step 2: Run to see them fail.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_pages.py -k stage`. Expected: 404.
- [ ] **Step 3: Add the route** in `create_app`, next to `/workshop`:

```python
    @app.get("/stage", response_class=HTMLResponse)
    def stage(request: Request):
        session = services.store.create()
        return templates.TemplateResponse(request, "stage.html", {"session": session, "parcha_no": parcha_no(session.id)})
```

- [ ] **Step 4: Create `src/parcha/templates/stage.html`.**

```html
{% extends "base.html" %}
{% block title %}Kaam ka Parcha — Stage{% endblock %}
{% block body_class %}page--stage{% endblock %}
{% block body %}
<header class="stage__head">
  <div class="brand">काम का पर्चा<span class="en">Kaam ka Parcha — one parcha, two phones</span></div>
  <p>मिस्त्री बोलता है → ग्राहक सुनकर “हाँ” कहता है → पर्चा मंज़ूर<span class="en">Mechanic speaks → customer hears and says “haan” → parcha sealed</span></p>
  <p class="fineprint">Gnani Prisma सुनता है · Gnani Timbre बोलता है · पर्चा № {{ parcha_no }}<span class="en">Simulated phone line and synthetic demo data. No call is placed and nothing is sent.</span></p>
</header>
<main class="stage">
  <figure class="phone">
    <figcaption>मिस्त्री<span class="en">Mechanic</span></figcaption>
    <iframe id="stage-workshop" title="Mechanic phone" src="/workshop?session_id={{ session.id }}" allow="microphone; autoplay; clipboard-write"></iframe>
  </figure>
  <figure class="phone">
    <figcaption>ग्राहक<span class="en">Vehicle owner</span></figcaption>
    <iframe id="stage-customer" title="Vehicle owner phone" src="/customer/{{ session.id }}" allow="microphone; autoplay; clipboard-write"></iframe>
  </figure>
</main>
{% endblock %}
```

- [ ] **Step 5: Run.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_pages.py` and `.\.venv\Scripts\python.exe -m pytest -q -m e2e tests/e2e/test_stage.py`. Expected: pass; `var/e2e/stage-sealed-1440.png` shows both phones, with the stamp on the mechanic's slip.
- [ ] **Step 6: Commit.**
  `git add src/parcha/app.py src/parcha/templates/stage.html tests/test_pages.py tests/e2e/test_stage.py` then `git commit -m "feat(ui): stage view with mechanic and owner phones side by side"`

---

### Task 9: Responsive and accessibility audit, budget, docs

**Files:**
- Create: `tests/e2e/test_responsive.py`, `docs/ui/*.png` (curated copies from `var/e2e/`)
- Modify: `README.md` ("Visual Interface Walkthrough"), `docs/demo.md` (shot list uses `/stage`), `scripts/run_webattack_suite.py` (selectors only, if they rely on removed markup)

**Interfaces:**
- Consumes: every page.
- Produces: the audit tests and the curated screenshots.

- [ ] **Step 1: Write the audit tests** in `tests/e2e/test_responsive.py`:

```python
import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import SCREENS, new_parcha, reply_by_api, speak

pytestmark = pytest.mark.e2e
VIEWPORTS = [(360, 800), (390, 844), (768, 1024), (1440, 900)]
INTAKE_T = "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
INCOMPLETE_V = "front brake pad saade labour do sau Somvaar shaam tak"
OVERFLOW = "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
TARGETS = """() => [...document.querySelectorAll('button, a.btn, summary, input[type=checkbox]')]
  .filter((n) => n.getClientRects().length && !n.closest('[hidden]'))
  .map((n) => { const r = (n.type === 'checkbox' ? n.closest('label') : n).getBoundingClientRect();
                return { name: n.id || n.getAttribute('aria-label') || n.textContent.trim().slice(0, 24),
                         w: r.width, h: r.height, mic: n.classList.contains('mic') }; })"""
FONT = "() => parseFloat(getComputedStyle(document.body).fontSize)"
UNNAMED = """() => [...document.querySelectorAll('button')].filter((b) => b.getClientRects().length)
  .filter((b) => !(b.getAttribute('aria-label') || b.textContent.trim())).map((b) => b.outerHTML.slice(0, 80))"""


def audit(page, label, width):
    assert page.evaluate(OVERFLOW) <= 1, f"{label}@{width}: horizontal overflow"
    for target in page.evaluate(TARGETS):
        assert target["w"] >= 48 and target["h"] >= 48, f"{label}@{width}: small target {target}"
        if target["mic"]:
            assert target["w"] >= 88 and target["h"] >= 88, f"{label}@{width}: mic too small {target}"
    assert page.evaluate(FONT) >= 16
    assert page.evaluate(UNNAMED) == [], f"{label}@{width}: unlabeled buttons"
    page.screenshot(path=str(SCREENS / f"{label}-{width}.png"), full_page=True)


@pytest.mark.parametrize("width, height", VIEWPORTS, ids=[f"{w}x{h}" for w, h in VIEWPORTS])
def test_layout_fits_and_targets_are_thumb_sized(page, world, width, height):
    page.set_viewport_size({"width": width, "height": height})
    page.goto("/workshop")
    audit(page, "workshop-empty", width)

    world.extractor.mode = "long_label"
    world.prisma.script_intake(transcribe=INTAKE_T, verbatim=INCOMPLETE_V)
    speak(page, "#record", "#stop")
    expect(page.locator("#slip")).to_be_visible(timeout=15000)
    audit(page, "workshop-long-flagged", width)

    world.prisma.reset()
    world.extractor.mode = "complete"
    session = new_parcha(world.url)
    page.goto(f"/customer/{session['id']}")
    audit(page, "customer-call", width)

    world.prisma.say("हाँ ठीक है")
    reply_by_api(world.url, session)
    page.goto(f"/customer/{session['id']}")
    audit(page, "customer-sealed", width)
    page.goto(f"/verify/{session['id']}")
    audit(page, "verify", width)


def test_reduced_motion_turns_animation_off(page, world):
    page.emulate_media(reduced_motion="reduce")
    session = new_parcha(world.url)
    world.prisma.say("हाँ ठीक है")
    reply_by_api(world.url, session)
    page.goto(f"/customer/{session['id']}")
    duration = page.get_by_role("img", name="मंज़ूर — Approved").evaluate(
        "(n) => parseFloat(getComputedStyle(n).animationDuration)")
    assert duration < 0.01
```

- [ ] **Step 2: Run.** `.\.venv\Scripts\python.exe -m pytest -q -m e2e tests/e2e/test_responsive.py`. Expected: pass. If a target fails, fix the CSS (never the threshold) and rerun.
- [ ] **Step 3: Budget.** Run `(Get-ChildItem src\parcha\static\parcha.css, src\parcha\static\ui.js, src\parcha\static\app.js, src\parcha\static\icons.svg | Measure-Object Length -Sum).Sum`. Expected: ≤ 61440.
- [ ] **Step 4: Tabular digits.** Open `var/e2e/workshop-slip-360.png` and `customer-call-360.png` and check that the ₹ column digits line up. If they don't (R14 flags this as unverified for Google-served Mukta), self-host Mukta 400/600/800 `.woff2` from `google/fonts` (OFL) under `src/parcha/static/fonts/` with `@font-face` in `parcha.css`. Then drop the Google Fonts `<link>` for Mukta, add `"static/fonts/*.woff2"` to package data, and rerun Step 2.
- [ ] **Step 5: Webattack suite selectors (do not run it; it spends credits).** Run `Select-String -Path scripts\run_webattack_suite.py -Pattern "locator|query_selector|wait_for_selector|#"`. Point any selector on removed markup (table rows, `.panel`, the old banners) at the preserved ids.
- [ ] **Step 6: Docs.**
  - Copy `var/e2e/workshop-slip-360.png`, `workshop-flagged-360.png`, `customer-call-360.png`, `customer-sealed-360.png`, `verify-360.png` and `stage-sealed-1440.png` to `docs/ui/`. They are synthetic data only.
  - In `README.md`, replace the "Visual Interface Walkthrough" table's four `docs/webattack_artifacts/*.png` images with these, captioned in Hindi with English.
  - In `docs/demo.md`, record the shot list from `/stage` at 125% zoom: dictation → slip → read-back → "haan" → stamp on both phones.
- [ ] **Step 7: Full verification.** `.\.venv\Scripts\python.exe -m pytest -q` then `.\.venv\Scripts\python.exe -m pytest -q -m e2e tests/e2e`, then `git diff --check`. Expected: green, green, clean. Finally, click through `/stage` by hand once on a real Android phone over LAN (`uvicorn --host 0.0.0.0`). Copy uses the legacy fallback on plain-http origins, so check that "कॉपी हुआ" appears.
- [ ] **Step 8: Records and commit.** Record the implementation as AIDLC effort **011** (`ui-digital-parcha-build`, parent 010): `requirements-delta.md`, `construction.md` (commit list, screenshots), `effort-state.md`, `audit.md`, plus a registry row.
  `git add tests/e2e/test_responsive.py docs/ui README.md docs/demo.md scripts/run_webattack_suite.py aidlc-docs` then `git commit -m "test(ui): responsive and accessibility audit; docs walkthrough"`

---

## Self-Review (done while writing)

**Spec coverage.**

| Spec section / stories | Task |
|---|---|
| Mechanic recording (1–10) | 6: mic dock, timer, meter, processing, blocked mic, repeat 422, heard bubble |
| Mechanic review (11–22) | 1 and 4 (slip, serial, kind icons, quotes, en-IN), 5 (`describeField`, abstain reason, re-ask chip), 6 (flag counter, अधूरा, read-back gated). Unrelated rows preserved: money-path plan plus `test_flagged_amount_…` |
| Mechanic send and wait (23–30) | 6: share sheet, wa.me, disclosure, polling, stamp + chime + vibrate, changes-asked, resume via `session_id` |
| Owner hearing (31–36) | 7: call card, play, caption, bilingual disclosure, wait-and-update, audio failure |
| Owner consent and answer (37–47) | 7: unticked consent → `/consent`, gated mic, hints not buttons, retry/ask_field copy, strike-through diff, fresh read-back, fallback buttons, 409 reload |
| Owner sealed (48–53) | 7: receipt, own words, stamp, PDF, clipboard copy, verify link |
| Verifier (54–56) | 4: status-dependent verdict, voice-note bubbles, folded evidence, `--danger` fixed |
| Demo and quality (57–65) | 8 (stage), 9 (360–1440 audit, reduced motion, names, budget), 5 and 6 (text-only DOM, hostile label) |
| API contract | 2 (payload fields, strict JSON), 8 (`/stage`) |
| Dependency on the money path | 0 (gate), 3 (mode-keyed fakes), 5 (strings moved verbatim), 6 (422 repeat, abstain labels on rows) |

**Step scan.** Every code step names its file and gives the code or exact edit. The one judgement step is Task 9 Step 4 (font fallback), and its trigger and action are both stated.

**Type consistency.**
- `stageFor` values `bolo|parcha|sunao|haan|manzoor` are used the same way in the stepper markup, `renderStepper` and `renderSession`.
- The ids emitted by `renderSlip` match the `_slip.html` ids (`slip`, `parcha-no`, `items-tbody`, `total-cell`, `delivery-info`).
- `recordOnce(start, stop, hooks)` has the same signature in Tasks 6 and 7.
- `StagePrisma.say` / `script_intake` / `reset` are used in Tasks 6–9 exactly as defined in Task 3.
- `new_parcha` / `reply_by_api` / `speak` have the same signatures everywhere.

**Review Focus.** All five items have tests in their owning tasks: 6, 6, 7, 7, 9.

**Proportion.** The owner asked for the build code in the plan, so the CSS, templates and JS are given in full. Beyond what the tests pin, implementers choose only the internal variable names.
