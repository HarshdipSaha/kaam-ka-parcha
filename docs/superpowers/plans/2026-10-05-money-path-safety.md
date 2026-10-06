# Money-Path Safety & Amount Benchmark v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rupee amounts come only from a deterministic Hinglish numeral grammar, never from an LLM. Any doubt (incomplete number, cross-check disagreement, empty result, 504/429) abstains and re-asks. Evon replaces Groq for line items. A judge-ready benchmark proves it, with three parts: an amount-labelled v2 set, a Gramvaani real-telephone slice, and a Timbre read-back echo test.

**Architecture:** Two new pure modules sit between Prisma and the session store. `numerals.py` reads amounts from text; `money.py` decides each amount or abstains. `Workflow.intake` and the amount branch of `Workflow.reask` route every amount through them, and abstention reasons are written as `system` transcript logs, so the sealed audit manifest carries them unchanged. The Line Noise Lab gains three things:
- canonical references and an explicit `empty_transcript` outcome;
- a money evaluator (`money_eval.py`) that replays the product's decision on runner output;
- three data sources (gold-first v2 generator, Gramvaani preparation, Timbre echo test). One report and a data card come out of them.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2, httpx, NumPy, FFmpeg (`pcm_mulaw`, `libopencore_amrnb`), pytest, pyarrow (benchmark extra only). Windows PowerShell from the repository root, same as the previous plan `docs/superpowers/plans/2026-10-04-kaam-ka-parcha.md`.

**Spec:** `docs/specs/money-path-safety-spec.md` is authoritative. Context: `docs/ideas/council-real-audio-verdict.md`, `docs/research/R9-real-audio-benchmark-analysis.md`, `docs/research/R4-technical-angles.md`.

## Global Constraints

- Money is integer paise. `LineItem.amount_paise` stays `int | None`, between 0 and 10,000,000 (₹1,00,000). Larger values abstain with `out_of_range`.
- **No LLM (Groq, Evon or any other) produces, attaches or corrects an amount.** Evon handles line items, part names and the delivery date only.
- The transcribe pass is a **formatting cross-check of the same decode**, never independent verification, in code comments, docs and the pitch.
- Abstention reasons, exact strings: `incomplete_number`, `crosscheck_disagreement`, `empty_transcript`, `provider_504`, `provider_429`, `ambiguous_attachment`, `out_of_range`.
- Session states are unchanged: `draft`, `review`, `awaiting_reply`, `fallback_ready`, `confirmed`. Expected-revision and confirmed-immutability rules are unchanged.
- No silent automatic retries in the product path. The Lab keeps its stop-on-first-provider-error behaviour.
- Ordinary tests consume **no API credits**. Live runs log spend and write outputs under the ignored `var/`.
- Public material: own-pipeline relative deltas only, after organiser consent. No absolute CER/WER, no competitor names (`src/parcha/lab/report.py` guards stay fail-closed).
- Gramvaani is **evaluation only**: never demo audio. Its audio and reference text are never committed, and no Gramvaani number goes public before permission from contact@gramvaani.org and organiser consent.
- The owner's extempore takes stay internal (under `var/`) until the organisers rule on real-person audio.
- Cost is **not** a constraint (owner, 2026-10-05: ≈₹4,700 ≈ 235,000 credits at ~50 credits/₹). Do not shrink the benchmark to save credits. Do record every run's spend. The ten extra keys from effort 006 still need written provenance before use.
- Read every JSONL file with `encoding="utf-8-sig"`. Windows PowerShell writes UTF-8 with a BOM.

## Review Focus

These are input classes the spec implies but no headline test covers, most likely first. Each has a test in the owning task.

1. **The mechanic says the total aloud** ("…labour do sau, kul saade chhe sau"). Expected: the total is checked against the sum of the items, not counted as an extra item. A mismatch abstains every amount. *Tests: Task 3, `test_spoken_total_*`.*
2. **The extractor quotes English labels while Prisma returns Devanagari.** Expected: amounts cannot be attached, so they abstain with `ambiguous_attachment`; they are never guessed. *Test: Task 3, `test_english_label_quotes_absent_from_devanagari_transcripts_abstain`.*
3. **Mid-sentence self-correction** ("saade chaar sau… nahi paanch sau"). Expected: abstain, not pick one. *Test: Task 3, `test_mid_sentence_self_correction_abstains_instead_of_guessing`.*
4. **A customer correction holding two numbers** ("teen sau nahi saade teen sau"). Expected: abstain and re-ask. *Test: Task 4, `test_correction_with_two_numbers_abstains`.*
5. **A manifest saved by PowerShell with a UTF-8 BOM.** Expected: it loads. *Test: Task 7, `test_manifest_with_utf8_bom_loads`.*

## Verified Facts (checked 2026-10-05 while writing this plan)

| Fact | Value | How verified |
|---|---|---|
| Gramvaani slice | `Trelis/vistaar-hi-gramvaani-test`: **1,032 rows**; columns `audio{bytes,path}`, `text`, `language`; all `language == "hi"`; ungated; card licence `gramvaani-asr-2022` | HF datasets-server `/info`, `/size`, Hub API, parquet downloaded (320,201,217 bytes) and read with pyarrow |
| Gramvaani audio | All RIFF WAV, **16 kHz**, mono, 16-bit. Total **10,063.6 s (2.80 h)**; min 1.01 s, mean 9.75 s, max 33.51 s; **3 clips > 29 s** (runner chunks at 29 s), 0 > 60 s | Decoded every row |
| Gramvaani text | No empty rows, no Latin letters, no digits, no tags. **157** references hold ≥1 number the grammar reads; 1 holds an incomplete one | Grammar run over all references |
| Gramvaani clipping | **291 / 1,032** source clips already contain full-scale samples (≤0.65% of samples), so the strata are `gramvaani_clipped` 291 and `gramvaani_unclipped` 741. The NumPy downsampler adds no hard clipping (whole-clip scaling) | `scripts/prepare_gramvaani.py` run on the real parquet |
| Gramvaani cost | Both passes: **≈4,025 credits (≈₹81)** | Durations × 0.2 credits/s × 2 |
| Timbre voices | **13 `hi-IN` voices**: Nalini, Bhavna, Yashvi, Urmila, Jwala, Chitra, Ambuja, Deepak, Roopesh, Vikrant, Hemraj, Jalaj, Omkar | `docs/notes/02-speech-apis.md` §3.4 |
| Credit rates | Prisma **0.20 credits per audio-second per pass**; Timbre **0.05 credits per character** | `docs/gates.md` probe (single call each) |
| Prisma REST | ≤60 s per file (the observed limit is 30 s; runner uses 29 s); **no word timestamps, no confidence**; an invalid `bias_list` is silently ignored | `docs/notes/02-speech-apis.md`, effort 005 |
| Bias list | `AUTOMOTIVE_BIAS_WORDS`: **65 unique**, all valid single letter-only words | Imported and validated |
| Read-back format today | `make_readback` sends amounts as **₹ digits** (`format_rupees` → `"₹450"`), not Hindi words | `src/parcha/readback.py` |
| Runner input | Clip audio must be **8 kHz mono 16-bit WAV** (`_read_pcm`). Codec `none` skips the round trip. The default `--impulse-profiles` includes all three impulse profiles, so v2 runs must pass `none` | `src/parcha/lab/runner.py`, `audio.py` |
| Clip IDs | Current pattern `^[a-z][0-9]{3}$` allows ≤999 per letter, too few for 1,032 Gramvaani clips | `src/parcha/lab/dataset.py` |
| Code prototyped | The grammar, money path, workflow changes, Evon payload, runner changes, money evaluator, v2 generator, echo scorer and Gramvaani preparation ran in a scratch copy of the repo on Python 3.14: **311 passed**. The 12 failures were the pre-existing FFmpeg-dependent tests, because this planning machine has no FFmpeg. Not executed here: the app-level tests (Task 5; `conftest.py` imports the app, which loads audio through FFmpeg), the live API paths, `register_owner_takes.py`, `bench_report.py`, and the final versions of `make_bias_control` and the Gramvaani unit tests. These run on the owner's laptop during implementation | `pytest --noconftest` in the scratch copy |

## Environment (owner's laptop, as in the previous plan)

```powershell
# from the repository root
py -3.12 -m venv .venv                                   # reuse if it already exists
.\.venv\Scripts\python.exe -m pip install -e ".[dev,bench]" # "bench" adds pyarrow (Task 12)
ffmpeg -hide_banner -encoders | findstr /i "pcm_mulaw libopencore_amrnb"   # both must print
.\.venv\Scripts\python.exe -m pytest -q                  # baseline before Task 1: all green
```

Live runs need `API_KEY` in `.env`. The Evon endpoint is `EXTRACTOR_BASE_URL` (Task 6).

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `src/parcha/numerals.py` | create | Hinglish amount grammar `parse_amounts`; renderers `render_hindi_amount`, `render_colloquial_amount` |
| `src/parcha/money.py` | create | `decide_amounts`, `spoken_item_order`, `settle_card_amounts`, `AbstainReason` |
| `src/parcha/gnani.py` | modify | `GnaniError.status` |
| `src/parcha/workflow.py` | modify | `RepeatRequest`, money path in `intake`, amount branch of `reask`, abstention logs |
| `src/parcha/app.py` | modify | `RepeatRequest` → HTTP 422 `{"repeat": true, "reason": …}`; Evon provider wiring |
| `src/parcha/static/app.js` | modify | Show "please say it again" on a repeat response |
| `src/parcha/readback.py` | modify | `amount_style="digits"|"words"` |
| `src/parcha/config.py`, `extract.py`, `.env.example` | modify | Evon as default provider, thinking off, JSON schema; no Groq fallback |
| `src/parcha/lab/metrics.py` | modify | `canonical_reference` |
| `src/parcha/lab/dataset.py` | modify | IDs `{3,4}` digits, `expected_amounts_paise`, `voice`, `audio_sha256`, BOM-safe loading |
| `src/parcha/lab/runner.py` | modify | Row fields `reference_canonical`, `cer_canonical`, `outcome`, `expected_amounts_paise`; mode `verbatim_nobias` |
| `src/parcha/lab/money_eval.py` | create | Replay the money decision on runner rows; summaries with Wilson bounds; Gramvaani number agreement |
| `src/parcha/lab/amount_bench.py` | create | Gold-first v2 estimates, corrections, stress amounts, voice list |
| `src/parcha/lab/gramvaani.py` | create | Parquet → 8 kHz WAVs + manifest rows |
| `src/parcha/lab/echo.py` | create | Timbre echo test core (injected synthesize/degrade/transcribe) |
| `src/parcha/lab/bench_report.py` | create | Private report + committed data card |
| `scripts/make_amount_benchmark.py`, `render_amount_benchmark.py`, `prepare_gramvaani.py`, `run_echo_test.py`, `register_owner_takes.py` | create | CLIs (dry-run forecast by default, `--live` to spend) |
| `data/benchmarks/amount_v2/*`, `data/benchmarks/gramvaani/index.jsonl`, `data/benchmarks/exclusions.json` | create | Committed manifests and index (no Gramvaani audio or text) |
| `docs/benchmarks/BENCHMARK_CARD.md` | create | Data card |
| `tests/fakes.py`, `test_numerals.py`, `test_money_path.py`, `test_extract_evon.py`, `test_lab_v2_runner.py`, `test_benchmark_v2.py`, `test_gramvaani.py`, `test_app_repeat.py` | create | Tests |
| `tests/conftest.py`, `test_workflow.py`, `test_config.py` | modify | Fakes and expectations that move to the new path |

---

### Task 0: Pre-flight (owner, no code)

- [ ] **Step 1:** Open the Gnani console and record the configured key's balance in `aidlc-docs/efforts/009-money-path-plan/effort-state.md`, plus where the ten extra keys came from.
- [ ] **Step 2:** Send the organiser Discord message:
  1. Does scripted real-person roleplay count as synthetic data?
  2. May recordings be real phone calls?
  3. Does a community Q8_0 GGUF satisfy Rule 3?
  4. May own-pipeline deltas be published?
  5. May public corpora such as Gramvaani and IndicContextEval be used for evaluation?
  6. May the extra keys be used?
- [ ] **Step 3:** Email contact@gramvaani.org asking permission to report evaluation results from the Gramvaani test set in a student contest submission. Record the date in the effort log.

### Task 1: Integrity corrections (documentation only)

**Files:** Modify `README.md`, `docs/demo.md`, `docs/gates.md`. Create `docs/corrections-2026-10.md`.

- [x] **Step 1:** In `README.md`, replace "Optional Extractor / LLM API Key (used for delta extraction)" with "Extractor endpoint (required): Evon v3.3 via an OpenAI-compatible server; it structures line items only — amounts are read by deterministic code". Replace the `GROQ_API_KEY` line with the four `EXTRACTOR_*` names from `.env.example` (Task 6).
- [x] **Step 2:** In `docs/demo.md`, delete every number not produced by a committed command: "+20.0% part recovery", "96.0% short-reply flush recovery", "800 synthetic telephony turns", "Measured by us, N=800", "garages lose 8% of margins", "139 tests". Replace "legally sealed" with "tamper-evident".
- [x] **Step 3:** In `docs/gates.md`, change the "74/74 PASS" row to "Not reproducible: no runner exists (see corrections note)". Note that `data/real_world_samples/mechanic_in_garage_noise.wav` is synthesised speech.
- [x] **Step 4:** Write `docs/corrections-2026-10.md` with one dated bullet per change above and the reason for it.
- [x] **Step 5:** Verify and commit.

```powershell
git diff --check
Select-String -Path README.md,docs\demo.md -Pattern "96.0%|N=800|139 tests|legally sealed|optional extractor" -SimpleMatch   # prints nothing
git add README.md docs/demo.md docs/gates.md docs/corrections-2026-10.md
git commit -m "docs: remove unmeasured claims and mark extractor required"
```

