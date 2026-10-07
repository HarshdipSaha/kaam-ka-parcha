import io
import wave

from parcha.lab.youtube_eval import ChunkResult, score_case, split_wav, summarize


def _wav(seconds: float, rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(2) * int(seconds * rate))
    return buf.getvalue()


def _seconds(wav: bytes) -> float:
    with wave.open(io.BytesIO(wav), "rb") as w:
        return w.getnframes() / w.getframerate()


def test_split_makes_rest_safe_overlapping_chunks_that_cover_the_audio():
    chunks = split_wav(_wav(60))
    assert all(_seconds(c) <= 25.0 + 1e-6 for c in chunks)
    assert len(chunks) == 3 and abs(_seconds(chunks[-1]) - 14.0) < 0.1  # 23 s step: 25 + 25 + 14 (overlapped)


def test_short_audio_is_one_chunk():
    assert len(split_wav(_wav(5))) == 1


def test_recall_counts_annotated_amounts_per_pass_and_where_both_agree():
    chunks = [
        ChunkResult("साढ़े चार सौ रुपये लेबर दो सौ रुपये", "04:30 ₹100 लेबर ₹200"),
        ChunkResult("तीन हज़ार सात सौ पचासी रुपये", "₹3,500 रुपये"),
    ]
    result = score_case([45000, 20000, 378500, 0], chunks)
    assert result["expected"] == 3
    assert result["recovered_verbatim"] == 3          # 450, 200 and "तीन हज़ार सात सौ पचासी" = 3,785
    assert result["recovered_transcribe"] == 2        # the transcribe pass wrote ₹3,500 for the last one
    assert result["recovered_agreed"] == 2            # so only 450 and 200 are agreed by both passes
    assert result["missed"] == []


def test_summary_adds_up():
    parts = [{"expected": 3, "recovered_verbatim": 2, "recovered_transcribe": 1, "recovered_agreed": 1},
             {"expected": 2, "recovered_verbatim": 2, "recovered_transcribe": 2, "recovered_agreed": 2}]
    assert summarize(parts) == {"cases": 2, "expected_amounts": 5, "recovered_verbatim": 4,
                                "recovered_transcribe": 3, "recovered_agreed": 3}
