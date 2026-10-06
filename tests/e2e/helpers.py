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


SPOKEN_AMOUNTS = {"items.part-1.amount_paise": "चार सौ पचास", "items.labour-1.amount_paise": "दो सौ"}


def confirm_amounts_by_api(http, world, sid: str, revision: int) -> int:
    """Second, deliberate recording of each amount; returns the new revision."""
    for field, spoken in SPOKEN_AMOUNTS.items():
        world.prisma.say(spoken)
        res = http.post(f"/sessions/{sid}/reask/{field}", data={"expected_revision": revision},
                        files={"audio": ("amount.wav", b"amount", "audio/wav")})
        res.raise_for_status()
        revision = res.json()["revision"]
    world.prisma.heard = None
    return revision


def new_parcha(world, *, read_back: bool = True) -> dict:
    """Create a session through the public API, optionally up to awaiting_reply.

    A single intake recording leaves amounts unconfirmed (independent-confirmation gate), so each
    amount gets the deliberate second recording a mechanic would give before the read-back.
    """
    with httpx.Client(base_url=world.url, timeout=30) as http:
        sid = http.post("/sessions").json()["id"]
        body = http.post(f"/sessions/{sid}/intake", data={"expected_revision": 0},
                         files={"audio": ("estimate.wav", b"audio", "audio/wav")})
        body.raise_for_status()
        revision = body.json()["revision"]
        if read_back:
            revision = confirm_amounts_by_api(http, world, sid, revision)
            http.post(f"/sessions/{sid}/readback", data={"expected_revision": revision}).raise_for_status()
        return http.get(f"/sessions/{sid}").json()


def confirm_amounts_in_ui(page, world) -> None:
    """Give each flagged amount its second recording through the row's own button."""
    import re
    from playwright.sync_api import expect

    for item, spoken, shown in (("part-1", SPOKEN_AMOUNTS["items.part-1.amount_paise"], "₹450"),
                                ("labour-1", SPOKEN_AMOUNTS["items.labour-1.amount_paise"], "₹200")):
        row = page.locator(f'[data-item="{item}"]')
        world.prisma.say(spoken)
        speak(page, row.get_by_role("button", name=re.compile("दोबारा बोलें")), "#stop")
        expect(row.locator(".row__amount")).to_have_text(shown, timeout=15000)
    world.prisma.heard = None
    expect(page.locator("#total-cell")).to_have_text("₹650", timeout=15000)


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