### Task 2: Numeral grammar

**Files:** Create `src/parcha/numerals.py`, `tests/test_numerals.py`.

**Interfaces:**
- Produces:
  - `MAX_ITEM_PAISE = 10_000_000`
  - `@dataclass(frozen=True) AmountMention(paise: int | None, status: str, text: str)`, where `status` is `"complete"` or `"incomplete"`
  - `parse_amounts(text: str) -> list[AmountMention]`
  - `render_hindi_amount(paise: int) -> str` (standard words + " रुपये")
  - `render_colloquial_amount(paise: int) -> str`

- [x] **Step 1: Write the failing test** `tests/test_numerals.py`:

```python
import pytest
from parcha.numerals import parse_amounts, render_hindi_amount


def values(text):
    return [(m.status, m.paise) for m in parse_amounts(text)]


@pytest.mark.parametrize("text,expected", [
    ("front brake pad saade chaar sau", [("complete", 45000)]),
    ("फ्रंट ब्रेक पैड साढ़े चार सौ लेबर दो सौ मंगलवार शाम तक", [("complete", 45000), ("complete", 20000)]),
    ("front brake pad ₹450, labour ₹200, Somvaar shaam tak", [("complete", 45000), ("complete", 20000)]),
    ("फ्रंट ब्रेक पैड 04:30 100 लेबर 200 मंगलवार शाम तक", [("complete", 10000), ("complete", 20000)]),  # effort 005
    ("clutch plate dedh hazaar", [("complete", 150000)]),
    ("ढाई सौ रुपये", [("complete", 25000)]),
    ("sava sau", [("complete", 12500)]),
    ("sava do sau", [("complete", 22500)]),
    ("paune do hazaar", [("complete", 175000)]),
    ("पौने सौ", [("complete", 7500)]),
    ("do hazaar pachaas", [("complete", 205000)]),
    ("baarah sau", [("complete", 120000)]),
    ("एक लाख", [("complete", 10000000)]),
    ("ek hazaar do sau", [("complete", 120000)]),
    ("labour pachaas", [("complete", 5000)]),
    ("1,200 rupaye", [("complete", 120000)]),
    ("४५० रुपये", [("complete", 45000)]),
    ("₹ 1,500.50", [("complete", 150050)]),
    ("2 हजार", [("complete", 200000)]),
])
def test_complete_amounts(text, expected):
    assert values(text) == expected


@pytest.mark.parametrize("text", ["brake pad saade", "brake pad saade chaar", "dedh", "sava"])
def test_incomplete_amounts(text):
    assert values(text) == [("incomplete", None)]


@pytest.mark.parametrize("text", [
    "एक रिसर्च में", "do din mein gaadi milegi", "chaar baje aana", "bees minute lagenge",
    "DL 3S AB 1234", "10:30 pe aana",
])
def test_distractors_are_not_money(text):
    assert values(text) == []


@pytest.mark.parametrize("text,expected", [   # real Gramvaani reference phrasing (rows 95, 106, 746, 17)
    ("दस हजार बीस हजार पच्चीस हजार तीस हजार", [("complete", 1000000), ("complete", 2000000),
                                              ("complete", 2500000), ("complete", 3000000)]),
    ("निर्धारित दूरी साढ़े पांच किलोमीटर रखा गया", []),
    ("पौने दो साल पहले इस केंद्र का उद्घाटन", []),
    ("हमारी छब्बीस जनवरी मनाते", []),
    ("लगभग ढाई सौ से अधिक बाल", [("complete", 25000)]),
])
def test_real_phone_speech_number_lists_dates_and_distances(text, expected):
    assert values(text) == expected


def test_vehicle_number_does_not_hide_a_following_amount():
    assert values("DL 3S AB 1234 brake pad saade chaar sau") == [("complete", 45000)]


@pytest.mark.parametrize("rupees", list(range(1, 100)) + [100, 125, 450, 999, 1000, 1050, 1200, 1500, 2050,
                                                          9999, 10000, 45000, 99999, 100000])
def test_render_then_parse_round_trips(rupees):
    assert values(render_hindi_amount(rupees * 100)) == [("complete", rupees * 100)]


def test_render_rejects_non_whole_rupees_and_out_of_range():
    for bad in (0, 150, 10_000_100):
        with pytest.raises(ValueError):
            render_hindi_amount(bad)
```

