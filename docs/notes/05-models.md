# Gnani AI models in depth (Evon, Prisma, Timbre, Warp, and the rest)

> Researched 2026-10-04 with curl (HF API, raw files), Playwright, and WebSearch/WebFetch. No Gnani API was called.
> I opened the Evon playground page but sent no messages.
> API request/response details are in `02-speech-apis.md`. This file covers the **models**: specs, benchmark claims, how to run them, and what we can actually use.
> **[SPEC]** = my inference or speculation, not a published fact.

## TL;DR (decision-relevant)

1. **Evon v3.3 is NVIDIA Nemotron-3-Nano-30B-A3B with continued pretraining, an extended tokenizer, SFT and GRPO. It is not Qwen.** It is a Mamba2+Transformer hybrid MoE (`nemotron_h`): 30B total, about 3.5B active, 128K context, BF16, 11 languages (en + 10 Indic incl. **Odia**). [HF config](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/config.json), [NOTICE](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/NOTICE)
2. **The weights are effectively public now.** The HF API reports `"gated": false`, and an anonymous `resolve/` of a safetensors shard returns a 302 to the CDN with `user_id=public`. Marketing pages still say "by request". [HF API](https://huggingface.co/api/models/gnani/gnani-evon-v3.3-30B-A3B), [Artha page](https://www.gnani.ai/artha-sovereign-ai)
3. **The 5,000 hackathon credits do not cover Evon.** The developer docs and API (`api.vachana.ai`) expose only Prisma STT, Timbre TTS and voice cloning. I found **no public hosted Evon API**. A participant repo says it is "Google Gemini substitut[ing] until a hosted endpoint launches". [docs index](https://docs.gnani.ai/llms.txt), [Bolo repo](https://github.com/satyabrata-mishra/Gnani-AI-Hackathon)
4. **Free ways to use Evon without a GPU:** (a) Gnani's own **web playground**, <https://playground.gnani.ai> (no login, UI only, not an API). (b) A community **HF ZeroGPU Space** running IQ4_XS GGUF via llama.cpp (8K ctx, 512-token replies, reasoning off). (c) **Community GGUF quants** (16.8 to 31.5 GiB) for llama.cpp on Kaggle 2×T4 or a big-RAM CPU box **[SPEC]**. (d) Rent one 80 GB GPU for BF16 vLLM.
5. **Evon's strengths, per Gnani's own card:** Indic extractive QA (XQuAD-in 64.59 F1, XorQA-in 41.83, both best among open models), MILU 78.74, and token efficiency (2.20 tokens/word vs 3.59). **Weaknesses:** summarisation (CrossSum-in chrF **4.67** vs Sarvam-105B 18.01), instruction following (IndicIFEval 47/29 vs Gemma-4-31B 81/38), **Odia**, and multi-step tool use (their stated limitation). Gemma-4 beats it on most rows. [README](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/README.md)
6. **Gnani itself says Evon is "not yet" recommended for real-time voice agents**, because it reasons by default. They recommend their STT/S2S models for live voice. A demo that runs Evon in `enable_thinking=false` mode and shows measured voice latency would be addressing a gap the vendor admits to. [Evon release notes FAQ](https://introducing-evon-v3-3-llm.netlify.app/)
7. **Prisma v2.5's home turf is noisy 8 kHz audio and rural Hindi.** It ranks #1 on Kathbath-noisy in 8 of 9 languages and on Gramvaani rural Hindi (22.0% WER). It **loses on MUCS 2021 code-switching** (to Microsoft or Sarvam in 4 of 5 languages) and **on FLEURS** (Sarvam wins 7 of 9). The STT API has **no Odia/Assamese/Bhojpuri**. [Prisma benchmark microsite](https://gnani-prisma-v2-5-benchmarks.netlify.app/), data extracted from its embedded JSON.
8. **Warp (speech-to-speech, 5B) is demo-request only.** It is not in the API. Do not plan around it.
9. **Legal caution:** Gnani's EULA says *"Results of any benchmark tests on the Gnani Product run by You may not be disclosed outside Your organization without the prior written consent of Gnani."* The EULA is written for licensed products. Whether it binds hackathon API use is unclear **[SPEC]**. Publishing WER tables that compare Gnani against competitors could be risky. Framing results as "what we measured on our own clips" is probably fine, but check with the organisers on Discord. [EULA](https://www.gnani.ai/legal/eula)

---

## 1. Evon v3.3 (LLM, open weights)

### 1.1 Identity and lineage
| Field | Value | Source |
|---|---|---|
| Repo | `gnani/gnani-evon-v3.3-30B-A3B`. The README code uses `gnani/gnani-evon-v3.3`, which the HF API **redirects** to the same repo, so both IDs work. | [HF API](https://huggingface.co/api/models/gnani/gnani-evon-v3.3-30B-A3B), [README](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/README.md) |
| Created / last modified | 2026-08-10 / 2026-09-09. Release date "August 2026". | [HF API](https://huggingface.co/api/models?author=gnani) |
| Base model | **NVIDIA Nemotron-3-Nano-30B-A3B-BF16** ("Derivative Work of NVIDIA Nemotron-3-Nano-30B-A3B") | [NOTICE](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/NOTICE), [GGUF card lineage](https://huggingface.co/luminenio/gnani-evon-v3.3-30B-A3B-GGUF) |
| Training | Continued pretraining on a blended English+Indic corpus (">2T tokens of Indic data"), then SFT, then RL (**GRPO**). Trained on H200 clusters with NeMo Curator, Megatron Bridge and NeMo RL. | [README](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/README.md), [models page](https://www.gnani.ai/models) |
| Tokenizer | Vocab **163,072**, "rebuilt for Indic scripts". Built with NVIDIA using **continued BPE** on the Nemotron merge table (+32K merges). Fertility is 1.88 tokens/word avg (hi 1.49, bn 1.97, ta 2.00, te 2.06), vs Sarvam-30B 2.01. | [tokenizer whitepaper](https://www.gnani.ai/resources/research/indic-tokenizer-nemotron), [config](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/config.json) |
| Token-efficiency claim | 3.5905 to 2.2046 tokens/word (**−38.6%**). Gujarati −47%, Malayalam −44%. Separately "~20% fewer tokens per Indian word than the GPT-5 family tokenizer". | [release notes](https://introducing-evon-v3-3-llm.netlify.app/), [models page](https://www.gnani.ai/models) |
| License | Apache 2.0 for Gnani's modifications. The underlying NVIDIA work stays under the **NVIDIA Nemotron Open Model License**. Redistribution must ship LICENSE, LICENSE-NVIDIA and NOTICE. | [NOTICE](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/NOTICE) |
| Gating | API: `gated:false`. Anonymous shard download works (302 to public CDN, verified 2026-10-04). The internship page, Artha page and release notes all still say "Access is granted on request". | [HF API](https://huggingface.co/api/models/gnani/gnani-evon-v3.3-30B-A3B?expand%5B%5D=gated), [release notes](https://introducing-evon-v3-3-llm.netlify.app/) |
| Popularity | 10,561 downloads, 52 likes (2026-10-04) | [HF API](https://huggingface.co/api/models/gnani/gnani-evon-v3.3-30B-A3B) |

### 1.2 Architecture (from `config.json`)
- `NemotronHForCausalLM`, `model_type: nemotron_h`. **52 layers: 23 Mamba2, 23 MoE, 6 attention.** [config](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/config.json), [release notes](https://introducing-evon-v3-3-llm.netlify.app/)
- hidden 2688; MoE: **128 routed experts, top-6, plus 1 shared expert** (shared intermediate 3712, expert intermediate 1856), `relu2` MLP activation.
- Attention: 32 Q heads, **2 KV heads** (GQA), head_dim 128, rope_theta 10000, `max_position_embeddings` 131072.
- Mamba2: 64 heads × 64 dim, ssm_state 128, conv kernel 4, `mamba_ssm_cache_dtype: float32`.
- Params by safetensors: 31.75B (BF16). 13 shards, **63.5 GB on disk**. [HF tree](https://huggingface.co/api/models/gnani/gnani-evon-v3.3-30B-A3B/tree/main)
- **[SPEC] KV-cache math:** only 6 attention layers × 2 KV heads × 128 dim × 2 (K,V) × 2 bytes ≈ **6 KB/token**, so a 128K context is about 0.8 GB of KV. The Mamba state is about 48 MB per sequence (fp32). Long context is cheap. The weights dominate memory.

### 1.3 Chat template, reasoning, tool calling
- ChatML-style `<|im_start|>role ... <|im_end|>` (eos `<|im_end|>`; generation eos ids [2, 11]). [chat_template.jinja](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/chat_template.jinja), [generation_config](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/generation_config.json)
- With no system prompt, the default identity is *"You are gnani-evon-v3.3, a large language model developed by Gnani.ai."* It can be overridden with the `model_identity` kwarg.
- **Reasoning is ON by default.** The template opens `<think>\n`. Pass `enable_thinking=False` (transformers) or `"chat_template_kwargs":{"enable_thinking":false}` (vLLM/SGLang) to get `<think></think>` and a direct answer. `truncate_history_thinking=True` strips old reasoning from history.
- **Tool calling:** tools are rendered into the system prompt as XML (`<tools><function><name>…<parameters><parameter>…`). The model replies with Qwen3-Coder-style calls:
  `<tool_call>\n<function=NAME>\n<parameter=ARG>\nvalue\n</parameter>\n</function>\n</tool_call>`. vLLM flags: `--enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser nano_v3`. [README](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/README.md)
- Gnani lists tool use as **"an active area of development"** and calls this release the "Indic-capability foundation". Agentic multi-step tool use is planned next. [README](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/README.md)
- Recommended sampling: `temperature=0.6, top_p=0.95`. For short deterministic answers use thinking off, `repetition_penalty=1.1`, max_tokens 2048. For reasoning use thinking on, rep 1.0, max_tokens 16384. Keep a system line such as "Respond in the same language and script as the question", and **verify the output script downstream**. [README](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/README.md)

### 1.4 Official inference recipes and hardware
| Runtime | Requirement / command | Source |
|---|---|---|
| Transformers | `>= 5.3.0`, `trust_remote_code=True`, `torch_dtype=bfloat16`, `device_map="auto"` (the config was saved with 5.8.1) | [README](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/README.md) |
| vLLM | `>= 0.12.0`: `vllm serve gnani/gnani-evon-v3.3 --max-model-len 131072 --trust-remote-code --enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser nano_v3` (OpenAI-compatible) | same |
| SGLang | `--dtype bfloat16 --context-length 131072 --mem-fraction-static 0.90 --moe-runner-backend triton` (Triton avoids the CUTLASS compile problem on pip-only installs). Add `--tp 2` for more concurrency. | same |
| "Supported hardware" | NVIDIA **H100 80GB, H200, A100**; Linux | same |
| Gnani's measured speed | TTFT **302 ms** (1K-token prompt), 454 ms (10K), 928 ms (100K); decode **257.3 tok/s** (σ≈1). Measured on "Gnani's own inference endpoint", default reasoning mode, single request. | [release notes](https://introducing-evon-v3-3-llm.netlify.app/) |

**[SPEC] VRAM planning:**
- BF16 weights are about 63.5 GB, so it needs **one 80 GB GPU** (A100/H100 80GB). It does not fit on 48 GB.
- FP8 (vLLM `--quantization fp8`, dynamic, Ada/Hopper) is about 32 GB, so it might fit one L40S or A6000 48 GB. No official FP8 checkpoint exists.
- 4-bit GGUF is 17 to 23 GiB plus buffers.

### 1.5 Community quantizations and hosted copies
| What | Details | Source |
|---|---|---|
| **GGUF** `luminenio/gnani-evon-v3.3-30B-A3B-GGUF` (unofficial, **gated** repo) | Q8_0 31.45 GiB · Q6_K 31.38 · Q5_K_M 24.40 · Q4_K_M 22.97 · Q5_K_S 22.32 · Q4_K_S 20.56 · Q3_K_L 19.46 · Q3_K_M 18.62 · **IQ4_XS 17.09** · Q3_K_S 16.84 · Q2_K 16.81. 134/401 tensors fall back to higher precision, so low-bit quants save little. Tested on an A10 with 10 layers offloaded. Quality vs BF16 **not evaluated**. 516 downloads. | [GGUF card](https://huggingface.co/luminenio/gnani-evon-v3.3-30B-A3B-GGUF), [derivatives API](https://huggingface.co/api/models?filter=base_model:gnani/gnani-evon-v3.3-30B-A3B) |
| **HF Space** `luminenio/gnani-evon-v3.3-chat` | Gradio app, IQ4_XS on **ZeroGPU (A10G)** via llama.cpp, 8,192 ctx, replies ≤512 tokens, reasoning off. Counts against each visitor's ZeroGPU quota. Status RUNNING 2026-10-04. | [Space README](https://huggingface.co/spaces/luminenio/gnani-evon-v3.3-chat/raw/main/README.md) |
| **Gnani playground** | <https://playground.gnani.ai/chat> ("Gnani Chat"): Evon v3.3 web UI, no login, "Chats are deleted after 7 days". Backend calls are `/api/playground/*` (internal, undocumented, **not for us to use**). | [Artha page link](https://www.gnani.ai/artha-sovereign-ai) |
| FriendliAI | Model page lists **Dedicated Endpoints** only. Serverless or pricing not shown. | [Friendli](https://friendli.ai/models/gnani/gnani-evon-v3.3-30B-A3B) |
| HF Inference Providers | `inferenceProviderMapping: {}`, so **no serverless provider**. | [HF API](https://huggingface.co/api/models/gnani/gnani-evon-v3.3-30B-A3B?expand%5B%5D=inferenceProviderMapping) |
| Gnani Inya agent builder LLM list | Its sample response lists Gnani LLMs "Pampa Go", "Pampa Priority" (plus OpenAI/Anthropic). No "Evon" ID is documented. | `docs/raw/llms-full.txt` §Get LLM Models ([docs](https://docs.gnani.ai/llms.txt)) |

### 1.6 Benchmarks (all self-reported, Gnani's harness)
MILU (79,608 items, 11 langs). Macro: **Evon 78.74** vs Sarvam-105B 75.71 vs Sarvam-30B 67.15. Evon leads 105B on 10/11 languages. **Odia is the exception and Evon's weakest language: 66.94 vs 73.70.** [README](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/README.md), [release notes](https://introducing-evon-v3-3-llm.netlify.app/)

| Benchmark | Evon v3.3 | Sarvam-30B | Sarvam-105B | Gemma-4-26B-A4B | Gemma-4-31B |
|---|---:|---:|---:|---:|---:|
| MILU | 78.74 | 67.15 | 75.71 | 82.65 | **85.29** |
| IndicMMLU-Pro | 68.79 | (58.00 on release page) | — | 70.34 | **79.02** |
| BharatMath | 73.97 | 60.32 | — | 76.48 | **78.61** |
| MGSM-Indic | 86.00 | 76.00 | — | — | — |
| XQuAD-in (F1) | **64.59** | 37.86 | 56.65 | 55.09 | 42.21 |
| XorQA-in (F1) | **41.83** | 22.86 | 34.98 | 34.47 | 30.16 |
| FLORES-in (chrF++) | 34.52 | 18.05 | **34.56** | — | — |
| CrossSum-in (chrF) | **4.67 (very weak)** | 9.66 | 18.01 | 18.85 | **23.09** |
| IndicIFEval-trans | 47.45 | 40.76 | 51.79 | 75.20 | **81.12** |
| IndicIFEval-ground | 28.66 | **40.69** | 37.88 | 34.73 | 37.79 |
| IndicSafe (5,965 rows) | 86.50 | 81.26 | — | 88.15 | **89.77** |

- vs hosted models (9-language MILU macro): Evon 79.46 · gpt-5.4-nano 79.69 · DeepSeek-V4-Flash 72.48 · gpt-5.6-luna 86.96 · gpt-5.4-mini 87.37 · gemini-3.5-flash-lite 90.41. [release notes](https://introducing-evon-v3-3-llm.netlify.app/)
- "Cost index" (Evon = 100, blended price ÷ MILU, prices undisclosed): DeepSeek-V4-Flash 219, gpt-5.6-luna 470, gpt-5.4-nano 527, gemini-3.5-flash-lite 854, gpt-5.4-mini 1,754. [release notes](https://introducing-evon-v3-3-llm.netlify.app/)
- Safety: the weakest categories are gender and caste discrimination (70.26%) and political manipulation (72.49%). [README](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B/raw/main/README.md)
- **Implication [SPEC]:** use Evon for **extracting fields or answers from Indic text** (its best capability) and for Indic chat. Do **not** rely on it for long summaries or for strict formatting or instruction following without validation (schema check plus retry). Avoid Odia-critical paths.

### 1.7 Gnani's own positioning and caveats
- "Is Evon v3.3 recommended for real-time voice agents? **Not yet.** … a non-reasoning serving mode is required before Gnani recommends it for production real-time voice." [release notes FAQ](https://introducing-evon-v3-3-llm.netlify.app/)
- "No live Evon deployments yet". Plans: 70B/100B models, **22 languages**, and speech-to-speech built on Evon. [Inc42](https://inc42.com/buzz/gnani-ai-unveils-sovereign-ai-stack-artha-for-enterprises/)
- **Evon v2.0** is listed in the Artha stack as "Enterprise reasoning: unified reasoning and tool orchestration across 11+ Indic languages, calibrated for BFSI, insurance, healthcare and telecom". It is not open-weights and not in the API. [Artha](https://www.gnani.ai/artha-sovereign-ai)

---

## 2. Prisma v2.5 (STT)

| Claim | Value | Source |
|---|---|---|
| Training data | **14M hours** of proprietary telephonic Indic speech, 12 languages, collected over 7 years from 200+ deployments ("14x more than any competitor") | [benchmark microsite](https://gnani-prisma-v2-5-benchmarks.netlify.app/), [14M-hours whitepaper](https://www.gnani.ai/resources/research/how-we-train-acoustic-models-on-14-million-hours-of-telephonic-speech) |
| Latency | Streaming P95 **< 200 ms** | [HF gnani/gnani](https://huggingface.co/gnani/gnani/raw/main/README.md), [internship page](https://www.gnani.ai/internship) |
| Languages | API: 10 (en, hi, bn, gu, kn, ml, mr, pa, ta, te), with Hinglish handled under `hi-IN`. Marketing says "40+ languages" (company-wide). | `02-speech-apis.md`, [models page](https://www.gnani.ai/models) |
| Launch | June 2026, "15% lower WER for rural Hindi, 18% lower WER across Dravidian", 2× throughput vs v2.0 | [microsite](https://gnani-prisma-v2-5-benchmarks.netlify.app/) |
| Capabilities claimed | Native GSM/VoIP codec handling, word-level code-switching without language tags, numerals and alphanumerics, Indian named entities, short utterances ("haan", "nahi", "theek hai"), diarization | [microsite](https://gnani-prisma-v2-5-benchmarks.netlify.app/), [models page](https://www.gnani.ai/models) |
| Code-switch paper | Unified Conformer-CTC with a **concatenated tokenizer** (Devanagari + Latin English + a learned Latin-script-Hindi vocabulary), intermediate LID heads, and a language alignment loss. On Hinglish 8 kHz G.711 (4,200 utterances): **switch-point MER 17.9%** vs cascade 29.3%, Whisper-v3 31.2%. Overall MER 16.2%, P95 ~185 ms. Open problems: **3-way switching (e.g. Hindi+English+Bhojpuri)**, prosodic cues. | [code-switching whitepaper](https://www.gnani.ai/resources/research/code-switching-at-8khz) |
| Rural ASR paper | Gramvaani WER **24.94%** "lowest of any model evaluated" (internal, May 2026). The microsite says 22.0%, a different eval or version. Discusses AMR-NB 4.75 to 12.2 kbps, AGC, MEMS mics, 2G jitter. | [rural ASR whitepaper](https://www.gnani.ai/resources/research/the-rural-india-asr-problem-engineering-speech-recognition-for-background-noise) |

### 2.1 Full benchmark data (Std WER %, extracted from the microsite's embedded `const B` JSON)
Comparators: ElevenLabs Scribe v2, Microsoft Azure STT, Sarvam Saaras v3, Deepgram Nova 3. Headline: "27 of 48 evaluations #1". [microsite](https://gnani-prisma-v2-5-benchmarks.netlify.app/)

| Lang | Kathbath P / best rival | Kathbath-noisy P / best rival | Notes |
|---|---|---|---|
| Hindi | **7.6** / 9.3 (11L) | **7.9** / 10.8 (11L) | Gramvaani **22.0** vs Sarvam 23.4, MS 26.4, 11L 27.5, DG 34.0. MUCS: P 11.2 vs **Sarvam 9.8** |
| Bengali | **10.0** / 11.5 | **10.5** / 12.6 | FLEURS: 11L wins (13.5 vs 14.8) |
| Telugu | **17.1** / 20.9 | **17.4** / 22.0 | MUCS: P **16.3** wins |
| Tamil | **20.4** / 22.0 | **21.1** / 24.3 | MUCS: MS 17.4 beats P 18.7; CommonVoice: DG 14.7 beats P 29.1 |
| Kannada | **14.4** / 15.7 | **15.0** / 17.4 | FLEURS: Sarvam 15.6 beats P 18.2 |
| Malayalam | **27.7** / 31.0 | **28.1** / 33.2 | FLEURS: Sarvam 18.7 beats P 26.7. IndicTTS: P 37.7 is poor |
| Marathi | **13.9** / 15.2 | **14.2** / 16.6 | MUCS: P **25.5** vs MS 18.1 (P is worst) |
| Gujarati | **12.5** / 13.2 | **13.0** / 14.6 | MUCS: MS 13.3 beats P 21.0 |
| Punjabi | 13.0 / **12.3 (11L)** | 13.8 / **13.3 (Sarvam)** | Only language where P loses Kathbath |

- Noise degradation, clean to noisy (avg): Prisma +3.6%, Sarvam **+2.6%**, MS +7.8%, 11L +12.2%. Prisma's absolute numbers are lower, but **Sarvam degrades less** relative to its own clean score. [microsite](https://gnani-prisma-v2-5-benchmarks.netlify.app/)
- **CER** (they argue CER is the right metric for Dravidian languages): Prisma wins Kathbath and Kathbath-noisy CER in all languages except Punjabi-noisy (Sarvam 4.0 vs 4.1). It loses Gramvaani CER narrowly (11.4 vs Sarvam 11.2). On FLEURS, Sarvam wins CER in 8 of 9 languages.
- **[SPEC] What this means for us:** Prisma is strongest on **noisy, 8 kHz, spontaneous Hindi/Dravidian** audio. It is weaker on read-speech or code-switch corpora (MUCS, FLEURS). The "Noise Canceller" award and Gnani's own story both point at **real phone-call audio**. For code-mixed demos, rely on Gnani's internal Hinglish claim (17.9% switch MER), not on public MUCS numbers.

## 3. Timbre v2.5 (TTS, "Beta")

| Claim | Value | Source |
|---|---|---|
| Voices / languages | "40+ voices. 10 Indian languages". Every voice speaks all 10, with a "best for" grouping. The HF adapter says 42 voices (v2.0 had 4, or "6 previous gen"). The models page says "21+ languages", **inconsistent**. | [Timbre page](https://www.gnani.ai/resources/gnani-timbre-v2-5-tts), [HF gnani/gnani](https://huggingface.co/gnani/gnani/raw/main/README.md), [models page](https://www.gnani.ai/models) |
| Latency | TTFB **< 200 ms** (Timbre page). "sub-100ms time-to-first-audio" (models page), **inconsistent**. | same |
| Audio | WAV, **8 to 48 kHz** (previous generation fixed 24 kHz), 64 concurrent streams, long-form over WebSocket | [Timbre page](https://www.gnani.ai/resources/gnani-timbre-v2-5-tts) |
| Controls | Speed **0.85× to 1.15×**, language styling, punctuation-aware prosody, emotion that adapts to text ("Empathetic in support. Assertive in collections.") | [Timbre page](https://www.gnani.ai/resources/gnani-timbre-v2-5-tts), [models page](https://www.gnani.ai/models) |
| Normalisation | ₹45,000 / dates / **card numbers / alphanumeric policy IDs (PLC-2291-XB) / addresses / finance jargon (NPA, QoQ)**, plus lakh/crore cadence | [Timbre page](https://www.gnani.ai/resources/gnani-timbre-v2-5-tts), [internship page](https://www.gnani.ai/internship) |
| Pitch vs rivals | "Why teams evaluating ElevenLabs, Cartesia, or Sarvam switch to Timbre" | [Timbre page](https://www.gnani.ai/resources/gnani-timbre-v2-5-tts) |
| Model IDs | `timbre-v2.5`; `timbre-v2.0` (formerly `vachana-voice-v3`). Voice clone uses `vachana-vc-v1`. | [HF gnani/gnani](https://huggingface.co/gnani/gnani/raw/main/README.md), `02-speech-apis.md` |

## 4. Warp v2.0 (speech-to-speech), Inya VoiceOS, Vachana, Inya, Armour, Plexus, Artha

| Name | What it is | Usable in hackathon? | Source |
|---|---|---|---|
| **Warp v2.0** | "India's first foundational **5B**-parameter model built to process speech-to-speech directly … no STT, no TTS, no intermediate text layer. Sub-200ms P95." Telephony, agentic. | **No.** Only "Request Demo". Not in docs. | [models page](https://www.gnani.ai/models) |
| **Inya VoiceOS** | 5B voice-to-voice model unveiled 2026-02-17 at the India AI Impact Summit (PM Modi). Built under the IndiaAI Mission. 14M+ h pretraining, 1.2M+ h task audio, 15+ languages, 24 kHz, "research preview" ahead of a **14B flagship**. **[SPEC]** Probably the same model line as Warp. | No | [Digit](https://www.digit.in/news/general/india-ai-impact-summit-2026-gnani-ai-unveils-indias-first-5b-voice-to-voice-ai-model-inya-voiceos.html), [Business Standard](https://www.business-standard.com/technology/tech-news/gnani-ai-unveils-5b-parameter-voice-to-voice-inya-voiceos-model-at-india-ai-summit-126021700403_1.html) |
| **Vachana** | Brand of the speech API and SDK (`api.vachana.ai`, PyPI `gnani-vachana` 0.7.9, import `gnani`). **Vachana STT** launched 2025-12-19 under the IndiaAI Mission: 1M+ hours, 1,056 domains, claimed 30 to 40% lower WER on low-resource and 10 to 20% on the top 8 languages, ~10M calls/day, P95 200 ms. Prisma is the successor or rebrand **[SPEC]**. | Yes (it is the API) | [Gnani blog](https://www.gnani.ai/resources/blogs/gnani-ai-launches-vachana-stt-a-foundational-indic-speech-to-text-model-trained-on-one-million-hours-under-the-indiaai-mission), [AIM](https://analyticsindiamag.com/ai-news-updates/gnani-ai-launches-vachana-speech-to-text-model-under-indiaai-mission/), [PyPI](https://pypi.org/pypi/gnani-vachana/json) |
| **HF `gnani/gnani`** | Transformers `pipeline()` adapter for Prisma and Timbre. **Hosted inference only, no weights.** Out of scope: offline/on-device, fine-tuning, custom vocabulary injection. | Yes (wrapper over credits) | [README](https://huggingface.co/gnani/gnani/raw/main/README.md) |
| **Inya (inya.ai)** | No-code agentic agent builder (voice/chat/SMS/email), 150+ customers. Platform API at `api.inya.ai`. Credits are set up via `hello-inya@gnani.site`, a **separate credit system [SPEC]**. | Maybe. See `04-agent-builder-and-platform-api.md`. | [BusinessToday/AIM snippets](https://inc42.com/company/gnani-ai/), `docs/raw/llms-full.txt` |
| **Armour365** | Voice biometrics (fraud detection "across five continents", since 2021) | No | [about](https://www.gnani.ai/about-us), [old GitHub](https://github.com/Gnani-AI) |
| **Plexus** | "Agentic AI workforce": identity-bearing agents, trigger workflows, governance. Waitlist only. | No | [Artha](https://www.gnani.ai/artha-sovereign-ai) |
| **Artha** | The "sovereign stack": Evon v3.3 + Evon v2.0 + Prisma v2.5 + Timbre v2.5 + Plexus, deployed in the customer's DC or VPC. Launched by Vice-President C. P. Radhakrishnan, **2026-08-28**. | Conceptual framing for our pitch | [Artha](https://www.gnani.ai/artha-sovereign-ai), [GKToday](https://www.gktoday.in/vice-president-launches-gnani-artha-sovereign-ai-stack/) |
| **gnani-mcp** | Official MCP server (Prisma, Timbre, voice clone as tools), `uvx gnani-mcp`, key from dashboard.gnani.ai. Repo created/pushed 2026-09-28. | Yes (uses credits) | [GitHub](https://github.com/Gnani-AI-Mintlify/gnani-mcp) |
| Other official repos | `livekit-plugins-gnani`, `pipecat-gnani`, `gnani-vachana`, `custom-speech-example` (Cognigy). The old `github.com/Gnani-AI` org is stale (2020-2023). | Yes | [GitHub org](https://github.com/Gnani-AI-Mintlify), [old org](https://github.com/Gnani-AI) |

## 5. Whitepapers (gnani.ai/resources/research)
All six are listed with date "Sep 29, 2026" (some have internal dates from May 2026). [research index](https://www.gnani.ai/resources/research)
1. [How to Benchmark an STT API on Indian Languages Before You Go Live](https://www.gnani.ai/resources/research/how-to-benchmark-stt-api-indian-languages)
2. [Building a SOTA Indic Tokenizer for NVIDIA Nemotron 3 Nano](https://www.gnani.ai/resources/research/indic-tokenizer-nemotron) (Gnani + NVIDIA, 19 May 2026; Evon's tokenizer)
3. [The Rural India ASR Problem](https://www.gnani.ai/resources/research/the-rural-india-asr-problem-engineering-speech-recognition-for-background-noise) (noise, low-end devices, AMR-NB on 2G; Bhojpuri WER 33.3% vs 15% Hindi cited from arXiv:2506.09653)
4. [How We Train Acoustic Models on 14 Million Hours of Telephonic Speech](https://www.gnani.ai/resources/research/how-we-train-acoustic-models-on-14-million-hours-of-telephonic-speech) (Kathbath-noisy avg 17.5% WER; Odia/Assamese 22 to 28%; codec-sim SpecAugment, SNR −5 to 20 dB)
5. [Code-Switching at 8kHz](https://www.gnani.ai/resources/research/code-switching-at-8khz) (13 May 2026; see §2)
6. [How We Benchmark ASR Models: WER, CER, Indic datasets](https://www.gnani.ai/resources/research/benchmarking-indic-asr-models-a-technical-deep-dive)

## 6. Practical implications for us

| Model | Through 5,000 credits? | Self-host? | Notes |
|---|---|---|---|
| Prisma v2.5 STT | **Yes** (REST ≤60 s, WS streaming, Batch with diarization) | No (hosted only) | Use 8 kHz telephony settings for the Noise Canceller story |
| Timbre v2.5 TTS | **Yes** (REST, SSE, WS) | No | Beta. Number/ID normalisation is a demo-able strength |
| Voice clone | **Yes** (`vachana-vc-v1`) | No | Check consent and ethics for any cloned voice |
| Evon v3.3 | **No hosted API found** | **Yes, open weights** | See the options below |
| Warp / Evon v2.0 / Plexus | No | No | Mention only as context |

**Ways a student without a GPU can run Evon** (the user's laptop has only an integrated gfx90c, see memory `dev-machine-hardware`):
1. **Prototype prompts and qualitative tests:** use <https://playground.gnani.ai> (manual UI) or the [ZeroGPU Space](https://huggingface.co/spaces/luminenio/gnani-evon-v3.3-chat). **[SPEC]** The Space can be called with `gradio_client`, but it uses IQ4_XS, 8K ctx and 512 tokens, is subject to quota, and belongs to a third party. That is too fragile for a live demo.
2. **Free GPU notebooks [SPEC]:** Kaggle (2× T4 = 32 GB VRAM, ~29 GB RAM, ~30 GPU-h/week) can likely run IQ4_XS or Q4_K_S GGUF with llama.cpp split across both T4s, roughly at ~3.5B-active speed. Colab free (one T4 16 GB, ~12 GB RAM) is **too small** for a 17 GiB file without heavy CPU/disk paging. BF16 or vLLM is impossible on either. The GGUF repo is gated, so accept its terms with an HF token.
3. **Rented 80 GB GPU [SPEC]:** one A100/H100 80GB on RunPod, Vast, Lambda or Modal running the official vLLM command gives an OpenAI-compatible endpoint with tool calling and reasoning parser. Only spin it up for demo recording and judging windows. A 48 GB card with `--quantization fp8` is an untested cheaper option.
4. **CPU llama.cpp [SPEC]:** a machine with ≥32 GB RAM can run Q4 GGUF at a few tokens/s, thanks to only ~3.5B active parameters. That is fine for offline batch extraction but not for live voice.
5. **Fallback design:** keep the LLM behind an OpenAI-compatible interface so Evon (self-hosted), the playground (for manual demo segments) or a stand-in can be swapped. Submissions must "name the Gnani AI models or APIs" used ([internship page](https://www.gnani.ai/internship)), so **Prisma and Timbre should carry the core of the demo**, with Evon as a visible bonus. Any non-Gnani LLM is a judging risk **[SPEC]**.
6. **If Evon is used in a voice loop:** `enable_thinking=false`, short max_tokens, a target-language and script system line, and script validation. Measure and show TTFT, since Gnani itself flags this as unsolved ([FAQ](https://introducing-evon-v3-3-llm.netlify.app/)).
