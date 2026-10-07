# sug.md — what still holds Kaam ka Parcha back, and what it costs to fix

Status as of 2026-10-07 (`main` at `bf00604`). Evidence for every number below is in `docs/gates.md`.
"Me" = what Claude can do in a session. "You" = needs the owner (a voice, a decision, an account, a person).

## Cost at a glance

| # | Problem | You | Me | Credits | Fixes how much |
|---|---|---|---|---|---|
| 1 | No real-speech accuracy number | 2–3 h | 2–3 h | ~1,500–3,000 | The biggest gap; turns "synthetic" into "real" |
| 2 | Flow feels slow (two recordings per amount) | 10 min to choose | 5–8 h | ~500 | Demo feels fast, safety unchanged |
| 3 | Wrong amounts still settle at 0 dB | none | 3–5 h | ~300 | Removes the one visible failure |
| 4 | Not deployed | 45–90 min | 1 h support | 0 | Judges can try it |
| 5 | Weak award fit | 1–2 h + emails | 2–3 h | 0–600 | Pick the award you can actually defend |

Total: roughly **half a day of your time and about a day and a half of mine**, in the order in section 6.
Credit figures are runner estimates at 0.2 credits per audio second (Prisma) and 0.05 per character (Timbre), not console billing.

---

## 1. No real-speech accuracy number

**Problem.** Every measured result is Timbre (synthetic) speech or public audio with no rupee labels. Gramvaani has no
amount labels and no publication permission. The YouTube set is a sanity check only: for 3 of 5 videos the annotated prices
were never spoken, so it cannot give a rate. A judge who asks "how accurate on a real mechanic?" gets no number.

**Fix: the owner takes (already built).**
1. `.\.venv\Scripts\python.exe scripts/make_owner_recorder.py`, open `var/owner_recorder.html` in Chrome, pick `var/benchmark_audio/owner/takes`.
2. Record the 80 cards in your own words (dedh, dhai, saade, sava, barah sau), near a running scooter or fan. About 60–90 min.
3. `scripts/register_owner_takes.py`, then run the runner on the owner manifest (plan Task 14 Step 2) and `parcha.lab.money_eval` (Step 5).
4. Report with Wilson upper bounds, as one speaker, and say so.

**Make it stronger (each adds credibility):**
- **3–5 more speakers with written consent** (a real mechanic, a woman, an older speaker). Same recorder, same cards. One accent is the main criticism of any single-speaker result. 20 cards each is enough.
- **Human listening labels.** Listen to every failed row and a 10% sample of passes, enter them in `var/lab/echo_labels.csv`. About 45 min. This replaces my model verdict with a real one.
- **Fix the YouTube annotations** or drop them: re-annotate 001/002/005 by listening, and delete 003/004 amounts that were never spoken.

**Acceptance.** `docs/gates.md` has a dated row: N real clips, speakers, wrong-accepted count with an upper bound, recovered-after-confirmation rate, and the sentence "real, single/multi-speaker, not Gramvaani".
**Risk.** The real number may be worse than synthetic. That is still better than not having one; the design already fails closed.

---

## 2. The flow feels slow

**Problem.** A flagged amount settles only when two consecutive recordings agree (`independent_confirmation_required`, `recordings_disagree`). In a live demo that is one "say it again" per amount. The first recording is a candidate for about 66% of amounts, so a re-ask usually finishes it, but a two-item estimate still means three recordings in front of judges.

**Rejected, with numbers (do not revisit without new data):** accepting when the two Prisma passes on one recording agree. On the saved runs that accepts 475 of 1,344 amounts and 4.0% of those are wrong (10.2% at 0 dB).

**Fix A (recommended): one repeat for the whole estimate, not one per amount.**
Add a "repeat the whole estimate once" action. The second recording is run through the same extraction; each item's amount is compared to the candidate from the first recording, item by item (the label evidence already gives item order). Amounts that agree settle; the rest stay flagged.
- Safety is unchanged: still two independent recordings agreeing per amount.
- Demo: speak, then say it again once, and every amount is settled in two takes.
- Work: a `Workflow.confirm_estimate()` path in `workflow.py`, a route in `app.py`, a button in `ui.js`/`workshop.html`, tests (including a disagreement on one item only), one e2e. 5–8 h.
- Measure: reuse `scripts/run_reask_bench.py` with multi-amount utterances. About 500 credits.

**Fix B (cheap, UI only): make the wait feel earned.** Show "1 of 2 heard" under each amount, show the heard words (already shipped), and a single "say all amounts again" mic at the top of the slip. 1–2 h.

**Fix C (demo craft, no code):** rehearse with clear audio; clean conditions recovered every row (600/600) in the re-ask benchmark, so a quiet room makes the second recording a formality.

**Not recommended:** letting the customer's read-back count as the independent check. It moves the check onto a person who may not listen carefully and changes what "wrong amount confirmed" means in `docs/specs/money-path-safety-spec.md`. If you want it, it is a spec change first, not a patch.

**Acceptance.** A demo script where one estimate with 2–3 amounts is fully settled in two recordings; test and e2e green; benchmark shows 0 wrong on clean audio.

---

## 3. Wrong amounts still settle at 0 dB

**Problem.** Held-out run: 2 of 930 pairs settled wrong (0.2%), both at G.711 0 dB; main run: 4 of 1,000 (all one amount, ₹31,000 heard as ₹21,000 in both voices). The cause is a consistent phonetic confusion, so two recordings agree on the same wrong value. Clean and control audio: 0 wrong in 1,158 pairs.

