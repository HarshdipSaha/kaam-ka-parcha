import argparse
from pathlib import Path
import sys
import wave

# Ensure src is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from parcha.config import Settings
from parcha.gnani import PrismaClient, TimbreClient


def get_balance(prompt: str, override: float | None = None) -> float:
    if override is not None:
        return override
    while True:
        try:
            line = input(prompt).strip()
            return float(line)
        except (ValueError, EOFError) as e:
            print(f"Invalid input: {e}. Please enter a numeric balance.")


def validate_clip_duration(clip_path: Path) -> float:
    if not clip_path.exists():
        raise FileNotFoundError(f"Clip file not found: {clip_path}")
    with wave.open(str(clip_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        if rate <= 0:
            raise ValueError(f"Invalid framerate in {clip_path}: {rate}")
        duration = frames / float(rate)
    if not (4.0 <= duration <= 8.0):
        raise ValueError(
            f"Clip duration {duration:.2f}s is outside required range [4.0, 8.0] seconds"
        )
    return duration


def run_probe(
    clip_path: Path,
    *,
    initial_balance: float | None = None,
    mid_balance: float | None = None,
    final_balance: float | None = None,
    settings: Settings | None = None,
) -> dict[str, float]:
    if settings is None:
        settings = Settings.load()
    settings.require_gnani()

    duration = validate_clip_duration(clip_path)

    init_bal = get_balance("Dashboard balance BEFORE STT call: ", initial_balance)

    wav_bytes = clip_path.read_bytes()
    prisma = PrismaClient(settings.api_key, base_url=settings.gnani_base_url)
    transcript = prisma.transcribe(wav_bytes, mode="transcribe")
    print(f"STT Transcript: {transcript}")

    mid_bal = get_balance("Dashboard balance AFTER STT call: ", mid_balance)
    stt_delta = init_bal - mid_bal
    rate = stt_delta / duration if duration > 0 else 0.0
    print(f"STT credits delta: {stt_delta:.2f} ({rate:.4f} credits/s)")

    timbre = TimbreClient(
        settings.api_key, voice=settings.tts_voice, base_url=settings.gnani_base_url
    )
    tts_audio = timbre.synthesize("कुल ₹650")
    print(f"TTS Audio received: {len(tts_audio)} bytes")

    fin_bal = get_balance("Dashboard balance AFTER TTS call: ", final_balance)
    tts_delta = mid_bal - fin_bal
    print(f"TTS credits delta: {tts_delta:.2f}")

    print("\n--- Summary of Credit Deltas ---")
    print(f"Clip Duration: {duration:.2f}s")
    print(f"Initial Balance: {init_bal:.2f}")
    print(f"Mid Balance: {mid_bal:.2f}")
    print(f"Final Balance: {fin_bal:.2f}")
    print(f"STT Credits: {stt_delta:.2f}")
    print(f"STT Credits/sec: {rate:.4f}")
    print(f"TTS Credits: {tts_delta:.2f}")
    print(f"Total Credits: {stt_delta + tts_delta:.2f}")

    return {
        "duration": duration,
        "initial_balance": init_bal,
        "mid_balance": mid_bal,
        "final_balance": fin_bal,
        "stt_delta": stt_delta,
        "credits_per_second": rate,
        "tts_delta": tts_delta,
        "total_delta": stt_delta + tts_delta,
    }


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe Gnani Prisma STT and Timbre TTS APIs for credit usage measurement"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run live paid calls against Gnani APIs (mandatory)",
    )
    parser.add_argument(
        "--clip",
        required=True,
        type=Path,
        help="Path to WAV audio clip with duration between 4 and 8 seconds",
    )
    parser.add_argument(
        "--initial-balance",
        type=float,
        default=None,
        help="Dashboard balance before any calls",
    )
    parser.add_argument(
        "--mid-balance",
        type=float,
        default=None,
        help="Dashboard balance after STT call",
    )
    parser.add_argument(
        "--final-balance",
        type=float,
        default=None,
        help="Dashboard balance after TTS call",
    )
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.live:
        sys.stderr.write("Error: --live flag is required to run probe\n")
        return 1

    try:
        run_probe(
            args.clip,
            initial_balance=args.initial_balance,
            mid_balance=args.mid_balance,
            final_balance=args.final_balance,
        )
        return 0
    except Exception as exc:
        # NEVER print API key, raw response headers, or log user secrets
        # On error, exit immediately without auto-retry.
        sys.stderr.write(f"Probe failed: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
