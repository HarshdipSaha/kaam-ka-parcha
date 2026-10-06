"""Gold-first synthetic manifests for testing spoken rupee amounts."""

from __future__ import annotations

import json
from pathlib import Path
from random import Random
from typing import Iterable

from parcha.lab.dataset import Clip
from parcha.numerals import render_colloquial_amount, render_hindi_amount

HINDI_TIMBRE_VOICES = (
    "Nalini", "Bhavna", "Yashvi", "Urmila", "Jwala", "Chitra", "Ambuja",
    "Deepak", "Roopesh", "Vikrant", "Hemraj", "Jalaj", "Omkar",
)

PARTS = (
    "ब्रेक पैड", "क्लच प्लेट", "चेन स्प्रॉकेट", "एयर फ़िल्टर", "इंजन ऑयल",
    "स्पार्क प्लग", "बैटरी", "बेयरिंग", "टायर", "ट्यूब", "हेडलाइट",
    "कार्बोरेटर", "शॉकर", "साइलेंसर", "क्लच केबल", "गियर ऑयल",
)

PART_AMOUNTS_RUPEES = (
    120, 150, 175, 200, 250, 300, 350, 450, 480, 500, 650, 750,
    900, 1050, 1200, 1250, 1500, 1750, 2050, 2500, 3500, 4200,
    7500, 10500,
)

LABOUR_RUPEES = (50, 100, 150, 200, 250, 300, 350, 400, 500)
DELIVERIES = ("सोमवार शाम तक", "कल सुबह तक", "बुधवार दोपहर तक", "आज शाम तक")
STRESS_RUPEES = (
    125, 150, 175, 225, 250, 275, 350, 375, 450, 950, 1050, 1150, 1250,
    1500, 1750, 1950, 2250, 2500, 3500, 4500, 5000, 5050, 5500, 7500,
    9900, 10050, 10500, 12000, 15000, 25000, 35000, 45000, 50500, 75000,
    99000, 99999, 100000, 1500, 450, 350,
)

BIAS_CONTROL_WORDS = (
    ("alternator", "अल्टरनेटर"),
    ("camshaft", "कैमशाफ्ट"),
    ("carburetor", "कार्बोरेटर"),
    ("caliper", "कैलिपर"),
    ("gasket", "गैसकेट"),
    ("bearing", "बेयरिंग"),
    ("clutch", "क्लच"),
    ("axle", "एक्सल"),
)

_CORRECTION_OPENERS = ("नहीं,", "नहीं नहीं,", "गलत है,", "", "भैया,")
_BIAS_FRAMES = (
    "{} बदलना पड़ेगा", "{} में आवाज़ आ रही है", "नया {} लगाना है", "{} चेक कर लो",
)
_TWO_PART_ROWS_PER_120 = 56


def _amount_text(rupees: int, rng: Random) -> str:
    paise = rupees * 100
    if rng.random() < 0.7:
        return render_colloquial_amount(paise)
    return render_hindi_amount(paise).removesuffix(" रुपये")


def _voices(n: int, rng: Random) -> list[str]:
    voices = list(HINDI_TIMBRE_VOICES)
    rng.shuffle(voices)
    return [voices[index % len(voices)] for index in range(n)]


def _validate_rows(rows: Iterable[dict]) -> list[dict]:
    return [Clip.model_validate(row).model_dump() for row in rows]


