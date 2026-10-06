import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import render_amount_benchmark as renderer


def test_forecast_counts_characters_and_rounds_credits():
    assert renderer.forecast([{"text": "abcd", "voice": "Nalini"}] * 3) == {
        "rows": 3,
        "chars": 12,
        "credits": 0.6,
        "voices": ["Nalini"],
    }


def test_forecast_sorts_unique_voices_and_handles_empty_rows():
    assert renderer.forecast([
        {"text": "हाय", "voice": "Yashvi"},
        {"text": "ok", "voice": "Nalini"},
        {"text": "", "voice": "Yashvi"},
    ]) == {
        "rows": 3,
        "chars": 5,
        "credits": 0.25,
        "voices": ["Nalini", "Yashvi"],
    }
    assert renderer.forecast([]) == {
        "rows": 0,
        "chars": 0,
        "credits": 0.0,
        "voices": [],
    }


def test_dry_run_reads_utf8_bom_jsonl_without_loading_credentials(tmp_path, monkeypatch, capsys):
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        '\ufeff{"text":"abcd","voice":"Nalini"}\n'
        '{"text":"hi","voice":"Bhavna"}\n',
        encoding="utf-8",
    )

    def credentials_must_not_be_loaded():
        raise AssertionError("dry-run must not load settings")

    monkeypatch.setattr(renderer.Settings, "load", credentials_must_not_be_loaded)
    assert renderer.main(["--manifest", str(manifest)]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "rows": 2,
        "chars": 6,
        "credits": 0.3,
        "voices": ["Bhavna", "Nalini"],
    }