**Fix: guard the confusable numbers.**
1. Build a small confusable list from the failures (इकतीस/इक्कीस, तैंतालीस/पैंतालीस, अस्सी/अड़तीस, and the usual 13/30, 14/40, 15/50 pairs). Score a settled amount "confusable" when any of its words is on the list.
2. For a confusable amount, **read the settled value back to the mechanic in Timbre before sealing** ("इकतीस हज़ार — सही?") or require a third agreeing recording. This costs one extra beat only for those amounts.
3. Optionally add a cheap noise gate: estimate SNR from the recording and treat < ~5 dB as "noisy", requiring the extra confirmation.

**Work.** Rules in `money.py` with tests (5–8 cases), a flag in the payload, UI label, offline replay on `var/lab/reask_recovery.jsonl` and `reask_heldout.jsonl` (free), then a live confirmation run on fresh amounts (about 300 credits). 3–5 h.

**Acceptance.** Offline replay shows the 6 known wrong settles are all routed to the extra confirmation, with no more than a few percent of correct amounts newly flagged.
**Honest limit.** This reduces wrong settles; it cannot reach zero. Keep the customer read-back and the audit trail in the story.

---

## 4. Not deployed

**Problem.** No public URL. Judges cannot try it, and a live demo depends on venue Wi-Fi and a laptop.

**Fix (the repo side is done: `Dockerfile`, `docker-compose.yml`, `render.yaml`, `docs/deploy.md`; the container builds and serves `/health`, `/workshop`, `/stage`).**
1. Render → New → Blueprint → select the repo.
2. Set secrets in the dashboard: `API_KEY`, `EXTRACTOR_BASE_URL`, `EXTRACTOR_API_KEY`, `EXTRACTOR_MODEL` (`EXTRACTOR_PROVIDER=evon`, `TTS_VOICE=Vikrant` are in the blueprint).
3. Use a paid instance, not a free one that sleeps, so the first judge does not hit a cold start. Check current pricing before relying on a number.
4. Open `https://<service>.onrender.com/stage` on a phone, grant the microphone, and run one full estimate.
5. Keep a 60-second screen recording as the fallback if the venue network fails.

**Things to check.**
- `EXTRACTOR_BASE_URL` must be reachable from the host; `http://localhost:8080/v1` only works on your laptop.
- One instance, one worker: sessions are in memory and are lost on restart. Do not let it restart mid-demo.
- Never set `.env` in the image; use the platform environment.
- Keep demo data synthetic and keep the simulated-line and clipboard-copy disclosures visible.

**Acceptance.** A public HTTPS URL that completes speak → read-back → "haan" → sealed PDF on a real phone, plus the fallback video.

---

## 5. Weak award fit

**Problem.** `docs/ideas/spec.md` positioned the project for Noise Canceller and Mixed Vibes, but the defensible claim today is "Real Deal" with no named real users, and no noise claim can be made public because the Gramvaani telephone audio has no publication permission.

**Fix by award:**

- **Noise Canceller (best realistic upgrade).** The owner takes are *your own real noisy audio*: record them beside a running scooter. Run them clean and through the G.711 and AMR-NB phone simulation at several SNRs, then report only matched, relative changes (the `report.py` guards already enforce this). No third-party permission is needed. This is the same recording session as section 1, so the marginal cost is about 30 min of analysis.
- **Mixed Vibes (Hinglish).** Package what already exists: colloquial forms (डेढ़, ढाई, साढ़े, सवा, पौने, बारह सौ) and the fix that took re-ask recovery from 73.3% to 96.3% on 1,000 live rows, plus the held-out run. A one-page table in the README and one slide. 1–2 h, no new credits.
- **Real Deal.** Needs a named real user. Ask one real mechanic (with consent) to try it for ten minutes and quote them. Even one is far stronger than none. Do not put customer details in the repo.
- **Gramvaani numbers.** Email `contact@gramvaani.org` and the organizers (plan Task 0 Step 2–3) for written permission. It costs 15 minutes but the reply is outside your control; until then every Gramvaani figure stays private.

**Acceptance.** `docs/ideas/spec.md` "Awards and positioning" updated to the awards you can actually evidence, each with the exact table or slide that supports it.

---

## 6. Suggested order

1. **Today, ~2 h (you):** record the 80 owner takes. Everything else depends on this.
2. **Today, ~1 h (you):** deploy on Render and run one estimate on your phone.
3. **Next, 5–8 h (me):** section 2 Fix A (whole-estimate repeat), with benchmark.
4. **Next, 3–5 h (me):** section 3 confusable-number guard, offline first, then one live run.
5. **After takes exist, ~3 h (me):** score the owner takes, update `docs/gates.md`, README table, award positioning (section 5).
6. **Any time (you):** 45-min human listening pass; send the two permission emails; ask one mechanic to try it.
7. **Last:** 60-second demo video, rehearsed on the deployed URL.

If you can only do three things: **record the takes, deploy, and record the demo video.**

## 7. What not to spend time on

- Re-running the synthetic benchmarks. They are done and reproducible.
- A rule that accepts an amount on one recording. The data says it is unsafe.
- Polishing the README visuals further. They already come from a live run.
- Chasing 100% on 0 dB synthetic speech. The honest story is "fails closed, customer confirms".