- [x] **Step 2: Run it to see it fail.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_numerals.py`. Expected: collection error `ModuleNotFoundError: No module named 'parcha.numerals'`.
- [x] **Step 3: Create `src/parcha/numerals.py`.** The tables and the phrase parser are the decision, so here is the full body, as prototyped:

```python
"""Deterministic Hinglish amount grammar. No network, no LLM.

parse_amounts(text) finds rupee amounts in Prisma output (Devanagari, romanised or ITN digits)
and returns them in spoken order: "complete" (a value in paise) or "incomplete" (a number was
started but cannot be valued safely, e.g. a dangling "saade"). render_* are the inverse.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

__all__ = ["AmountMention", "MAX_ITEM_PAISE", "parse_amounts", "render_colloquial_amount", "render_hindi_amount"]

MAX_ITEM_PAISE = 10_000_000  # mirrors LineItem.amount_paise le=10_000_000

_DEVA_1_99 = (
    "एक दो तीन चार पांच छह सात आठ नौ दस "
    "ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस बीस "
    "इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस "
    "इकतीस बत्तीस तैंतीस चौंतीस पैंतीस छत्तीस सैंतीस अड़तीस उनतालीस चालीस "
    "इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस उनचास पचास "
    "इक्यावन बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ "
    "इकसठ बासठ तिरसठ चौंसठ पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर सत्तर "
    "इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर उन्यासी अस्सी "
    "इक्यासी बयासी तिरासी चौरासी पचासी छियासी सत्तासी अट्ठासी नवासी नब्बे "
    "इक्यानवे बानवे तिरानवे चौरानवे पचानवे छियानवे सत्तानवे अट्ठानवे निन्यानवे"
).split()
_DEVA_VARIANTS = {
    "पाँच": 5, "छः": 6, "छे": 6, "पन्द्रह": 15, "तिरेपन": 53, "चौव्वन": 54, "अठावन": 58,
    "सरसठ": 67, "अरसठ": 68, "उनासी": 79, "निन्यानबे": 99, "बानबे": 92, "तिरानबे": 93,
    "चौरानबे": 94, "पचानबे": 95, "छियानबे": 96, "सत्तानबे": 97, "अट्ठानबे": 98, "इक्यानबे": 91,
}
_ROMAN_1_99 = (
    "ek do teen chaar paanch chhah saat aath nau das "
    "gyaarah baarah terah chaudah pandrah solah satrah athaarah unnees bees "
    "ikkees baaees teyees chaubees pachchees chhabbees sattaaees atthaaees untees tees "
    "iktees battees taintees chauntees paintees chhattees saintees adtees untaalees chaalees "
    "iktaalees bayaalees taintaalees chavaalees paintaalees chhiyaalees saintaalees adtaalees unchaas pachaas "
    "ikyaavan baavan tirpan chauvan pachpan chhappan sattaavan atthaavan unsath saath "
    "iksath baasath tirsath chausath painsath chhiyaasath sadsath adsath unhattar sattar "
    "ikhattar bahattar tihattar chauhattar pachhattar chhihattar satahattar athahattar unaasi assi "
    "ikyaasi bayaasi tiraasi chauraasi pachaasi chhiyaasi sattaasi atthaasi navaasi nabbe "
    "ikyaanve baanve tiraanve chauraanve pachaanve chhiyaanve sattaanve atthaanve ninyaanve"
).split()
_ROMAN_VARIANTS = {
    "tin": 3, "char": 4, "panch": 5, "chhe": 6, "che": 6, "chah": 6, "nao": 9, "pachis": 25,
    "chaunsath": 64, "sarsath": 67, "arsath": 68, "artees": 38, "artaalees": 48, "byaalees": 42,
}
_MULTIPLIERS = {
    "सौ": 100, "sau": 100, "हजार": 1_000, "hazaar": 1_000, "hazar": 1_000, "hajar": 1_000,
    "लाख": 100_000, "lakh": 100_000, "laakh": 100_000, "करोड": 10_000_000, "crore": 10_000_000,
    "karod": 10_000_000,
}
# fraction prefix -> (kind, value): "add"/"sub" adjust the following number; "fixed" multiplies the multiplier
_FRACTIONS = {
    "साढे": ("add", 0.5), "saade": ("add", 0.5), "sadhe": ("add", 0.5), "saadhe": ("add", 0.5),
    "सवा": ("add", 0.25), "sava": ("add", 0.25), "sawa": ("add", 0.25),
    "पौने": ("sub", 0.25), "paune": ("sub", 0.25), "pone": ("sub", 0.25),
    "डेढ": ("fixed", 1.5), "dedh": ("fixed", 1.5), "derh": ("fixed", 1.5),
    "ढाई": ("fixed", 2.5), "dhai": ("fixed", 2.5), "dhaai": ("fixed", 2.5),
}
_CURRENCY = {"₹", "rs", "inr", "रुपये", "रुपए", "रुपया", "rupaye", "rupay", "rupees", "rupee", "rupya"}
_NON_MONEY_UNITS = {
    "मिनट", "minute", "minat", "घंटे", "घंटा", "ghante", "ghanta", "दिन", "din", "हफ्ते", "hafte",
    "महीने", "mahine", "साल", "saal", "बजे", "baje", "किलो", "kilo", "किलोमीटर", "km", "लीटर", "litre",
    "liter", "प्रतिशत", "percent", "नंबर", "number",
    # month names: "छब्बीस जनवरी" is a date, not ₹26
    "जनवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर",
    "january", "february", "march", "april", "june", "july", "august", "september", "october",
    "november", "december",
}
_DIGITS = re.compile(r"^\d{1,3}(?:,\d{2,3})+(?:\.\d{1,2})?$|^\d+(?:\.\d{1,2})?$")
_TIME = re.compile(r"^\d{1,2}:\d{2}$")
_DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_PUNCT = re.compile(r"[\"'“”‘’()\[\]{}!?;।|/\\-]+")
_VEHICLE = re.compile(  # Indian registration, e.g. "DL 3S AB 1234", "MH 12 AB 1234"
    r"\b[A-Za-z]{2}\s?\d{1,2}\s?[A-Za-z]{0,3}\s?[A-Za-z]{1,3}\s?\d{1,4}\b"
)


def _fold_deva(token: str) -> str:
    token = unicodedata.normalize("NFD", token).replace("़", "").replace("ँ", "ं")
    return unicodedata.normalize("NFC", token)  # nukta dropped, chandrabindu -> anusvara


def _fold_roman(token: str) -> str:
    token = token.casefold().replace("ee", "i").replace("oo", "u").replace("w", "v").replace("z", "j")
    return re.sub(r"(.)\1+", r"\1", token)


def _key(token: str) -> str:
    return _fold_deva(token) if re.search(r"[ऀ-ॿ]", token) else _fold_roman(token)


_WORDS: dict[str, int] = {}
for _n, _w in enumerate(_DEVA_1_99, 1):
    _WORDS[_key(_w)] = _n
for _n, _w in enumerate(_ROMAN_1_99, 1):
    _WORDS[_key(_w)] = _n
for _w, _n in {**_DEVA_VARIANTS, **_ROMAN_VARIANTS}.items():
    _WORDS[_key(_w)] = _n
_MULT = {_key(w): v for w, v in _MULTIPLIERS.items()}
_FRAC = {_key(w): v for w, v in _FRACTIONS.items()}
_CUR = {_key(w) for w in _CURRENCY}
_NONMONEY = {_key(w) for w in _NON_MONEY_UNITS}


@dataclass(frozen=True)
class AmountMention:
    paise: int | None
    status: str  # "complete" | "incomplete"
    text: str


@dataclass(frozen=True)
class _Tok:
    raw: str
    kind: str  # num | mult | frac | digit | time | cur | nonmoney | other
    value: float | tuple | None = None


def _tokenize(text: str) -> list[_Tok]:
    text = unicodedata.normalize("NFC", text).translate(_DEVA_DIGITS)
    text = _VEHICLE.sub(" ", text)
    text = _PUNCT.sub(" ", text.replace("₹", " ₹ "))
    out: list[_Tok] = []
    for raw in text.split():
        raw = raw.strip(".,")
        if not raw:
            continue
        if _TIME.match(raw):
            out.append(_Tok(raw, "time"))
        elif _DIGITS.match(raw):
            out.append(_Tok(raw, "digit", float(raw.replace(",", ""))))
        elif re.search(r"\d", raw):            # letters+digits: codes, not money
            out.append(_Tok(raw, "other"))
        else:
            k = _key(raw)
            if k in _WORDS:
                out.append(_Tok(raw, "num", _WORDS[k]))
            elif k in _MULT:
                out.append(_Tok(raw, "mult", _MULT[k]))
            elif k in _FRAC:
                out.append(_Tok(raw, "frac", _FRAC[k]))
            elif k in _CUR:
                out.append(_Tok(raw, "cur"))
            elif k in _NONMONEY:
                out.append(_Tok(raw, "nonmoney"))
            else:
                out.append(_Tok(raw, "other"))
    return out


def _paise(rupees: float) -> int | None:
    value = round(rupees * 100)
    return value if abs(rupees * 100 - value) < 1e-6 else None


def _parse_phrase(toks: list[_Tok], i: int) -> tuple[float | None, bool, int]:
    """Parse one amount phrase starting at i. Returns (rupees or None, complete, next_index)."""
    if toks[i].kind == "digit":
        value, j = toks[i].value, i + 1
        if j < len(toks) and toks[j].kind == "mult":
            value, j = value * toks[j].value, j + 1
        return value, True, j
    total, last_mult, j = 0.0, None, i
    while j < len(toks):
        t = toks[j]
        if t.kind == "frac":
            kind, frac = t.value
            nxt = toks[j + 1] if j + 1 < len(toks) else None
            if kind == "fixed":
                if nxt is None or nxt.kind != "mult" or (last_mult and nxt.value >= last_mult):
                    return None, False, j + 1
                total, last_mult, j = total + frac * nxt.value, nxt.value, j + 2
                continue
            if nxt is not None and nxt.kind == "mult" and kind == "add" and frac == 0.25:
                total, last_mult, j = total + 1.25 * nxt.value, nxt.value, j + 2   # sava sau = 125
                continue
            if nxt is not None and nxt.kind == "mult" and kind == "sub":
                total, last_mult, j = total + 0.75 * nxt.value, nxt.value, j + 2   # paune sau = 75
                continue
            after = toks[j + 2] if j + 2 < len(toks) else None
            if nxt is None or nxt.kind != "num":
                return None, False, j + 1                                          # dangling saade/sava/paune
            if after is None or after.kind != "mult":
                return None, False, j + 2                                          # caller checks the unit word
            n = nxt.value + frac if kind == "add" else nxt.value - frac
            total, last_mult, j = total + n * after.value, after.value, j + 3
            continue
        if t.kind == "num":
            nxt = toks[j + 1] if j + 1 < len(toks) else None
            if nxt is not None and nxt.kind == "mult" and (last_mult is None or nxt.value < last_mult):
                total, last_mult, j = total + t.value * nxt.value, nxt.value, j + 2
                continue
            if nxt is not None and nxt.kind == "mult":                             # "das hazaar bees hazaar"
                return total, True, j
            if last_mult is not None:                                              # "do hazaar pachaas"
                return total + t.value, True, j + 1
            if t.value >= 11 or (nxt is not None and nxt.kind == "cur"):
                return float(t.value), True, j + 1
            return None, True, j + 1          # bare 1..10 with no multiplier or currency is not money
        if t.kind == "mult" and last_mult is None and total == 0:
            total, last_mult, j = float(t.value), t.value, j + 1                   # "sau", "hazaar"
            continue
        break
    return (None, True, j) if last_mult is None else (total, True, j)


def parse_amounts(text: str) -> list[AmountMention]:
    """Rupee amounts in spoken order. Clock times and amounts followed by a non-money unit are skipped."""
    toks = _tokenize(text or "")
    mentions: list[AmountMention] = []
    i = 0
    while i < len(toks):
        if toks[i].kind not in {"num", "mult", "frac", "digit"}:
            i += 1
            continue
        rupees, complete, j = _parse_phrase(toks, i)
        span = " ".join(t.raw for t in toks[i:j])
        if j < len(toks) and toks[j].kind == "nonmoney":
            i = j + 1
            continue
        if not complete:
            mentions.append(AmountMention(None, "incomplete", span))
        elif rupees is not None:
            paise = _paise(rupees)
            mentions.append(AmountMention(paise, "complete", span) if paise is not None
                            else AmountMention(None, "incomplete", span))
        i = max(j, i + 1)
    return mentions


def _below_100(n: int) -> str:
    return _DEVA_1_99[n - 1]


def render_hindi_amount(paise: int) -> str:
    """Whole rupees as standard Hindi words plus 'रुपये'. Inverse of parse_amounts."""
    if paise <= 0 or paise % 100 or paise > MAX_ITEM_PAISE:
        raise ValueError("render_hindi_amount supports whole rupees from ₹1 to ₹1,00,000")
    rupees, parts = paise // 100, []
    for size, word in ((100_000, "लाख"), (1_000, "हज़ार"), (100, "सौ")):
        group, rupees = divmod(rupees, size)
        if group:
            parts.append(f"{_below_100(group)} {word}")
    if rupees:
        parts.append(_below_100(rupees))
    return " ".join(parts) + " रुपये"


def render_colloquial_amount(paise: int) -> str:
    """How a mechanic says it: डेढ़/ढाई/साढ़े/सवा/पौने and 'बारह सौ' where they apply; else standard words."""
    if paise <= 0 or paise % 100 or paise > MAX_ITEM_PAISE:
        raise ValueError("render_colloquial_amount supports whole rupees from ₹1 to ₹1,00,000")
    rupees = paise // 100
    for unit, word in ((1_000, "हज़ार"), (100, "सौ")):
        whole, part = divmod(rupees, unit)
        if part * 4 % unit or not 1 <= whole <= 99 or (unit == 100 and whole >= 10):
            continue
        quarter = part * 4 // unit
        if quarter == 0 and unit == 100 and rupees % 1_000:
            return f"{_below_100(whole)} सौ"                                       # 300 -> तीन सौ
        if quarter == 2:
            special = {1: "डेढ़", 2: "ढाई"}.get(whole)
            return f"{special} {word}" if special else f"साढ़े {_below_100(whole)} {word}"
        if quarter == 1:
            return f"सवा {word}" if whole == 1 else f"सवा {_below_100(whole)} {word}"
        if quarter == 3:
            return f"पौने {_below_100(whole + 1)} {word}"
    if 1_100 <= rupees <= 9_900 and rupees % 100 == 0 and rupees % 1_000:
        return f"{_below_100(rupees // 100)} सौ"                                   # 1,200 -> बारह सौ
    return render_hindi_amount(paise).removesuffix(" रुपये")
```

- [x] **Step 4: Run the tests.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_numerals.py`. Expected: **149 passed**.
- [x] **Step 5: Commit.** `git add src/parcha/numerals.py tests/test_numerals.py`, then `git commit -m "feat(money): deterministic Hinglish amount grammar"`.

### Task 3: Money path at intake

**Files:** Create `src/parcha/money.py`, `tests/fakes.py`, `tests/test_money_path.py`. Modify `src/parcha/gnani.py:9-15`, `src/parcha/workflow.py`, `tests/conftest.py:44-48`, `tests/test_workflow.py:36-40,119`.

**Interfaces:**
- Consumes: `parse_amounts`, `MAX_ITEM_PAISE` (Task 2).
- Produces:
  - `GnaniError(message, *, status: int | None = None)` with `.status`
  - `money.AbstainReason` (the seven strings)
  - `AmountDecision(paise: int | None, reason: AbstainReason | None, quote: str)`
  - `decide_amounts(verbatim: str, transcribe: str | None, *, expected_count: int) -> list[AmountDecision]`
  - `spoken_item_order(card, transcripts) -> list[str] | None`
  - `settle_card_amounts(card, *, verbatim, transcribe) -> tuple[JobCard, dict[str, AbstainReason]]`
  - `workflow.RepeatRequest(reason)` with `.reason`
  - `workflow.provider_reason(exc) -> AbstainReason | None`
  - `workflow.abstain_logs(abstentions, when) -> tuple[TranscriptLog, ...]`
  - `Workflow._two_passes(wav) -> tuple[str, str]`
  - Abstention logs use `role="system"`, `mode=f"abstain:{field}"` and `text=reason`.

- [x] **Step 1: Write the fake and the failing tests.** `tests/fakes.py` (it also exports the intake texts reused in Task 4):

```python
INTAKE_T = "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
INTAKE_V = "front brake pad saade chaar sau labour do sau Somvaar shaam tak"


class ScriptedPrisma:
    """Fake Prisma returning scripted outputs in call order; an Exception entry is raised instead."""

    def __init__(self, script):
        self.script, self.calls = list(script), []

    def transcribe(self, wav, *, mode, bias=None, score=1.0):
        self.calls.append((wav, mode, bias, score))
        if not self.script:
            raise AssertionError(f"unexpected extra Prisma call (mode={mode})")
        out = self.script.pop(0)
        if isinstance(out, Exception):
            raise out
        return out
```

`tests/test_money_path.py`, as prototyped (the intake tests; Task 4 appends the re-ask tests to the same file):

```python
from datetime import date, datetime

import pytest

from parcha.artefact import audit_manifest
from parcha.gnani import GnaniError
from parcha.schema import Delivery, Evidence, JobCard, LineItem, review_fields
from parcha.session import Conflict, SessionStore
from parcha.workflow import RepeatRequest, Workflow
from tests.fakes import ScriptedPrisma

T_EN = "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
V_EN = "front brake pad saade chaar sau labour do sau Somvaar shaam tak"
T_W2 = "फ्रंट ब्रेक पैड 04:30 100 लेबर 200 मंगलवार शाम तक"          # effort 005, real transcribe output
V_W2 = "फ्रंट ब्रेक पैड साढ़े चार सौ लेबर दो सौ मंगलवार शाम तक"


def card(labels=("front brake pad", "labour"), amounts=(99900, 99900)) -> JobCard:
    """Extractor output with deliberately wrong amounts: the money path must replace them."""
    return JobCard(
        items=[LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=amounts[0]),
               LineItem(id="labour-1", label="labour", kind="labour", amount_paise=amounts[1])],
        delivery=Delivery(date=date(2026, 10, 6), window="evening", spoken="shaam tak"),
        evidence=[Evidence(field="items.part-1.label", quote=labels[0], review_score=0.95),
                  Evidence(field="items.part-1.amount_paise", quote="₹999", review_score=0.95),
                  Evidence(field="items.labour-1.label", quote=labels[1], review_score=0.95),
                  Evidence(field="items.labour-1.amount_paise", quote="₹999", review_score=0.95),
                  Evidence(field="delivery", quote="shaam tak", review_score=0.95)],
    )


class CardExtractor:
    def __init__(self, result):
        self.result = result

    def extract_card(self, normalized, verbatim, recorded_at_utc):
        return self.result

    def extract_field(self, *args, **kwargs):
        raise AssertionError("amount re-ask must not call the extractor")


def service(prisma, extractor):
    store = SessionStore()
    session = store.create()
    return Workflow(store=store, prisma=prisma, extractor=extractor,
                    normalize_audio=lambda b, m: b"RIFFpcm"), store, session.id


def abstentions(session):
    return {log.mode.removeprefix("abstain:"): log.text for log in session.logs if log.mode.startswith("abstain:")}


def test_intake_amounts_come_from_grammar_not_extractor():
    wf, _, sid = service(ScriptedPrisma([T_EN, V_EN]), CardExtractor(card()))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert [it.amount_paise for it in s.card.items] == [45000, 20000]
    assert {ev.field: ev.quote for ev in s.card.evidence}["items.part-1.amount_paise"] == "saade chaar sau"
    assert abstentions(s) == {} and review_fields(s.card) == []


def test_w2_crosscheck_disagreement_abstains_only_the_disputed_item():
    wf, _, sid = service(ScriptedPrisma([T_W2, V_W2]), CardExtractor(card(labels=("फ्रंट ब्रेक पैड", "लेबर"))))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert [it.amount_paise for it in s.card.items] == [None, 20000]
    assert abstentions(s) == {"items.part-1.amount_paise": "crosscheck_disagreement"}


def test_incomplete_number_abstains():
    wf, _, sid = service(ScriptedPrisma([T_EN, "front brake pad saade labour do sau shaam tak"]), CardExtractor(card()))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert [it.amount_paise for it in s.card.items] == [None, 20000]
    assert abstentions(s) == {"items.part-1.amount_paise": "incomplete_number"}


def test_amount_count_mismatch_abstains_every_amount():
    wf, _, sid = service(ScriptedPrisma([T_EN, "front brake pad saade chaar sau"]), CardExtractor(card()))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert [it.amount_paise for it in s.card.items] == [None, None]
    assert set(abstentions(s).values()) == {"ambiguous_attachment"}


def test_spoken_total_that_matches_the_items_is_not_an_extra_item():
    wf, _, sid = service(ScriptedPrisma(["front brake pad ₹450, labour ₹200, kul ₹650, shaam tak",
                                         "front brake pad saade chaar sau labour do sau kul saade chhe sau shaam tak"]),
                         CardExtractor(card()))
    assert [it.amount_paise for it in wf.intake(sid, b"a", "audio/webm", expected_revision=0).card.items] == [45000, 20000]


def test_spoken_total_that_disagrees_with_the_items_abstains_every_amount():
    wf, _, sid = service(ScriptedPrisma(["front brake pad ₹450, labour ₹200, kul ₹700, shaam tak",
                                         "front brake pad saade chaar sau labour do sau kul saat sau shaam tak"]),
                         CardExtractor(card()))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert [it.amount_paise for it in s.card.items] == [None, None]
    assert set(abstentions(s).values()) == {"crosscheck_disagreement"}


def test_mid_sentence_self_correction_abstains_instead_of_guessing():
    wf, _, sid = service(ScriptedPrisma([T_EN, "front brake pad saade chaar sau nahi paanch sau labour do sau"]),
                         CardExtractor(card()))
    assert [it.amount_paise for it in wf.intake(sid, b"a", "audio/webm", expected_revision=0).card.items] == [None, None]


def test_english_label_quotes_absent_from_devanagari_transcripts_abstain():
    wf, _, sid = service(ScriptedPrisma([T_W2, V_W2]), CardExtractor(card()))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert set(abstentions(s).values()) == {"ambiguous_attachment"}


def test_empty_transcripts_request_a_repeat_without_touching_the_session():
    wf, store, sid = service(ScriptedPrisma(["", "  "]), CardExtractor(card()))
    with pytest.raises(RepeatRequest) as info:
        wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert info.value.reason == "empty_transcript" and store.get(sid).revision == 0


@pytest.mark.parametrize("status,reason", [(504, "provider_504"), (429, "provider_429")])
def test_provider_errors_request_a_repeat(status, reason):
    wf, store, sid = service(ScriptedPrisma([GnaniError(f"HTTP {status}", status=status)]), CardExtractor(card()))
    with pytest.raises(RepeatRequest) as info:
        wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert info.value.reason == reason and store.get(sid).revision == 0


def test_other_provider_errors_still_raise_gnani_error():
    wf, _, sid = service(ScriptedPrisma([GnaniError("boom", status=500)]), CardExtractor(card()))
    with pytest.raises(GnaniError):
        wf.intake(sid, b"a", "audio/webm", expected_revision=0)


def test_abstained_card_cannot_be_read_back_and_reason_is_in_audit_manifest():
    wf, store, sid = service(ScriptedPrisma([T_W2, V_W2]), CardExtractor(card(labels=("फ्रंट ब्रेक पैड", "लेबर"))))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    with pytest.raises(Conflict, match="card needs review"):
        store.start_readback(sid, expected_revision=s.revision)
    assert "abstain:items.part-1.amount_paise" in [e["mode"] for e in audit_manifest(store.get(sid))["logs"]]
```

- [x] **Step 2: Run it to see it fail.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_money_path.py`. Expected: `ImportError: cannot import name 'RepeatRequest'`.
- [x] **Step 3: Give `GnaniError` a status.** In `src/parcha/gnani.py`:

```python
class GnaniError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None):
        super().__init__(message)
        self.status = status


def _check_response(response: httpx.Response) -> None:
    if response.status_code != 200:
        raise GnaniError(f"Gnani request failed: HTTP {response.status_code}", status=response.status_code)
```

- [x] **Step 4: Create `src/parcha/money.py`.** The attachment and abstention rules are the decision, so the full body follows:

```python
"""Money path: amounts come only from the numeral grammar; the transcribe pass is a formatting cross-check."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Literal

