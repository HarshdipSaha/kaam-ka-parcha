# sug.md — what Kaam ka Parcha needs to become a contender (agent-ready)

Audience: a coding agent working in this repo, plus one human owner. **Part A is for the agent. Part B is for the human only**;
the agent must not attempt Part B, simulate it, or fake its outputs. Written 2026-10-07; `main` at `5b7d601`, 635 offline tests
passing. Contest deadline: **11:59 PM IST, 10 November 2026** (34 days from writing). Evidence for every project number quoted
here is in `docs/gates.md`; contest facts are quoted from the official pages listed in section 11.

---

## 0. Rules for the agent (read first, every session)

1. **Start of task.** Run `git status`, read `AGENTS.md`, `CONTEXT.md`, and then only the files named in the task you pick. Preserve unrelated work. Pick tasks in the priority order of section 9 unless the human says otherwise.
2. **Credits are not a constraint.** The owner has a large hackathon Gnani balance (about 235,000 credits reported, not console-verified) and will add more. Use the real `.env` keys and run live benchmarks at full size. Do not shrink samples, skip conditions, or stop to ask about spend for tasks in this file. Use the best Gnani models and options available.
3. **Guards stay on anyway.** Run each script's dry-run forecast first, pass `--max-credits` generously (for example 5000), and log estimated spend in `docs/gates.md` labelled "estimate, not console billing".
4. **Rate limits are the real constraint.** Use `--interval 1.0` or more, run one live job at a time, and resume rather than restart (runners skip finished rows). Two concurrent live jobs caused HTTP 429 before.
5. **Secrets.** Never print, log, commit or paste `.env` values, keys, endpoint hostnames of private services, or private audio. Outputs go under ignored `var/`. Never `git add .env` or anything under `var/`.
6. **Contest data rule (binding).** The organisers require: *"use synthetic data only. Do not put anyone's real phone number, account number, Aadhaar, PAN or recorded calls into your project or demo."* Acceptable: sample scripts, **self-recorded audio with consent**, generated fake identifiers. Never add recorded calls or third-party recordings to the repo, the demo, the video, or the submission text. See A0.
7. **Honest reporting.** The organisers say *"A demo that fakes a result will cost you more than one that shows an honest limitation."* Synthetic (Timbre) speech is not real-speech accuracy; label it. Update `docs/gates.md`, `aidlc-docs/efforts/009-money-path-plan/effort-state.md` and README numbers only from fresh, reproducible runs. Never invent human labels, owner recordings, user quotes, or engagement numbers. Name every model truthfully (the extractor is not Gnani Evon today; see section 2).
8. **Money rules from `AGENTS.md` still apply:** integer paise, unknown stays `None`, evidence tied to transcript, confirmed sessions immutable, no sealed artefact from an incomplete card, keep the telephony-simulation and clipboard-copy disclosures.
9. **Test-first, then verify.** Add a regression that fails for the observed problem, run focused tests, then `.\.venv\Scripts\python.exe -m pytest -q` (offline) and, for UI changes, `.\.venv\Scripts\python.exe -m pytest -q tests/e2e -m e2e` (offline fakes, zero credits). Run `git diff --check`.
10. **Commit.** Scoped commits on `main`, push without force, end messages with the attribution line the harness provides. Exclude `.env`, `var/`.
11. **Rejected ideas — do not implement:**
    - Accepting an amount when the two Prisma passes on one recording agree. Saved runs: 475 of 1,344 amounts accepted, 4.0% of those wrong (10.2% at 0 dB).
    - Letting the customer read-back stand in for the independent amount check. That is a spec change (`docs/specs/money-path-safety-spec.md`), not a patch.
    - Integrating Gnani Warp (speech-to-speech). It is not in the contest's model list or the public API docs.
    - Real telephony (real phone calls / real numbers). It conflicts with the data rule; keep the disclosed in-browser simulation.

## 1. Contest facts that drive priorities

