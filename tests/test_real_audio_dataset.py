import numpy as np

from parcha.audio import _write_pcm
from parcha.lab.real_audio import select_indiccontext_rows
from parcha.lab.dataset import load_manifest, save_manifest
from scripts.prepare_indiccontext_benchmark import _duration
from scripts.prepare_user_youtube_benchmark import parse_vtt, select_caption_windows
from scripts.combine_real_audio_manifests import combine_manifests


def _row(name, *, domain, style, mixed, speaker, duration=12, text="Hindi utterance"):
    return {
        "audio": [{"src": f"https://example.test/{name}.wav"}],
        "reference_text_no_brackets": text,
        "duration": duration,
        "domain_name": domain,
        "speech_style": style,
        "code_mixing": mixed,
        "speaker_id": speaker,
        "file_name": f"{name}.wav",
    }


def test_selector_covers_strata_and_keeps_speakers_disjoint():
    rows = [
        _row("a", domain="Skilled Trades", style="Read", mixed=True, speaker="s1"),
        _row("b", domain="Skilled Trades", style="Read", mixed=True, speaker="s1"),
        _row("c", domain="Skilled Trades", style="Extempore", mixed=True, speaker="s2"),
        _row("d", domain="Engineering", style="Read", mixed=False, speaker="s3"),
        _row("e", domain="Engineering", style="Extempore", mixed=False, speaker="s4"),
        _row("too-short", domain="Arts", style="Read", mixed=False, speaker="s5", duration=2),
        _row("no-reference", domain="Arts", style="Read", mixed=False, speaker="s6", text=""),
    ]

    selected = select_indiccontext_rows(rows, limit=8, seed=17)

    assert {row["file_name"] for row in selected} == {"a.wav", "c.wav", "d.wav", "e.wav"}
    assert len({row["speaker_id"] for row in selected}) == len(selected)
    assert select_indiccontext_rows(rows, limit=8, seed=17) == selected


def test_selector_respects_requested_sample_limit():
    rows = [
        _row(str(i), domain=f"Domain {i}", style="Read", mixed=bool(i % 2), speaker=f"s{i}")
        for i in range(10)
    ]

    assert len(select_indiccontext_rows(rows, limit=6, seed=1)) == 6


def test_duration_uses_available_frames_when_streamed_wav_has_placeholder_count(tmp_path):
    wav = bytearray(_write_pcm(np.zeros(8000, dtype="<i2")))
    wav[40:44] = (2**31 - 1).to_bytes(4, "little")
    path = tmp_path / "streamed.wav"
    path.write_bytes(wav)

    assert _duration(path) == 1.0


def test_caption_windows_keep_auto_reference_text_and_prefer_repair_context():
    cues = parse_vtt("""WEBVTT

00:00:00.000 --> 00:00:04.000
आज clutch plate बदली है

00:00:04.000 --> 00:00:08.000
इसका price पंद्रह सौ रुपये है

00:00:08.000 --> 00:00:12.000
फिर labour cost बताता हूं
""")

    selected = select_caption_windows(cues, per_video=1)

    assert len(selected) == 1
    assert selected[0]["start"] == 0
    assert selected[0]["end"] == 12
    assert "clutch plate" in selected[0]["text"]
    assert "1500" not in selected[0]["text"]


def test_combiner_keeps_audio_paths_rooted_and_sources_attributed(tmp_path):
    audio_root = tmp_path / "audio"
    indic_audio = audio_root / "indiccontext"
    youtube_audio = audio_root / "youtube"
    indic_audio.mkdir(parents=True)
    youtube_audio.mkdir(parents=True)
    wav = _write_pcm(np.zeros(8000, dtype="<i2"))
    (indic_audio / "i001.wav").write_bytes(wav)
    (youtube_audio / "y001.wav").write_bytes(wav)
    indic_manifest = tmp_path / "indic.jsonl"
    youtube_manifest = tmp_path / "youtube.jsonl"
    save_manifest([{
        "id": "i001", "text": "sample", "reference_transcribe": "sample",
        "entities": {}, "audio": "i001.wav", "kind": "speech", "seed": 1,
        "source": "open_dataset", "reference_type": "dataset_reference",
    }], indic_manifest)
    save_manifest([{
        "id": "y001", "text": "sample", "reference_transcribe": "sample",
        "entities": {}, "audio": "y001.wav", "kind": "speech", "seed": 2,
        "source": "user_provided_youtube", "reference_type": "auto_caption",
    }], youtube_manifest)
    output = tmp_path / "combined.jsonl"

    count, digest = combine_manifests(
        [(indic_manifest, indic_audio), (youtube_manifest, youtube_audio)],
        audio_root=audio_root, output=output,
    )
    clips = load_manifest(output, audio_root=audio_root)

    assert count == 2
    assert len(digest) == 64
    assert [clip.audio for clip in clips] == ["indiccontext/i001.wav", "youtube/y001.wav"]
    assert [clip.reference_type for clip in clips] == ["dataset_reference", "auto_caption"]
