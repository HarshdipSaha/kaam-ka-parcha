# Effort 002: Construction Log

**Effort ID:** 002  
**Reference:** webattack-realworld-validation  
**Scope:** WebAttack Local Surface Probing, Real-World Voice Data Acquisition & Playwright End-to-End Test Suite  
**Date:** 2026-10-05  

---

## 1. Real-World Voice & Acoustic Sample Acquisition
* **Source:** OpenSLR, Wikimedia Commons & Lingua Libre.
* **Downloaded & Standardized Artifacts:**
  - `data/real_world_samples/car_engine_idle_16k.wav` (Real car engine rumble & idling sound from Volvo 850 T5).
  - `data/real_world_samples/engine_rev_16k.wav` (Real vehicle engine revving sound).
  - `data/real_world_samples/hi_hindi_16k.wav` (Native Hindi speaker voice).
  - `data/real_world_samples/hi_bharat_16k.wav` (Native Hindi speaker voice).
  - `data/real_world_samples/hi_ank_16k.wav` (Native Hindi speaker pronouncing numeric token).
  - `data/real_world_samples/mechanic_in_garage_noise.wav` (Synthesized mechanic spoken phrase mixed with authentic Volvo 850 T5 engine rumble via FFmpeg `amix` at 78 dB ambient).
  - `data/real_world_samples/customer_affirmation_phrase.wav` (Spoken customer reply "हाँ ठीक है").
  - `data/real_world_samples/real_world_manifest.json` (Structured catalog of 3 authentic workshop repair dispute cases and resolution workflows).

---

## 2. Server Enhancements
* **Root Navigation:** Added `@app.get("/")` route redirecting to `/workshop` for instant browser usability.
* **Extractor Hardening:** Configured `openai/gpt-oss-120b` (Groq) with enhanced `CARD_SYSTEM_PROMPT` and robust delivery window normalization (`morning`, `afternoon`, `evening`).

---

## 3. WebAttack Probing & Verification Suite
* **Crawler & Surface Mapping:** Scans all application routes (`/`, `/workshop`, `/health`, `/customer/{id}`), forms, and action buttons.
* **Responsive Layout Audit:** Evaluates Desktop 1080p, Desktop 1440w, Tablet 768w, and Mobile iPhone 14 (390w) viewports for horizontal overflow bugs (`scrollWidth > clientWidth`).
* **Playwright Interactive Driving:**
  - Simulates mechanic intake with authentic engine-noise audio.
  - Tests parsed job card rendering on `/workshop`.
  - Generates telephony readback with Gnani Timbre.
  - Drives customer review page on `/customer/{session_id}`.
  - Submits customer affirmative response and seals the card.
  - Validates tamper-evident ReportLab PDF download with embedded `transcripts.json`.
  - Validates WhatsApp plain-text export.
* **Security & Negative Test Suite:**
  - 404 verification for unknown sessions.
  - 409 conflict protection on unconfirmed PDF downloads.
  - Path traversal injection protection on session IDs and file routes.
  - 422 input validation on empty audio streams.
  - 409 stale revision reply rejection.
