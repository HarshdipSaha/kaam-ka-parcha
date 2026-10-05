import json
from pathlib import Path
import numpy as np
import pytest

from parcha.audio import _read_pcm, _write_pcm, erase_frames
from parcha.credits import BudgetExceeded
from parcha.gnani import GnaniError
from parcha.lab.runner import Runner, RunnerConfig, get_clip_duration, main


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
    assert "Impulse profiles (4): none, impact_wrench, metal_spanner, compressor_exhaust" in captured.out
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
        "stt_mode",
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
        assert res["wer"] == 0.0
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


def test_runner_splits_audio_longer_than_gnani_rest_limit(tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    source = make_test_wav(32 * 8000 + 4800)  # 32.6 seconds
    (audio_dir / "s001.wav").write_bytes(source)
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({
        "id": "s001", "text": "idle", "reference_transcribe": "",
        "entities": {}, "audio": "s001.wav", "kind": "engine_only",
        "seed": 1, "source": "recorded_ambient",
    }) + "\n", encoding="utf-8")

    class LengthCheckingPrisma:
        def __init__(self):
            self.durations = []

        def transcribe(self, wav: bytes, *, mode: str = "transcribe") -> str:
            self.durations.append(len(_read_pcm(wav)) / 8000)
            return ""

    client = LengthCheckingPrisma()
    config = RunnerConfig(
        manifest_path=manifest, audio_root=audio_dir, output_path=tmp_path / "out.jsonl",
        codecs=["g711"], snr_dbs=[None], loss_percents=[0], max_credits=20,
        remaining_credits=20,
    )
    runner = Runner(config, client=client)

    forecast = runner.forecast()
    results = runner.run()

    assert forecast["total_calls"] == 2
    assert forecast["projected_credits"] == pytest.approx(32.6 * 0.2)
    assert client.durations == pytest.approx([29.0, 3.6])
    assert all(duration <= 30 for duration in client.durations)
    assert len(results) == 1
    assert results[0]["transcript"] == ""
    assert results[0]["transcription_error"] is None
    assert results[0]["api_chunks"] == 2


def test_forecast_accounts_for_amr_padding_at_chunk_boundary(tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "s001.wav").write_bytes(make_test_wav(29 * 8000))
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({
        "id": "s001", "text": "idle", "reference_transcribe": "",
        "entities": {}, "audio": "s001.wav", "kind": "engine_only",
        "seed": 1, "source": "recorded_ambient",
    }) + "\n", encoding="utf-8")

    class CountingPrisma(FakePrisma):
        def __init__(self):
            super().__init__(reply="")
            self.durations = []

        def transcribe(self, wav: bytes, *, mode: str = "transcribe") -> str:
            self.durations.append(len(_read_pcm(wav)) / 8000)
            return super().transcribe(wav, mode=mode)

    client = CountingPrisma()
    runner = Runner(RunnerConfig(
        manifest_path=manifest, audio_root=audio_dir, output_path=tmp_path / "out.jsonl",
        codecs=["amr_nb_4750"], snr_dbs=[None], loss_percents=[0],
        impulse_profiles=[None], max_credits=10, remaining_credits=10,
    ), client=client)

    forecast = runner.forecast()
    result = runner.run()[0]

    assert forecast["total_calls"] == 2
    assert client.call_count == 2
    assert result["api_chunks"] == 2
    assert max(client.durations) <= 29


def test_runner_marks_long_clip_rejected_if_any_chunk_fails(tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "s001.wav").write_bytes(make_test_wav(70 * 8000))
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({
        "id": "s001", "text": "idle", "reference_transcribe": "",
        "entities": {}, "audio": "s001.wav", "kind": "engine_only",
        "seed": 1, "source": "recorded_ambient",
    }) + "\n", encoding="utf-8")

    class PartlyRejectedPrisma:
        def __init__(self):
            self.call_count = 0

        def transcribe(self, wav: bytes, *, mode: str = "transcribe") -> str:
            self.call_count += 1
            raise GnaniError("Gnani request failed: HTTP 429")

    client = PartlyRejectedPrisma()
    config = RunnerConfig(
        manifest_path=manifest, audio_root=audio_dir, output_path=tmp_path / "out.jsonl",
        codecs=["g711"], snr_dbs=[None], loss_percents=[0], max_credits=20,
        remaining_credits=20,
    )
    result = Runner(config, client=client).run()[0]

    assert client.call_count == 1
    assert result["api_chunks"] == 1
    assert result["transcript"] is None
    assert result["transcription_error"] == "Gnani request failed: HTTP 429"
    assert result["hallucinated_word_count"] is None


