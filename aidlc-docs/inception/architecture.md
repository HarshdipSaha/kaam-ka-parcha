# AI-DLC Inception: System Architecture (Reconciled)

**Project:** Kaam ka Parcha (Phone-Sealed)  
**Status:** Inception Baseline — Reconciled & Locked  
**Baseline Date:** 2026-10-04 (Reconciled 2026-10-05)  

---

## 1. System Overview

```mermaid
flowchart TD
    subgraph Client["Client Tier (FastAPI Web App)"]
        UI["Workshop Intake UI (/workshop)"]
        CustomerUI["Customer Review UI (/customer/{id})"]
        ArtefactView["Confirmed Parcha PDF (/parcha.pdf)<br/>WhatsApp Text (/whatsapp.txt)"]
    end

    subgraph Leg1Pipeline["Leg 1 Engine: Workshop Speech & Structuring"]
        AudioIn["Raw Workshop Audio (Opus/WebM/WAV)"] --> Normalizer["normalize_upload()<br/>(FFmpeg 16 kHz Mono PCM)"]
        Normalizer --> Prisma1["PrismaClient (REST hi-IN)<br/>Pass 1: format=transcribe (ITN)"]
        Normalizer --> Prisma2["PrismaClient (REST hi-IN)<br/>Pass 2: format=verbatim (bias_list)"]
        Prisma1 & Prisma2 --> Extractor["Extractor (Groq / OpenAI API)<br/>Key Rotation on HTTP 429"]
        Extractor --> JobCardSchema["Strict JobCard (Pydantic v2)<br/>Paise Amounts & Computed Total"]
        JobCardSchema --> SessionState["SessionStore (In-Memory RLock)<br/>draft -> review -> awaiting_reply"]
    end

    subgraph Leg2Pipeline["Leg 2 Engine: Telephony Simulation & Sealing"]
        SessionState --> TimbreSynthesizer["TimbreClient (REST hi-IN)<br/>Nalini, 8 kHz mu-law PCM"]
        TimbreSynthesizer --> AudioEngine["audio.py Transcode Pipeline<br/>mulaw_to_wav + mix_at_snr + codec_round_trip"]
        AudioEngine --> DegradedWAV["Degraded Telephony Audio<br/>(G.711 / AMR-NB 4.75k + 5dB Noise)"]
        DegradedWAV --> CustomerPlayer["Customer Audio Player"]
        CustomerReply["Customer Voice Reply<br/>('Haan theek hai' / 'Nahi badlo')"] --> ReplyNormalizer["normalize_upload(8 kHz)"]
        ReplyNormalizer --> TelephonyASR["PrismaClient Telephony STT (8 kHz)"]
        TelephonyASR --> Classifier["classify_reply()<br/>(Conservative Acceptance vs Negation)"]
        Classifier --> ConfirmationSeal["SessionStore.confirm()<br/>Status: confirmed (Immutable)"]
        Classifier --> DeltaUpdater["Workflow.reply() Targeted Delta Update<br/>Status: review (Needs New Read-Back)"]
    end

    subgraph Storage["Sealed Artefacts Engine"]
        ConfirmationSeal --> PDFGen["render_pdf() (ReportLab Canvas)<br/>attach_transcripts() (pypdf)"]
        PDFGen --> SealedPDF["Sealed Parcha PDF + transcripts.json"]
        ConfirmationSeal --> TextGen["whatsapp_text() Plain Text"]
    end

    subgraph Lab["Line Noise Lab (parcha.lab)"]
        Manifest["100-Utterance SynthCall-IN Manifest"] --> LabRunner["runner.py (Budgeted Grid Sweep)"]
        LabRunner --> Metrics["metrics.py (CER, Amount Match, Drop, Hallucination)"]
        Metrics --> Reports["report.py (Private Summary & Guarded Public Delta)"]
        Manifest --> WSFlushProbe["ws_flush_probe.py (8 kHz WS Flush Probe)"]
    end
```

---

## 2. Technology Stack & API Choices

| Layer | Technology | Justification |
|---|---|---|
| **Speech-to-Text (STT)** | **Gnani Prisma v2.5** (`api.vachana.ai/stt/v3`) | Native Indic ITN for currency/dates; 8 kHz telephony optimization; `bias_list` vocabulary boosting. |
| **Streaming Telephony STT** | **Gnani WebSocket STT** (`api.vachana.ai/stt/v3/stream`) | Realtime streaming evaluation with telephony VAD headers and 500 ms zero-padding silence tail. |
| **Text-to-Speech (TTS)** | **Gnani Timbre v2.5** (`api.vachana.ai/api/v1/tts/inference`) | High-fidelity Indic voices (Nalini), native 8 kHz $\mu$-law output matching cellular channels. |
| **LLM Extractor** | **Groq OpenAI-Compatible API** (`llama-3.3-70b-versatile`) | Fast, structured JSON extraction with multi-key pool rotation on HTTP 429. |
| **Audio Processing** | **FFmpeg 9.0 (Subprocess Pipes) + NumPy** | Codec transcoding (AMR-NB 4.75 kbps via `libopencore_amrnb`, G.711 via `pcm_mulaw`), calibrated SNR mixing, and frame erasure. |
| **Backend & Routing** | **Python 3.12 / FastAPI / Uvicorn** | High-performance asynchronous HTTP routing, dependency injection (`AppServices`), Jinja2 templating, and static asset delivery. |
| **Validation & State** | **Pydantic v2 + Threading RLock** | Strict frozen data models (`extra="forbid"`) and thread-safe revisioned optimistic session store. |
| **Document Generation** | **ReportLab 4.0 + PyPDF 4.0** | Produces customer-facing tamper-evident PDF with cryptographically embedded `transcripts.json` audit trail. |
| **Evaluation Spine** | **Custom Levenshtein Dynamic Program + NumPy** | Character Error Rate (CER), numeric amount match, short-reply drop, and non-speech hallucination counting. |

---

## 3. Data Flow & Security
* **Secrets Management:** `API_KEY` and `GROQ_API_KEY` are read from `.env` and kept out of version control. Dataclass fields use `field(repr=False)` to prevent secret leakage in logs.
* **Synthetic PII:** All customer phone numbers, names, and vehicle registration plates are synthetically generated.
* **Storage Isolation:** Session audio and generated artifacts are stored under ignored `var/` or in-memory, never committed.
* **Offline Testing:** 100% of the unit test suite runs offline with mock transports and in-memory audio fixtures, consuming 0 Gnani credits.
