# Effort 001: Construction Log

**Effort ID:** 001  
**Reference:** core-system  
**Scope:** Tasks 1–19 Implementation & Test Construction  

---

## 1. Unit Construction Log

### Unit 1: Package, Configuration & Offline Health Route (Task 1)
* **Files:** `pyproject.toml`, `.gitignore`, `.env.example`, `src/parcha/__init__.py`, `src/parcha/config.py`, `src/parcha/app.py`, `tests/test_config.py`.
* **Commits:** `09763aa`, `405b85e`.
* **Testing:** 7 unit tests verifying offline `/health`, fallback environment resolution, credential validation, and secret masking in `__repr__`.

### Unit 2: Gnani Prisma & Timbre REST Clients (Task 2)
* **Files:** `src/parcha/gnani.py`, `tests/test_gnani.py`.
* **Commit:** `de14791`.
* **Testing:** 4 unit tests verifying multipart form parameters (`format=transcribe`, `format=verbatim`), bias list limits ($\le 100$ single words), 8 kHz $\mu$-law audio synthesis, and key redaction from exception traces.

### Unit 3: Credit Calculator & Single-Call Probe (Task 3)
* **Files:** `src/parcha/credits.py`, `scripts/probe_api.py`, `tests/test_credits.py`, `docs/gates.md`.
* **Commit:** `6983a59`.
* **Testing:** 7 unit tests verifying exact credit forecasting, budget cap guard (`BudgetExceeded`), duration validation ($4.0\text{s} \le t \le 8.0\text{s}$), and CLI dry-run execution.

### Unit 4: Telephony Audio Conversion & Codec Chain (Task 4)
* **Files:** `src/parcha/audio.py`, `tests/test_audio.py`, `assets/README.md`.
* **Commit:** `8a196d2`.
* **Testing:** 10 unit tests verifying FFmpeg pipe execution, 8 kHz $\mu$-law decoding, G.711 / AMR-NB 4.75k round-trip, SNR noise mixing, and waveform clipping prevention.

### Unit 5: Feasibility Gate Runner & Telephony WebSocket Client (Task 5)
* **Files:** `src/parcha/gnani_ws.py`, `scripts/early_gates.py`, `tests/test_early_gates.py`, `docs/gates.md`.
* **Commit:** `7662e95`.
* **Testing:** 12 unit tests verifying telephony VAD headers, 1024-byte frame chunking, 500ms silence padding, WebSocket client mocking, and CLI execution.

### Unit 6: Validated Job Card Schema (Task 6)
* **Files:** `src/parcha/schema.py`, `tests/test_schema.py`.
* **Commit:** `76e599d`.
* **Testing:** 8 unit tests verifying Pydantic v2 strict models, non-negative integer paise validation, computed total derivation, evidence scoring rules, and duplicate ID rejection.

### Unit 7: Revisioned In-Memory Session Store (Task 7)
* **Files:** `src/parcha/session.py`, `tests/test_session.py`, `tests/__init__.py`.
* **Commit:** `d4113ae`.
* **Testing:** 4 unit tests verifying thread-safe `RLock` isolation, stale read-back rejection, review-needed prevention, and confirmation sealing immutability.

### Unit 8: Spoken Field Extraction with Key Rotation (Task 8)
* **Files:** `src/parcha/extract.py`, `tests/test_extract.py`.
* **Commit:** `01004dc`.
* **Testing:** 14 unit tests verifying LLM chat completions, Groq key rotation on HTTP 429, Unicode NFKC quote matching, Asia/Kolkata weekday resolution, and targeted single-item delta extraction.

### Unit 9: Workshop Speech Intake & Voice Re-Ask (Task 9)
* **Files:** `src/parcha/workflow.py`, `src/parcha/audio.py`, `src/parcha/session.py`, `tests/test_workflow.py`.
* **Commit:** `3078e96`.
* **Testing:** 6 unit tests verifying dual-pass intake orchestration, MIME parameter stripping, audio duration bounds ($0.3\text{s} \le t \le 60\text{s}$), and targeted voice re-asking.

