from pathlib import Path
import subprocess
import sys
import pytest
from pydantic import ValidationError

from parcha.lab.dataset import (
    AMOUNTS,
    DELIVERIES,
    PART_WORDS,
    Clip,
    load_manifest,
    make_prompts,
    save_manifest,
)
from scripts.make_synthcall import main as make_synthcall_main


def test_100_seeded_prompts_are_stable():
    first = make_prompts(seed=20261004)
    second = make_prompts(seed=20261004)
    assert first == second
    assert len(first) == 100
    assert len({row["id"] for row in first}) == 100
    assert all("amount_paise" in row["entities"] for row in first)
    assert all("part" in row["entities"] for row in first)
    assert all("delivery_date" in row["entities"] for row in first)
    assert all("delivery_window" in row["entities"] for row in first)
    assert all("reference_transcribe" in row for row in first)
    assert all("text" in row for row in first)
    assert all(row["audio"] == f"{row['id']}.wav" for row in first)
    assert all(row["kind"] == "speech" for row in first)
    assert all(row["source"] == "timbre" for row in first)
    assert all(row["seed"] == 20261004 for row in first)
    assert first[0]["id"] == "s001"
    assert first[-1]["id"] == "s100"


def test_manifest_rejects_duplicate_id(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    line = '{"id":"s001","text":"pad saade chaar sau","reference_transcribe":"pad ₹450","entities":{"amount_paise":45000},"audio":"s001.wav","kind":"speech","seed":1}'
    manifest.write_text(line + "\n" + line + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_manifest(manifest, require_audio=False)


def test_manifest_requires_audio_when_enabled(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    line = '{"id":"s001","text":"pad saade chaar sau","reference_transcribe":"pad ₹450","entities":{"amount_paise":45000},"audio":"s001.wav","kind":"speech","seed":1}'
    manifest.write_text(line + "\n", encoding="utf-8")

    # Missing audio file raises FileNotFoundError
    with pytest.raises(FileNotFoundError, match="audio file not found"):
        load_manifest(manifest, audio_root=audio_dir, require_audio=True)

    # Path traversal outside audio_root raises ValueError
    traversal_line = '{"id":"s002","text":"pad saade chaar sau","reference_transcribe":"pad ₹450","entities":{"amount_paise":45000},"audio":"../outside.wav","kind":"speech","seed":1}'
    manifest.write_text(traversal_line + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="outside audio root"):
        load_manifest(manifest, audio_root=audio_dir, require_audio=True)

    # When audio exists, passes successfully
    (audio_dir / "s001.wav").write_bytes(b"dummy wav data")
    manifest.write_text(line + "\n", encoding="utf-8")
    loaded = load_manifest(manifest, audio_root=audio_dir, require_audio=True)
    assert len(loaded) == 1
    assert loaded[0].id == "s001"


def test_committed_manifest_is_valid():
    manifest_path = Path(__file__).resolve().parent.parent / "data" / "synthcall_manifest.jsonl"
    assert manifest_path.exists(), f"Committed manifest missing: {manifest_path}"
    clips = load_manifest(manifest_path, require_audio=False)
    assert len(clips) == 100
    assert len({c.id for c in clips}) == 100

    allowed_parts = set(PART_WORDS)
    allowed_paise = {amt[1] for amt in AMOUNTS}
    allowed_dates = {deliv[1] for deliv in DELIVERIES}
    allowed_windows = {deliv[2] for deliv in DELIVERIES}

    for index, clip in enumerate(clips):
        assert clip.id == f"s{index + 1:03d}"
        assert clip.kind == "speech"
        assert clip.source == "timbre"
        assert clip.audio == f"{clip.id}.wav"
        assert clip.seed == 20261004

        # Non-synthetic identifiers rejected via strict allowlist
        part = clip.entities.get("part")
        assert part in allowed_parts, f"Unexpected part '{part}' not in allowed synthetic vocabulary"

        paise = clip.entities.get("amount_paise")
        assert paise in allowed_paise, f"Unexpected amount {paise} not in synthetic amounts"

        d_date = clip.entities.get("delivery_date")
        assert d_date in allowed_dates, f"Unexpected delivery date {d_date}"

        d_window = clip.entities.get("delivery_window")
        assert d_window in allowed_windows, f"Unexpected delivery window {d_window}"


def test_make_synthcall_dry_run_exits_0(tmp_path, capsys):
    manifest_path = Path(__file__).resolve().parent.parent / "data" / "synthcall_manifest.jsonl"
    rc = make_synthcall_main([
        "--manifest", str(manifest_path),
        "--output-dir", str(tmp_path / "audio"),
        "--max-credits", "2000",
    ])
    assert rc == 0
    captured = capsys.readouterr()
    assert "SynthCall-IN Pre-Flight TTS Forecast" in captured.out
    assert "Total Clips:       100" in captured.out
    assert "PASS (Within budget cap)" in captured.out


def test_make_synthcall_cli_dry_run(tmp_path):
    manifest_path = Path(__file__).resolve().parent.parent / "data" / "synthcall_manifest.jsonl"
    res = subprocess.run(
        [
            sys.executable,
            "scripts/make_synthcall.py",
            "--manifest", str(manifest_path),
            "--output-dir", str(tmp_path / "audio"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "SynthCall-IN Pre-Flight TTS Forecast" in res.stdout


def test_clip_model_extra_fields_forbidden():
    valid_data = {
        "id": "s001",
        "text": "test",
        "reference_transcribe": "ref",
        "entities": {"part": "brake"},
        "audio": "s001.wav",
        "kind": "speech",
        "seed": 42,
        "source": "timbre",
    }
    # Valid data succeeds
    clip = Clip.model_validate(valid_data)
    assert clip.id == "s001"

    # Extra field raises ValidationError
    invalid_data = {**valid_data, "unexpected_extra": 123}
    with pytest.raises(ValidationError):
        Clip.model_validate(invalid_data)


def test_save_and_load_manifest_roundtrip(tmp_path):
    test_manifest = tmp_path / "roundtrip.jsonl"
    prompts = make_prompts(seed=12345)
    save_manifest(prompts, test_manifest)

    loaded = load_manifest(test_manifest, require_audio=False)
    assert len(loaded) == len(prompts)
    for original, obj in zip(prompts, loaded):
        assert obj.id == original["id"]
        assert obj.text == original["text"]
        assert obj.reference_transcribe == original["reference_transcribe"]
        assert obj.entities == original["entities"]
        assert obj.audio == original["audio"]
        assert obj.kind == original["kind"]
        assert obj.seed == original["seed"]
        assert obj.source == original["source"]
