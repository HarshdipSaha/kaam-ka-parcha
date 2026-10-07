# AGENTS.md

## Project

Kaam ka Parcha turns a mechanic's spoken Hinglish repair estimate into a customer-confirmed job card. Gnani Prisma handles speech recognition; Timbre provides the read-back. The customer reviews, corrects, and confirms the current estimate before PDF and WhatsApp-text artefacts become available.

The application is Python 3.12+ with FastAPI, Pydantic v2, Jinja templates, and plain browser JavaScript. It uses a `src/` package layout and an in-memory session store; restarting the server loses sessions. The customer call is an in-browser telephony simulation, and WhatsApp delivery is clipboard copy.

## Start a task

1. Inspect `git status`, the current branch, and the relevant code/tests before editing. Preserve unrelated work.
2. Read `CONTEXT.md` for domain vocabulary. For domain changes, follow `docs/agents/domain.md` and read relevant ADRs under `docs/adr/` if present.
3. For issue-driven work, read the GitHub issue and comments with `gh issue view <number> --comments`. Follow `docs/agents/issue-tracker.md`; consult `docs/agents/triage-labels.md` when assigning or changing labels.
4. For product scope or voice-sealing changes, consult `docs/ideas/spec.md` and `docs/specs/closed-loop-voice-sealing-spec.md`. For evaluation or demo claims, consult `docs/gates.md` and `docs/demo.md`.

Historical plans, handoffs, and saved screenshots describe earlier states. Confirm their claims against current code, live issues, and fresh validation before using them as instructions or evidence.

## Setup and commands

Run commands from the repository root. On Windows PowerShell:

```powershell
# Initial setup; reuse the existing environment when available.
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

# Offline suite and a focused example.
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q tests/test_session.py

# Development server.
.\.venv\Scripts\python.exe -m uvicorn parcha.app:app --reload --port 8000
```

On Linux/macOS, create the environment with `python3.12 -m venv .venv` and use `.venv/bin/python` for the same module commands. Dependencies and pytest configuration live in `pyproject.toml`; there is no configured formatter or linter command.

Copy `.env.example` to `.env` only when local configuration is needed, preserving any existing `.env`. Use `.env.example` and `src/parcha/config.py` for the actual setting names; some README examples describe older names. Shell environment variables override `.env` values.

FFmpeg must be on `PATH` for audio processing. G.711 uses `pcm_mulaw`; AMR-NB support depends on the installed FFmpeg build. Check available codecs before interpreting a codec failure as an application bug.

## Code map

| Area | Files and responsibilities |
| --- | --- |
| HTTP and dependency wiring | `src/parcha/app.py`: `create_app`, `AppServices`, routes, validation/error responses |
| Voice workflow | `src/parcha/workflow.py`: intake, targeted corrections, read-back, customer replies |
| Domain and state | `src/parcha/schema.py`: frozen validated models and review requirements; `src/parcha/session.py`: revisions, transitions, confirmation, consent logs |
| Extraction | `src/parcha/extract.py`, `vocabulary.py`: source-backed fields, Hinglish amounts, automotive terminology |
| Speech integrations | `src/parcha/gnani.py`, `gnani_ws.py`, `readback.py`: REST/WebSocket clients, TTS, reply classification |
| Offline demo and privacy | `src/parcha/mock.py`: scripted speech services for `PARCHA_MOCK=1` (never for accuracy claims); `src/parcha/redact.py`: identifier masking before text reaches the external extractor; `src/parcha/guard.py`: rate, session and daily spend limits |
| Audio and evaluation | `src/parcha/audio.py`, `credits.py`, `lab/`: degradation, budgeting, datasets, metrics, guarded reports |
| Artefacts | `src/parcha/artefact.py`: canonical audit manifest, hashes, embedded PDF evidence, WhatsApp text |
| Browser UI | `src/parcha/templates/`, `src/parcha/static/app.js`: workshop, customer, verification views |
| Validation and tooling | `tests/`, `tests/conftest.py`, `scripts/`: offline fakes, regressions, live probes and browser suite |

Keep route handling in `app.py`, workflow orchestration in `workflow.py`, and state changes in `SessionStore`. Extend the existing service injection and fake clients for offline testing.

## Correctness rules

- Store money as integer paise. Reject coercible booleans, strings, and floats; preserve unknown amounts as `None` and require review instead of inventing a total.
- Keep extracted fields tied to transcript evidence. Ambiguous amounts, unsupported labels, or missing delivery details must remain reviewable. Corrections update the selected field and preserve unrelated items and evidence.
- Preserve frozen models, unique item IDs, and canonical evidence paths. Revalidate updated cards through the schema.
- Enforce expected revisions on edits and replies. A correction invalidates the earlier read-back; confirmation must refer to the current read-back revision. Confirmed sessions are immutable.
- Use the code's state names: `draft`, `review`, `awaiting_reply`, `fallback_ready`, and `confirmed`. README diagrams use older display terminology.
- Keep ambiguous replies in the review/retry/fallback flow. Preserve explicit consent capture and audit logging when changing customer interactions.
- Generate sealed artefacts only from confirmed, complete cards. Keep visible PDF hashes, embedded `transcripts.json`, and verification responses consistent with the canonical audit-manifest helpers.
- Retain the telephony-simulation and clipboard-copy disclosures. Use synthetic identifiers in demonstrations and fixtures.

## Tests and evidence

For a behavior change, add a regression that exercises the observable failure, run the focused tests, then run the offline suite before committing. Reuse `tests/conftest.py` fakes; ordinary tests must consume no speech API credits. Mock success proves application logic, not live recognition quality.

For UI changes, validate the affected workshop/customer/verification flow and mobile layout. `scripts/run_webattack_suite.py` is an optional browser suite requiring Playwright, a running server at `http://127.0.0.1:8000`, and live configuration. Playwright is not included in the project's dev extra. Inspect the script before running it: it can invoke paid services and overwrite `docs/webattack_artifacts/`.

For documentation-only changes, check referenced paths, command accuracy, and `git diff --check`; application tests are unnecessary unless behavior also changes.

Report the checks actually run and any skipped checks or limitations. Update gate statuses, test counts, or performance claims only from fresh reproducible evidence. A single known demo recording does not establish general recognition accuracy.

## Credentials, credits, and reports

- Keep credentials in local environment configuration. Never commit `.env`, API keys, private audio, or personal customer data, or include secrets in logs and screenshots.
- Live probes (`scripts/probe_api.py`, `early_gates.py`, `ws_flush_probe.py`), lab sweeps, and live browser flows consume credits. Establish the requested run scope and budget before executing them; retain existing budget guards and use `--max-credits` where supported.
- Store generated private run output under ignored `var/`. Commit curated fixtures or evidence only when the task calls for them.
- Public lab reports must pass the existing `src/parcha/lab/report.py` guards: recorded written organizer consent with a real reference, matched own-pipeline relative deltas, and no competitor comparisons or absolute CER/WER. Preserve the fail-closed behavior; example consent references are not authorization.

## Finishing work

Review the final diff for unrelated files, generated output, and secrets; run `git diff --check`. Keep commits scoped to the requested change and describe validation in the handoff. Follow the user's requested branch and publication workflow; when direct-to-main is requested, push only the reviewed task changes to `main` without rewriting remote history.

Keep `CONTEXT.md` a vocabulary document. Create an ADR only for a hard-to-reverse architectural decision with material trade-offs, as described in `docs/agents/domain.md`.
