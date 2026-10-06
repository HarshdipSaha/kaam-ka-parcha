from pathlib import Path
import pytest

from parcha.lab.dataset import Clip
from scripts.register_owner_takes import parse_prompt_sheet, register


def test_register_maps_take_to_prompt():
    prompt_rows = [
        {
            "id": "o001",
            "expected_amounts_paise": [45000, 20000],
            "text": "brake pad ₹450, labour ₹200, Somvaar shaam tak",
            "reference_transcribe": "brake pad ₹450, labour ₹200, Somvaar shaam tak",
            "entities": {"delivery": "Somvaar shaam tak"},
            "audio": "o001.wav",
            "kind": "speech",
            "seed": 0,
        }
    ]
    rows = register(prompt_rows, ["o001.wav"])
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == "o001"
    assert row["audio"] == "o001.wav"
    assert row["expected_amounts_paise"] == [45000, 20000]
    assert row["source"] == "consented_script"
    assert row["stratum"] == "owner_extempore"
    assert row["voice"] is None
    # Verify that the generated row satisfies Clip schema
    validated = Clip.model_validate(row)
    assert validated.id == "o001"
    assert validated.expected_amounts_paise == [45000, 20000]


def test_register_raises_value_error_for_take_without_prompt():
    prompt_rows = [
        {
            "id": "o001",
            "expected_amounts_paise": [45000, 20000],
            "text": "brake pad ₹450, labour ₹200",
            "reference_transcribe": "brake pad ₹450, labour ₹200",
            "entities": {},
        }
    ]
    with pytest.raises(ValueError, match="o999"):
        register(prompt_rows, ["o999.wav"])


def test_register_accepts_path_objects():
    prompt_rows = [
        {
            "id": "o001",
            "expected_amounts_paise": [45000, 20000],
            "text": "brake pad ₹450, labour ₹200",
            "reference_transcribe": "brake pad ₹450, labour ₹200",
            "entities": {},
        },
        {
            "id": "o002",
            "expected_amounts_paise": [150000],
            "text": "clutch plate ₹1500",
            "reference_transcribe": "clutch plate ₹1500",
            "entities": {},
        },
    ]
    rows = register(prompt_rows, [Path("var/raw/o001.wav"), Path("var/raw/o002.wav")])
    assert [r["id"] for r in rows] == ["o001", "o002"]
    assert [r["audio"] for r in rows] == ["o001.wav", "o002.wav"]
    assert [r["expected_amounts_paise"] for r in rows] == [[45000, 20000], [150000]]


def test_owner_prompt_sheet_has_80_cards():
    sheet_path = Path("data/benchmarks/amount_v2/owner_prompt_sheet.md")
    assert sheet_path.exists(), f"missing {sheet_path}"
    prompts = parse_prompt_sheet(sheet_path)
    assert len(prompts) == 80
    assert [p["id"] for p in prompts] == [f"o{i:03d}" for i in range(1, 81)]
    for p in prompts:
        assert len(p["expected_amounts_paise"]) >= 1
        assert p["source"] == "consented_script"
        assert p["stratum"] == "owner_extempore"
        assert p["voice"] is None
        # Clip validation
        Clip.model_validate(p)


def test_cli_execution_with_no_takes(tmp_path, capsys):
    from scripts.register_owner_takes import main
    sheet_path = Path("data/benchmarks/amount_v2/owner_prompt_sheet.md")
    takes_dir = tmp_path / "takes"
    takes_dir.mkdir()
    audio_dir = tmp_path / "audio"
    manifest = tmp_path / "manifest.jsonl"
    
    code = main([
        "--prompts", str(sheet_path),
        "--takes-dir", str(takes_dir),
        "--audio-dir", str(audio_dir),
        "--manifest", str(manifest),
    ])
    assert code == 0
    out = capsys.readouterr().out
    assert "Loaded 80 prompts" in out

