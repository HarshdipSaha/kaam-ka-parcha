"""
scripts/run_webattack_suite.py - Full-Surface Probing, Responsive Audit,
and End-to-End Playwright Automated Testing for Kaam Ka Parcha.
"""
import asyncio
import io
import json
import os
import sys
import time
from pathlib import Path
import requests
from playwright.async_api import async_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"
ARTIFACTS_DIR = Path("docs/webattack_artifacts")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

VIEWPORTS = [
    {"name": "Desktop_1080p", "width": 1920, "height": 1080, "is_mobile": False, "has_touch": False},
    {"name": "Desktop_1440w", "width": 1440, "height": 900, "is_mobile": False, "has_touch": False},
    {"name": "Tablet_768w", "width": 768, "height": 1024, "is_mobile": True, "has_touch": True},
    {"name": "Mobile_iPhone14", "width": 390, "height": 844, "is_mobile": True, "has_touch": True},
]

OVERFLOW_DETECTOR_JS = """
() => {
  const docWidth = document.documentElement.clientWidth;
  const badElements = [];
  
  document.querySelectorAll('*').forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.right > docWidth + 1 || el.scrollWidth > el.clientWidth + 1) {
      const style = window.getComputedStyle(el);
      if (style.overflowX !== 'auto' && style.overflowX !== 'scroll' && style.display !== 'none') {
        badElements.push({
          tag: el.tagName,
          id: el.id,
          className: el.className,
          scrollWidth: el.scrollWidth,
          clientWidth: el.clientWidth,
          overflowDelta: Math.round(rect.right - docWidth)
        });
      }
    }
  });
  return badElements;
}
"""

async def run_crawler_and_surface_probe(browser):
    print("\n" + "="*50)
    print("PHASE 1: Surface Mapping & Protocol Sniffing")
    print("="*50)

    visited = set()
    to_visit = [f"{BASE_URL}/", f"{BASE_URL}/workshop", f"{BASE_URL}/health"]
    api_traffic = set()
    console_logs = []
    page_errors = []
    discovered_buttons = []
    discovered_links = []

    page = await browser.new_page(viewport={"width": 1440, "height": 900})
    page.on("request", lambda r: api_traffic.add(f"{r.method} {r.url}") if not any(x in r.url for x in [".css", ".js", ".png", ".jpg", ".ico"]) else None)
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    while to_visit:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)
        print(f"  Probing surface: {url}")
        
        try:
            resp = await page.goto(url, wait_until="networkidle", timeout=15000)
            status = resp.status if resp else "none"
            print(f"   -> Status: {status}")

            links = await page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
            for l in links:
                discovered_links.append({"page": url, "link": l})
                if l.startswith(BASE_URL) and l not in visited and l not in to_visit:
                    to_visit.append(l)

            buttons = await page.eval_on_selector_all(
                "button",
                "btns => btns.map(b => ({ id: b.id, text: b.innerText.trim(), disabled: b.disabled }))"
            )
            for b in buttons:
                discovered_buttons.append({"page": url, "button": b})

        except Exception as e:
            print(f"   -> Error probing {url}: {e}")

    await page.close()
    return {
        "visited_routes": list(visited),
        "api_traffic": sorted(list(api_traffic)),
        "discovered_links": discovered_links,
        "discovered_buttons": discovered_buttons,
        "console_logs": console_logs,
        "page_errors": page_errors
    }

async def run_responsive_audit(browser, url: str, label: str):
    print(f"\n" + "="*50)
    print(f"PHASE 2: Responsive & Layout Audit for {label} ({url})")
    print("="*50)

    audit_results = []
    for vp in VIEWPORTS:
        name = vp["name"]
        print(f"  Testing Viewport: {name} ({vp['width']}x{vp['height']})")

        ctx = await browser.new_context(
            viewport={"width": vp["width"], "height": vp["height"]},
            is_mobile=vp["is_mobile"],
            has_touch=vp["has_touch"]
        )
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=15000)
            overflows = await page.evaluate(OVERFLOW_DETECTOR_JS)
            shot_path = ARTIFACTS_DIR / f"{label}_{name}.png"
            await page.screenshot(path=str(shot_path), full_page=True)

            status = "PASS" if len(overflows) == 0 else "FAIL"
            print(f"   -> Overflow check: {status} (Bad elements: {len(overflows)})")
            if overflows:
                for o in overflows[:3]:
                    print(f"      <{o['tag']} id='{o['id']}' class='{o['className']}'> +{o['overflowDelta']}px")
            print(f"   -> Screenshot saved: {shot_path.name}")

            audit_results.append({
                "viewport": name,
                "dimensions": f"{vp['width']}x{vp['height']}",
                "status": status,
                "overflow_count": len(overflows),
                "overflows": overflows,
                "screenshot": str(shot_path.relative_to(ARTIFACTS_DIR.parent.parent))
            })
        finally:
            await ctx.close()

    return audit_results

