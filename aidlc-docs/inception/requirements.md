# AI-DLC Inception: Requirements Baseline (Reconciled)

**Project:** Kaam ka Parcha (Phone-Sealed)  
**Status:** Inception Baseline — Reconciled & Locked  
**Baseline Date:** 2026-10-04 (Reconciled 2026-10-05)  
**Contest:** Gnani AI Great Indian AI Challenge (Oct 1 – Nov 10, 2026)  

---

## 1. Project Mission & Objectives
Build a dual-leg voice AI workflow for Indian two-wheeler and automotive repair workshops:
1. **Primary Goal:** Win the ₹1L/month 6-month internship offer (~₹6L value) by demonstrating senior-level architectural rigor and deep mastery of Gnani AI APIs.
2. **Secondary Goal:** Secure the **Noise Canceller** (₹50k) and/or **Mixed Vibes** (₹50k) award.
3. **Tertiary Goal:** Achieve top-tier organic engagement on LinkedIn and X through an authentic, $\le$60-second video demo.

---

## 2. Functional Requirements (FR)

### Leg 1: Workshop Intake & Extraction
* **FR-1.1 (Voice Dictation over Engine Noise):** System accepts Hinglish spoken audio (recorded near running engines, 65–75 dB ambient). Supports web browser recording via `MediaRecorder` with Opus/WebM/MP4 support.
* **FR-1.2 (Dual-Pass STT):**
  * Pass A (`format=transcribe`): Inverse Text Normalization (ITN) converts spoken numbers/dates (*"saade chaar sau"*, *"Somvaar"*) into numeric structures (`₹450`, `Monday`).
  * Pass B (`format=verbatim` + `bias_list`): Boosts exact automotive part and fluid vocabulary (*clutch plate, brake shoe, mobil oil*, max 100 single words).
* **FR-1.3 (Deterministic Entity Extraction):** Extracts structured schema where money is strictly stored in non-negative integer paise. Total is computed and never accepted as user/LLM input.
* **FR-1.4 (Evidence Scoring & Verification):** Normalizes transcripts with Unicode NFKC. Requires verbatim text quote in transcripts for every line item label, amount, and delivery. Evidence score must be $\ge 0.8$; otherwise flagged for human review.
* **FR-1.5 (Targeted Voice Re-Ask):** Workshop UI supports re-recording single unverified fields without wiping the draft card.

### Leg 2: Telephony Customer Authorization Loop
* **FR-2.1 (Indic Telephony Speech Synthesis):** Gnani Timbre v2.5 generates 8 kHz $\mu$-law audio reading the exact bill breakdown in natural Hindi (`hi-IN`, `timbre-v2.5`, Nalini voice).
* **FR-2.2 (Acoustic Telephony Simulation):** Audio is routed through an FFmpeg pipeline simulating G.711 / AMR-NB 4.75 kbps codec compression and line noise (5 dB SNR) with transparent on-screen disclosure.
* **FR-2.3 (Robust Phrasal Confirmation):** Timbre explicitly prompts for a phrasal confirmation (*"ठीक है? हाँ कहें, या सुधार बताएं।"*). Conservative classifier gives negation (`nahi`) priority over acceptance (`haan`).
* **FR-2.4 (Telephonic ASR Response & Revision Seal):** Customer reply is transcribed. If confirmed, seals the exact revision heard. If contested, executes a targeted delta update on the single contested field, invalidating old read-backs and triggering a new revision read-back.

### Artefact: The Confirmed Parcha
* **FR-3.1 (Digital Sealed Agreement PDF):** Generates a tamper-evident ReportLab PDF containing:
  * Fixed synthetic workshop details & vehicle registration.
  * Itemized parts, labour, and computed rupee total.
  * Promised delivery date, window, and spoken date.
  * Simulation line notice (no PSTN call placed).
  * Cryptographic embedded `transcripts.json` stream containing the full audit trail (mechanic, system read-back, customer reply).
* **FR-3.2 (WhatsApp-Ready Plain Text):** Formatted summary pre-rendered for instant one-click clipboard copying. No automated carrier messaging or false transmission claims.

---

## 3. Non-Functional & Competition Requirements (NFR)
* **NFR-1 (Credit Budgeting & Capping):** Full testing and development must not exceed the 5,000 Gnani credit balance. Bounded feasibility gates, probes, and sweeps enforce a strict 2,000 credit cap. Unit tests run 100% offline with zero credit spend.
* **NFR-2 (Zero-Leak & EULA Compliance):** Never publish comparative third-party benchmark tables (Prisma vs. Whisper/Google). Only publish internal pipeline deltas (Denoise On vs. Off, `bias_list` gain, SNR vs. CER) after written organizer permission. Secret keys are excluded from `repr()`, logs, and web responses.
* **NFR-3 (Synthetic Data Rule):** All customer phone numbers, vehicle registrations, and names must be synthetic.
* **NFR-4 (Simulated Call Disclosure):** On-screen badge during customer leg: *"Simulated phone line: audio passed through G.711 / AMR-NB 4.75 kbps + street noise at 5 dB. No call was placed. All names and amounts are synthetic."*
* **NFR-5 (Response Latency):** Sub-second local processing for state transitions; bounded timeouts (30s) on all audio and speech operations.
