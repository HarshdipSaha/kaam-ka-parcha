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
    "डेढ़": ("fixed", 1.5), "dedh": ("fixed", 1.5), "derh": ("fixed", 1.5),
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
_NUMERIC_DATE = re.compile(r"(?<!\d)(?:\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})(?!\d)")
_DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_PUNCT = re.compile(r"[\"'“”‘’()\[\]{}!?;।|/\\-]+")
_VEHICLE = re.compile(  # Indian registration, e.g. "DL 3S AB 1234", "MH 12 AB 1234"
    r"\b[A-Za-z]{2}[\s-]?\d{1,2}[\s-]?[A-Za-z]{0,3}[\s-]?[A-Za-z]{1,3}[\s-]?\d{1,4}\b"
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


def _spelling_variants(word: str) -> set[str]:
    """Spellings Prisma uses for the standard 1-99 words that the table above lacks.

    Observed in live runs: उन्तीस (उनतीस), तेंतीस/तेतीस (तैंतीस), उन्चास (उनचास), अट्ठारह/अठ्ठाराह (अठारह), चौतीस
    (चौंतीस). Rules: drop the anusvara; ai-matra nasal forms; the उन- prefix with a conjunct; अठ/अट्ठ/अठ्ठ stems; a long
    -राह ending. Without these an unknown number word is skipped and its unit alone reads as a one-unit amount.
    """
    base = _fold_deva(word)
    forms = {base, base.replace("ं", "")}
    for nasal in ("ें", "े", "ै"):
        forms.add(base.replace("ैं", nasal))
    for form in list(forms):
        if form.startswith("उन") and not form.startswith("उन्"):
            forms.add("उन्" + form[2:])
    for form in list(forms):
        for stem in ("अठ", "अट्ठ", "अठ्ठ"):
            if form.startswith(stem):
                forms.update(other + form[len(stem):] for other in ("अठ", "अट्ठ", "अठ्ठ"))
    for form in list(forms):
        if form.endswith("रह"):
            forms.add(form[:-2] + "राह")
    forms.discard(base)
    return forms


for _n, _w in enumerate(_DEVA_1_99, 1):
    for _variant in _spelling_variants(_w):
        _WORDS.setdefault(_key(_variant), _n)      # never override a standard word or an explicit variant
_MULT = {_key(w): v for w, v in _MULTIPLIERS.items()}
_FRAC = {_key(w): v for w, v in _FRACTIONS.items()}
_CUR = {_key(w) for w in _CURRENCY}
_NONMONEY = {_key(w) for w in _NON_MONEY_UNITS}
_MONTHS = {_key(w) for w in (
    "जनवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर",
    "january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
    "november", "december",
)}
_MODEL_YEAR_CUES = {_key("model"), _key("मॉडल")}


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
    text = _NUMERIC_DATE.sub(" ", text)
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


def _has_model_year_cue_before(toks: list[_Tok], i: int) -> bool:
    if not i:
        return False
    previous_key = _key(toks[i - 1].raw.rstrip(":"))
    if previous_key in _MODEL_YEAR_CUES:
        return True
    return (
        previous_key == _key("year")
        and i > 1
        and _key(toks[i - 2].raw.rstrip(":")) in _MODEL_YEAR_CUES
    )


def _has_model_year_cue_after(toks: list[_Tok], i: int) -> bool:
    return i < len(toks) and _key(toks[i].raw.rstrip(":")) in _MODEL_YEAR_CUES


def _is_calendar_year(toks: list[_Tok], i: int) -> bool:
    token = toks[i]
    if token.kind != "digit" or not token.value.is_integer() or not 1900 <= token.value <= 2099:
        return False
    previous = toks[i - 1] if i else None
    if previous is not None and previous.kind == "cur":
        return False
    previous_key = _key(previous.raw.rstrip(":")) if previous is not None else ""
    return (
        _has_model_year_cue_before(toks, i)
        or _has_model_year_cue_after(toks, i + 1)
        or previous_key in _MONTHS
    )


def _is_model_year_phrase(
    toks: list[_Tok], start: int, end: int, rupees: float | None
) -> bool:
    if rupees is None or not rupees.is_integer() or not 1900 <= rupees <= 2099:
        return False
    if start and toks[start - 1].kind == "cur":
        return False
    return _has_model_year_cue_before(toks, start) or _has_model_year_cue_after(toks, end)


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
            if nxt is not None and nxt.kind == "mult" and kind == "add" and frac == 0.5:
                total, last_mult, j = total + 1.5 * nxt.value, nxt.value, j + 2    # saade sau = 150
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
        if toks[i].kind == "digit" and _is_calendar_year(toks, i):
            i += 1
            continue
        if toks[i].kind not in {"num", "mult", "frac", "digit"}:
            i += 1
            continue
        rupees, complete, j = _parse_phrase(toks, i)
        if _is_model_year_phrase(toks, i, j, rupees):
            i = max(j, i + 1)
            continue
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
