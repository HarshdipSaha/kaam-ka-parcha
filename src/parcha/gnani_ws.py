import asyncio
import io
import json
import wave
import websockets

from .gnani import KeyPool

__all__ = [
    "WS_URL",
    "pcm_frames",
    "silence_frames",
    "telephony_headers",
    "transcribe_telephony",
]

WS_URL = "wss://api.vachana.ai/stt/v3/stream"


def pcm_frames(wav_bytes: bytes) -> list[bytes]:
    with wave.open(io.BytesIO(wav_bytes), "rb") as source:
        if (source.getframerate(), source.getnchannels(), source.getsampwidth()) != (8000, 1, 2):
            raise ValueError("WS input must be mono 8 kHz signed-16-bit WAV")
        pcm = source.readframes(source.getnframes())
    if not pcm:
        raise ValueError("empty WS input")
    chunks = [pcm[i:i + 1024] for i in range(0, len(pcm), 1024)]
    return [chunk.ljust(1024, b"\x00") for chunk in chunks]


def silence_frames(sample_rate: int = 8000, minimum_ms: int = 500) -> list[bytes]:
    frame_ms = 512 / sample_rate * 1000  # 64 ms for 512 samples
    count = int(-(-minimum_ms // frame_ms))  # ceiling
    return [b"\x00" * 1024 for _ in range(count)]


def telephony_headers(api_key: str) -> dict[str, str]:
    """`api_key` may be a comma-separated list; the WebSocket has no failover, so it uses the first usable key."""
    return {
        "x-api-key-id": KeyPool.from_value(api_key).current(),
        "lang_code": "hi-IN",
        "x-sample-rate": "8000",
        "x-vad-threshold": "0.7",
        "x-min-speech-ms": "200",
        "x-min-silence-ms": "500",
        "x-min-segment-ms": "100",
    }


async def transcribe_telephony(
    wav_bytes: bytes,
    api_key: str,
    timeout_s: float = 10.0,
    ws_url: str = WS_URL,
) -> tuple[str, list[dict]]:
    events: list[dict] = []
    async with websockets.connect(
        ws_url,
        additional_headers=telephony_headers(api_key),
        open_timeout=timeout_s,
    ) as socket:
        async def receive_final() -> str:
            while True:
                message = json.loads(await asyncio.wait_for(socket.recv(), timeout=timeout_s))
                events.append(message)
                if message.get("type") == "transcript":
                    return str(message.get("text", ""))
                if message.get("type") == "error":
                    raise RuntimeError("Gnani WS returned an error event")

        receiver = asyncio.create_task(receive_final())
        try:
            for frame in pcm_frames(wav_bytes) + silence_frames():
                await socket.send(frame)
                await asyncio.sleep(0.064)
            transcript = await asyncio.wait_for(receiver, timeout=timeout_s)
        finally:
            if not receiver.done():
                receiver.cancel()
        return transcript, events
