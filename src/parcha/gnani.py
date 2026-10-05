import json
import re
from typing import Literal
import httpx

__all__ = ["GnaniError", "PrismaClient", "TimbreClient"]


class GnaniError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None):
        super().__init__(message)
        self.status = status


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
        data = {"language_code": "hi-IN", "format": mode}
        if words:
            data.update(
                bias_list=json.dumps(words, ensure_ascii=False),
                bias_score=str(score),
            )
        response = self.http.post(
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
    ) -> tuple[str, float]:
        transcript = self.transcribe(wav, mode=mode, bias=bias, score=score)
        return transcript, getattr(self, "last_confidence", 1.0)


class TimbreClient:
    def __init__(
        self,
        api_key: str,
        voice: str = "Nalini",
        http: httpx.Client | None = None,
        base_url: str = "https://api.vachana.ai",
    ):
        self.api_key, self.voice = api_key, voice
        self.http = http or httpx.Client(timeout=45)
        self.base_url = base_url.rstrip("/")

    def __repr__(self) -> str:
        return f"<TimbreClient voice={self.voice!r} base_url={self.base_url!r}>"

    def synthesize(self, text: str) -> bytes:
        if not text.strip():
            raise ValueError("TTS text is empty")
        body = {
            "text": text,
            "voice": self.voice,
            "model": "timbre-v2.5",
            "language": "hi-IN",
            "speed": 1.0,
            "audio_config": {
                "sample_rate": 8000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "pcm_mulaw",
                "container": "mulaw",
            },
        }
        response = self.http.post(
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
