# R7 — Three days on one A100 40 GB: what a GPU sprint can add to Kaam ka Parcha

> Research ticket R7 for the Gnani "Great Indian AI Internship Challenge" (deadline 10 Nov 2026). The question, verbatim: *"I will have GPU for 3 days, GPU A100 40GB NVIDIA, what can I do more on this idea to win more?"* Researched 2026-10-05. Methods: read the repo at `main` (`15212db`, clean tree): `AGENTS.md`, `README.md`, `CONTEXT.md`, `docs/ideas/{council-verdict,spec}.md`, `docs/gates.md`, `docs/demo.md`, `docs/remaining-work-handoff.md`, `aidlc-docs/registry.md` and efforts 001–005, `docs/research/R4-technical-angles.md`, `docs/notes/{01,02,05}-*.md`, `.scratch/closed-loop-voice-sealing/issues/*`, and `src/parcha/` (`extract.py`, `workflow.py`, `config.py`, `app.py`, `gnani.py`, `lab/*`). `curl` against the Hugging Face API for repo, gating, file-size and derivative data. WebSearch and WebFetch for everything else. **No Gnani API or other paid API was called, and no code was changed.** Legend: **[SPEC]** = my inference or estimate, not a published fact; **[VERIFY]** = cheap to check live, do it before relying on it.

---

## 1. Executive summary

