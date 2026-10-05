# Documentation Corrections — October 2026

- **2026-10-05 — README extractor setup:** Marked the extractor as required and documented the four `EXTRACTOR_*` settings. The prior README called it optional and named a stale `GROQ_API_KEY` variable.
- **2026-10-05 — README speech endpoint setting:** Corrected `API_BASE_URL` to `GNANI_BASE_URL` because `Settings` does not consume the old name.
- **2026-10-05 — Demo recovery figures:** Removed the claimed `+20.0%` part recovery, `96.0%` short-reply recovery, `800` synthetic turns, and `N=800` attribution. No committed evaluation command or result supports those figures; the demo now shows evaluation settings and pending measurements.
- **2026-10-05 — README and demo workshop-margin figures:** Removed the unsupported `5% to 8%` README and `8%` demo claims because the repository contains no traceable source or measurement for them.
- **2026-10-05 — Demo test count and runtime:** Removed the claim of `139` tests in `17` seconds because it is not supported by a committed command result.
- **2026-10-05 — Demo legal wording:** Replaced “legally sealed” with “tamper-evident”; the artefact supports tamper-evidence language, not a legal enforceability claim.
- **2026-10-05 — Generalisation ledger:** Marked the 74-case result unreproducible because the repository has evaluation helpers and unit tests but no runner that executes the full corpus and produces that result.
- **2026-10-05 — Garage audio provenance:** Labeled `mechanic_in_garage_noise.wav` as synthesized mechanic speech mixed with recorded engine rumble, so the ledger does not imply the mechanic speech was recorded in a real garage.
- **2026-10-05 — E2E gate evidence:** Marked the dated E2E result not reproducible because the only tracked input is the synthesized WAV and no committed result artifact supports the reported credit spend, exact amounts, or PDF verification.
