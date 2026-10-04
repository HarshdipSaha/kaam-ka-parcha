from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any
import wave

import numpy as np

from parcha.audio import _read_pcm, _write_pcm, codec_round_trip, erase_frames, mix_at_snr
from parcha.credits import BudgetExceeded
from parcha.lab.dataset import Clip, load_manifest
from parcha.lab.metrics import amount_match, cer

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
    noise_path: Path | None = None
    cache_dir: Path = field(default_factory=lambda: Path("var/lab/cache"))
    ablation: str | None = None

    def __post_init__(self) -> None:
        self.manifest_path = Path(self.manifest_path)
        self.audio_root = Path(self.audio_root)
        self.output_path = Path(self.output_path)
        self.cache_dir = Path(self.cache_dir)
        if self.noise_path is not None:
            self.noise_path = Path(self.noise_path)


def get_clip_duration(clip: Clip, audio_root: Path) -> float:
    """Return clip duration in seconds from audio file or estimate 6.0s."""
    audio_path = (audio_root / clip.audio).resolve()
    if audio_path.is_file():
        try:
            with wave.open(str(audio_path), "rb") as wf:
                return wf.getnframes() / float(wf.getframerate())
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

    def _get_noise_wav(self) -> bytes:
        if self._noise_wav_cached is not None:
            return self._noise_wav_cached

        if self.config.noise_path and self.config.noise_path.is_file():
            self._noise_wav_cached = self.config.noise_path.read_bytes()
        else:
            # Deterministic synthetic background noise (alternating +/-1000)
            rng = np.random.default_rng(self.config.seed)
            samples = rng.integers(-1000, 1001, size=8000, dtype=np.int16)
            self._noise_wav_cached = _write_pcm(samples)

        return self._noise_wav_cached

    def _resolve_grid(self) -> tuple[list[str], list[float | None], list[float]]:
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

        return codecs, snr_dbs, loss_percents

    def degrade_audio(
        self, source_wav: bytes, codec: str | None, snr: float | None, loss: float
    ) -> bytes:
        """Apply noise, codec, and frame loss degradations with caching."""
        source_hash = hashlib.sha256(source_wav).hexdigest()
        cache_key = hashlib.sha256(
            f"{source_hash}:{codec}:{snr}:{loss}:{self.config.seed}".encode()
        ).hexdigest()
        cache_file = self.config.cache_dir / f"{cache_key}.wav"

        if cache_file.exists():
            return cache_file.read_bytes()

        degraded = source_wav

        # 1. Noise mix at target SNR
        if snr is not None:
            noise_wav = self._get_noise_wav()
            degraded, _ = mix_at_snr(degraded, noise_wav, snr)

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
        codecs, snr_dbs, loss_percents = self._resolve_grid()

        conditions_count = len(codecs) * len(snr_dbs) * len(loss_percents)
        total_calls = len(clips) * conditions_count

        clip_durations = [get_clip_duration(c, self.config.audio_root) for c in clips]
        total_duration = sum(clip_durations) * conditions_count
        projected_credits = total_duration * self.config.credits_per_second

        cap = min(self.config.max_credits, self.config.remaining_credits)
        is_under_budget = projected_credits <= cap

        return {
            "manifest_path": self.config.manifest_path,
            "total_clips": len(clips),
            "codecs": codecs,
            "snr_dbs": snr_dbs,
            "loss_percents": loss_percents,
            "conditions_count": conditions_count,
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
        codecs, snr_dbs, loss_percents = self._resolve_grid()

        self.config.output_path.parent.mkdir(parents=True, exist_ok=True)

        results: list[dict[str, Any]] = []
        total_spent = 0.0

        for clip in clips:
            audio_path = (self.config.audio_root / clip.audio).resolve()
            source_wav = audio_path.read_bytes()
            clip_dur = len(_read_pcm(source_wav)) / 8000.0

            for codec in codecs:
                for snr in snr_dbs:
                    for loss in loss_percents:
                        projected_call_cost = clip_dur * self.config.credits_per_second

                        # Budget limit check before each call
                        if (
                            total_spent + projected_call_cost > self.config.max_credits
                            or total_spent + projected_call_cost > self.config.remaining_credits
                        ):
                            raise BudgetExceeded(
                                f"Budget limit reached: spent {total_spent:.2f} + projected {projected_call_cost:.2f} "
                                f"exceeds limit (max: {self.config.max_credits:.2f}, remaining: {self.config.remaining_credits:.2f})"
                            )

                        degraded_wav = self.degrade_audio(source_wav, codec, snr, loss)

                        t0 = time.perf_counter()
                        try:
                            transcript = prisma.transcribe(degraded_wav, mode="transcribe")
                        except TypeError:
                            transcript = prisma.transcribe(degraded_wav)
                        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

                        reference = clip.reference_transcribe
                        cer_score = round(cer(reference, transcript), 4)

                        expected_paise = clip.entities.get("amount_paise") if clip.entities else None
                        amt_match = (
                            amount_match(int(expected_paise), transcript)
                            if expected_paise is not None
                            else False
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
                        variant = f"{var_prefix}_{codec}_{snr_label}_{loss_label}"

                        row = {
                            "clip_id": clip.id,
                            "codec": codec,
                            "snr": snr,
                            "loss": loss,
                            "variant": variant,
                            "transcript": transcript,
                            "reference": reference,
                            "cer": cer_score,
                            "amount_matched": amt_match,
                            "latency_ms": latency_ms,
                            "credits_spent": call_credits,
                        }

                        # Checkpoint append
                        with self.config.output_path.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(row, ensure_ascii=False) + "\n")

                        results.append(row)

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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = RunnerConfig(
        manifest_path=args.manifest,
        audio_root=args.audio_root,
        output_path=args.output,
        credits_per_second=args.credits_per_second,
        remaining_credits=args.remaining_credits,
        max_credits=args.max_credits,
        ablation=args.ablation,
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
        print(f"Sweep complete. Evaluated {len(results)} calls.")
        print(f"Results written to: {config.output_path}")
        return 0
    except BudgetExceeded as exc:
        sys.stderr.write(f"Budget exceeded during sweep: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
