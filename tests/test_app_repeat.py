from fastapi.testclient import TestClient

from parcha.app import create_app
from tests.fakes import INTAKE_T, ScriptedPrisma


def post_intake(client, sid):
    return client.post(f"/sessions/{sid}/intake", data={"expected_revision": 0},
                       files={"audio": ("a.wav", b"bytes", "audio/wav")})


def test_empty_transcripts_return_a_structured_repeat_request(fake_services):
    fake_services.workflow.prisma = ScriptedPrisma(["", ""])
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    res = post_intake(client, sid)
    assert res.status_code == 422
    assert res.json()["detail"] == {"repeat": True, "reason": "empty_transcript"}
    assert client.get(f"/sessions/{sid}").json()["revision"] == 0


def test_independent_confirmation_abstention_has_actionable_hindi_label(fake_services):
    client = TestClient(create_app(fake_services))
    response = client.get("/static/ui.js")

    assert response.status_code == 200
    assert 'independent_confirmation_required: "रकम दोबारा बोलकर पक्की करें"' in response.text


def test_session_payload_explains_each_amount_awaiting_re_ask(fake_services):
    fake_services.workflow.prisma = ScriptedPrisma([INTAKE_T, "front brake pad saade labour do sau Somvaar shaam tak"])
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    body = post_intake(client, sid).json()
    assert body["abstentions"] == {
        "items.part-1.amount_paise": "incomplete_number",
        "items.labour-1.amount_paise": "independent_confirmation_required",
    }
    assert "items.part-1.amount_paise" in body["review_fields"]
