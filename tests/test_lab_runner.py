import json
from pathlib import Path
import numpy as np
import pytest

from parcha.audio import _read_pcm, _write_pcm, erase_frames
from parcha.credits import BudgetExceeded
from parcha.lab.runner import Runner, RunnerConfig, main


def make_test_wav(num_samples: int = 8000, amplitude: int = 4000) -> bytes:
    t = np.arange(num_samples)
    samples = (amplitude * np.sin(2 * np.pi * 440 * t / 8000)).astype("<i2")
    return _write_pcm(samples)


class FakePrisma:
    def __init__(self, reply: str = "brake ka part ₹450, Somvaar shaam tak"):
        self.reply = reply
        self.call_count = 0

    def transcribe(self, wav: bytes, *, mode: str = "transcribe") -> str:
        self.call_count += 1
        return self.reply


def test_frame_erasure_deterministic_and_bounds():
    # 8000 samples = 50 frames of 160 samples each (1 second)
    wav = make_test_wav(8000)

    # 1. Determinism with identical seed
    out1, loss1 = erase_frames(wav, 20.0, seed=42)
    out2, loss2 = erase_frames(wav, 20.0, seed=42)
    assert out1 == out2
    assert loss1 == loss2 == 0.2  # 10 of 50 frames erased

    # Different seed produces different erasure pattern
    out3, loss3 = erase_frames(wav, 20.0, seed=999)
    assert loss3 == 0.2
    assert out1 != out3

    # 2. Lower bound: loss <= 0 returns audio unchanged
    out_zero, loss_zero = erase_frames(wav, 0.0, seed=42)
    assert out_zero == wav
    assert loss_zero == 0.0

    out_neg, loss_neg = erase_frames(wav, -10.0, seed=42)
    assert out_neg == wav
    assert loss_neg == 0.0

    # 3. Upper bound: loss >= 100 zeroes all frames
    out_100, loss_100 = erase_frames(wav, 100.0, seed=42)
    assert loss_100 == 1.0
    samples_100 = _read_pcm(out_100)
    assert np.all(samples_100 == 0)

    out_150, loss_150 = erase_frames(wav, 150.0, seed=42)
    assert loss_150 == 1.0
    assert np.all(_read_pcm(out_150) == 0)

    # 4. Short audio (< 160 samples)
    short_wav = _write_pcm(np.full(100, 1000, dtype="<i2"))
    out_short, loss_short = erase_frames(short_wav, 50.0, seed=42)
    assert out_short == short_wav
    assert loss_short == 0.0


def test_runner_dry_run_forecast(tmp_path, capsys):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "s001.wav").write_bytes(make_test_wav(40000))  # 5.0 seconds
    (audio_dir / "s002.wav").write_bytes(make_test_wav(40000))  # 5.0 seconds

    manifest = tmp_path / "manifest.jsonl"
    rows = [
        {
            "id": "s001",
            "text": "brake ka part saade chaar sau rupaye, Somvaar shaam tak",
            "reference_transcribe": "brake ka part ₹450, Somvaar shaam tak",
            "entities": {"part": "brake", "amount_paise": 45000},
            "audio": "s001.wav",
            "kind": "speech",
            "seed": 20261004,
            "source": "timbre",
        },
        {
            "id": "s002",
            "text": "clutch ka part pachaas rupaye, Mangalvaar subah tak",
            "reference_transcribe": "clutch ka part ₹50, Mangalvaar subah tak",
            "entities": {"part": "clutch", "amount_paise": 5000},
            "audio": "s002.wav",
            "kind": "speech",
            "seed": 20261004,
            "source": "timbre",
        },
    ]
    manifest.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    out_file = tmp_path / "results.jsonl"
    config = RunnerConfig(
        manifest_path=manifest,
        audio_root=audio_dir,
        output_path=out_file,
        codecs=["g711"],
        snr_dbs=[None, 10.0],
        loss_percents=[0.0],
        credits_per_second=0.2,
        remaining_credits=100.0,
        max_credits=50.0,
    )
    runner = Runner(config)
    fc = runner.forecast()

    # 2 clips * 1 codec * 2 snrs * 1 loss = 4 calls
    assert fc["total_clips"] == 2
    assert fc["total_calls"] == 4
    # 2 clips * 5.0s = 10s per condition * 2 conditions = 20s
    assert fc["total_duration_seconds"] == pytest.approx(20.0)
    # 20s * 0.2 = 4.0 credits
    assert fc["projected_credits"] == pytest.approx(4.0)
    assert fc["is_under_budget"] is True

    # Test CLI dry run exits 0 and prints forecast
    rc = main([
        "--manifest", str(manifest),
        "--audio-root", str(audio_dir),
        "--output", str(out_file),
    ])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Line Noise Lab STT Pre-Flight Forecast" in captured.out
    assert "PASS (Within budget cap)" in captured.out


