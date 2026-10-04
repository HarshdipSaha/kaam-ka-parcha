from __future__ import annotations

import json
from pathlib import Path
from random import Random
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Clip(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z][0-9]{3}$")
    text: str
    reference_transcribe: str
    entities: dict[str, str | int]
    audio: str
    kind: Literal["speech", "reply", "engine_only"]
    seed: int
    source: Literal["timbre", "consented_script", "synthetic_noise"] = "timbre"


PART_WORDS = (
    "brake", "clutch", "piston", "chain", "sprocket", "bearing",
    "filter", "plug", "cable", "tyre", "tube", "rim", "fork", "shock",
    "battery", "starter", "alternator", "radiator", "coolant", "gasket",
    "valve", "camshaft", "carburetor", "injector", "silencer", "exhaust",
    "mirror", "headlamp", "indicator", "mudguard",
)

AMOUNTS = (
    ("saade chaar sau", 45000), ("pachaas", 5000),
    ("do sau", 20000), ("saat sau pachaas", 75000),
    ("ek hazaar", 100000), ("baarah sau", 120000),
    ("do hazaar pachaas", 205000), ("paanch sau", 50000),
    ("ek lakh", 10000000), ("ek crore", 1000000000),
)

DELIVERIES = (
    ("Somvaar shaam tak", "2026-10-05", "evening"),
    ("Mangalvaar subah tak", "2026-10-06", "morning"),
)


def make_prompts(seed: int = 20261004) -> list[dict]:
    terms = list(PART_WORDS)
    Random(seed).shuffle(terms)
    rows = []
    for index in range(100):
        part = terms[index % len(terms)]
        spoken_amount, paise = AMOUNTS[index % len(AMOUNTS)]
        spoken_delivery, iso_date, window = DELIVERIES[index % len(DELIVERIES)]
        rows.append({
            "id": f"s{index + 1:03d}",
            "text": f"{part} ka part {spoken_amount} rupaye, {spoken_delivery}",
            "reference_transcribe": f"{part} ka part ₹{paise // 100:,}, {spoken_delivery}",
            "entities": {
                "part": part,
                "amount_paise": paise,
                "delivery_date": iso_date,
                "delivery_window": window,
            },
            "audio": f"s{index + 1:03d}.wav",
            "kind": "speech",
            "seed": seed,
            "source": "timbre",
        })
    return rows


def load_manifest(
    path: Path | str,
    audio_root: Path | str | None = None,
    require_audio: bool = True,
) -> list[Clip]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest file not found: {manifest_path}")

    root: Path | None = None
    if require_audio:
        root = (Path("var/lab/audio") if audio_root is None else Path(audio_root)).resolve()

    clips: list[Clip] = []
    seen_ids: set[str] = set()

    for line_num, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on line {line_num}: {exc}") from exc

        clip = Clip.model_validate(data)
        if clip.id in seen_ids:
            raise ValueError(f"duplicate id: {clip.id}")
        seen_ids.add(clip.id)

        if require_audio:
            assert root is not None
            if not clip.audio or not clip.audio.strip():
                raise ValueError(f"empty audio path for clip {clip.id}")
            resolved_audio = (root / clip.audio).resolve()
            try:
                resolved_audio.relative_to(root)
            except ValueError:
                raise ValueError(f"audio path outside audio root: {clip.audio}")
            if not resolved_audio.is_file():
                raise FileNotFoundError(f"audio file not found: {resolved_audio}")

        clips.append(clip)

    return clips


def save_manifest(rows: list[dict] | list[Clip], path: Path | str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for row in rows:
            if isinstance(row, BaseModel):
                data = row.model_dump()
            elif isinstance(row, dict):
                data = row
            else:
                data = dict(row)
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
