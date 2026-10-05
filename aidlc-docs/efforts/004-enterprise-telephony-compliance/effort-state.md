# Effort 004: Enterprise Telephony Robustness & DPDP Compliance Pipeline

## Metadata
- **Effort ID:** `004`
- **Reference:** `enterprise-telephony-compliance`
- **Title:** Enterprise Voice-Sealed Service Agreement & Telephony Robustness Pipeline
- **Status:** active
- **Started:** 2026-10-05
- **Completed:** Pending
- **Related Issues:** #1 (Epic), #3 (Phrasal VAD), #4 (Digital Fallback), #5 (Verification QR & Endpoint), #6 (DPDP Act Consent), #7 (Transient Impulse Noise Lab)

## Scope & Deliverables
1. **Issue #3**: `readback.py` phrasal prompt synthesis engine ("Agar aapko yeh manzoor hai, toh boliye: 'Haan, theek hai'. Koi badlaav chahiye toh rate batayein."), Indic currency/date normalization, expanded phrasal affirmation classifier.
2. **Issue #4**: Confidence-gated multi-channel digital fallback router (`score < 0.65` or retry exhaustion), `/sessions/{id}/fallback` endpoint, interactive one-tap confirmation payload.
3. **Issue #5**: Scannable verification QR code rendered on sealed PDF linking to `/verify/{session_id}` route with interactive audio playback and SHA-256 digest integrity verification.
4. **Issue #6**: DPDP Act 2023 statutory consent banner and voice consent prompt, cryptographic consent timestamp and audit log recorded in session metadata and canonical transcript manifest.
5. **Issue #7**: Transient impulse noise generator (pneumatic wrench, spanner drop) and idle engine rumble hallucination evaluation suite in `parcha.lab`.
6. **Issue #1**: Epic closure, full documentation sync, and end-to-end multi-viewport Playwright verification.

## Progress & Status
- [x] **Issue #3**: `feat(telephony): Phrasal Telephony Prompting & VAD Stabilization Engine`
  - Created [`src/parcha/readback.py`](../../src/parcha/readback.py) with `PHRASAL_AFFIRMATION_PROMPT`, `format_rupees`, `make_readback`, and `classify_reply`.
  - Re-exported symbols in [`src/parcha/workflow.py`](../../src/parcha/workflow.py) for backward compatibility.
  - Implemented phrasal affirmation prompt: *"Agar aapko yeh manzoor hai, toh boliye: 'Haan, theek hai'. Koi badlaav chahiye toh rate batayein."*
  - Preserved Indic currency numeral pre-normalization and date formatting within new phrasal templates.
  - Upgraded reply classifier to accept both 3-word phrasal affirmations (with honorifics, Devanagari, and manzoor forms) and legacy monosyllabic affirmations.
  - Added unit tests in [`tests/test_readback.py`](../../tests/test_readback.py) and [`tests/test_reply.py`](../../tests/test_reply.py).
  - Verification: 171/171 offline tests passing, `python -m compileall -q src tests scripts` passing with 0 errors.

## Next Phase: Issue #4 Implementation
- Issue #4: `feat(telephony): Confidence-Gated Multi-Channel Digital Fallback`

