# Effort 017 — speech-safety-and-evidence (2026-11-10)

**State:** complete for the first slice (3a, 1a, 1c, 1f of the owner's hardening list). Offline suite 839 passed.
The rest of the list is assessed below and deferred, not dropped.

## Why
An external review proposed three changes: a tamper-evident evidence record, persistent sessions, and a trustworthy
speech input layer. Each claim was checked against the code first.

## Verified and fixed
- **3a, dead confidence gate (live safety bug).** Prisma's documented responses carry `"confidence": null`; the client
  substituted 1.0 and kept it in shared client state (`last_confidence`), so the 0.65 fallback gate never fired and two
  concurrent requests could read each other's value. Now `PrismaClient.transcribe_detailed` returns
  `Transcript(text, confidence)` with `None` when nothing was reported, per call. In `reply()`, a reported confidence
  under 0.65 still falls back; an **unknown** confidence on a yes triggers a second `verbatim` pass over the same audio,
  and the parcha is confirmed only when both passes hear a yes (otherwise `unconfirmed_accept` and a retry, then the
  fallback after two). Corrections and unclear replies make no extra call: they already lead to a re-read or a retry.
  Deviation from the proposal: `transcribe()` still returns `str`, so the dozens of fakes and tests that script it are
  untouched; only the detailed call changed.
- **1c, the digest did not cover the amounts.** `audit_manifest` held logs and consent but not the card. It now carries
  `schema: parcha-manifest/1`, `channel`, and the card (item ids, labels, kinds, `amount_paise`, `total_paise`,
  delivery date, window and phrase).
- **1a, printed audio hashes could not be checked.** The served `intake.wav`/`reply.wav` are the raw uploads, while the
  printed hash was of the processed audio. `TranscriptLog.raw_audio_sha256` is recorded on intake and reply, included
  in the manifest, and printed on the PDF and verify page; `audio_sha256` keeps the processed hash.
- **1f, QR and label.** The QR encoded a bare `/verify/{id}` (scans to nowhere); it now encodes
  `PUBLIC_BASE_URL/verify/{id}` and is omitted when no base URL is set. The verify page no longer claims
  "BSA 2023 §§ 61–63 Compliant" or "Tamper-Evident"; it says "SHA-256 audit record ... (unsigned)".

## Tests
- Added `tests/test_reply_confidence.py` (unknown vs reported confidence, concurrency, two-pass agreement, no extra call
  on corrections) and `tests/test_evidence_record.py` (card in manifest, one-amount tamper changes the digest, card in
  the PDF attachment, printed hashes equal the served files, QR address, no QR without a base URL).
- Changed on purpose: three tests now expect two Prisma calls on a confirmed yes; the QR test passes a base URL; three
  tests that required the "Compliant"/"Bharatiya Sakshya Adhiniyam" wording now forbid it.

## Deferred (assessed)
- **1d Ed25519 signing, `POST /verify` from the PDF, offline CLI.** The step that makes the record genuinely
  tamper-evident without trusting the server. Needs `PARCHA_SIGNING_KEY` set on Render and a new dependency; not done
  on submission day so the live PDF does not switch to "UNSIGNED DEMO" mid-recording. Next.
- **1b hash chain.** Adds little until signing exists: the manifest digest already covers every log in order, so an
  edit or reorder changes it. Worth doing together with 1d and the database (append-only rows).
- **1e consent rework.** Agreed that the current consent hash proves nothing (rebuildable string). Spoken consent adds a
  `<Record>` step to the live call, so it waits until after the demo.
- **2 SQLite persistence.** Right fix for `/verify` 404s after restarts, but Render's free plan has an ephemeral disk,
  so it only pays off with a paid disk (or an external database). Plan it with the hosting decision.
- **3b silence-aware splitting, 3c WebSocket segments.** 3b changes the money path at chunk edges and needs the
  incomplete-number rule plus real long recordings to validate; 3c affects display-only captions. Lower priority.