### Unit 10: Workshop HTTP API & Recording UI (Task 10)
* **Files:** `src/parcha/app.py`, `src/parcha/templates/workshop.html`, `src/parcha/static/app.js`, `tests/conftest.py`, `tests/test_app.py`.
* **Commit:** `736a274`.
* **Testing:** 6 integration tests verifying `/workshop` HTML, `AppServices` dependency injection, session creation, audio upload intake, and error code mapping (404, 409, 422, 502, 503).

### Unit 11: Telephony Read-Back Generation (Task 11)
* **Files:** `src/parcha/workflow.py`, `src/parcha/app.py`, `tests/test_readback.py`.
* **Commit:** `82f89e0`.
* **Testing:** 6 unit tests verifying Hindi read-back prompt generation, rupee formatting, telephony line degradation, and WAV serving endpoints.

### Unit 12: Customer Reply Classification & Confirmation Seal (Task 12)
* **Files:** `src/parcha/workflow.py`, `tests/test_reply.py`.
* **Commit:** `52399f7`.
* **Testing:** 10 unit tests verifying conservative reply classification (negation priority, `theek hai` acceptance), targeted correction handling, and revision seal invariants.

### Unit 13: Customer Review WebApp (Task 13)
* **Files:** `src/parcha/templates/customer.html`, `src/parcha/app.py`, `src/parcha/static/app.js`, `tests/test_app.py`.
* **Commit:** `5439617`.
* **Testing:** 5 integration tests verifying `/customer/{id}` UI, simulation notice banner, audio playback controls, reply submission, and zero key leakage in responses.

### Unit 14: Confirmed PDF & WhatsApp Artefacts (Task 14)
* **Files:** `src/parcha/artefact.py`, `src/parcha/app.py`, `tests/test_artefact.py`.
* **Commit:** `4fe0340`.
* **Testing:** 5 unit tests verifying ReportLab PDF generation, embedded `transcripts.json` stream extraction via `pypdf`, plain text WhatsApp summary formatting, and 409 unconfirmed access guards.

### Unit 15: SynthCall-IN Manifest & Dataset (Task 15)
* **Files:** `src/parcha/lab/dataset.py`, `data/synthcall_manifest.jsonl`, `scripts/make_synthcall.py`, `tests/test_dataset.py`, `.gitignore`.
* **Commit:** `8e083e2`.
* **Testing:** 8 unit tests verifying deterministic 100-prompt generation, duplicate ID rejection, path traversal prevention, and TTS CLI dry-run execution.

### Unit 16: Line Noise Lab Metrics & Budgeted Runner (Task 16)
* **Files:** `src/parcha/audio.py`, `src/parcha/lab/metrics.py`, `src/parcha/lab/runner.py`, `tests/test_lab_metrics.py`, `tests/test_lab_runner.py`.
* **Commit:** `ce0da67`.
* **Testing:** 8 unit tests verifying CER Levenshtein dynamic program, amount extraction, 20ms frame erasure, cached degradation, and pre-call budget enforcement.

### Unit 17: Private Lab Reports & Guarded Public Delta Export (Task 17)
* **Files:** `src/parcha/lab/report.py`, `tests/test_lab_report.py`, `docs/gates.md`.
* **Commit:** `e465896`.
* **Testing:** 6 unit tests verifying private metric aggregation, fail-closed consent enforcement, competitor benchmark suppression, and paired delta calculations.

### Unit 18: 8 kHz WebSocket Telephony Flush Probe (Task 18)
* **Files:** `scripts/ws_flush_probe.py`, `tests/test_ws_frames.py`, `docs/gates.md`.
* **Commit:** `3c46b55`.
* **Testing:** 13 unit tests verifying 1024-byte packetization, 8-frame (512 ms) zero-padding silence tail, affirmative recovery detection, and CLI dry-run execution.

### Unit 19: Rehearsal Run Sheet & Project Documentation (Task 19)
* **Files:** `README.md`, `docs/gates.md`, `docs/demo.md`.
* **Commit:** `a5ca37e`.
* **Testing:** Verified complete test suite passing (139/139), zero whitespace diff errors, and clean git status.
