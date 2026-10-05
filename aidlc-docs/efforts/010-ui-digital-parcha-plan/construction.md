# Effort 010: Construction Log

## 1. Current UI read (2026-10-05)

- Templates `workshop.html`, `customer.html` and `verify.html` each carry their own copy of a dark slate `<style>` block.
- `app.js` renders with `innerHTML`, including extracted labels.
- The workshop table shows `ID` and `Kind` columns.
- Review items show raw paths ("Needs review: items.part-1.amount_paise").
- The customer DPDP checkbox is pre-ticked.
- `verify.html` always says "Verified" and uses an undefined `--danger` colour.
- "WhatsApp Text" downloads a `.txt` file, although the README promises a clipboard copy.

## 2. Research (five parallel agents)

The owner asked the agents to stop early and hand over what they had. Their reports were copied verbatim into `docs/research/`:

| File | Agent focus | Headline |
|---|---|---|
| R10 | Sarvam and Indic hackathon winners | 15 projects. Sarvam's own winners are poorly documented. Most winners shipped generic SaaS looks, so a UI that resembles its users is an open differentiator |
| R11 | `campus` and `Beacon` | Both are WeMakeDevs × AWS "First Commit" winners: CampusEvac took 3rd (Best UI), Beacon 2nd. Beacon switched from a dark dashboard to light paper on submission day |
| R12 | Voice-AI hackathon winners | Split screen, one focal point, burned-in captions, a stamp moment; a 60-second checklist |
| R13 | Target audience | Data-backed personas. 15 ranked requirements: 96 px mic, Hindi first, light 7:1 contrast, en-IN digits, soundbox-style confirmation |
| R14 | Indian visual language | Direction A, "Digital Parcha": a bill-book slip, violet stamp, green for money arrived. Token set with computed contrast ratios |

## 3. Harness probe (scratch only, before the owner stopped test runs)

An in-process uvicorn server on the offline fakes with Chromium's fake microphone drove `/workshop` end to end in the scratchpad. It found a **real bug**: with no noise mixed in, `/readback` returns `"measured_snr_db": Infinity`, which is invalid JSON, so the browser shows "Error starting read-back". The plan's Task 2 fixes it. The owner then asked that nothing more be run or installed during planning.

Environment-only side effects, all inside the ignored `.venv/`:
- a virtual environment;
- the project in editable mode;
- `imageio-ffmpeg`, with its binary copied to `.venv/Scripts/ffmpeg.exe`;
- `pytest-playwright` and Chromium.

The baseline offline suite on this laptop gave 207 passed and 3 failed. The failures are `test_early_gates` live mocks that need `API_KEY` in the environment; they are pre-existing and environment-only.

## 4. Spec and plan

- **Spec** written with the to-spec template, then reformatted and committed by a parallel session (`a54623b`). This effort edited it to point at effort 010 and added the "Dependency on the money-path plan" section.
- **Plan** written with writing-plans. Its structure:
  - **Task 0** gates on the money-path plan having landed.
  - **Tasks 1–2:** server helpers and the payload/JSON contract.
  - **Task 3:** the browser seam, with mode-keyed fakes because every intake now makes two Prisma passes.
  - **Tasks 4–8:** the design system, verify page, `ui.js`, workshop, customer and stage pages.
  - **Task 9:** responsive and accessibility audit, plus docs.
- **Integration with the money-path plan:**
  - 422 repeat handling;
  - `abstentions` shown on flagged rows;
  - `REPEAT_MESSAGE` and `ABSTAIN_LABELS` moved verbatim into `ui.js`;
  - `describeHttpError` kept on `window`;
  - no typed amount entry.

## 5. Validation

Documentation only. Per the owner's instruction, no tests were run on the plan's code; it runs on the implementing machine. Checks done: relative links in the new docs and `git diff --check`.