def make_estimates(n: int = 120, seed: int = 20261005) -> list[dict]:
    """Build estimates with one or two parts and a separately spoken labour amount."""
    if n < 0:
        raise ValueError("n must be non-negative")

    rng = Random(seed)
    two_part_count = round(_TWO_PART_ROWS_PER_120 * n / 120)
    two_part_indexes = set(rng.sample(range(n), two_part_count)) if two_part_count else set()
    voices = _voices(n, rng)
    rows: list[dict] = []

    for index in range(n):
        part_count = 2 if index in two_part_indexes else 1
        selected_parts = rng.sample(PARTS, part_count)
        part_amounts = [rng.choice(PART_AMOUNTS_RUPEES) for _ in selected_parts]
        labour = rng.choice(LABOUR_RUPEES)
        delivery = rng.choice(DELIVERIES)

        amount_labels = [rupees * 100 for rupees in (*part_amounts, labour)]
        lines = [f"{part} {_amount_text(amount, rng)}" for part, amount in zip(selected_parts, part_amounts)]
        lines.append(f"labour {_amount_text(labour, rng)}")
        lines.append(delivery)
        text = ", ".join(lines)
        clip_id = f"v{index + 1:03d}"
        rows.append({
            "id": clip_id,
            "text": text,
            "reference_transcribe": text,
            "entities": {"delivery": delivery, "item_count": part_count},
            "audio": f"{clip_id}.wav",
            "kind": "speech",
            "seed": seed,
            "expected_amounts_paise": amount_labels,
            "voice": voices[index],
            "source": "timbre",
            "stratum": "scripted_estimate",
        })
    return _validate_rows(rows)


def make_corrections(n: int = 40, seed: int = 20261006) -> list[dict]:
    """Build customer reply clips correcting a single spoken amount."""
    if n < 0:
        raise ValueError("n must be non-negative")

    rng = Random(seed)
    voices = _voices(n, rng)
    rows: list[dict] = []
    for index in range(n):
        rupees = rng.choice(STRESS_RUPEES)
        opener = rng.choice(_CORRECTION_OPENERS)
        text = f"{opener} {render_colloquial_amount(rupees * 100)} बोला था"
        clip_id = f"c{index + 1:03d}"
        rows.append({
            "id": clip_id,
            "text": text,
            "reference_transcribe": text,
            "entities": {"amount_paise": rupees * 100},
            "audio": f"{clip_id}.wav",
            "kind": "reply",
            "seed": seed,
            "expected_amounts_paise": [rupees * 100],
            "voice": voices[index],
            "source": "timbre",
            "stratum": "correction",
        })
    return _validate_rows(rows)


def make_bias_control(n: int = 20, seed: int = 20261007) -> list[dict]:
    """Build clips whose automotive terms overlap the Prisma bias vocabulary."""
    if n < 0:
        raise ValueError("n must be non-negative")

    rng = Random(seed)
    voices = _voices(n, rng)
    rows: list[dict] = []
    for index in range(n):
        word, spoken_word = BIAS_CONTROL_WORDS[index % len(BIAS_CONTROL_WORDS)]
        frame = _BIAS_FRAMES[index % len(_BIAS_FRAMES)]
        text = frame.format(spoken_word)
        clip_id = f"b{index + 1:03d}"
        rows.append({
            "id": clip_id,
            "text": text,
            "reference_transcribe": text,
            "entities": {"bias_word": word},
            "audio": f"{clip_id}.wav",
            "kind": "speech",
            "seed": seed,
            "expected_amounts_paise": [],
            "voice": voices[index],
            "source": "timbre",
            "stratum": "bias_control",
        })
    return _validate_rows(rows)


def write_amount_benchmarks(output_dir: Path | str = "data/benchmarks/amount_v2") -> dict[str, int]:
    """Validate and write all gold-first amount benchmark manifests."""
    output = Path(output_dir)
    estimates = make_estimates()
    corrections = make_corrections()
    bias_control = make_bias_control()
    output.mkdir(parents=True, exist_ok=True)

    for name, rows in (
        ("estimates.jsonl", estimates),
        ("corrections.jsonl", corrections),
        ("bias_control.jsonl", bias_control),
    ):
        # Revalidate at the write boundary so generated files can never bypass Clip.
        validated = _validate_rows(rows)
        with (output / name).open("w", encoding="utf-8", newline="\n") as stream:
            for row in validated:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")

    stress_rupees = list(dict.fromkeys(STRESS_RUPEES))
    (output / "stress_rupees.json").write_text(
        json.dumps(stress_rupees, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "estimates": len(estimates),
        "amounts": sum(len(row["expected_amounts_paise"]) for row in estimates),
        "corrections": len(corrections),
        "stress_amounts": len(stress_rupees),
    }