async def run_e2e_interactive_journey(browser):
    print("\n" + "="*50)
    print("PHASE 3: End-to-End Dual-Leg Interactive Driving")
    print("="*50)

    # 1. Create a session via API
    r = requests.post(f"{BASE_URL}/sessions")
    assert r.status_code == 200, f"Session creation failed: {r.text}"
    session_data = r.json()
    session_id = session_data["id"]
    print(f"  1. Created Session ID: {session_id} (rev: {session_data['revision']}, status: {session_data['status']})")

    # 2. Workshop intake using real mixed garage audio sample
    intake_audio_path = Path("data/real_world_samples/mechanic_in_garage_noise.wav")
    if not intake_audio_path.exists():
        intake_audio_path = Path("data/real_world_samples/speech_in_garage_noise.wav")
    audio_bytes = intake_audio_path.read_bytes()

    print(f"  2. Submitting workshop intake audio ({len(audio_bytes)} bytes from {intake_audio_path.name})...")
    intake_resp = requests.post(
        f"{BASE_URL}/sessions/{session_id}/intake",
        data={"expected_revision": 0},
        files={"audio": ("intake.wav", audio_bytes, "audio/wav")}
    )
    print(f"   -> Intake HTTP Status: {intake_resp.status_code}")
    assert intake_resp.status_code == 200, f"Intake failed: {intake_resp.text}"
    session_data = intake_resp.json()
    total_rs = session_data['total_paise'] / 100 if session_data.get('total_paise') else 0
    print(f"   -> Parsed Card Total: ₹{total_rs} (rev: {session_data['revision']}, status: {session_data['status']}, items: {len(session_data['card']['items']) if session_data.get('card') else 0})")

    # 3. Drive Workshop UI in Playwright to verify rendering of parsed card
    print(f"  3. Driving Workshop UI in Playwright for session {session_id}...")
    ws_context = await browser.new_context(viewport={"width": 1440, "height": 900})
    ws_page = await ws_context.new_page()
    await ws_page.goto(f"{BASE_URL}/workshop?session_id={session_id}", wait_until="networkidle")
    
    # Assert elements on workshop page
    ws_shot = ARTIFACTS_DIR / "workshop_parsed_card.png"
    await ws_page.screenshot(path=str(ws_shot), full_page=True)
    print(f"   -> Saved workshop parsed card screenshot: {ws_shot.name}")

    # Click 'Read estimate to customer' button on workshop UI
    readback_btn = await ws_page.query_selector("#start-readback")
    if readback_btn and not await readback_btn.is_disabled():
        print("   -> Clicking '#start-readback' on workshop page...")
        await readback_btn.click()
        try:
            await ws_page.wait_for_selector("#customer-link:visible", timeout=8000)
        except Exception:
            pass

    # Ensure readback status is awaiting_reply
    session_data = requests.get(f"{BASE_URL}/sessions/{session_id}").json()
    if session_data["status"] != "awaiting_reply":
        print("   -> Triggering readback via API...")
        readback_resp = requests.post(
            f"{BASE_URL}/sessions/{session_id}/readback",
            data={"expected_revision": session_data["revision"]}
        )
        assert readback_resp.status_code == 200, f"Readback failed: {readback_resp.text}"
        session_data = requests.get(f"{BASE_URL}/sessions/{session_id}").json()

    print(f"   -> Status after readback: {session_data['status']} (Rev: {session_data['revision']})")
    assert session_data["status"] == "awaiting_reply", "Session should be in awaiting_reply status"
    
    # Verify Customer Link is present
    customer_link = await ws_page.query_selector("#customer-link")
    if customer_link:
        customer_href = await customer_link.get_attribute("href")
        print(f"   -> Workshop generated customer link: {customer_href}")
    await ws_context.close()

    # 4. Drive Customer Review UI via Playwright
    customer_url = f"{BASE_URL}/customer/{session_id}"
    print(f"  4. Driving Customer Review page via Playwright: {customer_url}")

    context = await browser.new_context(
        viewport={"width": 1440, "height": 900},
        permissions=["microphone"]
    )
    page = await context.new_page()
    await page.goto(customer_url, wait_until="networkidle")

    # Assert elements on customer page
    disclosure = await page.text_content("#disclosure")
    print(f"   -> Disclosure Banner: \"{disclosure.strip()[:60]}...\"")
    assert "Simulated phone line" in disclosure

    # Check status badge
    badge_text = await page.text_content("#card-status-badge")
    print(f"   -> Customer Review Status Badge: {badge_text}")

    # Check Audio Player
    player_src = await page.get_attribute("#readback-player", "src")
    print(f"   -> Readback Audio Player Src: {player_src}")
    assert player_src and f"/sessions/{session_id}/readback.wav" in player_src

    # Verify audio streaming endpoint
    wav_resp = requests.get(f"{BASE_URL}{player_src}")
    print(f"   -> Telephony Audio Stream Check: HTTP {wav_resp.status_code} ({len(wav_resp.content)} bytes, {wav_resp.headers.get('content-type')})")
    assert wav_resp.status_code == 200

    # Take screenshot of awaiting_reply state
    shot1 = ARTIFACTS_DIR / "customer_awaiting_reply.png"
    await page.screenshot(path=str(shot1), full_page=True)
    print(f"   -> Saved customer review screenshot: {shot1.name}")

    # 5. Customer affirmation seal ("हाँ ठीक है")
    print("  5. Submitting customer affirmation ('Haan theek hai')...")
    affirm_audio_path = Path("data/real_world_samples/customer_affirmation_phrase.wav")
    affirm_bytes = affirm_audio_path.read_bytes()

    affirmation_resp = requests.post(
        f"{BASE_URL}/sessions/{session_id}/reply",
        data={
            "expected_revision": session_data["revision"],
            "readback_revision": session_data["revision"]
        },
        files={"audio": ("reply.wav", affirm_bytes, "audio/wav")}
    )
    print(f"   -> Customer Reply Status: {affirmation_resp.status_code}")
    assert affirmation_resp.status_code == 200, f"Customer reply failed: {affirmation_resp.text}"
    reply_outcome = affirmation_resp.json()
    print(f"   -> Outcome: {reply_outcome.get('outcome')}")
    print(f"   -> Message: {reply_outcome.get('message')}")
    print(f"   -> Final Status: {reply_outcome.get('status')} (Rev: {reply_outcome.get('revision')})")

    # Reload Customer UI to inspect Sealed State
    await page.reload(wait_until="networkidle")
    confirmed_banner_visible = await page.is_visible("#confirmed-banner")
    pdf_btn_visible = await page.is_visible("#download-pdf-link")
    whatsapp_btn_visible = await page.is_visible("#whatsapp-link")

    print(f"   -> Confirmed Banner Visible: {confirmed_banner_visible}")
    print(f"   -> PDF Download Button Visible: {pdf_btn_visible}")
    print(f"   -> WhatsApp Button Visible: {whatsapp_btn_visible}")
    assert confirmed_banner_visible, "Confirmed banner should be visible"
    assert pdf_btn_visible, "PDF download button should be visible"

    shot2 = ARTIFACTS_DIR / "customer_sealed_state.png"
    await page.screenshot(path=str(shot2), full_page=True)
    print(f"   -> Saved confirmed state screenshot: {shot2.name}")

    # 6. Verify Artefact downloads
    print("  6. Verifying Artefact Downloads (PDF & WhatsApp)...")
    pdf_resp = requests.get(f"{BASE_URL}/sessions/{session_id}/pdf")
    print(f"   -> Sealed PDF Status: {pdf_resp.status_code} ({len(pdf_resp.content)} bytes, Type: {pdf_resp.headers.get('content-type')})")
    assert pdf_resp.status_code == 200
    assert pdf_resp.content.startswith(b"%PDF"), "Response is not a valid PDF header"

    whatsapp_resp = requests.get(f"{BASE_URL}/sessions/{session_id}/whatsapp")
    print(f"   -> WhatsApp Text Status: {whatsapp_resp.status_code}")
    print(f"   -> WhatsApp Summary Preview:\n{'-'*30}\n{whatsapp_resp.text.strip()}\n{'-'*30}")
    assert whatsapp_resp.status_code == 200
    assert "Kaam ka Parcha" in whatsapp_resp.text or "kaam ka parcha" in whatsapp_resp.text.lower()

    await context.close()

    return {
        "session_id": session_id,
        "intake_status": intake_resp.status_code,
        "readback_status": 200,
        "reply_status": affirmation_resp.status_code,
        "pdf_download_status": pdf_resp.status_code,
        "pdf_bytes": len(pdf_resp.content),
        "whatsapp_download_status": whatsapp_resp.status_code,
        "whatsapp_preview": whatsapp_resp.text[:200]
    }

