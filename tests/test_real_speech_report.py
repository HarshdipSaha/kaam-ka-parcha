import pytest

from parcha.lab.real_speech_report import (ATTRIBUTION, licensed_rows, private_summary, public_summary,
                                           relative_degradation)


def row(clip, snr, cer, *, mixed=False, source="open_dataset", lic="CC BY 4.0", mode="transcribe", codec="g711"):
    return {"clip_id": clip, "source": source, "source_license": lic, "stt_mode": mode, "codec": codec, "snr": snr,
            "cer": cer, "wer": cer * 2, "clip_type": "speech",
            "stratum": f"Domain|Read|code_mixed={'true' if mixed else 'false'}"}


def sweep(clip, clean, noisy, **kw):
    return [row(clip, None, clean, **kw)] + [row(clip, s, noisy, **kw) for s in (10.0, 5.0, 0.0)]


ROWS = sweep("i001", 0.10, 0.15) + sweep("i002", 0.20, 0.30, mixed=True) + sweep("y001", 0.1, 0.9, source="user_provided_youtube", lic="unknown")


def test_only_licensed_dataset_rows_are_used():
    assert {r["clip_id"] for r in licensed_rows(ROWS)} == {"i001", "i002"}
    assert "y001" not in private_summary(ROWS)


def test_relative_change_is_paired_against_clean_and_split_by_code_mix():
    entries = relative_degradation(ROWS, bootstrap=50)
    pick = lambda s: next(e for e in entries if e["slice"] == s and e["metric"] == "cer" and e["snr"] == "0dB")
    assert pick("all")["relative_change_pct"] == pytest.approx(50.0)          # (0.45-0.30)/0.30
    assert pick("code_mixed")["clips"] == 1 and pick("monolingual")["clips"] == 1
    assert pick("code_mixed")["relative_change_pct"] == pytest.approx(50.0)


def test_public_summary_is_fail_closed_without_consent():
    with pytest.raises(PermissionError):
        public_summary(ROWS, organizer_consent=False, consent_ref="X-1")
    with pytest.raises(PermissionError):
        public_summary(ROWS, organizer_consent=True, consent_ref="  ")


def test_public_summary_has_attribution_no_absolute_rates_and_no_competitors():
    text = public_summary(ROWS, organizer_consent=True, consent_ref="DISCORD-2026-10-REF")
    assert ATTRIBUTION in text and "AI4Bharat" in text and "+50%" in text
    assert "0.10" not in text and "0.15" not in text
    with pytest.raises(ValueError):
        public_summary(ROWS, organizer_consent=True, consent_ref="compared with whisper")
