# Effort State: 007 — GPU Sprint Research, Multilingual-Model Review & Council Verdict

**Effort ID:** 007
**Reference:** `gpu-sprint-multilingual-council`
**Title:** A100 GPU Sprint Research, Multilingual-Model Literature Review & LLM Council Verdict
**Status:** complete (documentation)
**Started:** 2026-10-05
**Completed:** 2026-10-05
**Parent Effort:** Inception baseline; informs follow-ups to `004-enterprise-telephony-compliance`

## Stage Progression

| Stage | Status | Notes |
|---|---|---|
| Requirements | Complete | [`requirements-delta.md`](requirements-delta.md): the owner's verbatim GPU question, a literature review using the `arxiv` skill, and a council using the `llm-council` skill, all documentation-only. |
| R7 GPU-sprint brief | Complete | [`R7-a100-gpu-sprint.md`](../../../docs/research/R7-a100-gpu-sprint.md). Key verified facts: Evon BF16 is 63.5 GB and doesn't fit; community GGUF Q8_0 (31.45 GiB) on llama.cpp is the ready-made fit; both HF repos ungated; 16-bit LoRA doesn't fit, 4-bit QLoRA is fragile. W1 (Groq Llama-3.3-70B mandatory in intake and re-ask) independently confirmed in code. |
| R8 literature review | Complete | [`R8-multilingual-models-arxiv.md`](../../../docs/research/R8-multilingual-models-arxiv.md). 45 papers, 5 clusters, proposals P1–P8. §1.3 corrected after peer review (W2 is a one-pass-right case). |
| Council | Complete | Framed question → 5 advisors → 5 fact-checked reviews → chairman. Verdict: [`council-gpu-multilingual-verdict.md`](../../../docs/ideas/council-gpu-multilingual-verdict.md). |
| Audit | Complete | [`audit.md`](audit.md). |
| Sync with `main` and commit | Complete | Rebased onto `main` after PR #17. Registry conflict resolved by keeping effort 006 and renumbering this effort to 007. Committed with the repo-local identity. |

## Decisions Recorded (from the verdict; not implemented)

1. Core promise: **a wrong rupee amount never gets confirmed.** Amounts come from a deterministic Hinglish numeral grammar, two-pass agreement and abstention with a targeted re-ask, on both intake and customer corrections. No LLM decides money.
2. Evon replaces Groq for line items and part names, with constrained output. It may suggest which pass is right, but only deterministic agreement auto-accepts an amount.
3. The GPU window is a bonus measured run: at most ~12 attended hours, one unattended scripted batch, demo footage, and quant export. No dates by 18 Oct means plan for no GPU.
4. Hinglish only. Dropped: QLoRA, Tanglish/Benglish, regional read-back, Parcha-Bench, the enhancement A/B, and the `bias_list` A/B.
5. Integrity fixes (README "optional", `demo.md` unmeasured numbers, `gates.md` "74/74 PASS") go in one dated corrections note, disclosed but not made the headline.
6. The first action is one organiser Discord message: Is scripted real-person roleplay "synthetic"? May recordings be real phone calls? Does a community Q8_0 GGUF satisfy Rule 3? Can own-pipeline deltas be published?

## Concurrent Effort 006 (merged the same day): assumptions it overtakes

This effort was written on one machine while effort [`006-real-api-real-audio-benchmark`](../006-real-api-real-audio-benchmark/effort-state.md) ran on another. Effort 006 was merged to `main` as PR #17 (`9721a54`) first, so this effort was renumbered from 006 to 007 during the merge. Effort 006 changes several inputs the council relied on:

- **W3 "no real recordings"** is partly overtaken. Effort 006 benchmarked 120 real CC BY 4.0 Hindi clips (IndicContextEval) plus five private user-provided workshop clips across both Prisma modes, two codecs and four SNR levels: 2,000 conditions.
- **Credit budget**: the council assumed ~4,980 credits left. Effort 006 estimates 4,964.86 credits spent on the configured key, and records that ten additional 5,000-credit keys are available.
- **W5 (HTTP 429)**: effort 006 added request spacing and stop-on-provider-error. Its run saw two HTTP 504s, each recovered on one retry.

The verdict's gates and recommendations should be re-checked against effort 006's results before they are acted on. A council re-run on those results is the planned next step.

## Evidence and Limitations

- Paper results in R8 are the papers' own results, not measurements of this pipeline. Numbers read through a summarising fetch are marked [VERIFY].
- Council advisors and reviewers are model agents with different prompts, not independent humans. Reviewers fact-checked against one repo file each, and their factual flags were carried into the verdict's corrections list.
- No Gnani API calls, no credit spend, no code changes.