def test_runner_runs_configured_formats_and_bias_with_correct_forecast(tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "s001.wav").write_bytes(make_test_wav(8000))
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({
        "id": "s001", "text": "brake pad", "reference_transcribe": "brake pad",
        "entities": {}, "audio": "s001.wav", "kind": "speech", "seed": 1,
        "source": "timbre",
    }) + "\n", encoding="utf-8")

    class FormatCheckingPrisma:
        def __init__(self):
            self.calls = []

        def transcribe(self, wav: bytes, *, mode: str, bias=None) -> str:
            self.calls.append((mode, bias))
            return mode

    client = FormatCheckingPrisma()
    config = RunnerConfig(
        manifest_path=manifest,
        audio_root=audio_dir,
        output_path=tmp_path / "out.jsonl",
        codecs=["g711"],
        snr_dbs=[None],
        loss_percents=[0.0],
        stt_modes=["transcribe", "verbatim"],
        bias_words=["brake", "clutch"],
        max_credits=10,
        remaining_credits=10,
    )
    runner = Runner(config, client=client)

    forecast = runner.forecast()
    results = runner.run()

    assert forecast["total_calls"] == 2
    assert forecast["projected_credits"] == pytest.approx(0.4)
    assert client.calls == [("transcribe", None), ("verbatim", ["brake", "clutch"])]
    assert [row["stt_mode"] for row in results] == ["transcribe", "verbatim"]
    assert [row["transcript"] for row in results] == ["transcribe", "verbatim"]


def test_runner_writes_source_stratum_and_word_error_rate(tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "i001.wav").write_bytes(make_test_wav(8000))
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({
        "id": "i001", "text": "clutch pad", "reference_transcribe": "Clutch, pad!",
        "entities": {}, "audio": "i001.wav", "kind": "speech", "seed": 1,
        "source": "open_dataset", "source_dataset": "IndicContextEval",
        "source_row": "row-1", "stratum": "Engineering|Read|mixed",
    }) + "\n", encoding="utf-8")

    class PunctuationOnlyDifference:
        def transcribe(self, wav: bytes, *, mode: str = "transcribe") -> str:
            return "clutch pad"

    result = Runner(RunnerConfig(
        manifest_path=manifest, audio_root=audio_dir, output_path=tmp_path / "out.jsonl",
        codecs=["g711"], snr_dbs=[None], loss_percents=[0], max_credits=10,
        remaining_credits=10,
    ), client=PunctuationOnlyDifference()).run()[0]

    assert result["source"] == "open_dataset"
    assert result["source_dataset"] == "IndicContextEval"
    assert result["source_row"] == "row-1"
    assert result["stratum"] == "Engineering|Read|mixed"
    assert result["wer"] == 0.0


def test_runner_cli_exposes_modes_bias_and_spacing():
    from parcha.lab.runner import parse_args

    args = parse_args([
        "--stt-modes", "transcribe,verbatim", "--bias-words", "brake,clutch",
        "--request-interval-seconds", "2", "--codecs", "g711",
        "--snr-dbs", "clean,10,5,0",
    ])

    assert args.stt_modes == "transcribe,verbatim"
    assert args.bias_words == "brake,clutch"
    assert args.request_interval_seconds == 2
    assert args.codecs == "g711"
    assert args.snr_dbs == "clean,10,5,0"


def test_forecast_duration_uses_available_frames_from_streamed_wav(tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    wav = bytearray(make_test_wav(8000))
    wav[40:44] = (2**31 - 1).to_bytes(4, "little")
    (audio_dir / "i001.wav").write_bytes(wav)
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({
        "id": "i001", "text": "sample", "reference_transcribe": "sample",
        "entities": {}, "audio": "i001.wav", "kind": "speech", "seed": 1,
    }) + "\n", encoding="utf-8")

    row = json.loads(manifest.read_text(encoding="utf-8"))
    from parcha.lab.dataset import Clip

    assert get_clip_duration(Clip.model_validate(row), audio_dir) == 1.0


def test_live_cli_reports_provider_error_as_aborted_sweep(monkeypatch, capsys):
    class ErrorResultRunner:
        def __init__(self, config):
            self.config = config

        def forecast(self):
            return {
                "manifest_path": self.config.manifest_path, "total_clips": 1,
                "codecs": ["g711"], "snr_dbs": [None], "loss_percents": [0],
                "impulse_profiles": [None], "stt_modes": ["transcribe"],
                "total_calls": 1, "total_duration_seconds": 1,
                "projected_credits": 0.2, "remaining_credits": 5000,
                "max_credits": 5000, "is_under_budget": True,
            }

        def run(self):
            return [{"api_chunks": 1, "transcription_error": "Gnani request failed: HTTP 429"}]

    monkeypatch.setattr("parcha.lab.runner.Runner", ErrorResultRunner)

    rc = main(["--live", "--manifest", "manifest.jsonl"])

    assert rc == 1
    assert "aborted after provider error" in capsys.readouterr().out


