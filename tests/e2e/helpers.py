"""Helpers shared by the browser tests."""
from __future__ import annotations

import time
from pathlib import Path

import httpx

SCREENS = Path("var/e2e")


def speak(surface, start, stop, seconds: float = 0.8) -> None:
    """Tap the mic, let Chromium's fake microphone record, then tap stop. surface: Page or FrameLocator."""
    start_loc = surface.locator(start) if isinstance(start, str) else start
    stop_loc = surface.locator(stop) if isinstance(stop, str) else stop
    start_loc.click()
    stop_loc.wait_for(state="visible")
    time.sleep(seconds)
    stop_loc.click()


def new_parcha(base_url: str, *, read_back: bool = True) -> dict:
    """Create a session through the public API, optionally up to awaiting_reply."""
    with httpx.Client(base_url=base_url, timeout=30) as http:
        sid = http.post("/sessions").json()["id"]
        body = http.post(f"/sessions/{sid}/intake", data={"expected_revision": 0},
                         files={"audio": ("estimate.wav", b"audio", "audio/wav")})
        body.raise_for_status()
        if read_back:
            http.post(f"/sessions/{sid}/readback", data={"expected_revision": body.json()["revision"]}).raise_for_status()
        return http.get(f"/sessions/{sid}").json()


def reply_by_api(base_url: str, session: dict) -> dict:
    """Post one customer reply; the words come from StagePrisma.say()."""
    with httpx.Client(base_url=base_url, timeout=30) as http:
        res = http.post(
            f"/sessions/{session['id']}/reply",
            data={"expected_revision": session["revision"], "readback_revision": session["readback_revision"],
                  "dpdp_consent": "true"},
            files={"audio": ("reply.wav", b"reply", "audio/wav")},
        )
        res.raise_for_status()
        return res.json()
