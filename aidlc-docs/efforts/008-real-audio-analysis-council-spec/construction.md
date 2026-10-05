# Effort 008: Construction Log

**Date:** 2026-10-05
**Scope:** Offline analysis of the effort-006 real-audio bundle, a council re-run, and a `to-spec` specification.

## 1. Inputs and setup

- `main` at `ad728d3`: PR #17 (`9721a54`) plus effort 007.
- Read the bundle README, effort 006 (`requirements-delta`, `construction`, `effort-state`), `src/parcha/lab/metrics.py` and `src/parcha/lab/real_audio.py`.
- Installed the `to-spec` skill from `mattpocock/skills` (`skills/engineering/to-spec/SKILL.md`, `agents/openai.yaml`, and the companion doc `docs/engineering/to-spec.md`) into `~/.claude/skills/to-spec/`, with `curl.exe` because of the PowerShell 5.1 TLS issue noted in effort 007. Read it before use.

  The skill is marked `disable-model-invocation`; it was followed here because the owner asked for it explicitly.
- Read the repo's to-spec prerequisites: `docs/agents/issue-tracker.md` (GitHub Issues via `gh`), `docs/agents/triage-labels.md` (`ready-for-agent`), `docs/agents/domain.md` and `CONTEXT.md`.
- **`gh` is not installed** and only SSH access exists, so the spec could not be published as an issue (see §4).

## 2. Analysis (R9)

1. **Exploratory pass.** Scratch scripts mirroring `parcha.lab.metrics` computed source × mode headlines, the degradation grid, paired verbatim − transcribe deltas with clip-level bootstrap CIs, strata, a reference-artefact re-score, numerals, bias words, failure shapes, the workshop slice and latency.
2. **Key discoveries:**
   - Code-mixed references carry duplicated Latin glosses. Prisma output is Devanagari-only, so cleaned CER is 0.070 against 0.162 as scored.
   - The engine-idle SNR steps add almost nothing; only AMR-NB at 0 dB bites.
   - The two passes tie on 88–91% of pairs; their difference is ITN numeral formatting.
   - There are no insertion failures. i109 is a silent empty on AMR-NB.
   - i036 has a reference/audio mismatch.
   - The 80 workshop rows are *redacted*, not empty.
3. **Committed script.** The analysis was consolidated into `scripts/analyze_real_audio_benchmark.py`: stdlib only, asserting recomputed CER == stored CER on all 1,920 dataset rows. It was run as `py -3 scripts/analyze_real_audio_benchmark.py data/benchmarks/real_audio_2026-10 var/lab/real_audio_analysis.md`, writing to ignored `var/` (`git check-ignore` confirmed). Its numbers match the exploratory pass. The numeral word list was narrowed: 28 numeral clips rather than 30.
4. **Write-up.** [`R9`](../../../docs/research/R9-real-audio-benchmark-analysis.md), marked private because it contains absolute CER/WER.
5. **Corrections after council review:**
   - Finding 7 now says bias boosting is *unverified*: REST silently ignores invalid lists, so a positive control is needed.
   - §6 now says two-pass agreement detects formatting/ITN errors only, not mishearing or deletions.

## 3. Council (`llm-council` skill)

| Step | What ran | Output |
|---|---|---|
| Frame | Product state, the 007 verdict summary, what effort 006 ran (including the recorded claim of ten extra keys of unrecorded provenance), R9 findings 1–8, rules, stakes, questions (a)–(f) | [`framed-question.md`](../../../docs/ideas/council-real-audio/framed-question.md) |
| Advisors | 5 in parallel, each reading only the framed question | [`responses-anon.md`](../../../docs/ideas/council-real-audio/responses-anon.md) |
| Anonymise | A = Outsider, B = Contrarian, C = Executor, D = Expansionist, E = First Principles | [`mapping-secret.md`](../../../docs/ideas/council-real-audio/mapping-secret.md) |
| Review | 5 in parallel; evidence files: R9, effort 006 construction log, 007 verdict, `abouthack.txt`, `docs/notes/02-speech-apis.md` | [`reviews.md`](../../../docs/ideas/council-real-audio/reviews.md) |
| Chairman | Skill structure plus repo sections and a "Decisions for the Updated Spec" list | [`council-real-audio-verdict.md`](../../../docs/ideas/council-real-audio-verdict.md) |

