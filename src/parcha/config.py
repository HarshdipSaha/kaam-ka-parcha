from dataclasses import dataclass, field
from os import environ
from typing import Mapping
from dotenv import dotenv_values


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default="", repr=False)
    extractor_base_url: str = ""
    extractor_api_key: str = field(default="", repr=False)
    extractor_model: str = ""
    extractor_provider: str = "external"
    tts_voice: str = "Nalini"
    gnani_base_url: str = "https://api.vachana.ai"
    reply_transport: str = "rest"

    @classmethod
    def from_mapping(cls, values: Mapping[str, str | None]) -> "Settings":
        base_url = (values.get("EXTRACTOR_BASE_URL") or "").strip()
        model = (values.get("EXTRACTOR_MODEL") or "").strip()
        key = (values.get("EXTRACTOR_API_KEY") or values.get("GROQ_API_KEY") or "").strip()
        if not base_url and ("GROQ_API_KEY" in values or key):
            base_url = "https://api.groq.com/openai/v1"
            if not model:
                model = "llama-3.3-70b-versatile"
        return cls(
            api_key=(values.get("API_KEY") or "").strip(),
            extractor_base_url=base_url,
            extractor_api_key=key,
            extractor_model=model,
            extractor_provider=(values.get("EXTRACTOR_PROVIDER") or "").strip() or "external",
            tts_voice=(values.get("TTS_VOICE") or "").strip() or "Nalini",
            gnani_base_url=(values.get("GNANI_BASE_URL") or "").strip() or "https://api.vachana.ai",
            reply_transport=(values.get("REPLY_TRANSPORT") or "").strip() or "rest",
        )

    @classmethod
    def load(cls) -> "Settings":
        return cls.from_mapping({**dotenv_values(".env"), **environ})

    def require_gnani(self) -> None:
        if not self.api_key or self.api_key == "replace_me":
            raise ValueError("API_KEY is required for live Gnani calls")

    def require_extractor(self) -> None:
        if not self.extractor_base_url or not self.extractor_model:
            raise ValueError("An extractor endpoint and model are required")
