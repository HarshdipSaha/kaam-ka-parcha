# Effort 007: A100 GPU Sprint Research, Multilingual-Model Literature Review & Council Verdict

**Effort ID:** 007
**Reference:** `gpu-sprint-multilingual-council`
**Parent:** Inception baseline (`aidlc-docs/inception/`); informs `004-enterprise-telephony-compliance` follow-ups
**Started:** 2026-10-05
**Type:** Research and ideation (documentation only; no application code changes)

## Problem

The builder will have one NVIDIA A100 40 GB for three days before the 10 Nov 2026 deadline. The 2026-10-04 council ([`docs/ideas/council-verdict.md`](../../../docs/ideas/council-verdict.md)) kept Evon out of the critical path mainly because there was no GPU to host it. Effort 005 also left a real accuracy failure open: on the 4.8-second mechanic-in-garage-noise clip, Prisma returned `04:30 100` where the spoken amount was ₹450 ([`005 construction log`](../005-lab-max-audio-duration-rejection/construction.md)). Before spending GPU hours, the project needs:

1. A grounded answer to: *"I will have a GPU for 3 days (A100 40 GB). What more can I do on this idea to win more?"*
2. Ideas taken from published multilingual-model work (Aya, BLOOM, Jais, EuroLLM, Swallow, Chinese-LLaMA, NLLB/Seamless/MMS, AI4Bharat's Indic models) and from LLM-based ASR error correction, read from the papers rather than from memory.
3. A multi-perspective decision on what to change in the project, using the LLM Council method (5 advisors, anonymous peer review, chairman synthesis).

## Requirements Delta

1. **R7 GPU sprint brief**: deep repo analysis, web-verified facts (Evon v3.3 hosting precision and runtime on 40 GB, LoRA feasibility, speech-enhancement evidence, rule compatibility), a ranked idea list, and a 72-hour plan whose outputs remain usable after the GPU is returned. Written to `docs/research/R7-a100-gpu-sprint.md` in the existing `R*.md` style.
2. **R8 literature review**: papers found with the `arxiv` skill (arXiv export API) and read in full text where available; per-paper findings with numbers and section references; explicit applicability to Kaam ka Parcha; a research log of every query. Written to `docs/research/R8-multilingual-models-arxiv.md`.
3. **Council run** using the `llm-council` skill's method: framed question (with R7, R8, and repo context), 5 independent advisors in parallel, anonymised peer review by 5 reviewers, and a chairman verdict. Persist all rounds under `docs/ideas/council-gpu-multilingual/` and the verdict at `docs/ideas/council-gpu-multilingual-verdict.md`, mirroring the 2026-10-04 council layout.
4. **AIDLC record**: this effort folder (`requirements-delta.md`, `construction.md` as the running log, `effort-state.md`, `audit.md`) and a registry row.
5. **Honesty constraints carried forward** from `AGENTS.md`: no Gnani API calls or credit spend in this effort; no competitor comparisons or absolute CER/WER proposed for public material; estimates marked as such; paper claims cited to the paper, not restated as our results.

## Out of Scope

- Any change to `src/`, `tests/`, `scripts/`, or data fixtures.
- Executing the GPU plan, requesting Evon weights, or renting compute.
- Committing or pushing. Changes are left in the working tree for the owner to review.
