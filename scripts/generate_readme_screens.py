"""Generate crisp, high-resolution, production screenshots for README.md.

Uses Playwright with device_scale_factor=2 for retina-crisp images without ugly
synthetic badges, expired dates, or clipped elements.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
import hashlib
from pathlib import Path
import threading
import time

from playwright.sync_api import sync_playwright
import uvicorn

from parcha.app import AppServices, create_app
from parcha.config import Settings
from parcha.schema import Delivery, Evidence, JobCard, LineItem, TranscriptLog
from parcha.session import Session, SessionStore

OUT = Path("docs/ui")
OUT.mkdir(parents=True, exist_ok=True)
PORT = 8769


def create_mock_wav() -> bytes:
    """Minimal valid 1-second 8kHz mono PCM WAV for audio players."""
    import struct
    sample_rate = 8000
    num_samples = sample_rate
    raw_data = b"\x00\x00" * num_samples
    data_size = len(raw_data)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,  # PCM
        1,  # mono
        sample_rate,
        sample_rate * 2,
        2,
        16,
        b"data",
        data_size,
    )
    return header + raw_data


def setup_sessions(store: SessionStore) -> tuple[str, str]:
    now = datetime(2026, 11, 10, 8, 30, 0, tzinfo=timezone.utc)
    wav_bytes = create_mock_wav()
    wav_hash = hashlib.sha256(wav_bytes).hexdigest()

    # Session 1: Workshop in-progress (Safety gate: 2 items flagged for re-ask)
    s1 = store.create()
    c1 = JobCard(
        items=(
            LineItem(id="part-1", label="फ्रंट ब्रेक पैड पार्ट", kind="part", amount_paise=None),
            LineItem(id="labour-1", label="लेबर", kind="labour", amount_paise=None),
        ),
        delivery=Delivery(
            date=date(2026, 11, 10),
            window="evening",
            spoken="मंगलवार शाम तक",
        ),
        evidence=(
            Evidence(field="items.part-1.label", quote="फ्रंट ब्रेक पैड", review_score=0.95),
            Evidence(field="items.part-1.amount_paise", quote="साढ़े चार सौ", review_score=0.0),
            Evidence(field="items.labour-1.label", quote="लेबर", review_score=0.95),
            Evidence(field="items.labour-1.amount_paise", quote="दो सौ", review_score=0.0),
            Evidence(field="delivery", quote="मंगलवार शाम तक", review_score=0.95),
        ),
    )
    logs1 = (
        TranscriptLog(
            role="mechanic",
            mode="intake",
            text="फ्रंट ब्रेक पैड पार्ट साढ़े चार सौ रुपये, लेबर दो सौ रुपये, मंगलवार शाम तक।",
            recorded_at_utc=now,
            audio_sha256=wav_hash,
        ),
    )
    store._items[s1.id] = replace(s1, card=c1, status="review", revision=1, logs=logs1)

    # Session 2: Customer Review & Confirmed Sealed Parcha (Real Phone Call channel)
    s2 = store.create()
    c2 = JobCard(
        items=(
            LineItem(id="part-1", label="फ्रंट ब्रेक पैड पार्ट", kind="part", amount_paise=45000),
            LineItem(id="labour-1", label="लेबर", kind="labour", amount_paise=20000),
        ),
        delivery=Delivery(
            date=date(2026, 11, 10),
            window="evening",
            spoken="मंगलवार शाम तक",
        ),
        evidence=(
            Evidence(field="items.part-1.label", quote="फ्रंट ब्रेक पैड", review_score=0.95),
            Evidence(field="items.part-1.amount_paise", quote="साढ़े चार सौ", review_score=0.98),
            Evidence(field="items.labour-1.label", quote="लेबर", review_score=0.95),
            Evidence(field="items.labour-1.amount_paise", quote="दो सौ", review_score=0.98),
            Evidence(field="delivery", quote="मंगलवार शाम तक", review_score=0.95),
        ),
    )
    readback_text = (
        "DPDP Act 2023 ke antargat yeh call service estimate confirmation hetu record ki ja rahi hai. "
        "फ्रंट ब्रेक पैड पार्ट: चार सौ पचास रुपये, लेबर: दो सौ रुपये. कुल छह सौ पचास रुपये. "
        "डिलीवरी मंगलवार शाम तक। Agar aapko yeh manzoor hai, toh boliye: 'Haan, theek hai'. Kuch galat ho toh bataiye."
    )
    logs2 = (
        TranscriptLog(
            role="mechanic",
            mode="intake",
            text="फ्रंट ब्रेक पैड पार्ट साढ़े चार सौ रुपये, लेबर दो सौ रुपये, मंगलवार शाम तक।",
            recorded_at_utc=now,
            audio_sha256=wav_hash,
        ),
        TranscriptLog(
            role="system",
            mode="timbre_readback",
            text=readback_text,
            recorded_at_utc=now,
        ),
        TranscriptLog(
            role="system",
            mode="call_channel",
            text="phone",
            recorded_at_utc=now,
        ),
        TranscriptLog(
            role="customer",
            mode="reply",
            text="हाँ, ठीक है",
            recorded_at_utc=now,
            audio_sha256=hashlib.sha256(b"CUSTOMER_HAAN_THEEK_HAI").hexdigest(),
        ),
    )
    store._items[s2.id] = replace(
        s2,
        card=c2,
        status="confirmed",
        revision=3,
        readback_revision=2,
        confirmed_at_utc=now,
        dpdp_consent_granted=True,
        dpdp_consent_at_utc=now,
        dpdp_consent_sha256=hashlib.sha256(b"DPDP_CONSENT_GRANTED_2026-11-10").hexdigest(),
        logs=logs2,
    )

    # Save audio files to var/sessions so audio elements find them
    base_dir = Path("var/sessions").resolve()
    for sid in (s1.id, s2.id):
        s_dir = base_dir / sid
        s_dir.mkdir(parents=True, exist_ok=True)
        (s_dir / "0.wav").write_bytes(wav_bytes)
        (s_dir / "1.wav").write_bytes(wav_bytes)
        (s_dir / "2.wav").write_bytes(wav_bytes)
        (s_dir / "reply.wav").write_bytes(wav_bytes)

    return s1.id, s2.id


def main():
    store = SessionStore()
    s1_id, s2_id = setup_sessions(store)

    settings = Settings(
        api_key="gnani_dummy_key_not_called",
        mock=False,
    )
    services = AppServices(
        settings=settings,
        store=store,
        workflow=None,  # Not calling external APIs
    )
    app = create_app(services)

    config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(1.5)

    base = f"http://127.0.0.1:{PORT}"
    print(f"Server started on {base}")

    with sync_playwright() as pw:
        # Launch Chromium with device_scale_factor=2 for ultra-crisp retina screenshots
        browser = pw.chromium.launch()

        # -------------------------------------------------------------
        # 1. workshop-flagged-360.png (Mechanic view with 2 items to check)
        # -------------------------------------------------------------
        print("Capturing workshop-flagged-360.png...")
        ctx_mobile = browser.new_context(
            viewport={"width": 360, "height": 800},
            device_scale_factor=2,
            locale="hi-IN",
        )
        p = ctx_mobile.new_page()
        p.goto(f"{base}/workshop?session_id={s1_id}")
        p.wait_for_selector("#slip")
        # Ensure height fits full slip cleanly so dock sits at bottom
        h = p.evaluate("document.documentElement.scrollHeight")
        p.set_viewport_size({"width": 360, "height": max(800, int(h) + 30)})
        p.wait_for_timeout(400)
        p.screenshot(path=str(OUT / "workshop-flagged-360.png"))
        ctx_mobile.close()

        # -------------------------------------------------------------
        # 2. customer-call-360.png (Customer review call)
        # -------------------------------------------------------------
        print("Capturing customer-call-360.png...")
        # Temporarily set s2 to awaiting_reply
        store._items[s2_id] = replace(store._items[s2_id], status="awaiting_reply")
        ctx_mobile = browser.new_context(
            viewport={"width": 360, "height": 800},
            device_scale_factor=2,
            locale="hi-IN",
        )
        p = ctx_mobile.new_page()
        p.goto(f"{base}/customer/{s2_id}")
        p.wait_for_selector("#audio-panel")
        # Ensure caption text has nice progress highlight
        p.evaluate("""() => {
            const el = document.getElementById('readback-caption');
            if (el) {
                const words = el.textContent.split(' ');
                const half = Math.floor(words.length * 0.45);
                el.innerHTML = '<span class="said">' + words.slice(0, half).join(' ') + '</span> ' + words.slice(half).join(' ');
            }
        }""")
        h = p.evaluate("document.documentElement.scrollHeight")
        p.set_viewport_size({"width": 360, "height": max(800, int(h) + 30)})
        p.wait_for_timeout(400)
        p.screenshot(path=str(OUT / "customer-call-360.png"))
        ctx_mobile.close()

        # Restore s2 to confirmed
        store._items[s2_id] = replace(store._items[s2_id], status="confirmed")

        # -------------------------------------------------------------
        # 3. customer-sealed-360.png (Customer confirmed receipt)
        # -------------------------------------------------------------
        print("Capturing customer-sealed-360.png...")
        ctx_mobile = browser.new_context(
            viewport={"width": 360, "height": 800},
            device_scale_factor=2,
            locale="hi-IN",
        )
        p = ctx_mobile.new_page()
        p.goto(f"{base}/customer/{s2_id}")
        p.wait_for_selector("#confirmed-banner")
        # Hide any transient toast
        p.evaluate("() => { const t = document.getElementById('toast'); if (t) t.hidden = true; }")
        h = p.evaluate("document.documentElement.scrollHeight")
        p.set_viewport_size({"width": 360, "height": max(800, int(h) + 30)})
        p.wait_for_timeout(400)
        p.screenshot(path=str(OUT / "customer-sealed-360.png"))
        ctx_mobile.close()

        # -------------------------------------------------------------
        # 4. verify-360.png (Public verification & audio replay)
        # -------------------------------------------------------------
        print("Capturing verify-360.png...")
        ctx_mobile = browser.new_context(
            viewport={"width": 360, "height": 800},
            device_scale_factor=2,
            locale="hi-IN",
        )
        p = ctx_mobile.new_page()
        p.goto(f"{base}/verify/{s2_id}")
        p.wait_for_selector("#verify-verdict")
        # Expand the technical evidence panel so judges can see the cryptographic proof
        p.evaluate("() => { const el = document.getElementById('dpdp-compliance-panel'); if (el) el.open = true; }")
        h = p.evaluate("document.documentElement.scrollHeight")
        p.set_viewport_size({"width": 360, "height": max(800, int(h) + 30)})
        p.wait_for_timeout(400)
        p.screenshot(path=str(OUT / "verify-360.png"))
        ctx_mobile.close()

        # -------------------------------------------------------------
        # 5. stage-sealed-1440.png (Desktop Stage view with both phones)
        # -------------------------------------------------------------
        print("Capturing stage-sealed-1440.png...")
        ctx_desktop = browser.new_context(
            viewport={"width": 1440, "height": 920},
            device_scale_factor=2,
            locale="hi-IN",
        )
        p = ctx_desktop.new_page()
        p.goto(f"{base}/stage?session_id={s2_id}")
        p.wait_for_selector("#stage-workshop")
        p.wait_for_selector("#stage-customer")
        # Wait for iframes to render
        p.wait_for_timeout(2500)
        # In the workshop iframe, scroll smoothly down so the slip and stamp are visible
        p.evaluate("""() => {
            const wDoc = document.getElementById('stage-workshop')?.contentDocument;
            const wWin = document.getElementById('stage-workshop')?.contentWindow;
            const cDoc = document.getElementById('stage-customer')?.contentDocument;
            if (wDoc && wDoc.getElementById('toast')) wDoc.getElementById('toast').hidden = true;
            if (cDoc && cDoc.getElementById('toast')) cDoc.getElementById('toast').hidden = true;
            if (wWin) wWin.scrollTo({ top: 210, behavior: 'instant' });
        }""")
        p.wait_for_timeout(500)
        p.screenshot(path=str(OUT / "stage-sealed-1440.png"))
        ctx_desktop.close()

        browser.close()

    print("All 5 production screenshots successfully generated in docs/ui/!")


if __name__ == "__main__":
    main()
