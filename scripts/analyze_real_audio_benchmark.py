"""Offline analysis of the real-audio benchmark bundle (no API calls).

Usage:
    python scripts/analyze_real_audio_benchmark.py data/benchmarks/real_audio_2026-10 var/lab/real_audio_analysis.md

Standard library only. The CER/WER functions mirror ``parcha.lab.metrics`` (NFKC + casefold;
WER also strips punctuation), and the script asserts that recomputed CER equals the stored CER
on every scoreable row. Output contains absolute CER/WER: keep it private (see AGENTS.md).
"""
from __future__ import annotations

import json
import random
import re
import statistics as st
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

LATIN = re.compile(r"[A-Za-z]")
DEVA = re.compile(r"[ऀ-ॿ]")
TAG = re.compile(r"<[^>]*>|\[[^\]]*\]")
DIGIT = re.compile(r"[0-9०-९]")
NUM_WORDS = set(
    "एक दो तीन चार पांच पाँच छह छः सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस बीस "
    "तीस चालीस पचास साठ सत्तर अस्सी नब्बे सौ हज़ार हजार लाख करोड़ साढ़े सवा पौने डेढ़ ढाई".split()
)
BIAS_LATIN = ["brake", "clutch", "bearing", "pressure", "plate", "gearbox", "engine", "oil", "filter", "labour", "price", "service"]
BIAS_DEVA = ["ब्रेक", "क्लच", "बेयरिंग", "प्रेशर", "प्लेट", "गियरबॉक्स", "इंजन", "ऑयल", "फ़िल्टर", "फिल्टर", "लेबर", "प्राइस", "सर्विस"]
SNRS = (None, 10.0, 5.0, 0.0)
MODES = ("transcribe", "verbatim")
CODECS = ("g711", "amr_nb_4750")


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _lev(a, b) -> int:
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        nxt = [i]
        for j, y in enumerate(b, 1):
            nxt.append(min(nxt[-1] + 1, row[j] + 1, row[j - 1] + (x != y)))
        row = nxt
    return row[-1]


def cer(ref: str, hyp: str) -> float:
    r, h = normalize(ref), normalize(hyp)
    return (0.0 if not h else 1.0) if not r else _lev(r, h) / len(r)


def _wtoks(text: str) -> list[str]:
    folded = unicodedata.normalize("NFKC", text).casefold()
    return "".join(" " if unicodedata.category(c).startswith("P") else c for c in folded).split()


def wer(ref: str, hyp: str) -> float:
    r, h = _wtoks(ref), _wtoks(hyp)
    return (0.0 if not h else 1.0) if not r else _lev(r, h) / len(r)


def clean_reference(text: str) -> str:
    """Strip <tags>/[tags]; drop a Latin token directly after a Devanagari token (code-mix gloss)."""
    out, prev_deva = [], False
    for tok in TAG.sub(" ", text).split():
        if LATIN.search(tok) and not DEVA.search(tok) and prev_deva:
            continue
        out.append(tok)
        prev_deva = bool(DEVA.search(tok))
    return " ".join(out)


def bias_hits(text: str) -> int:
    low = text.casefold()
    return sum(len(re.findall(rf"\b{b}\b", low)) for b in BIAS_LATIN) + sum(text.count(b) for b in BIAS_DEVA)


def m(xs) -> float | None:
    xs = [x for x in xs if x is not None]
    return round(st.fmean(xs), 4) if xs else None


def pct(xs, q) -> float | None:
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    f, c = int(k), min(int(k) + 1, len(xs) - 1)
    return round(xs[f] + (xs[c] - xs[f]) * (k - f), 4)


def boot_ci(per_clip: dict[str, list[float]], n: int = 2000, seed: int = 7) -> tuple[float, float, float]:
    clips = list(per_clip)
    rng = random.Random(seed)
    stat = lambda sample: st.fmean(v for c in sample for v in per_clip[c])
    boots = sorted(stat([rng.choice(clips) for _ in clips]) for _ in range(n))
    return round(stat(clips), 4), round(boots[int(0.025 * n)], 4), round(boots[int(0.975 * n)], 4)


