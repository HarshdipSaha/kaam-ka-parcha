# Effort 005: Audit

**Audit date:** 2026-10-05
**Status:** Pending merge.

| Requirement | Evidence | Audit result |
|---|---|---|
| REST requests at or below provider limit | 32.6-second offline fixture is submitted as 29.0s + 3.6s; live 32.6-second recording returned without duration rejection | Pass |
| Request forecast accounts for chunks, including AMR-NB frame padding | 29-second AMR regression verifies forecast and actual runner both make two requests | Pass |
| Any chunk rejection fails the full row closed and stops later calls | 70-second regression rejects the first chunk and verifies no later chunks are sent; transcript and hallucination count remain null | Pass |
| Real noisy condition is evaluated honestly | Two variants returned a wrong spoken amount; two later calls were API rejected with HTTP 429 | Partial; estimate quality gate not met |
| No claims of broad model accuracy | Effort-state and construction log explicitly constrain conclusions to the probed clips | Pass |

## Acceptance

The 400 failure is resolved for the lab runner: requests are split below the observed 30-second REST limit, and the same engine-only recording completes. This fix does not make the real noisy estimate amount-correct. The live noisy speech spot check surfaced a ₹450 recognition failure and two HTTP 429 responses; those failures remain visible in the AIDLC record and require separate investigation before claiming reliable real-world estimates.

Mark this effort complete only after the PR passes review and merges.
