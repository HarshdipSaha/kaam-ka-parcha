# Hinglish rupee amounts: what we handle, what we measured

Kaam ka Parcha reads rupee amounts from a mechanic's Hinglish speech with a deterministic numeral grammar
(`src/parcha/numerals.py`, `src/parcha/money.py`). No language model decides an amount. This note explains the
forms handled, the one speech-recogniser quirk that mattered, the measured effect, and the safety rule that follows.

All figures below come from **synthetic (Timbre) speech** run through Gnani Prisma and are application-logic
evidence, not real-speech accuracy. Each links to its row in [`docs/gates.md`](../gates.md#11-money-path-safety-and-benchmark-v2-effort-009).

## Colloquial forms handled

| Spoken | Meaning | Note |
|---|---|---|
| डेढ़ सौ / डेढ़ हज़ार | 150 / 1,500 | fixed 1.5 |
| ढाई सौ / ढाई हज़ार | 250 / 2,500 | fixed 2.5 |
| साढ़े चार सौ | 450 | N + 0.5, N from 3 to 99 |
| सवा सौ / सवा दो हज़ार | 125 / 2,250 | N + 0.25 |
| पौने दो सौ / पौने दो हज़ार | 175 / 1,750 | N - 0.25 |
| बारह सौ, चौदह सौ | 1,200 / 1,400 | hundreds used for 11-19 |

Romanised variants (`dedh`, `dhai`, `saade`, `sava`, `paune`) are parsed too. Anything the grammar cannot place
completely (a truncated "साढ़े", a missing unit) becomes an *abstention*, never a guessed amount.

## The recogniser quirk: Prisma writes साढ़े चार सौ as `04:30 100`

Prisma has two output formats. `verbatim` keeps the words ("साढ़े चार सौ"); `transcribe` applies number
formatting. For fractions the formatter produces clock-like and mixed strings, for example
`04:30 ₹100`, `साढ़े 4,000`, `03:30 हज़ार`, `ढाई ₹100`, `पौने ₹200`. The money path uses the `transcribe` pass only as a
**formatting cross-check** of the `verbatim` words, so these strings first have to be normalised back to the
amount they encode (`normalise_transcribe_fractions`). A real disagreement is never hidden: "साढ़े चार सौ"
against `04:30 ₹200` still abstains (`crosscheck_disagreement`).

## Measured effect

| Measurement | Result | Evidence |
|---|---|---|
| Re-ask recovery before the normaliser (100 amounts x 2 voices x 5 conditions, 1,000 live rows) | 73.3% recovered | [gates.md](../gates.md#11-money-path-safety-and-benchmark-v2-effort-009), "Re-ask recovery" row |
| After the normaliser (same rows, re-scored) | 96.3% recovered; every clean/control row recovers | same row |
| Held-out run (930 rows, fresh amounts none of which tuned the normaliser) | 96.8% recovered | "Held-out re-ask run" row |

## Why one recording is never enough

Even at 96-97% recovery, a single recording's accepted amount was wrong about 2.3% of the time (24 of 1,000
main rows, 20 of 930 held-out rows, all at 0 dB SNR). Accepting an amount just because the two Prisma passes on
*one* recording agree was also tested offline on the saved runs: 475 of 1,344 amounts would have been accepted
and 19 (4.0%; 10.2% at 0 dB) would have been wrong, so that rule was rejected.

The product rule, in plain words: **an amount is settled only when two separate recordings of the speaker agree**
(the second can be a per-amount "say again" or one repeat of the whole estimate). Measured on the saved runs, two
agreeing recordings settled 93-95% of amounts at the first pair with 0.2-0.4% wrong, all at 0 dB, and 0 wrong in
the clean and control conditions.

## Limits

- Synthetic speech from two Timbre voices; real workshop speech is not measured here.
- At 0 dB some number words are confused identically on both recordings (इकतीस heard as इक्कीस); those amounts
  need a third recording (see the look-alike rule in `src/parcha/money.py`).
- Code-mixed vs monolingual speech: not split here; see the licensed-corpus robustness report once published.
