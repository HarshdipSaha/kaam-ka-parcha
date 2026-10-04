# Audio Assets and Telephony Codecs

This directory contains reference audio assets and documentation for the telephony simulation pipeline of **Kaam Ka Parcha**.

## Asset Specifications & Metadata Standards

Any audio asset tracked in this repository or used in acoustic benchmarks must adhere to the following schema and requirements:

| Field | Description / Requirement |
|---|---|
| **File Name** | Canonical identifier (e.g., `street_noise.wav`) |
| **Attribution** | Source origin, creator, or recording contributor |
| **License / Consent** | Verifiable permissive license (e.g., CC0, CC-BY 4.0) or documented explicit recording consent for research/evaluation |
| **Capture Conditions** | Device setup, acoustic environment (e.g., busy roadside, vegetable market), background noise characteristics |
| **Format** | Standard uncompressed RIFF WAV, 16-bit signed PCM (`pcm_s16le`) |
| **Sample Rate** | 8000 Hz (telephony narrowband standard) |
| **Channels** | 1 (Mono) |
| **Duration** | Target length in seconds/milliseconds |

## Policy on Real-World Noise Samples

- **Consent & Licensing Pre-requisite**: Before adding physical audio recordings such as `assets/street_noise.wav`, verifiable written license or recording consent documentation must be provided and recorded.
- **In-Memory Test Fixtures**: To ensure repeatable, self-contained, and compliant CI builds without external asset dependencies, all unit tests (`tests/test_audio.py`) use synthetic in-memory sine wave and noise fixtures.

## Tested Telephony Codecs

The shared audio module (`src/parcha/audio.py`) integrates FFmpeg-driven codec round-trips to reproduce realistic Indian narrowband PSTN/telephony network conditions:

1. **G.711 $\mu$-law (`pcm_mulaw`)**:
   - Sample rate: 8000 Hz, 8-bit log-companded PCM at 64 kbps.
   - Used for PSTN / VoIP telephony trunks and IVR audio channels (Timbre/Exotel telephony streams).

2. **AMR-NB 4.75 kbps (`libopencore_amrnb`)**:
   - Adaptive Multi-Rate Narrowband speech codec running at lowest GSM cellular bitrate (4.75 kbps, 8000 Hz).
   - Simulates harsh 2G/poor-coverage cellular speech links commonly encountered by informal and rural workforce callers.