| Fact (official wording where quoted) | What it means for this project |
|---|---|
| Shortlist: *"Verified engagement on your nominated posts, recorded by the closing cutoff"*; selection mail: *"selecting the team on the bases of popular engagement on LinkedIn or X"* | The **internship** depends on public posts, not only on code quality. Posts must go out early so engagement accumulates before 10 Nov. Nominating posts in the submission form is required; *"tagging alone"* is not enough. |
| *"Your skills and your interview decide the offer."* Interviews are individual. | The owner must be able to explain every design decision and number. See A13 (interview brief). |
| Submission: working demo or video, written explanation, Gnani models/APIs used, each member's contribution, links to nominated posts with **#GnaniAI** and **#GreatIndianAIInternshipChallenge** | A13 prepares all text; the human posts and submits. |
| Ten awards, ₹50,000 each; *"Each team or individual can win a maximum of one award."* Awards are judged *"irrespective of internship selection."* | Optimise for one primary award, but the evidence should qualify for two or three so judges can place it. See section 4. |
| Crowd Favourite excludes *"purchased votes, bots and engagement exchanges."* | No engagement pods or paid boosts; organic only. |
| Data rule (section 0, rule 6) | Gramvaani recorded calls and YouTube creators' voices must stay out of the project, demo and video. See A0. |
| Strong entries *"start with an Indian problem, an Indian language and real Indian audio, then ship a working app."* | Real audio must be the owner's own consented recordings (B1) or a licensed corpus (IndicContextEval, CC BY 4.0). |
| Gnani public APIs: STT REST (**up to 60 s**), STT Realtime (WebSocket), STT Batch, TTS REST/SSE/WebSocket, **Voice Cloning**, 10 language codes (`bn, en, gu, hi, kn, ml, mr, pa, ta, te`-IN). No hosted Evon/LLM endpoint is documented. Evon v3.3 weights are Apache-2.0 on Hugging Face (30B, ~3.5B active, vLLM ≥ 0.12, ~60–80 GB GPU at full context). | We use REST STT + REST TTS only. Unused: Realtime STT (live captions), voice cloning, other languages, the 60 s limit. Evon is not used today (see section 2). |

## 2. Current state (facts to build on)

**Product.**
- Amount rule: a flagged amount settles only when two consecutive recordings agree (`independent_confirmation_required`, `recordings_disagree`; `Workflow._require_agreeing_recordings` in `src/parcha/workflow.py`). Heard quotes are stored as zero-score evidence and shown on flagged rows.
- Transcribe-pass fraction formats (`04:30 ₹100`, `साढ़े 4,000`, `03:30 हज़ार`, `ढाई ₹100`, `पौने ₹200`) are normalised before the cross-check (`normalise_transcribe_fractions` in `src/parcha/money.py`).
- Read-back default: Timbre voice **Vikrant**, amounts in Hindi **words**, closing prompt "Kuch galat ho toh bataiye." (`src/parcha/readback.py`).
- UI: Hindi-first workshop/customer/verify pages, one-screen `/stage` view, EN | हिं toggle (`src/parcha/templates/`, `src/parcha/static/`).
- **Extractor: the live `.env` uses an external OpenAI-compatible LLM (`EXTRACTOR_PROVIDER` is not `evon`). Gnani Evon is NOT used in practice.** `render.yaml` and `.env.example` claim Evon defaults that are not reachable without self-hosting. The README caption was corrected on 2026-10-07; the submission text must say this honestly unless A8 is done.
- Deployment files exist and the image builds and serves `/health`, `/workshop`, `/stage`: `Dockerfile`, `docker-compose.yml`, `render.yaml`, `docs/deploy.md`. **Not yet deployed. No abuse protection yet** (a public URL would let anyone spend API credits; see A12).
- Repo visibility: **private** (`HarshdipSaha/kaam-ka-parcha`).

**Evidence.**
- Re-ask benchmark (synthetic speech, `scripts/run_reask_bench.py`): main 1,000 rows + held-out 930 rows. Single re-ask 96–97% recovered but ~2.3% wrong (rejected). Two agreeing recordings: 93–95% settle at the first pair, 0.2–0.4% wrong, all at 0 dB; clean and control: **0 wrong in 1,158 pairs**.
- Read-back echo (synthetic): Vikrant/words 120/120 on control, G.711 and AMR-NB 4.75 at 0 dB.
- Hinglish forms: re-ask recovery rose from 73.3% to 96.3% after the fraction fix (1,000 live rows); held-out 96.8%.
- Known confusion two recordings cannot fix: ₹31,000 heard as ₹21,000 (इकतीस/इक्कीस) at 0 dB.
- Real speech: **no labelled real workshop speech yet** (owner takes not recorded).

**Audio assets and their legal status.**

| Asset | Where | Status under the contest data rule | Use |
|---|---|---|---|
| Timbre synthetic speech (estimates, corrections, stress, echo) | `data/benchmarks/amount_v2/`, `var/` | Synthetic. Allowed. | Public evidence, labelled synthetic. |
| AI4Bharat IndicContextEval, 120 Hindi clips (read + extempore, code-mix flag), CC BY 4.0 | `data/benchmarks/real_audio_2026-10/` (committed), results in `var/lab/real_audio_results.jsonl` | Licensed real speech, not calls. Allowed with attribution. | Real-speech robustness story (A14), relative deltas only. |
| Gramvaani telephone recordings | index committed at `data/benchmarks/gramvaani/index.jsonl`; audio and results under `var/` | **Recorded calls. Must not be in the project or demo.** | Remove from repo and submission (A0). Internal history only. |
| YouTube mechanic videos | audio under `var/`; URLs and spoken quotes committed in `scripts/benchmark_youtube_samples.py`; scorer `scripts/run_youtube_eval.py` | Third-party voices, no recorded permission. | Remove creator quotes/URLs from the repo; never in demo or video (A0). |
| Owner takes | not recorded yet (`var/benchmark_audio/owner/takes/`) | Self-recorded with consent. Allowed. | The real-speech headline (A3). |