1. **The step that decides the rupee figures is not a Gnani model today.** `Extractor` in `src/parcha/extract.py` is an OpenAI-compatible client. Its defaults (`config.py`, `.env.example`) point at **Groq `llama-3.3-70b-versatile`**. `EXTRACTOR_PROVIDER` is read but never used, there is no rules extractor, and `require_extractor()` blocks intake and re-ask without it (`app.py:187,223`). On the 4.8 s clip, the card shows ₹450 only because this Llama call picked the verbatim-pass evidence over Prisma's ITN output `04:30 100` (effort 005). The GPU is most useful for **putting Evon v3.3 in that slot and proving it with the first real extraction eval**. That makes Prisma, Timbre and Evon all load-bearing and removes a "genuine use" risk.
2. **Evon on one A100 40 GB (verified 2026-10-05):** the BF16 weights (31.75 B params, 13 shards, **63.5 GB**) do **not** fit. The only ready-made checkpoint that fits is the community **GGUF Q8_0 (31.45 GiB)**, served by **llama.cpp** built with `nemotron_h_moe` support. vLLM supports the architecture, but **no Evon FP8, AWQ or GPTQ checkpoint exists**. You would have to make one with llm-compressor. FP8 runs as weight-only W8A16 Marlin on Ampere, about 33 GB and tight [SPEC]. W4A16 would be about 18 GB [SPEC]. The KV cache is about **6 KB/token** (only 6 of the 52 layers are attention), so context length is not the constraint.
3. **No access lead time.** `gated:false` on both `gnani/gnani-evon-v3.3-30B-A3B` and `luminenio/gnani-evon-v3.3-30B-A3B-GGUF` (HF API, 2026-10-05). The contest page still says "by request", so file a request anyway as a formality (§9).
4. **Fine-tuning:** 16-bit LoRA needs about **60 GB** (Unsloth), so it is out on this card. 4-bit QLoRA is plausible: a NeMo AutoModel recipe reports about 20 GB peak at load and about 35 GB in training. The tooling is fragile, though: an unresolved Unsloth MoE merge failure, `mamba-ssm`/`causal-conv1d` version pins, and Evon needs transformers ≥ 5.3. Treat it as a **conditional stretch** and run it only if the base-model eval shows a gap.
5. **Do not expect a denoiser to help Prisma.** Enhancement artefacts are the main cause of ASR degradation (Iwamoto et al., Interspeech 2022). A Dec-2025 study found enhanced audio was **worse than the noisy original in 40/40 configurations** across four modern ASR models. DeepFilterNet accepts **48 kHz only**. Gnani's own Batch `with_denoise` is the native option to test. This is CPU and credit work, not GPU work, and it is low priority.
6. **Best pick: "Evon cross-examines Prisma"** (ideas #1 + #2 below). Evon replaces Groq. A deterministic Hindi-numeral grammar plus an Evon reconciler compares the `transcribe` and `verbatim` passes, and any disagreement triggers a targeted Timbre re-ask. Success metric: **false-confirmation rate** (a wrong amount presented as ready) on noisy transcripts, reported as an own-pipeline delta. That is evidence for Noise Canceller and a strong interview story.
7. **Spend credits before the GPU arrives.** Rendering and transcribing test audio, recording real speakers, and writing the eval runner all run on the laptop. Do them first, so every GPU hour goes to Evon compute on cached transcripts. Sprint budget: **about 1,150–1,700 credits** (§11), leaving at least 3,000 for the Line Noise Lab grid and judging.
8. **What must survive after the GPU is returned:** GGUF quants calibrated on domain text and checked against Q8_0, a frozen eval JSONL, a gold-first synthetic corpus, the recorded live demo, a hosting kit (ZeroGPU Space, Modal, Kaggle) and a deterministic CPU fallback. Never fall back to a non-Gnani LLM.
9. **Rule and claim risks found:** (a) Groq/Llama sits in the critical path; (b) `docs/demo.md` puts **unmeasured** numbers on the proof card ("+20.0% part recovery", "96.0% short-reply flush recovery", "800 synthetic telephony turns"), which is a Rule 7 "misleading demo" risk; (c) `data/generalization_corpus_v1.json` labels 74 hand-written text cases with provenance such as `consented_workshop_mechanic_recording`, but no audio exists and no code runs any extractor on them, so the gate row "74/74 PASS" cannot be reproduced; (d) any non-Gnani ASR, TTS or LLM in the product, or any public cross-engine number, adds risk.
10. **Most of what decides an award needs no GPU:** record real speakers (Oct 7 gate), run the Lab grid (Oct 19), get Discord consent for public numbers (Oct 10), and correct the demo proof card. The GPU sprint adds to that work and does not replace it.

---

## 2. Repo state: built, proven, unproven

### 2.1 Built and working (offline-tested)

| Area | What exists | Evidence |
|---|---|---|
| App and state | FastAPI workshop, customer and verify views; revisioned `SessionStore` (`draft → review → awaiting_reply → fallback_ready → confirmed`); frozen Pydantic models | `src/parcha/app.py`, `session.py`, `schema.py` |
| Money safety | `amount_paise` accepts only `int` or `None` (rejects bool, str, float); a tie between duplicate labels sets the amount to `None` and forces review | effort 003 `construction.md` §1.1–1.2 |
| Prisma | REST `/stt/v3` dual-pass: `transcribe` (ITN) and `verbatim` with a 65-word `bias_list`; captures confidence | `gnani.py`, `vocabulary.py`, `workflow.py:110-116` |
| Timbre | `timbre-v2.5`, `hi-IN`, 8 kHz µ-law; ffmpeg G.711/AMR-NB chain with recorded engine noise at 5 dB | `gnani.py`, `audio.py`, `workflow.py:202-265` |
| Customer loop | Phrasal prompt ("Haan, theek hai"); confidence < 0.65 or ≥ 2 retries goes to digital fallback | effort 004 (#3, #4), `workflow.py:267-470` |
| Sealing | One canonical audit-manifest SHA-256 shown in the PDF and embedded as `transcripts.json`; QR to `/verify/{id}`; DPDP consent log | `artefact.py`, effort 003 §1.3, #5, #6 |
| Line Noise Lab | Codec × SNR × loss × impulse grid, 29 s REST chunking, CER/WER/amount/hallucination metrics, public delta export that fails closed without consent | `lab/runner.py`, `noise.py`, `metrics.py`, `report.py`, effort 005 |
| Tests | **196 offline tests passing** (effort 005); the README badge still says 170 | effort 005 `construction.md` |

### 2.2 Weak or unproven (verified against code)

| # | Weakness | Evidence | Matters for |
|---|---|---|---|
| W1 | **Non-Gnani LLM decides the money.** Groq Llama-3.3-70B is the default and only extractor and is mandatory for intake. The README calls it "optional". | `config.py:44-50`, `.env.example`, `app.py:187`; grep finds no use of `extractor_provider` | Rule 3 "genuine use"; claim accuracy |
| W2 | **ITN money error on the only noisy clip.** `transcribe` returned `फ्रंट ब्रेक पैड 04:30 100 …` for "saade chaar sau" (₹450), in **both** the clean and `impact_wrench` conditions. Probably "साढ़े चार" parsed as the time 4:30 and "सौ" as 100 [SPEC on mechanism]. | effort 005 `construction.md` | Noise Canceller, Mixed Vibes |
| W3 | **No real human recordings.** `mechanic_in_garage_noise.wav` is *synthesised* speech mixed with a Wikimedia Volvo engine. The Oct 7 gate (10 real lines beside a scooter) is pending. | effort 002 `construction.md:18`, `docs/gates.md` | Every audio claim |
| W4 | **The "generalisation corpus" has never been run.** 74 cases, all romanised, `transcript_verbatim == transcript_normalized` in 74/74 (unlike real Prisma output: Devanagari, ₹ digits, ITN errors). Provenance labels name recordings that don't exist. No script feeds it to any extractor; tests only score hand-built cards. | `data/generalization_corpus_v1.json`, `scripts/generate_generalization_corpus.py`, `tests/test_generalization_corpus.py` | Gate row "74/74 PASS" not reproducible |
| W5 | **HTTP 429.** 2 of 4 back-to-back calls were throttled. The client keeps only the status code (no body, no `Retry-After`) and never retries. Intake makes 2 sequential STT calls, so one 429 fails the whole intake. | effort 005; `gnani.py:_check_response` | Live demo reliability |
| W6 | **Unmeasured numbers on the proof card**: "+20.0% part recovery", "96.0% short-reply flush recovery", "800 synthetic telephony turns". | `docs/demo.md` §1 (00:53–01:00), S12 | Rule 7 "misleading demos" |
| W7 | **Lab grid never run; SynthCall audio never rendered.** The manifest exists, the WAVs do not. `make_synthcall.py` assumes 1 credit per TTS call, but the measured rate is 0.05 cr/char (≈2–3 cr per line). | `data/synthcall_manifest.jsonl`, `scripts/make_synthcall.py`, `docs/gates.md` §1 | Credit planning, Noise Canceller |
| W8 | **No consent for public numbers.** The Discord answers are "Pending"; the README example uses a placeholder `consent-ref`. | `docs/gates.md` §5 | Every public number |
| W9 | **Extractor payload isn't Evon-ready.** It sends no `chat_template_kwargs` (Evon reasons by default) and no `response_format` schema. `_parse_json` grabs the first `{` to the last `}`, which reasoning text can break. | `extract.py:334-338, 366-385` | Evon swap (#1) |

### 2.3 Gate ledger (`docs/gates.md` + council)

| Gate | Status | Note |
|---|---|---|
| Oct 4 single-call credit probe | **PASS** | 0.20 cr/s STT; 0.05 cr/char TTS (one probe each) |
| Oct 5 generalisation suite "74/74, 0 false confirmations" | **Claimed PASS, not reproducible** | W4: no runner, no audio |
| Oct 5 E2E sealed parcha ₹650 | PASS on 1 synthetic-speech clip | Same clip's ITN pass gives `04:30 100` (W2) |
| Oct 6 credit-grid forecast | Open | Straightforward (`early_gates.py`) |
| Oct 7 garage amounts ≥ 7/10 (real scooter) | **Open** | W3 |
| Oct 8 Timbre→G.711→Prisma ≥ 9/10 | Open | |
| Oct 10 haan/nahi drop ≤ 10%; hallucination ≤ 1 word/clip | Open | Idle-engine sample returned 0 words (effort 005, n=1) |
| Oct 10 Discord: synthetic-filming + public deltas | **Open** | W8 |
| Oct 12 casting | Open | |
| Oct 15 `bias_list` A/B (verbatim) | Open | |
| Oct 19 Lab v0 grid + WS flush ≥ 95% | **Open** | W7 |

### 2.4 Award positioning (max one award per entrant)

| Award | Fit today | Missing | What the GPU can add |
|---|---|---|---|
| **Noise Canceller** (council's primary) | Medium: simulated 8 kHz leg, impulse lab code, one noisy clip | Real recordings, the Lab grid, a fix for the W2 class of error, consent for public numbers | Money-safety layer (#2) with a measured false-confirmation delta; adversarial numeral corpus (#3). The acoustic side stays CPU and credit work |
| **Mixed Vibes** (secondary) | Medium: Hinglish dual-pass ITN | Any measurement on real code-mixed Prisma output (mixed Devanagari/Latin); no Tanglish/Benglish | Evon extraction on script-mixed transcripts; optional Tanglish/Benglish numeral leg (#7) |
| **Solo Ninja** | Strong on breadth | Evidence quality; the non-Gnani core (W1) | "One student self-hosts the whole Artha stack (Prisma + Timbre + Evon)" |
| **Jugaad Genius** | Low–medium | One distinctly unexpected use | "Evon cross-examines two Prisma modes" (#2); "Prisma checks Timbre's read-back before it plays" (echo check, #10, no GPU) |
| **Demo Day Drop** | Storyboard only | Real footage; honest proof card | Record the live three-model demo during the GPU window (#4) |
| Real Deal | Council: don't claim (garages aren't among the named users) | — | — |
| Main Character | Not applicable (Hinglish) | A regional-language leg | #7 makes a weak case at best |
| Crowd Favourite | Social only | — | One shareable angle post: "one GPU ran the whole sovereign stack" |
| Small Town, Big Build | Depends on the college **[VERIFY]** | — | — |
| Two-Person Army | Not applicable (solo) | — | — |

---

## 3. Evon v3.3 on one A100 40 GB: verified facts

### 3.1 Identity

| Field | Value | Source |
|---|---|---|
| Repo | `gnani/gnani-evon-v3.3-30B-A3B` (alias `gnani/gnani-evon-v3.3`); `gated:false`; 10,571 downloads, 53 likes; last modified 2026-09-09 | [HF API](https://huggingface.co/api/models/gnani/gnani-evon-v3.3-30B-A3B) |
| Weights | BF16 31,749,969,344 params (+2,944 F32); 13 safetensors shards totalling **63.5 GB** (12 × ~4.99 GB + 3.57 GB) | [HF tree API](https://huggingface.co/api/models/gnani/gnani-evon-v3.3-30B-A3B/tree/main) |
| Architecture | `NemotronHForCausalLM` (`nemotron_h`): 52 layers = 23 Mamba2 + 23 MoE + 6 attention; 128 routed experts top-6 + 1 shared; hidden 2688; 2 KV heads × 128; vocab 163,072; 128K context | `docs/notes/05-models.md` (from `config.json`) |
| Card | Hardware "NVIDIA H100 80GB, H200, A100", Linux; transformers ≥ 5.3.0, vLLM ≥ 0.12.0, SGLang; thinking off via `enable_thinking=False` / `chat_template_kwargs`; temperature 0.6, top_p 0.95 | [model card](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B) |
| Derivatives | **Exactly one**: `luminenio/gnani-evon-v3.3-30B-A3B-GGUF` (`gated:false` now; R4 recorded it as gated on 2026-10-04) | [HF derivatives API](https://huggingface.co/api/models?filter=base_model:gnani/gnani-evon-v3.3-30B-A3B), [GGUF API](https://huggingface.co/api/models/luminenio/gnani-evon-v3.3-30B-A3B-GGUF) |
| GGUF details | Q8_0 31.45 GiB · Q6_K 31.38 · Q5_K_M 24.40 · Q4_K_M 22.97 · IQ4_XS 17.09 · Q2_K 16.81. Fallback types are used for 134/401 tensors, so low-bit files shrink little. Built at llama.cpp commit `8b4b3558f1459c13e4aa38d5c94d306a00dc6acd` and needs `nemotron_h_moe`. "Quantization loss has not been measured against the BF16 source model." Smoke-tested only (A10, 10 layers offloaded, 2K context). | [GGUF card](https://huggingface.co/luminenio/gnani-evon-v3.3-30B-A3B-GGUF) |
| Hosted API | None found. Competitor entries self-host with vLLM (e.g. `kural`: `vllm serve … --max-model-len 32768`, thinking off) | [kural](https://github.com/Mirdumurugesan/kural), `05-models.md` §1.5 |

### 3.2 Precision × runtime fit matrix (A100 40 GB ≈ 40 GiB; Ampere SM 8.0, **no native FP8 tensor cores**)

| Option | Weight size | Fits 40 GB? | Runtime | Ready-made? | Verdict |
|---|---|---|---|---|---|
| BF16 | 63.5 GB | **No** | vLLM, SGLang, transformers | Yes | Only with CPU offload, which is far too slow [SPEC] |
| BF16 + `--cpu-offload-gb ~30` | 63.5 GB | Technically | vLLM | Yes | Weights stream over PCIe every step; unusable for eval at scale [SPEC] |
| **GGUF Q8_0** | **31.45 GiB** | **Yes, ~5–6 GiB headroom** [SPEC] | **llama.cpp** (`llama-server`, OpenAI-compatible, `json_schema` → GBNF) | **Yes** | **Primary path.** A third-party sizing site puts Q8_0 at 38.6 GB total at 8K context ([canitrun](https://canitrun.dev/models/nemotron-3-nano/), method not stated) |
| GGUF Q5_K_M / Q4_K_M / IQ4_XS | 24.40 / 22.97 / 17.09 GiB | Yes, easily | llama.cpp | Yes | Deployment candidates after the GPU; validate against Q8_0 (§8 #5) |
| FP8 (self-made, llm-compressor) | ≈ 33 GB [SPEC]; proxy: NVIDIA's base-model FP8 is **32.68 GB** | Tight [SPEC] | vLLM, which on Ampere runs it as **weight-only W8A16 FP8 Marlin** ([vLLM FP8 doc](https://docs.vllm.ai/en/latest/features/quantization/llm_compressor/fp8/)). FP8 MoE on Ampere needed vLLM ≥ 0.9 ([Qwen3 FP8 thread](https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/discussions/2)) | **No** Evon FP8 exists | Optional. NVIDIA lists **A100** as supported hardware for its Nemotron-3-Nano FP8, which uses selective quantization with attention and the Mamba layers feeding it kept in BF16; AIME25 89.1 → 87.7 ([NVIDIA FP8 card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8)) **[VERIFY on Evon]** |
| W4A16 (AWQ/GPTQ, self-made) | ≈ 18 GB [SPEC]; proxies: base AWQ **17.84 GB**, GPTQ **19.75 GB** | Yes, comfortable | vLLM Marlin (Ampere supported per [vLLM hardware table](https://docs.vllm.ai/en/latest/features/quantization/index.html)) | **No** Evon W4A16 exists; base-model AWQ was tested on vLLM 0.15 on H100/B200/RTX PRO 6000, **not A100** ([stelterlab AWQ](https://huggingface.co/stelterlab/NVIDIA-Nemotron-3-Nano-30B-A3B-AWQ)) | Optional, for high-throughput batch only. llm-compressor has `nemotron_h` loading support and sequential onloading for single-GPU quantisation ([v0.14.0 notes](https://github.com/vllm-project/llm-compressor/releases/tag/0.14.0), [sequential onloading](https://docs.vllm.ai/projects/llm-compressor/en/latest/examples/big_models_with_sequential_onloading/)). Needs about 64 GB of host RAM [SPEC] |
| bitsandbytes 4-bit | ≈ 17–20 GB | Yes | transformers | n/a | Use it for QLoRA training only; slow for inference [SPEC] |

### 3.3 Memory math

| Item | Value | Basis |
|---|---|---|
| KV cache | 6 attn layers × 2 KV heads × 128 dim × 2 (K, V) × 2 B ≈ **6 KB/token**, so 32K tokens ≈ 0.2 GB | arithmetic on `config.json` values [SPEC] |
| Mamba state | 23 layers × 64 heads × 64 × 128 × 4 B (fp32) ≈ **48 MB per sequence** | `05-models.md` §1.2 [SPEC] |
| Embedding + LM head | 163,072 × 2,688 × 2 B ≈ 0.88 GB each (Evon's vocab is about 32K tokens larger than base Nemotron's) | arithmetic [SPEC] |
| Q8_0 on A100 40 GB | 31.45 GiB weights + ~1–2 GiB compute buffers + ~0.2 GiB KV (`-c 32768 -np 8`) ≈ 33–34 GiB | [SPEC] **[VERIFY with `nvidia-smi`]** |

### 3.4 Throughput: known numbers vs estimates

| Number | Context | Source |
|---|---|---|
| 257.3 tok/s decode, TTFT 302 ms at a 1K-token prompt | Gnani's own endpoint, BF16, reasoning mode, single request, GPU unstated | release notes, via `05-models.md` §1.4 |
| 116.9 tok/s, Q6_K, A100 40 GB | Third-party site, methodology not stated | [canitrun](https://canitrun.dev/models/nemotron-3-nano/) (weak) |
| 86 tok/s Q4_K_M (M4 Max); 63.6 tok/s UD-Q4_K_XL (DGX Spark) | Base Nemotron 3 Nano | R4 §4 |
| **80–150 tok/s single-stream; ~300–600 tok/s aggregate with `-np 8`** | llama.cpp Q8_0 on A100 | **[SPEC]**; measure in block B1 |
| **≈2–3 s per job-card extraction** (~700 prompt tokens, ~200 output tokens, thinking off) | | **[SPEC]** |
| 5,000 generated dictations × ~200 tokens = 1 M tokens ≈ **0.5–1 h** at 300–600 tok/s | Corpus generation (#3) | **[SPEC]**; vLLM is not needed for this volume |

### 3.5 Runtime decision

- **Primary: llama.cpp `llama-server` with `-ngl 99` (all layers on GPU) and the Q8_0 model.** It is known to load `nemotron_h_moe`, needs no quantisation work, exposes OpenAI-compatible `/v1/chat/completions`, and turns `response_format: json_schema` into grammar-constrained decoding ([guide](https://www.simplified.guide/llama-cpp/server-constrain-json-schema)). The same artefact family (GGUF) runs after the GPU is gone. Turn thinking off with the template kwarg or reasoning flag **[VERIFY exact flag in your build]**.
- **Optional: vLLM with a self-made W4A16.** Only worth it if batch generation becomes the bottleneck, which it won't at about 1 M tokens [SPEC]. Hard cap: 2 h of setup.
- **Skip on this card:** BF16 vLLM/SGLang (needs 80 GB) and transformers BF16.

---

## 4. Fine-tuning Evon on 40 GB (LoRA / QLoRA)

| Fact | Value | Source |
|---|---|---|
| 16-bit LoRA VRAM | "around **60GB**" | [Unsloth Nemotron 3 guide](https://unsloth.ai/docs/models/nemotron-3) |
| Official Unsloth notebook | Nemotron-3-Nano-30B-A3B SFT LoRA on an **A100 80 GB** Colab; router fine-tuning disabled by default; keep ≥ 75% reasoning data to preserve reasoning | same |
| 4-bit QLoRA, measured | NeMo AutoModel `force_hf`, streaming per-layer quantisation: **~20 GB peak at load, ~35 GB in training**; `out_proj` and `lm_head` kept out of 4-bit and out of LoRA; `attn_implementation: eager` | [NVIDIA forum (GB10)](https://forums.developer.nvidia.com/t/fine-tuning-nemotron-3-nano-30b-a3b-on-asus-ascent-gx10-gb10-dgx-spark-cuda-oom-at-load-box-freezes-4-bit-qlora-fix/372434) |
| QLoRA recipe | seq 4096, batch 1 × grad-accum 8, r=16, α=16, targets `q,k,v,o,gate,up,down`; needs `mamba-ssm` + `causal-conv1d` (CUDA) and bitsandbytes | [AceCloud](https://acecloud.ai/blog/nemotron-3-nano-multi-gpu-fine-tuning/) |
| Version pins | `mamba_ssm` 2.2.5, `causal_conv1d` 1.5.2, torch 2.7.1/CUDA 12.8; "use a clean environment" | [DataCamp](https://www.datacamp.com/tutorial/fine-tuning-nvidia-nemotron-3-nano) |
| Known failure | LoRA **merge** fails on MoE expert tensors (`…experts.1.up_proj.SCB … do not match!`) with 8-bit loading; **unresolved** (Jan 2026) | [unsloth #3854](https://github.com/unslothai/unsloth/issues/3854), [discussion #3810](https://github.com/unslothai/unsloth/discussions/3810) |
| Evon-specific | Requires **transformers ≥ 5.3**, while those Unsloth reports used 4.56. Extended 163K vocab. Fine-tuning guidance on the card: none | [model card](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B) |
| Serving an adapter later | llama.cpp: `convert_lora_to_gguf.py` → `llama-server --lora adapter.gguf` (hot-swappable) | [GGUF-my-LoRA](https://huggingface.co/blog/ngxson/gguf-my-lora) — **[VERIFY `nemotron_h` support in `convert_lora_to_gguf`]** |

**Verdict.** Within about a day it is **feasible but fragile**. Training compute on 2–3K examples is small (≈1–4 h [SPEC]); the environment is the risk. Run it only if block B2 shows Evon (prompted, schema-constrained) misses the dev-split targets. Cap setup at 2 h. An adapter is durable only if it converts to GGUF **or** merges and re-quantises on CPU with ≥ 64 GB RAM [SPEC].

---

## 5. Speech enhancement before Prisma: helps or hurts?

| Evidence | Finding | Source |
|---|---|---|
| Iwamoto et al., Interspeech 2022 | Enhancement **artefacts**, not residual noise, are the main cause of ASR degradation. Adding back part of the noisy input ("observation adding") raises the signal-to-artefact ratio and improves ASR. | [ISCA](https://www.isca-archive.org/interspeech_2022/iwamoto22_interspeech.html), [arXiv 2201.06685](https://arxiv.org/pdf/2201.06685) |
| "When De-noising Hurts", Dec 2025 | MetricGAN+ before Whisper, Parakeet, Gemini Flash 2.0 and Parrotlet-a: noisy audio beat enhanced audio in **all 40 configurations**, by **+1.1 to +46.6 pts** absolute semWER | [arXiv 2512.17562](https://arxiv.org/abs/2512.17562) |
| "Perceptually Better, Semantically Worse", EMNLP 2026 | MetricGAN+ **more than doubles** LLM output divergence (0.318 vs 0.135) despite better PESQ; PESQ correlates weakly (ρ = −0.467) | [arXiv 2608.30348](https://arxiv.org/abs/2608.30348) |
| Practitioner view | "A denoiser tuned for perceptual quality routinely strips the cues an acoustic model relies on and raises WER." Proposal closed "not planned", no measurements | [kesha-voice-kit #988](https://github.com/drakulavich/kesha-voice-kit/issues/988) |
| Vendor blog (weak) | DeepFilterNet-class front-ends claim 20–40% relative WER gains "in genuinely loud conditions" | [Forasoft](https://www.forasoft.com/blog/article/speech-recognition-accuracy-noisy-environments) |
| DeepFilterNet facts | MIT/Apache-2.0; "only wav files with a sampling rate of 48kHz are supported"; DFN2 is the default model, DFN3 is newest | [GitHub](https://github.com/Rikorose/DeepFilterNet) |
| Gnani-native option | Batch `with_denoise`: "speech enhancement for every file", +25% processing time, same billing | `docs/notes/02-speech-apis.md:187` |
| Prior | Prisma is trained on 14M h of telephonic audio with codec augmentation, so enhancement is more likely to hurt than help **[SPEC]**. Upsampling 8 kHz to 48 kHz for DFN adds no band information **[SPEC]** | `05-models.md` §2 |

**If you test it** (CPU and credits, not GPU): use 3 arms (raw / Batch `with_denoise` / DFN3 mixed back at 0.3 for observation adding) × about 60 clips at G.711 and AMR-NB with 5 dB engine noise, scoring **amount exact-match**. Expect no gain. Publish only own-pipeline deltas, and keep a "DFN fixes Prisma" framing out of public posts.

---

## 6. Rule compatibility and claim risks

| Risk | Severity | Where | Mitigation |
|---|---|---|---|
| Non-Gnani LLM (Groq/Llama) decides amounts in the critical path | **High** | W1 | Evon primary + deterministic fallback; delete the Groq default from `.env.example`/README; keep Groq only for private internal baselines |
| Unmeasured proof-card numbers | **High** | W6 `docs/demo.md` | Replace with measured own-pipeline deltas (N, settings, date) or remove |
| Corpus provenance labels imply recordings that don't exist | Medium | W4 | Relabel `provenance: hand_written_text`; regenerate the corpus with real Prisma transcripts |
| Running Whisper, IndicConformer or MMS as a second opinion, aligner or baseline | **High** | any GPU idea | Don't. It replaces or benchmarks a Gnani model and creates competitor comparisons |
| Distilling extraction into a small non-Gnani LLM (Qwen, Gemma, Llama) for CPU | **High** | GPU idea | Don't. Use Evon GGUF plus a deterministic grammar instead |
| Generating demo or test audio with a non-Gnani TTS | Medium | corpus ideas | Use Timbre (voices + `vachana-vc-v1` clone) and consenting human speakers |
| Publishing Evon vs other-LLM tables, absolute CER/WER, or "denoiser beats Prisma" | **High** | reports/posts | `report.py` guard; own-pipeline deltas only; Discord consent first |
| Redistributing Evon quants or adapters | Low | §8 #5 | Ship `LICENSE`, `LICENSE-NVIDIA`, `NOTICE` (Apache-2.0 + NVIDIA Open Model License per `05-models.md`); name it "community quant, not official" |
| "By request" wording vs `gated:false` | Low | §3.1 | File the request or ask on Discord anyway; record the date |
| Cached Evon replies in a demo while the host is down | Medium | post-GPU | Disclose on screen as "replayed Evon output recorded <date>" (Rule 7) |
| QLoRA'd or quantised Evon still counts as "Evon v3.3"? | Low [SPEC] | submission | Name it precisely: "Evon v3.3 (self-hosted Q8_0 GGUF [+ LoRA])"; ask on Discord |

---

## 7. Idea long list

Load = how load-bearing the Gnani models are in the idea (1–5).

| # | Idea | GPU role | Award | Load | Verdict |
|---|---|---|---|---|---|
| 1 | **Evon Sovereign Extractor**: Evon replaces Groq for card and correction extraction (thinking off, `json_schema`-constrained, evidence-quote checks kept) plus the first real extraction eval | Hosts Evon Q8_0; runs evals | All (genuine use), Solo Ninja | 5 | **Top** |
| 2 | **Rupee Cross-Examiner**: deterministic Hindi-numeral grammar on the verbatim pass + Evon reconciler between `transcribe` and `verbatim`; disagreement triggers a targeted Timbre re-ask | Evon reconciler eval | **Noise Canceller**, Mixed Vibes, Jugaad | 5 | **Top** |
| 3 | **Gold-first SynthCall v2**: sampled gold JSON → Evon verbalises mechanic-style Hinglish (colloquial numerals, distractor numbers, corrections) → grammar re-parse validator → 3–5K text cases; subset goes through Timbre → codec → Prisma | Batch generation | Noise Canceller / interview | 4 | **Top** |
| 4 | **Live three-model demo + voice-loop latency**: record the 60 s video and a long walkthrough with Prisma + Timbre + Evon live; TTFT, tok/s and end-to-end breakdown with thinking off (Gnani's FAQ says Evon is "not yet" ready for real-time voice) | Hosts Evon during the shoot | **Demo Day Drop**, Solo Ninja | 5 | **Top** |
| 5 | **Post-GPU hosting kit**: imatrix GGUF quants calibrated on domain text (Q5_K_M/Q4_K_M/IQ4_XS), checked against Q8_0 on the frozen eval; ZeroGPU Space, Modal function, Kaggle notebook; deterministic fallback | Computes imatrix; runs quant ladder eval | Enables every claim at judging | 4 | **Top** |
| 6 | QLoRA adapter on Evon for extraction (conditional on a B2 gap) | Training | Interview depth | 5 | Stretch |
| 7 | Tanglish/Benglish leg: Evon normalises spoken Tamil/Bengali amounts (no Prisma ITN for ta/bn); Timbre ta/bn read-back | Evon eval | Mixed Vibes (named), Main Character | 5 | Stretch (8–14 h + credits) |
| 8 | Reply-intent: Evon generates 2–3K Hinglish confirmation/correction paraphrases to expand and test `classify_reply` (lexicon stays CPU) | Generation | Noise Canceller (short replies) | 3 | Good filler for idle GPU time |
| 9 | Enhancement A/B (raw / `with_denoise` / DFN3 + observation adding) | None needed | Noise Canceller | 3 | Do on CPU later, low priority (§5) |
| 10 | **Echo check**: Prisma transcribes the degraded Timbre read-back before playback; if the amount doesn't survive, re-synthesise slower or with another voice | None | Jugaad Genius, Noise Canceller | 5 | Strong, but no GPU; ~1 cr per read-back |
| 11 | Multi-view Prisma consensus (raw / 8 kHz-normalised / `with_denoise`) agreement-gates amounts | None | Noise Canceller | 5 | Credits ×2–3; after #2 |
| 12 | Run the Line Noise Lab grid (100 × 2 × 4) | None | Noise Canceller | 5 | **Must do**, credit-bound (≈960–1,132 cr forecast) |
| 13 | Real-speaker session: 3–5 consenting people × 10 scripted lines beside a running scooter | None | All audio claims | 5 | **Must do** before the GPU |
| 14 | Self-made W4A16/FP8 Evon for vLLM throughput | Quantisation | Interview | 4 | Optional (§3.5) |
| 15 | Evon "dispute explainer" at pickup (sealed parcha vs new bill, spoken in Hindi via Timbre) | Hosts Evon | Real Deal-ish | 4 | Low; needs live Evon after the GPU |
| 16 | Evon writes read-back text for Timbre | Hosts Evon | — | 3 | **No**: Evon is weak at summarisation (CrossSum-in chrF 4.67) and the read-back is deterministic today |
| 17 | Distil a small non-Gnani extractor for CPU | Training | — | 1 | **Reject** (§6) |
| 18 | Whisper/IndicConformer second opinion or forced alignment | Inference | — | 1 | **Reject** (§6) |
| 19 | Open-source TTS to diversify noisy test voices | Inference | — | 2 | **Reject** (use Timbre + clone + humans) |
| 20 | Train your own denoiser or ASR adapter | Training | — | 1 | **Reject** (replaces Prisma's job; months of work) |

---

## 8. Ranked shortlist

Scoring: award impact 1–5; Gnani load-bearing 1–5; human h = attended hours (pre-GPU + GPU); GPU h = wall-clock GPU time, much of it unattended; credits = Gnani API credits.

| Rank | Idea | Award target | Award impact | Gnani load | Human h | GPU h | Risk | Survives after GPU | Credits |
|---|---|---|---|---|---|---|---|---|---|
| **1** | Evon Sovereign Extractor + real eval (#1) | Every award's "genuine use"; Solo Ninja | 4 | 5 | 8–10 (3 pre) | 6–8 | Low–Med (llama.cpp build, prompt quality) | Prompt + schema, frozen eval JSONL, GGUF choice; live only via the #5 hosts | 0 (cached transcripts) |
| **2** | Rupee Cross-Examiner (#2) | **Noise Canceller** (primary), Mixed Vibes, Jugaad | 5 | 5 | 9–12 (5 pre) | 4–6 | Med (review rate may rise) | **Grammar runs on CPU forever**; reconciler via #5; false-confirmation delta | ~600–800 (shared with #3, pre-GPU) |
| **3** | Gold-first SynthCall v2 (#3) | Noise Canceller / interview evidence | 3 | 4 | 5–7 (2 pre) | 2–4 (unattended) | Low | **Dataset** (text + audio-transcript pairs), splits by template family | Included in #2 (+~400 optional second batch) |
| **4** | Live three-model demo + latency (#4) | **Demo Day Drop**, Solo Ninja | 4 | 5 | 5–6 | 3–6 | Low | **Video**, latency table, B-roll | ~150–200 |
| **5** | Post-GPU hosting kit (#5) | Keeps 1, 2 and 4 alive for judging and interviews | 3 | 4 | 4–6 | 3–5 | Med (ZeroGPU/Modal quirks) | **Quants on HF**, Space/notebook/Modal app, fallback mode | 0 |
| 6 | QLoRA adapter (#6) | Interview depth | 2 | 5 | 6–10 | 8–12 | **High** | Adapter (if GGUF-convertible) | 0 |
| 7 | Tanglish/Benglish leg (#7) | Mixed Vibes | 3 | 5 | 8–14 | 3–4 | Med–High | Eval + demo clip | ~300 |

**Single best pick: #1 + #2 shipped together as "Evon cross-examines Prisma".** #1 is the prerequisite: it removes the W1 rule risk and gives the project its first real extraction numbers. #2 is the layer that can win an award: it attacks the observed `04:30 100` failure class and produces a public-safe own-pipeline metric (false confirmations before vs after). The grammar half survives with no GPU at all. #3 feeds both; #4 and #5 make the result visible and durable.

**How #2 works (design sketch, [SPEC]):**
1. **Grammar(V)**: parse amounts from the verbatim pass. Handles Devanagari and romanised units (ek…ninyanve), multipliers (sau/hazaar/lakh), fractional prefixes (saade +½, sava +¼, paune −¼, dedh 1½, dhai 2½), digits, and spans. Time-like tokens in T (`hh:mm` next to "सौ"/100) are flagged as **ITN-artefact suspects**.
2. **Evon**: given T, V and the grammar candidates, return per-item amounts with V-quotes, schema-constrained.
3. **Auto-accept** an amount only if Grammar(V) == Evon **and** (T agrees **or** T's disagreement matches a known ITN-artefact pattern). Otherwise set `amount_paise=None` and send a field-level re-ask via Timbre ("Brake pad kitne ka? Sirf rakam boliye").
4. **Metrics**: false-confirmation rate (wrong amount presented ready), review rate (its cost), and exact-amount recovery after re-ask, each with its N.

---

## 9. Before the GPU arrives (so no GPU hour is wasted)

| When | Task | Hours | Output | Notes |
|---|---|---|---|---|
| T-3d | **Confirm the box**: A100 40 GB SXM or PCIe, driver/CUDA ≥ 12.4, **disk ≥ 250 GB** (BF16 63.5 + Q8_0 34 + Q4/Q5 ~45 + BF16-GGUF 64 for imatrix quants), **host RAM ≥ 64 GB** (128 ideal for conversion/merge), Linux, internet to `huggingface.co`, SSH port-forwarding, tmux, Docker or conda, exclusive use, exact 72 h start time | 0.5 | Spec sheet | If RAM < 64 GB or disk < 150 GB: skip BF16, imatrix-from-BF16 and QLoRA (use the luminenio quants) |
| T-3d | **Evon access**: `gated:false` today, so zero lead time. Still click "request" if a form appears and post a Discord note ("self-hosting Evon v3.3 Q8_0 for extraction"). Ask on Discord: hosted Evon for participants? does a quantised/LoRA Evon count as "Evon v3.3"? | 0.5 | Dated record | Also chase the two pending Oct 10 questions |
| T-3d | **Fix the demo-claims risk**: strike the unmeasured proof-card numbers from `docs/demo.md` (W6) | 0.5 | Honest storyboard | No GPU needed |
| T-3d…T-1d | **Extractor plumbing** (CPU, with TDD): configurable `chat_template_kwargs={"enable_thinking":false}`, `response_format` json_schema (card + correction schemas), `repetition_penalty`, provider `evon`; strip `<think>…</think>` defensively; keep the evidence-quote validation | 2–3 | PR, offline tests | Test against Groq or a tiny local GGUF **for plumbing only** |
| T-3d…T-1d | **Hindi-numeral grammar** module + unit tests (saade/sava/paune/dedh/dhai, Devanagari + romanised, hazaar/lakh, distractors: years, vehicle numbers, "4 baje") | 3–4 | `parcha/numerals.py` (CPU fallback forever) | Core of #2 |
| T-2d | **Eval runner** `scripts/eval_extractor.py`: any OpenAI-compatible endpoint, cache keyed by (model file SHA, prompt version, input hash), per-case JSONL, metrics from `lab/eval_corpus.py`, fixed dev/holdout/challenge splits | 2–3 | Runner + dry run on 74 cases | Fixes W4 |
| T-2d | **Gold-first sampler + verbaliser prompt + validator** (template-only mode works without Evon) | 2 | 300 template lines now; Evon variants later | Feeds #3 |
| T-2d | **Prisma/Timbre batch runner with cache and throttle**: one request at a time, ≥ 1 s spacing, jittered exponential backoff on 429 (log `Retry-After` if present), cache by audio SHA-256 + params, `--max-credits` | 2 | Fixes W5 for batch work | |
| T-2d…T-1d | **Spend credits now**: (a) record **3–5 consenting speakers × 10 lines** beside a scooter (Oct 7 gate); (b) render **~120 gold-first lines** with Timbre; (c) Prisma `transcribe` + `verbatim` on each at G.711 and AMR-NB 4.75 with 5 dB engine noise; cache everything | 3 | ~160 audio cases with cached transcript pairs | ≈ 970 credits (§11) |
| T-1d | **GPU scripts ready**: llama.cpp CUDA build script (`-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=80`, fallback commit `8b4b355`); `hf download luminenio/gnani-evon-v3.3-30B-A3B-GGUF --include "*Q8_0*"` (and Q4_K_M, Q5_K_M); optional BF16 `hf download gnani/gnani-evon-v3.3-30B-A3B`; `hf_transfer` on; pinned QLoRA env file (transformers ≥ 5.3, peft, bitsandbytes, `mamba-ssm`, `causal-conv1d`) | 1.5 | `gpu/` bootstrap scripts | Untested pieces are flagged **[VERIFY]** |
| T-1d | **Hosting skeletons**: Gradio + llama-cpp-python ZeroGPU Space (needs an HF account > 30 days old with verified email); Modal function; Kaggle notebook | 1.5 | Repos ready to receive the chosen GGUF | |
| T-1d | **Prompt prototyping without a GPU** on the Gnani playground (UI only; don't call its internal API) | 1 | v0 prompts | `05-models.md` §1.5 |
| T-0 | **Demo shot list** for the live-Evon scenes; props, scooter, consent forms | 1 | Shoot plan for B9 | |

Pre-GPU total ≈ **20–24 h** of focused work. Everything else in §10 assumes it is done.

---

## 10. The 72-hour GPU plan (6-hour blocks; H0 = first SSH login)

A = attended, U = unattended (queue jobs before sleeping). Attended total ≈ 38–42 h.

| Block | Mode | Goal | Tasks | Outputs | Kill criteria → fallback |
|---|---|---|---|---|---|
| **B1 H0–6** | A | Evon serving | `nvidia-smi`; start parallel downloads (Q8_0 first, then Q4_K_M/Q5_K_M, then BF16 only if disk/RAM allow); build llama.cpp; `llama-server -m Q8_0 -ngl 99 -c 32768 -np 8 --jinja` with thinking off; smoke test JSON-schema output; measure TTFT, tok/s, VRAM; SSH tunnel so the laptop app uses `EXTRACTOR_BASE_URL=http://localhost:8080/v1` | Live Evon endpoint; perf log | Build fails > 90 min → prebuilt CUDA binary/container **[VERIFY tag]** or commit `8b4b355`. Q8_0 OOM → Q5_K_M. Download < 20 MB/s → skip BF16 (drop imatrix-from-BF16 and QLoRA) |
| **B2 H6–12** | A | First real extraction numbers (#1) | Run the 74-case corpus + ~160 cached Prisma transcript pairs; ≤ 3 prompt versions **on dev only**; freeze; run holdout/challenge **once**; private Groq baseline on the same cases | `eval/evon_v1/*.jsonl`, private report | Schema-valid < 98% → flatten schema / retry once. Dev amount accuracy below target after 3 versions → mark QLoRA go-candidate. **Never tune on holdout** |
| **B3 H12–18** | U | Corpus v2 (#3) + calibration data | Evon verbalises 3–5K gold-first cases (`-np 8`, temp 0.8); grammar validator filters; split by template family; then `llama-imatrix` over ~200K tokens of workshop Hinglish (computed on Q8_0 **[VERIFY acceptable]**) | `data/synthcall_v2/*.jsonl`, `imatrix.dat` | Validator pass < 60% → tighten prompt in the morning. imatrix fails → use the luminenio quants as-is |
| **B4 H18–24** | A | Rupee Cross-Examiner (#2) | Implement reconciler prompt + acceptance rule; evaluate on the noisy cached transcripts (incl. the W2 type) and the adversarial challenge split; compare arms: ITN-only / current dual-pass / + grammar / + grammar + Evon. Laptop in parallel: optional second Timbre + Prisma batch on Evon-generated lines | False-confirmation and review-rate deltas (private) | Reconciler raises false confirmations, or review rate > 50% on clean cases → reconciler may only *flag*, never edit; ship grammar-only |
| **B5 H24–30** | A | Quant ladder (#5) | Convert BF16 → GGUF (CPU) and quantise Q5_K_M/Q4_K_M/IQ4_XS with the domain imatrix; run the **frozen** eval on Q8_0 vs each | Deploy-quant decision; upload to HF (private first) with license files | Q4 loses > 2 pts amount accuracy **or** adds any false confirmation → deploy Q5_K_M/Q8_0 (fits the 48 GB ZeroGPU slice) |
| **B6 H30–36** | A | QLoRA go/no-go (#6) | **Go only if** BF16 is present, a dev gap exists (amount accuracy < target or false confirmations > 0), and the env builds in ≤ 2 h. Else run stretch #8 (reply paraphrases) or #7 | Decision log | Env not training by H34 → abandon, log the negative result |
| **B7 H36–42** | U | Train or generate | QLoRA: 4-bit, exclude `lm_head`/`out_proj`/router, r=16, seq 1024, 2–3K gold-first examples, 1–2 epochs. Or: reply-paraphrase generation + eval | Adapter checkpoint or paraphrase set | OOM at seq 1024 → seq 512 → stop. NaN loss → stop |
| **B8 H42–48** | A | Adapter verdict | Eval the adapter (PEFT, or llama.cpp `--lora` after `convert_lora_to_gguf` **[VERIFY nemotron_h]**); keep only if dev **and** holdout improve ≥ 2 pts with no new false confirmations | Keep/discard record | Not convertible to GGUF → keep as an interview artefact only; don't deploy |
| **B9 H48–54** | A | Live demo shoot (#4) | Record the 60 s video and a 3–5 min walkthrough with all three models live; on-screen telephony-simulation disclosure; latency HUD (Prisma ×2, Evon, Timbre) | Raw footage, latency table | Mic flaky → pre-recorded WAV inputs (disclosed). Endpoint flaky → re-take; never fake |
| **B10 H54–60** | A | Hosting kit live (#5) | Deploy the chosen GGUF to the ZeroGPU Space and/or Modal and/or Kaggle; point the app at it with the A100 idle; verify the deterministic fallback; write the private report | Working post-GPU endpoint(s) | No host works → fallback mode + recorded video, disclosed |
| **B11 H60–66** | U/A | Final frozen run | Re-run the full frozen eval on the deploy quant; package JSONL + configs + commit SHA; draft own-pipeline deltas (public only after Discord consent; `report.py` guard) | Evidence bundle | Anything regressed → revert to the B5 choice |
| **B12 H66–72** | A | Teardown | Copy artefacts off the box with SHA-256 checksums (GGUFs, imatrix, adapter, datasets, eval, footage); delete HF token and API keys from the box; stop the instance | Durable artefacts (§12) | — |

---

## 11. Gnani credit budget

Rates from `docs/gates.md` (single probes, **[VERIFY]** with a second probe): Prisma **0.20 cr per audio-second per pass**; Timbre **0.05 cr per character**. Balance ≈ 4,980 [SPEC]: 4,990.0 after the effort-003 E2E, minus ~10.4 cr estimated in effort 005 (provider billing not inspected).

| Item | Calc | Credits | When |
|---|---|---|---|
| Timbre render, gold-first lines | 120 × ~55 chars × 0.05 | 330 | Pre-GPU |
| Prisma on those lines | 120 × 5 s × 2 passes × 2 conditions (G.711+5 dB, AMR-NB 4.75+5 dB) × 0.20 | 480 | Pre-GPU |
| Real-speaker clips | 40 × 5 s × 2 passes × 2 conditions (raw, G.711+5 dB) × 0.20 | 160 | Pre-GPU |
| Demo takes | ~20 full flows × ≈9 cr (intake 2 + read-back ~6 + reply 0.6) | 180 | B9 |
| **Lean sprint total** | | **≈1,150** | |
| Optional second batch (Evon-generated lines) | 60 × (2.75 TTS + 4.0 Prisma) | 405 | B4 |
| Optional enhancement A/B (§5), later | 60 × 5 s × 3 arms × 0.20 | 180 | After |
| **Standard sprint total** | | **≈1,700** | |
| Keep in reserve: Line Noise Lab grid | 100 × 2 × 4 forecast | 960–1,132 | Oct 19 gate |
| Keep in reserve: judging and interview demos, re-asks | | ≥ 500 | Nov |
| **Remaining after standard sprint + reserves** | 4,980 − 1,700 − 1,132 − 500 | **≈1,650 buffer** | |

The Evon side costs **zero credits**: it is not covered by programme credits (`CONTEXT.md`) and runs on cached transcripts.

---

## 12. What survives after the GPU is gone

| Artefact | Where it lives | Runs without the A100? | Used for |
|---|---|---|---|
| Hindi-numeral grammar + acceptance rule | repo (`src/parcha/`) | **Yes, CPU** | Live fallback, Noise Canceller story |
| Frozen eval JSONL (per case, per quant, per arm) + configs + commit SHA | repo (curated) / `var/` (raw) | Yes | Interview; own-pipeline deltas |
| SynthCall v2 text corpus + ~160 audio-transcript pairs | repo `data/` (synthetic only; human audio private under `var/`) | Yes | Regression set; future Lab runs |
| Domain-imatrix GGUF quants (+ license files) | HF (private, or public as "community quant") | Yes, on the hosts below | Live Evon at judging |
| QLoRA adapter (only if it won) | HF | Only via llama.cpp `--lora` or a merged GGUF | Interview |
| Recorded demo + walkthrough + latency table | Drive / YouTube unlisted | Yes | Demo Day Drop, posts, interviews |

**Post-GPU hosting options**

| Host | Cost | What fits | Est. per-extraction latency | Notes / source |
|---|---|---|---|---|
| Own HF **ZeroGPU** Space | Free (2 Spaces; account > 30 days, verified email); PRO $9/mo for 10 Spaces | 48 GB half RTX Pro 6000 → **Q8_0 fits** | ~2–4 s warm + GPU-attach delay [SPEC] | Gradio only; visitor quota **2 min (anon) / 5 min (free) / 40 min (PRO)** per day; 60 s default per call ([ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu)); precedent: luminenio IQ4_XS Space |
| **Modal** | **$30/month free**; A100-40GB **$0.000583/s (≈ $2.10/h)** → ≈ 14 free A100-h/month | Q8_0 (llama.cpp) or W4A16 (vLLM) | Warm 2–3 s; cold start minutes [SPEC] | Scale to zero; warm it for scheduled judging windows ([Modal pricing](https://modal.com/pricing)) |
| **Kaggle** 2×T4 | Free, 30 GPU-h/week (R4) | Q4_K_M / IQ4_XS split across GPUs | 25–50 tok/s → ~5–8 s [SPEC, R4] | 12-h sessions + tunnel; fine for scheduled demos |
| Laptop CPU | Free | This research machine: **31.6 GB RAM**, i5-1345U, Iris Xe, 70 GB free → IQ4_XS (17.09 GiB) or Q4_K_M (22.97 GiB) | 3–8 tok/s → 30–60 s [SPEC] | Offline batch only. R4 mentions a different dev machine (gfx90c), so check whichever machine you demo on **[VERIFY]** |
| Deterministic fallback | Free | — | ms | Review-heavy by design; disclose as "Evon offline" mode |
| Cached replay | Free | — | ms | Must be labelled as replayed (Rule 7) |

---

## 13. Do-not-do list for the GPU window

| Don't | Why |
|---|---|
| Run a non-Gnani ASR (Whisper, IndicConformer, MMS) or TTS anywhere in the product or in public numbers | Replaces or benchmarks Gnani; competitor-comparison ban (§6) |
| Distil the extractor into Qwen, Gemma or Llama for CPU | Same problem as W1, in a new place |
| Fight vLLM builds for more than 2 h | llama.cpp Q8_0 already covers inference *and* generation volume (§3.4) |
| QLoRA before a baseline eval exists | No way to show it helped; highest-risk item |
| Tune prompts, grammar or thresholds on holdout/challenge | Invalidates the only honest numbers (handoff doc rule) |
| Leave the GPU idle overnight | Queue B3/B7 jobs before sleeping |
| Put absolute CER/WER, Evon-vs-other-LLM, or "denoiser beats Prisma" in any post | `report.py` guard, EULA caution, Discord consent pending |
| Commit human audio, keys, or raw private outputs | `AGENTS.md` credentials rules; use `var/` |

---

## 14. Open questions / VERIFY list

1. GPU box: `nvidia-smi` memory (40,960 MiB?), driver/CUDA, disk, host RAM, egress speed to HF.
2. llama.cpp: current `master` loads `nemotron_h_moe`; exact flag to disable Evon thinking (`--chat-template-kwargs` vs reasoning budget); `json_schema` works with Evon's template.
3. imatrix computed on Q8_0 (BF16 doesn't fit VRAM) is acceptable for quantising from BF16 GGUF.
4. vLLM on Ampere: FP8 Marlin MoE and W4A16 Marlin MoE with `nemotron_h` Mamba layers (only if #14 is attempted).
5. `convert_lora_to_gguf.py` handles `nemotron_h` adapters.
6. Timbre credit cost per character (second probe); Prisma 429 policy (`Retry-After`?), and safe request spacing.
7. Discord: hosted Evon for participants? Does a quantised or LoRA'd Evon count? Public own-pipeline deltas OK? Scripted real-person filming counts as synthetic?
8. College tier (Small Town, Big Build eligibility).
9. Mechanism of `04:30 100` (ITN time-parse of "साढ़े चार") — confirm by looking at the cached verbatim transcript for the same clip.

---

## 15. Research log

### Search queries run (WebSearch)
| Query | What it gave |
|---|---|
| `Unsloth fine-tune Nemotron 3 Nano 30B-A3B LoRA VRAM` | Unsloth guide (60 GB 16-bit LoRA), merge-failure issue and discussion, NVIDIA HF thread, AceCloud QLoRA blog |
| `vLLM FP8 Marlin Ampere A100 weight-only MoE support` | FP8 Marlin PR #5975, vLLM FP8 docs, llm-compressor W8A16 issue, SGLang Ampere MoE issue, Qwen3 FP8 thread |
| `Nemotron-3-Nano-30B-A3B QLoRA 4-bit bitsandbytes fine-tuning 40GB GPU memory` | NVIDIA forum NeMo AutoModel QLoRA recipe (~20 GB load, ~35 GB train), DataCamp tutorial |
| `llm-compressor sequential onloading quantize 30B MoE single GPU W4A16 GPTQ Nemotron-H` | llm-compressor v0.14.0 (`nemotron_h` loading, GPTQ speedups), sequential onloading doc |
| `llama.cpp Nemotron 3 Nano 30B-A3B A100 tokens per second Q8_0 benchmark` | canitrun sizing/throughput (unverified method), bartowski GGUF, llama.cpp discussion #20421 |
| `vLLM nemotron_h NemotronHForCausalLM supported models quantization AWQ GPTQ Ampere` | vLLM quantisation hardware table; GPTQModel `nemotron_h` support note |
| `speech enhancement artifacts degrade ASR performance Iwamoto "How bad are artifacts"` | Iwamoto et al. 2022 (artefacts cause degradation; observation adding helps) and follow-ups |
| `DeepFilterNet front-end Whisper ASR WER noisy evaluation does denoising help or hurt` | Vendor blog (20–40% claim), kesha-voice-kit DFN3 evaluation issue, Interspeech 2024 SE-vs-ASR paper |
| `speech enhancement before robust ASR foundation model hurts WER study 2025` | arXiv 2512.17562 (40/40 worse), arXiv 2608.30348 (EMNLP 2026), arXiv 2607.11157 |
| `Gnani Evon v3.3 hosted API endpoint October 2026` | No official hosted endpoint; competitor repos (kural, boli-zero, Gnani-AI-Hackathon) self-host or substitute |
| `llama.cpp imatrix importance matrix quantization calibration data domain quality improvement llama-imatrix` | llama.cpp imatrix tool README; benefit largest at 2–4 bpw |
| `llama.cpp convert_lora_to_gguf --lora adapter llama-server hot swap LoRA GGUF` | GGUF-my-LoRA blog; `--lora` / `--lora-scaled` serving |
| `llama.cpp server json_schema response_format grammar constrained output OpenAI compatible` | `response_format` json_schema → GBNF in llama-server; thinking templates can interfere |

### API calls (curl, no auth)
| Call | What it gave |
|---|---|
| `huggingface.co/api/models/gnani/gnani-evon-v3.3-30B-A3B?expand[]=gated…` | `gated:false`, 10,571 downloads, BF16 31,749,969,344 params |
| `…/gnani-evon-v3.3-30B-A3B/tree/main` | 13 shards, sizes (sum 63.5 GB), tokenizer 20.8 MB |
| `huggingface.co/api/models?filter=base_model:gnani/gnani-evon-v3.3-30B-A3B` | Only one derivative: luminenio GGUF |
| `…/luminenio/gnani-evon-v3.3-30B-A3B-GGUF?expand[]=gated` | `gated:false` (changed since R4) |
| `huggingface.co/api/models?search=evon` | No other Evon repos (no FP8/AWQ/GPTQ) |
| `huggingface.co/api/models?search=Nemotron-3-Nano-30B-A3B` | Base-model quant ecosystem (NVIDIA FP8/NVFP4, AWQ, GPTQ, GGUF) |
| `…/tree/main` for NVIDIA FP8, RedHatAI FP8, stelterlab AWQ, TevunahAi GPTQ | Size proxies: 32.68 / 32.68 / 17.84 / 19.75 GB |

### URLs relied on (WebFetch)
| URL | What it gave |
|---|---|
| https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B | Hardware list, runtime versions, thinking toggle, sampling, no fine-tuning guidance |
| https://huggingface.co/luminenio/gnani-evon-v3.3-30B-A3B-GGUF | Quant sizes, llama.cpp commit, fallback tensors, no quality eval |
| https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8 | A100 listed as supported; selective FP8; AIME25 89.1 → 87.7; vLLM ≥ 0.12 |
| https://huggingface.co/stelterlab/NVIDIA-Nemotron-3-Nano-30B-A3B-AWQ | llm-compressor INT4; vLLM 0.15; tested on H100/B200/RTX PRO 6000 (not A100); experimental |
| https://docs.vllm.ai/en/latest/features/quantization/index.html | Marlin/AWQ/GPTQ on Ampere; FP8 W8A8 not on Ampere; GGUF supported |
| https://docs.vllm.ai/en/latest/features/quantization/llm_compressor/fp8/ | "Turing/Ampere GPUs are supported for W8A16 (weight-only FP8) utilizing Marlin kernels" |
| https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/discussions/2 | FP8 Marlin MoE on Ampere arrived around vLLM 0.9.0 (PR #16850) |
| https://github.com/vllm-project/llm-compressor/releases/tag/0.14.0 | `nemotron_h` fast loading; GPTQ ~15× faster, up to 30× on MoE |
| https://unsloth.ai/docs/models/nemotron-3 | 60 GB 16-bit LoRA; router disabled; A100-80GB notebook |
| https://github.com/unslothai/unsloth/issues/3854 | Unresolved MoE LoRA merge failure (8-bit, `.SCB` mismatch) |
| https://github.com/unslothai/unsloth/discussions/3810 | Same failure; no maintainer fix |
| https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16/discussions/17 | NVIDIA points to Megatron-Bridge and Unsloth for fine-tuning |
| https://forums.developer.nvidia.com/t/fine-tuning-nemotron-3-nano-30b-a3b-on-asus-ascent-gx10-gb10-dgx-spark-cuda-oom-at-load-box-freezes-4-bit-qlora-fix/372434 | QLoRA peaks ~20 GB load / ~35 GB train; exclusions |
| https://acecloud.ai/blog/nemotron-3-nano-multi-gpu-fine-tuning/ | QLoRA hyperparameters and dependencies |
| https://www.datacamp.com/tutorial/fine-tuning-nvidia-nemotron-3-nano | `mamba_ssm` 2.2.5 / `causal_conv1d` 1.5.2 pins |
| https://canitrun.dev/models/nemotron-3-nano/ | Q8_0 38.6 GB total at 8K; A100 40GB Q6_K 116.9 t/s (method unstated, weak) |
| https://github.com/ggml-org/llama.cpp/discussions/20421 | Only Apple-silicon numbers on the page; no A100 data |
| https://www.isca-archive.org/interspeech_2022/iwamoto22_interspeech.html | Artefacts drive ASR degradation; observation adding helps |
| https://arxiv.org/abs/2512.17562 | Enhancement worse in 40/40 configs, +1.1 to +46.6 pts |
| https://arxiv.org/abs/2608.30348 | Enhancement doubles LLM output divergence despite better PESQ |
| https://github.com/Rikorose/DeepFilterNet | 48 kHz only; MIT/Apache-2.0 |
| https://github.com/drakulavich/kesha-voice-kit/issues/988 | Practitioner warning; closed without measurement |
| https://modal.com/pricing | $30/month free; A100-40GB $0.000583/s |
| https://huggingface.co/docs/hub/spaces-zerogpu | 48/96 GB slices; daily quotas; hosting limits; Gradio-only |
| https://www.gnani.ai/internship | Must name Gnani models; synthetic data rule; Evon "by request"; one award max |
| https://www.gnani.ai/resources/blogs/great-indian-ai-internship-challenge-2026 | Award criteria wording; "every project must use Gnani AI Models/APIs" |
| https://github.com/Mirdumurugesan/kural | Competitor self-hosts Evon with vLLM, thinking off |
| https://www.forasoft.com/blog/article/speech-recognition-accuracy-noisy-environments | Vendor claim of 20–40% gain from DFN-class front-ends (weak) |
| https://huggingface.co/blog/ngxson/gguf-my-lora | LoRA → GGUF conversion and `--lora` serving |
| https://www.simplified.guide/llama-cpp/server-constrain-json-schema | `response_format` json_schema in llama-server |
| https://github.com/ggml-org/llama.cpp/tree/master/tools/imatrix | imatrix tool (search result; README not fetched) |
| https://docs.vllm.ai/projects/llm-compressor/en/latest/examples/big_models_with_sequential_onloading/ | Sequential onloading for single-GPU quantisation (search result) |

### Local evidence read (repo)
`src/parcha/{extract,workflow,config,app,gnani,vocabulary}.py`, `src/parcha/lab/{eval_corpus,noise,runner}.py`, `data/generalization_corpus_v1.json` (74/74 identical verbatim/normalized transcripts; provenance counts), `data/synthcall_manifest.jsonl`, `data/real_world_samples/real_world_manifest.json`, `docs/gates.md`, `docs/demo.md`, `aidlc-docs/efforts/00{2,3,4,5}-*/…`, `.scratch/closed-loop-voice-sealing/issues/*`, `git log` (HEAD `15212db`). Machine specs via `Get-CimInstance` (31.6 GB RAM, i5-1345U, Iris Xe).
