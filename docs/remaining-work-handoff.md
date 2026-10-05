# Remaining Work Handoff: Source-backed Estimates

## Instruction to the next agent

Follow the **Matt Pocock workflow** already installed in this repository. Start by reading `AGENTS.md`, then use the workflow skills in this order where relevant:

1. `$triage` to inspect the live tracker and confirm issue ownership/status.
2. `$diagnosing-bugs` before changing extraction behaviour.
3. `$tdd` for each bug fix: write a failing regression, observe it fail for the intended reason, then implement the smallest robust fix.
4. `$implement` for the production change.
5. `$code-review` with separate reviewers before opening the PR.
6. `$github-pr-workflow` to create, validate, merge, and close the PR.

Do not mark gates, issues, or README claims as passing until there is current reproducible evidence. Do not use only mocked unit tests or only the one known demo audio as proof.

## Current committed baseline

Branch: `fix/sealed-parcha-evidence`  
Baseline commit: `2c738b0 fix(parcha): seal source-backed estimates`

That commit already does the following:

- Runs the recorded noisy mechanic WAV through live Gnani STT, extraction, customer readback/reply, PDF creation, and WhatsApp text generation.
- Produces one brake-pad part of Rs. 450 plus labour of Rs. 200, for Rs. 650, on that known audio.
- Adds automotive vocabulary bias, G.711 simulation, recorded engine ambience at 5 dB SNR, transcript audio SHA-256 fields, an attached audit manifest, and corrected documentation/gates.
- Passed the suite at the time it was committed: `141 passed, 1 warning`.

The known source audio is a regression fixture. It is necessary, but it is not sufficient evidence that the product works generally.

## Important worktree warning

There are **uncommitted, incomplete review-follow-up edits** in the worktree after `2c738b0`. They were interrupted and have not received the full suite or live-flow validation. One edit also accidentally replaced much of `tests/test_config.py` instead of adding a test. Do **not** build a PR from the current dirty worktree.

First inspect `git status` and `git diff`. Preserve only changes you deliberately validate. A clean restart from `2c738b0` is safer, then reapply the intended fixes below with TDD.

## Remaining blocking problems

### 1. Reject malformed monetary values before they can affect totals

Review found that Pydantic accepts coercible values for `LineItem.amount_paise`:

- `true` becomes `1`
- `false` becomes `0`
- `"750"` becomes `750`

This is unsafe because an extractor response with the wrong JSON type can silently alter a rupee total.

Required implementation:

- Make `amount_paise` accept only `None` or a JSON integer.
- Reject booleans, strings, floats, and other coercible values.
- Ensure `Extractor.extract_card()` and `Extractor.extract_field()` turn validation failures into an actionable `ExtractionError` and never produce a card total from them.

Required tests:

- Direct schema tests for `true`, `false`, numeric string, decimal, negative, and valid integer.
- Extractor integration tests showing malformed full-card and correction responses fail before a `JobCard` is created.
- A test that valid `0` remains an integer if zero-price items are product-supported; otherwise make the product rule explicit and test the chosen rule.

### 2. Deduplicate semantic label variants safely

The current dedupe groups only exact normalized labels. It catches identical `front brake pad` entries but can retain two entries for variants such as:

- `brake-pad` and `front brake pad`
- different word order
- harmless punctuation/spacing differences
- equivalent Hindi, Hinglish, or transliterated labels where the evidence supports equivalence

Required implementation principles:

- Do not use a broad keyword match such as every occurrence of `brake`; it can collapse distinct parts.
- Match only within the same `kind` (`part` or `labour`).
- Normalize Unicode and punctuation, tokenize labels, and use a conservative similarity rule.
- Require evidence support from the transcripts before collapsing a non-exact pair.
- If two candidates cannot be distinguished, preserve one incomplete item with `amount_paise=None` and force review/re-ask. Never silently choose an amount on a tie.
- Preserve correct evidence field paths after reassigning canonical item IDs.

Required tests:

- Exact duplicates (existing fixture).
- `brake-pad` versus `front brake pad` where verbatim evidence supports Rs. 450 and a corrupted pass says Rs. 100.
- Word order/punctuation variant.
- A negative case proving `front brake pad` and `rear brake pad` are retained as separate parts.
- A negative case proving `brake pad` and `brake disc` are retained as separate parts.
- A tie case that removes the total and requires review.

## Evidence and artifact correctness

### 3. Use one canonical audit-manifest implementation

