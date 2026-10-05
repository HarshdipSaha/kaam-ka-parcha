# Requirements Delta: Effort 002 — WebAttack & Real-World Validation

**Effort ID:** 002  
**Reference:** webattack-realworld-validation  
**Date:** 2026-10-05  
**Baseline:** `aidlc-docs/inception/requirements.md`  

---

## 1. Context & Motivation
Effort 001 delivered the core Python pipeline, API endpoints, mock-based offline unit tests, and architecture.
To establish production-grade readiness and validate against real-world voice acoustic conditions:
1. The local web service must be actively driven on `localhost:8000`.
2. A comprehensive surface attack probe (`/webattack`) must be executed against all reachable endpoints, forms, buttons, and state mutations.
3. Authentic real-world voice/acoustic recordings (Indian workshop noise, two-wheeler/four-wheeler engine sounds, Hinglish vehicle repair dialogues) must be discovered, fetched, and cataloged.
4. Playwright test automation must execute full dual-leg interactive journeys (Mechanic intake -> Customer review -> Delta update -> PDF/WhatsApp confirmation) under multiple viewports, verifying zero layout overflows and clean console error logs.
5. All activities must be logged per the AI-DLC guidelines.

---

## 2. Requirements Delta

### NEW Functional Requirements
- **FR-002.1 (Live Local Service Lifecyle):** Automate cold-start polling, port binding, and clean teardown of Uvicorn service for testing.
- **FR-002.2 (WebAttack Surface Crawler):** Deep crawler mapping all GET routes, form submissions, action buttons, API queries, and network payloads on `localhost:8000`.
- **FR-002.3 (Real-World Speech & Acoustic Corpus):** Acquire open-source real Indian speech audio, ambient garage/engine recordings, and real-world mechanic repair conversation transcripts/cases.
- **FR-002.4 (Playwright Interactive E2E Flow):** Simulate live mechanic input (audio upload & form inputs), verify extraction, navigate to customer review page, verify playback UI, execute targeted correction, and verify the sealed state and PDF download.
- **FR-002.5 (Dual-Viewport Responsive & Overflow Audit):** Inspect 1920x1080 (Desktop), 1440x900 (Laptop), 768x1024 (Tablet), and 390x844 (Mobile iPhone) with DOM overflow evaluation (`scrollWidth > clientWidth`).

### NEW Non-Functional Requirements
- **NFR-002.1 (Zero Regressions):** Probing and end-to-end tests must pass without throwing 500 Internal Server Errors or silent UI unresponsiveness.
- **NFR-002.2 (Zero Credit Leak During Playwright Automated Runs):** Use mock or synthetic test session payloads for automated browser regression testing unless explicitly gated.
- **NFR-002.3 (AI-DLC Traceability):** Persist crawl logs, Playwright screenshots, test reports, and audit trail in `aidlc-docs/efforts/002-webattack-realworld-validation/`.
