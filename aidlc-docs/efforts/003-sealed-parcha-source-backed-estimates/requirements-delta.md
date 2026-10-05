# Requirements Delta: Effort 003 — Sealed Parcha Source-Backed Estimates

**Effort ID:** 003  
**Reference:** sealed-parcha-source-backed-estimates  
**Date:** 2026-10-05  
**Baseline:** `aidlc-docs/inception/requirements.md`  
**GitHub Issues:** #8, #9, #2  

---

## 1. Context & Motivation

Code review and live Hinglish testing uncovered several critical edge cases in extraction and evidence sealing:
1. Pydantic's default type coercion allows JSON booleans (`true` -> `1`, `false` -> `0`), strings (`"750"` -> `750`), and decimals into `LineItem.amount_paise`, risking silent invoice corruption.
2. Exact label normalization fails to catch semantic duplicates such as `front brake pad` and `brake-pad` or word-order variants, which can double-charge customers.
3. The PDF visible text and embedded `transcripts.json` independently compute manifest digests, creating a risk of SHA-256 divergence.
4. Default telephony noise path was relative to shell CWD, failing when executed from arbitrary subdirectories or when installed.
5. Claims of robustness over noisy Hinglish dictation must be grounded in an 8-category evaluation corpus with separate development and holdout/challenge splits and rigorous metric reporting.

---

## 2. Requirements Delta

### NEW Functional Requirements
- **FR-003.1 (Strict Monetary Integer Validation):** `LineItem.amount_paise` must accept ONLY `None` or an exact JSON integer (rejecting `bool`, `str`, `float`, and negative numbers). Both `Extractor.extract_card` and `Extractor.extract_field` must raise `ExtractionError` on malformed monetary values.
- **FR-003.2 (Safe Semantic Label Deduplication):** Deduplicate label variants within the same kind (`part` or `labour`) using conservative token subset matching (minimum 2 tokens overlap for non-identical labels). Maintain negative discrimination between distinct parts (`front brake pad` vs `rear brake pad`, `brake pad` vs `brake disc`). In tie scenarios with conflicting amounts, set `amount_paise=None` to require explicit review.
- **FR-003.3 (Canonical Audit Manifest):** Provide a single source of truth helper `audit_manifest` and `audit_manifest_sha256` that produces canonical UTF-8 JSON with sorted keys and fixed separators `(",", ":")` used identically for the PDF attachment and visible header text.
- **FR-003.4 (CWD-Independent Asset Resolution):** Resolve `DEFAULT_TELEPHONY_NOISE_PATH` relative to project/package structure and bundle noise assets in package data.
- **FR-003.5 (8-Category Generalization Evaluation Corpus):** Implement a versioned evaluation corpus spanning >=72 test cases across 8 specified categories with ground truth, split into development and holdout/challenge partitions, evaluated against exact item match, paise accuracy, false-merge/split rates, and review rate.
- **FR-003.6 (Domain Biasing Registry Verification):** Ensure domain vocabulary contains 60+ automotive mechanical components and colloquial terms correctly injected into verbatim STT biasing.

### NEW Non-Functional Requirements
- **NFR-003.1 (Evidence Before Claims):** All documented performance metrics and README claims must reflect current reproducible test suite evidence.
- **NFR-003.2 (Deterministic Sealing):** Hashing must be strictly deterministic across environments and platforms.
