# Great Indian AI Internship Challenge (Gnani AI): Overview, Rules, Scoring

> Sources, read 2026-10-04 with Playwright + curl: <https://www.gnani.ai/internship> (incl. expanded FAQ),
> <https://www.gnani.ai/great-indian-ai-internship-registration-form> (participation terms),
> registration confirmation email (`docs/response.txt`), `docs/abouthack.txt`.

## TL;DR

- **What:** Gnani AI's contest for students in India. "Build Sovereign AI for India" on **Gnani's own models**:
  **Prisma v2.5** (STT), **Timbre v2.5** (TTS, beta), **Evon v3.3** (30B MoE open-weight LLM on Hugging Face).
  Voice cloning is also in the docs.
- **Prize:** up to **100 paid 6-month internships** (stipend **up to ₹1 lakh/month per person**; that is a ceiling, not the standard amount),
  starting **Jan 1 2027**. Separately, **10 awards of ₹50,000** each.
- **Deadline:** **Nov 10 2026** for the final submission (no extensions). The contest opened Oct 1 2026, a 31-day build window.
  **As of today (Oct 4) there are 37 days left.**
- **What decides it:** a **working public demo**, and above all **engagement on LinkedIn/X posts**. The confirmation email says outright:
  *"Gnani AI will be selecting the team on the bases of popular engagement on LinkedIn or X."*
  Engagement only counts up to the published closing cutoff. After that come submission review, an individual interview, and then a written offer.
- **Resources:** 5,000 programme credits (go to the primary registrant), API console at app.gnani.ai, docs at docs.gnani.ai,
  Discord <https://discord.gg/aECcvtABpq> (server "Gnani AI APIs": **482 members, 26 online on 2026-10-04**, a rough proxy for the size of the field),
  email `internshipscontest@gnani.ai`.
- **Status:** the user (Harshdip Saha) is **registered** (confirmation email received). An API key is in `.env` (`API_KEY`).

## Eligibility
- Currently enrolled in a degree or course at a college or university **in India**, and **18+** on the day of registration.
- **Solo, or a team of two**, where both members are eligible. The primary registrant registers and invites the teammate.
  Each member accepts the terms individually. Credits and all communication go to the primary registrant.
  The teammate's email is kept only for verification and testing.

## Rules that matter
| # | Rule | Implication |
|---|------|-------------|
| 1 | The stipend is **per person** and not split | Teams carry no stipend penalty |
| 2 | **Offers are individual**: each teammate is interviewed separately | Record each member's contribution clearly; one can get an offer without the other |
| 3 | The project **must use Gnani AI models/APIs**, and the submission **names them** plus each member's contribution | "Entries must show **genuine use** of Gnani AI technology." Make the Gnani models central, not an add-on |
| 4 | **Public demo on LinkedIn and/or X**: explain the build, name the Gnani tech, **tag Gnani's official account**, use **#GnaniAI #GreatIndianAIInternshipChallenge**. **Nominate one post per platform** | "Tagging alone does not complete your entry." Post on **both** platforms to get two nominated posts |
| 5 | **Deadline Nov 10 2026** is fixed. Project details can be edited until final submission | Fill in the workspace early and refine it later |
| 6 | Only a **written offer** counts | — |
| 7 | **Authenticity**: no purchased engagement, bots, paid promotion, **engagement exchanges** (e.g. "like-for-like" groups), plagiarism, or misleading demos | Invalid interactions are excluded. A substantiated breach means disqualification. Grow engagement organically |
| 8 | **Data:** *"Don't put anyone's real phone numbers, account numbers, Aadhaar, PAN or recorded calls into your project or demo. Use synthetic data."* | All demo data must be synthetic. Generate telephony audio with Timbre or by recording yourself and adding noise; do not use real call recordings |
| 9 | Scope: *"Build a working application ... that addresses a **practical need for enterprises, developers or creators**."* | Frame the problem around a real user (enterprise, developer, or creator) |
| 10 | Gnani may change, suspend, or cancel anything without notice | Watch Discord and email |

## Selection pipeline (internships)
1. **Public demo**: a post with a live demo or demo video on LinkedIn/X, using the hashtags and the tag.
2. **Verified engagement**: Gnani counts reactions, comments, and reshares on the **nominated** posts. Only engagement recorded by the **closing cutoff** counts.
3. **Shortlisting**: submissions are reviewed *"under the scoring method on the programme page"*. **The programme page does not actually publish a scoring formula** (checked 2026-10-04). Unknown weights; worth asking on Discord.
4. **Interviews**: one-to-one, every shortlisted person (teammates separately). Offers depend on *"assessed skills, interview performance and suitability for available roles"*.
5. **Written offers**: stipend and terms. High performers *may* convert to full-time (not guaranteed).

**Strategic reading:** engagement gets you onto the shortlist, and the interview and your demonstrated skill get you the offer.
You need **(a)** a demo that is visually or virally compelling and can earn real reactions in a 60s clip,
and **(b)** real technical depth you can defend in an interview (streaming, telephony noise, code-mixing, evaluation numbers).
**Post early.** Engagement accumulates over time, so a first working post well before Nov 10 (e.g. ~Oct 25) gives it time to grow,
followed by update posts. Only nominated posts count, so decide which post to nominate.

