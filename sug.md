# sug.md — remaining work for Kaam ka Parcha (agent-ready)

Audience: a coding agent working in this repo, plus one human owner. Part A is for the agent. Part B is for the human only; the
agent must not attempt it, and must not fake its outputs. Repo state when written: `main` at `1a99bc8`, 635 offline tests passing.
Evidence for every number quoted here is in `docs/gates.md`.

## 0. Rules for the agent (read first)

1. **Start of task.** Run `git status`, read `AGENTS.md`, `CONTEXT.md`, then only the files named in the task you pick. Preserve unrelated work.
2. **Credits are not a constraint.** The owner has a large hackathon Gnani balance (about 235,000 credits reported, not console-verified) and will add more. Use the real `.env` keys and run live benchmarks at full size. Do not shrink samples, skip conditions, or stop to ask about spend for tasks in this file.
3. **Guards stay on anyway.** Run the dry-run forecast first, pass `--max-credits` generously (for example 5000), and log estimated spend in `docs/gates.md` labelled "estimate, not console billing".
4. **Rate limits are the real constraint.** Use `--interval 1.0` or more, run one live job at a time, and resume rather than restart (runners skip finished rows).
5. **Secrets.** Never print, log, commit or paste `.env` values, keys or private audio. Outputs go under ignored `var/`. Never `git add .env` or anything under `var/`.
6. **Honest reporting.** Synthetic (Timbre) speech is not real-speech accuracy; label it. Update `docs/gates.md`, `aidlc-docs/efforts/009-money-path-plan/effort-state.md` and README numbers only from fresh, reproducible runs. Never invent human labels or owner recordings.
7. **Money rules from `AGENTS.md` still apply:** integer paise, unknown stays `None`, evidence tied to transcript, confirmed sessions immutable, no sealed artefact from an incomplete card, keep the telephony-simulation and clipboard-copy disclosures.
8. **Test-first, then verify.** Add a regression that fails for the observed problem, run focused tests, then `.\.venv\Scripts\python.exe -m pytest -q` (offline) and, for UI changes, `.\.venv\Scripts\python.exe -m pytest -q tests/e2e -m e2e` (offline fakes, zero credits). Run `git diff --check`.
9. **Commit.** Scoped commits on `main`, push without force, end messages with the attribution line the harness provides. Exclude `.env`, `var/`.
10. **Rejected idea — do not implement:** accepting an amount when the two Prisma passes on one recording agree. Saved runs show 475 of 1,344 amounts accepted and 4.0% of those wrong (10.2% at 0 dB). Do not let the customer read-back stand in for the independent check either; that is a spec change (`docs/specs/money-path-safety-spec.md`), not a patch.

## 1. Current state (facts to build on)

- Amount rule: a flagged amount settles only when two consecutive recordings agree (`independent_confirmation_required`, `recordings_disagree`; `Workflow._require_agreeing_recordings` in `src/parcha/workflow.py`). Candidate quotes are stored as zero-score evidence.
- Transcribe-pass fraction formats are normalised before the cross-check (`normalise_transcribe_fractions` in `src/parcha/money.py`).
- Re-ask benchmark (`scripts/run_reask_bench.py`, `src/parcha/lab/reask_bench.py`, synthetic speech): main run 1,000 rows, held-out run 930 rows. Single re-ask recovers 96–97% but wrongly accepts about 2.3% (rejected). Two agreeing recordings settle 93–95% of pairs with 0.2–0.4% wrong, all at 0 dB; clean and control: 0 wrong in 1,158 pairs.
- Known confusion that two recordings cannot fix: ₹31,000 heard as ₹21,000 (इकतीस/इक्कीस) in both voices at G.711/AMR 0 dB.
- Read-back default: Vikrant + `words`, closing prompt "Kuch galat ho toh bataiye." (`src/parcha/readback.py`).
- Deployment files exist and the image builds and serves `/health`, `/workshop`, `/stage`: `Dockerfile`, `docker-compose.yml`, `render.yaml`, `docs/deploy.md`.
- Owner-take tooling exists: `scripts/make_owner_recorder.py`, `scripts/register_owner_takes.py`, `docs/owner-recording.md`. The takes themselves do not exist yet.