## 3. Gap analysis: contender bar vs today

| What a contender needs | Today | Gap | Tasks |
|---|---|---|---|
| Public posts with real engagement by 10 Nov | None | **Critical** (decides the shortlist) | B7, A13 |
| A public, working demo | Runs locally and in Docker | Deploy + abuse protection | A12, B2, A6 |
| 60-second video | None | Needed for submission and Demo Day Drop | A13 (script), B6 |
| Written explanation, models, contributions | Scattered across docs | Must be one clear document | A13, B8 |
| Built on Gnani models | Prisma + Timbre yes; Evon claimed but not used | Honesty risk, weaker "Gnani stack" story | A8 |
| Real-speech evidence | Synthetic + licensed corpus (unpublished) | No labelled real workshop speech | B1, A3, A14 |
| Data-rule compliance | Gramvaani index and YouTube quotes in repo | Must be removed before any public link | A0 |
| Smooth demo | Two recordings per flagged amount | Feels slow on stage | A1 |
| Low-SNR safety | 0.2–0.4% wrong at 0 dB | One visible failure class | A2 |
| Interview readiness | Owner knows the project | Needs a crisp brief with numbers | A13 |
| Wider award fit | Hindi only, REST only | Optional extras | A9, A10, A11 |

## 4. Award strategy (one award maximum; build evidence for 2–3)

| Award | Fit | Evidence we have / can get | Likely competition | Verdict |
|---|---|---|---|---|
| **Mixed Vibes** (code-mixed voice) | Strong: Hinglish rupee amounts (डेढ़, ढाई, साढ़े, सवा, पौने, बारह सौ) end to end | Measured 73.3% → 96.3% fix; held-out 96.8%; two-recording safety; IndicContextEval has a code-mix flag | Many Hinglish chat/voice apps, few with measured numeral handling | **Primary target.** A5, A10 (Tanglish/Benglish read-back strengthens it). |
| **Real Deal** (most useful real-world problem) | Good: verbal repair estimates are disputed daily; Gnani sells into Automobile | Needs one real mechanic using it (B5) and the owner takes (B1) | Farmer, kirana and health tools (the named examples) | **Secondary.** Only credible with B5. |
| **Demo Day Drop** (best 60-second video) | Good story: speak → customer hears → "haan" → sealed slip | Live screenshots exist; needs the video | Every entrant makes a video | **Secondary**; craft matters more than code (B6, A13 storyboard). |
| **Jugaad Genius** (creative use of Gnani models) | Timbre→Prisma echo loop to choose the read-back voice; Prisma two-pass cross-check; optional mechanic-voice cloning (A11) | Echo study done (Nalini ~57–65% vs Vikrant 120/120 on stress/confirm sets) | Unknown | **Tertiary**; tell the echo-loop story in posts. |
| **Noise Canceller** (messy, real telephonic audio) | Product leg is a simulated phone line; real telephone recordings are disallowed | Owner's own noisy takes through G.711/AMR-NB; IndicContextEval relative degradation | Teams with real call data are disallowed from using it too | Possible only after B1 + A14; do not lead with it. |
| **Main Character** (regional / low-resource language) | Weak unless the customer leg speaks another language | A10 adds Tamil/Kannada/Bengali read-back | Dedicated regional-language projects (e.g. Bhojpuri) | Not a target; A10 is mainly for Mixed Vibes. |
| **Solo Ninja / Two-Person Army / Small Town** | Depends on registration facts | B8 | — | Automatic consideration; confirm facts. |
| **Crowd Favourite** | Public votes | B7 | Social-media-savvy teams | Side effect of B7, not a target. |

## 5. Competition calibration (public repos seen on 2026-10-07)

Public entries found: a Bhojpuri voice experiment on Prisma/Timbre/Evon (161 tests, no accuracy measured, invite-only trial), an Indian-language call copilot (streaming STT, real API integration not yet run), and a farmers' voice desk (Prisma/Timbre). None publishes measured accuracy. **Our differentiators are measured safety and honest evidence**; lead with them, and do not undercut them with overclaims.

---

# PART A — Agent tasks

Priorities: **P0** = needed to submit credibly; **P1** = clearly raises award odds; **P2** = optional upside.

## A0. (P0) Data-rule and honesty audit — do this first

**Problem.** The repo contains a Gramvaani recorded-call index and YouTube creators' URLs and spoken quotes. The contest forbids recorded calls in the project or demo. The README and `render.yaml` previously implied Evon extraction.

