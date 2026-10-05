# Effort 009: Construction Log

**Date:** 2026-10-05

## 1. Skill and environment

- Installed `writing-plans` from `obra/superpowers` (`skills/writing-plans/SKILL.md`) into `~/.claude/skills/writing-plans/` and followed it.
- The environment follows `docs/superpowers/plans/2026-10-04-kaam-ka-parcha.md` and `AGENTS.md`: Windows PowerShell from the repo root, `.\.venv\Scripts\python.exe`, FFmpeg with `pcm_mulaw` and `libopencore_amrnb`.
- The planning machine has Python 3.14 only and no FFmpeg. An FFmpeg binary download was blocked by Claude Code's safety check because the source wasn't named by the owner, and the agent did not work around it.

## 2. Data verification (real sources)

- **Gramvaani** (`Trelis/vistaar-hi-gramvaani-test`): HF datasets-server `/info` and `/size`, the Hub API, and the downloaded parquet (320,201,217 bytes), read with pyarrow.
  - 1,032 rows; columns `audio{bytes,path}`, `text`, `language`.
  - All WAV, 16 kHz, mono, 16-bit; 10,063.6 s in total (1.01–33.51 s); 3 clips longer than 29 s.
  - References contain no digits, Latin letters or tags; 157 contain a number the grammar reads.
  - 291 clips already contain clipping from the source.
  - Forecast for both passes: ≈4,025 credits.
- **Timbre voices:** 13 `hi-IN` voices, per `docs/notes/02-speech-apis.md` §3.4.
- **Rates:** 0.20 credits per second for Prisma and 0.05 credits per character for Timbre, per `docs/gates.md`.
- **Bias list:** 65 unique words, all valid for Prisma.
- **Code facts:**
  - `make_readback` sends ₹ digits;
  - the runner needs 8 kHz WAV and supports codec `none`;
  - the default `--impulse-profiles` includes all three profiles;
  - `Clip.id` allows only 3 digits;
  - `test_app.py` expects a ₹650 total from the conftest fake.
- **Credit forecasts from the generated texts:**
  - v2 render 396 credits;
  - echo screen 13,621 credits;
  - echo confirm ≈2,337 credits per voice/style pair;
  - total ≈26,000 credits ≈₹520.

## 3. Prototypes (scratch copy of the repo, not committed)

The following were run against the real modules with `pytest --noconftest`: grammar, money layer, workflow intake and re-ask, `GnaniError.status`, Evon payload, runner fields and `verbatim_nobias`, money evaluator, v2 generator, echo scorer and Gramvaani preparation. The result was **311 passed**; the 12 failures are the pre-existing FFmpeg-only tests.

Issues found and fixed during prototyping, now reflected in the plan:
1. The vehicle-number regex missed the "DL 3S AB 1234" format.
2. Number lists ("दस हजार बीस हजार") were merged into one amount.
3. Distances and dates ("साढ़े पांच किलोमीटर", "छब्बीस जनवरी") were read as money.
4. Filter overshoot added clipping, so the downsampler now scales the whole clip instead.
5. A spoken total ("kul …") was an extra amount, so it is now checked against the sum of the items.
6. Windows BOM in JSONL broke loading, so files are now read as `utf-8-sig`.

## 4. Owner direction mid-task

The owner asked to stop testing and downloading and to complete the plan. These items stay unexecuted and are flagged in the plan's Verified Facts table for implementation time: the final `make_bias_control` and Gramvaani unit tests, the app-level tests, the live paths, `register_owner_takes.py` and `bench_report.py`.

## 5. Outputs

- The plan: 17 tasks, Global Constraints, Review Focus with tests, Verified Facts, and a self-review.
- Spec corrections; this effort; the registry row.
- Pushed directly to `main` at the owner's request.
