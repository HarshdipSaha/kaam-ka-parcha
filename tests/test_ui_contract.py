import json

from fastapi.testclient import TestClient

from parcha.app import create_app


def _reject_constant(name):
    raise ValueError(f"non-JSON constant {name}")


def _intake(client, sid, rev=0):
    return client.post(f"/sessions/{sid}/intake", data={"expected_revision": rev},
                       files={"audio": ("a.wav", b"bytes", "audio/wav")})


def test_payload_carries_display_fields(fake_services):
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    body = _intake(client, sid).json()
    assert len(body["parcha_no"]) == 6 and body["parcha_no"].isdigit()
    assert body["status_label"] == "जाँच बाकी"
    assert "front brake pad" in body["mechanic_transcript"]
    assert body["readback_text"] is None
    assert body["readback_revision"] is None
    assert body["abstentions"] == {}          # money-path key still present


def test_readback_response_is_strict_json_when_no_noise_is_mixed(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    fake_services.workflow.noise_wav = None   # measured SNR becomes +inf
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    rev = _intake(client, sid).json()["revision"]
    res = client.post(f"/sessions/{sid}/readback", data={"expected_revision": rev})
    assert res.status_code == 200
    body = json.loads(res.text, parse_constant=_reject_constant)
    assert body["manifest"]["measured_snr_db"] is None
    payload = client.get(f"/sessions/{sid}").json()
    assert payload["readback_text"] == body["text"]
    assert payload["readback_revision"] == body["readback_revision"]