**Do.**
1. Remove `data/benchmarks/gramvaani/index.jsonl` from the repo (`git rm`), and remove Gramvaani mentions from README, `docs/benchmarks/BENCHMARK_CARD.md` public sections, and any submission text. Keep a one-line note in `docs/gates.md` that an internal Gramvaani diagnostic existed and is excluded under the contest data rule. Do not delete the ignored `var/` artefacts unless the human asks.
2. In `scripts/benchmark_youtube_samples.py`, remove the hard-coded video URLs, titles and creator transcript quotes (`spoken_context`, `quote`); make the script read a local, ignored manifest instead. Keep `scripts/run_youtube_eval.py` for internal use only, and state in `docs/gates.md` that this set is internal and not part of the submission.
3. Check `data/benchmarks/real_audio_2026-10/README.md`: it says to remove the evaluation exports before making the repo public. Keep the CC BY 4.0 audio and attribution; remove or redact the YouTube-derived rows from any committed `results`/`summary` files.
4. Grep the repo for real identifiers: phone-number-like digit runs, Aadhaar/PAN patterns, emails other than placeholders, vehicle plates that are not clearly synthetic. Keep `KA-01-AB-1234 (Synthetic Demo)`-style values only.
5. Make model naming truthful everywhere: README "Gnani AI models used", `render.yaml` comments, `.env.example`, `docs/deploy.md`. Until A8 lands: "Prisma v2.5 (STT), Timbre v2.5 (TTS); field extraction by an external OpenAI-compatible LLM".
6. Scan git history for secrets before any visibility change: `git log -p --all | Select-String -Pattern 'API_KEY=|gsk_|sk-'` (print only the commit id and file, never the match). If anything is found, stop and tell the human to rotate keys; do not rewrite history without explicit approval.

**Done when.** No recorded-call data or third-party voice text is tracked; every model claim matches the code path that runs; a short "Data and consent" section in the README explains what audio is used and why.

## A1. (P1) Whole-estimate repeat (removes the "say it again per amount" friction)

**Problem.** Every flagged amount needs its own second recording. A live demo shows several "say it again" beats.

**Do.**
1. Read `src/parcha/workflow.py` (`intake`, `reask`, `_reask_amount`, `_require_agreeing_recordings`), `src/parcha/money.py` (`settle_card_amounts`, `spoken_item_order`, `decide_amounts`), `src/parcha/app.py` (`/intake`, `/reask` routes), `src/parcha/static/app.js`, `ui.js`.
2. Add `Workflow.confirm_estimate(session_id, blob, mime, expected_revision)`: run both Prisma passes on the new recording, extract amounts per item in spoken order, and for each currently flagged item compare against its stored candidate quote. Settle an item only when both agree; leave the rest flagged with the right reason (`recordings_disagree` or `independent_confirmation_required`). Do not touch already-settled items. Require `expected_revision`, bump the revision, log a `confirm_estimate` transcript entry with the audio hash.
3. Add `POST /sessions/{id}/confirm-estimate` in `app.py` (validation and errors only). Add a top-of-slip mic button "पूरा पर्चा दोबारा बोलें / Say the whole estimate again", shown while any amount is flagged; keep the per-row buttons. Show "1 of 2 heard" under each flagged amount.
4. Tests: both amounts agree → both settle; one disagrees → only it stays flagged; different item order; empty or provider-error recording; stale revision → 409; confirmed session immutable. One offline e2e.

**Benchmark (live, full size).** Extend `src/parcha/lab/reask_bench.py` with multi-amount utterances (2–4 amounts, colloquial rendering), the five conditions (`control`, `g711|clean`, `g711|0`, `amr_nb_4750|clean`, `amr_nb_4750|0`), two voices, and a held-out seed. Report settled rate, wrong-settled with a Wilson upper bound, and recordings per estimate.

**Done when.** Suites green; 0 wrong settled on clean/control; the demo path needs two recordings per estimate regardless of item count.

## A2. (P1) Guard look-alike numbers at low SNR

**Problem.** At 0 dB both recordings can agree on a consistently confused value. 6 wrong settles across 1,930 benchmark pairs, all at 0 dB.

**Do.**
1. Replay `var/lab/reask_recovery.jsonl` and `var/lab/reask_heldout.jsonl` through `parcha.lab.reask_bench.rescore`/`paired_outcomes` (offline, free) and list every settled-wrong pair. Add standard look-alikes (इकतीस/इक्कीस, तैंतालीस/पैंतालीस, अस्सी/अड़तीस, and the 13/30 … 19/90 spoken forms).
2. In `money.py` add a pure function flagging a settled amount as `confusable` when any of its number words is in the set; surface it in the payload.
3. For a confusable amount, require one more step before it counts: either a Timbre read-back to the mechanic ("इकतीस हज़ार — सही?") accepting only a clear yes, or a third agreeing recording. Choose the one with fewer code paths and record the choice in the AIDLC effort state.
4. Optional: estimate SNR and apply the same step below ~5 dB.
5. Tests: each known failure is routed to the extra step; ₹450/₹1,200 are not; the step cannot be bypassed via the API.