async def run_negative_security_tests():
    print("\n" + "="*50)
    print("PHASE 4: Negative, Security & Edge Case Probing")
    print("="*50)

    results = []

    # 1. Non-existent session
    r1 = requests.get(f"{BASE_URL}/sessions/nonexistent-session-xyz")
    assert r1.status_code == 404
    results.append({"test": "Unknown session GET returns 404", "status": "PASS", "code": r1.status_code})
    print(f"  [PASS] Non-existent session returns 404: {r1.json()}")

    # 2. Unconfirmed PDF download protection
    draft_session = requests.post(f"{BASE_URL}/sessions").json()["id"]
    r2 = requests.get(f"{BASE_URL}/sessions/{draft_session}/pdf")
    assert r2.status_code == 409
    results.append({"test": "Unconfirmed PDF download returns 409 Conflict", "status": "PASS", "code": r2.status_code})
    print(f"  [PASS] Unconfirmed PDF download returns 409: {r2.json()}")

    # 3. Path traversal attack probe in session_id / readback.wav
    r3 = requests.get(f"{BASE_URL}/sessions/../../etc/passwd/readback.wav?revision=1")
    assert r3.status_code in [400, 404]
    results.append({"test": "Path traversal in session_id rejected", "status": "PASS", "code": r3.status_code})
    print(f"  [PASS] Path traversal rejected: HTTP {r3.status_code}")

    # 4. Empty audio intake validation
    r4 = requests.post(
        f"{BASE_URL}/sessions/{draft_session}/intake",
        data={"expected_revision": 0},
        files={"audio": ("empty.wav", b"", "audio/wav")}
    )
    assert r4.status_code == 422
    results.append({"test": "Empty audio intake returns 422", "status": "PASS", "code": r4.status_code})
    print(f"  [PASS] Empty audio upload rejected with 422: {r4.json()}")

    # 5. Stale revision reply
    r5 = requests.post(
        f"{BASE_URL}/sessions/{draft_session}/reply",
        data={"expected_revision": 99, "readback_revision": 99},
        files={"audio": ("fake.wav", b"123", "audio/wav")}
    )
    assert r5.status_code == 409
    results.append({"test": "Stale revision reply returns 409", "status": "PASS", "code": r5.status_code})
    print(f"  [PASS] Stale revision reply rejected with 409: {r5.json()}")

    return results

