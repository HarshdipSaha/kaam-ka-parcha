"""Customer read-back languages beyond Hindi: fixed, reviewed strings only.

Hindi (`hi-IN`) stays the default and is handled by the original code in `readback.py`. For a regional language the
read-back is assembled from the fixed strings below, with **digit-style amounts** (Timbre reads numerals natively; we
never machine-translate an amount) and a reply classifier that only accepts a clear yes.

REVIEW REQUIRED: these strings were drafted without a native-speaker check. Task B8 in `docs/dev-notes/sug.md` asks the owner to have a
native speaker review each pack before the language is shown to real customers; the UI labels them "preview".
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["DEFAULT_LANGUAGE", "LANGUAGES", "LanguagePack", "pack_for", "supported_codes"]

DEFAULT_LANGUAGE = "hi-IN"


@dataclass(frozen=True)
class LanguagePack:
    code: str
    name: str                      # shown in the workshop selector, in the language itself and in English
    english_name: str
    voices: tuple[str, ...]        # Timbre voices for this language; the first is the default
    consent_notice: str            # statutory call-recording notice (DPDP Act 2023)
    total_word: str
    delivery_word: str
    windows: dict[str, str]        # delivery window words
    closing_prompt: str            # asks for a clear yes and invites a correction
    yes_words: frozenset[str]
    no_words: frozenset[str]
    ok_words: frozenset[str]       # allowed after a yes ("haan, theek hai")
    modifiers: frozenset[str] = frozenset()


LANGUAGES: dict[str, LanguagePack] = {
    "ta-IN": LanguagePack(
        code="ta-IN", name="தமிழ்", english_name="Tamil",
        voices=("Brinda", "Trisha", "Asmita", "Vedika", "Noopur"),
        consent_notice="மதிப்பீட்டை உறுதிப்படுத்துவதற்காக, DPDP சட்டம் 2023-இன் கீழ் இந்த அழைப்பு பதிவு செய்யப்படுகிறது.",
        total_word="மொத்தம்", delivery_word="டெலிவரி",
        windows={"morning": "காலை", "afternoon": "மதியம்", "evening": "மாலை"},
        closing_prompt="இது சரி என்றால், 'ஆமா, சரி' என்று சொல்லுங்கள். ஏதாவது தவறு இருந்தால் சொல்லுங்கள்.",
        yes_words=frozenset({"ஆமா", "ஆம்", "ஆமாம்", "ஆமாங்க"}),
        no_words=frozenset({"இல்லை", "இல்ல", "வேண்டாம்", "தவறு"}),
        ok_words=frozenset({"சரி", "சரிங்க"}),
    ),
    "bn-IN": LanguagePack(
        code="bn-IN", name="বাংলা", english_name="Bengali",
        voices=("Dhruva", "Kirra"),
        consent_notice="আনুমানিক খরচ নিশ্চিত করার জন্য, DPDP আইন ২০২৩ অনুযায়ী এই কলটি রেকর্ড করা হচ্ছে।",
        total_word="মোট", delivery_word="ডেলিভারি",
        windows={"morning": "সকাল", "afternoon": "দুপুর", "evening": "সন্ধ্যা"},
        closing_prompt="আপনি রাজি থাকলে বলুন: 'হ্যাঁ, ঠিক আছে'। কিছু ভুল থাকলে জানান।",
        yes_words=frozenset({"হ্যাঁ", "হ্যা", "হাঁ", "হ্যাঁ।"}),
        no_words=frozenset({"না", "নাহ", "নয়", "ভুল"}),
        ok_words=frozenset({"ঠিক", "আছে", "ঠিকাছে"}),
    ),
    "kn-IN": LanguagePack(
        code="kn-IN", name="ಕನ್ನಡ", english_name="Kannada",
        voices=("Kavin", "Saanvi"),
        consent_notice="ಅಂದಾಜನ್ನು ದೃಢೀಕರಿಸುವುದಕ್ಕಾಗಿ, DPDP ಕಾಯ್ದೆ 2023 ರ ಅಡಿಯಲ್ಲಿ ಈ ಕರೆಯನ್ನು ರೆಕಾರ್ಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ.",
        total_word="ಒಟ್ಟು", delivery_word="ಡೆಲಿವರಿ",
        windows={"morning": "ಬೆಳಿಗ್ಗೆ", "afternoon": "ಮಧ್ಯಾಹ್ನ", "evening": "ಸಂಜೆ"},
        closing_prompt="ನಿಮಗೆ ಒಪ್ಪಿಗೆಯಿದ್ದರೆ ಹೇಳಿ: 'ಹೌದು, ಸರಿ'. ಏನಾದರೂ ತಪ್ಪಿದ್ದರೆ ತಿಳಿಸಿ.",
        yes_words=frozenset({"ಹೌದು", "ಹೌದ", "ಹೌದ್ರಿ"}),
        no_words=frozenset({"ಇಲ್ಲ", "ಬೇಡ", "ತಪ್ಪು"}),
        ok_words=frozenset({"ಸರಿ", "ಸರಿಯಾಗಿದೆ"}),
    ),
}


def supported_codes() -> tuple[str, ...]:
    return (DEFAULT_LANGUAGE, *LANGUAGES)


def pack_for(code: str | None) -> LanguagePack | None:
    """The regional pack for `code`; None means Hindi (the original path) and raises for an unknown code."""
    if code in (None, "", DEFAULT_LANGUAGE):
        return None
    try:
        return LANGUAGES[code]
    except KeyError:
        raise ValueError(f"unsupported read-back language: {code}") from None
