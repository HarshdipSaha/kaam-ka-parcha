"""Live captions: relay browser PCM to Gnani's realtime STT socket and hand the transcripts straight back.

Display only. Nothing here reads or writes a session card, so a caption can never become an amount: the money path
still decides every amount from the two REST Prisma passes of the finished recording.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
import json
from typing import Any

import websockets

from parcha.gnani_ws import WS_URL, silence_frames, telephony_headers

__all__ = ["FRAME_BYTES", "relay_captions"]

FRAME_BYTES = 1024            # Gnani wants exactly 1024-byte PCM frames (512 samples at 8 kHz)
BYTES_PER_SECOND = 8000 * 2


async def relay_captions(
    audio_in: AsyncIterator[bytes],
    emit: Callable[[dict], Awaitable[None]],
    *,
    api_key: str,
    connect: Callable[..., Any] = websockets.connect,
    ws_url: str = WS_URL,
    max_seconds: float = 60.0,
    flush_seconds: float = 1.5,
    timeout_s: float = 10.0,
    partials: bool = True,
) -> None:
    """Stream 8 kHz mono s16le PCM chunks from `audio_in`, emit caption dicts: {"type": "caption", "text", "final"}.

    Ends when `audio_in` ends or `max_seconds` of audio has been sent; trailing silence flushes the last segment.
    Upstream detail is never forwarded: an upstream error becomes a generic {"type": "error"} event.
    """
    headers = telephony_headers(api_key)
    if partials:
        headers["x-partials"] = "true"
    async with connect(ws_url, additional_headers=headers, open_timeout=timeout_s) as socket:
        async def receive() -> None:
            async for raw in socket:
                try:
                    message = json.loads(raw)
                except (TypeError, ValueError):
                    continue
                kind = message.get("type")
                if kind in ("transcript", "final_transcript", "partial_transcript"):
                    text = str(message.get("text", "")).strip()
                    if text:
                        await emit({"type": "caption", "text": text, "final": kind != "partial_transcript"})
                elif kind == "error":
                    await emit({"type": "error"})

        receiver = asyncio.create_task(receive())
        try:
            buffer = b""
            sent_bytes = 0
            limit = int(max_seconds * BYTES_PER_SECOND)
            async for chunk in audio_in:
                buffer += chunk
                while len(buffer) >= FRAME_BYTES and sent_bytes < limit:
                    await socket.send(buffer[:FRAME_BYTES])
                    buffer = buffer[FRAME_BYTES:]
                    sent_bytes += FRAME_BYTES
                if sent_bytes >= limit:
                    break
            if buffer and sent_bytes < limit:
                await socket.send(buffer.ljust(FRAME_BYTES, b"\x00"))
            for frame in silence_frames():
                await socket.send(frame)
            try:
                await asyncio.wait_for(asyncio.shield(receiver), timeout=flush_seconds)
            except asyncio.TimeoutError:
                pass
        finally:
            receiver.cancel()
            try:
                await receiver
            except (asyncio.CancelledError, websockets.ConnectionClosed):
                pass