**Done when.** Offline replay catches all 6 known wrong settles with < ~5% of correct settles newly flagged; a fresh held-out live run shows 0 wrong settles at every condition; residual risk recorded honestly.

## A3. (P0 once B1 is done) Score the owner takes

**Precondition.** `var/benchmark_audio/owner/takes/` has o001…o080 and the human confirmed they are complete. Otherwise stop and report; never synthesise substitutes.

**Do.**
1. `.\.venv\Scripts\python.exe scripts/register_owner_takes.py` → `var/benchmark_audio/owner/manifest.jsonl`.
2. Dry-run, then live: the amount runner per `docs/superpowers/plans/2026-10-05-money-path-safety.md` Task 14 Step 2 (owner manifest, `--audio-root var/benchmark_audio/owner`, `--output var/lab/v2_owner.jsonl`, codecs `g711,amr_nb_4750`, SNRs `clean,0`, modes `transcribe,verbatim`, 1 s spacing, bias words as in that step).
3. Score per Task 14 Step 5 (`parcha.lab.money_eval`). If the human recorded a second take per card, also score the two-recording rule and A1's whole-estimate repeat; otherwise report candidate rates only.
4. Report in `docs/gates.md`: N clips, one speaker (say so), wrong-accepted with a Wilson upper bound, candidate rate, per-condition table, the owner's own noise conditions. Refresh `var/lab/benchmark_report.md` with `parcha.lab.bench_report`.

**Done when.** Dated gates row exists, plan checkboxes updated, nothing about the speaker or audio committed.

## A4. (P2) YouTube set: internal only

Superseded by A0 for compliance. If kept for internal sanity checks, mark the amounts that were never spoken (videos 003 and 004) as `speech_grounded: false` in the local manifest and skip them in `scripts/run_youtube_eval.py`. Never cite this set publicly.

## A5. (P1) Package the Hinglish story (Mixed Vibes)

**Do.** Add `docs/benchmarks/hinglish-amounts.md` and a short README section: colloquial forms handled, the transcribe-format normalisation (with the real example "Prisma writes साढ़े चार सौ as 04:30 100"), the measured effect (73.3% → 96.3% on 1,000 live rows; held-out 96.8%), why single-recording acceptance was rejected (2.3% wrong), and the two-recording rule in plain words. Add the code-mixed vs monolingual split from IndicContextEval if A14 produces it. Every figure links to its `docs/gates.md` row. No new credits needed.

## A6. (P0 after B2) Deployment smoke test

Given the public URL from the human: `GET /health`, `/workshop`, `/stage` return 200; `ui.js` and `parcha.css` load; no secret, hostname of a private service, or stack trace appears in any response; the A12 limits are active (a burst of requests is refused). If a failure is found, fix it in the repo (never by weakening checks) and tell the human what to redeploy. Never ask for or print keys.

## A7. Keep records current

After each task: update `docs/gates.md` (dated rows: command, output path, N, estimated spend), `aidlc-docs/efforts/009-money-path-plan/effort-state.md` (or a new effort under `aidlc-docs/efforts/` with `registry.md` updated), plan checkboxes, and a short `HANDOFF.md`. Then the full offline suite, `git diff --check`, scoped commit, push.

## A8. (P0/P1) Run extraction on Gnani Evon v3.3

**Problem.** The submission must name the Gnani models used. Today extraction runs on an external LLM, so only two of the three contest models are in use, and docs implied otherwise.

**Do.**
1. Read `src/parcha/extract.py`, `src/parcha/config.py` (`extractor_*`), `tests/` for extractor fakes.
2. Serve Evon v3.3 with an OpenAI-compatible server: `vllm serve gnani/gnani-evon-v3.3 --trust-remote-code` (vLLM ≥ 0.12; ~60–80 GB GPU at full context, much less with `--max-model-len 8192`). Use non-thinking settings for structured output (`temperature` low or 0.6 per model card, `enable_thinking=false`, `max_tokens` ~2048). The GPU host comes from B9; never commit its address.
3. Point `EXTRACTOR_BASE_URL`/`EXTRACTOR_MODEL` at it via the environment only; set `EXTRACTOR_PROVIDER=evon`. Keep the existing fallback behaviour: if the extractor fails, fields stay reviewable (never invent).
4. Measure before switching: run the extractor offline over the saved transcripts in `var/lab/v2_estimates.jsonl` and `v2_corrections.jsonl` against the manifests' known items (labels, item count, delivery), for both the current external LLM and Evon. Report field accuracy per model in `docs/gates.md` (synthetic transcripts; say so). Amounts stay with the numeral grammar regardless of the LLM.
5. Update README "Gnani AI models used", `render.yaml`, `docs/deploy.md` (Evon endpoint must be reachable from the app host).

