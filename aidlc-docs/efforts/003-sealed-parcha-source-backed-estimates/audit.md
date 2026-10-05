# Audit: Effort 003 — Sealed Parcha Source-Backed Estimates

**Effort ID:** 003  
**Reference:** sealed-parcha-source-backed-estimates  
**Date:** 2026-10-05  
**Review Type:** Code Quality, Security, and Spec Compliance Audit  

---

## 1. Traceability Matrix

| Requirement | Implementation Artifact | Test Suite Evidence | Status |
|---|---|---|---|
| **FR-003.1** (Strict monetary validation) | `src/parcha/schema.py`, `src/parcha/extract.py` | `tests/test_schema.py`, `tests/test_extract.py` | Verified (Pass) |
| **FR-003.2** (Semantic label deduplication) | `src/parcha/extract.py` | `tests/test_extract.py` | Verified (Pass) |
| **FR-003.3** (Canonical audit manifest SHA-256) | `src/parcha/artefact.py` | `tests/test_artefact.py`, `scripts/run_webattack_suite.py` | Verified (Pass) |
| **FR-003.4** (CWD-independent noise resolution) | `src/parcha/config.py`, `src/parcha/assets/` | `tests/test_config.py` | Verified (Pass) |
| **FR-003.5** (Generalization evaluation corpus) | `data/generalization_corpus_v1.json`, `src/parcha/lab/eval_corpus.py` | `tests/test_generalization_corpus.py` | Verified (Pass) |
| **FR-003.6** (Automotive domain biasing) | `src/parcha/vocabulary.py`, `src/parcha/workflow.py` | `tests/test_vocabulary.py`, `tests/test_workflow.py` | Verified (Pass) |

---

## 2. Security & Data Integrity Audit

1. **Monetary Integrity**: Disallowed all implicit coercions from JSON values (e.g. `true` becoming 1, `"750"` becoming 750, floats being rounded). Values must be non-negative integer paise or `None`.
2. **Deduplication Boundary**: Token subset matching strictly requires minimum 2 tokens overlap for non-identical labels, precluding keyword over-merges (e.g. `brake` matching every brake item). Distinct components such as front vs rear pads and pads vs discs are proven retained.
3. **Cryptographic Sealing**: Canonical JSON formatting guarantees deterministic hashing across all Python runtimes. The digest on the visible PDF header matches the attachment payload byte-for-byte.
4. **Environment Isolation**: No hard-coded directory assumptions; package assets resolve safely regardless of execution directory.

---

## 3. Sign-Off Verdict

- **Code Review**: Standards and Spec compliance verified. Zero P1/P2 issues.
- **Test Result**: 170 passed offline tests. Full Playwright E2E interactive run passed.
- **Recommendation**: Merge into `main` and close GitHub issues #8, #9, and #2.
