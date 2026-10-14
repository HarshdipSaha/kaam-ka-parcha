import hashlib
import json
import pytest

from scripts import benchmark_timbre_v3 as benchmark


@pytest.mark.parametrize('cap', [float('nan'), float('inf'), -1, 0])
def test_invalid_budget_is_rejected(cap):
    with pytest.raises(ValueError):
        benchmark.ensure_within_cap({'estimated_credits': 1}, cap)


def test_live_retry_forecast_is_checked_before_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark.Settings, 'load', lambda: pytest.fail('credentials loaded'))
    with pytest.raises(ValueError, match='exceeds cap'):
        benchmark.run_live([{'id': 'one', 'text': '1234567890', 'voice': 'Shivani'}],
                           ['timbre-v3.0'], tmp_path / 'run', max_credits=1)


def test_forecast_accounts_for_each_model_and_refuses_an_over_cap_run():
    rows = [{"id": "one", "text": "simple estimate", "voice": "Vikrant"}]
    forecast = benchmark.forecast(rows, ["timbre-v2.5", "timbre-v3.0"])
    assert forecast == {"cases": 1, "requests": 2, "characters": 30, "estimated_credits": 1.5}
    assert benchmark.ensure_within_cap(forecast, 1.5) is None


def test_committed_v3_manifest_exercises_inline_expression_tags():
    rows = benchmark._read_manifest(benchmark.DEFAULT_MANIFEST)
    text = " ".join(row["text"] for row in rows)
    assert "<pauses>" in text
    assert "<slow>" in text


def test_live_run_writes_a_sanitized_jsonl_log_and_raw_audio(tmp_path, monkeypatch):
    class FakeSettings:
        api_key = "test-only-key"
        gnani_base_url = "https://example.invalid"

        def require_gnani(self):
            pass

    class FakeTimbre:
        def __init__(self, api_key, *, voice, model, base_url):
            assert api_key == "test-only-key"
            self.voice, self.model = voice, model

        def synthesize(self, text):
            return bytes([255]) * 16

        def close(self):
            pass

    monkeypatch.setattr(benchmark.Settings, "load", lambda: FakeSettings())
    monkeypatch.setattr(benchmark, "TimbreClient", FakeTimbre)
    rows = [{"id": "case-1", "text": "simple estimate", "voice": "Vikrant"}]
    output = benchmark.run_live(rows, ["timbre-v3.0"], tmp_path / "run", max_credits=100_000)

    records = [json.loads(line) for line in (output / "results.jsonl").read_text(encoding="utf-8").splitlines()]
    assert records[0]["status"] == "success"
    assert records[0]["audio_sha256"] == hashlib.sha256(bytes([255]) * 16).hexdigest()
    assert records[0]["audio_bytes"] == 16
    assert records[0]["api_key"] is None
    assert (output / records[0]["audio_file"]).read_bytes() == bytes([255]) * 16
    assert json.loads((output / "manifest.json").read_text(encoding="utf-8"))["max_credits"] == 100_000


def test_live_run_logs_a_redacted_error_message(tmp_path, monkeypatch):
    class FakeSettings:
        api_key = "secret-key"
        gnani_base_url = "https://example.invalid"

        def require_gnani(self):
            pass

    class FailingTimbre:
        def __init__(self, *args, **kwargs):
            pass

        def synthesize(self, text):
            raise RuntimeError("HTTP 400 rejected secret-key")

    monkeypatch.setattr(benchmark.Settings, "load", lambda: FakeSettings())
    monkeypatch.setattr(benchmark, "TimbreClient", FailingTimbre)
    output = benchmark.run_live(
        [{"id": "case-1", "text": "simple estimate", "voice": "Vikrant"}],
        ["timbre-v3.0"], tmp_path / "run", max_credits=100_000,
    )

    record = json.loads((output / "results.jsonl").read_text(encoding="utf-8"))
    assert record["error_message"] == "HTTP 400 rejected [REDACTED]"


def test_live_run_retries_a_transient_timbre_500(tmp_path, monkeypatch):
    from parcha.gnani import GnaniError

    class FakeSettings:
        api_key = "test-key"
        gnani_base_url = "https://example.invalid"

        def require_gnani(self):
            pass

    class FlakyTimbre:
        calls = 0

        def __init__(self, *args, **kwargs):
            pass

        def synthesize(self, text):
            self.__class__.calls += 1
            if self.calls == 1:
                raise GnaniError("Gnani request failed: HTTP 500", status=500)
            return b"audio"

    monkeypatch.setattr(benchmark.Settings, "load", lambda: FakeSettings())
    monkeypatch.setattr(benchmark, "TimbreClient", FlakyTimbre)
    monkeypatch.setattr(benchmark.time, "sleep", lambda seconds: None)
    output = benchmark.run_live(
        [{"id": "case-1", "text": "simple estimate", "voice": "Vikrant"}],
        ["timbre-v3.0"], tmp_path / "run", max_credits=100_000,
    )

    record = json.loads((output / "results.jsonl").read_text(encoding="utf-8"))
    assert record["status"] == "success"
    assert record["attempts"] == 2
