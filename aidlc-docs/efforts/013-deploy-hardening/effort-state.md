# Effort 013 — deploy-hardening (2026-10-07)

**State:** complete. Deployed and verified live on Render.

## Scope
Harden the app for a public, judge-facing deployment: CI, licensing, an offline demo mode, spend/length/privacy
guards, Gnani key failover, and the actual deploy. Prompted by a review of the repo against the contest brief and
two other entrants (Kural, Boli-Zero); see `HARSHDOTHIS.md` (gitignored, local) for the full P0/P1 list this
session worked from.

## Delivered
- `.github/workflows/ci.yml` — offline suite on every push/PR; switched to a static FFmpeg build after the apt one
  lacked the AMR-NB encoder (`libopencore_amrnb`), which failed 3 lab tests in CI only (commit `1a98ee1`).
- `LICENSE` (MIT) — the README badge linked to a file that didn't exist.
- `src/parcha/mock.py` + `PARCHA_MOCK=1` — scripted Prisma/Extractor/Timbre so the full flow (intake → reask →
  readback → reply → PDF → verify) runs with no keys and no credits. Never for accuracy claims.
- `src/parcha/redact.py` — masks Indian phone numbers, Aadhaar and PAN before transcript text reaches the external
  extractor; amounts and plates pass through untouched (plates can be evidence).
- `src/parcha/gnani.py`: `KeyPool` + `chunk_for_tts` — `API_KEY` may list several comma-separated keys; a 401/403
  (Gnani's signal for a bad key or spent credits) retires that key for the process and the next one takes over,
  shared by Prisma/Timbre/captions (commit `d568ed7`). Long read-backs split into sentence-sized pieces below
  1,000 chars before Timbre (another entrant measured a Timbre failure point around 1,500–2,800 chars; not
  verified against our own account).
- `src/parcha/audio.py`: `stt_normalizer` enforces a 29.5 s cap before Prisma (its REST endpoint rejects clips of
  about 30 s or more, contra the documented 60 s); optional `AUDIO_CLEANUP=1` high-pass + denoise, off by default,
  unmeasured.
- `src/parcha/app.py` / `guard.py`: `MAX_SPEECH_CALLS_PER_DAY` — app-wide daily cap on credit-spending POSTs,
  independent of the existing per-client limits.
- `render.yaml` defaulted to the free plan (`plan: free`) so deploy needs no card; `docs/deploy.md`,
  `.env.example`, `README.md` updated to match (real state names, CI badge, safeguards table, mock-mode
  instructions, a business-case hypothesis section).
- Moved `sug.md` and `.scratch/` into `docs/dev-notes/` (still tracked; `aidlc-docs/`, `docs/raw/`,
  `docs/webattack_artifacts/` were left in place — many docs link to them).
- **Deployed**: Render blueprint `kaam-ka-parcha` connected to `HarshdipSaha/kaam-ka-parcha`, free plan, built and
  went live at `https://kaam-ka-parcha.onrender.com` (`/health` → `{"ok":true}`, `/stage` renders). `PUBLIC_BASE_URL`,
  `TWILIO_*` added later by effort 014.

## Tests
- Offline suite: 743 → 754 (P2 polish) → 758 (key failover) → stayed 758 through the free-plan commit.
- CI failed once on `main` (AMR-NB encoder missing, 3 tests; a 4th/5th failure was unrelated — early-gates tests
  reading a stale env var name `GNANI_API_KEY` instead of `API_KEY`, which only passed locally because of a local
  `.env`). Both fixed same session; confirmed `.env` moved aside locally then CI green on `main`.
- `signature_valid` (used again in effort 014) was later checked against the official `twilio-python` SDK test
  vector, not written yet at this point.

## Verification
- `git diff --check` clean (only CRLF warnings, no conflict markers).
- Full offline suite green before every push; CI green on `main` after the FFmpeg/env-var fixes.
- Live: `/health` and `/stage` checked directly after deploy (Playwright).

## Remaining (user or follow-up)
- `AUDIO_CLEANUP` A/B measurement (HARSHDOTHIS.md P1-5).
- `aidlc-docs/`, `docs/raw/`, `docs/webattack_artifacts/` cleanup decision before any further repo-visibility change.
- Native-speaker review of Tamil/Bengali/Kannada read-back strings (pre-existing, unrelated to this effort).