**Done when.** The deployed app extracts with Evon (or the README states clearly why not), and a measured comparison is recorded.

## A9. (P2) Live captions with STT Realtime (WebSocket)

**Do.** Use the existing `src/parcha/gnani_ws.py` to stream partial transcripts into the workshop page while the mechanic speaks (words appear live). Keep the REST two-pass decision for amounts unchanged; captions are display-only and never feed the money path. Offline tests with a fake socket; one live check. Also raise the REST chunk limit in `src/parcha/lab/runner.py` (`REST_MAX_AUDIO_SECONDS = 29.0`) only if a live test confirms the documented 60 s limit.

**Done when.** Live captions visible within about a second on the deployed URL; money path untouched (tests prove the captions cannot set an amount).

## A10. (P1) Customer read-back in the customer's language (Mixed Vibes / Main Character)

**Do.**
1. Let the customer page choose a language (start with `ta-IN` Tamil, `bn-IN` Bengali, `kn-IN` Kannada; Hindi stays default).
2. Read-back templates per language in `src/parcha/readback.py` with **digit-style amounts** (Timbre handles numerals and lakh/crore cadence), the statutory consent line, and an affirmation prompt per language. No machine translation of amounts; templates are fixed strings reviewed by the human (B8).
3. Reply classification words per language in `classify_reply` (yes/no/ok forms, e.g. Tamil "ஆமா", "சரி", "இல்லை"), with negation priority as today; unclear stays unclear.
4. Prisma `language_code` for the customer reply follows the chosen language.
5. Echo benchmark per language (live, full size): extend `scripts/run_echo_test.py` with a language axis and Timbre voices for that language; report pass rates on control, G.711 and AMR-NB 0 dB. Pick the best voice per language as done for Hindi.

**Done when.** A Tamil (or Bengali) customer can hear the estimate and confirm by voice end to end, with measured echo pass rates in `docs/gates.md`.

## A11. (P2, Jugaad) Read-back in the mechanic's own voice (voice cloning, consent-gated)

**Do.** Using Gnani's voice-cloning embeddings endpoint, let the owner (only the owner, with recorded consent) create a voice profile from a self-recorded sample and use it for the read-back. Show "आवाज़: मिस्त्री की क्लोन आवाज़ (सहमति से) / Cloned voice, with consent" on the call card. Run the echo test with the cloned voice and compare to Vikrant; ship it only if it is not worse. Never clone anyone else; never store the sample in the repo.

**Done when.** Measured echo comparison recorded; disclosure visible; default stays Vikrant unless the cloned voice measures at least as well.

## A12. (P0 before B2) Public-demo hardening

**Problem.** A public URL would let anyone call Prisma/Timbre on the owner's keys and fill memory.

**Do.**
1. Per-IP rate limits on `/intake`, `/reask`, `/readback`, `/reply`, `/sessions` (for example 10 requests/minute/IP), returning a friendly 429 the UI already understands.
2. Hard caps: upload size, audio duration (≤ 60 s, matching the STT limit), sessions per IP, total sessions (the untouched-session cap already exists in `SessionStore`).
3. Optional demo access code (env `DEMO_ACCESS_CODE`; when set, a small gate page sets a cookie). Off by default locally.
4. Generic error bodies (no stack traces, no upstream URLs); log server-side only.
5. Run the `security-review` skill on the diff; fix findings.

**Done when.** Tests for each limit; a burst test returns 429 without calling the speech fakes; README/deploy docs describe the limits.

## A13. (P0) Submission package, posts, video script, interview brief

**Do (drafts only; the human edits, posts and submits).**
1. `docs/submission/explanation.md` (≤ 1 page): problem (verbal repair estimates disputed daily), who uses it (two-wheeler/car workshops and their customers), how it works, **exact Gnani models and endpoints used** (Prisma v2.5 STT REST, both `transcribe` and `verbatim` formats with bias words; Timbre v2.5 TTS voice Vikrant; Evon only if A8 is done), what is measured (with gates links), honest limitations (synthetic-speech evidence, one-speaker owner takes, simulated phone line, clipboard WhatsApp), data and consent. Leave "each member's contribution" as a placeholder for the human.
2. `docs/submission/posts.md`: 4 post drafts (LinkedIn long form + X short form each), with both hashtags and placeholders for the video/screenshot links:
   - Launch: the problem and a 20-second clip.
   - Behind the build: "Gnani Prisma writes साढ़े चार सौ as 04:30 100 — here is how we made Hinglish rupee amounts safe" (the fraction fix, 73.3% → 96.3%).
   - Jugaad: the Timbre→Prisma echo loop that picked the read-back voice (Nalini vs Vikrant).
   - Real user: a mechanic trying it (only if B5 happens; otherwise a self-recorded workshop clip).
   No engagement-exchange requests; no claims beyond `docs/gates.md`.
