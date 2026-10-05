# Effort 010: UI Research, "Digital Parcha" Spec & Implementation Plan

**Effort ID:** 010
**Reference:** `ui-digital-parcha-plan`
**Parent:** `009-money-path-plan` (runs first; this plan builds on its contracts)
**Started:** 2026-10-05
**Type:** Research, specification and plan. No product code changes.

## Problem

The owner says the UI is poor on web and phone. They asked for:
1. Deep, multi-agent research on winners of similar hackathons (Sarvam and other Indic/voice events), including their websites and code, plus two named repos (`AfreenInnovates/campus`, `Prashant-thakur77/Beacon`). The design must "resemble the target audience".
2. All agent reports saved in the repo as markdown.
3. A spec written with `to-spec` (mattpocock/skills).
4. A detailed plan, using `writing-plans` (obra/superpowers), with code snippets for the website and all Playwright tests.
5. No implementation, test runs or package installs during this effort.
6. The plan must run **after** the money-path plan (effort 009).

## Requirements Delta

1. **Research R10–R14** under `docs/research/`:
   - R10 Sarvam and Indic hackathon winners;
   - R11 the CampusEvac and Beacon repos;
   - R12 voice-AI hackathon winners and 60-second demos;
   - R13 the target audience;
   - R14 the Indian visual language.
2. **Spec** `docs/specs/ui-digital-parcha-spec.md`:
   - follows the to-spec template, with the testing seams named;
   - uses project vocabulary;
   - keeps ids, disclosures and legal strings;
   - includes a section on its dependency on the money-path plan.
3. **Plan** `docs/superpowers/plans/2026-10-05-ui-digital-parcha.md`:
   - writing-plans header, Global Constraints, Review Focus and File Structure;
   - Tasks 0–9 with the full CSS, templates, JS, backend changes and Playwright tests;
   - a self-review.
4. **AIDLC record:** this folder plus a registry row.

## Out of Scope

- Changes to `src/` or `tests/`; any test run, package install or browser download; any Gnani API call.
- Publishing the spec to GitHub Issues (`gh` is not installed).
