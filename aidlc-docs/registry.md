# AI-DLC Effort Registry

**Project:** Kaam ka Parcha (Phone-Sealed)  
**Last Updated:** 2026-10-07
**Baseline:** `aidlc-docs/inception/` (Locked & Signed Off)  

---

## Registered Efforts

| Effort ID | Reference | Title | Status | Created | Completed | Plan / Reference |
|---|---|---|---|---|---|---|
| **001** | `core-system` | Kaam Ka Parcha Core Implementation (Tasks 1–19) | **complete** | 2026-10-04 | 2026-10-05 | [`docs/superpowers/plans/2026-10-04-kaam-ka-parcha.md`](../docs/superpowers/plans/2026-10-04-kaam-ka-parcha.md) |
| **002** | `webattack-realworld-validation` | Localhost Surface WebAttack, Deep Real-World Voice Data & Playwright E2E Testing | **complete** | 2026-10-05 | 2026-10-05 | [`aidlc-docs/efforts/002-webattack-realworld-validation/`](efforts/002-webattack-realworld-validation/effort-state.md) |
| **003** | `sealed-parcha-source-backed-estimates` | Sealed Parcha Evidence Alignment, Monetary Sanitization, Semantic Deduplication & Generalization Evaluation Corpus | **complete** | 2026-10-05 | 2026-10-05 | [`aidlc-docs/efforts/003-sealed-parcha-source-backed-estimates/`](efforts/003-sealed-parcha-source-backed-estimates/effort-state.md) |
| **004** | `enterprise-telephony-compliance` | Enterprise Voice-Sealed Service Agreement & Telephony Robustness Pipeline (Issues #3-#7, Epic #1) | **active** | 2026-10-05 | Pending | [`aidlc-docs/efforts/004-enterprise-telephony-compliance/`](efforts/004-enterprise-telephony-compliance/effort-state.md) |
| **005** | `lab-max-audio-duration-rejection` | Split Long Lab Audio at the Gnani REST Duration Limit | **complete** | 2026-10-05 | 2026-10-05 | [`aidlc-docs/efforts/005-lab-max-audio-duration-rejection/`](efforts/005-lab-max-audio-duration-rejection/effort-state.md) |
| **006** | `real-api-real-audio-benchmark` | Budgeted Real-API Benchmark Across Hindi Speech and User-Provided Workshop Audio | **active** | 2026-10-05 | Pending | [`aidlc-docs/efforts/006-real-api-real-audio-benchmark/`](efforts/006-real-api-real-audio-benchmark/effort-state.md) |
| **007** | `gpu-sprint-multilingual-council` | A100 GPU Sprint Research (R7), Multilingual-Model Literature Review (R8) & LLM Council Verdict | **complete** (docs) | 2026-10-05 | 2026-10-05 | [`aidlc-docs/efforts/007-gpu-sprint-multilingual-council/`](efforts/007-gpu-sprint-multilingual-council/effort-state.md) |
| **008** | `real-audio-analysis-council-spec` | Real-Audio Benchmark Analysis (R9), Council Re-run & Money-Path Safety Spec | **complete** (docs; spec committed, GitHub issue pending) | 2026-10-05 | 2026-10-05 | [`aidlc-docs/efforts/008-real-audio-analysis-council-spec/`](efforts/008-real-audio-analysis-council-spec/effort-state.md) |
| **009** | `money-path-plan` | Money-Path Safety & Benchmark v2 Implementation Plan (writing-plans) | **active** | 2026-10-05 | Pending | [`aidlc-docs/efforts/009-money-path-plan/`](efforts/009-money-path-plan/effort-state.md) |
| **010** | `ui-digital-parcha-plan` | UI Research (R10–R14), "Digital Parcha" Spec & Implementation Plan (runs after 009) | **complete** (plan; implementation not started) | 2026-10-05 | 2026-10-05 | [`aidlc-docs/efforts/010-ui-digital-parcha-plan/`](efforts/010-ui-digital-parcha-plan/effort-state.md) |
| **011** | `ui-digital-parcha-build` | Build of the 010 plan: presentation helpers, payload contract, design system, workshop/customer/stage/verify pages | **complete** | 2026-10-05 | 2026-10-05 | [`aidlc-docs/efforts/011-ui-digital-parcha-build/`](efforts/011-ui-digital-parcha-build/construction.md) |
| **012** | `deploy-ready` | Container + deploy files, owner-take recorder, bounded sessions | **complete** (repo side; deployment is a user step) | 2026-10-07 | 2026-10-07 | [`aidlc-docs/efforts/012-deploy-ready/`](efforts/012-deploy-ready/effort-state.md) |
| **013** | `deploy-hardening` | CI, LICENSE, offline mock mode, spend/length/privacy guards, Gnani key failover; deployed live to Render (free plan) | **complete** | 2026-10-07 | 2026-10-07 | [`aidlc-docs/efforts/013-deploy-hardening/`](efforts/013-deploy-hardening/effort-state.md) |
| **014** | `twilio-phone-leg` | Real customer phone call via Twilio alongside the simulated line; live-verified with a real call (confirmed, PDF sealed) | **complete** | 2026-10-07 | 2026-10-07 | [`aidlc-docs/efforts/014-twilio-phone-leg/`](efforts/014-twilio-phone-leg/effort-state.md) |

---

## Inception Baseline Status
- **Requirements:** [`aidlc-docs/inception/requirements.md`](inception/requirements.md) (Locked)
- **Architecture:** [`aidlc-docs/inception/architecture.md`](inception/architecture.md) (Locked)
- **Components:** [`aidlc-docs/inception/components.md`](inception/components.md) (Locked)
- **Audit Trail:** [`aidlc-docs/inception/audit.md`](inception/audit.md) (Signed Off)

---

## Active & Next Efforts
- **Concurrent Active Effort:** `006-real-api-real-audio-benchmark` — User-requested budgeted real-API speech evaluation.
- **Active Effort:** `004-enterprise-telephony-compliance` — Resolves GitHub Issues #3, #4, #5, #6, #7, and Epic #1.
- **Follow-up from 014:** no `/workshop` UI button for the Twilio call yet (API-only); no automatic WhatsApp/SMS
  delivery after a phone confirmation; real-call accuracy scoring (~20 calls) not yet run.
