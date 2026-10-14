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
    api_key: str = field(default="", repr=False)   # one Gnani key, or several separated by commas (used in order)
    extractor_base_url: str = ""
    extractor_api_key: str = field(default="", repr=False)
    extractor_model: str = ""
    extractor_provider: str = "evon"
    tts_voice: str = "Vikrant"
    gnani_base_url: str = "https://api.vachana.ai"
    reply_transport: str = "rest"
    jev_api_key: str = field(default="", repr=False)
    jev_model: str = "jev-1.13.0"
    jev_timeout_ms: int = 20000
    jev_review_enabled: bool = False
    use_automotive_bias: bool = True
    telephony_codec: str = "g711"
    telephony_target_snr_db: float = 5.0
    telephony_noise_path: Path = DEFAULT_TELEPHONY_NOISE_PATH
    # Public-demo guards (0 / empty = off, the local default); see src/parcha/guard.py.
    rate_limit_per_minute: int = 0
    sessions_per_ip_per_hour: int = 0
    max_total_sessions: int = 0
    max_upload_bytes: int = 8 * 1024 * 1024
    max_speech_calls_per_day: int = 0   # app-wide cap on credit-spending POSTs per rolling 24 h
    demo_access_code: str = field(default="", repr=False)
    audio_cleanup: bool = False      # AUDIO_CLEANUP=1: high-pass + denoise recordings before Prisma (unmeasured; see audio.py)
    twilio_account_sid: str = ""
    twilio_auth_token: str = field(default="", repr=False)
    twilio_from_number: str = ""
    public_base_url: str = ""        # this app's own public HTTPS URL, needed so Twilio can fetch audio back from it
    mock: bool = False               # PARCHA_MOCK=1: scripted offline speech services (src/parcha/mock.py)
    trust_proxy: bool = False
    caption_partials: bool = True    # interim transcripts via the x-partials header (live probe 2026-10-07: ~0.6 s cadence)

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
            jev_api_key=(values.get("TYPESAFE_API_KEY") or values.get("JEV_API_KEY") or "").strip(),
            jev_model=(values.get("TYPESAFE_DEFAULT_MODEL") or "jev-1.13.0").strip(),
            jev_timeout_ms=max(1, _int(values.get("JEV_TIMEOUT_MS"), 20000)),
            jev_review_enabled=(values.get("JEV_REVIEW_ENABLED") or "").casefold() in {"1", "true", "yes", "on"},
            use_automotive_bias=(values.get("USE_AUTOMOTIVE_BIAS") or "true").strip().casefold() not in {"0", "false", "no", "off"},
            telephony_codec=(values.get("TELEPHONY_CODEC") or "").strip() or "g711",
            telephony_target_snr_db=float((values.get("TELEPHONY_TARGET_SNR_DB") or "5.0").strip()),
            rate_limit_per_minute=_int(values.get("RATE_LIMIT_PER_MINUTE"), 0),
            sessions_per_ip_per_hour=_int(values.get("SESSIONS_PER_IP_PER_HOUR"), 0),
            max_total_sessions=_int(values.get("MAX_TOTAL_SESSIONS"), 0),
            max_upload_bytes=_int(values.get("MAX_UPLOAD_BYTES"), 8 * 1024 * 1024),
            max_speech_calls_per_day=_int(values.get("MAX_SPEECH_CALLS_PER_DAY"), 0),
            demo_access_code=(values.get("DEMO_ACCESS_CODE") or "").strip(),
            audio_cleanup=(values.get("AUDIO_CLEANUP") or "").strip().casefold() in {"1", "true", "yes", "on"},
            twilio_account_sid=(values.get("TWILIO_ACCOUNT_SID") or "").strip(),
            twilio_auth_token=(values.get("TWILIO_AUTH_TOKEN") or "").strip(),
            twilio_from_number=(values.get("TWILIO_FROM_NUMBER") or "").strip(),
            public_base_url=(values.get("PUBLIC_BASE_URL") or "").strip().rstrip("/"),
            mock=(values.get("PARCHA_MOCK") or "").strip().casefold() in {"1", "true", "yes", "on"},
            caption_partials=(values.get("CAPTION_PARTIALS") or "1").strip().casefold() not in {"0", "false", "no", "off"},
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
        if self.mock:
            return
        if not any(k.strip() and k.strip() != "replace_me" for k in self.api_key.split(",")):
            raise ValueError("API_KEY is required for live Gnani calls")

    def require_twilio(self) -> None:
        if not (self.twilio_account_sid and self.twilio_auth_token and self.twilio_from_number and self.public_base_url):
            raise ValueError("TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER and PUBLIC_BASE_URL are all required for a phone call")

    def require_extractor(self) -> None:
        if self.mock:
            return
        if not self.extractor_base_url or not self.extractor_model:
            raise ValueError("An extractor endpoint and model are required")
