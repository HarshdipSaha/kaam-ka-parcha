# Effort State: 008 — Real-Audio Analysis, Council Re-run & Money-Path Safety Spec

**Effort ID:** 008
**Reference:** `real-audio-analysis-council-spec`
**Status:** complete for analysis and council; spec draft held back for owner revision
**Started:** 2026-10-05
**Completed:** 2026-10-05
**Parents:** `006-real-api-real-audio-benchmark`, `007-gpu-sprint-multilingual-council`

## Stage Progression

| Stage | Status | Notes |
|---|---|---|
| Requirements | Complete | [`requirements-delta.md`](requirements-delta.md) |
| R9 deep analysis | Complete | [`R9`](../../../docs/research/R9-real-audio-benchmark-analysis.md) plus a one-command reproduction, `scripts/analyze_real_audio_benchmark.py`. Private: absolute CER/WER. |
| Council re-run | Complete | [`council-real-audio-verdict.md`](../../../docs/ideas/council-real-audio-verdict.md). Its gates supersede 007's where they conflict. |
| Spec (`to-spec`) | Drafted; **held back** | `docs/specs/money-path-safety-spec.md` exists locally as a draft. At the owner's request it was not committed with this effort, because it will be revised first. Once revised: label `ready-for-agent`; publishing needs `gh` signed in as HarshdipSaha. |
| Audit | Complete | [`audit.md`](audit.md) |
| Commit | Complete (partial by design) | Analysis, council, script and this effort were committed and pushed to `main`. The spec draft stays local until revised. |

## Key Results

1. **Scoring artefact.** Cleaned-reference CER is 0.070 against 0.162 as scored. Code-mixed speech is not harder once scored fairly.
2. **Engine-idle noise is too easy.** Only AMR-NB 4.75 at 0 dB degrades (+39–41% relative).
3. **The transcribe and verbatim passes are one decode.** Their difference is numeral formatting. Agreement between them is a formatting cross-check only.
4. **Failures are deletions and silent empties, never insertions.** i109 returned an empty-200 on AMR-NB. i036 has a label mismatch.
5. **No amount labels exist yet.** The product's promise is unmeasured.
6. **Council decisions:**
   - The money path is verbatim → numeral grammar → paise, with abstain-and-re-ask on incomplete numbers, cross-check disagreement, empty-200, 504 and 429, on intake and corrections.
   - Evon replaces Groq for items and parts only.
   - Benchmark v2: ~240 paise-labelled utterances, at most 2,000 credits.
   - Award target: Real Deal.
   - No use of the ten keys without written provenance.

## Owner Update: Credit Balance (2026-10-05)

The owner reports **about ₹4,700 remaining**, at roughly **50 credits per ₹1**. That is about **235,000 credits**. Source: the owner's statement in session on 2026-10-05; the dashboard was not read by the agent.

| Item | At 50 credits/₹ |
|---|---|
| Remaining balance | ≈ 235,000 credits |
| Effort 006 spend (4,964.86 credits, local estimate) | ≈ ₹99 |
| Benchmark v2 budget cap (≤ 2,000 credits) | ≈ ₹40 |
| Single-pass Prisma audio at 0.2 credits/s | ≈ 326 hours |

Consequences:
- **Credits are not a binding constraint.** The council's "one key nearly spent" concern (008 Review 2) is resolved by this statement.
- **Unit reconciliation is still open.** `CONTEXT.md` describes 5,000 programme credits per registration, which is ≈ ₹100 at the stated rate, so the reported balance exceeds a single registration's grant.
- **The provenance item is unchanged.** Before relying on any balance beyond the programme grant, record where it came from (the ten extra keys from effort 006, or any top-up), as the verdict's 2026-10-06 gate requires.

## Open Items for the Owner

- Balance: **recorded** (above, owner-stated). Still open: the written provenance of the balance beyond the programme grant and of the ten extra keys (verdict "one thing to do first").
- Send the organiser Discord questions (007 list plus "may these keys be used?").
- Confirm the spec's two seams and its derived decision on attaching amounts to items.
- Revise the spec draft, then commit it and publish it as a GitHub issue once `gh` is available.
