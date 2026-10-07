"""A real customer phone call via Twilio Programmable Voice, as plain TwiML (no Twilio SDK dependency).

Call flow:
  workshop clicks "Call customer" -> POST /sessions/{id}/telephony/call places an outbound call
  Twilio connects the call -> POST /telephony/twilio/voice -> <Play> the read-back, then <Record> the reply
  Twilio posts the recording -> POST /telephony/twilio/recording -> same reply-classification workflow as the
  browser leg, then <Say> the outcome and hang up.

This is an additional leg, not a replacement: the in-browser simulated line stays available, and the two never
mix mid-session (a session reaches whichever leg answers first). A real call is real telephone audio, reported
as such — no simulated-line disclosure applies to it.

Twilio signs every webhook request (`X-Twilio-Signature`): HMAC-SHA1 over the exact request URL with every POST
parameter's name and value appended, sorted by name, keyed by the account's Auth Token, base64-encoded.
https://www.twilio.com/docs/usage/security#validating-requests
"""
from __future__ import annotations

import base64
import hashlib
import hmac
from xml.sax.saxutils import escape

import httpx

TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"


class TwilioError(RuntimeError):
    pass


def twiml(body: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>'


def say(text: str, *, language: str = "en-IN") -> str:
    return f'<Say language="{escape(language)}">{escape(text)}</Say>'


def play(url: str) -> str:
    return f"<Play>{escape(url)}</Play>"


def record(action_url: str, *, max_length: int = 20, timeout: int = 4) -> str:
    """A beep, then record up to `max_length` seconds, ending on `timeout` seconds of silence."""
    return (
        f'<Record action="{escape(action_url)}" method="POST" maxLength="{max_length}" '
        f'timeout="{timeout}" playBeep="true" trim="trim-silence"/>'
    )


def hangup() -> str:
    return "<Hangup/>"


def signature_valid(auth_token: str, url: str, params: dict[str, str], signature: str | None) -> bool:
    """Twilio's documented request-validation algorithm. A missing token or signature never validates."""
    if not auth_token or not signature:
        return False
    base = url + "".join(f"{k}{v}" for k, v in sorted(params.items()))
    expected = base64.b64encode(hmac.new(auth_token.encode(), base.encode(), hashlib.sha1).digest()).decode()
    return hmac.compare_digest(expected, signature)


def place_call(
    *,
    account_sid: str,
    auth_token: str,
    to: str,
    from_: str,
    voice_url: str,
    status_callback: str | None = None,
    http: httpx.Client | None = None,
) -> str:
    """Start an outbound call; Twilio fetches `voice_url` (TwiML) once it connects. Returns the call SID."""
    http = http or httpx.Client(timeout=15)
    data = {"To": to, "From": from_, "Url": voice_url, "Method": "POST"}
    if status_callback:
        data["StatusCallback"] = status_callback
        data["StatusCallbackMethod"] = "POST"
    resp = http.post(
        f"{TWILIO_API_BASE}/Accounts/{account_sid}/Calls.json",
        data=data,
        auth=(account_sid, auth_token),
    )
    if resp.status_code >= 400:
        raise TwilioError(f"Twilio call request failed: HTTP {resp.status_code}: {resp.text}")
    return resp.json()["sid"]


def send_sms(
    *,
    account_sid: str,
    auth_token: str,
    to: str,
    from_: str,
    body: str,
    http: httpx.Client | None = None,
) -> str:
    """Send a one-off SMS. Returns the message SID. Trial accounts: verified numbers only, and the
    message carries Twilio's own "Sent from a Twilio trial account" prefix."""
    http = http or httpx.Client(timeout=15)
    resp = http.post(
        f"{TWILIO_API_BASE}/Accounts/{account_sid}/Messages.json",
        data={"To": to, "From": from_, "Body": body},
        auth=(account_sid, auth_token),
    )
    if resp.status_code >= 400:
        raise TwilioError(f"Twilio SMS request failed: HTTP {resp.status_code}: {resp.text}")
    return resp.json()["sid"]


def download_recording(
    *, account_sid: str, auth_token: str, recording_url: str, http: httpx.Client | None = None
) -> bytes:
    """Fetch a completed recording as WAV. `recording_url` is the `RecordingUrl` Twilio posts (no extension)."""
    http = http or httpx.Client(timeout=30)
    resp = http.get(f"{recording_url}.wav", auth=(account_sid, auth_token))
    if resp.status_code >= 400:
        raise TwilioError(f"Twilio recording download failed: HTTP {resp.status_code}")
    return resp.content