from .numerals import MAX_ITEM_PAISE, parse_amounts
from .schema import Evidence, JobCard, LineItem

__all__ = ["AbstainReason", "AmountDecision", "decide_amounts", "settle_card_amounts", "spoken_item_order"]

AbstainReason = Literal["incomplete_number", "crosscheck_disagreement", "empty_transcript",
                        "provider_504", "provider_429", "ambiguous_attachment", "out_of_range"]


@dataclass(frozen=True)
class AmountDecision:
    paise: int | None
    reason: AbstainReason | None  # None means accepted
    quote: str


_TOTAL_MARKER = re.compile(r"(?:^|\s)(?:कुल|टोटल|kul|total)(?=\s|$)", re.IGNORECASE)


def _split_spoken_total(text: str) -> tuple[str, str | None]:
    match = _TOTAL_MARKER.search(text)
    return (text, None) if match is None else (text[: match.start()], text[match.end():])


def decide_amounts(verbatim: str, transcribe: str | None, *, expected_count: int) -> list[AmountDecision]:
    """One decision per expected slot. Never guesses: any doubt yields paise=None plus a reason."""
    if not verbatim.strip() or (transcribe is not None and not transcribe.strip()):
        return [AmountDecision(None, "empty_transcript", "")] * expected_count
    body, total_text = _split_spoken_total(verbatim)
    spoken = parse_amounts(body)
    if len(spoken) != expected_count:
        return [AmountDecision(None, "ambiguous_attachment", "")] * expected_count
    if total_text is not None:
        totals = [m.paise for m in parse_amounts(total_text) if m.status == "complete"]
        if totals[:1] != [sum(m.paise or 0 for m in spoken)] or any(m.status != "complete" for m in spoken):
            return [AmountDecision(None, "crosscheck_disagreement", m.text) for m in spoken]
    cross = parse_amounts(_split_spoken_total(transcribe)[0]) if transcribe is not None else None
    counts_differ = cross is not None and len(cross) != len(spoken)
    decisions: list[AmountDecision] = []
    for i, mention in enumerate(spoken):
        if mention.status != "complete" or mention.paise is None:
            decisions.append(AmountDecision(None, "incomplete_number", mention.text))
        elif mention.paise > MAX_ITEM_PAISE:
            decisions.append(AmountDecision(None, "out_of_range", mention.text))
        elif counts_differ or (cross is not None and cross[i].paise != mention.paise):
            decisions.append(AmountDecision(None, "crosscheck_disagreement", mention.text))
        else:
            decisions.append(AmountDecision(mention.paise, None, mention.text))
    return decisions


