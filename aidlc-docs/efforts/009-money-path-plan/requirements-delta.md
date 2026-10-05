# Effort 009: Money-Path Safety Implementation Plan

**Effort ID:** 009
**Reference:** `money-path-plan`
**Parent:** `008-real-audio-analysis-council-spec` (spec `docs/specs/money-path-safety-spec.md`)
**Started:** 2026-10-05
**Type:** Planning (no product code changes)

## Problem

The money-path spec (effort 008), updated with three owner decisions, needs an implementation plan. The decisions are: a mandatory Gramvaani slice, Timbre tested through an echo test, and cost not a constraint. The owner asked that the plan:
- use the writing-plans skill (obra/superpowers);
- follow the previous plan's environment (Windows PowerShell, Python 3.12 `.venv` on the second laptop);
- check every data reference against the real source;
- carry code snippets that work;
- produce a benchmark that impresses judges;
- be pushed directly.

## Requirements Delta

1. Plan at `docs/superpowers/plans/2026-10-05-money-path-safety.md`, in the skill's format: header, Global Constraints, Review Focus, bite-sized TDD tasks with Interfaces blocks, and a self-review.
2. Every dataset, voice, rate and code-interface claim checked against its source, with the check recorded in the plan's "Verified Facts" table.
3. Code snippets for the new modules prototyped against the real repository code before inclusion. At the owner's later request, no further testing or package installation during planning: the remaining checks happen during implementation.
4. Spec corrections from the verification: the current read-back format is ₹ digits, the echo-test cost and two-stage design, the verified Gramvaani facts, and the `out_of_range` reason.
5. AIDLC record and registry row. Commit and push directly to `main`.

## Out of Scope

- Implementing the plan.
- Live API calls.