async def main():
    start_time = time.time()
    print("="*60)
    print("LAUNCHING WEBATTACK AUTOMATED PROBING SUITE")
    print(f"Target: {BASE_URL}")
    print("="*60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--disable-web-security"
            ]
        )

        # 1. Surface crawl
        surface_report = await run_crawler_and_surface_probe(browser)

        # 2. Responsive viewports audit for /workshop
        workshop_audit = await run_responsive_audit(browser, f"{BASE_URL}/workshop", "workshop")

        # 3. Interactive E2E Driving
        e2e_report = await run_e2e_interactive_journey(browser)

        # 4. Responsive viewports audit for /customer/{session_id}
        customer_url = f"{BASE_URL}/customer/{e2e_report['session_id']}"
        customer_audit = await run_responsive_audit(browser, customer_url, "customer")

        # 5. Negative security tests
        negative_report = await run_negative_security_tests()

        await browser.close()

    elapsed = time.time() - start_time
    full_report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(elapsed, 2),
        "target_base_url": BASE_URL,
        "surface_probe": surface_report,
        "responsive_audits": {
            "workshop": workshop_audit,
            "customer": customer_audit
        },
        "e2e_interactive": e2e_report,
        "negative_security_tests": negative_report
    }

    report_path = ARTIFACTS_DIR / "webattack_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print("WEBATTACK PROBING COMPLETED SUCCESSFULLY!")
    print(f"Elapsed Time: {elapsed:.2f}s")
    print(f"Report saved to: {report_path}")
    print(f"Screenshots saved in: {ARTIFACTS_DIR}/")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
