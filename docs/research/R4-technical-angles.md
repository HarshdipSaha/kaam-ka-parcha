# R4 — Technical angles: datasets, telephony simulation, Evon hosting, measurement, idea seeds

> Research ticket R4 for the Gnani "Great Indian AI Internship Challenge" (deadline 10 Nov 2026). Researched 2026-10-04 with WebSearch/WebFetch, `curl` against the Hugging Face API and dataset pages. **No Gnani API was called.** Stack facts come from `docs/notes/02-speech-apis.md`, `03-sdks-and-integrations.md`, `05-models.md` (authoritative). Legend: **[SPEC]** = my inference/estimate, not a published fact; **[VERIFY]** = cheap to check live, do it before relying on it.

---

## 1. Executive summary

1. **There is exactly one public corpus of real Indic telephone speech: Gramvaani (OpenSLR 118).** 100 h labelled + 5 h dev + 3 h eval + 1,000 h unlabelled, spontaneous Hindi over the Mobile Vaani IVR, mp3 at mixed 8–48 kHz, "free for academic purposes" ([openslr.org/118](https://www.openslr.org/118/)). Gnani itself calls Gramvaani and Kathbath-noisy "the datasets that matter most for production voice AI in India" ([Gnani benchmarking deep-dive](https://www.gnani.ai/resources/research/benchmarking-indic-asr-models-a-technical-deep-dive)). Everything else "noisy" (Kathbath-noisy, Vaani, IndicVoices) is smartphone-app speech, and everything code-mixed (MUCS, HiACC, CS-FLEURS) is lecture/read/synthetic speech, not phone calls. **No public Indic call-centre corpus exists.** The honest fix is to *build* one: Timbre two-voice dialogues with exact ground truth, pushed through an 8 kHz codec/noise chain (§3), then scored on Prisma. That gives entity-level and speaker-turn ground truth that no public set provides.
2. **Kathbath-noisy is small and specific**: it is the ~5 h of recordings *rejected at QC* (10 M + 10 F speakers), not SNR-controlled noise ([IndicSUPERB paper](https://arxiv.org/pdf/2208.11761)). For a WER-vs-SNR curve you must synthesise noise yourself anyway. Use **MUSAN** (CC BY 4.0, 11 GB), **DEMAND** (CC BY-SA 3.0), **WHAM! noise** (CC BY-NC 4.0, 17 GB) and, uniquely Indian, **Vaani-Noise-Event-Dataset** (154.6 h of annotated Indian ambient noise, CC BY 4.0, 17.7 GB).
3. **Telephony simulation is a solved tooling problem**: stock ffmpeg does G.711 µ/A-law, G.726, Opus; an AMR-capable build adds AMR-NB 4.75–12.2 kbps; `phonesim` (MIT, pip) wraps all of it with seeded profiles incl. packet loss, jitter, AGC and clock drift ([deepmark/phonesim](https://github.com/deepmark/phonesim)); `audiomentations` (MIT, 43 transforms) handles SNR-controlled noise, band-limiting, room IRs, bit-crush and clipping. Gnani's own training recipe (AMR-NB at all 8 bitrates on 40 % of data, 0–15 dB non-stationary rural noise) is published and can be mirrored exactly ([rural ASR whitepaper](https://www.gnani.ai/resources/research/the-rural-india-asr-problem-engineering-speech-recognition-for-background-noise)).
4. **Evon without a GPU is feasible but should be a bonus, not the spine.** Cheapest real path: **Modal** ($30/month free credit, A100-80GB $2.50/h per-second billing → ~12 free A100-hours/month, vLLM BF16 official recipe) or **RunPod** (A100 80GB community $1.19/h; RTX 4090 $0.34/h or A6000-48GB $0.33/h for Q4/Q8 GGUF). Free paths: **Kaggle 2×T4** (30 h/week) running IQ4_XS GGUF (~17 GiB) via llama.cpp at an estimated 25–50 tok/s **[SPEC]**, and **HF ZeroGPU** (48 GB RTX Pro 6000 slice, free accounts can host 2 Spaces, 5 min/day/visitor, PRO $9/mo → 40 min/day). Budget ₹3–5k ≈ $36–60 ≈ 30–50 A100-hours on RunPod. Measured decode: 257 tok/s BF16 on Gnani's endpoint; 86 tok/s Q4_K_M on M4 Max; 63.6 tok/s on DGX Spark.
5. **What will impress Gnani's engineers** is already written down by Gnani: tiered WER/CER by SNR band (>20, 15–20, <15 dB) at **8 kHz, never upsampled**; 200–500 utterances per condition (400+ for ±1 pt); separate code-switch WER; entity vocabulary (NPA/EMI/DPD/KYC/OTP, amounts); diarization word-attribution accuracy; **P95 latency under concurrency**; dataset-level (not per-utterance) aggregation; NFC normalisation; and "do not compress into one composite score" ([how to benchmark STT](https://www.gnani.ai/resources/research/how-to-benchmark-stt-api-indian-languages)). Their code-switch paper defines **switch-point MER as MER inside a 1-s window centred on each annotated language boundary** ([code-switching at 8 kHz](https://www.gnani.ai/resources/research/code-switching-at-8khz)). Reproducing *their* metrics on *our* system is the interview story.
6. **EULA guard-rail**: publish only our own system's deltas (denoise on/off, SNR curves, preset A vs B, bias_list on/off). Never a "Gnani vs X" table. Ask organisers on Discord before posting absolute WERs **[VERIFY]**.
7. **Three strongest seeds (§6)**: **Line Noise Lab** (reproducible telephony-stress harness: the measurement backbone and the Noise Canceller entry), **Phone-a-Form / Paisa Proof** (entity-first form filling over a 2G-grade line with ITN read-back; real-world + Mixed Vibes), and **Echo Test** (Timbre→phone-line→Prisma round-trip as an intelligibility meter for every voice: the Jugaad Genius candidate). Runner-up: **Kisan Call Mirror** (two-leg regional-language helpline assist, Main Character).

---

## 2. Dataset table

Sizes/hours are from the linked cards or papers; "gated: auto" means click-through on Hugging Face with a logged-in token (instant). All AI4Bharat/ARTPARK repos are gated-auto.

| # | Dataset | Languages | Hours | Sample rate | Telephony / noisy? | Code-mixed? | Licence | Link | How to get it | Download size |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Gramvaani 1111 h Hindi ASR Challenge** (Interspeech 2022) | Hindi, regional dialects (Bihar/UP/Jharkhand/MP…) | 100 h train + 5 h dev + 3 h eval labelled; 1,000 h unlabelled | **mp3, mixed 8–48 kHz** (real IVR) | **Yes, real spontaneous telephone speech** via Mobile Vaani; natural background | Some, incidental | "Used freely for academic purposes; commercial use by permission (contact@gramvaani.org)" | [openslr.org/118](https://www.openslr.org/118/), [challenge site](https://sites.google.com/view/gramvaaniasrchallenge/dataset), [paper](https://www.isca-archive.org/interspeech_2022/bhanushali22_interspeech.pdf) | Direct tar.gz from OpenSLR mirrors; HF mirror of the Vistaar test slice: [Trelis/vistaar-hi-gramvaani-test](https://huggingface.co/datasets/Trelis/vistaar-hi-gramvaani-test) (1,032 rows, 0.32 GB, ungated) | Train 2.0 GB, Dev 98 MB, Eval 62 MB, unlabelled 5×(3.2–8.2 GB) ≈ 30 GB |
| 2 | **Kathbath** (IndicSUPERB) | 12: bn gu hi kn ml mr or pa sa ta te ur | 1,684 h total (hi 150, ta 185, mr 185, te 155, ml 147, pa 137, gu 129, bn 116, or 112, sa 116, ur 87, kn 66) | 16 kHz as staged by Vistaar **[VERIFY raw]** | No (read speech on smartphone app); "noisy" split exists (#3) | No | GitHub says CC0; HF card says cc-by-4.0 | [HF ai4bharat/Kathbath](https://huggingface.co/datasets/ai4bharat/Kathbath), [GitHub](https://github.com/AI4Bharat/IndicSUPERB), [paper](https://arxiv.org/pdf/2208.11761) | HF gated-auto; or Vistaar zip [kathbath.zip](https://indicwhisper.objectstore.e2enetworks.net/vistaar_benchmarks/kathbath.zip); Hindi test on [Trelis/vistaar-hi-kathbath-test](https://huggingface.co/datasets/Trelis/vistaar-hi-kathbath-test) (1,929 rows, 0.34 GB) | Train 85 GB; test-known 2 GB; test-unknown 2 GB |
| 3 | **Kathbath-noisy** ("Kathbath-hard") | same 12 | ~5 h total noisy (10 M + 10 F speakers), i.e. recordings *rejected at verification* | 16 kHz (Vistaar) | **Noisy, not telephony**; uncontrolled SNR | No | CC0 (Trelis mirror says cc0-1.0) | [paper §4](https://arxiv.org/pdf/2208.11761), [kathbath_noisy.zip](https://indicwhisper.objectstore.e2enetworks.net/vistaar_benchmarks/kathbath_noisy.zip) | Trelis Hindi slice [vistaar-hi-kathbath_noisy-test](https://huggingface.co/datasets/Trelis/vistaar-hi-kathbath_noisy-test) (1,929 rows, 0.34 GB, ungated) | test-known-noisy 2 GB, test-unknown-noisy 1.4 GB |
| 4 | **MUCS 2021 Subtask 2** (code-switching) | **Hindi-English** (89.86 h train / 5.18 h test), **Bengali-English** (46.11 / 7.02) | ≈148 h | **16 kHz**, spoken-tutorial tech lectures | No | **Yes, intra-sentential, word-level annotated** | **CC BY-SA 4.0** | [MUCS data page](https://navana-tech.github.io/MUCS2021/data.html), [paper](https://www.isca-archive.org/interspeech_2021/diwan21_interspeech.html) | HF mirrors: [dianavdavidson/MUCS-Hinglish](https://huggingface.co/datasets/dianavdavidson/MUCS-Hinglish) (55,961 rows, 10 GB, adds per-segment English-word ratio buckets), [Trelis/vistaar-hi-mucs-test](https://huggingface.co/datasets/Trelis/vistaar-hi-mucs-test) (3,897 rows, 0.61 GB); Vistaar [mucs.zip](https://indicwhisper.objectstore.e2enetworks.net/vistaar_benchmarks/mucs.zip) | 0.6–10 GB |
| 5 | **MUCS 2021 Subtask 1** (monolingual) | hi, mr, or at **8 kHz** (~95 h each, story narration / healthcare-agri-finance); ta, te, gu at 16 kHz (40 h each, Microsoft) | ≈ 400 h | **8 kHz for hi/mr/or** | 8 kHz read speech (not phone-codec) | No | hi/mr/or: challenge terms (password-free mirror); ta/te/gu: Microsoft Open Data licence | [MUCS data page](https://navana-tech.github.io/MUCS2021/data.html) | Direct links on page | tens of GB |
| 6 | **IndicVoices** | 22 scheduled languages | 23.7K h total, 11.2K h transcribed (HF card, 2026); paper v1: 7,348 h / 1,639 h transcribed, 16,237 speakers, 145 districts | not stated on public pages **[VERIFY]** | Smartphone, natural/spontaneous, real-world rooms; **17 % conversational two-party** | Natural Hinglish in extempore/conv | **CC BY 4.0** | [HF ai4bharat/IndicVoices](https://huggingface.co/datasets/ai4bharat/IndicVoices), [paper](https://arxiv.org/abs/2403.01926) | HF gated-auto; use `streaming=True` and one language config; community Hinglish filters exist e.g. [dianavdavidson/indic-voices-hinglish-…](https://huggingface.co/datasets/dianavdavidson/indic-voices-hinglish-nospeakeroverlap-spon3.3-acronyms-fixed2) | Very large (TBs); per-language shards |
| 7 | **IndicVoices-R** (TTS-grade subset) | 22 | 1,704 h, 10,496 speakers (9–175 h/lang) | high quality (TTS-grade) | No | No | **CC BY 4.0** | [HF ai4bharat/indicvoices_r](https://huggingface.co/datasets/ai4bharat/indicvoices_r), [NeurIPS'24 paper](https://arxiv.org/html/2409.05356v2) | HF gated-auto | hundreds of GB |
| 8 | **Svarah** (Indian-accented English) | en-IN, speakers from 19 L1s, 65 districts | 9.6 h, 117 speakers; read + spontaneous | not stated **[VERIFY]** | Clean-ish, no | No | Not stated on card **[VERIFY]** | [HF ai4bharat/Svarah](https://huggingface.co/datasets/ai4bharat/Svarah), [GitHub](https://github.com/AI4Bharat/Svarah), [paper](https://arxiv.org/abs/2305.15760) | HF gated-auto | ~1–2 GB **[SPEC]** |
| 9 | **Lahaja** (multi-accent Hindi) | Hindi spoken by 19-L1 speakers, 83 districts | 12.5 h, 132 speakers; read + extempore | not stated | No | No | **MIT** (HF card) | [HF ai4bharat/Lahaja](https://huggingface.co/datasets/ai4bharat/Lahaja), [paper](https://arxiv.org/pdf/2408.11440) | HF gated-auto | ~2 GB **[SPEC]** |
| 10 | **Vaani** (IISc/ARTPARK + Google) | 105 languages, 165 districts | 31,255 h total; 2,043 h transcribed | variable (smartphone) | **Real-world ambient noise**, image-prompted spontaneous speech | Natural code-mixing | **CC BY 4.0** | [HF ARTPARK-IISc/Vaani](https://huggingface.co/datasets/ARTPARK-IISc/Vaani), [transcription part](https://huggingface.co/datasets/ARTPARK-IISc/Vaani-transcription-part) (hi kn te bn ta gu), [paper](https://arxiv.org/abs/2603.28714) | HF gated (share contact info) | Huge; use per-district/language shards |
| 11 | **Vaani-Benchmark-V1.0** | Hindi (with code-switching) | 10.9 h, 5,050 segments, 1,103 speakers, 104 districts, **3 independent human transcriptions each** | variable | Real-world noise markers in transcripts | Yes, natural | **CC BY 4.0** | [HF ARTPARK-IISc/Vaani-Benchmark-V1.0](https://huggingface.co/datasets/ARTPARK-IISc/Vaani-Benchmark-V1.0), [paper](https://arxiv.org/html/2606.21408) | HF gated (contact info) | ~1–2 GB **[SPEC]** |
| 12 | **Vaani-Noise-Event-Dataset** (Indian noise bank) | — (non-speech) | **~154.6 h, 90,637 segments**, 7 classes (animals, traffic, baby/child, music/singing, phone/alarms, appliances, human non-speech) + 10 h speaker-disjoint eval | not stated | **Yes: real Indian household/street noise** | — | **CC BY 4.0** | [HF ARTPARK-IISc/Vaani-Noise-Event-Dataset](https://huggingface.co/datasets/ARTPARK-IISc/Vaani-Noise-Event-Dataset) | HF gated (contact info) | **17.7 GB** |
| 13 | **Shrutilipi** | 12 (bn gu hi kn ml mr or pa sa ta te ur) | 6,400 h mined from All India Radio bulletins | broadcast | No (clean read news) | No | **CC BY 4.0** | [HF ai4bharat/Shrutilipi](https://huggingface.co/datasets/ai4bharat/Shrutilipi), [site](https://datasets.ai4bharat.org/shrutilipi/) | HF gated-auto | very large; use for vocab/LM only |
| 14 | **SPRING-INX** (IIT Madras) | as bn gu hi kn ml mr or pa ta | ~2,000 h manually transcribed | — | Mixed read/conversational **[VERIFY]** | — | **CC BY 4.0** (paper) | [paper](https://arxiv.org/abs/2310.14654), [asr.iitm.ac.in](https://asr.iitm.ac.in/) (JS site, form) | Request via site | large |
| 15 | **IndicTTS** (IITM, via SPRINGLab) | hi (10.33 h, 1 M + 1 F), en, gu, bn, ta, mr, te, kn… | ~10 h/lang | **48 kHz** studio | No (clean baseline; Gnani benchmarks on it) | No | "Indic TTS licence terms" (research; read before use) | [HF SPRINGLab/IndicTTS-Hindi](https://huggingface.co/datasets/SPRINGLab/IndicTTS-Hindi), [collection](https://huggingface.co/collections/SPRINGLab/indictts-datasets) | HF ungated | Hindi 8.21 GB |
| 16 | **Common Voice** (Mozilla) | ta, bn, hi, mr, pa, ur, ml, or, as… | varies widely: Tamil and Bengali hundreds of hours, Hindi tens, others single digits **[approx, not re-verified]** | 48 kHz mp3, crowd mics | Crowd read speech, some noise | No | **CC0** | [commonvoice.mozilla.org/datasets](https://commonvoice.mozilla.org/en/datasets); Vistaar test slices [commonvoice.zip](https://indicwhisper.objectstore.e2enetworks.net/vistaar_benchmarks/commonvoice.zip) | CV portal (email gate) or Vistaar zip | GBs per language |
| 17 | **FLEURS** (Google) | 102 langs incl. as bn gu hi kn ml mr ne or pa ta te ur | ~10–12 h per language | 16 kHz | No (read Wikipedia sentences) | No | **CC BY 4.0** | [HF google/fleurs](https://huggingface.co/datasets/google/fleurs) (ungated); Vistaar [fleurs.zip](https://indicwhisper.objectstore.e2enetworks.net/vistaar_benchmarks/fleurs.zip) | `load_dataset("google/fleurs","hi_in")` | ~1 GB/lang (630 GB whole) |
| 18 | **CS-FLEURS** | 113 code-switched pairs / 52 langs; **Hindi-English in XTTS-Test2** | ~300 h total, mostly **synthetic TTS** (XTTS/MMS) + a human-read subset | — | No | **Yes (synthetic)** | **CC BY-NC 4.0** | [HF byan/cs-fleurs](https://huggingface.co/datasets/byan/cs-fleurs) | HF ungated (0.03 GB metadata; audio via LFS) | small |
| 19 | **HiACC** (Hinglish adults + children) | Hinglish | 5.24 h, 5,176 utts (3,318 adult, 1,858 child); read + spontaneous | not stated | No | **Yes** | **CC BY 4.0** | [Zenodo 15551669](https://zenodo.org/records/15551669), [paper](https://www.sciencedirect.com/science/article/pii/S2352340925006109) | Direct zip | **531.6 MB** |
| 20 | **addyo07/noisy-hinglish-asr** (community) | hi, en, hinglish, + non-speech negatives | 36.6 h, 28,681 clips; benchmark splits `clean_hi` 500, `hinglish` 1,036, `noisy_hi` 250, `negatives` 200 | **16 kHz PCM16 mono** | **Synthetic desktop/room noise** | **Yes** | Apache-2.0 | [HF addyo07/noisy-hinglish-asr](https://huggingface.co/datasets/addyo07/noisy-hinglish-asr) | HF ungated, parquet | 3.85 GB |
| 21 | **Bhashini / ULCA** datasets | many | varies | varies | some | some | per-contributor; portal login | [bhashini.gov.in](https://bhashini.gov.in/) | Registration; slow **[SPEC]** | — |
| 22 | **Google Indic multi-speaker TTS** (OpenSLR 63–66, 78–79) | ml, mr, ta, te, gu, kn | ~5–10 h each, many speakers | 48 kHz | No | No | CC BY-SA 4.0 (known; not re-verified today) | [openslr.org/63](https://www.openslr.org/63/) … [/79](https://www.openslr.org/79/) | Direct zips | 1–3 GB each |
| N1 | **MUSAN** (noise+music+speech) | — | ~109 h | 16 kHz | noise bank | — | **CC BY 4.0** | [openslr.org/17](https://www.openslr.org/17/) | `musan.tar.gz` | **11 GB** |
| N2 | **DEMAND** | — | 15 environments (kitchen, bus, metro, café, traffic…) × 16 channels | 48 kHz and 16 kHz | noise bank | — | **CC BY-SA 3.0** | [Zenodo 1227121](https://zenodo.org/records/1227121) | per-environment zips 80–376 MB | ~6.3 GB all |
| N3 | **WHAM! noise** | — | restaurants/bars/parks (SF Bay), processed to remove intelligible speech | 16 kHz stereo float32 (also 48 kHz version, 76 GB) | noise bank | — | **CC BY-NC 4.0** | [wham.whisper.ai](http://wham.whisper.ai/) | `wham_noise.zip` | **17 GB → 35 GB** |
| N4 | **RIRS_NOISES** (room IRs) | — | simulated + real RIRs | 16 kHz | reverb bank | — | Apache 2.0 (known) | [openslr.org/28](https://www.openslr.org/28/) | zip | ~1 GB |

**Call-centre-like corpora:** none public for Indic. Gnani's own 4,200-utterance Hinglish G.711 set (SNR −2 to 15 dB, collections/customer-service/field-support) is private ([code-switching whitepaper](https://www.gnani.ai/resources/research/code-switching-at-8khz)). Closest public proxies: Gramvaani (#1, IVR monologues), MUCS hi/mr/or at 8 kHz (#5), IndicVoices conversational (#6). **Recommendation:** synthesise a "SynthCall-IN" set (Timbre two voices → §3 chain) for entity/turn ground truth and keep Gramvaani as the real-world anchor.

**Vistaar** (AI4Bharat, MIT) is the one-stop staging of the exact test sets Gnani's benchmark microsite uses (Kathbath, Kathbath-noisy, CommonVoice, FLEURS, IndicTTS, MUCS, Gramvaani) with `evaluation.py` ([GitHub AI4Bharat/vistaar](https://github.com/AI4Bharat/vistaar)). Download the zips above or the `Trelis/vistaar-hi-*` Hindi slices (ungated, <1 GB each).

---

## 3. Telephony-simulation recipe

Goal: turn 16/48 kHz clean speech into audio that behaves like an Indian phone call, with every parameter logged so the result is reproducible. Mirror Gnani's own description of the channel: band-limit 200/300–3,400 Hz, 8 kHz, AMR-NB 4.75–12.2 kbps, up to 15 % packet loss on 2G/EDGE, AGC, 0–10 dB SNR non-stationary noise (wind, cattle, diesel engines, hand pumps, children, radios) ([rural ASR whitepaper](https://www.gnani.ai/resources/research/the-rural-india-asr-problem-engineering-speech-recognition-for-background-noise)); G.711 at −2 to 15 dB SNR for BFSI calls ([code-switching whitepaper](https://www.gnani.ai/resources/research/code-switching-at-8khz)).

### 3.1 Pipeline order (matters)
`clean 16k → (room IR) → + noise at target SNR → band-limit/level/AGC → resample 8k → codec encode → (packet loss / PLC) → codec decode → PCM16 8k`
Then: stream to Prisma WS with `x-sample-rate: 8000` as PCM16 1024-byte frames (64 ms cadence), or upload to REST/Batch. Note the WS wants **PCM**, so the codec is baked in by the encode→decode round trip; the µ-law *container* is only relevant for Timbre output (`container: mulaw` forces 8 kHz) and for real carriers (Twilio sends `audio/x-mulaw` 8 kHz; Exotel sends 16-bit slin 8 kHz base64).

### 3.2 ffmpeg one-liners (check your build: `ffmpeg -hide_banner -encoders | findstr /i "amr gsm g726 opus mulaw"`; the gyan.dev "full" Windows build ships libopencore-amrnb and libgsm **[VERIFY]**)
```bash
# G.711 mu-law round trip (PSTN/VoIP baseline)
ffmpeg -y -i in16k.wav -af "highpass=f=300,lowpass=f=3400" -ac 1 -ar 8000 -c:a pcm_mulaw tmp.ul
ffmpeg -y -f mulaw -ar 8000 -ac 1 -i tmp.ul -c:a pcm_s16le out_g711.wav
# A-law: swap pcm_mulaw/mulaw for pcm_alaw/alaw
# AMR-NB (2G/3G cellular). Bitrates: 4.75k 5.15k 5.9k 6.7k 7.4k 7.95k 10.2k 12.2k
ffmpeg -y -i in16k.wav -ac 1 -ar 8000 -c:a libopencore_amrnb -b:a 4.75k tmp.amr
ffmpeg -y -i tmp.amr -c:a pcm_s16le -ar 8000 out_amr475.wav
# GSM full-rate 13 kbps (needs libgsm)
ffmpeg -y -i in16k.wav -ac 1 -ar 8000 -c:a libgsm -f gsm tmp.gsm && ffmpeg -y -i tmp.gsm -c:a pcm_s16le out_gsm.wav
# G.726 ADPCM 16/24/32/40 kbps (native ffmpeg)
ffmpeg -y -i in16k.wav -ac 1 -ar 8000 -c:a g726 -b:a 16k tmp.g726 && ffmpeg -y -f g726 -ar 8000 -i tmp.g726 -c:a pcm_s16le out_g726.wav
# Opus VoIP leg (WhatsApp/VoLTE-ish) with encoder-side loss hints
ffmpeg -y -i in16k.wav -ac 1 -ar 16000 -c:a libopus -b:a 12k -application voip -frame_duration 20 -packet_loss 10 -fec 1 tmp.ogg
# Level/AGC-ish: compressor + limiter
ffmpeg -y -i x.wav -af "acompressor=threshold=-20dB:ratio=4:attack=5:release=50,alimiter=limit=0.9" y.wav
```
Docs: [FFmpeg codecs](https://ffmpeg.org/ffmpeg-codecs.html); G.711/AMR-NB/GSM-FR facts: [G.711](https://en.wikipedia.org/wiki/G.711), [APSIPA 2019 codec-augmentation paper](http://www.apsipa.org/proceedings/2019/pdfs/216.pdf) (down-sample to 8 kHz, pass through diverse codecs: the same recipe Gnani describes).

**sox equivalents:** `sox in.wav -r 8000 -c 1 -e mu-law out.wav`; AGC: `sox in.wav out.wav compand 0.3,1 6:-70,-60,-20 -5 -90 0.2`.

### 3.3 phonesim (all-in-one, seeded)
```bash
pip install phonesim          # MIT; needs ffmpeg on PATH (AMR profiles need an AMR-capable ffmpeg)
python -m phonesim.cli run --in a.wav --out b.wav --profile voip_to_cellular_narrowband --seed 7
python -m phonesim.cli analyze --clean a.wav --degraded b.wav
```
```python
from phonesim import PhoneCallSimulator, load_audio, save_audio
x, sr = load_audio("in.wav", sr=24000)
y = PhoneCallSimulator(profile="pstn_narrowband")(x, seed=1234)   # G.711 8 kHz
```
Profiles: `pstn_narrowband` (G.711), `voip_opus_wideband` (≤5 % erasures), `voip_to_cellular_narrowband` (Opus→AMR-NB), `voip_to_cellular_wideband` (Opus→AMR-WB), G.726 and stress variants. Models packet loss, jitter/playout buffer, AGC, ambient noise, clock drift, multi-codec transcoding, per-codec band-limits; deterministic per seed ([deepmark/phonesim](https://github.com/deepmark/phonesim)).

### 3.4 audiomentations (SNR ladder, Indian noise, rooms, device artefacts)
```python
from audiomentations import (Compose, AddBackgroundNoise, AddShortNoises, ApplyImpulseResponse,
    RoomSimulator, BandPassFilter, TanhDistortion, ClippingDistortion, BitCrush, Gain, Limiter, Resample)
snr = 5   # sweep: inf, 20, 15, 10, 5, 0, -5 dB
chain = Compose([
  RoomSimulator(p=0.5),                                   # needs pip install audiomentations[extras] (pyroomacoustics)
  AddBackgroundNoise(sounds_path="noise/vaani_events", min_snr_db=snr, max_snr_db=snr, p=1.0),   # MUSAN / DEMAND / WHAM! / Vaani-Noise
  AddShortNoises(sounds_path="noise/transients", min_snr_db=snr-5, max_snr_db=snr+5, p=0.5),     # horns, dogs, utensils
  Gain(min_gain_db=-12, max_gain_db=6, p=0.7),            # level mismatch
  TanhDistortion(min_distortion=0.05, max_distortion=0.3, p=0.3),   # cheap-mic/AGC saturation
  BandPassFilter(min_center_freq=1000, max_center_freq=1200, min_bandwidth_fraction=1.8, max_bandwidth_fraction=2.0, p=1.0),
  Resample(min_sample_rate=8000, max_sample_rate=8000, p=1.0),
])
```
43 transforms incl. `Mp3Compression`, `Aliasing`, `AirAbsorption`, `LowPassFilter`, `TimeMask` ([docs](https://iver56.github.io/audiomentations/), MIT). Then hand the 8 kHz array to the ffmpeg codec step. `torchaudio.io.AudioEffector` is **deprecated in 2.8 and removed in 2.9** ([docs](https://docs.pytorch.org/audio/2.8.0/generated/torchaudio.io.AudioEffector.html)), so don't build on it; use ffmpeg subprocess or phonesim.

### 3.5 Packet loss and PLC (Python, 20 ms frames, bursty Gilbert-Elliott)
```python
import numpy as np
def packet_loss(x, sr=8000, frame_ms=20, p_loss=0.10, burst=0.5, plc="repeat", seed=0):
    rng = np.random.default_rng(seed); n = int(sr*frame_ms/1000); y = x.copy(); lost=False
    for i in range(0, len(x)-n, n):
        lost = rng.random() < (burst if lost else p_loss)        # Gilbert-Elliott: stay-lost prob = burst
        if lost:
            if plc == "repeat" and i >= n: y[i:i+n] = y[i-n:i] * np.linspace(1, 0.3, n)   # crude repeat+fade PLC
            else: y[i:i+n] = 0.0                                                            # zero-fill
    return y
```
Sweep `p_loss` ∈ {0, 2, 5, 10, 15} % (Gnani cites up to 15 % on 2G). Log `{codec, bitrate, snr_db, noise_file, rir, p_loss, burst, seed}` per utterance into a JSONL manifest: this manifest *is* the reproducibility claim in the interview.

### 3.6 Ground-truth-rich synthetic calls ("SynthCall-IN")
Script 200–500 utterances per language with controlled entities (₹ amounts in lakh/crore wording, 10-digit phones, OTPs, dates, UPI IDs, IFSC) and Hinglish switch points tagged `<tag …>`; render with Timbre (two voices per dialogue, speed 0.85–1.15, `language` explicit so numbers read natively); push through §3.1. You now have exact text, exact entity values, exact speaker turns and exact utterance end-times (for endpointing latency). Caveat for the write-up: TTS speech is cleaner and more regular than humans; always pair with Gramvaani/own recordings.

---

## 4. Evon hosting options

Evon v3.3 = Nemotron-3-Nano-30B-A3B derivative (hybrid Mamba2+MoE, ~3.5B active), BF16 weights 63.5 GB on disk, open on HF, no hosted API; community GGUF `luminenio/gnani-evon-v3.3-30B-A3B-GGUF` (gated repo; IQ4_XS 17.09 GiB, Q4_K_M 22.97, Q8_0 31.45) (see `05-models.md`). Thinking must be off (`enable_thinking=false`) for anything voice-shaped.

| Platform | GPU / RAM | Price | Est. single-stream decode | Setup effort | Notes / link |
|---|---|---|---|---|---|
| **Gnani playground / community ZeroGPU Space** | n/a | free | n/a (UI only) | none | Prompt prototyping only; not an API ([playground](https://playground.gnani.ai), [Space](https://huggingface.co/spaces/luminenio/gnani-evon-v3.3-chat)) |
| **Kaggle Notebooks** | 2×T4 16 GB (32 GB VRAM), 12-h sessions, **30 GPU-h/week free** | ₹0 | **25–50 tok/s [SPEC]** for IQ4_XS/Q4_K_S split across both T4s with llama.cpp (T4 = 320 GB/s, ~2 GB active weights/token at Q4, old arch, layer-split serialises GPUs) | medium: build llama.cpp CUDA, download 17 GiB GGUF (HF token), expose `llama-server` via cloudflared/ngrok | No vLLM (needs ≥A100-class + bf16). Fine for offline extraction and for recording a demo; brittle for live judging ([Kaggle docs](https://www.kaggle.com/docs/efficient-gpu-usage)) |
| **Google Colab free** | 1×T4 16 GB, ~12 GB RAM | ₹0 | too tight: 17 GiB GGUF > VRAM and > RAM **[SPEC]** | — | Skip; Colab Pro (~₹1k/mo, A100-40GB intermittently) would run Q8 GGUF **[SPEC]** |
| **HF Spaces ZeroGPU** | **48 GB slice of RTX Pro 6000 Blackwell** (`large`), 96 GB `xlarge` at 2× quota | free account: host 2 Spaces, **5 min GPU/day per visitor**; PRO $9/mo: 40 min/day, +$1 per 10 min; default 60 s per call | Q4–Q8 GGUF fits; speed unknown **[SPEC: 60–120 tok/s]** | medium: Gradio-only, `@spaces.GPU(duration=…)`, llama-cpp-python; precedent exists (luminenio Space) | Cold-start/VRAM-attach latency per call is the risk; perfect for a *recorded* 60-s demo and a public link ([ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu)) |
| **Modal** | A100-80GB $0.000694/s (**$2.50/h**), A100-40GB $2.10/h, H100 $3.95/h, L40S $1.95/h, A10 $1.10/h, T4 $0.59/h; per-second; **$30/month free credit** | ≈12 free A100-80GB hours/month | BF16 vLLM: Gnani measured **257 tok/s**, TTFT 302 ms on their endpoint; expect 100–150 tok/s single-stream on A100 **[SPEC]** | low–medium: `vllm serve gnani/gnani-evon-v3.3 --trust-remote-code --reasoning-parser nano_v3 --tool-call-parser qwen3_coder` in a Modal function with a volume for weights (63.5 GB download once) | **Best "real" option**: scale-to-zero, OpenAI-compatible endpoint for Pipecat `OpenAILLMService` ([Modal pricing](https://modal.com/pricing)) |
| **RunPod** | A100 80GB PCIe **$1.19/h community** / $1.59 secure; H100 PCIe $1.99/$2.89; L40S $0.79; **RTX 4090 24 GB $0.34**; **RTX A6000 48 GB $0.33**; network storage $0.07/GB/mo | ₹3–5k ≈ $36–60 ≈ 30–50 A100-h or 100+ 4090-h | A100 BF16 as above; 4090 Q4_K_M ≈ "100+ tok/s class" (community claim, weak source) **[SPEC]**; A6000 Q8_0 fits (31.5 GB) | medium: pod + persistent volume; must stop pods or the budget evaporates | Community cloud can be pre-empted; use for eval batches and demo recording ([RunPod pricing](https://www.runpod.io/pricing)) |
| **Vast.ai** | A100 80GB quoted $0.39–0.90/h by third parties; per-second billing; interruptible 50 % cheaper | cheapest | as above | medium–high (host reliability varies) | [vast.ai/pricing](https://vast.ai/pricing); third-party numbers via [tech-insider](https://tech-insider.org/runpod-vs-lambda-vs-vast-ai-2026/) |
| **Lambda** | A100 80GB $2.79/h (8× only), H100 PCIe $3.29/h, GH200 $2.29/h | too coarse | — | — | Not for us ([Lambda pricing](https://lambda.ai/pricing)) |
| **CPU laptop** | no GPU (gfx90c iGPU), RAM unknown | ₹0 | 32 GB-RAM box: ~5–10 tok/s Q4 **[SPEC]**; a 16 GB laptop cannot hold the 17 GiB file | low | Offline batch extraction only |

Reference speeds (measured, not ours): BF16 on Gnani's endpoint 257 tok/s decode, TTFT 302 ms at 1K prompt ([release notes](https://introducing-evon-v3-3-llm.netlify.app/)); base Nemotron-3-Nano Q4_K_M on M4 Max 86 tok/s, pp512 1,213 tok/s, 24.4 GB ([llama.cpp discussion #20421](https://github.com/ggml-org/llama.cpp/discussions/20421)); UD-Q4_K_XL on DGX Spark 63.6 tok/s ([NVIDIA forum](https://forums.developer.nvidia.com/t/help-running-nemotron-3-nano-30b-a3b-fp8-on-dgx-spark-gb10/354771?page=2)). Base-model GGUF sizes for sanity: Q4_K_M 24.66 GB, IQ4_XS 18.13 GB ([bartowski](https://huggingface.co/bartowski/nvidia_Nemotron-3-Nano-30B-A3B-GGUF)); the Evon quant needs the extended 163K-token vocab, so use the luminenio files or re-quantise yourself (llama.cpp ≥ b7423 has `nemotron_h`).

**Plan:** prototype prompts on the playground → run eval batches on Kaggle (free) → host the demo endpoint on Modal with free credit (vLLM, thinking off) → keep an OpenAI-compatible fallback (Groq, as Gnani's own Pipecat example does) behind a flag.

---

## 5. Measurement plan templates

Tools: `jiwer` 4.x (WER/CER/MER/WIL, `process_words`, `visualize_alignment`, transforms `Compose/RemovePunctuation/ToLowerCase/Strip/ReduceToListOfListOfWords`, RapidFuzz C++ core; empty ref+hyp → 0 error since 4.0) ([jiwer docs](https://jitsi.github.io/jiwer/)); `whisper-normalizer` (BasicTextNormalizer with `preserve_marks=True` for Indic combining marks; MalayalamNormalizer; MIT) ([PyPI](https://pypi.org/project/whisper-normalizer/)); `indic-nlp-library` `IndicNormalizerFactory` for nukta/chandrabindu/NFC variants; Vistaar `evaluation.py` ([GitHub](https://github.com/AI4Bharat/vistaar)); `PIER` ([GitHub](https://github.com/enesyugan/PIER-CodeSwitching-Evaluation)); `pyannote.metrics` for DER; `speechbrain` ECAPA or Resemblyzer for speaker-similarity cosine.

Gnani's house rules to copy ([benchmark guide](https://www.gnani.ai/resources/research/how-to-benchmark-stt-api-indian-languages), [deep-dive](https://www.gnani.ai/resources/research/benchmarking-indic-asr-models-a-technical-deep-dive)): WER + CER with S/D/I/H breakdown; **CER for Dravidian**; **dataset-level aggregation** (sum edits / sum ref words), never mean of per-utterance WER; NFC before tokenising; 200 utts/condition for shortlisting, **400+ for ±1 pt at 95 % CI**; tiers >20 / 15–20 / <15 dB SNR; **8 kHz, never upsampled**; separate code-switch set; 50–100 domain terms; double-annotate 10 % (>95 % agreement); P95 latency **under concurrency**; diarization = % words attributed to the right speaker; no composite score.

### T1 — WER/CER vs SNR × codec (Noise Canceller core)
Grid: codec ∈ {16k clean, G.711, AMR-NB 12.2, AMR-NB 4.75, GSM-FR, Opus 12k 10 % loss} × SNR ∈ {∞, 20, 15, 10, 5, 0, −5} × noise ∈ {Vaani events, MUSAN babble, DEMAND traffic} × Prisma mode ∈ {REST verbatim, Batch, **Batch `with_denoise`**, WS telephony preset}. Sources: Gramvaani eval 3 h (real), Kathbath-noisy Hindi slice, SynthCall-IN. Normalise both sides identically (NFC, strip punctuation incl. danda `।`, collapse spaces, lower-case Latin; **score numerals in verbatim only**, ITN separately in T2). Report curves + S/D/I and a "denoise gain" per SNR. Bootstrap CI over utterances (1,000 resamples). N ≥ 200 per cell; prioritise 3 codecs × 4 SNRs to keep credits sane.

### T2 — Entity accuracy (ITN, bias_list, TN read-back)
Entities: ₹ amounts (incl. lakh/crore, paise), 10-digit phones, OTP/PIN 4–6 digits, dates, times, UPI IDs, IFSC/PAN. Metrics: exact-match entity accuracy, digit error rate (CER on digit strings), currency-format correctness, slot-level F1. Arms: `format=verbatim` vs `transcribe` vs `itn_native_numerals=true`; `bias_list` on/off for brand/scheme names at `bias_score` 1.0/1.5; `substitution_map` for known confusions. Round-trip arm: Timbre reads the ITN output back (`language` explicit) → human/ASR check that TN said "two lakh forty thousand". Caveat: ITN documented for hi/en only.

### T3 — Code-switch metrics (Mixed Vibes)
On MUCS Hi-En test (5.18 h, word-level English ratios available in the dianavdavidson mirror), HiACC, SynthCall-IN Hinglish, plus Gramvaani incidental English. Metrics: overall WER; **PIER** with points-of-interest = Latin-script/English tokens (script-based auto-tagging or `<tag>` manual tags); **switch-point MER** = MER inside a ±0.5 s window around each annotated boundary (Gnani's definition; needs word timings → use forced alignment of the reference or SynthCall-IN's known boundaries); **transliteration-invariant WER** (map hypothesis Latin↔Devanagari English with IndicXlit before scoring) to separate script choice from recognition errors. Buckets by English-word ratio (0–20 / 20–40 / 40–60 %). Compare `hi-IN` vs `en-IN` vs undocumented `multi_lang_codes` **[VERIFY]**.

### T4 — Streaming latency, endpointing, barge-in
Instrument a raw `websockets` client: log `t_frame_sent` per 1024-byte frame, `t_processing`, `t_transcript`, server `latency`, `audio_duration_ms`. Ground-truth end-of-speech from SynthCall-IN (known) or a reference VAD on the clean source. Report p50/p95/p99 of: (a) server-reported `latency`; (b) wall-clock EOS→final; (c) decomposition `≈ x-min-silence-ms + network + model`. Sweep `x-min-silence-ms` 300/500/800 and `x-vad-threshold` 0.5/0.7 at 8 kHz vs 16 kHz; count **premature endpoints** (one reference utterance → ≥2 segments) and **merged utterances**; measure **short-utterance drop rate** ("haan", "nahi", "theek hai") vs `x-min-segment-ms`/`x-min-speech-ms` at each SNR. Concurrency: 5/10/20 parallel sessions, P95. **Barge-in** (Pipecat `GnaniTTSService`): loop Timbre output into the mic path, inject user speech at t0, measure t(TTS stops) − t0 and false-barge rate under noise; definitions follow standard voice-agent metrics (barge-in detection latency, true/false barge-in rate, endpointing latency, TTFT/TTF) ([Hamming guide](https://hamming.ai/resources/voice-agent-evaluation-metrics-guide)). Remember the 15-min session cap and finals-only transcripts.

### T5 — Diarization (Batch, 2 speakers)
Build RTTM from `segments[].start_time/end_time/speaker_id`; DER via `pyannote.metrics` (collar 0.25 s) and **cpWER** (concatenated min-permutation WER) and Gnani's "% words to correct speaker". Sources: SynthCall-IN two-voice dialogues (exact turns), IndicVoices conversational, own two-phone recordings. Arms: `with_denoise` on/off, overlap fraction, same-gender vs mixed voices. Note `segment_id` is 0 everywhere in the docs' sample; key on index.

### T6 — TTS and voice clone
Objective only (solo dev, no MOS panel): speaker-similarity cosine (ECAPA) clone-vs-reference; **Timbre→(§3 chain)→Prisma round-trip WER** as intelligibility-under-telephony per voice/speed/sample-rate; TN correctness checklist on the Timbre normalisation page's known issues (OTP compression, 14+ digit runs). Clone reference from IndicVoices-R/OpenSLR TTS speakers (consented, licensed) rather than real people.

### T7 — Evon in the loop
TTFT and tokens/s with `enable_thinking=false`, short `max_tokens`; **output-script validation rate** (Gnani asks you to verify script downstream); schema-valid JSON rate on field extraction with one retry; compare to Groq fallback on the same prompts. This directly addresses Gnani's stated "not yet for real-time voice" gap ([release FAQ](https://introducing-evon-v3-3-llm.netlify.app/)).

**Publishing rule:** report deltas and curves for *our* pipeline; no competitor rows; label everything "measured by us on N utterances, dates, settings".

---

## 6. Idea seeds

Each seed names the load-bearing Gnani models, the award fit, a 60-s demo scene, the headline number it can produce, and the biggest risk. Starred (★) = the three strongest.

### ★ S1. Line Noise Lab (reproducible telephony-stress harness)
- **Motivation:** nobody outside Gnani can see how Indic STT degrades across codec × SNR × packet loss; Gnani's own guide says vendors hide this. Build the open harness.
- **Gnani models:** Prisma REST + WS (8 kHz telephony preset) + Batch `with_denoise`; Timbre to generate SynthCall-IN.
- **Award fit:** Noise Canceller; interview depth.
- **60-s scene:** play one Gramvaani clip clean → G.711 → AMR-NB 4.75 at 0 dB with cattle/diesel noise; live WER ticker per arm; flip `with_denoise` and watch the recovered words light up; show the JSONL manifest + seed that regenerates it.
- **Headline number:** "WER degrades X pts from 16k-clean to AMR-NB-4.75@5 dB; denoise recovers Y pts; telephony VAD preset cuts dropped 'haan/nahi' by Z %" (N≥200/cell, bootstrap CI).
- **Biggest risk:** EULA on publishing benchmark results → publish deltas only, confirm with organisers. Credits: 6 codecs × 7 SNRs × 200 utts is ~8k calls; prune the grid.

### ★ S2. Phone-a-Form + Paisa Proof (entity-first form filling over a 2G line)
- **Motivation:** scheme/KYC forms fail on amounts, phone numbers, dates; ITN + TN read-back + extractive LLM is exactly the Gnani stack's strength (ITN rules for lakh/crore, ₹, 10-digit phones; Timbre TN reads IDs digit-by-digit).
- **Gnani models:** Prisma WS (`format=transcribe`, `bias_list` for scheme names, `substitution_map`), Timbre (`language` explicit, `mulaw` 8 kHz out), Evon (extractive QA → JSON fields, thinking off) with schema validation; optional clone for a trusted "sahayak" voice.
- **Award fit:** Real-world impact; Mixed Vibes (Hinglish amounts: "do lakh rupees transfer karna hai"); Main Character if run in ta/te/kn.
- **60-s scene:** caller on a simulated AMR-NB 4.75 kbps line dictates PM-Kisan details in Hinglish; fields fill live; Timbre reads back "₹2,40,000 … 98765 43210" in native cadence; caller says "nahi, chaalis nahi, chauvanne" → correction; final JSON.
- **Headline number:** entity exact-match accuracy at 8 kHz AMR-NB vs clean; digit error rate; end-to-end turn p95.
- **Biggest risk:** ITN only hi/en; Evon instruction-following is weak (IndicIFEval 47/29) → constrain to extraction + retry; Evon hosting cost.

### ★ S3. Echo Test (Timbre→phone line→Prisma round-trip as an intelligibility meter)
- **Motivation:** unexpected use: use the STT to grade the TTS (and vice versa). Which of the 42 voices, speeds and sample rates survive µ-law/AMR-NB/noise best? Nobody publishes "phone-line intelligibility per voice".
- **Gnani models:** Timbre (all voices, speed 0.85–1.15, 8–48 kHz, mulaw/alaw containers), Prisma REST/Batch, voice clone (does a clone survive the line as well as a stock voice?).
- **Award fit:** Jugaad Genius; also informs every IVR builder which voice to pick.
- **60-s scene:** heat-map of voice × channel round-trip WER animates in; click a cell to hear clean vs degraded; recommendation card "for AMR-NB 2G calls use Urmila at 0.95×".
- **Headline number:** "voice X keeps round-trip WER at a % under AMR-NB-4.75@5 dB vs b % for voice Y; speed 1.15 costs c pts on the phone".
- **Biggest risk:** TTS-to-STT WER conflates both models' errors (say so; use a clean-16k control column); mild EULA question since it ranks Gnani's own voices (internal to Gnani, likely fine) **[VERIFY]**.

### S4. Kisan Call Mirror (two-leg regional-language helpline assist)
- **Motivation:** Kisan Call Centre-style calls in ta/te/kn with 2-speaker structure; live diarization is not in the WS, so run one WS session per leg (agent, farmer).
- **Gnani models:** 2× Prisma WS at 8 kHz (one language each → also handles a Hindi agent + Tamil farmer), Batch diarization for the post-call record, Evon extractive QA over scheme PDFs, Timbre regional voice.
- **Award fit:** Main Character; real-world.
- **Headline number:** per-leg p95 latency; cpWER/speaker-attribution accuracy vs Batch diarization; answer-grounding rate.
- **Risk:** two sessions double credits; Evon latency.

### S5. Sahi Sunna (SNR-adaptive front-end)
- **Motivation:** VAD headers are fixed per connection and the docs give presets by environment; estimate SNR live (noise floor in the first 2 s) and (re)connect with the matching preset; switch Batch `with_denoise` for archives.
- **Gnani models:** Prisma WS presets, Batch denoise.
- **Award fit:** Noise Canceller.
- **Headline number:** dropped-short-utterance rate and WER at 0–5 dB with adaptive vs default preset.
- **Risk:** reconnect gap; gain may be small → measure first (T4).

### S6. Switchboard (code-switch error microscope)
- **Motivation:** WER hides switch-point failure (PIER paper: 20 % MER vs 34 % at switch points). Visualise where Hinglish breaks and whether `bias_list` of English domain words fixes it.
- **Gnani models:** Prisma REST (`hi-IN`, `en-IN`, `multi_lang_codes` if it works), `bias_list`, Timbre Poorvi (`hi-en`) for synthetic switch-heavy test lines.
- **Award fit:** Mixed Vibes.
- **Headline number:** PIER and switch-point MER on MUCS/HiACC/SynthCall-IN by English-ratio bucket; Δ from bias_list.
- **Risk:** MUCS is lecture speech, not phone; `multi_lang_codes` undocumented.

### S7. Dadi ki Kahani (consented voice clone for family storytelling)
- **Motivation:** 20-s grandparent sample → clone reads regional-language children's stories with TN-correct numbers/dates; a consent + watermark-disclosure flow baked in.
- **Gnani models:** voice-clone embeddings + VC TTS (8–44.1 kHz), Prisma for the "record your consent sentence" step.
- **Award fit:** Jugaad Genius / Main Character.
- **Headline number:** speaker-similarity cosine vs reference; round-trip WER of cloned vs stock voice.
- **Risk:** ethics and policy around cloning; clone quality from phone-grade 8 kHz samples; whether VC accepts `language` is unknown **[VERIFY]**.

### S8. Shor Shield (noise-aware live compliance)
- **Motivation:** extend Gnani's real-time compliance tutorial with per-segment SNR so alerts carry confidence; measure false-alert rate vs SNR.
- **Gnani models:** Prisma WS + `substitution_map` for disclosure phrases.
- **Award fit:** Noise Canceller (incremental).
- **Headline number:** disclosure-detection recall/false-alarm by SNR band.
- **Risk:** looks like the tutorial; needs S1's harness anyway.

### S9. Jugaad IVR Bridge (real phone, real codec)
- **Motivation:** demo on an actual call: Exotel Voicebot applet streams **16-bit slin 8 kHz mono PCM base64**, chunks in multiples of 320 bytes (min 3.2 KB=100 ms), events `connected/start/media/dtmf/stop/mark/clear` ([Exotel](https://support.exotel.com/support/solutions/articles/3000108630-voicebot-applet)); Twilio Media Streams send `audio/x-mulaw` 8 kHz with `mark`/`clear` for barge-in ([Twilio](https://www.twilio.com/docs/voice/media-streams/websocket-messages)). Re-frame to Prisma's 1024-byte frames; Timbre `mulaw` out.
- **Gnani models:** Prisma WS 8 kHz, Timbre mulaw, Pipecat serializers.
- **Award fit:** best 60-s demo; Noise Canceller on a real line.
- **Headline number:** real-call EOS→reply p95; barge-in latency.
- **Risk:** Indian DID numbers need KYC/paid plans; Twilio trial limits **[SPEC]**; fall back to WebRTC + §3 simulated channel.

### S10. Evon-on-ZeroGPU (free Indic brain for the voice loop)
- **Motivation:** Gnani says Evon isn't ready for real-time voice; show the measured gap and a free hosting path (48 GB ZeroGPU slice, Q4/Q5 GGUF, thinking off).
- **Gnani models:** Evon (self-hosted) + Prisma + Timbre.
- **Award fit:** Jugaad Genius.
- **Headline number:** TTFT and tok/s on ZeroGPU vs Modal A100; script-validity rate.
- **Risk:** 5 min/day quota, cold start, third-party quant quality unknown.

### S11. Boli Map (dialect × noise robustness map for Hindi)
- **Motivation:** Lahaja (83 districts), Vaani-Benchmark (104 districts, 3 refs), Gramvaani metadata (dialect/region) → WER by region and SNR; where does `bias_list` help?
- **Gnani models:** Prisma REST/Batch.
- **Award fit:** Main Character; interview depth.
- **Headline number:** regional WER spread; multi-reference WER on Vaani-Benchmark.
- **Risk:** publishing absolute WERs (EULA); heavy downloads.

### S12. Negatives & Non-speech (false-transcript rate)
- **Motivation:** real lines carry hold music, IVR tones, breathing; `addyo07` ships 200 "expect empty" negatives and Vaani-Noise 154 h of non-speech. Measure Prisma's insertion rate on pure noise at each level and VAD setting (Batch fails silent files after 3 retries, WS emits nothing on zeros).
- **Award fit:** Noise Canceller; cheap and surprising.
- **Headline number:** hallucinated words per minute of non-speech by preset.
- **Risk:** low wow alone; fold into S1.

**Why S1+S2+S3:** S1 is the measurement spine every other seed needs and is the natural Noise Canceller entry; S2 is the product story (real-world, Hinglish entities, regional) and exercises the most Gnani surface (ITN, bias, TN read-back, Evon, clone); S3 is the cheapest genuinely unexpected use of the stack and generates a shareable artefact (voice × channel heat-map). Together they produce ~6 defensible numbers for the interview and reuse one SynthCall-IN corpus and one telephony chain.

---

## 7. Verify-live checklist (first API session)
- Does REST accept 8 kHz µ-law-decoded WAV without re-encoding artefacts; confirm "auto-converted to 16 kHz mono" path vs sending raw 8k to WS.
- `multi_lang_codes` format and Hinglish output script.
- WS: is zero-padding a valid flush; `x-partials`; real `latency` at 8k vs 16k from Delhi.
- Batch: turnaround for a 5-min file with/without `with_denoise`; diarization quality on SynthCall-IN.
- VC: response shape, `language` support, quality from an 8 kHz sample.
- Credit cost per STT second / TTS character (nothing documented) → size the T1 grid.
- Organisers (Discord): is publishing our own WER curves acceptable under the EULA.