`src/parcha/artefact.py` independently builds the same evidence payload for the PDF-visible SHA-256 line and for `transcripts.json`. Refactor this into one helper that:

1. Builds the manifest dictionary.
2. Produces canonical UTF-8 JSON using sorted keys and fixed separators.
3. Returns the SHA-256 digest.

Use that helper for both the embedded attachment and the visible PDF value. Add a test that extracts the PDF attachment, recomputes its digest, and confirms the same digest appears in the PDF text.

### 4. Make the default recorded-noise path independent of the shell working directory

`Settings.telephony_noise_path` was relative to the current directory. Resolve the default from the repository/package location, or package the WAV resource and load it with package-resource APIs.

Validate by changing to a temporary working directory, constructing default services, and proving the recorded-noise file is still found. If distribution packaging is supported, build and install a wheel in a temporary environment and repeat this check; a source checkout test alone does not prove installed behaviour.

Keep the UI/PDF disclosure exact: it may say `recorded engine ambience at 5 dB` only if that is the audio actually supplied to the workflow.

## Generalisation evaluation: required before claiming success

The existing live test uses one real recorded mechanic audio. It must remain as a regression test, but do not overfit extraction rules, vocabulary, prompts, or thresholds to its wording.

Build a versioned evaluation corpus under `data/` or `tests/fixtures/` with a manifest containing:

- source/provenance and permission status for every recording;
- anonymisation status;
- language mix (Hindi, Hinglish, English); 
- noise type and approximate SNR;
- expected items, kind, integer paise amounts, delivery, and review requirement;
- split (`development`, `holdout`, `challenge`).

Use at least these categories:

| Category | Minimum cases | Purpose |
| --- | ---: | --- |
| Clean Hindi/Hinglish workshop speech | 10 | Basic extraction |
| Engine/road/workshop noise | 10 | Noise robustness |
| Different speakers, regions, and pacing | 10 | Speaker generalisation |
| Multiple parts and labour | 10 | Item separation and totals |
| Corrections/re-asks | 8 | Revision safety |
| Ambiguous or missing amounts | 8 | Review and re-ask behaviour |
| Adversarial number confusions/timestamps | 8 | Prevent corrupted totals |
| Duplicate or near-duplicate labels | 8 | Dedupe safety |

Keep a true holdout/challenge set that is never used while tuning prompts, vocabulary, similarity rules, or thresholds. Record each run with code commit, configuration, model/provider version, corpus version, timestamp, and per-case result.

Measure separately:

- exact item set match;
- amount accuracy in paise;
- total accuracy;
- false-confirmation rate: wrong complete card presented as ready;
- false-merge rate: two real parts collapsed;
- false-split rate: one spoken part duplicated;
- correct review/re-ask rate for ambiguity;
- end-to-end customer confirmation success.

Do not turn a weak result into a passing gate by excluding failures or editing ground truth after a run. Store raw transcripts and redacted outputs as evidence. Any external live API run should record the exact request configuration without credentials.

## Required end-to-end validation

After code and corpus tests pass, run all of the following on a fresh process:

1. Full unit/integration suite: `python -m pytest -q`.
2. Static smoke check: `python -m compileall -q src scripts` and `git diff --check`.
3. Recorded known-audio customer flow: intake -> review -> readback -> real confirmation audio -> PDF -> WhatsApp text. Assert the card has exactly one brake-pad item, Rs. 450 part, Rs. 200 labour, total Rs. 650, and valid artifact digests.
4. The complete corpus evaluation, including untouched holdout/challenge data.
5. Manual visual inspection of the resulting workshop card, customer confirmation page, and PDF. Check that the displayed total equals the visible line items.

Update `docs/webattack_artifacts/` only from a fresh run. Keep both the positive known-audio artifact and representative failures/review-required cases so the evidence is not selectively positive.

## Documentation and tracker actions

- Keep future-dated gates as **Pending** until evidence exists.
- Replace qualitative claims such as `works in noisy Hinglish` with a corpus version, metrics, sample size, and date.
- Link raw or redacted reproducible artifacts from gates and issue comments.
- Continue using GitHub issues #8 and #9. If the vocabulary-bias acceptance criteria are fully verified, the PR may close #2 as well.
- Create a focused PR with a body that states exact validation commands and corpus results. Do not merge until review resolves all P1 findings.

## Final acceptance rule

The work is complete only when the product reliably refuses uncertain totals, the known real-audio regression still yields exactly Rs. 650 with no duplicate brake pad, the independent holdout corpus supports the public claim, and the PDF attachment and visible digest are generated from one canonical manifest.