## The 10 awards (₹50,000 each, max one per team/individual, independent of internships)
| # | Award | Criterion | Fit notes |
|---|-------|-----------|-----------|
| 01 | Main Character | Best build in a **regional / low-resource Indian language** | Prisma covers ~10–11 languages (en-IN, hi, bn, kn, gu, pa, mr, te, ta, ml, or). Pick a non-Hindi language |
| 02 | Mixed Vibes | Best **code-mixed** voice experience (Hinglish, Tanglish, Benglish) | Gnani's headline strength |
| 03 | Real Deal | Most useful **real-world problem** (farmers, kirana stores, rural health workers) | Needs credible users and impact framing |
| 04 | Noise Canceller | Best performance on **messy, noisy, real telephonic audio** | Prisma is trained on 8 kHz call-centre audio. Show measured WER on noisy synthetic calls |
| 05 | Two-Person Army | Best project by a **team of two** | Only if you have a teammate |
| 06 | Solo Ninja | Best project by a **single participant** | Only if solo |
| 07 | Jugaad Genius | Most **creative / unexpected use** of Gnani models | Unusual use of STT/TTS/voice cloning/Evon |
| 08 | Small Town, Big Build | Entry from a **Tier 2/3** college or city | Likely **not applicable**: the user is at NSUT Delhi (metro) |
| 09 | Demo Day Drop | Best **60-second demo video** | Make the main demo exactly ≤60s; it doubles as the social post |
| 10 | Crowd Favourite | **Public votes** on LinkedIn/X (#GreatIndianAIInternshipChallenge #GnaniAI) | Same engagement that drives the shortlist |

## Submission checklist (participant workspace)
**Step 2: Describe the project** (editable until final submission)
- [ ] Project title
- [ ] Problem being solved
- [ ] Who will use it
- [ ] Gnani AI models/APIs planned (Prisma v2.5 / Timbre v2.5 / Voice Clone / Evon v3.3)
- [ ] Each member's contribution

**Step 3: Submit** (by Nov 10 2026)
- [ ] Demo or video of the **working** project
- [ ] Written project explanation
- [ ] Gnani AI models/APIs used
- [ ] Links to nominated **LinkedIn** post and **X** post (one per platform; tag Gnani; both hashtags)
- [ ] Confirmation receipt from the workspace

## Key dates
| Date | Event |
|------|-------|
| Oct 1 2026 | Contest start; registration and workspace open |
| **Oct 4 2026** | Today: registered, API key present |
| Nov 10 2026 | **Final submission close** (and presumably the engagement cutoff; confirm) |
| After close | Shortlist and individual interviews |
| Jan 1 2027 | Internships start (6 months; location and arrangement in the offer) |

## Official links
| What | URL |
|------|-----|
| Programme page | <https://www.gnani.ai/internship> |
| Registration form + participation terms | <https://www.gnani.ai/great-indian-ai-internship-registration-form> |
| API console (Keycloak login, realm `inya`) | <https://app.gnani.ai/> |
| Developer docs | <https://docs.gnani.ai/> (LLM index: `/llms.txt`, full dump: `/llms-full.txt`, saved in `docs/raw/`) |
| Models overview | <https://www.gnani.ai/models> |
| Prisma v2.5 benchmarks | <https://www.gnani.ai/resources/prisma-v2-5-stt-benchmarks> |
| Timbre v2.5 | <https://www.gnani.ai/resources/gnani-timbre-v2-5-tts> |
| Evon v3.3 release notes | <https://www.gnani.ai/resources/introducing-evon-v3-3-large-language-model> |
| Evon v3.3 weights (gated, Apache 2.0) | <https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B> |
| Artha (sovereign stack) | <https://www.gnani.ai/artha-sovereign-ai> |
| Discord | <https://discord.gg/aECcvtABpq> |
| GitHub | <https://github.com/gnani-ai> |
| X / LinkedIn (tag these) | <https://x.com/GnaniAi> · <https://www.linkedin.com/company/gnani-ai/> |
| Contest email | internshipscontest@gnani.ai |
| EULA / Privacy | <https://www.gnani.ai/legal/eula> · <https://www.gnani.ai/privacy> |

## Other observations
- The public STT marketing snippet uses **`https://api.vachana.ai/stt/v3`** with header **`X-API-Key-ID`**. "Vachana" is the API brand. See `02-speech-apis.md`.
- Marketing claims (gnani.ai/speech-to-text-api): "<4% WER", 8 kHz telephony optimized, built-in NER for PAN/Aadhaar/amounts.
  Kathbath-Noisy WER: **Prisma 6.2%** vs Google 12.9%, BharatGen 14.8%, Sarvam 16.3%, Whisper-large 22.1%. These are Gnani's own numbers.
- The registration page says the docs cover *"STT, TTS, **LLM**, and streaming"*, but the docs index has no LLM endpoint (see `02`/`05`).
  The FAQ says Evon is used by downloading it from Hugging Face. Ask on Discord whether a hosted Evon endpoint exists for participants.
- **There is no public pricing.** gnani.ai/pricing redirects to "Book a demo". What a "credit" buys (seconds of STT? characters of TTS?) is only visible in the dashboard. **Check the dashboard before heavy testing.**
- The IP/ownership terms are *"set out in the programme terms"* (FAQ). The visible participation terms on the registration page say nothing about IP. The EULA may; see `06`.

## Open questions to ask on Discord / check in dashboard
1. Credit unit and burn rate per API (STT sec / TTS chars / voice clone).
2. Is there a hosted Evon endpoint (OpenAI-compatible?) for participants, or only HF self-hosting?
3. The "scoring method on the programme page": what are the weights of engagement vs technical review?
4. Exact engagement cutoff time (Nov 10, IST?). Do posts made before the project is in the workspace count?
5. Is Agent Builder (app.gnani.ai voice agents, telephony test calls) included in programme credits?
