# Effort 007: Construction Log

**Date:** 2026-10-05
**Scope:** Research and ideation only. A100 GPU-sprint brief (R7), multilingual-model and ASR-correction literature review (R8), and an LLM Council verdict. No application code, tests, scripts or data were changed.

## 1. Setup

- Cloned `HarshdipSaha/kaam-ka-parcha` at `main` `15212db` (clean tree) over a dedicated SSH key and host alias, kept separate from the owner's work GitHub account.
- Installed two skills into `~/.claude/skills/` at the owner's request:
  - `llm-council`, from `aiwithremy/claude-skills-llm-council`.
  - `arxiv`, from `NousResearch/hermes-agent`, `skills/research/arxiv`, including `scripts/search_arxiv.py`.

  Both were read before use. The first download attempt failed because Windows PowerShell 5.1 hit a TLS error on `raw.githubusercontent.com`; the retry with `curl.exe` succeeded.
- Read the repo conventions in `AGENTS.md`, `README.md`, `aidlc-docs/registry.md` and efforts 004–005, the earlier council run in `docs/ideas/council/` and `council-verdict.md`, the research style in `docs/research/R4-technical-angles.md`, and the contest page in `docs/abouthack.txt`.
- **Identity note:** git in this clone first resolved to the owner's global work identity (`--show-origin` showed the global `.gitconfig`). At the owner's request, a repo-local `user.name`/`user.email` for their personal account was set before any commit.

## 2. R7: GPU-sprint brief (one background agent)

- A general-purpose agent did a deep repo analysis, web-verified Evon v3.3 hosting on a 40 GB A100 (HF API, model cards, llama.cpp/vLLM/Unsloth/NeMo docs) and the speech-enhancement evidence, then brainstormed the owner's question verbatim. Its output is [`docs/research/R7-a100-gpu-sprint.md`](../../../docs/research/R7-a100-gpu-sprint.md); its own research log is in §15.
- **Independent verification of R7's most serious claim (W1).** `src/parcha/config.py:44-50` defaults the extractor to `https://api.groq.com/openai/v1` with `llama-3.3-70b-versatile`. `app.py:187` (intake) and `app.py:223` (re-ask) call `settings.require_extractor()`, which raises if no endpoint or model is set (`config.py:77-79`). `extractor_provider` is stored (`config.py:33,56`), but grep finds no consumer. **Confirmed.**

## 3. R8: literature review (`arxiv` skill + five reader agents)

- **Discovery**, all through the `arxiv` skill against `export.arxiv.org`, with about 4 s between calls:
  - 14 keyword searches with `search_arxiv.py`. These were loose: the helper OR-matches words, so many hits were off-topic.
  - One `--id` lookup of 30 landmark papers. All resolved to the expected titles.
  - 9 boolean `abs:`/`ti:` queries. One returned an empty body and was retried.

  The full query list and hits are in R8 §11.
- **Reading:** five reader agents ran in parallel, one per cluster (A: LLM error correction, 7 papers; B: entities, biasing and Hinglish, 7; C: international multilingual LLMs, 10; D: Indic LLMs, script and tokens, 8; E: speech, noise and synthetic data, 11). Each returned per-paper findings with table references, applicability and read depth. Clusters C and D were partly read through a summarising fetch, and R8 marks those numbers **[VERIFY]** where the reader flagged them.
- **Synthesis:** written to [`docs/research/R8-multilingual-models-arxiv.md`](../../../docs/research/R8-multilingual-models-arxiv.md): 45 papers, 9 summary findings, 8 proposals (P1–P8), a do-not-do list, and open questions Q1–Q5.
- **Correction after peer review:** Review 2 found that R8 §1.3 mislabelled W2 (`04:30 100`) as a "both passes wrong" case. The verbatim pass held ₹450, so it is a one-pass-right case. §1.3 was rewritten.

## 4. LLM Council (`llm-council` skill)

| Step | What ran | Output |
|---|---|---|
| 1. Frame | Context from the repo, R7 and R8; neutral question with decision, contest facts, verified weaknesses W1–W9, Evon facts, R7 shortlist, R8 findings, stakes and questions (a)–(f) | [`framed-question.md`](../../../docs/ideas/council-gpu-multilingual/framed-question.md) |
| 2. Advisors | 5 parallel agents: Contrarian, First Principles, Expansionist, Outsider, Executor. Each read only the framed question; 150–300 words | [`responses-anon.md`](../../../docs/ideas/council-gpu-multilingual/responses-anon.md) |
| 3. Anonymise | Randomised letters: A = Expansionist, B = Executor, C = Outsider, D = Contrarian, E = First Principles | [`mapping-secret.md`](../../../docs/ideas/council-gpu-multilingual/mapping-secret.md) |
| 4. Peer review | 5 parallel reviewers. Each read the question, the anonymised responses and **one evidence file** (R7, R8, `gates.md`, `demo.md`, `abouthack.txt`), following the 2026-10-04 convention; three skill questions plus factual flags | [`reviews.md`](../../../docs/ideas/council-gpu-multilingual/reviews.md) |
| 5. Chairman | One agent read the question, responses, key and reviews, and produced the skill's five sections plus this repo's "Factual Corrections" and "Dated Go/No-Go Gates" | [`council-gpu-multilingual-verdict.md`](../../../docs/ideas/council-gpu-multilingual-verdict.md) |

Deviation from the skill's defaults: the skill says to present the verdict only in chat and write no files. The owner asked for everything in markdown, and the repo already keeps council rounds under `docs/ideas/`, so all rounds were saved in that layout.

**Review tally:** strongest B ×2 (Reviews 1, 3) and E ×3 (Reviews 2, 4, 5); biggest blind spot A ×5.

**Verdict headline:** a wrong rupee amount never gets confirmed. Money is decided by a deterministic numeral grammar, two-pass agreement and abstention with re-ask, on intake and on corrections. Evon replaces Groq for line items and part names. The GPU is a bonus measured run capped at about 12 attended hours. The first action is one organiser Discord message with four questions.

## 5. Sync with `main` (PR #17) and renumbering

- While this effort was being written, the owner's second machine merged PR #17, "feat: add real-audio speech benchmark" (`9721a54`), which registered **effort 006** (`real-api-real-audio-benchmark`).
- Steps:
  1. Stashed the local docs (`git stash push -u`).
  2. Fast-forwarded `main` from `15212db` to `9721a54`.
  3. Re-applied the stash.
- The only conflict was `aidlc-docs/registry.md`, where both sides added a 006 row. Resolution: keep the merged 006 row unchanged and register this effort as **007**.
- Renamed the folder `006-gpu-sprint-multilingual-council` → `007-gpu-sprint-multilingual-council`. Updated every effort reference in this folder, `framed-question.md`, the verdict and R8 with a byte-safe replace. arXiv IDs containing "006" were left alone.
- Recorded in `effort-state.md` which council inputs effort 006 overtakes: real audio exists, the credit balance differs, and request spacing was added.
- The repo-local git identity was set to the owner's personal account before committing.

## 6. Validation

- Documentation-only change, so application tests were not run (`AGENTS.md`, "Tests and evidence").
- `git diff --check` and a check that every relative link in the new files resolves; results are recorded in [`audit.md`](audit.md).
- No credentials, private audio or personal data were written. No Gnani API was called and no credits were spent.
