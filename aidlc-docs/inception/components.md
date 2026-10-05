# AI-DLC Inception: Component Breakdown (Reconciled)

**Project:** Kaam ka Parcha (Phone-Sealed)  
**Status:** Inception Baseline — Reconciled & Locked  
**Baseline Date:** 2026-10-04 (Reconciled 2026-10-05)  

---

## Component Units

```
kaam-ka-parcha/
├── src/parcha/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Settings dataclass, env loading, credential gates, secret repr masking
│   ├── gnani.py             # PrismaClient (REST dual-pass) & TimbreClient (8k mu-law) HTTP boundaries
│   ├── gnani_ws.py          # Telephony streaming WebSocket client, 1024-byte framing, 500ms silence tail
│   ├── credits.py           # CreditPlan arithmetic, budget capping, gate scoring formulas
│   ├── audio.py             # FFmpeg wrapper, mulaw_to_wav, codec_round_trip, mix_at_snr, normalize_upload, erase_frames
│   ├── schema.py            # StrictModel, LineItem, Delivery, Evidence, JobCard, TranscriptLog, review_fields
│   ├── session.py           # Session dataclass, SessionStore with RLock, optimistic revisions, seal invariants
│   ├── extract.py           # Extractor with Groq multi-key rotation, quote verification, weekday resolution
│   ├── workflow.py          # Workflow orchestrator (intake, reask, start_readback, classify_reply, reply)
│   ├── artefact.py          # render_pdf with ReportLab, attach_transcripts with pypdf, whatsapp_text formatter
│   ├── app.py               # FastAPI app factory, AppServices dependency injection, REST & HTML routes
│   │
│   ├── templates/           # Jinja2 frontend views
│   │   ├── workshop.html    # Workshop bay recording and card review interface
│   │   └── customer.html    # Customer telephony playback, review, and reply interface
│   │
│   ├── static/
│   │   └── app.js           # MediaRecorder client audio capture, state rendering, API event wiring
│   │
│   └── lab/                 # Line Noise Lab evaluation harness
│       ├── __init__.py      # Exports for lab module
│       ├── dataset.py       # Clip model, PART_WORDS, AMOUNTS, make_prompts, load_manifest, save_manifest
│       ├── metrics.py       # CER Levenshtein dynamic program, amount_match, short_reply_drop, hallucinated_words
│       ├── runner.py        # Budgeted line noise grid runner, degradation cache, checkpointing, CLI
│       └── report.py        # Private summary generator and fail-closed guarded public delta exporter
│
├── data/
│   └── synthcall_manifest.jsonl  # 100-utterance locked synthetic test manifest
│
├── scripts/
│   ├── probe_api.py         # Calibrated single-call STT and TTS probe CLI
│   ├── early_gates.py       # Early feasibility gate runner CLI (garage, tts, replies, bias)
│   ├── make_synthcall.py    # TTS audio generation CLI
│   └── ws_flush_probe.py    # 8 kHz WebSocket telephony flush probe CLI
│
└── tests/                   # 139 unit and integration tests (100% offline, zero credit burn)
    ├── conftest.py          # Reusable AppServices, mock workflow, and TestClient fixtures
    ├── test_config.py       # Settings, environment, and secret masking tests
    ├── test_gnani.py        # Prisma and Timbre REST boundary tests
    ├── test_credits.py      # Credit arithmetic, budget caps, and probe CLI tests
    ├── test_audio.py        # Codecs, mulaw decode, SNR mixing, and audio normalizer tests
    ├── test_early_gates.py  # Gate metrics, telephony headers, and dry-run CLI tests
    ├── test_schema.py       # Pydantic v2 validation, paise totals, and evidence tests
    ├── test_session.py      # Session store, revision markers, and concurrency conflict tests
    ├── test_extract.py      # Extractor, quote validation, Groq key rotation, and correction tests
    ├── test_workflow.py     # Dual-pass intake, audio normalizer, and re-ask tests
    ├── test_app.py          # Workshop & customer routes, error mapping, and secret leak tests
    ├── test_readback.py     # Readback generation, rupee formatting, and audio serving tests
    ├── test_reply.py        # Hinglish reply classification, targeted correction, and seal tests
    ├── test_artefact.py     # PDF generation, embedded transcripts.json, and WhatsApp tests
    ├── test_dataset.py      # Manifest stability, validation, and dry-run tests
    ├── test_lab_metrics.py  # CER, amount match, reply drop, and hallucination tests
    ├── test_lab_runner.py   # Frame erasure, budget limit, and runner tests
    ├── test_lab_report.py   # Private summary, fail-closed consent, and competitor ban tests
    └── test_ws_frames.py    # 1024-byte framing, silence padding, and WS probe tests
```

---

## Component Responsibilities & Boundaries

### 1. `parcha.gnani` & `parcha.gnani_ws` (Speech API Boundaries)
* **Responsibility:** Typed interface to Gnani REST STT, REST TTS, and WebSocket Streaming STT.
* **Guarantees:** Redacts API keys from all exceptions and `__repr__`. Validates single-word bias rules. 

### 2. `parcha.audio` (Acoustic Processing Engine)
* **Responsibility:** DSP, sample rate conversion, G.711 / AMR-NB codec simulation, calibrated noise mixing, and packet loss simulation.
* **Guarantees:** Pure subprocess arguments (immune to shell injection), strict bounds checking on audio duration ($0.3\text{s} \le t \le 60\text{s}$) and file sizes ($\le 8\text{MB}$).

### 3. `parcha.schema` & `parcha.session` (Domain State Machine)
* **Responsibility:** Pure domain models and thread-safe revisioned optimistic session store.
* **Guarantees:** Money is strictly non-negative integer paise. Computed totals cannot be set externally. `confirm()` strictly requires that the customer confirmed the exact read-back revision last heard. Confirmed sessions are immutable.

### 4. `parcha.extract` & `parcha.workflow` (Intelligence & Orchestration)
* **Responsibility:** LLM extraction with Groq key rotation on HTTP 429, quote verification, and end-to-end workflow orchestration.
* **Guarantees:** Unquoted facts receive zero score and trigger review. Targeted corrections update only the specified item without modifying unaffected fields. Conservative classifier prioritizes negation over acceptance.

### 5. `parcha.artefact` (Sealed Agreement Generator)
* **Responsibility:** Produces tamper-evident PDF agreement and plain-text WhatsApp summary from confirmed session snapshots.
* **Guarantees:** Embeds `transcripts.json` audit trail inside the PDF container. WhatsApp output contains clear simulation disclosures and strictly forbids false transmission claims.

### 6. `parcha.lab` (Line Noise Lab)
* **Responsibility:** Automated evaluation harness measuring CER, amount match, short reply drop, and hallucinated words across codecs and SNRs.
* **Guarantees:** Fails closed without recorded organizer consent. Strictly forbids competitor benchmark comparisons or raw absolute rankings.
