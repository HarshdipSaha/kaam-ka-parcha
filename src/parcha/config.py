from dataclasses import dataclass, field
from os import environ
from pathlib import Path
from typing import Mapping
from dotenv import dotenv_values

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PACKAGE_ASSET_PATH = PACKAGE_ROOT / "assets" / "car_engine_idle_16k.wav"
PROJECT_DATA_PATH = PROJECT_ROOT / "data" / "real_world_samples" / "car_engine_idle_16k.wav"

DEFAULT_TELEPHONY_NOISE_PATH = PACKAGE_ASSET_PATH if PACKAGE_ASSET_PATH.exists() else PROJECT_DATA_PATH


def resolve_project_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    candidate_package = PACKAGE_ROOT / path
    if candidate_package.exists():
        return candidate_package
    return PROJECT_ROOT / path



def _int(raw: str | None, default: int) -> int:
    try:
        return max(0, int((raw or "").strip()))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default="", repr=False)
    extractor_base_url: str = ""
    extractor_api_key: str = field(default="", repr=False)
    extractor_model: str = ""
    extractor_provider: str = "evon"
    tts_voice: str = "Vikrant"
    gnani_base_url: str = "https://api.vachana.ai"
    reply_transport: str = "rest"
    use_automotive_bias: bool = True
    telephony_codec: str = "g711"
    telephony_target_snr_db: float = 5.0
    telephony_noise_path: Path = DEFAULT_TELEPHONY_NOISE_PATH
    # Public-demo guards (0 / empty = off, the local default); see src/parcha/guard.py.
    rate_limit_per_minute: int = 0
    sessions_per_ip_per_hour: int = 0
    max_total_sessions: int = 0
    max_upload_bytes: int = 8 * 1024 * 1024
    demo_access_code: str = field(default="", repr=False)
    trust_proxy: bool = False
    caption_partials: bool = False   # ask the realtime STT for interim transcripts (undocumented x-partials header)

    @classmethod
    def from_mapping(cls, values: Mapping[str, str | None]) -> "Settings":
        base_url = (values.get("EXTRACTOR_BASE_URL") or "").strip()
        model = (values.get("EXTRACTOR_MODEL") or "").strip()
        key = (values.get("EXTRACTOR_API_KEY") or "").strip()
        return cls(
            api_key=(values.get("API_KEY") or "").strip(),
            extractor_base_url=base_url,
            extractor_api_key=key,
            extractor_model=model,
            extractor_provider=(values.get("EXTRACTOR_PROVIDER") or "").strip() or "evon",
            tts_voice=(values.get("TTS_VOICE") or "").strip() or "Vikrant",
            gnani_base_url=(values.get("GNANI_BASE_URL") or "").strip() or "https://api.vachana.ai",
            reply_transport=(values.get("REPLY_TRANSPORT") or "").strip() or "rest",
            use_automotive_bias=(values.get("USE_AUTOMOTIVE_BIAS") or "true").strip().casefold() not in {"0", "false", "no", "off"},
            telephony_codec=(values.get("TELEPHONY_CODEC") or "").strip() or "g711",
            telephony_target_snr_db=float((values.get("TELEPHONY_TARGET_SNR_DB") or "5.0").strip()),
            rate_limit_per_minute=_int(values.get("RATE_LIMIT_PER_MINUTE"), 0),
            sessions_per_ip_per_hour=_int(values.get("SESSIONS_PER_IP_PER_HOUR"), 0),
            max_total_sessions=_int(values.get("MAX_TOTAL_SESSIONS"), 0),
            max_upload_bytes=_int(values.get("MAX_UPLOAD_BYTES"), 8 * 1024 * 1024),
            demo_access_code=(values.get("DEMO_ACCESS_CODE") or "").strip(),
            caption_partials=(values.get("CAPTION_PARTIALS") or "").strip().casefold() in {"1", "true", "yes", "on"},
            trust_proxy=(values.get("TRUST_PROXY") or "").strip().casefold() in {"1", "true", "yes", "on"},
            telephony_noise_path=resolve_project_path(
                (values.get("TELEPHONY_NOISE_PATH") or "").strip()
                or DEFAULT_TELEPHONY_NOISE_PATH
            ),
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