def test_runner_stops_the_sweep_after_rate_limit(tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "s001.wav").write_bytes(make_test_wav(8000))
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({
        "id": "s001", "text": "test", "reference_transcribe": "test",
        "entities": {}, "audio": "s001.wav", "kind": "speech", "seed": 1,
        "source": "timbre",
    }) + "\n", encoding="utf-8")

    class RateLimitedPrisma:
        def __init__(self):
            self.call_count = 0

        def transcribe(self, wav: bytes, *, mode: str = "transcribe") -> str:
            self.call_count += 1
            raise GnaniError("Gnani request failed: HTTP 429")

    client = RateLimitedPrisma()
    runner = Runner(RunnerConfig(
        manifest_path=manifest,
        audio_root=audio_dir,
        output_path=tmp_path / "out.jsonl",
        codecs=["g711", "amr_nb_4750"],
        snr_dbs=[None, 10.0],
        loss_percents=[0.0],
        max_credits=10,
        remaining_credits=10,
    ), client=client)

    results = runner.run()

    assert client.call_count == 1
    assert len(results) == 1
    assert results[0]["transcription_error"] == "Gnani request failed: HTTP 429"


def test_runner_resume_skips_completed_calls_after_local_preparation_failure(tmp_path, monkeypatch):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "s001.wav").write_bytes(make_test_wav(40000))
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({
        "id": "s001", "text": "test", "reference_transcribe": "test",
        "entities": {}, "audio": "s001.wav", "kind": "speech", "seed": 1,
    }) + "\n", encoding="utf-8")
    output = tmp_path / "results.jsonl"
    config = RunnerConfig(
        manifest_path=manifest, audio_root=audio_dir, output_path=output,
        codecs=["g711"], snr_dbs=[None, 10.0], loss_percents=[0],
        noise_path=None, max_credits=10, remaining_credits=10,
    )
    first_client = FakePrisma()
    first_runner = Runner(config, client=first_client)
    original_degrade = first_runner.degrade_audio

    def fail_on_noisy_condition(source_wav, codec, snr, loss, impulse_profile=None):
        if snr == 10.0:
            raise ValueError("local mix failed before request")
        return original_degrade(source_wav, codec, snr, loss, impulse_profile)

    monkeypatch.setattr(first_runner, "degrade_audio", fail_on_noisy_condition)
    with pytest.raises(ValueError, match="local mix failed"):
        first_runner.run()
    assert first_client.call_count == 1
    assert output.exists()
    assert output.with_suffix(output.suffix + ".meta.json").exists()

    resume_config = RunnerConfig(
        manifest_path=manifest, audio_root=audio_dir, output_path=output,
        codecs=["g711"], snr_dbs=[None, 10.0], loss_percents=[0],
        noise_path=None, max_credits=10.0, remaining_credits=10.0,
        request_interval_seconds=0.0, resume=True,
    )
    resumed_client = FakePrisma()
    resumed = Runner(resume_config, client=resumed_client).run()

    assert resumed_client.call_count == 1
    assert len(resumed) == 1
    assert resumed[0]["snr"] == 10.0
    assert len(output.read_text(encoding="utf-8").splitlines()) == 2


def test_runner_resume_rejects_grid_changes(tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "s001.wav").write_bytes(make_test_wav(8000))
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({
        "id": "s001", "text": "test", "reference_transcribe": "test",
        "entities": {}, "audio": "s001.wav", "kind": "speech", "seed": 1,
    }) + "\n", encoding="utf-8")
    output = tmp_path / "results.jsonl"
    Runner(RunnerConfig(
        manifest_path=manifest, audio_root=audio_dir, output_path=output,
        codecs=["g711"], snr_dbs=[None], max_credits=10, remaining_credits=10,
    ), client=FakePrisma()).run()

    changed = Runner(RunnerConfig(
        manifest_path=manifest, audio_root=audio_dir, output_path=output,
        codecs=["g711"], snr_dbs=[None, 10], max_credits=10,
        remaining_credits=10, resume=True,
    ), client=FakePrisma())
    with pytest.raises(ValueError, match="configuration does not match"):
        changed.run()
