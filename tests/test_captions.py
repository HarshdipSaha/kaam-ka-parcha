import asyncio
from dataclasses import replace
import json

from fastapi.testclient import TestClient
import pytest
from starlette.websockets import WebSocketDisconnect

from parcha.app import AppServices, create_app
from parcha.captions import FRAME_BYTES, relay_captions

SILENCE = b"\x00" * FRAME_BYTES


class FakeGnaniSocket:
    """Stands in for the Gnani realtime socket: replies with scripted events once trailing silence arrives."""

    def __init__(self, events):
        self.events = events
        self.sent: list[bytes] = []
        self.headers = None
        self._queue: asyncio.Queue = asyncio.Queue()
        self._flushed = False

    def connect(self, url, additional_headers=None, open_timeout=None):
        self.headers = additional_headers
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def send(self, frame):
        self.sent.append(frame)
        if frame == SILENCE and not self._flushed:
            self._flushed = True
            for event in self.events:
                self._queue.put_nowait(json.dumps(event))
            self._queue.put_nowait(None)

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self._queue.get()
        if item is None:
            raise StopAsyncIteration
        return item


async def chunks(*parts):
    for part in parts:
        yield part


def run_relay(socket, *parts, **kwargs):
    events = []

    async def emit(event):
        events.append(event)

    asyncio.run(relay_captions(chunks(*parts), emit, api_key="k", connect=socket.connect, flush_seconds=0.5, **kwargs))
    return events


def test_odd_sized_chunks_become_exact_frames_then_silence_flushes():
    socket = FakeGnaniSocket([{"type": "transcript", "text": "front brake pad"}])
    events = run_relay(socket, b"\x01" * 700, b"\x02" * 1000, b"\x03" * 600)     # 2300 bytes
    audio = [f for f in socket.sent if f != SILENCE]
    assert all(len(f) == FRAME_BYTES for f in socket.sent)
    assert len(audio) == 3 and audio[2].endswith(b"\x00" * (FRAME_BYTES - 252))   # 2300 - 2048 = 252, zero-padded
    assert socket.sent[-1] == SILENCE
    assert events == [{"type": "caption", "text": "front brake pad", "final": True}]


def test_partials_are_marked_not_final_and_requested_only_when_enabled():
    socket = FakeGnaniSocket([{"type": "partial_transcript", "text": "front"}, {"type": "transcript", "text": "front brake"}])
    events = run_relay(socket, b"\x01" * 2048, partials=True)
    assert [(e["text"], e["final"]) for e in events] == [("front", False), ("front brake", True)]
    assert socket.headers["x-partials"] == "true"
    plain = FakeGnaniSocket([])
    run_relay(plain, b"\x01" * 1024)
    assert "x-partials" not in plain.headers


def test_audio_beyond_the_time_cap_is_not_sent():
    socket = FakeGnaniSocket([])
    run_relay(socket, b"\x01" * (16000 * 3), max_seconds=1.0)                      # 3 s offered, 1 s allowed
    assert len([f for f in socket.sent if f != SILENCE]) == 16          # 16 x 1,024 B just covers 1 s; the rest is dropped


def test_upstream_error_becomes_a_generic_event_without_detail():
    socket = FakeGnaniSocket([{"type": "error", "message": "key sk-secret rejected by https://private.example"}])
    events = run_relay(socket, b"\x01" * 1024)
    assert events == [{"type": "error"}]


# ---- HTTP/websocket surface --------------------------------------------------------------------------------

def client_with(fake_services: AppServices, socket: FakeGnaniSocket, **settings):
    services = AppServices(replace(fake_services.settings, **settings), fake_services.store, fake_services.workflow,
                           fake_services.timbre, caption_connect=socket.connect)
    return TestClient(create_app(services)), services


def test_captions_stream_to_the_browser_and_never_touch_the_session(fake_services):
    socket = FakeGnaniSocket([{"type": "transcript", "text": "brake pad paanch sau"}])
    client, services = client_with(fake_services, socket)
    sid = client.post("/sessions").json()["id"]
    before = client.get(f"/sessions/{sid}").json()
    with client.websocket_connect(f"/sessions/{sid}/captions") as ws:
        ws.send_bytes(b"\x01" * 3000)
        ws.send_text("stop")
        assert ws.receive_json() == {"type": "caption", "text": "brake pad paanch sau", "final": True}
    assert client.get(f"/sessions/{sid}").json() == before            # no card, no amount, same revision
    assert before["card"] is None and before["revision"] == 0


def test_caption_text_cannot_set_an_amount(fake_services):
    socket = FakeGnaniSocket([{"type": "transcript", "text": "front brake pad ₹450 labour ₹200"}])
    client, services = client_with(fake_services, socket)
    sid = client.post("/sessions").json()["id"]
    with client.websocket_connect(f"/sessions/{sid}/captions") as ws:
        ws.send_bytes(b"\x01" * 1024)
        ws.send_text("stop")
        ws.receive_json()
    session = services.store.get(sid)
    assert session.card is None and session.logs == ()


@pytest.mark.parametrize("settings, code", [({"demo_access_code": "open"}, 4401), ({"api_key": ""}, 4503)])
def test_captions_refuse_when_gated_or_unconfigured(fake_services, settings, code):
    client, _ = client_with(fake_services, FakeGnaniSocket([]), **settings)
    sid = fake_services.store.create().id
    with pytest.raises(WebSocketDisconnect) as info:
        with client.websocket_connect(f"/sessions/{sid}/captions"):
            pass
    assert info.value.code == code


def test_captions_for_an_unknown_session_close_cleanly(fake_services):
    client, _ = client_with(fake_services, FakeGnaniSocket([]))
    with pytest.raises(WebSocketDisconnect) as info:
        with client.websocket_connect("/sessions/nope/captions"):
            pass
    assert info.value.code == 4404


def test_caption_sockets_share_the_rate_limit(fake_services):
    client, _ = client_with(fake_services, FakeGnaniSocket([]), rate_limit_per_minute=2)
    sid = client.post("/sessions").json()["id"]                      # hit 1 of 2
    with client.websocket_connect(f"/sessions/{sid}/captions") as ws:  # hit 2: allowed
        ws.send_text("stop")
    with pytest.raises(WebSocketDisconnect) as info:                 # hit 3: refused
        with client.websocket_connect(f"/sessions/{sid}/captions"):
            pass
    assert info.value.code == 4429