def label(snr) -> str:
    return "clean" if snr is None else f"{int(snr)}dB"


def main(bundle: Path, out: Path) -> None:
    rows = [json.loads(l) for l in (bundle / "results.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    manifest = {r["id"]: r for r in (json.loads(l) for l in (bundle / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
    ds = [r for r in rows if r["source"] == "open_dataset"]
    ws = [r for r in rows if r["source"] != "open_dataset"]
    for r in ds:
        stored = r["cer"]
        assert abs(cer(r["reference"], r["transcript"] or "") - stored) < 1e-3, r["clip_id"]
        r["cer_c"] = cer(clean_reference(r["reference"]), r["transcript"] or "")
        r["wer_c"] = wer(clean_reference(r["reference"]), r["transcript"] or "")
    idx = {(r["clip_id"], r["stt_mode"], r["codec"], r["snr"]): r for r in rows}
    clips = sorted({r["clip_id"] for r in ds})
    cm = {c for c in clips if manifest[c]["stratum"].endswith("true")}
    L: list[str] = []
    P = L.append

    P("# Real-audio benchmark analysis (private: contains absolute CER/WER)\n")
    P(f"rows={len(rows)}; dataset rows={len(ds)} ({len(clips)} clips); workshop rows={len(ws)}; "
      f"estimated credits={round(sum(r.get('credits_spent') or 0 for r in rows), 3)}; recomputed CER == stored CER on all {len(ds)} dataset rows")
    silent = sorted({f"{r['clip_id']}/{r['stt_mode']}/{r['codec']}/{label(r['snr'])}" for r in ds if not (r["transcript"] or "").strip()})
    P(f"dataset rows with an empty transcript and no error (silent empty): {len(silent)} -> {', '.join(silent)}")
    P(f"workshop rows with transcript text present in the bundle: {sum(1 for r in ws if (r['transcript'] or '').strip())}/{len(ws)} (text redacted by design)")

    P("\n## A. Headline: as scored vs cleaned reference (dataset)\n\n| slice | mode | n | CER scored | CER cleaned | WER scored | WER cleaned |\n|---|---|---|---|---|---|---|")
    for name, pred in (("all", lambda r: True), ("code_mixed=true", lambda r: r["clip_id"] in cm), ("code_mixed=false", lambda r: r["clip_id"] not in cm)):
        for mode in MODES:
            g = [r for r in ds if pred(r) and r["stt_mode"] == mode]
            P(f"| {name} | {mode} | {len(g)} | {m(r['cer'] for r in g)} | {m(r['cer_c'] for r in g)} | {m(r['wer'] for r in g)} | {m(r['wer_c'] for r in g)} |")
    gloss = sum(1 for c in clips if clean_reference(manifest[c]["text"]) != manifest[c]["text"])
    P(f"\nreferences changed by cleaning: {gloss}/{len(clips)}; with <tags>: {sum(1 for c in clips if TAG.search(manifest[c]['text']))}; "
      f"Latin-token share in code-mixed references: {m(sum(1 for t in manifest[c]['text'].split() if LATIN.search(t)) / len(manifest[c]['text'].split()) for c in cm)}; "
      f"in code-mixed hypotheses: {m(sum(1 for t in (r['transcript'] or '').split() if LATIN.search(t)) / max(len((r['transcript'] or '').split()), 1) for r in ds if r['clip_id'] in cm)}")

    P("\n## B. Style x code-mixing (dataset, cleaned)\n\n| style | code_mixed | clips | CER scored | CER cleaned | WER cleaned |\n|---|---|---|---|---|---|")
    for style in ("Read", "Extempore"):
        for flag in ("false", "true"):
            g = [r for r in ds if f"|{style}|code_mixed={flag}" in r["stratum"]]
            P(f"| {style} | {flag} | {len({r['clip_id'] for r in g})} | {m(r['cer'] for r in g)} | {m(r['cer_c'] for r in g)} | {m(r['wer_c'] for r in g)} |")

    P("\n## C. Degradation grid (dataset, cleaned CER; scored CER in brackets)\n\n| mode | codec | clean | 10dB | 5dB | 0dB | 0dB vs clean |\n|---|---|---|---|---|---|---|")
    for mode in MODES:
        for codec in CODECS:
            cells, vals = [], []
            for s in SNRS:
                g = [r for r in ds if r["stt_mode"] == mode and r["codec"] == codec and r["snr"] == s]
                vals.append(m(r["cer_c"] for r in g))
                cells.append(f"{vals[-1]} ({m(r['cer'] for r in g)})")
            P(f"| {mode} | {codec} | " + " | ".join(cells) + f" | {round((vals[3] - vals[0]) / vals[0] * 100, 1)}% |")
    ranks = lambda v: [sorted(range(len(v)), key=lambda i: v[i]).index(i) for i in range(len(v))]
    a = ranks([idx[(c, "transcribe", "g711", None)]["cer_c"] for c in clips])
    b = ranks([idx[(c, "transcribe", "g711", 0.0)]["cer_c"] for c in clips])
    n = len(a)
    P(f"\nSpearman rho, per-clip cleaned CER clean vs 0 dB (transcribe, G.711): {round(1 - 6 * sum((x - y) ** 2 for x, y in zip(a, b)) / (n * (n * n - 1)), 3)}")
    d = [idx[(c, "transcribe", "amr_nb_4750", None)]["cer_c"] - idx[(c, "transcribe", "g711", None)]["cer_c"] for c in clips]
    P(f"AMR-NB minus G.711 at clean (transcribe, cleaned): mean {m(d)}; worse {sum(x > 0.001 for x in d)}, better {sum(x < -0.001 for x in d)}, same {sum(abs(x) <= 0.001 for x in d)}")

    P("\n## D. Paired verbatim minus transcribe (dataset, scored CER; negative = verbatim better)\n\n| codec | snr | dCER [95% CI] | dWER [95% CI] | verbatim better | transcribe better | ties |\n|---|---|---|---|---|---|---|")
    for codec in CODECS:
        for s in SNRS:
            dc, dw, wins = defaultdict(list), defaultdict(list), Counter()
            for c in clips:
                t, v = idx[(c, "transcribe", codec, s)], idx[(c, "verbatim", codec, s)]
                dc[c].append(v["cer"] - t["cer"]); dw[c].append(v["wer"] - t["wer"])
                wins["v" if v["cer"] < t["cer"] else "t" if t["cer"] < v["cer"] else "="] += 1
            x, y = boot_ci(dc), boot_ci(dw)
            P(f"| {codec} | {label(s)} | {x[0]} [{x[1]}, {x[2]}] | {y[0]} [{y[1]}, {y[2]}] | {wins['v']} | {wins['t']} | {wins['=']} |")

    num = {c for c in clips if any(w in NUM_WORDS for w in manifest[c]["text"].split()) or DIGIT.search(manifest[c]["text"])}
    P(f"\n## E. Numerals\n\nclips whose reference contains number words or digits: {len(num)}/{len(clips)}\n\n| mode | hyps with digits (numeral clips) | hyps with digits (other clips) |\n|---|---|---|")
    for mode in MODES:
        gn = [r for r in ds if r["stt_mode"] == mode and r["clip_id"] in num]
        go = [r for r in ds if r["stt_mode"] == mode and r["clip_id"] not in num]
        P(f"| {mode} | {round(sum(bool(DIGIT.search(r['transcript'] or '')) for r in gn) / len(gn), 3)} | {round(sum(bool(DIGIT.search(r['transcript'] or '')) for r in go) / len(go), 3)} |")
    P("\nExamples (G.711 clean), reference / transcribe / verbatim:")
    for c in ("i002", "i020"):
        if c in manifest:
            P(f"- {c} REF: {manifest[c]['text'][:110]}\n  - T: {(idx[(c, 'transcribe', 'g711', None)]['transcript'] or '')[:110]}\n  - V: {(idx[(c, 'verbatim', 'g711', None)]['transcript'] or '')[:110]}")

    P("\n## F. Bias words (12-word list sent with verbatim only)\n")
    for mode in MODES:
        g = [r for r in ds if r["stt_mode"] == mode]
        P(f"- {mode}: hypotheses with >=1 bias word {sum(bias_hits(r['transcript'] or '') > 0 for r in g)}/{len(g)}")
    ins = [r for r in ds if r["stt_mode"] == "verbatim" and bias_hits(r["transcript"] or "") > max(
        bias_hits(manifest[r["clip_id"]]["text"]), bias_hits(idx[(r["clip_id"], "transcribe", r["codec"], r["snr"])]["transcript"] or ""))]
    P(f"- verbatim rows with more bias words than both the reference and the paired transcribe hypothesis: {len(ins)}")

    P("\n## G. Failure shapes (dataset, scored)\n\n| mode | snr | CER>0.5 | hyp/ref chars <0.6 | >1.4 |\n|---|---|---|---|---|")
    for mode in MODES:
        for s in SNRS:
            g = [r for r in ds if r["stt_mode"] == mode and r["snr"] == s]
            ratio = [len(normalize(r["transcript"] or "")) / max(len(normalize(r["reference"])), 1) for r in g]
            P(f"| {mode} | {label(s)} | {round(sum(r['cer'] > 0.5 for r in g) / len(g), 3)} | {round(sum(x < 0.6 for x in ratio) / len(g), 3)} | {round(sum(x > 1.4 for x in ratio) / len(g), 3)} |")
    const = [c for c in clips if len({idx[(c, mo, co, s)]["transcript"] for mo in MODES for co in CODECS for s in SNRS}) == 1 and idx[(c, "transcribe", "g711", None)]["cer_c"] > 0.5]
    P(f"\nclips with one identical high-error transcript across all 16 conditions (likely reference/audio mismatch): {', '.join(const) or 'none'}")
    worst = sorted(clips, key=lambda c: -st.fmean(r["cer_c"] for r in ds if r["clip_id"] == c))[:6]
    P("worst clips by mean cleaned CER: " + ", ".join(f"{c} ({round(st.fmean(r['cer_c'] for r in ds if r['clip_id'] == c), 3)}; {manifest[c]['stratum']})" for c in worst))
    g0 = [idx[(c, "transcribe", "g711", None)]["cer_c"] for c in clips]
    P(f"share of clips with cleaned CER = 0 / <= 0.05 (transcribe, G.711 clean): {round(sum(x == 0 for x in g0) / n, 3)} / {round(sum(x <= 0.05 for x in g0) / n, 3)}")

    P("\n## H. Workshop slice (auto-caption pseudo-references; text redacted)\n\n| mode | codec | clean | 10dB | 5dB | 0dB |\n|---|---|---|---|---|---|")
    for mode in MODES:
        for codec in CODECS:
            P(f"| {mode} | {codec} | " + " | ".join(str(m(r["cer"] for r in ws if r["stt_mode"] == mode and r["codec"] == codec and r["snr"] == s)) for s in SNRS) + " |")

    P("\n## I. Latency (ms)\n\n| mode | codec | p50 | p95 | max | p50 ms per audio-second |\n|---|---|---|---|---|---|")
    for mode in MODES:
        for codec in CODECS:
            g = [r for r in rows if r["stt_mode"] == mode and r["codec"] == codec]
            per = [r["latency_ms"] / (r["credits_spent"] / 0.2) for r in g if r.get("credits_spent")]
            P(f"| {mode} | {codec} | {pct([r['latency_ms'] for r in g], .5)} | {pct([r['latency_ms'] for r in g], .95)} | {round(max(r['latency_ms'] for r in g), 1)} | {pct(per, .5)} |")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(L)} lines)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
