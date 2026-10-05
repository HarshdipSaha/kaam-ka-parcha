from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any, Literal

import numpy as np

from parcha.audio import _read_pcm, _write_pcm, codec_round_trip, erase_frames, mix_at_snr, normalize_upload
from parcha.credits import BudgetExceeded
from parcha.gnani import GnaniError
from parcha.lab.dataset import Clip, load_manifest
from parcha.lab.metrics import amount_match, cer, hallucinated_words, word_error_rate
from parcha.lab.noise import IMPULSE_PROFILES, inject_impulses

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENGINE_NOISE_PATH = PROJECT_ROOT / "data" / "real_world_samples" / "car_engine_idle_16k.wav"
REST_MAX_AUDIO_SECONDS = 29.0  # leave margin under Gnani REST's 30-second limit
SAMPLE_RATE = 8000
# FFmpeg's AMR-NB frame round-trip can pad the clip by 20 ms at its tail.
FORECAST_CODEC_PADDING_SECONDS = {"amr_nb_4750": 0.05}

__all__ = [
    "BudgetExceeded",
    "Runner",
    "RunnerConfig",
    "main",
    "print_forecast",
]


@dataclass
class RunnerConfig:
    manifest_path: Path
    audio_root: Path
    output_path: Path = field(default_factory=lambda: Path("var/lab/line_noise_results.jsonl"))
    codecs: list[str] = field(default_factory=lambda: ["g711", "amr_nb_4750"])
    snr_dbs: list[float | None] = field(default_factory=lambda: [None, 10.0, 5.0, 0.0])  # None = clean
    loss_percents: list[float] = field(default_factory=lambda: [0.0])
    seed: int = 20261004
    credits_per_second: float = 0.2
    remaining_credits: float = 5000.0
    max_credits: float = 2000.0
    noise_path: Path | None = field(default_factory=lambda: DEFAULT_ENGINE_NOISE_PATH)
    impulse_profiles: list[str | None] = field(default_factory=list)
    cache_dir: Path = field(default_factory=lambda: Path("var/lab/cache"))
    ablation: str | None = None
    stt_modes: list[Literal["transcribe", "verbatim"]] = field(default_factory=lambda: ["transcribe"])
    bias_words: list[str] | None = None
    request_interval_seconds: float = 0.0
    resume: bool = False

    def __post_init__(self) -> None:
        self.manifest_path = Path(self.manifest_path)
        self.audio_root = Path(self.audio_root)
        self.output_path = Path(self.output_path)
        self.cache_dir = Path(self.cache_dir)
        if self.noise_path is not None:
            self.noise_path = Path(self.noise_path)
        if not self.stt_modes:
            raise ValueError("at least one STT mode is required")
        if any(mode not in {"transcribe", "verbatim"} for mode in self.stt_modes):
            raise ValueError("STT modes must be transcribe or verbatim")
        if self.bias_words and "verbatim" not in self.stt_modes:
            raise ValueError("bias words require verbatim mode")
        if self.request_interval_seconds < 0:
            raise ValueError("request interval cannot be negative")
        unknown = {profile for profile in self.impulse_profiles if profile is not None} - set(IMPULSE_PROFILES)
        if unknown:
            raise ValueError(f"Unknown impulse profiles: {', '.join(sorted(unknown))}")


def get_clip_duration(clip: Clip, audio_root: Path) -> float:
    """Return clip duration in seconds from audio file or estimate 6.0s."""
    audio_path = (audio_root / clip.audio).resolve()
    if audio_path.is_file():
        try:
            return len(_read_pcm(audio_path.read_bytes())) / float(SAMPLE_RATE)
        except Exception:
            pass
    return 6.0