def test_dry_run_cli_works_with_no_api_key(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps({"text": "hello", "voice": "Nalini"}) + "\n",
        encoding="utf-8",
    )
    script = Path(renderer.__file__).resolve()
    project_root = script.parent.parent
    env = os.environ.copy()
    env["API_KEY"] = ""
    env["PYTHONPATH"] = str(project_root / "src")
    completed = subprocess.run(
        [sys.executable, str(script), "--manifest", str(manifest)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(completed.stdout) == {
        "rows": 1,
        "chars": 5,
        "credits": 0.25,
        "voices": ["Nalini"],
    }


@pytest.mark.parametrize("interval", ["-0.1", "nan", "inf"])
def test_invalid_request_interval_is_rejected(tmp_path, interval):
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        renderer.main([
            "--manifest", str(manifest),
            "--request-interval-seconds", interval,
        ])
    assert exc_info.value.code == 2


def test_live_mode_requires_gnani_credentials_before_creating_outputs(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps({"text": "hello", "voice": "Nalini", "audio": "clip.wav"}) + "\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "audio"
    monkeypatch.setattr(renderer.Settings, "load", lambda: renderer.Settings(api_key=""))

    with pytest.raises(ValueError, match="API_KEY is required"):
        renderer.main([
            "--manifest", str(manifest),
            "--audio-dir", str(output_dir),
            "--live",
        ])
    assert not output_dir.exists()


def test_live_render_reuses_clients_skips_cache_spaces_requests_and_closes(tmp_path, monkeypatch, capsys):
    manifest = tmp_path / "manifest.jsonl"
    rows = [
        {"text": "one", "voice": "Nalini", "audio": "one.wav"},
        {"text": "cached", "voice": "Bhavna", "audio": "cached.wav"},
        {"text": "hello", "voice": "Bhavna", "audio": "other.wav"},
        {"text": "two", "voice": "Nalini", "audio": "nested/two.wav"},
    ]
    manifest.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "cached.wav").write_bytes(b"keep")

    class FakeSettings:
        api_key = "test-only"
        gnani_base_url = "https://example.invalid"

        def require_gnani(self):
            pass

    constructed = []

    class FakeTimbreClient:
        def __init__(self, api_key, *, voice, base_url):
            self.voice = voice
            self.closed = False
            constructed.append(self)

        def synthesize(self, text):
            return f"{self.voice}:{text}".encode()

        def close(self):
            self.closed = True

    conversions = []
    pauses = []
    monkeypatch.setattr(renderer.Settings, "load", lambda: FakeSettings())
    monkeypatch.setattr(renderer, "TimbreClient", FakeTimbreClient)
    monkeypatch.setattr(
        renderer, "mulaw_to_wav",
        lambda payload: conversions.append(payload) or b"wav:" + payload,
    )
    monkeypatch.setattr(renderer.time, "sleep", pauses.append)

    assert renderer.main([
        "--manifest", str(manifest),
        "--audio-dir", str(audio_dir),
        "--live",
        "--request-interval-seconds", "0.25",
    ]) == 0

    assert (audio_dir / "cached.wav").read_bytes() == b"keep"
    assert (audio_dir / "one.wav").read_bytes() == b"wav:Nalini:one"
    assert (audio_dir / "other.wav").read_bytes() == b"wav:Bhavna:hello"
    assert (audio_dir / "nested" / "two.wav").read_bytes() == b"wav:Nalini:two"
    assert conversions == [b"Nalini:one", b"Bhavna:hello", b"Nalini:two"]
    assert pauses == [0.25, 0.25]
    assert [client.voice for client in constructed] == ["Nalini", "Bhavna"]
    assert all(client.closed for client in constructed)
    assert json.loads(capsys.readouterr().out) == {
        "rows": 4,
        "chars": 17,
        "credits": 0.85,
        "voices": ["Bhavna", "Nalini"],
    }


def _install_live_clients(monkeypatch, *, synthesize_failure=None, close_failures=()):
    class FakeSettings:
        api_key = "test-only"
        gnani_base_url = "https://example.invalid"

        def require_gnani(self):
            pass

    clients = []

    class FakeTimbreClient:
        def __init__(self, api_key, *, voice, base_url):
            self.voice = voice
            self.closed = False
            clients.append(self)

        def synthesize(self, text):
            if self.voice == synthesize_failure:
                raise ValueError(f"synthesis failed for {self.voice}")
            return f"{self.voice}:{text}".encode()

        def close(self):
            self.closed = True
            if self.voice in close_failures:
                raise RuntimeError(f"close failed for {self.voice}")

    monkeypatch.setattr(renderer.Settings, "load", lambda: FakeSettings())
    monkeypatch.setattr(renderer, "TimbreClient", FakeTimbreClient)
    monkeypatch.setattr(renderer, "mulaw_to_wav", lambda payload: b"wav:" + payload)
    monkeypatch.setattr(renderer.time, "sleep", lambda seconds: None)
    return clients


def _two_voice_render_args(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    rows = [
        {"text": "one", "voice": "Nalini", "audio": "one.wav"},
        {"text": "two", "voice": "Bhavna", "audio": "two.wav"},
    ]
    manifest.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return [
        "--manifest", str(manifest),
        "--audio-dir", str(tmp_path / "audio"),
        "--live",
        "--request-interval-seconds", "0",
    ]


def _install_side_effect_tracker(monkeypatch):
    settings_loads = []
    clients = []
    requests = []

    class FakeSettings:
        api_key = "test-only"
        gnani_base_url = "https://example.invalid"

        def require_gnani(self):
            pass

    class FakeTimbreClient:
        def __init__(self, api_key, *, voice, base_url):
            self.voice = voice
            clients.append(self)

        def synthesize(self, text):
            requests.append((self.voice, text))
            return b"mulaw"

        def close(self):
            pass

    monkeypatch.setattr(
        renderer.Settings,
        "load",
        lambda: settings_loads.append(True) or FakeSettings(),
    )
    monkeypatch.setattr(renderer, "TimbreClient", FakeTimbreClient)
    monkeypatch.setattr(renderer, "mulaw_to_wav", lambda payload: b"wav")
    monkeypatch.setattr(renderer.time, "sleep", lambda seconds: None)
    return settings_loads, clients, requests


def _live_args_for_rows(tmp_path, rows, audio_dir=None):
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    output_dir = tmp_path / "audio" if audio_dir is None else audio_dir
    return [
        "--manifest", str(manifest),
        "--audio-dir", str(output_dir),
        "--live",
        "--request-interval-seconds", "0",
    ], output_dir


def test_cleanup_attempts_every_client_and_reports_close_failure(tmp_path, monkeypatch):
    clients = _install_live_clients(monkeypatch, close_failures={"Nalini"})

    with pytest.raises(RuntimeError, match="close failed for Nalini"):
        renderer.main(_two_voice_render_args(tmp_path))

    assert [client.voice for client in clients] == ["Nalini", "Bhavna"]
    assert all(client.closed for client in clients)


def test_synthesis_error_remains_primary_when_client_cleanup_fails(tmp_path, monkeypatch):
    clients = _install_live_clients(
        monkeypatch,
        synthesize_failure="Bhavna",
        close_failures={"Nalini"},
    )

    with pytest.raises(ValueError, match="synthesis failed for Bhavna") as exc_info:
        renderer.main(_two_voice_render_args(tmp_path))

    assert all(client.closed for client in clients)
    assert any("close failed for Nalini" in note for note in exc_info.value.__notes__)


@pytest.mark.parametrize("bad_path_kind", ["traversal", "absolute", "root"])
def test_live_preflight_rejects_late_escaping_or_root_path_before_side_effects(
    tmp_path, monkeypatch, bad_path_kind
):
    output_dir = tmp_path / "audio"
    if bad_path_kind == "traversal":
        bad_path = "../escaped.wav"
    elif bad_path_kind == "absolute":
        bad_path = str(tmp_path / "escaped.wav")
    else:
        bad_path = "."
    rows = [
        {"text": "first", "voice": "Nalini", "audio": "first.wav"},
        {"text": "later", "voice": "Bhavna", "audio": bad_path},
    ]
    args, output_dir = _live_args_for_rows(tmp_path, rows, output_dir)
    settings_loads, clients, requests = _install_side_effect_tracker(monkeypatch)

    with pytest.raises(ValueError, match="row 2"):
        renderer.main(args)

    assert settings_loads == []
    assert clients == []
    assert requests == []
    assert not output_dir.exists()


@pytest.mark.parametrize(
    "bad_audio",
    [
        {"text": "later", "voice": "Bhavna", "audio": "nested/../same.wav"},
        {"text": "later", "voice": "Bhavna", "audio": "same.wav"},
    ],
)
def test_live_preflight_rejects_duplicate_resolved_destinations_before_side_effects(
    tmp_path, monkeypatch, bad_audio
):
    rows = [
        {"text": "first", "voice": "Nalini", "audio": "same.wav"},
        bad_audio,
    ]
    args, output_dir = _live_args_for_rows(tmp_path, rows)
    settings_loads, clients, requests = _install_side_effect_tracker(monkeypatch)

    with pytest.raises(ValueError, match="duplicate audio destination"):
        renderer.main(args)

    assert settings_loads == []
    assert clients == []
    assert requests == []
    assert not output_dir.exists()


def test_live_preflight_rejects_symlink_escape_before_side_effects(tmp_path, monkeypatch):
    output_dir = tmp_path / "audio"
    output_dir.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    link = output_dir / "outside-link"
    try:
        link.symlink_to(outside_dir, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"directory symlinks are unavailable: {exc}")

    rows = [
        {"text": "first", "voice": "Nalini", "audio": "first.wav"},
        {"text": "later", "voice": "Bhavna", "audio": "outside-link/escaped.wav"},
    ]
    args, _ = _live_args_for_rows(tmp_path, rows, output_dir)
    settings_loads, clients, requests = _install_side_effect_tracker(monkeypatch)

    with pytest.raises(ValueError, match="row 2"):
        renderer.main(args)

    assert settings_loads == []
    assert clients == []
    assert requests == []
    assert not (output_dir / "first.wav").exists()
    assert not (outside_dir / "escaped.wav").exists()


@pytest.mark.parametrize(
    "bad_row",
    [
        {"voice": "Bhavna", "audio": "bad.wav"},
        {"text": None, "voice": "Bhavna", "audio": "bad.wav"},
        {"text": "later", "audio": "bad.wav"},
        {"text": "later", "voice": ["Bhavna"], "audio": "bad.wav"},
        {"text": "later", "voice": "Bhavna"},
        {"text": "later", "voice": "Bhavna", "audio": 5},
    ],
)
def test_live_preflight_rejects_late_missing_or_invalid_fields_before_side_effects(
    tmp_path, monkeypatch, bad_row
):
    rows = [
        {"text": "first", "voice": "Nalini", "audio": "first.wav"},
        bad_row,
    ]
    args, output_dir = _live_args_for_rows(tmp_path, rows)
    settings_loads, clients, requests = _install_side_effect_tracker(monkeypatch)

    with pytest.raises(ValueError, match="row 2"):
        renderer.main(args)

    assert settings_loads == []
    assert clients == []
    assert requests == []
    assert not output_dir.exists()


@pytest.mark.parametrize(
    ("filename", "expected_rows", "expected_chars", "expected_credits"),
    [
        ("estimates.jsonl", 120, 7140, 357.0),
        ("corrections.jsonl", 40, 1084, 54.2),
    ],
)
def test_generated_amount_manifests_have_expected_forecasts(
    filename, expected_rows, expected_chars, expected_credits
):
    path = Path("data/benchmarks/amount_v2") / filename
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines()]
    result = renderer.forecast(rows)
    assert result["rows"] == expected_rows
    assert result["chars"] == expected_chars
    assert result["credits"] == expected_credits


def test_bias_control_manifest_forecast_is_available():
    path = Path("data/benchmarks/amount_v2/bias_control.jsonl")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines()]
    result = renderer.forecast(rows)
    assert result["rows"] == 20
    assert result["chars"] == 418
    assert result["credits"] == 20.9
