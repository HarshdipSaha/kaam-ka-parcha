import asyncio
import io
import json
from pathlib import Path
import socket
import sys
import wave
import pytest

# Ensure src and root are in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parcha.config import Settings
from parcha.credits import BudgetExceeded
from parcha.gnani_ws import pcm_frames, silence_frames, telephony_headers, WS_URL
import scripts.ws_flush_probe as ws_flush_probe


def make_wav_bytes(
    num_samples: int,
    sample_rate: int = 8000,
    channels: int = 1,
    sampwidth: int = 2,
    sample_val: bytes = b"\x12\x34",
) -> bytes:
    """Create in-memory WAV bytes with deterministic sample contents."""
    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(sample_val * num_samples)
    return bio.getvalue()


# ---------------------------------------------------------------------------
# 1. Test frame sizing and padding helpers in src/parcha/gnani_ws.py
# ---------------------------------------------------------------------------

def test_pcm_frames_exact_and_padded_chunks():
    """Verify pcm_frames returns exactly 1024-byte chunks, padded if needed."""
    # Case A: 512 samples = 1024 bytes -> exactly 1 chunk of 1024 bytes, 0 padding
    wav_1024 = make_wav_bytes(512)
    frames_1024 = pcm_frames(wav_1024)
    assert len(frames_1024) == 1
    assert len(frames_1024[0]) == 1024
    assert frames_1024[0] == b"\x12\x34" * 512

    # Case B: 1024 samples = 2048 bytes -> exactly 2 chunks of 1024 bytes
    wav_2048 = make_wav_bytes(1024)
    frames_2048 = pcm_frames(wav_2048)
    assert len(frames_2048) == 2
    assert all(len(f) == 1024 for f in frames_2048)

    # Case C: 500 samples = 1000 bytes -> padded with 24 zeros to 1024 bytes
    wav_1000 = make_wav_bytes(500)
    frames_1000 = pcm_frames(wav_1000)
    assert len(frames_1000) == 1
    assert len(frames_1000[0]) == 1024
    assert frames_1000[0][:1000] == b"\x12\x34" * 500
    assert frames_1000[0][1000:] == b"\x00" * 24

    # Case D: 1025 samples = 2050 bytes -> 2 full chunks + 1 chunk of 2 bytes + 1022 zeros
    wav_2050 = make_wav_bytes(1025)
    frames_2050 = pcm_frames(wav_2050)
    assert len(frames_2050) == 3
    assert all(len(f) == 1024 for f in frames_2050)
    assert frames_2050[2][:2] == b"\x12\x34"
    assert frames_2050[2][2:] == b"\x00" * 1022


def test_pcm_frames_format_validation():
    """Verify invalid sample rate, channel count, or empty audio raises ValueError."""
    # 16 kHz instead of 8 kHz
    wav_16k = make_wav_bytes(500, sample_rate=16000)
    with pytest.raises(ValueError, match="mono 8 kHz signed-16-bit WAV"):
        pcm_frames(wav_16k)

    # Stereo instead of mono
    wav_stereo = make_wav_bytes(500, channels=2)
    with pytest.raises(ValueError, match="mono 8 kHz signed-16-bit WAV"):
        pcm_frames(wav_stereo)

    # 8-bit instead of 16-bit
    wav_8bit = make_wav_bytes(500, sampwidth=1, sample_val=b"\x55")
    with pytest.raises(ValueError, match="mono 8 kHz signed-16-bit WAV"):
        pcm_frames(wav_8bit)

    # Empty WAV
    wav_empty = make_wav_bytes(0)
    with pytest.raises(ValueError, match="empty WS input"):
        pcm_frames(wav_empty)


def test_silence_frames_at_least_500ms_zero_padding():
    """Verify silence_frames produces at least 500ms of 1024-byte zero frames."""
    # Default: 8000 Hz, 500 ms minimum
    # Frame duration: 512 samples / 8000 = 64 ms per frame
    # ceil(500 / 64) = 8 frames
    # 8 frames * 64 ms = 512 ms (>= 500 ms)
    silence = silence_frames(8000, 500)
    assert len(silence) == 8
    assert all(len(f) == 1024 for f in silence)
    assert all(f == b"\x00" * 1024 for f in silence)
    assert sum(len(f) for f in silence) == 8192

    # Check 250 ms: ceil(250 / 64) = 4 frames -> 256 ms >= 250 ms
    silence_250 = silence_frames(8000, 250)
    assert len(silence_250) == 4
    assert all(f == b"\x00" * 1024 for f in silence_250)

    # Check 750 ms: ceil(750 / 64) = 12 frames -> 768 ms >= 750 ms
    silence_750 = silence_frames(8000, 750)
    assert len(silence_750) == 12
    assert all(f == b"\x00" * 1024 for f in silence_750)