def print_forecast(fc: dict[str, Any]) -> None:
    """Print human-readable pre-flight credit forecast."""
    print("==================================================")
    print("Line Noise Lab STT Pre-Flight Forecast")
    print("==================================================")
    print(f"Manifest:          {fc['manifest_path']}")
    print(f"Total Clips:       {fc['total_clips']}")
    print(f"Codecs ({len(fc['codecs'])}):       {', '.join(str(c) for c in fc['codecs'])}")
    print(
        f"SNRs ({len(fc['snr_dbs'])}):         {', '.join('clean' if s is None else f'{s}dB' for s in fc['snr_dbs'])}"
    )
    print(f"Losses ({len(fc['loss_percents'])}):       {', '.join(f'{l}%' for l in fc['loss_percents'])}")
    profiles = [profile or "none" for profile in fc["impulse_profiles"]]
    print(f"Impulse profiles ({len(profiles)}): {', '.join(profiles)}")
    print(f"STT modes ({len(fc['stt_modes'])}):  {', '.join(fc['stt_modes'])}")
    print(f"Total Grid Calls:  {fc['total_calls']}")
    print(f"Est Total Seconds: {fc['total_duration_seconds']:.1f}s")
    print(f"Projected Credits: {fc['projected_credits']:.2f}")
    print(f"Remaining Credits: {fc['remaining_credits']:.2f}")
    print(f"Max Credits Cap:   {fc['max_credits']:.2f}")
    if fc["is_under_budget"]:
        print("Status:            PASS (Within budget cap)")
    else:
        print("Status:            EXCEEDS BUDGET")
    print("==================================================")


