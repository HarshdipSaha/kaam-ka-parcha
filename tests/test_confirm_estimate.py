import pytest

from parcha.gnani import GnaniError
from parcha.session import Conflict
from parcha.workflow import NothingToConfirm
from tests.fakes import ScriptedPrisma
from tests.test_money_path import CardExtractor, T_EN, V_EN, abstentions, card, service

PART = "items.part-1.amount_paise"
LABOUR = "items.labour-1.amount_paise"
T_DIFF = "front brake pad ₹450, labour ₹300, Somvaar shaam tak"
V_DIFF = "front brake pad saade chaar sau labour teen sau Somvaar shaam tak"


def start():
    wf, _, sid = service(ScriptedPrisma([T_EN, V_EN]), CardExtractor(card()))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert [it.amount_paise for it in s1.card.items] == [None, None]
    return wf, sid, s1


def confirm(wf, sid, revision, transcribe, verbatim):
    wf.prisma.script.extend([transcribe, verbatim])
    return wf.confirm_estimate(sid, b"r", "audio/webm", expected_revision=revision)


def test_one_repeat_settles_every_agreeing_amount():
    wf, sid, s1 = start()
    s2 = confirm(wf, sid, s1.revision, T_EN, V_EN)
    assert [it.amount_paise for it in s2.card.items] == [45000, 20000]
    assert abstentions(s2).get(PART) == abstentions(s1).get(PART)   # no new abstain logs for settled items
    assert s2.logs[-1].mode == "confirm_estimate" and s2.logs[-1].audio_sha256
    assert s2.revision == s1.revision + 1


def test_a_disagreeing_amount_stays_flagged_and_the_other_settles():
    wf, sid, s1 = start()
    s2 = confirm(wf, sid, s1.revision, T_DIFF, V_DIFF)
    assert s2.card.items[0].amount_paise == 45000
    assert s2.card.items[1].amount_paise is None
    assert abstentions(s2)[LABOUR] == "recordings_disagree"
    # the newly heard value is the candidate: a second repeat that agrees with it settles it
    s3 = confirm(wf, sid, s2.revision, T_DIFF, V_DIFF)
    assert [it.amount_paise for it in s3.card.items] == [45000, 30000]


def test_settled_items_are_not_touched_by_a_later_repeat():
    wf, sid, s1 = start()
    s2 = confirm(wf, sid, s1.revision, T_DIFF, V_DIFF)
    assert s2.card.items[0].amount_paise == 45000
    s3 = confirm(wf, sid, s2.revision, "front brake pad ₹900, labour ₹300, Somvaar shaam tak",
                 "front brake pad nau sau labour teen sau Somvaar shaam tak")
    assert s3.card.items[0].amount_paise == 45000          # settled earlier, never overwritten
    assert s3.card.items[1].amount_paise == 30000


def test_count_mismatch_settles_nothing_and_keeps_candidates():
    wf, sid, s1 = start()
    s2 = confirm(wf, sid, s1.revision, "front brake pad ₹450, Somvaar shaam tak",
                 "front brake pad saade chaar sau Somvaar shaam tak")
    assert [it.amount_paise for it in s2.card.items] == [None, None]
    assert set(abstentions(s2).values()) == {"ambiguous_attachment"}
    candidate = next(ev for ev in s2.card.evidence if ev.field == PART)
    assert candidate.quote.strip() and candidate.review_score == 0.0   # intake candidate preserved


def test_different_spoken_order_still_attaches_by_label():
    wf, sid, s1 = start()
    s2 = confirm(wf, sid, s1.revision, "labour ₹200, front brake pad ₹450, Somvaar shaam tak",
                 "labour do sau front brake pad saade chaar sau Somvaar shaam tak")
    assert [it.amount_paise for it in s2.card.items] == [45000, 20000]


def test_empty_recording_logs_a_reason_and_changes_no_amount():
    wf, sid, s1 = start()
    s2 = confirm(wf, sid, s1.revision, "", "")
    assert [it.amount_paise for it in s2.card.items] == [None, None]
    assert set(abstentions(s2).values()) == {"empty_transcript"}


def test_provider_429_is_a_repeat_not_an_error():
    wf, sid, s1 = start()
    wf.prisma.script.append(GnaniError("rate limited", status=429))
    s2 = wf.confirm_estimate(sid, b"r", "audio/webm", expected_revision=s1.revision)
    assert set(abstentions(s2).values()) == {"provider_429"}


def test_stale_revision_conflicts_before_any_speech_call():
    wf, sid, s1 = start()
    wf.prisma.script.extend([T_EN, V_EN])
    with pytest.raises(Conflict):
        wf.confirm_estimate(sid, b"r", "audio/webm", expected_revision=s1.revision - 1)
    assert len(wf.prisma.script) == 2        # nothing consumed


def test_nothing_to_confirm_when_all_amounts_settled():
    wf, sid, s1 = start()
    s2 = confirm(wf, sid, s1.revision, T_EN, V_EN)
    with pytest.raises(NothingToConfirm):
        wf.confirm_estimate(sid, b"r", "audio/webm", expected_revision=s2.revision)


# ---- HTTP surface -------------------------------------------------------------------------------------------
from fastapi.testclient import TestClient

from parcha.app import create_app
from tests.fakes import INTAKE_T, INTAKE_V


def api_client(fake_services):
    fake_services.workflow.prisma = ScriptedPrisma([INTAKE_T, INTAKE_V])
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    body = client.post(f"/sessions/{sid}/intake", data={"expected_revision": 0},
                       files={"audio": ("a.wav", b"bytes", "audio/wav")}).json()
    return client, sid, body


def post_confirm(client, sid, revision):
    return client.post(f"/sessions/{sid}/confirm-estimate", data={"expected_revision": revision},
                       files={"audio": ("a.wav", b"bytes", "audio/wav")})


def test_payload_reports_which_flagged_amounts_were_heard_once(fake_services):
    _, _, body = api_client(fake_services)
    assert set(body["heard_once"]) == {PART, LABOUR}


def test_route_settles_both_amounts_with_one_recording(fake_services):
    client, sid, body = api_client(fake_services)
    fake_services.workflow.prisma.script.extend([INTAKE_T, INTAKE_V])
    res = post_confirm(client, sid, body["revision"])
    assert res.status_code == 200
    assert [it["amount_paise"] for it in res.json()["card"]["items"]] == [45000, 20000]
    assert res.json()["heard_once"] == []
    # nothing left to confirm
    again = post_confirm(client, sid, res.json()["revision"])
    assert again.status_code == 422


def test_route_rejects_stale_revision_empty_audio_and_unknown_session(fake_services):
    client, sid, body = api_client(fake_services)
    assert post_confirm(client, sid, body["revision"] - 1).status_code == 409
    empty = client.post(f"/sessions/{sid}/confirm-estimate", data={"expected_revision": body["revision"]},
                        files={"audio": ("a.wav", b"", "audio/wav")})
    assert empty.status_code == 422
    assert post_confirm(client, "nope", 0).status_code == 404


def test_confirmed_session_is_immutable(fake_services):
    from dataclasses import replace

    client, sid, body = api_client(fake_services)
    store = fake_services.store
    store._items[sid] = replace(store.get(sid), status="confirmed")   # state forced: guard must still hold
    fake_services.workflow.prisma.script.extend([INTAKE_T, INTAKE_V])
    assert post_confirm(client, sid, body["revision"]).status_code == 409
    assert len(fake_services.workflow.prisma.script) == 2              # no speech call was made