def _fold(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def spoken_item_order(card: JobCard, transcripts: list[str]) -> list[str] | None:
    """Item ids ordered by where their label-evidence quote first appears; None if any can't be located."""
    positions: list[tuple[float, str]] = []
    for item in card.items:
        quote = next((ev.quote for ev in card.evidence
                      if ev.field == f"items.{item.id}.label" and ev.quote.strip()), item.label or "")
        if not quote.strip():
            return None
        found = None
        for transcript in transcripts:
            text = _fold(transcript)
            at = text.find(_fold(quote))
            if at != -1 and text:
                found = at / len(text)
                break
        if found is None:
            return None
        positions.append((found, item.id))
    return [item_id for _, item_id in sorted(positions)]


def settle_card_amounts(card: JobCard, *, verbatim: str,
                        transcribe: str | None) -> tuple[JobCard, dict[str, AbstainReason]]:
    """Replace every item amount with the grammar's decision; return the new card and per-field abstentions."""
    order = spoken_item_order(card, [t for t in (transcribe, verbatim) if t])
    if order is None:
        decisions = [AmountDecision(None, "ambiguous_attachment", "")] * len(card.items)
        order = [item.id for item in card.items]
    else:
        decisions = decide_amounts(verbatim, transcribe, expected_count=len(card.items))
    by_id = dict(zip(order, decisions))
    items = tuple(LineItem(id=it.id, label=it.label, kind=it.kind, amount_paise=by_id[it.id].paise)
                  for it in card.items)
    evidence = [ev for ev in card.evidence if not ev.field.endswith(".amount_paise")]
    abstentions: dict[str, AbstainReason] = {}
    for item_id, decision in by_id.items():
        field = f"items.{item_id}.amount_paise"
        if decision.reason is None:
            evidence.append(Evidence(field=field, quote=decision.quote, review_score=1.0))
        else:
            abstentions[field] = decision.reason
    return JobCard(items=items, delivery=card.delivery, evidence=tuple(evidence)), abstentions
```

- [x] **Step 5: Wire it into `Workflow.intake`** in `src/parcha/workflow.py`.
  1. Imports: `from .gnani import GnaniError, PrismaClient, TimbreClient`, `from .money import AbstainReason, decide_amounts, settle_card_amounts`, and add `Evidence` to the schema import.
  2. Above `Readback`, add:

  ```python
  class RepeatRequest(RuntimeError):
      """The speaker must say it again; nothing on the card was changed."""

      def __init__(self, reason: AbstainReason):
          super().__init__(reason)
          self.reason = reason


  def provider_reason(exc: GnaniError) -> AbstainReason | None:
      return {504: "provider_504", 429: "provider_429"}.get(exc.status)


  def abstain_logs(abstentions: dict[str, AbstainReason], when: datetime) -> tuple[TranscriptLog, ...]:
      return tuple(TranscriptLog(role="system", mode=f"abstain:{field}", text=reason, recorded_at_utc=when)
                   for field, reason in sorted(abstentions.items()))
  ```

  3. In `intake`, replace the two inline `self.prisma.transcribe` calls and the `extract_card` line with:

  ```python
          normalized, verbatim = self._two_passes(wav)
          if not normalized.strip() and not verbatim.strip():
              raise RepeatRequest("empty_transcript")
          card = self.extractor.extract_card(normalized, verbatim, recorded_at_utc)
          card, abstentions = settle_card_amounts(card, verbatim=verbatim, transcribe=normalized)
  ```

  4. Append `+ abstain_logs(abstentions, recorded_at_utc)` to the `logs` tuple.
  5. Add the method:

  ```python
      def _two_passes(self, wav: bytes) -> tuple[str, str]:
          """Transcribe pass then verbatim pass on the same audio; 504/429 become RepeatRequest."""
          try:
              normalized = self.prisma.transcribe(wav, mode="transcribe")
              verbatim = self.prisma.transcribe(
                  wav, mode="verbatim", bias=list(self.bias_words) if self.use_bias else None)
          except GnaniError as exc:
              reason = provider_reason(exc)
              if reason is None:
                  raise
              raise RepeatRequest(reason) from exc
          return normalized, verbatim
  ```

- [x] **Step 6: Move the shared fakes onto the new path.**
  - In `tests/conftest.py` and in `tests/test_workflow.py`'s `FakePrisma`, change the verbatim reply to `"front brake pad saade chaar sau labour do sau Somvaar shaam tak"`.
  - In `test_workflow.py:119`, assert that same text.
  - Existing totals (₹650) then still hold.
- [x] **Step 7: Run the tests.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_money_path.py tests/test_workflow.py tests/test_app.py`. Expected: all pass. Then the full suite: `.\.venv\Scripts\python.exe -m pytest -q`. Expected: green. `reask` is untouched until Task 4, so its existing test still passes through the extractor.
- [x] **Step 8: Commit.** `git add src/parcha/money.py src/parcha/gnani.py src/parcha/workflow.py tests/fakes.py tests/test_money_path.py tests/conftest.py tests/test_workflow.py`, then `git commit -m "feat(money): amounts only from grammar with abstain-and-re-ask at intake"`.

### Task 4: Amount re-ask uses the same path

**Files:** Modify `src/parcha/workflow.py` (`reask`), `tests/test_workflow.py:257-321`, `tests/test_money_path.py`.

**Interfaces:**
- Consumes: `decide_amounts`, `RepeatRequest`, `abstain_logs`, `_two_passes` (Task 3).
- Produces: `Workflow._reask_amount(session, field, wav, audio_sha256, expected_revision, recorded_at_utc) -> Session`. `reask` keeps its public signature.

- [x] **Step 1: Append the failing tests** to `tests/test_money_path.py`:

```python
def test_amount_reask_uses_grammar_and_keeps_other_fields():
    prisma = ScriptedPrisma([T_W2, V_W2, "₹350", "साढ़े तीन सौ"])
    wf, _, sid = service(prisma, CardExtractor(card(labels=("फ्रंट ब्रेक पैड", "लेबर"))))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    s2 = wf.reask(sid, "items.part-1.amount_paise", b"r", "audio/webm", expected_revision=s1.revision)
    assert [it.amount_paise for it in s2.card.items] == [35000, 20000]
    assert s2.card.delivery == s1.card.delivery and review_fields(s2.card) == []
    assert s2.logs[-1].mode == "reask:items.part-1.amount_paise"
    assert [c[1] for c in prisma.calls[2:]] == ["transcribe", "verbatim"]


def test_amount_reask_with_provider_429_leaves_field_unset_and_logs_reason():
    wf, _, sid = service(ScriptedPrisma([T_EN, V_EN, GnaniError("HTTP 429", status=429)]), CardExtractor(card()))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    s2 = wf.reask(sid, "items.part-1.amount_paise", b"r", "audio/webm", expected_revision=s1.revision)
    assert [it.amount_paise for it in s2.card.items] == [None, 20000]
    assert abstentions(s2)["items.part-1.amount_paise"] == "provider_429"


def test_correction_with_two_numbers_abstains():
    wf, _, sid = service(ScriptedPrisma([T_EN, V_EN, "₹300 ₹350", "teen sau nahi saade teen sau"]), CardExtractor(card()))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    s2 = wf.reask(sid, "items.part-1.amount_paise", b"r", "audio/webm", expected_revision=s1.revision)
    assert s2.card.items[0].amount_paise is None
    assert abstentions(s2)["items.part-1.amount_paise"] == "ambiguous_attachment"
```

In `tests/test_workflow.py::test_reask_updates_single_field_and_increments_revision`, build the service with `prisma=ScriptedPrisma([INTAKE_T, INTAKE_V, "₹500", "paanch sau", "Mangalvaar subah", "rear brake pad"])`, importing `INTAKE_T`, `INTAKE_V` and `ScriptedPrisma` from `tests.fakes`. Keep every existing assertion: the amount becomes 50000 through the grammar, and the delivery and label re-asks still use the extractor.

- [x] **Step 2: Run them to see them fail.** `.\.venv\Scripts\python.exe -m pytest -q tests/test_money_path.py -k "reask or two_numbers"`. Expected: `AssertionError: amount re-ask must not call the extractor`.
- [x] **Step 3: Branch `reask`.** Right after `audio_sha256` is computed:

  ```python
  if field.endswith(".amount_paise"):
      return self._reask_amount(session, field, wav, audio_sha256, expected_revision, recorded_at_utc)
  ```

  Then add `_reask_amount`. It runs `_two_passes`; on `RepeatRequest` it uses `exc.reason`. Otherwise it logs `reask:{field}` with the verbatim text and takes `decide_amounts(verbatim, transcript, expected_count=1)[0]`. It replaces only that item's `amount_paise`. It replaces that field's evidence with `Evidence(field, quote, 1.0)` when accepted; otherwise it removes the evidence and appends `abstain_logs({field: reason}, recorded_at_utc)`. Finally it calls `store.set_card(...)` once.
- [x] **Step 4: Run the tests.** `.\.venv\Scripts\python.exe -m pytest -q`. Expected: all green.
- [x] **Step 5: Commit.** `git commit -am "feat(money): amount re-asks use grammar and cross-check, never the extractor"`

### Task 5: Website: "please say it again" and why an amount is being re-asked

**Files:** Modify `src/parcha/app.py` (`session_payload` at line 70; the `intake` and `reask` handlers at 176–241) and `src/parcha/static/app.js` (intake and re-ask error handling at lines 287–290 and 343–346, plus `renderSession`). Create `tests/test_app_repeat.py`. Runs on the owner's laptop, because the app fixtures need FFmpeg.

**Interfaces:**
- Consumes: `RepeatRequest` (Task 3) and abstention logs (`mode="abstain:{field}"`).
- Produces: HTTP 422 with `detail == {"repeat": true, "reason": <AbstainReason>}`. `session_payload(...)["abstentions"]` is a `dict[field, reason]` holding only fields still in `review_fields`.

- [x] **Step 1: Write the failing tests** `tests/test_app_repeat.py`:

```python
from fastapi.testclient import TestClient

from parcha.app import create_app
from tests.fakes import INTAKE_T, ScriptedPrisma


def post_intake(client, sid):
    return client.post(f"/sessions/{sid}/intake", data={"expected_revision": 0},
                       files={"audio": ("a.wav", b"bytes", "audio/wav")})


def test_empty_transcripts_return_a_structured_repeat_request(fake_services):
    fake_services.workflow.prisma = ScriptedPrisma(["", ""])
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    res = post_intake(client, sid)
    assert res.status_code == 422
    assert res.json()["detail"] == {"repeat": True, "reason": "empty_transcript"}
    assert client.get(f"/sessions/{sid}").json()["revision"] == 0


def test_session_payload_explains_each_amount_awaiting_re_ask(fake_services):
    fake_services.workflow.prisma = ScriptedPrisma([INTAKE_T, "front brake pad saade labour do sau Somvaar shaam tak"])
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    body = post_intake(client, sid).json()
    assert body["abstentions"] == {"items.part-1.amount_paise": "incomplete_number"}
    assert "items.part-1.amount_paise" in body["review_fields"]
```

- [x] **Step 2:** Run `.\.venv\Scripts\python.exe -m pytest -q tests/test_app_repeat.py`. Expected: the first test fails with an HTTP 502 or a text detail; the second with `KeyError: 'abstentions'`.
- [x] **Step 3: Backend** (`src/parcha/app.py`). Import `RepeatRequest` from `.workflow` and `review_fields` from `.schema`. Add:

```python
def abstention_reasons(session) -> dict[str, str]:
    """Latest abstain reason per field, kept only while that field still needs review."""
    pending = set(review_fields(session.card)) if session.card else set()
    reasons: dict[str, str] = {}
    for log in session.logs:
        if log.mode.startswith("abstain:"):
            reasons[log.mode.removeprefix("abstain:")] = log.text
    return {field: reason for field, reason in reasons.items() if field in pending}
```

  Add `"abstentions": abstention_reasons(session),` to the dict that `session_payload` returns. In both the `intake` and `reask` handlers, insert this before `except (AudioError, ExtractionError) as exc:`:

```python
        except RepeatRequest as exc:
            raise HTTPException(422, {"repeat": True, "reason": exc.reason})
```

- [x] **Step 4: Front end** (`src/parcha/static/app.js`). Add near the top:

```js
const REPEAT_MESSAGE = "आवाज़ साफ़ नहीं आई — कृपया फिर से बोलिए (Please say it again)";
const ABSTAIN_LABELS = {
  incomplete_number: "अधूरी रकम — फिर से पूछेंगे",
  crosscheck_disagreement: "रकम पक्की नहीं — फिर से पूछेंगे",
  ambiguous_attachment: "कौन सी रकम किस आइटम की — साफ़ नहीं",
  empty_transcript: "आवाज़ नहीं आई",
  provider_504: "नेटवर्क रुका — फिर से बोलिए",
  provider_429: "बहुत जल्दी-जल्दी — थोड़ा रुककर बोलिए",
  out_of_range: "रकम सीमा से बाहर",
};

function describeHttpError(detail, status) {
  if (detail && typeof detail === "object" && detail.repeat) return REPEAT_MESSAGE;
  return (typeof detail === "string" && detail) || `Server returned HTTP ${status}`;
}
```

  In both the intake handler (line 289) and `handleReask` (line 345), replace `throw new Error(err.detail || \`Server returned HTTP ${res.status}\`);` with `throw new Error(describeHttpError(err.detail, res.status));`. This also fixes the current "[object Object]" message for object details. In `renderSession`, where each entry of `session.review_fields` is drawn, append the label when one exists:

```js
const reason = (session.abstentions || {})[field];
if (reason) {
  const tag = document.createElement("span");
  tag.className = "abstain-reason";
  tag.textContent = ABSTAIN_LABELS[reason] || reason;
  itemEl.appendChild(tag);   // itemEl = the element renderSession already creates for this review field
}
```

  Add `.abstain-reason { margin-left: .5rem; font-size: .85em; color: #b45309; }` to the page stylesheet in `templates/workshop.html`.
- [x] **Step 5: Verify.** Run `.\.venv\Scripts\python.exe -m pytest -q`. Expected: green. Then start `.\.venv\Scripts\python.exe -m uvicorn parcha.app:app --reload --port 8000`, open `/workshop`, record two seconds of silence, and confirm the Hindi repeat message appears and the Record button is enabled again. Record an estimate that ends with a dangling "saade" and confirm the brake-pad amount shows "अधूरी रकम — फिर से पूछेंगे". Check the mobile layout at 390 px width (AGENTS.md: UI changes need the affected flow and mobile check).
- [x] **Step 6:** `git add src/parcha/app.py src/parcha/static/app.js src/parcha/templates/workshop.html tests/test_app_repeat.py`, then `git commit -m "feat(app): repeat request and per-amount re-ask reasons in the workshop UI"`

### Task 6: Evon replaces Groq for line items

**Files:** Modify `src/parcha/config.py:33,43-56`, `src/parcha/extract.py` (`Extractor.__init__`, `_post_chat`, `_parse_json`, `extract_card`, and `CARD_SYSTEM_PROMPT` to "return amount_paise as null"), `src/parcha/app.py:36-40`, `.env.example`, `tests/conftest.py:151-158`, `tests/test_config.py:50-54`. Create `tests/test_extract_evon.py`.

**Interfaces:**
- Produces: `Settings.extractor_provider` defaults to `"evon"`, with no Groq fallback. `Extractor(base_url, api_key, model, http=None, provider="evon")`. `extract.CARD_RESPONSE_SCHEMA`.

- [x] **Step 1: Write the failing tests** `tests/test_extract_evon.py`:

```python
import json
from datetime import datetime, timezone

import httpx
import pytest

from parcha.config import Settings
from parcha.extract import CARD_RESPONSE_SCHEMA, Extractor

WHEN = datetime(2026, 10, 4, 10, tzinfo=timezone.utc)
T = "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
V = "front brake pad saade chaar sau labour do sau Somvaar shaam tak"
CARD = {"items": [{"id": "part-1", "label": "front brake pad", "kind": "part", "amount_paise": None},
                  {"id": "labour-1", "label": "labour", "kind": "labour", "amount_paise": None}],
        "delivery": {"date": "2026-10-05", "window": "evening", "spoken": "Somvaar shaam tak"},
        "evidence": [{"field": "items.part-1.label", "quote": "front brake pad", "review_score": 0.95},
                     {"field": "items.labour-1.label", "quote": "labour", "review_score": 0.95},
                     {"field": "delivery", "quote": "Somvaar shaam tak", "review_score": 0.9}]}


def capture(content, seen):
    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_evon_turns_thinking_off_and_requests_the_card_schema():
    seen = []
    Extractor("http://localhost:8080/v1", "", "gnani-evon-v3.3", capture(json.dumps(CARD), seen)).extract_card(T, V, WHEN)
    assert seen[0]["chat_template_kwargs"] == {"enable_thinking": False}
    assert seen[0]["response_format"] == {"type": "json_schema",
                                          "json_schema": {"name": "job_card", "schema": CARD_RESPONSE_SCHEMA}}


def test_external_provider_sends_a_plain_openai_payload():
    seen = []
    Extractor("http://t/v1", "k", "m", capture(json.dumps(CARD), seen), provider="external").extract_card(T, V, WHEN)
    assert "chat_template_kwargs" not in seen[0] and "response_format" not in seen[0]


def test_reasoning_block_is_stripped_before_parsing():
    card = Extractor("http://l/v1", "", "m", capture("<think>maybe ₹999?</think>" + json.dumps(CARD), [])
                     ).extract_card(T, V, WHEN)
    assert [it.label for it in card.items] == ["front brake pad", "labour"]


def test_groq_key_alone_no_longer_configures_an_extractor():
    settings = Settings.from_mapping({"GROQ_API_KEY": "groq-secret"})
    assert settings.extractor_base_url == "" and settings.extractor_provider == "evon"
    with pytest.raises(ValueError, match="extractor endpoint and model are required"):
        settings.require_extractor()
```

- [x] **Step 2:** Run `.\.venv\Scripts\python.exe -m pytest -q tests/test_extract_evon.py`. Expected: `ImportError: cannot import name 'CARD_RESPONSE_SCHEMA'`.
- [x] **Step 3: Implement.**
  - **`config.py`:** `key = (values.get("EXTRACTOR_API_KEY") or "").strip()`. Delete the Groq default block. The dataclass default and the `from_mapping` default for `extractor_provider` become `"evon"`.
  - **`extract.py`:** add `CARD_RESPONSE_SCHEMA`, an object schema with:
    - `items` (an array of `{id: ^[a-z]+-[0-9]+$, label: string|null, kind: part|labour, amount_paise: integer|null}`, all four required, minItems 1);
    - `delivery` (object|null with `date`, `window` enum, `spoken`);
    - `evidence` (array of `{field, quote, review_score}`, all required);
    - top-level `required ["items","delivery","evidence"]`.

    Add `provider` to `Extractor.__init__`. `_post_chat(messages, schema=None)` adds `chat_template_kwargs={"enable_thinking": False}` when the provider is `"evon"`, plus `response_format`: json_schema when `schema` is set, else `{"type": "json_object"}`. `_parse_json` first applies `re.sub(r"<think>.*?</think>", "", content, flags=re.S)`. `extract_card` calls `_post_chat(messages, schema=CARD_RESPONSE_SCHEMA)`.
  - **`app.py`:** `Extractor(..., provider=settings.extractor_provider)`.
  - **`.env.example`:** `EXTRACTOR_BASE_URL=http://localhost:8080/v1`, `EXTRACTOR_API_KEY=`, `EXTRACTOR_MODEL=gnani-evon-v3.3`, `EXTRACTOR_PROVIDER=evon`.
  - **`conftest.py`:** use those values.
  - **`test_config.py`:** rename the Groq test to `test_settings_have_no_groq_fallback` and assert that all three extractor fields are `""`.
- [x] **Step 4:** Run `.\.venv\Scripts\python.exe -m pytest -q`. Expected: green. Live smoke test against a running `llama-server` (Evon Q8_0 per R7 §3): `curl.exe http://localhost:8080/v1/models` lists the model, and one intake on `/workshop` shows labels with amounts set by the grammar.
- [x] **Step 5:** `git commit -am "feat(extract): Evon as the line-item extractor; no Groq fallback"`

### Task 7: Line Noise Lab: canonical references, outcomes, labels, bias control

**Files:** Modify `src/parcha/lab/metrics.py`, `src/parcha/lab/dataset.py:13,29,96`, `src/parcha/lab/runner.py:18,53,67-68,478-486,505-558`. Create `tests/test_lab_v2_runner.py`, `data/benchmarks/exclusions.json`.

**Interfaces:**
- Produces:
  - `canonical_reference(text: str) -> str`
  - `Clip`: `id` pattern `^[a-z][0-9]{3,4}$`, plus `expected_amounts_paise: list[int] = []`, `voice: str | None`, `audio_sha256: str | None`
  - runner rows gain `reference_canonical`, `outcome ∈ {"ok","empty_transcript","provider_error"}`, `expected_amounts_paise`, `cer_canonical`
  - `stt_modes` accepts `"verbatim_nobias"`, which calls Prisma verbatim with no bias

- [x] **Step 1: Write the failing tests** `tests/test_lab_v2_runner.py`. They run without FFmpeg because `codecs=["none"]`:

```python
import json

import numpy as np

from parcha.audio import _write_pcm
from parcha.lab.dataset import load_manifest
from parcha.lab.metrics import canonical_reference
from parcha.lab.runner import Runner, RunnerConfig


def wav(seconds=1.0):
    t = np.arange(int(8000 * seconds))
    return _write_pcm((4000 * np.sin(2 * np.pi * 440 * t / 8000)).astype("<i2"))


def manifest(tmp_path, bom=False):
    audio = tmp_path / "audio"
    audio.mkdir()
    (audio / "g0001.wav").write_bytes(wav())
    row = {"id": "g0001", "text": "मॉडल model <stammers> चार सौ", "reference_transcribe": "मॉडल model <stammers> चार सौ",
           "entities": {}, "audio": "g0001.wav", "kind": "speech", "seed": 1, "source": "open_dataset",
           "expected_amounts_paise": [40000]}
    path = tmp_path / "m.jsonl"
    path.write_text(("﻿" if bom else "") + json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    return path, audio


class Replies:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def transcribe(self, wav, *, mode, bias=None):
        self.calls.append((mode, bias))
        return self.replies.pop(0)


def config(path, audio, tmp_path, **kw):
    return RunnerConfig(manifest_path=path, audio_root=audio, output_path=tmp_path / "out.jsonl", codecs=["none"],
                        snr_dbs=[None], loss_percents=[0.0], max_credits=10, remaining_credits=10, **kw)


def test_canonical_reference_drops_glosses_and_tags():
    assert canonical_reference("मॉडल model <stammers> करंट Current [noise] चार सौ") == "मॉडल करंट चार सौ"


def test_four_digit_ids_and_amount_labels_load(tmp_path):
    clip = load_manifest(*manifest(tmp_path))[0]
    assert clip.id == "g0001" and clip.expected_amounts_paise == [40000]


def test_manifest_with_utf8_bom_loads(tmp_path):
    assert load_manifest(*manifest(tmp_path, bom=True))[0].id == "g0001"


def test_rows_carry_canonical_reference_outcome_and_labels(tmp_path):
    path, audio = manifest(tmp_path)
    row = Runner(config(path, audio, tmp_path), client=Replies("मॉडल चार सौ")).run()[0]
    assert row["reference_canonical"] == "मॉडल चार सौ"
    assert row["cer_canonical"] == 0.0 and row["cer"] > 0.0
    assert row["outcome"] == "ok" and row["expected_amounts_paise"] == [40000]


def test_empty_success_is_recorded_as_empty_transcript(tmp_path):
    path, audio = manifest(tmp_path)
    row = Runner(config(path, audio, tmp_path), client=Replies("   ")).run()[0]
    assert row["outcome"] == "empty_transcript" and row["cer_canonical"] is None


def test_bias_control_runs_verbatim_with_and_without_bias(tmp_path):
    path, audio = manifest(tmp_path)
    client = Replies("a", "b")
    rows = Runner(config(path, audio, tmp_path, stt_modes=["verbatim", "verbatim_nobias"], bias_words=["brake"]),
                  client=client).run()
    assert client.calls == [("verbatim", ["brake"]), ("verbatim", None)]
    assert [r["stt_mode"] for r in rows] == ["verbatim", "verbatim_nobias"]
```

- [x] **Step 2:** Run `.\.venv\Scripts\python.exe -m pytest -q tests/test_lab_v2_runner.py`. Expected: `ImportError: cannot import name 'canonical_reference'`.
- [x] **Step 3: Implement.**
  - **`canonical_reference`** in `metrics.py`, with the same rule as `scripts/analyze_real_audio_benchmark.py::clean_reference`: strip `<…>` and `[…]`; drop a Latin-only token that directly follows a Devanagari token.
  - **`Clip`:** widen the pattern and add the three fields. `load_manifest` reads with `encoding="utf-8-sig"`.
  - **Runner:**
    - extend the `stt_modes` literal and validation;
    - call Prisma with `api_mode = "verbatim" if stt_mode == "verbatim_nobias" else stt_mode`, sending bias only for `"verbatim"`;
    - compute `reference_canonical`;
    - `outcome = "provider_error" if transcription_error else "empty_transcript" if not (transcript or "").strip() else "ok"`;
    - add the four row keys, with `cer_canonical` set only when `outcome == "ok"`.
  - **`data/benchmarks/exclusions.json`:** `{"i036": "reference/audio mismatch (R9 §3)", "y001": "auto-caption pseudo-reference", "y002": "auto-caption pseudo-reference", "y003": "auto-caption pseudo-reference", "y004": "auto-caption pseudo-reference", "y005": "auto-caption pseudo-reference"}`.
- [x] **Step 4:** Run `.\.venv\Scripts\python.exe -m pytest -q`. Expected: green. Reproduce R9 to confirm nothing moved: `py -3 scripts/analyze_real_audio_benchmark.py data/benchmarks/real_audio_2026-10 var/lab/real_audio_analysis.md` prints `wrote … (65 lines)`.
- [x] **Step 5:** `git commit -am "feat(lab): canonical references, explicit empty outcome, amount labels, bias control mode"`

### Task 8: Money evaluator

**Files:** Create `src/parcha/lab/money_eval.py` with a `__main__` CLI, and tests in `tests/test_benchmark_v2.py` (money-eval part).

**Interfaces:**
- Consumes: `decide_amounts` (Task 3), `canonical_reference` (Task 7), runner rows (Task 7).
- Produces:
  - `AmountOutcome(clip_id, condition, slice, expected_paise, decided_paise, reason)` with `.kind ∈ {"correct","wrong_accepted","abstained"}`
  - `score_rows(rows, expected: dict[str, list[int]], slices: dict[str, str]) -> list[AmountOutcome]`
  - `summarize(outcomes) -> list[dict]`, with keys `slice, condition, amounts, wrong_accepted, correct, abstained, wrong_amount_confirmed_rate, wrong_amount_confirmed_upper95, abstain_rate, abstain_reasons`
  - `wilson_upper(failures, n, z=1.96) -> float`
  - `score_number_agreement(reference, hypothesis) -> dict` with keys `ref_numbers, matched, confident_wrong, abstain_equivalent`
  - CLI: `python -m parcha.lab.money_eval --results R.jsonl [--results R2.jsonl] --manifest M.jsonl [--manifest M2.jsonl] --out var/lab/money_eval.json`

- [x] **Step 1: Write the failing tests:**

```python
import pytest

from parcha.lab.money_eval import score_number_agreement, score_rows, summarize, wilson_upper


def row(clip, mode, transcript, codec="amr_nb_4750", snr=0.0, error=None):
    return {"clip_id": clip, "stt_mode": mode, "codec": codec, "snr": snr, "transcript": transcript,
            "transcription_error": error}


def test_money_eval_counts_wrong_accepted_and_abstentions():
    expected = {"v001": [45000, 20000], "v002": [45000, 20000]}
    rows = [row("v001", "transcribe", "ब्रेक पैड 450 लेबर 200"), row("v001", "verbatim", "ब्रेक पैड साढ़े चार सौ लेबर दो सौ"),
            # both passes mishear identically: agreement cannot catch it -> counted, not hidden
            row("v002", "transcribe", "ब्रेक पैड 350 लेबर 200"), row("v002", "verbatim", "ब्रेक पैड साढ़े तीन सौ लेबर दो सौ")]
    t = summarize(score_rows(rows, expected, {"v001": "scripted_estimate", "v002": "scripted_estimate"}))[0]
    assert (t["amounts"], t["correct"], t["wrong_accepted"]) == (4, 3, 1)
    assert t["wrong_amount_confirmed_upper95"] > t["wrong_amount_confirmed_rate"]


def test_money_eval_treats_provider_errors_as_abstentions():
    rows = [row("c001", "transcribe", None, error="HTTP 504"), row("c001", "verbatim", "साढ़े तीन सौ")]
    t = summarize(score_rows(rows, {"c001": [35000]}, {"c001": "correction"}))[0]
    assert t["abstained"] == 1 and t["abstain_reasons"] == {"provider_error": 1}


def test_wilson_upper_bound_is_not_zero_when_no_failures():
    assert 0.0 < wilson_upper(0, 480) < 0.01 and wilson_upper(0, 0) == 1.0


@pytest.mark.parametrize("hypothesis,expected", [
    ("लगभग ढाई सौ से अधिक बाल", (1, 0, 0)), ("लगभग डेढ़ सौ से अधिक बाल", (0, 1, 0)), ("लगभग से अधिक बाल", (0, 0, 1)),
])
def test_gramvaani_number_agreement(hypothesis, expected):
    got = score_number_agreement("लगभग ढाई सौ से अधिक बाल", hypothesis)
    assert (got["matched"], got["confident_wrong"], got["abstain_equivalent"]) == expected
```

- [x] **Step 2:** Run `.\.venv\Scripts\python.exe -m pytest -q tests/test_benchmark_v2.py -k "money_eval or wilson or agreement"`. Expected: `ModuleNotFoundError: parcha.lab.money_eval`.
- [x] **Step 3: Implement.**
  - `score_rows` joins `transcribe` and `verbatim` rows by clip and full runner condition. Standard labels remain `{codec}|clean` or `{codec}|{snr}`; fractional SNRs retain precision, and non-default loss/impulse profiles are appended to the label. A provider-error row yields `reason="provider_error"` for every expected amount even when the counterpart row is missing; otherwise paired rows use `decide_amounts(verbatim, transcribe, expected_count=len(expected))`.
  - `wilson_upper` is the standard Wilson score upper bound.
  - `score_number_agreement` applies `canonical_reference` to the reference and keeps the complete grammar values. A count mismatch marks every reference number as `abstain_equivalent`. Otherwise it compares position by position: incomplete → abstain, equal → matched, else confident_wrong.
  - The CLI reads all repeated result files and manifests with `utf-8-sig`, builds `expected` and `slices` (from `stratum`), skips clips listed in `data/benchmarks/exclusions.json`, and writes the summary JSON.
- [x] **Step 4:** Run `.\.venv\Scripts\python.exe -m pytest -q`. Expected: green.
- [x] **Step 5:** `git add src/parcha/lab/money_eval.py tests/test_benchmark_v2.py`, then `git commit -m "feat(lab): money evaluator with Wilson bounds and Gramvaani number agreement"`

- **Task 8 validation:** 10 passed in `tests/test_benchmark_v2.py`; 433 passed in the full offline suite. `git diff --check` passed. No live APIs were called.

### Task 9: Gold-first v2 data (estimates, corrections, stress amounts, bias control)

**Files:** Create `src/parcha/lab/amount_bench.py` and `scripts/make_amount_benchmark.py`. Extend `tests/test_benchmark_v2.py`. Output: `data/benchmarks/amount_v2/{estimates.jsonl, corrections.jsonl, stress_rupees.json, bias_control.jsonl}`.

**Interfaces:**
- Produces:
  - `HINDI_TIMBRE_VOICES` (13 names, as in Verified Facts)
  - `PARTS`, `PART_AMOUNTS_RUPEES`, `LABOUR_RUPEES`, `DELIVERIES`, `STRESS_RUPEES`
  - `make_estimates(n=120, seed=20261005) -> list[dict]`
  - `make_corrections(n=40, seed=20261006) -> list[dict]`
  - `make_bias_control(n=20, seed=20261007) -> list[dict]`
  - Each row is `Clip`-valid, with `expected_amounts_paise` in spoken order and a `voice`.

- [x] **Step 1: Write the failing tests:**

```python
import pytest

from parcha.lab.amount_bench import (HINDI_TIMBRE_VOICES, STRESS_RUPEES, make_bias_control, make_corrections,
                                     make_estimates)
from parcha.numerals import parse_amounts, render_colloquial_amount


@pytest.mark.parametrize("rupees,spoken", [
    (450, "साढ़े चार सौ"), (150, "डेढ़ सौ"), (250, "ढाई सौ"), (125, "सवा सौ"), (175, "पौने दो सौ"),
    (1500, "डेढ़ हज़ार"), (1250, "सवा हज़ार"), (1750, "पौने दो हज़ार"), (1200, "बारह सौ"),
    (3500, "साढ़े तीन हज़ार"), (2050, "दो हज़ार पचास"), (75, "पचहत्तर"),
])
def test_colloquial_forms(rupees, spoken):
    assert render_colloquial_amount(rupees * 100) == spoken


@pytest.mark.parametrize("rupees", sorted(set(STRESS_RUPEES)))
def test_colloquial_render_round_trips_through_the_grammar(rupees):
    assert [(m.status, m.paise) for m in parse_amounts(render_colloquial_amount(rupees * 100))] == [("complete", rupees * 100)]


def test_estimates_are_deterministic_labelled_and_parse_back_exactly():
    rows = make_estimates()
    assert len(rows) == 120 and rows == make_estimates()
    assert {r["voice"] for r in rows} <= set(HINDI_TIMBRE_VOICES) and len({r["voice"] for r in rows}) >= 10
    for r in rows:
        assert [m.paise for m in parse_amounts(r["text"]) if m.status == "complete"] == r["expected_amounts_paise"]


def test_corrections_are_single_amount_replies():
    rows = make_corrections()
    assert len(rows) == 40 and all(r["kind"] == "reply" for r in rows)
    assert all([m.paise for m in parse_amounts(r["text"])] == r["expected_amounts_paise"] for r in rows)


def test_bias_control_uses_only_product_bias_words():
    from parcha.vocabulary import AUTOMOTIVE_BIAS_WORDS
    rows = make_bias_control()
    assert len(rows) == 20 and all(r["stratum"] == "bias_control" for r in rows)
    assert all(r["entities"]["bias_word"] in AUTOMOTIVE_BIAS_WORDS for r in rows)
```

- [x] **Step 2:** Run `.\.venv\Scripts\python.exe -m pytest -q tests/test_benchmark_v2.py`. Expected: `ModuleNotFoundError: parcha.lab.amount_bench`.
- [x] **Step 3: Implement `amount_bench.py`.** The tables below are the decision (the hard spoken forms and near-collisions are over-represented on purpose); the generators follow them:

```python
HINDI_TIMBRE_VOICES = ("Nalini", "Bhavna", "Yashvi", "Urmila", "Jwala", "Chitra", "Ambuja",
                       "Deepak", "Roopesh", "Vikrant", "Hemraj", "Jalaj", "Omkar")
PARTS = ("ब्रेक पैड", "क्लच प्लेट", "चेन स्प्रॉकेट", "एयर फ़िल्टर", "इंजन ऑयल", "स्पार्क प्लग", "बैटरी", "बेयरिंग",
         "टायर", "ट्यूब", "हेडलाइट", "कार्बोरेटर", "शॉकर", "साइलेंसर", "क्लच केबल", "गियर ऑयल")
PART_AMOUNTS_RUPEES = (120, 150, 175, 200, 250, 300, 350, 450, 480, 500, 650, 750, 900, 1050, 1200, 1250, 1500,
                       1750, 2050, 2500, 3500, 4200, 7500, 10500)
LABOUR_RUPEES = (50, 100, 150, 200, 250, 300, 350, 400, 500)
DELIVERIES = ("सोमवार शाम तक", "कल सुबह तक", "बुधवार दोपहर तक", "आज शाम तक")
STRESS_RUPEES = (125, 150, 175, 225, 250, 275, 350, 375, 450, 950, 1050, 1150, 1250, 1500, 1750, 1950, 2250,
                 2500, 3500, 4500, 5000, 5050, 5500, 7500, 9900, 10050, 10500, 12000, 15000, 25000, 35000,
                 45000, 50500, 75000, 99000, 99999, 100000, 1500, 450, 350)
```

  - **`make_estimates`:** `Random(seed)`. Per row:
    - 1–2 parts from `PARTS` plus a labour line;
    - amounts from the tables;
    - 70% colloquial wording (`render_colloquial_amount`), otherwise standard (`render_hindi_amount(...).removesuffix(" रुपये")`);
    - text `"{part} {amount}, …, लेबर {amount}, {delivery}"`, which is also `reference_transcribe`;
    - id `v001…`, `source="timbre"`, `stratum="scripted_estimate"`, `voice=rng.choice(HINDI_TIMBRE_VOICES)`.
  - **`make_corrections`:** `"{opener} {colloquial(STRESS_RUPEES[k])} बोला था"`, with openers `("नहीं,", "नहीं नहीं,", "गलत है,", "", "भैया,")`, `kind="reply"`, ids `c001…`, `stratum="correction"`.
  - **`make_bias_control`:** 20 short Devanagari sentences, each containing one product bias word that is rare in everyday speech. It cycles through this table, with the sentence frames `("{} बदलना पड़ेगा", "{} में आवाज़ आ रही है", "नया {} लगाना है", "{} चेक कर लो")`, `entities={"bias_word": word}`, ids `b001…`, `stratum="bias_control"`, and a random voice:

```python
BIAS_CONTROL_WORDS = (("alternator", "अल्टरनेटर"), ("camshaft", "कैमशाफ्ट"), ("carburetor", "कार्बोरेटर"),
                      ("caliper", "कैलिपर"), ("gasket", "गैसकेट"), ("bearing", "बेयरिंग"), ("clutch", "क्लच"),
                      ("axle", "एक्सल"))
```
  - **The script:** validates every row with `Clip.model_validate` and writes the four files. It prints `estimates=120 (amounts=296) corrections=40 stress_amounts=37`.
- [x] **Step 4:** Run `.\.venv\Scripts\python.exe -m pytest -q`, then `.\.venv\Scripts\python.exe scripts/make_amount_benchmark.py`. Expected: the counts line above.
- [x] **Step 5:** `git add src/parcha/lab/amount_bench.py scripts/make_amount_benchmark.py data/benchmarks/amount_v2 tests/test_benchmark_v2.py`, then `git commit -m "feat(bench): gold-first amount-labelled v2 set, corrections, stress amounts, bias control"`

### Task 10: Render the synthetic slices with Timbre (multi-voice)

**Files:** Create `scripts/render_amount_benchmark.py` and `tests/test_render_forecast.py`.

**Interfaces:**
- Produces: `forecast(rows) -> {"rows", "chars", "credits", "voices"}` using `TTS_CREDITS_PER_CHAR = 0.05`.
- CLI: `--manifest`, `--audio-dir var/benchmark_audio/amount_v2`, `--live`, `--request-interval-seconds 1.0`.
- Live: one `TimbreClient(settings.api_key, voice=row["voice"], base_url=settings.gnani_base_url)` per voice; `mulaw_to_wav(client.synthesize(text))` written to `audio-dir/row["audio"]`; existing files are skipped (cache).

- [x] **Step 1: Failing test:** `forecast([{"text": "abcd", "voice": "Nalini"}] * 3) == {"rows": 3, "chars": 12, "credits": 0.6, "voices": ["Nalini"]}`.
- [x] **Step 2:** Run it. Expected: FAIL (no module).
- [x] **Step 3:** Implement as above. Read the manifest with `utf-8-sig`.
- [x] **Step 4: Dry-run forecasts.** Count the exact `text` codepoints sent to Timbre. Estimates: 120 rows, 7,140 chars, 357.00 credits; corrections: 40 rows, 1,084 chars, 54.20 credits; bias control: 20 rows, 418 chars, 20.90 credits. The earlier estimates/corrections figures (6,843 / 342.15 and 1,080 / 54.0) did not match the generated manifests.
- [x] **Step 5: Live render.** On 2026-10-06, the owner confirmed hackathon-provided API keys, sufficient credits, and authorized the 432.1-credit forecast. Generated 120 estimate, 40 correction, and 20 bias-control WAVs (180 total). `ffprobe` confirmed `pcm_s16le`, 8 kHz, mono for one file from each manifest. The exact console balance and billed amount were not independently captured; organizer/Gramvaani outreach remains pending for later public or real-data runs.
- [x] **Step 6:** `git add scripts/render_amount_benchmark.py tests/test_render_forecast.py`, then `git commit -m "feat(bench): multi-voice Timbre renderer with per-character forecast"`

### Task 11: Owner extempore takes (internal)

**Files:** Create `scripts/register_owner_takes.py`, `data/benchmarks/amount_v2/owner_prompt_sheet.md`, `tests/test_register_owner_takes.py`.

- [ ] **Step 1: Failing test.** `register(prompt_rows, take_files)` maps `o001.wav` → `expected_amounts_paise` of prompt `o001`. It sets `source="consented_script"`, `stratum="owner_extempore"`, `voice=None`, and raises `ValueError` for a take without a prompt.
- [ ] **Step 2:** Run it. Expected: FAIL.
- [ ] **Step 3:** The prompt sheet lists 80 cards: parts and amounts in digits, never a script to read. The owner records each as natural speech beside a running scooter, on a phone, as `var/benchmark_audio/owner/o001.wav…`. The script writes `var/benchmark_audio/owner/manifest.jsonl` (ignored), normalised to 8 kHz with `normalize_upload(…, sample_rate=8000)`.
- [ ] **Step 4:** Run `.\.venv\Scripts\python.exe -m pytest -q`. Expected: green.
- [ ] **Step 5:** `git add scripts/register_owner_takes.py data/benchmarks/amount_v2/owner_prompt_sheet.md tests/test_register_owner_takes.py`, then `git commit -m "feat(bench): owner extempore takes registration (kept internal)"`

### Task 12: Gramvaani real-telephone slice

**Files:** Create `src/parcha/lab/gramvaani.py`, `scripts/prepare_gramvaani.py`, `tests/test_gramvaani.py`. Modify `pyproject.toml` to add `bench = ["pyarrow>=15"]`. Output: `data/benchmarks/gramvaani/index.jsonl` (committed). Audio and the text manifest go under `var/benchmark_audio/gramvaani/` (ignored).

**Interfaces:**
- Produces:
  - `SOURCE_DATASET`, `SOURCE_LICENSE`
  - `downsample_16k_to_8k(samples: np.ndarray) -> np.ndarray`
  - `wav16k_to_wav8k(blob: bytes) -> bytes`
  - `source_clipped(blob: bytes) -> bool`
  - `prepare(parquet_path: Path, audio_dir: Path) -> list[dict]`

- [ ] **Step 1: Write the failing tests:**

```python
import io, wave
import numpy as np
import pytest

from parcha.audio import _read_pcm
from parcha.lab.gramvaani import downsample_16k_to_8k, source_clipped, wav16k_to_wav8k


def wav_at(samples, rate=16000):
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples.astype("<i2").tobytes())
    return out.getvalue()


def tone(hz, amp=10000, n=16000):
    return (amp * np.sin(2 * np.pi * hz * np.arange(n) / 16000)).astype("<i2")


def rms(x):
    return float(np.sqrt(np.mean(x.astype(float) ** 2)))


def test_output_is_runner_ready_8k_and_keeps_duration():
    pcm = _read_pcm(wav16k_to_wav8k(wav_at(tone(1000))))   # raises unless 8 kHz mono 16-bit
    assert len(pcm) == 8000


def test_anti_alias_removes_6khz_and_keeps_1khz():
    assert rms(downsample_16k_to_8k(tone(6000))) < 50 < 5000 < rms(downsample_16k_to_8k(tone(1000)))


def test_overshoot_is_scaled_not_clipped_and_source_clipping_is_flagged():
    square = np.where(np.sin(2 * np.pi * 300 * np.arange(16000) / 16000) >= 0, 32767, -32767).astype("<i2")
    out = np.abs(downsample_16k_to_8k(square).astype(np.int32))
    assert int(out.max()) <= 32767
    flat_top = (out[1:] >= 32767) & (out[:-1] >= 32767)   # hard clipping = runs of full-scale samples
    assert int(flat_top.sum()) == 0                       # isolated equal peaks after scaling are fine
    assert source_clipped(wav_at(square)) and not source_clipped(wav_at(tone(1000)))


def test_rejects_non_16k_input():
    with pytest.raises(ValueError, match="expected 16 kHz mono 16-bit WAV"):
        wav16k_to_wav8k(wav_at(tone(1000)[:8000], rate=8000))
```

- [ ] **Step 2:** Run `.\.venv\Scripts\python.exe -m pytest -q tests/test_gramvaani.py`. Expected: `ModuleNotFoundError`.
- [ ] **Step 3: Create `src/parcha/lab/gramvaani.py`.** This is the verified version: on the real parquet it wrote 1,032 clips with 10,063.6 s preserved, attenuated a 6 kHz tone to RMS 14 against 7,070 for a 1 kHz tone, and added no hard clipping.

```python
"""Gramvaani real-telephone slice: Vistaar test parquet -> 8 kHz mono WAVs + Line Noise Lab manifest rows.
Evaluation only; audio and reference text stay in ignored var/."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import wave

import numpy as np

SOURCE_DATASET = "Trelis/vistaar-hi-gramvaani-test"
SOURCE_LICENSE = "gramvaani-asr-2022: academic use; commercial use by permission (contact@gramvaani.org)"
_TAPS = 63


def _lowpass_taps(cutoff_ratio: float = 0.45) -> np.ndarray:
    """Windowed-sinc low-pass; cutoff as a fraction of the output Nyquist (8 kHz output -> 3.6 kHz)."""
    n = np.arange(_TAPS) - (_TAPS - 1) / 2
    taps = np.sinc(cutoff_ratio * n) * np.hamming(_TAPS)
    return taps / taps.sum()


def downsample_16k_to_8k(samples: np.ndarray) -> np.ndarray:
    """Factor-2 decimation after anti-alias filtering; never upsamples. Overshoot scales the clip, never clips."""
    decimated = np.convolve(samples.astype(np.float64), _lowpass_taps(), mode="same")[::2]
    peak = float(np.max(np.abs(decimated))) if len(decimated) else 0.0
    if peak > 32767:
        decimated *= 32767 / peak
    return np.rint(decimated).astype("<i2")


def source_clipped(blob: bytes) -> bool:
    """True when the 16 kHz source already has full-scale samples (authentic IVR clipping: 291/1,032 clips)."""
    with wave.open(io.BytesIO(blob)) as w:
        s = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    return bool(len(s)) and int(np.max(np.abs(s.astype(np.int32)))) >= 32767


def wav16k_to_wav8k(blob: bytes) -> bytes:
    with wave.open(io.BytesIO(blob)) as w:
        if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (16000, 1, 2):
            raise ValueError("expected 16 kHz mono 16-bit WAV")
        samples = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(downsample_16k_to_8k(samples).tobytes())
    return out.getvalue()


def prepare(parquet_path: Path, audio_dir: Path) -> list[dict]:
    """Write g0001.wav … and return Clip-compatible manifest rows."""
    import pyarrow.parquet as pq

    table = pq.read_table(parquet_path)
    audio_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for k, (audio, text) in enumerate(zip(table.column("audio").to_pylist(), table.column("text").to_pylist()), 1):
        clip_id = f"g{k:04d}"
        wav8k = wav16k_to_wav8k(audio["bytes"])
        (audio_dir / f"{clip_id}.wav").write_bytes(wav8k)
        rows.append({"id": clip_id, "text": text, "reference_transcribe": text, "entities": {},
                     "audio": f"{clip_id}.wav", "kind": "speech", "seed": 0, "source": "open_dataset",
                     "source_dataset": SOURCE_DATASET, "source_license": SOURCE_LICENSE,
                     "source_row": audio["path"],
                     "stratum": "gramvaani_clipped" if source_clipped(audio["bytes"]) else "gramvaani_unclipped",
                     "reference_type": "dataset_reference", "audio_sha256": hashlib.sha256(wav8k).hexdigest()})
    return rows
```

  `scripts/prepare_gramvaani.py`:
  - arguments: `--parquet` (required), `--audio-dir var/benchmark_audio/gramvaani`, `--index data/benchmarks/gramvaani/index.jsonl`;
  - validates each row with `Clip`;
  - writes the full manifest (with text) next to the audio;
  - writes the committed index with only `id, source_row, audio_sha256, stratum, duration_s`;
  - prints the totals and the two-pass credit forecast.
- [ ] **Step 4: Download, prepare and check:**

```powershell
New-Item -ItemType Directory -Force var\benchmark_audio\gramvaani | Out-Null
curl.exe -L -o var\benchmark_audio\gramvaani\test.parquet https://huggingface.co/datasets/Trelis/vistaar-hi-gramvaani-test/resolve/main/data/test-00000-of-00001.parquet
(Get-Item var\benchmark_audio\gramvaani\test.parquet).Length          # 320201217
.\.venv\Scripts\python.exe scripts/prepare_gramvaani.py --parquet var\benchmark_audio\gramvaani\test.parquet
# expected: clips=1032 total_s=10063.6 (2.80 h) forecast_credits_both_passes=4025.4
.\.venv\Scripts\python.exe -m pytest -q
```

- [ ] **Step 5:** `git add src/parcha/lab/gramvaani.py scripts/prepare_gramvaani.py tests/test_gramvaani.py pyproject.toml data/benchmarks/gramvaani/index.jsonl`, then `git commit -m "feat(bench): Gramvaani real-telephone slice preparation (index only committed)"`

### Task 13: Timbre echo test

**Files:** Modify `src/parcha/readback.py` (`make_readback(card, *, include_consent=False, amount_style="digits")`). Create `src/parcha/lab/echo.py`, `scripts/run_echo_test.py`, and the echo tests in `tests/test_benchmark_v2.py`.

**Interfaces:**
- Consumes: `render_hindi_amount` (Task 2), `parse_amounts`, `HINDI_TIMBRE_VOICES`, `STRESS_RUPEES`, `make_estimates` (Task 9).
- Produces:
  - `EchoRow(card_id, voice, style, condition, expected_paise, heard_paise, transcript, passed, tts_ms)`
  - `expected_sequence(card) -> tuple[int, ...]` (items, then total)
  - `score_echo(card, transcript) -> (heard, passed)`
  - `run_echo(cards, voices, styles, conditions, *, synthesize, degrade, transcribe) -> list[EchoRow]`
  - Script stages `screen` (13 voices × {digits, words} × 37 stress cards) and `confirm` (top 3 pairs ranked on `amr_nb_4750|0`, on the 120 estimate cards)
  - Conditions: `["control", "g711|clean", "amr_nb_4750|0"]`

- [ ] **Step 1: Write the failing tests:**

```python
from parcha.lab.echo import expected_sequence, run_echo, score_echo
from parcha.numerals import parse_amounts
from parcha.readback import make_readback
from tests.test_schema import sample_card


def test_readback_words_style_speaks_amounts_as_hindi_words():
    text = make_readback(sample_card(), amount_style="words")
    assert "चार सौ पचास रुपये" in text and "₹" not in text
    assert [m.paise for m in parse_amounts(text)] == [45000, 20000, 65000]


def test_echo_scores_each_voice_style_condition_and_reuses_one_synthesis():
    calls = {"tts": 0}

    def synthesize(text, voice):
        calls["tts"] += 1
        return text.encode(), 120.0

    def degrade(wav, condition):   # the 2G line garbles ₹450 into ₹350
        return wav.replace("₹450".encode(), "₹350".encode()) if condition == "amr_nb_4750|0" else wav

    rows = run_echo({"k1": sample_card()}, ["Nalini", "Deepak"], ["digits"], ["control", "g711|clean", "amr_nb_4750|0"],
                    synthesize=synthesize, degrade=degrade, transcribe=lambda wav: wav.decode())
    assert calls["tts"] == 2 and len(rows) == 6
    assert [r.passed for r in rows if r.condition == "amr_nb_4750|0"] == [False, False]
    assert expected_sequence(sample_card()) == (45000, 20000, 65000) and score_echo(sample_card(), "")[1] is False
```

- [ ] **Step 2:** Run `.\.venv\Scripts\python.exe -m pytest -q tests/test_benchmark_v2.py -k "echo or readback"`. Expected: FAIL with `TypeError: make_readback() got an unexpected keyword argument 'amount_style'`.
- [ ] **Step 3: Implement.**
  - **`make_readback`:** a local `money(paise)` returns `format_rupees(paise)` for `"digits"` and `render_hindi_amount(paise)` for `"words"`, used for each item and the total.
  - **`echo.py`:** synthesize once per (card, voice, style), then reuse that audio for every condition. The control condition skips `degrade`.
  - **`scripts/run_echo_test.py --live`:**
    - Synthesis: `TimbreClient(..., voice=v).synthesize` → `mulaw_to_wav`.
    - Degrade: `mix_at_snr(wav, noise8k, 0.0)` for `|0`, then `codec_round_trip(…, codec)`. `noise8k = normalize_upload(DEFAULT_TELEPHONY_NOISE_PATH.read_bytes(), "audio/wav", sample_rate=8000)`.
    - Transcribe: `PrismaClient.transcribe(wav, mode="verbatim")` with a 1 s spacing.
    - Output: `var/lab/echo_{stage}.jsonl`.
    - The read-back runs **without** the DPDP consent sentence, because "DPDP Act 2023" would parse as a number.
- [ ] **Step 4: Verify the forecasts, then run live:**

```powershell
.\.venv\Scripts\python.exe scripts/run_echo_test.py --stage screen     # {"cards": 37, "voice_style_pairs": 26, "tts_chars": 136214, "credits": 13621.4}
.\.venv\Scripts\python.exe scripts/run_echo_test.py --stage screen --live
.\.venv\Scripts\python.exe scripts/run_echo_test.py --stage confirm --from var/lab/echo_screen.jsonl          # ≈2,337 credits per pair, so ≈7,000 for 3
.\.venv\Scripts\python.exe scripts/run_echo_test.py --stage confirm --from var/lab/echo_screen.jsonl --live
```

  Then listen to **every** failed row and a 10% random sample of passes. Label each failure in `var/lab/echo_labels.csv` as `timbre`, `line` or `prisma`.
- [ ] **Step 5:** `git add src/parcha/readback.py src/parcha/lab/echo.py scripts/run_echo_test.py tests/test_benchmark_v2.py`, then `git commit -m "feat(bench): Timbre read-back echo test (screen + confirm)"`

### Task 14: Live benchmark runs

**Files:** None created. Outputs go to `var/lab/`. Record spend and dates in the effort log.

- [ ] **Step 1: Amount-labelled slices.** Do a dry run first; it prints the forecast. Then add `--live`.

```powershell
$bias = .\.venv\Scripts\python.exe -c "from parcha.vocabulary import AUTOMOTIVE_BIAS_WORDS as W; print(','.join(W))"
foreach ($m in "estimates","corrections") {
  .\.venv\Scripts\python.exe -m parcha.lab.runner --manifest data/benchmarks/amount_v2/$m.jsonl --audio-root var/benchmark_audio/amount_v2 `
    --codecs g711,amr_nb_4750 --snr-dbs clean,0 --impulse-profiles none --stt-modes transcribe,verbatim `
    --bias-words $bias --request-interval-seconds 1 --remaining-credits 235000 --max-credits 5000 `
    --output var/lab/v2_$m.jsonl          # add --live after reading the printed forecast
}
```

  The runner crosses codecs with SNRs. The spec's two conditions are `g711|clean` and `amr_nb_4750|0`. The other two cells (`g711|0`, `amr_nb_4750|clean`) are cheap context; report them separately.
- [ ] **Step 2: Owner takes.** Same command with `--manifest var/benchmark_audio/owner/manifest.jsonl --audio-root var/benchmark_audio/owner --output var/lab/v2_owner.jsonl`.
- [ ] **Step 3: Gramvaani.** `--manifest var/benchmark_audio/gramvaani/manifest.jsonl --audio-root var/benchmark_audio/gramvaani --codecs none --snr-dbs clean --impulse-profiles none --stt-modes transcribe,verbatim --bias-words <same> --max-credits 5000 --output var/lab/gramvaani.jsonl`. Forecast ≈4,025 credits.
- [ ] **Step 4: Bias positive control.** `--manifest data/benchmarks/amount_v2/bias_control.jsonl --codecs none --snr-dbs clean --stt-modes verbatim,verbatim_nobias --bias-words <same> --output var/lab/bias_control.jsonl`. Pass rule: the outputs differ, or the bias word is recovered more often with bias, on ≥1 clip. Otherwise record "boosting not observable" and drop bias claims (spec).
- [ ] **Step 5: Score.** `.\.venv\Scripts\python.exe -m parcha.lab.money_eval --results var/lab/v2_estimates.jsonl --results var/lab/v2_corrections.jsonl --results var/lab/v2_owner.jsonl --manifest data/benchmarks/amount_v2/estimates.jsonl --manifest data/benchmarks/amount_v2/corrections.jsonl --manifest var/benchmark_audio/owner/manifest.jsonl --out var/lab/money_eval.json`. Acceptance: `wrong_accepted == 0` in every slice × condition. Any non-zero opens a regression task (add an abstain rule, then re-run that slice).

### Task 15: Report and data card

**Files:** Create `src/parcha/lab/bench_report.py`, `tests/test_bench_report.py`, `docs/benchmarks/BENCHMARK_CARD.md`.

**Interfaces:**
- Produces: `build_report(money_eval: list[dict], gramvaani_rows: list[dict], echo_rows: list[dict], bias_rows: list[dict]) -> str` (private markdown) and `python -m parcha.lab.bench_report` (writes `var/lab/benchmark_report.md`).

- [ ] **Step 1: Failing tests.** Given synthetic inputs, the report:
  - has one table per slice × condition with `amounts`, `wrong_accepted`, `wrong_amount_confirmed_upper95`, `abstain_rate` and the top abstain reasons;
  - has a Gramvaani section with canonical CER (marked PRIVATE), number agreement (`matched / confident_wrong / abstain_equivalent`), the clipped vs unclipped split, and the silent-empty count;
  - has an echo table of pass rate per voice × style × condition;
  - has a bias-control verdict line;
  - has p50/p95 latency per pass;
  - has total credits;
  - contains the string `PRIVATE: absolute metrics — do not publish`;
  - contains none of the names in `report.FORBIDDEN_COMPETITORS`.
- [ ] **Step 2:** Run it. Expected: FAIL.
- [ ] **Step 3:** Implement. Write `BENCHMARK_CARD.md` (no metrics) with:
  - composition: v2 estimates 120 / 296 amounts, corrections 40, owner takes 80 (internal), stress 37, bias control 20, Gramvaani 1,032 (2.80 h, 291 clipped);
  - construction (gold-first, colloquial forms, 13 voices, seeds);
  - licences (CC BY 4.0 IndicContextEval; Gramvaani academic, by permission; synthetic Timbre audio);
  - exclusions;
  - intended use and limits ("synthetic speech flatters results; Gramvaani has no rupee labels; the owner's takes are one speaker");
  - the reproduce commands from Tasks 9–14.
- [ ] **Step 4:** Run `.\.venv\Scripts\python.exe -m pytest -q` and `.\.venv\Scripts\python.exe -m parcha.lab.bench_report`. Expected: green, and the report is written.
- [ ] **Step 5:** `git add src/parcha/lab/bench_report.py tests/test_bench_report.py docs/benchmarks/BENCHMARK_CARD.md`, then `git commit -m "feat(bench): private benchmark report and data card"`

### Task 16: Decisions and records

**Files:** Modify `aidlc-docs/efforts/009-money-path-plan/*`, `aidlc-docs/registry.md`, `docs/gates.md`.

- [ ] **Step 1: Transcribe pass.** Keep it only if `money_eval` shows ≥1 amount where the transcribe cross-check turned a would-be wrong acceptance into an abstention. To check, re-run the decision with `transcribe=None` on the same rows. Otherwise remove the second pass from `intake` and `reask` in a follow-up task (spec decision).
- [ ] **Step 2: Read-back voice and amount style.** Use the confirm-stage leader on `amr_nb_4750|0`; on a tie, keep Nalini. Set `TTS_VOICE` and `make_readback(..., amount_style=…)` as the product default. Record known read-back risks (amount patterns that still fail).
- [ ] **Step 3: Award.** Noise Canceller only if the Gramvaani results support it on real telephonic audio, with organiser and Gram Vaani consent for any public number. Otherwise Real Deal.
- [ ] **Step 4:** Update `docs/gates.md` with dated, reproducible rows (command + output path + N + spend), and update the registry.
- [ ] **Step 5:** `git commit -am "docs(aidlc): record money-path and benchmark v2 decisions"`

---

## Self-Review (done while writing)

- **Spec coverage:**
  - Primary metric (Tasks 8, 14); numeral grammar (2); intake money path (3); re-ask (4); provider failure policy (3–5).
  - Abstention reasons and audit manifest (3); read-back invariant (existing `start_readback` guard, asserted in Task 3).
  - Evon extractor (6); Lab fixes (7); R9 reproducible (Task 7, Step 4).
  - v2 amount slices (9–11); Gramvaani (12); Timbre echo test (13); bias positive control (9, 14); transcribe decision (16); credits (Global Constraints, Task 0); integrity (1); award (16); publication guard (15).
  - No gaps found.
- **Type consistency:**
  - `decide_amounts(verbatim, transcribe, *, expected_count)` is the same in Tasks 3, 4 and 8.
  - `AbstainReason` strings are identical everywhere; `provider_error` exists only inside `money_eval` (a Lab outcome, not a product reason).
  - `Clip.expected_amounts_paise` is used in Tasks 7–12.
  - Runner modes `transcribe`, `verbatim`, `verbatim_nobias`.
- **Proportion:** this plan carries full bodies only where the code is the decision (grammar tables, abstention rules, the resampler) or where the owner asked for working snippets. Everything here was executed in a scratch copy before inclusion, except the live API paths and the FFmpeg-dependent app tests, which run on the owner's laptop.

## Execution status update (2026-10-06)

- [x] Task 7 — Line Noise Lab: canonical references, outcomes, labels, bias control; Steps 1–5 complete. Validation: 12 focused tests, 53 affected lab/dataset tests, 423 full offline tests passed.
- Next: Task 8.

## Task 9 completion update — Gold-first v2 amount data

- [x] Add test-first renderer, stress round-trip, estimate, correction, and bias-control regressions; observe the expected missing-module failure before implementation.
- [x] Implement seeded benchmark generators and a writer that validates every JSONL row as `Clip`.
- [x] Generate `data/benchmarks/amount_v2/estimates.jsonl` (120 rows, 296 labels), `corrections.jsonl` (40 rows), `stress_rupees.json` (37 distinct amounts), and `bias_control.jsonl` (20 rows).
- [x] Run `tests/test_benchmark_v2.py` (15 passed) and the offline suite with `PYTHONPATH=src API_KEY=test-only` (438 passed).
- [x] Confirm the generator prints `estimates=120 (amounts=296) corrections=40 stress_amounts=37`; no live APIs or paid services used.