class Runner:
    def __init__(self, config: RunnerConfig, client: Any = None):
        self.config = config
        self.client = client
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        self._noise_wav_cached: bytes | None = None
        self._noise_source = "not_mixed"
        self._noise_sha256: str | None = None

    @property
    def _metadata_path(self) -> Path:
        return self.config.output_path.with_suffix(self.config.output_path.suffix + ".meta.json")

    @staticmethod
    def _condition_key(
        clip_id: str,
        stt_mode: str,
        codec: str,
        snr: float | None,
        loss: float,
        impulse_profile: str | None,
    ) -> tuple[str, str, str, float | None, float, str | None]:
        return (
            clip_id, stt_mode, codec,
            None if snr is None else float(snr), float(loss), impulse_profile,
        )

    def _run_signature(self, clips: list[Clip]) -> str:
        audio_hashes = {}
        for clip in clips:
            path = (self.config.audio_root / clip.audio).resolve()
            audio_hashes[clip.id] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_hash = hashlib.sha256(self.config.manifest_path.read_bytes()).hexdigest()
        noise_hash = None
        if self.config.noise_path is not None and self.config.noise_path.is_file():
            noise_hash = hashlib.sha256(self.config.noise_path.read_bytes()).hexdigest()
        payload = {
            "manifest_sha256": manifest_hash,
            "audio_sha256": audio_hashes,
            "noise_file_sha256": noise_hash,
            "codecs": self.config.codecs,
            "snr_dbs": [None if value is None else float(value) for value in self.config.snr_dbs],
            "loss_percents": [float(value) for value in self.config.loss_percents],
            "seed": self.config.seed,
            "credits_per_second": float(self.config.credits_per_second),
            "remaining_credits": float(self.config.remaining_credits),
            "max_credits": float(self.config.max_credits),
            "impulse_profiles": self.config.impulse_profiles,
            "ablation": self.config.ablation,
            "stt_modes": self.config.stt_modes,
            "bias_words": self.config.bias_words,
            "request_interval_seconds": float(self.config.request_interval_seconds),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _load_resume_state(
        self, clips: list[Clip], codecs: list[str], snr_dbs: list[float | None],
        loss_percents: list[float], impulse_profiles: list[str | None],
    ) -> tuple[list[dict[str, Any]], set[tuple[str, str, str, float | None, float, str | None]], float]:
        if not self.config.output_path.is_file() or not self._metadata_path.is_file():
            raise ValueError("resume requires an existing result file and matching metadata sidecar")
        metadata = json.loads(self._metadata_path.read_text(encoding="utf-8"))
        if metadata.get("signature") != self._run_signature(clips):
            raise ValueError("resume configuration does not match the saved run")

        allowed: set[tuple[str, str, str, float | None, float, str | None]] = set()
        for clip in clips:
            clip_snrs, clip_profiles = self._conditions_for_clip(clip, snr_dbs, impulse_profiles)
            for codec in codecs:
                for snr in clip_snrs:
                    for loss in loss_percents:
                        for profile in clip_profiles:
                            for mode in self.config.stt_modes:
                                allowed.add(self._condition_key(clip.id, mode, codec, snr, loss, profile))

        clips_by_id = {clip.id: clip for clip in clips}
        prior_rows: list[dict[str, Any]] = []
        completed: set[tuple[str, str, str, float | None, float, str | None]] = set()
        total_spent = 0.0
        for line_number, line in enumerate(self.config.output_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("transcription_error"):
                raise ValueError("cannot resume after a provider error; start a new run after resolving it")
            key = self._condition_key(
                row["clip_id"], row["stt_mode"], row["codec"], row.get("snr"),
                row["loss"], row.get("impulse_profile"),
            )
            clip = clips_by_id.get(key[0])
            if key not in allowed or clip is None:
                raise ValueError(f"saved result line {line_number} is outside the configured run")
            if key in completed:
                raise ValueError(f"duplicate saved result condition on line {line_number}")
            if (
                row.get("seed") != self.config.seed
                or row.get("reference") != clip.reference_transcribe
                or row.get("source") != clip.source
                or row.get("source_row") != clip.source_row
            ):
                raise ValueError(f"saved result line {line_number} does not match the manifest")
            if row.get("snr") is None:
                if row.get("noise_sha256") is not None:
                    raise ValueError(f"saved result line {line_number} has an unexpected noise hash")
            elif row.get("noise_sha256") != hashlib.sha256(self._get_noise_wav()).hexdigest():
                raise ValueError(f"saved result line {line_number} uses different background noise")
            completed.add(key)
            prior_rows.append(row)
            total_spent += float(row.get("credits_spent", 0.0))
        return prior_rows, completed, total_spent

    def _get_noise_wav(self) -> bytes:
        if self._noise_wav_cached is not None:
            return self._noise_wav_cached

        if self.config.noise_path and self.config.noise_path.is_file():
            raw_noise = self.config.noise_path.read_bytes()
            try:
                _read_pcm(raw_noise)
                self._noise_wav_cached = raw_noise
            except Exception:
                self._noise_wav_cached = normalize_upload(raw_noise, "audio/wav", sample_rate=8000)
            self._noise_source = f"recorded:{self.config.noise_path.name}"
        else:
            # Deterministic synthetic background noise (alternating +/-1000)
            rng = np.random.default_rng(self.config.seed)
            samples = rng.integers(-1000, 1001, size=8000, dtype=np.int16)
            self._noise_wav_cached = _write_pcm(samples)
            self._noise_source = "synthetic_control"

        self._noise_sha256 = hashlib.sha256(self._noise_wav_cached).hexdigest()

        return self._noise_wav_cached

    @staticmethod
    def _conditions_for_clip(
        clip: Clip,
        snr_dbs: list[float | None],
        impulse_profiles: list[str | None],
    ) -> tuple[list[float | None], list[str | None]]:
        if clip.kind == "engine_only":
            return [None], [None]
        return snr_dbs, impulse_profiles

    @staticmethod
    def _with_headroom(wav: bytes, peak_limit: int = 14_000) -> bytes:
        """Attenuate evaluation inputs before additive mixing, preserving SNR."""
        samples = _read_pcm(wav)
        peak = int(np.max(np.abs(samples.astype(np.int32)))) if len(samples) else 0
        if peak <= peak_limit:
            return wav
        scaled = np.rint(samples.astype(np.float64) * (peak_limit / peak)).astype("<i2")
        return _write_pcm(scaled)

    @staticmethod
    def _split_for_rest(wav: bytes) -> list[bytes]:
        """Split mono 8 kHz PCM WAVs into REST-safe chunks without resampling."""
        samples = _read_pcm(wav)
        max_samples = int(REST_MAX_AUDIO_SECONDS * SAMPLE_RATE)
        return [
            _write_pcm(samples[start : start + max_samples])
            for start in range(0, len(samples), max_samples)
        ] or [_write_pcm(np.asarray([], dtype="<i2"))]

    def _resolve_grid(self) -> tuple[list[str], list[float | None], list[float], list[str | None]]:
        codecs = list(self.config.codecs)
        snr_dbs = list(self.config.snr_dbs)
        loss_percents = list(self.config.loss_percents)

        ablation = (self.config.ablation or "").lower().strip()
        if ablation in ("clean", "baseline"):
            snr_dbs = [None]
            loss_percents = [0.0]
        elif ablation == "codec":
            snr_dbs = [None]
            loss_percents = [0.0]
        elif ablation == "noise":
            codecs = ["g711"]
            snr_dbs = [s for s in self.config.snr_dbs if s is not None]
            loss_percents = [0.0]
        elif ablation == "loss":
            codecs = ["g711"]
            snr_dbs = [None]
            loss_percents = [l for l in self.config.loss_percents if l > 0.0] or [1.0, 5.0, 10.0]

        impulse_profiles: list[str | None] = self.config.impulse_profiles or [None]
        return codecs, snr_dbs, loss_percents, impulse_profiles

    def degrade_audio(
        self, source_wav: bytes, codec: str | None, snr: float | None, loss: float, impulse_profile: str | None = None
    ) -> bytes:
        """Apply noise, codec, and frame loss degradations with caching."""
        source_hash = hashlib.sha256(source_wav).hexdigest()
        noise_wav = self._get_noise_wav() if snr is not None else None
        noise_hash = self._noise_sha256 if snr is not None else "no_stationary_mix"
        cache_key = hashlib.sha256(
            f"{source_hash}:{noise_hash}:{codec}:{snr}:{loss}:{impulse_profile}:{self.config.seed}".encode()
        ).hexdigest()
        cache_file = self.config.cache_dir / f"{cache_key}.wav"

        if cache_file.exists():
            return cache_file.read_bytes()

        degraded = self._with_headroom(source_wav) if snr is not None else source_wav

        # 1. Noise mix at target SNR
        if snr is not None:
            assert noise_wav is not None
            degraded, _ = mix_at_snr(degraded, noise_wav, snr)

        if impulse_profile is not None:
            degraded = inject_impulses(degraded, impulse_profile, seed=self.config.seed)

        # 2. Codec round trip
        if codec and codec not in ("clean", "none", "raw"):
            degraded = codec_round_trip(degraded, codec)

        # 3. Frame erasure
        if loss and loss > 0.0:
            degraded, _ = erase_frames(degraded, loss, seed=self.config.seed)

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(degraded)
        return degraded

    def forecast(self) -> dict[str, Any]:
        """Compute grid evaluation forecast and credit check."""
        clips = load_manifest(self.config.manifest_path, require_audio=False)
        codecs, snr_dbs, loss_percents, impulse_profiles = self._resolve_grid()

        total_calls = 0
        total_duration = 0.0
        for clip in clips:
            clip_snrs, clip_profiles = self._conditions_for_clip(clip, snr_dbs, impulse_profiles)
            conditions_per_codec = (
                len(clip_snrs)
                * len(loss_percents)
                * len(clip_profiles)
                * len(self.config.stt_modes)
            )
            conditions = len(codecs) * conditions_per_codec
            duration = get_clip_duration(clip, self.config.audio_root)
            chunks_per_codec = sum(
                max(
                    1,
                    int(np.ceil(
                        (duration + FORECAST_CODEC_PADDING_SECONDS.get(codec, 0.0))
                        / REST_MAX_AUDIO_SECONDS
                    )),
                )
                for codec in codecs
            )
            total_calls += conditions_per_codec * chunks_per_codec
            total_duration += duration * conditions
        projected_credits = total_duration * self.config.credits_per_second

        cap = min(self.config.max_credits, self.config.remaining_credits)
        is_under_budget = projected_credits <= cap

        return {
            "manifest_path": self.config.manifest_path,
            "total_clips": len(clips),
            "codecs": codecs,
            "snr_dbs": snr_dbs,
            "loss_percents": loss_percents,
            "impulse_profiles": impulse_profiles,
            "stt_modes": list(self.config.stt_modes),
            "conditions_count": total_calls / len(clips) if clips else 0,
            "total_calls": total_calls,
            "total_duration_seconds": round(total_duration, 2),
            "credits_per_second": self.config.credits_per_second,
            "projected_credits": round(projected_credits, 2),
            "remaining_credits": self.config.remaining_credits,
            "max_credits": self.config.max_credits,
            "effective_budget": cap,
            "is_under_budget": is_under_budget,
        }

    def run(self, client: Any = None) -> list[dict[str, Any]]:
        """Execute sweep across clips and degradation conditions, enforcing budget limits."""
        prisma = client or self.client
        if prisma is None:
            from parcha.config import Settings
            from parcha.gnani import PrismaClient

            settings = Settings.load()
            settings.require_gnani()
            prisma = PrismaClient(settings.api_key, base_url=settings.gnani_base_url)

        clips = load_manifest(
            self.config.manifest_path, audio_root=self.config.audio_root, require_audio=True
        )
        codecs, snr_dbs, loss_percents, impulse_profiles = self._resolve_grid()

        self.config.output_path.parent.mkdir(parents=True, exist_ok=True)
        results: list[dict[str, Any]] = []
        if self.config.resume:
            _, completed_conditions, total_spent = self._load_resume_state(
                clips, codecs, snr_dbs, loss_percents, impulse_profiles
            )
        else:
            self.config.output_path.write_text("", encoding="utf-8")
            signature = self._run_signature(clips)
            self._metadata_path.write_text(
                json.dumps({"signature": signature}, indent=2), encoding="utf-8"
            )
            completed_conditions = set()
            total_spent = 0.0
        halt_after_error = False

        for clip in clips:
            if halt_after_error:
                break
            audio_path = (self.config.audio_root / clip.audio).resolve()
            source_wav = audio_path.read_bytes()
            try:
                _read_pcm(source_wav)
            except Exception:
                source_wav = normalize_upload(source_wav, "audio/wav", sample_rate=8000)
            clip_dur = len(_read_pcm(source_wav)) / 8000.0

            for codec in codecs:
                if halt_after_error:
                    break
                clip_snrs, clip_profiles = self._conditions_for_clip(clip, snr_dbs, impulse_profiles)
                for snr in clip_snrs:
                    if halt_after_error:
                        break
                    for loss in loss_percents:
                        if halt_after_error:
                            break
                        for impulse_profile in clip_profiles:
                            if halt_after_error:
                                break
                            for stt_mode in self.config.stt_modes:
                                if halt_after_error:
                                    break
                                condition_key = self._condition_key(
                                    clip.id, stt_mode, codec, snr, loss, impulse_profile
                                )
                                if condition_key in completed_conditions:
                                    continue
                                projected_call_cost = clip_dur * self.config.credits_per_second
                                if (
                                    total_spent + projected_call_cost > self.config.max_credits
                                    or total_spent + projected_call_cost > self.config.remaining_credits
                                ):
                                    raise BudgetExceeded(
                                        f"Budget limit reached: spent {total_spent:.2f} + projected {projected_call_cost:.2f} "
                                        f"exceeds limit (max: {self.config.max_credits:.2f}, remaining: {self.config.remaining_credits:.2f})"
                                    )
                                degraded_wav = self.degrade_audio(source_wav, codec, snr, loss, impulse_profile)
                                t0 = time.perf_counter()
                                transcription_error = None
                                chunk_transcripts: list[str] = []
                                audio_chunks = self._split_for_rest(degraded_wav)
                                chunk_errors: list[str] = []
                                attempted_chunks = 0
                                for audio_chunk in audio_chunks:
                                    attempted_chunks += 1
                                    try:
                                        bias = self.config.bias_words if stt_mode == "verbatim" else None
                                        if bias:
                                            chunk_transcripts.append(
                                                prisma.transcribe(audio_chunk, mode=stt_mode, bias=bias)
                                            )
                                        else:
                                            chunk_transcripts.append(
                                                prisma.transcribe(audio_chunk, mode=stt_mode)
                                            )
                                    except GnaniError as exc:
                                        chunk_errors.append(str(exc))
                                        break
                                    except Exception as exc:
                                        chunk_errors.append(f"{type(exc).__name__}: {exc}")
                                        break
                                    finally:
                                        if self.config.request_interval_seconds:
                                            time.sleep(self.config.request_interval_seconds)
                                if chunk_errors:
                                    transcript = None
                                    transcription_error = "; ".join(chunk_errors)
                                    # A paid sweep stops on its first provider error (including 429).
                                    halt_after_error = True
                                else:
                                    transcript = " ".join(part.strip() for part in chunk_transcripts if part.strip())
                                latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

                                reference = clip.reference_transcribe
                                cer_score = round(cer(reference, transcript), 4) if transcript is not None else None
                                wer_score = round(word_error_rate(reference, transcript), 4) if transcript is not None else None
                                expected_paise = clip.entities.get("amount_paise") if clip.entities else None
                                amt_match = (
                                    amount_match(int(expected_paise), transcript)
                                    if expected_paise is not None and transcript is not None
                                    else None
                                )
                                call_credits = round(projected_call_cost, 4)
                                total_spent += call_credits
                                var_prefix = self.config.ablation or "sweep"
                                snr_label = (
                                    "clean"
                                    if snr is None
                                    else f"{int(snr) if isinstance(snr, (int, float)) and snr.is_integer() else snr}db"
                                )
                                loss_label = (
                                    f"{int(loss) if isinstance(loss, (int, float)) and loss.is_integer() else loss}loss"
                                )
                                profile_label = impulse_profile or "no_impulse"
                                variant = f"{var_prefix}_{stt_mode}_{codec}_{snr_label}_{loss_label}_{profile_label}"
                                row = {
                                    "clip_id": clip.id,
                                    "source": clip.source,
                                    "source_dataset": clip.source_dataset,
                                    "source_license": clip.source_license,
                                    "source_row": clip.source_row,
                                    "speaker_hash": clip.speaker_hash,
                                    "stratum": clip.stratum,
                                    "reference_type": clip.reference_type,
                                    "stt_mode": stt_mode,
                                    "bias_words": self.config.bias_words if stt_mode == "verbatim" else None,
                                    "codec": codec,
                                    "snr": snr,
                                    "loss": loss,
                                    "impulse_profile": impulse_profile,
                                    "seed": self.config.seed,
                                    "noise_source": self._noise_source if snr is not None else "none",
                                    "noise_sha256": self._noise_sha256 if snr is not None else None,
                                    "measured_snr_db": snr,
                                    "clip_type": clip.kind,
                                    "variant": variant,
                                    "transcript": transcript,
                                    "transcription_error": transcription_error,
                                    "api_chunks": attempted_chunks,
                                    "reference": reference,
                                    "cer": cer_score,
                                    "wer": wer_score,
                                    "amount_matched": amt_match,
                                    "latency_ms": latency_ms,
                                    "credits_spent": call_credits,
                                    "hallucinated_word_count": hallucinated_words(transcript) if clip.kind == "engine_only" and transcript is not None else None,
                                }
                                with self.config.output_path.open("a", encoding="utf-8") as f:
                                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                                results.append(row)
                                completed_conditions.add(condition_key)

        return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run budgeted line noise STT evaluation sweep"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Execute live API calls against Prisma STT",
    )
    parser.add_argument(
        "--impulse-profiles",
        default="none,impact_wrench,metal_spanner,compressor_exhaust",
        help="Comma-separated profiles; include none for stationary-noise control (default: control plus all transients)",
    )
    parser.add_argument(
        "--noise-path",
        type=Path,
        default=None,
        help="Optional stationary engine/noise WAV mixed before transient impulses",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/synthcall_manifest.jsonl"),
        help="Path to manifest JSONL",
    )
    parser.add_argument(
        "--audio-root",
        type=Path,
        default=Path("var/lab/audio"),
        help="Path to audio root directory",
    )
    parser.add_argument(
        "--credits-per-second",
        type=float,
        default=0.2,
        help="STT credits per audio second (default: 0.2)",
    )
    parser.add_argument(
        "--remaining-credits",
        type=float,
        default=5000.0,
        help="Current remaining credits (default: 5000.0)",
    )
    parser.add_argument(
        "--max-credits",
        type=float,
        default=2000.0,
        help="Maximum credits allocated for sweep (default: 2000.0)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("var/lab/line_noise_results.jsonl"),
        help="Path to output results JSONL",
    )
    parser.add_argument(
        "--ablation",
        type=str,
        default=None,
        help="Ablation mode or identifier",
    )
    parser.add_argument(
        "--stt-modes",
        default="transcribe",
        help="Comma-separated STT formats: transcribe,verbatim",
    )
    parser.add_argument(
        "--bias-words",
        default="",
        help="Comma-separated single-word bias list, sent only to verbatim mode",
    )
    parser.add_argument(
        "--request-interval-seconds",
        type=float,
        default=0.0,
        help="Delay between STT requests (useful for conservative live sweeps)",
    )
    parser.add_argument(
        "--codecs",
        default="g711,amr_nb_4750",
        help="Comma-separated audio codecs to evaluate",
    )
    parser.add_argument(
        "--snr-dbs",
        default="clean,10,5,0",
        help="Comma-separated SNR values; use clean for un-noised audio",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue a partial run only when its saved manifest/configuration signature matches",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = RunnerConfig(
        manifest_path=args.manifest,
        audio_root=args.audio_root,
        output_path=args.output,
        codecs=[codec.strip() for codec in args.codecs.split(",") if codec.strip()],
        snr_dbs=[
            None if snr.strip().lower() in {"clean", "none"} else float(snr.strip())
            for snr in args.snr_dbs.split(",")
            if snr.strip()
        ],
        credits_per_second=args.credits_per_second,
        remaining_credits=args.remaining_credits,
        max_credits=args.max_credits,
        ablation=args.ablation,
        noise_path=args.noise_path,
        impulse_profiles=[None if p.strip().lower() == "none" else p.strip() for p in args.impulse_profiles.split(",") if p.strip()],
        stt_modes=[mode.strip() for mode in args.stt_modes.split(",") if mode.strip()],
        bias_words=[word.strip() for word in args.bias_words.split(",") if word.strip()] or None,
        request_interval_seconds=args.request_interval_seconds,
        resume=args.resume,
    )
    runner = Runner(config)
    fc = runner.forecast()

    if not args.live:
        print_forecast(fc)
        return 0

    if not fc["is_under_budget"]:
        raise BudgetExceeded(
            f"Projected credits ({fc['projected_credits']:.1f}) exceeds budget cap ({min(config.max_credits, config.remaining_credits):.1f})"
        )

    print_forecast(fc)
    print("Starting live sweep execution...")
    try:
        results = runner.run()
        provider_errors = [row for row in results if row.get("transcription_error")]
        attempted_requests = sum(int(row.get("api_chunks", 0)) for row in results)
        if provider_errors:
            print(
                f"Sweep aborted after provider error. Recorded {len(results)} conditions "
                f"across {attempted_requests} attempted requests."
            )
            print(f"Provider error: {provider_errors[0]['transcription_error']}")
            print(f"Partial results written to: {config.output_path}")
            return 1
        print(f"Sweep complete. Evaluated {len(results)} conditions across {attempted_requests} requests.")
        print(f"Results written to: {config.output_path}")
        return 0
    except BudgetExceeded as exc:
        sys.stderr.write(f"Budget exceeded during sweep: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