3. `docs/submission/video-script.md`: a 60-second storyboard with shot list, on-screen Hindi + English captions, voice-over lines, and timings (0–5 s hook: "₹450 bola tha, ₹900 likh diya?"; 5–40 s live flow on the deployed `/stage`; 40–55 s one failure and recovery; 55–60 s models used + hashtags). Must show the simulated-line disclosure.
4. `docs/submission/interview-brief.md`: architecture diagram (text), the money-path decisions with their numbers, why single-recording acceptance was rejected, how the benchmarks were built and their limits, what you would do with more time, and 15 likely interview questions with short answers.

**Done when.** All four files exist, every number links to `docs/gates.md`, and nothing in them violates the data rule.

## A14. (P1) Licensed real-speech robustness (IndicContextEval, CC BY 4.0)

**Do.** From the existing `var/lab/real_audio_results.jsonl` (2,000 rows: 120 licensed clips plus 5 YouTube-source clips), exclude the YouTube rows and compute **relative** degradation of the transcript-quality metrics from clean to 10/5/0 dB under G.711 and AMR-NB, and split by the code-mix flag. Respect `src/parcha/lab/report.py`: no absolute CER/WER publicly, no competitor comparisons, and a recorded organizer consent reference before any public lab report (B3). If the run needs refreshing, re-run live at full size with 1 s spacing. Attribute AI4Bharat in every place the numbers appear.

**Done when.** A guarded report exists under `var/lab/` and, after B3, a public summary with attribution.

## A15. (P2) Mobile and accessibility pass