---

# PART A — Agent tasks

## A1. Whole-estimate repeat (removes the "say it again per amount" friction)

**Problem.** Every flagged amount needs its own second recording. A live demo shows several "say it again" beats.

**Do.**
1. Read `src/parcha/workflow.py` (`intake`, `reask`, `_reask_amount`, `_require_agreeing_recordings`), `src/parcha/money.py` (`settle_card_amounts`, `spoken_item_order`), `src/parcha/app.py` (`/intake`, `/reask` routes), `src/parcha/static/app.js`, `ui.js`.
2. Add `Workflow.confirm_estimate(session_id, blob, mime, expected_revision)`: run both Prisma passes on the new recording, extract amounts per item in spoken order (reuse `spoken_item_order` and `decide_amounts`), and for each item currently flagged compare against its stored candidate quote. Settle an item only when both agree; leave the rest flagged with the right reason (`recordings_disagree` or `independent_confirmation_required`). Do not touch items that are already settled. Revision rules apply: require `expected_revision`, bump the revision, log a `confirm_estimate` transcript entry with the audio hash.
3. Add a route `POST /sessions/{id}/confirm-estimate` in `app.py` (validation and errors only; logic stays in `workflow.py`). Add a single top-of-slip mic button "पूरा पर्चा दोबारा बोलें / Say the whole estimate again" in the workshop UI, shown while any amount is flagged; keep the per-row buttons.
4. Show progress such as "1 of 2 heard" under each flagged amount.
5. Tests: both amounts agree → both settle; one item disagrees → only that one stays flagged; item order differs from the first recording; empty or provider-error recording; stale revision → 409; confirmed session → immutable. One offline e2e: speak once, speak again, read-back becomes available.

**Benchmark (live, full size).** Extend `src/parcha/lab/reask_bench.py` with multi-amount utterances (2–4 amounts per utterance, same colloquial rendering), conditions as today (`control`, `g711|clean`, `g711|0`, `amr_nb_4750|clean`, `amr_nb_4750|0`), two voices, a held-out seed. Report settled rate, wrong-settled count with Wilson upper bound, and recordings needed per estimate. Record results in `docs/gates.md`.

**Done when.** Offline suite and e2e green; benchmark shows 0 wrong settled on clean and control conditions; the demo path (speak, repeat once, read-back) needs two recordings per estimate regardless of item count.

## A2. Guard look-alike numbers at low SNR

**Problem.** At 0 dB, both recordings can agree on a consistently confused value (₹31,000 heard as ₹21,000). 6 wrong settles across 1,930 benchmark pairs, all at 0 dB.

**Do.**
1. Build the confusable set from data: replay `var/lab/reask_recovery.jsonl` and `var/lab/reask_heldout.jsonl` through `parcha.lab.reask_bench.rescore`/`paired_outcomes` (free, offline) and list every settled-wrong pair. Add the standard look-alike pairs (इकतीस/इक्कीस, तैंतालीस/पैंतालीस, अस्सी/अड़तीस, and 13/30, 14/40, 15/50, 16/60, 17/70, 18/80, 19/90 spoken forms).
2. In `money.py`, add a pure function that flags a settled amount as `confusable` when any of its number words is in the set. Surface the flag in the session payload.
3. For a flagged amount, require one more step before it can count as settled: read the settled value back to the mechanic through Timbre ("इकतीस हज़ार — सही?") and accept only a clear yes, or require a third agreeing recording. Pick the one that needs fewer code paths and document the choice in the AIDLC effort state.
4. Optional: estimate SNR of the recording (`parcha.audio` has SNR helpers) and apply the same extra step when SNR is below about 5 dB.
5. Tests: each known failure is routed to the extra step; a normal amount (₹450, ₹1,200) is not; the extra step cannot be skipped by the API.