def test_runner_stops_before_overspending_budget(tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "s001.wav").write_bytes(make_test_wav(40000))  # 5.0s -> 1.0 credit
    (audio_dir / "s002.wav").write_bytes(make_test_wav(40000))  # 5.0s -> 1.0 credit

    manifest = tmp_path / "manifest.jsonl"
    rows = [
        {
            "id": "s001",
            "text": "test 1",
            "reference_transcribe": "ref 1",
            "entities": {"amount_paise": 45000},
            "audio": "s001.wav",
            "kind": "speech",
            "seed": 1,
            "source": "timbre",
        },
        {
            "id": "s002",
            "text": "test 2",
            "reference_transcribe": "ref 2",
            "entities": {"amount_paise": 5000},
            "audio": "s002.wav",
            "kind": "speech",
            "seed": 1,
            "source": "timbre",
        },
    ]
    manifest.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    fake_prisma = FakePrisma()

    # Case 1: Budget too small for first call
    config_too_small = RunnerConfig(
        manifest_path=manifest,
        audio_root=audio_dir,
        output_path=tmp_path / "results_small.jsonl",
        codecs=["g711"],
        snr_dbs=[None],
        loss_percents=[0.0],
        credits_per_second=0.2,
        max_credits=0.5,  # Needs 1.0 credit for first call
    )
    runner_small = Runner(config_too_small)
    with pytest.raises(BudgetExceeded, match="Budget limit"):
        runner_small.run(client=fake_prisma)

    # Case 2: Budget covers 1 call (1.0 credit), but fails before 2nd call (needs 2.0 total)
    out_partial = tmp_path / "results_partial.jsonl"
    config_partial = RunnerConfig(
        manifest_path=manifest,
        audio_root=audio_dir,
        output_path=out_partial,
        codecs=["g711"],
        snr_dbs=[None],
        loss_percents=[0.0],
        credits_per_second=0.2,
        max_credits=1.5,
    )
    runner_partial = Runner(config_partial)
    with pytest.raises(BudgetExceeded, match="Budget limit"):
        runner_partial.run(client=fake_prisma)

    # Check that checkpoint recorded the 1st call before halting
    lines = [ln for ln in out_partial.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["clip_id"] == "s001"
    assert record["credits_spent"] == pytest.approx(1.0)


def test_runner_executes_with_fake_prisma(tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "s001.wav").write_bytes(make_test_wav(40000))  # 5.0s

    manifest = tmp_path / "manifest.jsonl"
    row = {
        "id": "s001",
        "text": "brake ka part saade chaar sau rupaye, Somvaar shaam tak",
        "reference_transcribe": "brake ka part ₹450, Somvaar shaam tak",
        "entities": {"part": "brake", "amount_paise": 45000},
        "audio": "s001.wav",
        "kind": "speech",
        "seed": 20261004,
        "source": "timbre",
    }
    manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")

    out_file = tmp_path / "results_live.jsonl"
    cache_dir = tmp_path / "cache"
    config = RunnerConfig(
        manifest_path=manifest,
        audio_root=audio_dir,
        output_path=out_file,
        cache_dir=cache_dir,
        codecs=["g711", "amr_nb_4750"],
        snr_dbs=[None, 10.0],
        loss_percents=[0.0],
        credits_per_second=0.2,
        remaining_credits=1000.0,
        max_credits=500.0,
        ablation="noise_sweep",
    )

    fake_client = FakePrisma(reply="brake ka part ₹450, Somvaar shaam tak")
    runner = Runner(config, client=fake_client)

    results = runner.run()

    # 1 clip * 2 codecs * 2 snrs * 1 loss = 4 results
    assert len(results) == 4
    assert fake_client.call_count == 4

    expected_keys = {
        "clip_id",
        "codec",
        "snr",
        "loss",
        "variant",
        "transcript",
        "reference",
        "cer",
        "amount_matched",
        "latency_ms",
        "credits_spent",
    }

    for res in results:
        assert expected_keys.issubset(res.keys())
        assert res["clip_id"] == "s001"
        assert res["transcript"] == "brake ka part ₹450, Somvaar shaam tak"
        assert res["reference"] == "brake ka part ₹450, Somvaar shaam tak"
        assert res["cer"] == 0.0
        assert res["amount_matched"] is True
        assert res["latency_ms"] >= 0.0
        assert res["credits_spent"] == pytest.approx(1.0)
        assert res["variant"].startswith("noise_sweep_")

    # Verify checkpoint output file
    saved_lines = [ln for ln in out_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(saved_lines) == 4
    first_saved = json.loads(saved_lines[0])
    assert first_saved["clip_id"] == "s001"
    assert first_saved["cer"] == 0.0

    # Verify caching: cached WAV files were generated in cache_dir
    cached_files = list(cache_dir.glob("*.wav"))
    assert len(cached_files) == 4
