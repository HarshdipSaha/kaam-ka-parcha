# Optional Jev reply review

Jev provides advice when the current reply rules classify a customer transcript as `unclear`. A high-confidence recommendation can choose a more specific retry message. Advice never confirms a job card, edits amounts, selects a correction field, or changes the retry/fallback limit. The existing consent and expected-revision checks remain authoritative.

Enable locally with `JEV_REVIEW_ENABLED=1`, `TYPESAFE_API_KEY` (or `JEV_API_KEY`), `TYPESAFE_DEFAULT_MODEL=jev-1.13.0`, and `JEV_TIMEOUT_MS=20000`. With the flag off, no key, or mock mode, the application makes no Jev calls. A provider failure, malformed response, empty reply, or overlong reply abstains and retains the original retry behavior. Existing identifier masking is applied before external review.

Each attempted review records model, choice, confidence, probability distribution and latency in a `jev_review` system observation; unavailable reviews record an unavailable status. Observations are appended through SessionStore with current revision checks. Requests are synchronous and may delay an unclear reply by the configured timeout. There are no automatic paid retries in this integration.

## Reproduce the private text benchmark

From the repository root:

```powershell
.\.venv\Scripts\python.exe scripts/benchmark_jev_replies.py
.\.venv\Scripts\python.exe scripts/benchmark_jev_replies.py --live
```

The first command counts cases without loading credentials or calling the API. The live command evaluates 60 distinct synthetic Hindi, Hinglish and English replies across approval, correction, rejection and uncertainty. It compares fixed expected labels with rules and Jev; request/response evidence and summary are saved under ignored `var/jev_replies/<UTC-run>/`. Transport failures count as unsuccessful results rather than disappearing from the denominator.

These cases are a curated smoke test, not a representative customer distribution, held-out evaluation, calibration study, or speech benchmark. Read private results before choosing any future automation threshold. Do not infer speech or consent reliability from text classification results.

API contract: https://docs.typesafe.ai/introduction/quickstart

## Timbre v3 synthesis probe

```powershell
.\.venv\Scripts\python.exe scripts/benchmark_timbre_v3.py
.\.venv\Scripts\python.exe scripts/benchmark_timbre_v3.py --live --max-credits 100000
```

This separate synthesis runner uses v3 voices and inline pacing tags and stores raw 8 kHz mu-law audio and outcome logs under ignored `var/timbre_v3/`. Character-based credits are an estimate using the historical v2.5 rate, not measured v3 billing. The application read-back continues to use its current model.
