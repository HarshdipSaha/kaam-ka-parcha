import json
from pathlib import Path

import numpy as np

from parcha.audio import _read_pcm, _write_pcm
from parcha.lab.noise import IMPULSE_PROFILES, inject_impulses
from parcha.lab.runner import Runner, RunnerConfig
from parcha.gnani import GnaniError


def _tone(samples: int = 16_000) -> bytes:
    timeline = np.arange(samples)
    pcm = (1_000 * np.sin(2 * np.pi * 220 * timeline / 8_000)).astype("<i2")
    return _write_pcm(pcm)


def test_each_impulse_profile_is_deterministic_and_localised():
    source = _tone()
    baseline = _read_pcm(source)

    assert set(IMPULSE_PROFILES) == {"impact_wrench", "metal_spanner", "compressor_exhaust"}
    for name in IMPULSE_PROFILES:
        first = _read_pcm(inject_impulses(source, name, seed=42))
        second = _read_pcm(inject_impulses(source, name, seed=42))
        assert np.array_equal(first, second)
        assert len(first) == len(baseline)
        assert not np.array_equal(first, baseline)
        assert np.max(np.abs(first.astype(np.int32))) <= 32767


def test_runner_records_profile_and_idle_hallucinations(tmp_path):
    audio = tmp_path / "audio"
    audio.mkdir()
    (audio / "s001.wav").write_bytes(_tone())
    (audio / "s002.wav").write_bytes(_write_pcm(np.full(16_000, 900, dtype="<i2")))
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("\n".join(json.dumps(row) for row in [
        {"id": "s001", "text": "brake", "reference_transcribe": "brake", "entities": {}, "audio": "s001.wav", "kind": "speech", "seed": 1, "source": "synthetic_noise"},
        {"id": "s002", "text": "", "reference_transcribe": "", "entities": {}, "audio": "s002.wav", "kind": "engine_only", "seed": 1, "source": "synthetic_noise"},
    ]) + "\n", encoding="utf-8")

    class FakePrisma:
        def transcribe(self, wav, *, mode):
            return "phantom words"

    rows = Runner(RunnerConfig(
        manifest_path=manifest, audio_root=audio, output_path=tmp_path / "result.jsonl",
        codecs=["g711"], snr_dbs=[None], loss_percents=[0.0],
        impulse_profiles=["metal_spanner"], max_credits=10,
    ), client=FakePrisma()).run()

    assert {row["impulse_profile"] for row in rows} == {None, "metal_spanner"}
    speech = next(row for row in rows if row["clip_type"] == "speech")
    assert speech["seed"] == 20261004
    assert speech["noise_source"] == "none"
    idle = next(row for row in rows if row["clip_type"] == "engine_only")
    assert idle["hallucinated_word_count"] == 2


def test_runner_normalizes_recorded_16khz_engine_audio(tmp_path):
    repository_data = Path("data")
    class FakePrisma:
        def transcribe(self, wav, *, mode):
            return ""

    rows = Runner(RunnerConfig(
        manifest_path=repository_data / "idle_hallucination_manifest.jsonl",
        audio_root=repository_data / "real_world_samples", output_path=tmp_path / "result.jsonl",
        codecs=["g711"], snr_dbs=[None], loss_percents=[0.0], max_credits=10,
    ), client=FakePrisma()).run()
    assert rows[0]["clip_type"] == "engine_only"


def test_idle_api_rejection_is_recorded_without_becoming_zero_hallucinations(tmp_path):
    audio = tmp_path / "audio"
    audio.mkdir()
    (audio / "s001.wav").write_bytes(_tone())
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({
        "id": "s001", "text": "", "reference_transcribe": "", "entities": {},
        "audio": "s001.wav", "kind": "engine_only", "seed": 1, "source": "synthetic_noise",
    }) + "\n", encoding="utf-8")

    class RejectingPrisma:
        def transcribe(self, wav, *, mode):
            raise GnaniError("Gnani request failed: HTTP 400")

    rows = Runner(RunnerConfig(
        manifest_path=manifest, audio_root=audio, output_path=tmp_path / "result.jsonl",
        codecs=["g711"], snr_dbs=[None], loss_percents=[0.0], max_credits=10,
    ), client=RejectingPrisma()).run()
    assert rows[0]["transcript"] is None
    assert rows[0]["transcription_error"] == "Gnani request failed: HTTP 400"
    assert rows[0]["hallucinated_word_count"] is None