**Measure.** Offline replay first: all 6 known wrong settles must be caught, and fewer than about 5% of correct settles newly flagged. Then one live run on fresh amounts (`--held-out --seed` new value) with the guard on.

**Done when.** The replay above passes, a fresh live run has 0 wrong settles at every condition including 0 dB, and `docs/gates.md` records the residual risk honestly (the customer read-back and audit trail remain the final check).

## A3. Score the owner takes (blocked until Part B item B1 is done)

**Precondition.** `var/benchmark_audio/owner/takes/` contains recordings (o001…o080) and the human has confirmed they are done. If not, stop and report; do not synthesize substitutes.

**Do.**
1. `.\.venv\Scripts\python.exe scripts/register_owner_takes.py` → `var/benchmark_audio/owner/manifest.jsonl`.
2. Dry-run, then run the amount runner on the owner manifest using the exact command in `docs/superpowers/plans/2026-10-05-money-path-safety.md` Task 14 Step 2 (`--manifest var/benchmark_audio/owner/manifest.jsonl --audio-root var/benchmark_audio/owner --output var/lab/v2_owner.jsonl`, codecs `g711,amr_nb_4750`, SNRs `clean,0`, modes `transcribe,verbatim`, spacing 1 s, bias words as in that step). Add `--live`.
3. Score with Task 14 Step 5 (`parcha.lab.money_eval` with the owner results and manifest). Also run the new re-ask logic on the owner takes: take each card's spoken amounts as the first recording and use A1's whole-estimate repeat only if the human supplied a second take; otherwise report single-take candidate rates only.
4. Report in `docs/gates.md`: N clips, one speaker, wrong-accepted with a Wilson upper bound, candidate rate, per-condition table. Add a README line only if the numbers support it.
5. Run `parcha.lab.bench_report` to refresh `var/lab/benchmark_report.md` (private).

**Done when.** `docs/gates.md` has a dated row for the owner slice, the plan's Task 14 Step 2 and Step 5 checkboxes are updated, and nothing about the speaker or audio is committed.

## A4. Fix or drop the YouTube annotations

**Problem.** `var/benchmark_audio/youtube_mechanic_benchmark.json` item prices for videos 003 and 004 were never spoken (the speaker gives a total or ranges), so scoring against them is invalid; only 001 and 002 match the speech.

**Do.** In `scripts/benchmark_youtube_samples.py`, remove or mark `"speech_grounded": false` on the unspoken amounts, make `scripts/run_youtube_eval.py` skip ungrounded amounts, update `tests/test_youtube_eval.py`, and rerun `scripts/run_youtube_eval.py --live` (about 900 credits). Do not claim a rate from this set; it stays a sanity check.

**Done when.** The report only counts speech-grounded amounts and `docs/gates.md` says so.

## A5. Package the Hinglish story for the Mixed Vibes award

**Do.** Add a short README section and a one-page `docs/benchmarks/hinglish-amounts.md` with: the colloquial forms handled (डेढ़, ढाई, साढ़े, सवा, पौने, बारह सौ), the transcribe-format normalisation, and the measured effect (re-ask recovery 73.3% → 96.3% on 1,000 live rows; held-out 96.8%), with the single-re-ask rejection and the two-recording rule explained in plain words. No new credits. Every number must trace to a `docs/gates.md` row.

**Done when.** Each figure in the new page links to its gates row.

## A6. Deployment support (after the human deploys, see B2)

**Do.** Given the public URL from the human, run a read-only smoke test: `GET /health`, `/workshop`, `/stage` return 200; the page loads `ui.js` and `parcha.css`; no secret appears in any response. If a failure is found, fix it in the repo (not by weakening checks) and tell the human what to redeploy. Never ask for or print keys.