- **Tally:** strongest E ×4, C ×1; biggest blind spot D ×5.
- **Headline:** PR #17 measured transcription, not the promise. Two-pass agreement is a formatting cross-check, not verification. The money path is verbatim → numeral grammar → paise, with abstain-and-re-ask on incomplete numbers, disagreement, empty-200, 504 and 429, on intake *and* corrections. The award target is Real Deal. Benchmark v2 is ~240 paise-labelled utterances at G.711 clean and AMR-NB 0 dB, at most 2,000 credits. No use of the ten keys without written provenance.
- **Chair's notes added in `reviews.md`:**
  - The contest page footer lists BFSI, Automobile and Collections, which supersedes 007 correction 6.
  - Rule 7 and the deltas guard come from the full programme terms.
  - The bias score of 1.0 was requested, but boosting was not verified.

## 4. Spec (`to-spec` skill)

- Followed the skill's process:
  - explored the code (the `Workflow` intake/re-ask paths, the extractor wiring, the fakes in the test fixtures, and the existing spec's template use);
  - sketched seams;
  - wrote with the skill's template;
  - used `CONTEXT.md` and `AGENTS.md` vocabulary.
- **Finding during exploration:** re-ask currently transcribes with the transcribe pass only and lets the external extractor parse the new amount. The spec moves re-ask onto the same verbatim + grammar + cross-check path as intake.
- **Seams:** two existing ones, workflow-through-HTTP with the fake services and the Lab runner/report with the fake Prisma. No new seams are proposed. The skill asks to confirm seams with the user, so they are recorded under "Seams for owner review" in the spec's Further Notes, as the owner asked not to be prompted.
- **Derived decision flagged for confirmation:** amounts attach to items deterministically. This follows from "no LLM touches amounts", but the council did not specify the rule.
- **Publication:** not possible without `gh`. The exact `gh issue create … --label ready-for-agent --body-file docs/specs/money-path-safety-spec.md` command is in the spec draft.
- **Held back:** the owner asked that the spec draft not be committed yet, because it will be revised first. It stays local at `docs/specs/money-path-safety-spec.md`, and links to it from committed files were turned into plain mentions.

## 5. Owner update and commit

- The owner reported a remaining balance of about ₹4,700 at roughly 50 credits per ₹1 (≈ 235,000 credits). This is recorded in [`effort-state.md`](effort-state.md) with the arithmetic and the remaining provenance item. The council verdict was left unedited as a historical record; the update lives in this effort.
- Committed and pushed to `main` with the repo-local personal identity: R9, the analysis script, the council round files and verdict, this effort folder, and the registry row. Not committed: the spec draft.

## 6. Spec draft updated with owner decisions (uncommitted)

- The owner decided three things on 2026-10-05:
  1. A Gramvaani real-telephone slice is mandatory (the Vistaar test slice, 1,032 utterances, evaluation-only, audio never committed).
  2. Timbre is tested with a read-back echo test (all Hindi voices × words-vs-digits × clean control, G.711 clean and AMR-NB 0 dB, with a listening check on failures).
  3. Cost is not a constraint (about ₹4,700 ≈ 235,000 credits).
- The spec draft's plain-language section, problem statement, solution, user stories (now 51), implementation and testing decisions, out-of-scope list and further notes were updated. Two council-008 items change: the v2 credit cap is lifted, and the award choice is reopened pending the Gramvaani and echo-test results.
- `/to-spec` could not be invoked by the agent: the skill is marked user-invocation-only. The owner should run it for a full skill-driven rewrite. The spec draft remains uncommitted at the owner's request.

## 7. Validation

- `git diff --check`, a relative-link check over every new markdown file, and a re-run of the analysis script. Results are in [`audit.md`](audit.md).
- No credentials or private audio were written. The script reads only the committed bundle. No API calls.