**Do.** Playwright on 360×800 and 390×844 with network throttled to "Fast 3G": time-to-first-interaction, audio playback, mic flow. Check colour contrast and focus order on all pages, Hindi font rendering, and the CSS+JS budget (currently ~69 KB vs the UI spec's 60 KB). Fix what is cheap; record the rest.

---

# PART B — Human-only tasks (the agent must not do or simulate these)

- [ ] **B1. Record the 80 owner takes (~60–90 min).** Run `.\.venv\Scripts\python.exe scripts/make_owner_recorder.py`, open `var/owner_recorder.html` in Chrome, choose `var/benchmark_audio/owner/takes`, and speak each card in your own words near a running scooter or fan (dedh, dhai, saade, sava, barah sau). Don't read the digits aloud. Ideally record each card twice so the two-recording rule can be scored on real speech. Tell the agent when done. Details: `docs/owner-recording.md`.
- [ ] **B1b. (Strongly recommended) 3–5 more speakers, 20 cards each,** with written consent (a real mechanic, a woman, an older speaker). Keep files private under `var/`. One accent is the main criticism of a single-speaker result.
- [ ] **B1c. Human listening labels (~45 min).** Every failed echo row and a 10% sample of passes; labels `timbre`, `line` or `prisma` in `var/lab/echo_labels.csv`.
- [ ] **B2. Deploy (~45–90 min, after A12).** Render → New → Blueprint → select the repo. Set secrets in the dashboard (`API_KEY`, `EXTRACTOR_BASE_URL` reachable from the host, `EXTRACTOR_API_KEY`, `EXTRACTOR_MODEL`, optional `DEMO_ACCESS_CODE`). Use a paid always-on instance, one instance only. Open `/stage` on a real phone, grant the microphone, complete one estimate. Send the URL to the agent (A6).
- [ ] **B3. Permissions (~15 min of effort).** Email `contact@gramvaani.org` only if you still want Gramvaani mentioned anywhere (recommended: drop it instead, per A0). Ask the organizers on Discord for written OK to publish relative benchmark numbers from your own pipeline (needed by the `report.py` guard). Record replies in the effort state.
- [ ] **B4. Console facts (~5 min).** Real credit balance and the source of every key, for the effort log.
- [ ] **B5. One real user (~1 h).** One real mechanic (with consent) tries the deployed app for ten minutes; capture a short quote and, with permission, a photo or clip of their hands/phone (no faces or numbers needed). Never put customer data in the repo.
- [ ] **B6. Demo video (~2–3 h including retakes).** Follow `docs/submission/video-script.md` (A13). Exactly 60 seconds, captions on, the simulated-line disclosure visible, one honest failure and recovery. Record on the deployed URL; keep a local-run take as a fallback.
- [ ] **B7. Social campaign (critical for the shortlist).** Post the A13 drafts on LinkedIn and X with **#GnaniAI #GreatIndianAIInternshipChallenge**, tagging Gnani AI. Suggested cadence: launch post by ~15 Oct, build-story post ~22 Oct, Jugaad/echo post ~29 Oct, final demo post with the 60-second video by ~3 Nov (leaves a week of engagement before the cutoff). Reply to every comment; share in college and maker groups; ask mechanics you know to try it. **No bought engagement, bots or engagement-exchange groups.** Nominate the posts in the submission form.
- [ ] **B8. Contest facts and workspace (~30 min).** Confirm solo vs team of two (affects Solo Ninja/Two-Person Army and the contributions field), and whether your college/town is Tier 2/3 (Small Town award). Update the participant workspace (title, problem, users, models, contributions). Review the A10 language templates if A10 is done (native speaker check).
- [ ] **B9. GPU for Evon (decision + account).** Decide whether to self-host Evon v3.3 for A8 (a rented 80 GB GPU or a serverless GPU provider; check current pricing). If not, accept the honest wording "external LLM for extraction".
- [ ] **B10. Interview practice (~2 h).** Read `docs/submission/interview-brief.md`, explain the money path and the benchmarks out loud without notes, and be ready to show the code.
- [ ] **B11. Consent records.** Written consent from every extra speaker (B1b) and for any voice cloning (A11, owner only). Keep consents private, not in the repo.
- [ ] **B12. Repo visibility.** Decide whether to make the repo public for judges and interviewers. Only after A0 is done and the secret scan is clean.
- [ ] **B13. Submit by 10 Nov, 11:59 PM IST (aim for 8 Nov).** Video or demo link, written explanation, models used, contributions, nominated post links.

## 9. Priority order and timeline (34 days)

| Window | Agent | Human |
|---|---|---|
| Oct 7–12 | A0, A12, A13 drafts | B1 record takes, B8 facts, B9 decide on Evon |
| Oct 13–19 | A3 (score takes), A1, A8 if B9 = yes | B2 deploy, B7 launch post (~15 Oct), B1b extra speakers |
| Oct 20–26 | A6, A2, A5, A14 | B5 real mechanic, B7 build-story post (~22 Oct), B1c labels |
| Oct 27–Nov 2 | A10 or A9 (pick one), A15, refresh A13 with final numbers | B6 video, B7 Jugaad post (~29 Oct), B3 replies |
| Nov 3–8 | Final records (A7), freeze features, fix only bugs | B7 final demo post (~3 Nov), B10 interview practice, B13 submit by ~8 Nov |
| Nov 9–10 | Standby | Buffer only |

If time is short, the minimum contender set is: **A0, A12, A13, A3 + B1, B2, B6, B7, B13.**

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Low engagement → not shortlisted | Start posting by mid-October; post the build-story and Jugaad angles, not only the launch; engage organically. |
| Disqualification or penalty for data-rule breach | A0 before any public link; only synthetic, licensed or self-recorded consented audio anywhere. |
| Public URL burns credits | A12 before B2; access code if needed. |
| Live demo fails (network, mic, provider 429/503) | Recorded fallback take (B6); keep `/stage` warm; one instance; retry-friendly UI messages already exist. |
| Owner takes show worse numbers than synthetic | Publish them anyway with the fail-closed story; honesty is explicitly rewarded. |
| Evon self-hosting too expensive or slow | Keep the external LLM and state it plainly (B9); the amount path never depends on the LLM. |
| Overclaiming in posts | Every claim must map to a `docs/gates.md` row (A13 enforces links). |
| Last-minute breakage | Feature freeze from 3 Nov; only bug fixes with tests after that. |

## 11. Sources (checked 2026-10-07)

- Official programme page: https://www.gnani.ai/internship
- Official guide and rules (judging, data rule, submission): https://www.gnani.ai/resources/blogs/great-indian-ai-internship-challenge-2026
- Registration confirmation e-mail and programme text: `docs/response.txt`, `docs/abouthack.txt`
- Gnani API introduction (available endpoints, voice cloning): https://docs.gnani.ai/api/introduction/introduction
- Gnani STT REST parameters (60 s limit, language codes, `format`, bias, substitution): https://docs.gnani.ai/api/STT/speech-to-text
- Evon v3.3 model card (licence, serving, settings): https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B
- Gnani model overview (Warp is speech-to-speech; not in the contest list): https://www.gnani.ai/dev/models-v2
- Public competitor repos seen: https://github.com/sameer261h/boli-zero, https://github.com/krunalbaraskar/gnani, https://github.com/aniket25042005/kisan_setu_gnani_ai_challenge

## 12. Out of scope

Re-running finished synthetic benchmarks without a code change; single-recording acceptance rules; Gramvaani runs of any kind (contest data rule); Warp; real phone calls; chasing 100% on 0 dB synthetic speech; publishing absolute CER/WER.