def test_one_point_zero_three_second_wav_frames():
    """Verify 1.03-second 8kHz WAV:

    8240 samples = 16480 bytes -> 17 chunks of 1024 bytes.
    Frame count: 17
    Byte count: 17408
    All-zero tail on chunk 17: exactly 928 bytes of zeros.
    """
    duration_s = 1.03
    rate = 8000
    expected_samples = int(duration_s * rate)  # 8240 samples
    expected_pcm_bytes = expected_samples * 2   # 16480 bytes

    assert expected_samples == 8240
    assert expected_pcm_bytes == 16480

    wav_data = make_wav_bytes(expected_samples, sample_val=b"\xab\xcd")
    frames = pcm_frames(wav_data)

    # Frame count check: 16480 / 1024 = 16.09375 -> 17 chunks
    assert len(frames) == 17

    # Total byte count check: 17 * 1024 = 17408 bytes
    assert sum(len(f) for f in frames) == 17408
    assert all(len(f) == 1024 for f in frames)

    # The first 16 chunks are full audio PCM (16 * 1024 = 16384 bytes)
    for i in range(16):
        assert frames[i] == b"\xab\xcd" * 512

    # The 17th chunk contains remaining 96 bytes (48 samples) and 928 zero bytes
    remaining_audio_bytes = 16480 - (16 * 1024)
    expected_padding_bytes = 1024 - remaining_audio_bytes
    assert remaining_audio_bytes == 96
    assert expected_padding_bytes == 928

    assert frames[16][:96] == b"\xab\xcd" * 48
    assert frames[16][96:] == b"\x00" * 928
    assert all(b == 0 for b in frames[16][96:])


# ---------------------------------------------------------------------------
# 2. Verify that no network socket is opened during unit tests
# ---------------------------------------------------------------------------

