import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from parcha.app import create_app
from parcha.money import confusable_amount
from tests.fakes import ScriptedPrisma
from tests.test_money_path import CardExtractor, T_EN, V_EN, abstentions, card, service

PART = "items.part-1.amount_paise"


@pytest.mark.parametrize("spoken", ["इक्कीस हज़ार", "इकतीस हज़ार", "तैंतालीस सौ", "पैंतालीस हज़ार", "अड़तीस सौ", "अस्सी",
                                    "तेरह सौ", "उन्नीस सौ", "पंद्रह सौ"])
def test_look_alike_number_words_are_confusable(spoken):
    assert confusable_amount(spoken)


@pytest.mark.parametrize("spoken", ["साढ़े चार सौ", "बारह सौ", "दो सौ", "डेढ़ हज़ार", "पाँच सौ रुपये", "पचास", "दस हज़ार", "तीस हज़ार"])
def test_everyday_amounts_are_not_confusable(spoken):
    assert not confusable_amount(spoken)


def _reask(wf, sid, revision, transcribe, verbatim):
    wf.prisma.script.extend([transcribe, verbatim])
    return wf.reask(sid, PART, b"r", "audio/webm", expected_revision=revision)


def test_a_confusable_amount_needs_a_third_agreeing_recording():
    t_in, v_in = "front brake pad ₹21,000, labour ₹200, Somvaar", "front brake pad इक्कीस हज़ार labour do sau Somvaar"
    wf, _, sid = service(ScriptedPrisma([t_in, v_in]), CardExtractor(card()))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)                    # recording 1 (candidate)
    s2 = _reask(wf, sid, s1.revision, "₹21,000", "इक्कीस हज़ार")                      # recording 2 agrees: not enough
    assert s2.card.items[0].amount_paise is None
    assert abstentions(s2)[PART] == "confusable_needs_third"
    s3 = _reask(wf, sid, s2.revision, "₹21,000", "इक्कीस हज़ार")                      # recording 3 agrees: settles
    assert s3.card.items[0].amount_paise == 2100000


def test_a_disagreeing_third_recording_resets_the_confusable_count():
    t_in, v_in = "front brake pad ₹21,000, labour ₹200, Somvaar", "front brake pad इक्कीस हज़ार labour do sau Somvaar"
    wf, _, sid = service(ScriptedPrisma([t_in, v_in]), CardExtractor(card()))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    s2 = _reask(wf, sid, s1.revision, "₹21,000", "इक्कीस हज़ार")
    s3 = _reask(wf, sid, s2.revision, "₹31,000", "इकतीस हज़ार")                      # the line was lying; they now differ
    assert s3.card.items[0].amount_paise is None
    assert abstentions(s3)[PART] == "recordings_disagree"
    s4 = _reask(wf, sid, s3.revision, "₹31,000", "इकतीस हज़ार")                      # agrees with last, but is confusable again
    assert s4.card.items[0].amount_paise is None
    assert abstentions(s4)[PART] == "confusable_needs_third"
    s5 = _reask(wf, sid, s4.revision, "₹31,000", "इकतीस हज़ार")
    assert s5.card.items[0].amount_paise == 3100000


def test_everyday_amounts_still_settle_on_two_recordings():
    wf, _, sid = service(ScriptedPrisma([T_EN, V_EN]), CardExtractor(card()))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    s2 = _reask(wf, sid, s1.revision, "₹450", "साढ़े चार सौ")
    assert s2.card.items[0].amount_paise == 45000


def test_the_api_cannot_skip_the_extra_step(fake_services):
    t_in, v_in = "front brake pad ₹21,000, labour ₹200, Somvaar", "front brake pad इक्कीस हज़ार labour do sau Somvaar"
    fake_services.workflow.prisma = ScriptedPrisma([t_in, v_in])
    fake_services.workflow.extractor = CardExtractor(card())
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    body = client.post(f"/sessions/{sid}/intake", data={"expected_revision": 0},
                       files={"audio": ("a.wav", b"x", "audio/wav")}).json()
    for expected_state in ("confusable_needs_third", None):
        fake_services.workflow.prisma.script.extend(["₹21,000", "इक्कीस हज़ार"])
        body = client.post(f"/sessions/{sid}/reask/{PART}", data={"expected_revision": body["revision"]},
                           files={"audio": ("a.wav", b"x", "audio/wav")}).json()
        assert body["abstentions"].get(PART) == expected_state
    assert body["card"]["items"][0]["amount_paise"] == 2100000


RESULTS = [Path("var/lab/reask_recovery.jsonl"), Path("var/lab/reask_heldout.jsonl")]


@pytest.mark.skipif(not all(p.is_file() for p in RESULTS), reason="private saved benchmark rows are not in this checkout")
def test_replay_catches_every_known_wrong_settle_and_flags_few_correct_ones():
    """Offline replay of the 1,930 saved live rows (965 voice pairs): free, no API calls."""
    from parcha.lab.reask_bench import VOICES, rescore

    wrong, correct = [], []
    for path in RESULTS:
        rows = rescore(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
        by = {(r["case_id"], r["condition"], r["voice"]): r for r in rows}
        for (case_id, condition, voice), first in by.items():
            second = by.get((case_id, condition, VOICES[1]))
            if voice != VOICES[0] or second is None or first["paise"] is None or first["paise"] != second["paise"]:
                continue
            flagged = confusable_amount(first["verbatim"]) or confusable_amount(second["verbatim"])
            (correct if first["paise"] == first["expected_paise"] else wrong).append(flagged)
    assert len(wrong) == 3 and all(wrong)                       # 21,000-for-31,000 twice and 13-for-1,300
    assert sum(correct) / len(correct) < 0.20                   # the price: about 1 in 6 benchmark settles needs a third take


def test_benchmark_pairing_counts_look_alike_pairs_as_needing_a_third_recording():
    from parcha.lab.reask_bench import VOICES, paired_outcomes

    def row(voice, verbatim, paise=2100000):
        return {"case_id": "r1", "condition": "g711|0", "voice": voice, "paise": paise,
                "expected_paise": 3100000, "verbatim": verbatim}

    result = paired_outcomes([row(VOICES[0], "इक्कीस हज़ार"), row(VOICES[1], "इक्कीस हज़ार")])["ALL"]
    assert result["settled_wrong"] == 0 and result["needs_third"] == 1 and result["settled"] == 0
