import re

from fastapi.testclient import TestClient

from parcha.app import create_app
from tests.test_pages import awaiting

SIM = ("Simulated phone line: the audio is processed to sound like a call. "
       "No real call is placed.")


def test_workshop_page_is_hindi_first_and_keeps_its_contract(fake_services):
    html = TestClient(create_app(fake_services)).get("/workshop").text
    assert '<html lang="hi">' in html and "/static/ui.js" in html and "/static/parcha.css" in html
    assert "बोलिए" in html and "Kaam ka Parcha — Workshop Estimate" in html
    # A working tool does not label the mechanic's own estimate "synthetic"; only the scripted mock mode is a demo.
    assert "Synthetic demo data" not in html and "pill--demo" not in html
    assert "<style>" not in html and ">Kind<" not in html
    for element_id in ("record", "stop", "message", "transcript", "card", "start-readback",
                       "customer-link", "review-section", "review-count"):
        assert f'id="{element_id}"' in html


def test_customer_page_is_a_call_with_unticked_consent(fake_services):
    client, sid, _ = awaiting(fake_services)
    html = client.get(f"/customer/{sid}").text
    assert "यह नकली फ़ोन लाइन है" in html and SIM in html
    assert "गैराज से कॉल" in html and "₹1,000" in html and "पार्ट" in html and "Kaam ka Parcha — Customer Estimate Review" in html
    box = re.search(r'<input[^>]*id="dpdp-consent-checkbox"[^>]*>', html).group(0)
    assert "checked" not in box
    assert re.search(r'id="readback-caption"[^>]*>\s*\S', html)
    assert "DPDP Act 2023" in html and "<style>" not in html


def test_stage_creates_one_session_and_frames_both_phones(fake_services):
    client = TestClient(create_app(fake_services))
    html = client.get("/stage").text
    sid = re.search(r'src="/customer/([A-Za-z0-9_-]+)"', html).group(1)
    assert f'src="/workshop?session_id={sid}"' in html
    assert client.get(f"/sessions/{sid}").status_code == 200
    assert html.count('allow="microphone; autoplay; clipboard-write"') == 2
    assert "Gnani Prisma" in html and "Gnani Timbre" in html