def test_no_network_socket_opened_during_unit_tests_and_dry_run(monkeypatch, tmp_path):
    """Guard verifying that frame helpers, CLI parsing, and dry-run never open network sockets."""
    def disallow_connect(*args, **kwargs):
        raise AssertionError("Forbidden network socket open attempted during unit test!")

    monkeypatch.setattr(socket.socket, "connect", disallow_connect)

    # 1. Run frame sizing helpers
    wav = make_wav_bytes(512)
    _ = pcm_frames(wav)
    _ = silence_frames(8000, 500)
    _ = telephony_headers("test-key")

    # 2. Create dummy manifest and WAV file
    dummy_wav = tmp_path / "clip.wav"
    with wave.open(str(dummy_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        wf.writeframes(b"\x00\x00" * 800)  # 0.1s

    manifest_file = tmp_path / "manifest.jsonl"
    manifest_file.write_text(
        json.dumps({"audio_path": str(dummy_wav), "expected": "haan", "duration": 0.1}) + "\n",
        encoding="utf-8",
    )

    out_file = tmp_path / "out.jsonl"

    # 3. Run dry run - must not touch network socket
    res = ws_flush_probe.run_ws_probe(
        manifest_path=manifest_file,
        output_path=out_file,
        live=False,
        silence_ms=[250, 500],
    )
    assert res["status"] == "dry_run"
    assert not out_file.exists()


# ---------------------------------------------------------------------------
# 3. Test CLI argument parsing and dry-run mode of scripts/ws_flush_probe.py
# ---------------------------------------------------------------------------

def test_cli_argument_parsing_defaults():
    """Verify default CLI arguments."""
    args = ws_flush_probe.parse_args([])
    assert args.live is False
    assert args.manifest == ws_flush_probe.DEFAULT_MANIFEST
    assert args.max_credits == 2000.0
    assert args.silence_ms == [500]
    assert args.output == ws_flush_probe.DEFAULT_OUTPUT
    assert args.credits_per_second == 0.2
    assert args.timeout_s == 10.0


def test_cli_argument_parsing_custom():
    """Verify custom CLI argument parsing including silence tail variations."""
    # Comma-separated silence-ms
    args = ws_flush_probe.parse_args([
        "--live",
        "--manifest", "var/gates/custom_manifest.jsonl",
        "--max-credits", "500",
        "--silence-ms", "250,500,750",
        "--output", "var/gates/custom_out.jsonl",
        "--credits-per-second", "0.25",
        "--timeout-s", "8.0",
    ])
    assert args.live is True
    assert args.manifest == Path("var/gates/custom_manifest.jsonl")
    assert args.max_credits == 500.0
    assert args.silence_ms == [250, 500, 750]
    assert args.output == Path("var/gates/custom_out.jsonl")
    assert args.credits_per_second == 0.25
    assert args.timeout_s == 8.0

    # Space-separated silence-ms
    args_space = ws_flush_probe.parse_args(["--silence-ms", "250", "500", "750"])
    assert args_space.silence_ms == [250, 500, 750]


def test_dry_run_mode_manifest_validation_and_exit_code(tmp_path):
    """Verify dry-run mode validates manifest/clips, prints forecast, and exits 0."""
    dummy_wav = tmp_path / "affirmative_01.wav"
    with wave.open(str(dummy_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        wf.writeframes(b"\x01\x00" * 8000)  # 1.0 second

    manifest_path = tmp_path / "haan_ws.jsonl"
    manifest_path.write_text(
        json.dumps({"audio_path": str(dummy_wav), "expected": "haan", "duration": 1.0}) + "\n",
        encoding="utf-8",
    )

    out_path = tmp_path / "results.jsonl"

    # Call main() in dry-run mode
    ret = ws_flush_probe.main([
        "--manifest", str(manifest_path),
        "--output", str(out_path),
        "--silence-ms", "500",
    ])
    assert ret == 0
    assert not out_path.exists()  # Dry run must not write results file


def test_dry_run_mode_fallback_manifest_nonexistent():
    """Verify dry-run mode when default manifest file does not yet exist on disk."""
    args = [
        "--manifest", "var/gates/nonexistent_test_manifest.jsonl",
        "--silence-ms", "500",
    ]
    ret = ws_flush_probe.main(args)
    assert ret == 0


def test_budget_exceeded_check_in_live_mode(tmp_path):
    """Verify live mode terminates with BudgetExceeded when forecast exceeds cap."""
    dummy_wav = tmp_path / "long.wav"
    with wave.open(str(dummy_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        wf.writeframes(b"\x00\x00" * 8000 * 100)  # 100 seconds

    manifest_path = tmp_path / "manifest.jsonl"
    manifest_path.write_text(
        json.dumps({"audio_path": str(dummy_wav), "duration": 100.0}) + "\n",
        encoding="utf-8",
    )

    # 100s * 0.2 = 20 credits, cap set to 10 credits -> BudgetExceeded
    with pytest.raises(BudgetExceeded):
        ws_flush_probe.run_ws_probe(
            manifest_path=manifest_path,
            output_path=tmp_path / "res.jsonl",
            live=True,
            max_credits=10.0,
            credits_per_second=0.2,
        )


# ---------------------------------------------------------------------------
# 4. Test affirmative recovery matching and recovery rate calculation
# ---------------------------------------------------------------------------

def test_affirmative_recovery_logic():
    """Verify terminal affirmative detection and non-affirmative rejection."""
    # Affirmative Devanagari and Latin forms
    assert ws_flush_probe.is_affirmative_recovered("हाँ", "haan") is True
    assert ws_flush_probe.is_affirmative_recovered("हाँ ठीक है", "haan") is True
    assert ws_flush_probe.is_affirmative_recovered("theek hai", "theek hai") is True
    assert ws_flush_probe.is_affirmative_recovered("ha theek", "theek") is True
    assert ws_flush_probe.is_affirmative_recovered("जी हाँ", "ji") is True
    assert ws_flush_probe.is_affirmative_recovered("sahi hai sir", "sahi") is True

    # Empty or whitespace transcripts (premature VAD cut)
    assert ws_flush_probe.is_affirmative_recovered("", "haan") is False
    assert ws_flush_probe.is_affirmative_recovered("   ", "haan") is False
    assert ws_flush_probe.is_affirmative_recovered("...", "haan") is False

    # Negative or non-target phrases
    assert ws_flush_probe.is_affirmative_recovered("नहीं बदलना है", "haan") is False
    assert ws_flush_probe.is_affirmative_recovered("scooter ka brake band karo", "haan") is False


def test_recovery_rate_calculation():
    """Verify recovery rate calculation and gate criteria."""
    assert ws_flush_probe.calculate_recovery_rate(95, 100) == (95, 100)
    assert ws_flush_probe.calculate_recovery_rate(48, 50) == (48, 50)
    assert ws_flush_probe.calculate_recovery_rate(0, 0) == (0, 0)


# ---------------------------------------------------------------------------
# 5. Test mock live streaming and zero API key leakage
# ---------------------------------------------------------------------------

def test_mock_live_probe_execution_and_clean_recording(monkeypatch, tmp_path):
    """Verify full streaming execution, event capture, close code, and zero key leak."""
    secret_key = "gnani-super-secret-api-key-9999"

    class FakeClientConnection:
        def __init__(self, responses: list[dict]):
            self.responses = list(responses)
            self.sent_frames: list[bytes] = []
            self.close_code = 1000

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def send(self, frame: bytes):
            self.sent_frames.append(frame)

        async def recv(self):
            await asyncio.sleep(0.001)
            if self.responses:
                return json.dumps(self.responses.pop(0))
            return json.dumps({"type": "transcript", "text": ""})

    fake_conn_1 = FakeClientConnection([
        {"type": "ready", "session_id": "sess-001"},
        {"type": "transcript", "text": "हाँ ठीक है"},
    ])
    fake_conn_2 = FakeClientConnection([
        {"type": "ready", "session_id": "sess-002"},
        {"type": "transcript", "text": ""},  # Dropped reply
    ])
    connections = [fake_conn_1, fake_conn_2]

    def mock_connect(url, **kwargs):
        assert url == WS_URL
        # Verify header passes key
        assert kwargs["additional_headers"]["x-api-key-id"] == secret_key
        return connections.pop(0)

    import websockets
    monkeypatch.setattr(websockets, "connect", mock_connect)

    # Create 2 test clips
    c1 = tmp_path / "clip1.wav"
    with wave.open(str(c1), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        wf.writeframes(b"\x01\x00" * 4000)  # 0.5s

    c2 = tmp_path / "clip2.wav"
    with wave.open(str(c2), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        wf.writeframes(b"\x01\x00" * 4000)

    manifest_file = tmp_path / "test_manifest.jsonl"
    manifest_file.write_text(
        json.dumps({"audio_path": str(c1), "expected": "haan", "duration": 0.5}) + "\n" +
        json.dumps({"audio_path": str(c2), "expected": "theek hai", "duration": 0.5}) + "\n",
        encoding="utf-8",
    )

    out_file = tmp_path / "probe_output.jsonl"

    fake_settings = Settings(
        api_key=secret_key,
        gnani_base_url="https://api.vachana.ai",
        tts_voice="timbre-v2.5",
    )

    result = ws_flush_probe.run_ws_probe(
        manifest_path=manifest_file,
        output_path=out_file,
        live=True,
        silence_ms=[500],
        settings=fake_settings,
    )

    # Recovery checks: 1 recovered, 1 dropped -> (1, 2) = 50%
    summary = result["summary"]
    assert summary["passed"] is False  # 50% < 95% threshold
    assert summary["decision"] == "NO_GO"
    assert summary["recovered_count"] == 1
    assert summary["total_count"] == 2
    assert summary["recovery_fraction"] == 0.5

    # Check results file
    assert out_file.exists()
    file_content = out_file.read_text(encoding="utf-8")

    # Critical Zero-Leak Assertion: API key must NEVER be leaked in output file
    assert secret_key not in file_content

    lines = file_content.strip().split("\n")
    assert len(lines) == 3  # 1 summary + 2 item lines
    summary_obj = json.loads(lines[0])
    assert summary_obj["type"] == "summary"
    assert summary_obj["recovery_rate"] == "1/2"

    item_1 = json.loads(lines[1])
    assert item_1["type"] == "item"
    assert item_1["recovered"] is True
    assert item_1["close_code"] == 1000
    assert len(item_1["events"]) == 2

    item_2 = json.loads(lines[2])
    assert item_2["type"] == "item"
    assert item_2["recovered"] is False
    assert item_2["close_code"] == 1000
