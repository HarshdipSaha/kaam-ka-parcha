# Effort 008: Real-Audio Benchmark Analysis, Council Re-run & Money-Path Safety Spec

**Effort ID:** 008
**Reference:** `real-audio-analysis-council-spec`
**Parents:** `006-real-api-real-audio-benchmark` (data), `007-gpu-sprint-multilingual-council` (prior verdict)
**Started:** 2026-10-05
**Type:** Analysis, decision record and specification. One offline analysis script; no product code changes.

## Problem

Effort 006 (PR #17, merged from the owner's second machine) ran 2,000 live Prisma conditions on real Hindi audio. Its `summary.json` reports grouped CER/WER, but three questions were open:
- what those numbers actually mean;
- whether they hold up;
- how they change the 007 verdict.

The owner asked for:
1. A deep analysis of the PR's results.
2. A re-run of the LLM Council on them.
3. An updated spec for the resulting improvements, written with the `to-spec` skill from `mattpocock/skills`.

All of it in markdown, with an AIDLC log.

## Requirements Delta

1. **R9 analysis.** An offline, reproducible analysis of `data/benchmarks/real_audio_2026-10/`. It must:
   - recompute the stored metrics exactly;
   - test reference quality;
   - give paired mode comparisons with clip-level confidence intervals;
   - show degradation by codec and SNR;
   - break results down by stratum;
   - analyse numerals, bias words, failure shapes, the workshop slice, latency and credit efficiency.

   Absolute numbers stay private (`AGENTS.md`). Deliverables: `docs/research/R9-real-audio-benchmark-analysis.md` and `scripts/analyze_real_audio_benchmark.py`, a stdlib-only, one-command reproduction.
2. **Council re-run** with the `llm-council` skill: a framed question, 5 advisors, 5 reviewers each with one evidence file, and a chairman verdict that includes a "Decisions for the Updated Spec" list. Saved under `docs/ideas/council-real-audio/`, with the verdict at `docs/ideas/council-real-audio-verdict.md`.
3. **Updated spec** via the `to-spec` skill (installed into `~/.claude/skills/to-spec/`):
   - follow its template;
   - record only decisions already made;
   - name the testing seams;
   - use the project vocabulary;
   - publish to the issue tracker, or record why it couldn't be published.

   Deliverable: `docs/specs/money-path-safety-spec.md`.
4. **AIDLC record**: this folder and a registry row.

## Out of Scope

- Product code changes (the spec describes them; implementation is a later effort).
- Any Gnani API call or credit spend.
- Committing or pushing without the owner's go-ahead.
