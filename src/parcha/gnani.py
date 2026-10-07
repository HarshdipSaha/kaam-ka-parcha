import json
import re
import time
from typing import Literal
import httpx

__all__ = ["GnaniError", "PrismaClient", "TimbreClient", "chunk_for_tts"]

# Another entrant's live probe (boli-zero, 2026-10-05) saw Timbre fail somewhere between ~1,500 and ~2,800 characters.
# Not verified here; long read-backs are split below a conservative limit so a many-item card cannot crash the demo.
TTS_MAX_CHARS = 1000
_SENTENCE_END = re.compile(r"(?<=[.!?।])\s+")


def chunk_for_tts(text: str, limit: int = TTS_MAX_CHARS) -> list[str]:
    """Split text into pieces of at most `limit` characters, preferring sentence, then comma, then word boundaries."""
    text = text.strip()
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current = ""
    for piece in _pieces(text, limit):
        if current and len(current) + 1 + len(piece) > limit:
            chunks.append(current)
            current = piece
        else:
            current = f"{current} {piece}".strip()
    if current:
        chunks.append(current)
    return chunks


def _pieces(text: str, limit: int) -> list[str]:
    """Sentence-sized pieces, each broken further (commas, then words) if still longer than `limit`."""
    out: list[str] = []
    for sentence in _SENTENCE_END.split(text):
        if len(sentence) <= limit:
            out.append(sentence)
            continue
        for part in re.split(r"(?<=,)\s+", sentence):
            if len(part) <= limit:
                out.append(part)
                continue
            line = ""
            for word in part.split():
                if line and len(line) + 1 + len(word) > limit:
                    out.append(line)
                    line = word
                else:
                    line = f"{line} {word}".strip()
            if line:
                out.append(line)
    return out


class GnaniError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None):
        super().__init__(message)
        self.status = status


RETRY_STATUSES = frozenset({429, 503})
RETRY_DELAYS = (1.0, 2.5)  # seconds before retry 1 and 2; Gnani rate-limits short bursts


def _post(http: httpx.Client, url: str, **kwargs) -> httpx.Response:
    """POST, retrying a rate-limit (429/503) twice with a short pause before giving up."""
    response = http.post(url, **kwargs)
    for delay in RETRY_DELAYS:
        if response.status_code not in RETRY_STATUSES:
            break
        time.sleep(delay)
        response = http.post(url, **kwargs)
    return response


def _check_response(response: httpx.Response) -> None:
    if response.status_code != 200:
        raise GnaniError(f"Gnani request failed: HTTP {response.status_code}", status=response.status_code)


class PrismaClient:
    def __init__(
        self,
        api_key: str,
        http: httpx.Client | None = None,
        base_url: str = "https://api.vachana.ai",
    ):
        self.api_key = api_key
        self.http = http or httpx.Client(timeout=45)
        self.base_url = base_url.rstrip("/")

    def __repr__(self) -> str:
        return f"<PrismaClient base_url={self.base_url!r}>"

    def transcribe(
        self,
        wav: bytes,
        *,
        mode: Literal["transcribe", "verbatim"],
        bias: list[str] | None = None,
        score: float = 1.0,
        language_code: str = "hi-IN",
    ) -> str:
        words = bias or []
        if words and mode != "verbatim":
            raise ValueError("bias_list requires verbatim mode")
        if len(words) > 100 or any(
            not re.fullmatch(r"[^\W\d_]+", word, re.UNICODE) for word in words
        ):
            raise ValueError("bias_list must contain at most 100 single words")
        if score not in {0.0, 0.5, 1.0, 1.5, 2.0}:
            raise ValueError("unsupported bias_score")
        data = {"language_code": language_code, "format": mode}
        if words:
            data.update(
                bias_list=json.dumps(words, ensure_ascii=False),
                bias_score=str(score),
            )
        response = _post(
            self.http,
            f"{self.base_url}/stt/v3",
            headers={"X-API-Key-ID": self.api_key},
            data=data,
            files={"audio_file": ("clip.wav", wav, "audio/wav")},
        )
        _check_response(response)
        payload = response.json()
        if payload.get("success") is not True or not isinstance(
            payload.get("transcript"), str
        ):
            raise GnaniError("Gnani STT response lacked a transcript")
        raw_conf = payload.get("confidence")
        self.last_confidence = float(raw_conf) if raw_conf is not None else 1.0
        return payload["transcript"].strip()

    def transcribe_detailed(
        self,
        wav: bytes,
        *,
        mode: Literal["transcribe", "verbatim"] = "transcribe",
        bias: list[str] | None = None,
        score: float = 1.0,
        language_code: str = "hi-IN",
    ) -> tuple[str, float]:
        transcript = self.transcribe(wav, mode=mode, bias=bias, score=score, language_code=language_code)
        return transcript, getattr(self, "last_confidence", 1.0)


class TimbreClient:
    def __init__(
        self,
        api_key: str,
        voice: str = "Vikrant",
        http: httpx.Client | None = None,
        base_url: str = "https://api.vachana.ai",
    ):
        self.api_key, self.voice = api_key, voice
        self.http = http or httpx.Client(timeout=45)
        self.base_url = base_url.rstrip("/")

    def __repr__(self) -> str:
        return f"<TimbreClient voice={self.voice!r} base_url={self.base_url!r}>"

    def synthesize(self, text: str, *, language: str = "hi-IN", voice: str | None = None) -> bytes:
        if not text.strip():
            raise ValueError("TTS text is empty")
        # Raw mu-law has no header, so the pieces' audio can simply be joined.
        return b"".join(self._synthesize_one(piece, language, voice) for piece in chunk_for_tts(text))

    def _synthesize_one(self, text: str, language: str, voice: str | None) -> bytes:
        body = {
            "text": text,
            "voice": voice or self.voice,
            "model": "timbre-v2.5",
            "language": language,
            "speed": 1.0,
            "audio_config": {
                "sample_rate": 8000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "pcm_mulaw",
                "container": "mulaw",
            },
        }
        response = _post(
            self.http,
            f"{self.base_url}/api/v1/tts/inference",
            headers={"X-API-Key-ID": self.api_key},
            json=body,
        )
        _check_response(response)
        if not response.content or response.headers.get(
            "content-type", ""
        ).startswith("application/json"):
            raise GnaniError("Gnani TTS response lacked raw audio")
        return response.content
