import json

import numpy as np
import pytest
from pydantic import ValidationError

from parcha.audio import _write_pcm
from parcha.lab.dataset import load_manifest
from parcha.lab.metrics import canonical_reference
from parcha.lab.runner import Runner, RunnerConfig


def _manifest_row(*, clip_id="g0001", reference="मॉडल model <stammers> चार सौ", **overrides):
    return {
        "id": clip_id,
        "text": reference,
        "reference_transcribe": reference,
        "entities": {},
        "audio": f"{clip_id}.wav",
        "kind": "speech",
        "seed": 1,
        "source": "open_dataset",
        "expected_amounts_paise": [40000],
        **overrides,
    }


def _write_manifest(path, row, *, bom=False):
    text = json.dumps(row, ensure_ascii=False) + "\n"
    path.write_text(("\ufeff" if bom else "") + text, encoding="utf-8")


def _runner(tmp_path, row, responses, *, stt_modes=None, bias_words=None):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / row["audio"]).write_bytes(
        _write_pcm(np.full(8000, 1000, dtype="<i2"))
    )
    manifest = tmp_path / "manifest.jsonl"
    _write_manifest(manifest, row)

    class ScriptedPrisma:
        def __init__(self):
            self.calls = []
            self.responses = iter(responses)

        def transcribe(self, wav, *, mode, bias=None):
            self.calls.append((mode, bias))
            response = next(self.responses)
            if isinstance(response, Exception):
                raise response
            return response

    client = ScriptedPrisma()
    runner = Runner(RunnerConfig(
        manifest_path=manifest,
        audio_root=audio_dir,
        output_path=tmp_path / "results.jsonl",
        codecs=["none"],
        snr_dbs=[None],
        loss_percents=[0.0],
        max_credits=10,
        remaining_credits=10,
        stt_modes=stt_modes or ["verbatim"],
        bias_words=bias_words,
        noise_path=None,
    ), client=client)
    return runner, client


def test_canonical_reference_strips_tags_and_latin_glosses():
    assert canonical_reference(
        "मॉडल model <stammers> करंट Current [noise] चार सौ"
    ) == "मॉडल करंट चार सौ"


def test_manifest_accepts_four_digit_suffix_and_expected_amounts(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    _write_manifest(manifest, _manifest_row())

    [clip] = load_manifest(manifest, require_audio=False)

    assert clip.id == "g0001"
    assert clip.expected_amounts_paise == [40000]
    assert clip.voice is None
    assert clip.audio_sha256 is None


def test_manifest_loads_utf8_bom_jsonl(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    _write_manifest(manifest, _manifest_row(), bom=True)

    [clip] = load_manifest(manifest, require_audio=False)

    assert clip.id == "g0001"


@pytest.mark.parametrize("invalid_amount", [True, "40000", 40000.0])
def test_manifest_rejects_coercible_expected_amounts_paise(tmp_path, invalid_amount):
    manifest = tmp_path / "manifest.jsonl"
    row = _manifest_row(expected_amounts_paise=[invalid_amount])
    _write_manifest(manifest, row)

    with pytest.raises(ValidationError):
        load_manifest(manifest, require_audio=False)


def test_runner_records_canonical_reference_and_amount_labels(tmp_path):
    row = _manifest_row()
    runner, _ = _runner(tmp_path, row, ["मॉडल चार सौ"])

    [result] = runner.run()

    assert result["reference_canonical"] == "मॉडल चार सौ"
    assert result["cer_canonical"] == 0.0
    assert result["cer"] > 0.0
    assert result["outcome"] == "ok"
    assert result["expected_amounts_paise"] == [40000]


def test_runner_marks_whitespace_transcript_empty_without_canonical_cer(tmp_path):
    row = _manifest_row(reference="मॉडल चार सौ")
    runner, _ = _runner(tmp_path, row, [" \t\n "])

    [result] = runner.run()

    assert result["outcome"] == "empty_transcript"
    assert result["cer_canonical"] is None


def test_nobias_verbatim_mode_uses_verbatim_api_without_bias(tmp_path):
    row = _manifest_row(reference="मॉडल चार सौ")
    runner, client = _runner(
        tmp_path,
        row,
        ["मॉडल चार सौ", "मॉडल चार सौ"],
        stt_modes=["verbatim", "verbatim_nobias"],
        bias_words=["brake"],
    )

    results = runner.run()

    assert client.calls == [("verbatim", ["brake"]), ("verbatim", None)]
    assert [row["stt_mode"] for row in results] == ["verbatim", "verbatim_nobias"]


def test_runner_marks_provider_error_outcome_without_canonical_cer(tmp_path):
    from parcha.gnani import GnaniError

    row = _manifest_row(reference="मॉडल चार सौ")
    runner, _ = _runner(tmp_path, row, [GnaniError("provider failed")])

    [result] = runner.run()

    assert result["outcome"] == "provider_error"
    assert result["cer_canonical"] is None


def test_resume_rejects_result_rows_missing_task7_schema_fields(tmp_path):
    row = _manifest_row(reference="मॉडल चार सौ")
    runner, _ = _runner(tmp_path, row, ["मॉडल चार सौ"])
    runner.run()

    output = runner.config.output_path
    sidecar = output.with_suffix(output.suffix + ".meta.json")
    assert sidecar.exists()
    saved_row = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
    for field in (
        "reference_canonical",
        "cer_canonical",
        "outcome",
        "expected_amounts_paise",
    ):
        saved_row.pop(field)
    output.write_text(json.dumps(saved_row, ensure_ascii=False) + "\n", encoding="utf-8")

    runner.config.resume = True

    class CountingPrisma:
        def __init__(self):
            self.calls = []

        def transcribe(self, wav, *, mode, bias=None):
            self.calls.append((mode, bias))
            return "मॉडल चार सौ"

    resumed_client = CountingPrisma()
    with pytest.raises(ValueError, match="saved result line 1 is missing required row fields"):
        Runner(runner.config, client=resumed_client).run()

    assert resumed_client.calls == []


def test_real_audio_exclusions_record_known_reference_problems():
    from pathlib import Path

    exclusions_path = Path(__file__).resolve().parents[1] / "data" / "benchmarks" / "exclusions.json"

    assert json.loads(exclusions_path.read_text(encoding="utf-8")) == {
        "i036": "reference/audio mismatch (R9 §3)",
        "y001": "auto-caption pseudo-reference",
        "y002": "auto-caption pseudo-reference",
        "y003": "auto-caption pseudo-reference",
        "y004": "auto-caption pseudo-reference",
        "y005": "auto-caption pseudo-reference",
    }
