r"""Capture README screenshots from a LIVE run: real Gnani Prisma, Timbre and extractor, driven by spoken audio.

The speech is synthetic (Timbre voices play into Chromium's fake microphone); the recognition, extraction and
read-back are real service output. No real customer data is used. Spends a few hundred credits.

    .\.venv\Scripts\python.exe scripts/capture_live_screens.py --live
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys
import time

import httpx

from parcha.audio import mulaw_to_wav
from parcha.config import Settings
from parcha.gnani import TimbreClient

WORK = Path("var/live_capture")
OUT = Path("docs/ui")
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"
ESTIMATE = "फ्रंट ब्रेक पैड, पार्ट साढ़े चार सौ रुपये, लेबर दो सौ रुपये, सोमवार शाम तक"
SAY = {
    "estimate": ("Roopesh", ESTIMATE),
    "part": ("Roopesh", "साढ़े चार सौ रुपये"),
    "labour": ("Roopesh", "दो सौ रुपये"),
    "reply": ("Vikrant", "हाँ, ठीक है"),
}
PART, LABOUR = "items.part-1.amount_paise", "items.labour-1.amount_paise"
MEDIA = [
    "--use-fake-ui-for-media-stream",
    "--use-fake-device-for-media-stream",
    "--autoplay-policy=no-user-gesture-required",
]
PHONE = {"width": 360, "height": 800}


def render_audio(settings: Settings) -> dict[str, tuple[Path, float]]:
    """Timbre -> 48 kHz mono WAV with a lead-in and a tail, so a recording started at any moment hears the words."""
    WORK.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, (voice, text) in SAY.items():
        client = TimbreClient(settings.api_key, voice=voice, base_url=settings.gnani_base_url)
        raw = WORK / f"{name}_raw.wav"
        raw.write_bytes(mulaw_to_wav(client.synthesize(text)))
        final = WORK / f"{name}.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", "adelay=700|700,apad=pad_dur=2",
             "-ar", "48000", "-ac", "1", str(final)],
            check=True,
        )
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(final)],
            capture_output=True, text=True, check=True,
        )
        out[name] = (final, float(probe.stdout))
    return out


def start_server() -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "parcha.app:app", "--port", str(PORT), "--workers", "1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        try:
            if httpx.get(f"{BASE}/health", timeout=2).status_code == 200:
                return proc
        except httpx.HTTPError:
            time.sleep(0.5)
    proc.kill()
    raise RuntimeError("server did not start")


def settle(http: httpx.Client, sid: str, revision: int, audio) -> int:
    """Each amount needs two agreeing recordings; say it again if the first was only a candidate."""
    for field, name in ((PART, "part"), (LABOUR, "labour")):
        wav = audio[name][0]
        for _ in range(3):
            res = http.post(
                f"/sessions/{sid}/reask/{field}", data={"expected_revision": revision},
                files={"audio": (wav.name, wav.read_bytes(), "audio/wav")},
            )
            res.raise_for_status()
            revision = res.json()["revision"]
            items = {i["id"]: i for i in res.json()["card"]["items"]}
            if items[field.split(".")[1]]["amount_paise"] is not None:
                break
    return revision


def with_mic(pw, wav: Path, viewport, actions) -> None:
    browser = pw.chromium.launch(args=[*MEDIA, f"--use-file-for-fake-audio-capture={wav.resolve()}"])
    page = browser.new_context(
        viewport=viewport, has_touch=True, locale="hi-IN", permissions=["microphone"]
    ).new_page()
    try:
        actions(page)
    finally:
        browser.close()


def main() -> int:
    from playwright.sync_api import expect, sync_playwright

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="make paid Prisma/Timbre/extractor calls")
    args = parser.parse_args()
    if not args.live:
        print("dry run: would render 4 short Timbre clips and run one live estimate -> read-back -> approval flow")
        return 0
    settings = Settings.load()
    settings.require_gnani()
    OUT.mkdir(parents=True, exist_ok=True)
    audio = render_audio(settings)
    hold = {name: seconds for name, (_, seconds) in audio.items()}
    server = start_server()
    try:
        with sync_playwright() as pw, httpx.Client(base_url=BASE, timeout=180) as http:
            state: dict = {}

            def mechanic(page):
                page.goto(f"{BASE}/workshop")
                page.locator("#record").click()
                page.locator("#stop").wait_for(state="visible")
                time.sleep(min(hold["estimate"], 8))
                page.locator("#stop").click()
                expect(page.locator("#slip")).to_be_visible(timeout=120000)
                page.wait_for_timeout(1500)
                state["sid"] = page.evaluate("window.getCurrentSession().id")
                state["rev"] = page.evaluate("window.getCurrentSession().revision")
                page.screenshot(path=str(OUT / "workshop-flagged-360.png"), full_page=True)

            with_mic(pw, audio["estimate"][0], PHONE, mechanic)
            sid = state["sid"]
            rev = settle(http, sid, state["rev"], audio)
            http.post(f"/sessions/{sid}/readback", data={"expected_revision": rev}).raise_for_status()

            browser = pw.chromium.launch(args=MEDIA)
            page = browser.new_context(
                viewport=PHONE, has_touch=True, locale="hi-IN", permissions=["microphone"]
            ).new_page()
            page.goto(f"{BASE}/customer/{sid}")
            page.wait_for_timeout(2000)
            page.screenshot(path=str(OUT / "customer-call-360.png"), full_page=True)
            browser.close()

            def customer(page):
                page.goto(f"{BASE}/customer/{sid}")
                page.locator("#dpdp-consent-checkbox").check()
                expect(page.locator("#customer-record")).to_be_enabled()
                page.locator("#customer-record").click()
                page.locator("#customer-stop").wait_for(state="visible")
                time.sleep(min(hold["reply"], 5))
                page.locator("#customer-stop").click()
                expect(page.locator("#confirmed-banner")).to_be_visible(timeout=120000)
                page.wait_for_timeout(1500)
                page.screenshot(path=str(OUT / "customer-sealed-360.png"), full_page=True)

            with_mic(pw, audio["reply"][0], PHONE, customer)

            browser = pw.chromium.launch(args=MEDIA)
            page = browser.new_context(viewport=PHONE, locale="hi-IN").new_page()
            page.goto(f"{BASE}/verify/{sid}")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / "verify-360.png"), full_page=True)

            # Stage: both phones side by side showing one sealed parcha, driven through the same live services.
            stage_sid = re.search(r'src="/customer/([A-Za-z0-9_-]+)"', httpx.get(f"{BASE}/stage").text).group(1)
            intake = http.post(
                f"/sessions/{stage_sid}/intake", data={"expected_revision": 0},
                files={"audio": ("estimate.wav", audio["estimate"][0].read_bytes(), "audio/wav")},
            )
            intake.raise_for_status()
            rev = settle(http, stage_sid, intake.json()["revision"], audio)
            http.post(f"/sessions/{stage_sid}/readback", data={"expected_revision": rev}).raise_for_status()
            http.post(
                f"/sessions/{stage_sid}/reply",
                data={"expected_revision": rev, "readback_revision": rev, "dpdp_consent": "true"},
                files={"audio": ("reply.wav", audio["reply"][0].read_bytes(), "audio/wav")},
            ).raise_for_status()
            page = browser.new_context(
                viewport={"width": 1440, "height": 900}, locale="hi-IN", permissions=["microphone"]
            ).new_page()
            page.goto(f"{BASE}/stage")
            page.evaluate(
                """(sid) => {
                    document.getElementById('stage-workshop').src = '/workshop?session_id=' + sid;
                    document.getElementById('stage-customer').src = '/customer/' + sid;
                }""",
                stage_sid,
            )
            page.wait_for_timeout(7000)
            page.screenshot(path=str(OUT / "stage-sealed-1440.png"), full_page=True)
            browser.close()
    finally:
        server.terminate()
    print(f"wrote screenshots to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
