# Construction: Effort 003 — Sealed Parcha Source-Backed Estimates

**Effort ID:** 003  
**Reference:** sealed-parcha-source-backed-estimates  
**Date:** 2026-10-05  
**Baseline:** `aidlc-docs/inception/requirements.md`  

---

## 1. Implemented Components

### 1.1 Strict Monetary Validation (`src/parcha/schema.py`, `src/parcha/extract.py`)
- Added `@field_validator("amount_paise", mode="before")` enforcing `type(value) is int or value is None`.
- Explicitly rejects `bool` (`True`/`False`), numeric strings (`"750"`), and float values (`450.5`), preventing extractor JSON type coercion from corrupting rupee amounts.
- Updated `Extractor.extract_card` and `Extractor.extract_field` to catch validation errors and raise `ExtractionError` instead of producing invalid cards.
- Comprehensive test coverage in `tests/test_schema.py` and `tests/test_extract.py`.

### 1.2 Conservative Semantic Label Deduplication (`src/parcha/extract.py`)
- Enhanced `_labels_describe_same_item` to match token sets and safe subset relationships (requiring at least 2 tokens overlap for non-identical tokens).
- Prevents collapsing distinct components (e.g. `front brake pad` vs `rear brake pad`, `brake pad` vs `brake disc`).
- Implemented tie detection: if duplicate candidates have equal transcript evidence, sets `amount_paise=None` to force explicit mechanic/customer review rather than silently picking an amount.
- Re-indexes line item IDs to canonical form (`part-1`, `labour-1`) and remaps evidence field pointers.

### 1.3 Canonical Audit Manifest & Deterministic Digest (`src/parcha/artefact.py`)
- Created unified helper `audit_manifest` and `audit_manifest_sha256`.
- Produces canonical UTF-8 JSON with sorted keys and separators `(",", ":")`.
- Used identically for visible PDF header text and embedded `transcripts.json` attachment.
- Verified in unit tests and WebAttack E2E test that the extracted attachment digest exactly matches the rendered PDF text.

### 1.4 Working-Directory-Independent Noise Asset Resolution (`src/parcha/config.py`, `src/parcha/assets/`)
- Resolved default noise path relative to package and repository root (`PROJECT_ROOT` / `PACKAGE_ROOT`).
- Bundled `car_engine_idle_16k.wav` into `src/parcha/assets/` and declared in `pyproject.toml` package-data.
- Tested `default_services()` and `Settings.from_mapping()` from temporary directories to guarantee robustness when running from subdirectories or as an installed package.

### 1.5 8-Category Generalization Evaluation Corpus (`data/generalization_corpus_v1.json`, `src/parcha/lab/eval_corpus.py`)
- Constructed versioned corpus with 74 cases across 8 required categories:
  1. Clean workshop speech (10 cases)
  2. Engine/road/workshop noise (10 cases)
  3. Different speakers, regions, and pacing (10 cases)
  4. Multiple parts and labour (10 cases)
  5. Corrections and re-asks (8 cases)
  6. Ambiguous or missing amounts (8 cases)
  7. Adversarial numbers and timestamps (8 cases)
  8. Duplicate and near-duplicate labels (10 cases)
- Partitioned into 44 development, 12 holdout, and 18 challenge cases.
- Implemented metrics calculation module reporting exact item match, paise accuracy, total accuracy, false confirmation rate, false merge rate, false split rate, and review rate.
- Verified via `tests/test_generalization_corpus.py`.

### 1.6 Automotive Domain Biasing Registry (`src/parcha/vocabulary.py`)
- Curated 65 automotive terms and brand names.
- Integrated into `PrismaClient.transcribe` verbatim pass under `AUTOMOTIVE_BIAS_WORDS`.
- Verified in `tests/test_vocabulary.py` and `tests/test_workflow.py`.

---

## 2. Test & Verification Summary

- **Unit & Integration Suite:** 170 passed (100% offline, 0 warnings).
- **Static Analysis:** `compileall` passed, `git diff --check` passed with 0 errors.
- **WebAttack E2E Suite:**
  - Surface crawler passed.
  - Responsive audit across 4 viewports passed with 0 overflows.
  - Real-world garage audio intake (`mechanic_in_garage_noise.wav`) parsed into Rs. 450 brake pad + Rs. 200 labour = Rs. 650 total.
  - Customer review page, G.711 + 5 dB engine audio playback, and customer affirmation ("Haan theek hai") passed.
  - Sealed PDF verified with valid embedded `transcripts.json` and matching SHA-256 manifest digest.
  - Negative security probes (404, 409, 422, path traversal) passed.