## A7. Keep records current

After each task above: update `docs/gates.md` (dated rows with command, output path, N, estimated spend), `aidlc-docs/efforts/009-money-path-plan/effort-state.md`, the plan checkboxes, and `HANDOFF.md` (untracked or tracked, keep it short). Then the full offline suite, `git diff --check`, scoped commit, push.

---

# PART B — Human-only tasks (the agent must not do or simulate these)

- [ ] **B1. Record the 80 owner takes (~60–90 min).** Run `.\.venv\Scripts\python.exe scripts/make_owner_recorder.py`, open `var/owner_recorder.html` in Chrome, choose `var/benchmark_audio/owner/takes`, and speak each card in your own words near a running scooter or fan (dedh, dhai, saade, sava, barah sau). Don't read digits aloud. Tell the agent when done. Details: `docs/owner-recording.md`.
- [ ] **B1b. (Strongly recommended) 3–5 more speakers, 20 cards each,** with written consent: a real mechanic, a woman, an older speaker. One accent is the main criticism of a single-speaker result. Use the same recorder; keep the files private under `var/`.
- [ ] **B1c. Human listening labels (~45 min).** Listen to every failed row and a 10% sample of passes from the echo runs and enter labels in `var/lab/echo_labels.csv` (`timbre`, `line` or `prisma`). Do not let the agent fill these in.
- [ ] **B2. Deploy (~45–90 min).** Render → New → Blueprint → select the repo. Set secrets in the dashboard: `API_KEY`, `EXTRACTOR_BASE_URL` (must be reachable from the host, not localhost), `EXTRACTOR_API_KEY`, `EXTRACTOR_MODEL`. Use a paid instance so it never sleeps, run one instance, then open `https://<service>.onrender.com/stage` on a real phone, grant the microphone, and complete one estimate. Send the URL to the agent for A6.
- [ ] **B3. Permissions (~15 min of effort, reply time is outside your control).** Email `contact@gramvaani.org` asking written permission to report Gramvaani evaluation results; message the organizers (plan Task 0 Steps 2–3). Until a reply is recorded in `aidlc-docs/efforts/009-money-path-plan/effort-state.md`, every Gramvaani figure stays private.
- [ ] **B4. Console facts (~5 min).** Read the real credit balance and where the extra keys came from in the Gnani console and give them to the agent for the effort log (plan Task 0 Step 1).
- [ ] **B5. One real user.** Ask one real mechanic (with consent) to try the deployed app for ten minutes; give the agent a short quote. Do not put customer data in the repo.
- [ ] **B6. Demo video (~30 min).** A 60-second screen recording on the deployed URL, including one failure and recovery (for example a noisy amount that needs the second recording). Keep it as the fallback if venue Wi-Fi fails.

## C. Suggested order

1. B1 (record takes) and B2 (deploy), in parallel with the agent doing A1 and A2.
2. A3 as soon as B1 is done; A6 as soon as B2 is done.
3. A4, A5, A7 any time.
4. B1c, B3, B4, B5 any time; B6 last.

## D. Award positioning (decide with the human, then update `docs/ideas/spec.md`)

- **Noise Canceller:** use the owner takes (the human's own real noisy audio, no third-party permission needed) run clean and through the G.711 and AMR-NB simulation at several SNRs; report only matched relative changes (the `src/parcha/lab/report.py` guards enforce this). Do not use Gramvaani numbers publicly without B3.
- **Mixed Vibes:** A5.
- **Real Deal:** needs B5; otherwise state "no named real user yet".
- Update the "Awards and positioning" section only to awards that have an evidence row.

## E. Out of scope

Re-running the finished synthetic benchmarks; single-recording acceptance rules; Gramvaani re-runs (transcripts do not change with decision-logic edits, and the set has no rupee labels); chasing 100% on 0 dB synthetic speech.
