import re

from fastapi.testclient import TestClient

from parcha.app import create_app


def resolve_amounts(client, sid, rev=1):
    """Single-recording amounts need a deliberate repeat before read-back (independent-confirmation gate)."""
    for field in ("items.part-1.amount_paise", "items.labour-1.amount_paise"):
        rev = client.post(f"/sessions/{sid}/reask/{field}", data={"expected_revision": rev},
                          files={"audio": ("c.wav", b"recorded correction", "audio/wav")}).json()["revision"]
    return rev


def awaiting(fake_services):
    fake_services.workflow.timbre = fake_services.timbre
    client = TestClient(create_app(fake_services))
    sid = client.post("/sessions").json()["id"]
    rev = client.post(f"/sessions/{sid}/intake", data={"expected_revision": 0},
                      files={"audio": ("a.wav", b"x", "audio/wav")}).json()["revision"]
    rev = resolve_amounts(client, sid, rev)
    client.post(f"/sessions/{sid}/readback", data={"expected_revision": rev})
    return client, sid, rev


def confirm(fake_services, client, sid, rev):
    fake_services.workflow.prisma.transcribe = lambda wav, mode, **kw: "हाँ ठीक है"
    res = client.post(f"/sessions/{sid}/reply", data={"expected_revision": rev, "readback_revision": rev},
                      files={"audio": ("r.wav", b"haan", "audio/wav")})
    assert res.json()["outcome"] == "confirmed"


def test_static_design_system_is_served(fake_services):
    client = TestClient(create_app(fake_services))
    css = client.get("/static/parcha.css")
    assert css.status_code == 200 and "--counter: #F3EEE3" in css.text and "prefers-reduced-motion" in css.text
    assert 'id="mic"' in client.get("/static/icons.svg").text


def test_unconfirmed_parcha_is_not_called_verified(fake_services):
    client, sid, _ = awaiting(fake_services)
    html = client.get(f"/verify/{sid}").text
    assert '<html lang="hi">' in html and "/static/parcha.css" in html
    assert "अभी मंज़ूर नहीं" in html and "असली पर्चा" not in html
    assert "Audit Verification" in html and "BSA 2023" in html and "Compliant" in html
    assert "var(--danger)" not in html


def test_confirmed_parcha_shows_verdict_slip_and_evidence(fake_services):
    client, sid, rev = awaiting(fake_services)
    confirm(fake_services, client, sid, rev)
    html = client.get(f"/verify/{sid}").text
    assert "असली पर्चा" in html and "Verified electronic record" in html
    assert "₹1,000" in html and "₹500" in html and "पार्ट" in html and "लेबर" in html
    assert "front brake pad" in html and "KA-01-AB-1234" not in html and "DPDP Act 2023" in html
    assert re.search(r'id="manifest-digest"[^>]*>[0-9a-f]{64}<', html)
    assert "मंज़ूर" in html                     # the stamp


def test_static_assets_are_versioned_so_a_deploy_cannot_leave_a_stale_stylesheet(fake_services):
    import re

    client = TestClient(create_app(fake_services))
    html = client.get("/workshop").text
    versions = set(re.findall(r'/static/(?:parcha\.css|ui\.js|app\.js)\?v=([0-9a-f]{10})', html))
    assert len(versions) == 1                       # one content hash, used by the stylesheet and both scripts
    assert client.get(f"/static/parcha.css?v={versions.pop()}").status_code == 200