def test_runner_keeps_headroom_for_real_noise_mixes(tmp_path):
    source = _write_pcm(np.full(8_000, 30_000, dtype="<i2"))
    noise = tmp_path / "noise.wav"
    noise.write_bytes(_write_pcm(np.full(8_000, 30_000, dtype="<i2")))
    runner = Runner(RunnerConfig(
        manifest_path=tmp_path / "missing.jsonl", audio_root=tmp_path,
        noise_path=noise, max_credits=10,
    ))
    mixed = runner.degrade_audio(source, "g711", 0.0, 0.0)
    assert len(_read_pcm(mixed)) == 8_000


def test_runner_replaces_stale_checkpoint_on_a_new_experiment(tmp_path):
    audio = tmp_path / "audio"
    audio.mkdir()
    (audio / "s001.wav").write_bytes(_tone())
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({
        "id": "s001", "text": "", "reference_transcribe": "", "entities": {},
        "audio": "s001.wav", "kind": "engine_only", "seed": 1, "source": "synthetic_noise",
    }) + "\n", encoding="utf-8")
    output = tmp_path / "result.jsonl"
    output.write_text('{"stale": true}\n', encoding="utf-8")

    class FakePrisma:
        def transcribe(self, wav, *, mode):
            return ""

    Runner(RunnerConfig(
        manifest_path=manifest, audio_root=audio, output_path=output,
        codecs=["g711"], snr_dbs=[None], loss_percents=[0.0], max_credits=10,
    ), client=FakePrisma()).run()
    saved = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(saved) == 1
    assert saved[0]["clip_id"] == "s001"


def test_engine_idle_rows_are_unmodified_by_snr_or_impulses(tmp_path):
    audio = tmp_path / "audio"
    audio.mkdir()
    (audio / "s001.wav").write_bytes(_tone())
    (audio / "s002.wav").write_bytes(_tone())
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("\n".join(json.dumps(row) for row in [
        {"id": "s001", "text": "speech", "reference_transcribe": "speech", "entities": {}, "audio": "s001.wav", "kind": "speech", "seed": 1, "source": "synthetic_noise"},
        {"id": "s002", "text": "", "reference_transcribe": "", "entities": {}, "audio": "s002.wav", "kind": "engine_only", "seed": 1, "source": "synthetic_noise"},
    ]) + "\n", encoding="utf-8")

    class FakePrisma:
        def transcribe(self, wav, *, mode):
            return ""

    rows = Runner(RunnerConfig(
        manifest_path=manifest, audio_root=audio, output_path=tmp_path / "result.jsonl",
        codecs=["g711"], snr_dbs=[None, 5.0], loss_percents=[0.0],
        impulse_profiles=["impact_wrench", "metal_spanner"], max_credits=10,
    ), client=FakePrisma()).run()
    idle_rows = [row for row in rows if row["clip_type"] == "engine_only"]
    assert [(row["snr"], row["impulse_profile"]) for row in idle_rows] == [(None, None)]


def test_cache_key_changes_when_stationary_noise_asset_changes(tmp_path):
    source = _tone()
    first_noise = tmp_path / "first.wav"
    second_noise = tmp_path / "second.wav"
    first_noise.write_bytes(_write_pcm(np.full(8_000, 1_000, dtype="<i2")))
    second_noise.write_bytes(_write_pcm(np.full(8_000, -1_000, dtype="<i2")))
    common = {"manifest_path": tmp_path / "missing.jsonl", "audio_root": tmp_path, "cache_dir": tmp_path / "cache"}
    first = Runner(RunnerConfig(**common, noise_path=first_noise)).degrade_audio(source, "g711", 5.0, 0.0)
    second = Runner(RunnerConfig(**common, noise_path=second_noise)).degrade_audio(source, "g711", 5.0, 0.0)
    assert first != second
