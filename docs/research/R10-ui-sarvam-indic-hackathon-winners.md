# Research A — Sarvam / Indic-voice hackathon winners: UI/UX patterns for Kaam ka Parcha

Date: 2026-10-05. Method: web search (session budget ran out partway), WebFetch on event and project pages, and shallow `git clone` of winner repos into `scratchpad/repos/` so I could read the code. Every claim below has a source URL. Anything I could not confirm is marked **UNVERIFIED**.

## 0. Caveats up front

- **Sarvam's own hackathons have poor public records.** For BuildIn' Hours (Aug 2026) we know the project names but not the teams or repos. Results for the Sarvam Epoch Buildathon (Jul 2026) were never published where I could see them. HackHazards '26 Sarvam-track results: not found. Build with Bulbul (Feb 2026) winners: not found. Most winner posts are on X/LinkedIn, and X returned HTTP 402 to WebFetch.
- The **best UI evidence comes from winners outside Sarvam-only events that still sit in the Indic/Bharat-voice space**: Build India 2026, AWS AI for Bharat 2026, Gemma 4 Good 2026, and Forge the Future 2026 (Sarvam was a partner).
- **No public record of earlier Gnani AI challenge winners.** The Great Indian AI Internship Challenge (Sep 30 – Nov 10 2026) is the current edition: https://www.gnani.ai/resources/blogs/great-indian-ai-internship-challenge-2026
- Many winners won on **problem framing and the demo, not on UI polish**. Several winning UIs are generic SaaS. That is the clearest anti-pattern finding (section 4).

## 1. Project table

| # | Project | Event / placement | What it does / target user | Links | UI stack | Verified? |
|---|---|---|---|---|---|---|
| 1 | **Chat2Cash** (rebranded "Snapdo") | Build India 2026 (Anthropic × Replit × Lightspeed), **Grand Prize $16,500** | Turns Hinglish WhatsApp order chats into GST invoices and payment tracking for kiranas, distributors and tiffin services | Blog: https://devfolio.co/blog/buildindia2026/ · Devfolio: https://devfolio.co/projects/chatcash-9791 · GitHub: https://github.com/swayam-mishra/Chat2Cash | React + Vite, Tailwind 4, Framer Motion, Clerk, Inter + "NeueHaasGrotesk" | Win verified. The repo I read is the post-hackathon rebrand (last commit 2026-05-25). The Replit demo URL returns 404. |
| 2 | **BimaSathi** (Team Rayquaza EX, IIIT-Delhi) | AWS **AI for Bharat** 2026, **Student Track winner** (public impact & accessibility) | WhatsApp-first, voice-enabled crop insurance (PMFBY) claim assistant for farmers in 7 languages, plus an operator dashboard for CSC operators | YourStory: https://yourstory.com/2026/06/crop-insurance-conversational-analytics-ai-for-bharat-hackathon · GitHub: https://github.com/ammarsksk/BimaSathi | Twilio WhatsApp + AWS (Transcribe/Polly/Bedrock); dashboard is React + Vite + vanilla CSS, Inter/Outfit/DM Serif Display | Verified (README names the team and the hackathon; team members match YourStory) |
| 3 | **MindBridge / मनसेतु** | Google DeepMind **Gemma 4 Good** Hackathon, **Unsloth Prize** (from 1,609 submissions) | Hindi-first, fully offline PHQ-9/GAD-7 voice screening for ASHA health workers | Google blog: https://blog.google/innovation-and-ai/technology/developers-tools/winning-entries-gemma-4-good-challenge/ · GitHub: https://github.com/HP-00/MindBridge-Gemma-4 · Demo: https://youtu.be/4sNyvlKk21I | React Native (Cactus SDK), Noto Sans Devanagari + Inter + JetBrains Mono | Verified |
| 4 | **MediAudit-X** (Team defcon1) | Forge the Future 2026 (Elastic × AWS × **Sarvam** × HackCulture), **2nd runner-up** per Elastic. The README says "Winner". | Claims auditor with cited evidence and a hash-chained audit ledger, for insurance reviewers | https://www.elastic.co/blog/mumbai-forge-the-future-hackathon-2026 · https://github.com/devanshupathak9/mediaudit-x | Next.js 15, Tailwind 3, lucide, react-joyride; navy/slate palette | Placement verified via Elastic |
| 5 | **Vigil** (Team Frustrated Engineers) | Forge the Future 2026, **Grand Winner** | Transcribes multilingual Indian sales calls and flags SEBI/AMFI violations with exact audio timestamps and the matching clause | https://www.elastic.co/blog/mumbai-forge-the-future-hackathon-2026 | Unknown, no repo found | Win verified; UI **UNVERIFIED** |
| 6 | **PragyanAI** | Lightspeed **Warpspeed 2025**, **1st runner-up**; entered the Sarvam AI Track and runs agent orchestration on Sarvam's LLM | Multilingual learning agent (videos, mind maps) for students | https://devfolio.co/blog/warpspeed-2025-recap/ · https://devfolio.co/projects/pragyanai-097f · FE: https://github.com/Pranay50x/Warp_hack | Next.js 15, Tailwind 4, Framer Motion, Geist/Inter; dark teal gradient with neon "futuristic-glow" text | Verified |
| 7 | **ArtisanGully** (Team Oopsie Operators) | Google Cloud **Gen AI Exchange 2025**, one of 10 winners | Marketplace for Indian artisans; AI listings, images and video ads from a photo or voice input | https://blog.hack2skill.com/gen-ai-exchange-hackathon-finale · candidate repo: https://github.com/navyajain7105/ArtisanGully · live: https://artisan-167575348709.europe-west1.run.app | Next.js (Firebase Studio starter) + shadcn; PT Sans; forest green #38761D with golden yellow #D4AC0D | Win verified; **repo ownership UNVERIFIED** |
| 8 | **Kisan Mitra AI** (Rajat Sahu, Vaishali Jha) | AWS AI for Bharat 2026, Professional Track winner | Farm assistant: soil reports turned into fertiliser advice, crop grading, voice-first in regional dialects | YourStory link above | Unknown | Win verified; UI **UNVERIFIED** |
| 9 | **Sarvam BuildIn' Hours** winners: (a) Govt Tender Discovery for MSMEs (Sarvam Vision), (b) Storytelling for Kids in Indic languages, (c) **Setu** (visual communication for people who cannot speak) | Sarvam BuildIn' Hours, Zo House Bengaluru, 18 Aug 2026, ₹5L pool, top 3 | See left | https://digitalterminal.in/tech-companies/zo-house-bengaluru-hosts-sarvam-ai-hackathon · https://smestreet.in/infocus/zo-house-bengaluru-hosts-sarvam-ais-buildin-hours-hackathon-6272-applied-in-48-hours-100-got-in-12391041 | Unknown | Names verified; teams/repos/UI **UNVERIFIED** |
| 10 | **VYOMA Innovation Challenge** (BHASHINI × Current AI × Kalpa Impact) winners: Asha Sahayak, Shravan, Sangrah – Apna Saathi, Sahyak Mitra – A.V.E.R.A. | Finale at IIIT-Delhi, 17 Sep 2026 | Offline, voice-first handheld assistants built on the **Suno Sutra** reference device | https://www.tripurastarnews.com/bhashini-current-ai-and-kalpa-impact-conclude-vyoma-innovation-challenge-showcase-open-source-ai-solutions-for-india/ · device software: https://github.com/currentai-org/suno-sutra-sw | Suno Sutra = embedded Linux handheld with screen, **physical push-to-talk trigger**, and a bottom status bar showing "ready" | Names verified; project details **UNVERIFIED** |
| 11 | **Techgentsia – Vconsol** ("Bharat VC") | **Bhashini Grand Innovation Challenge** winner (₹50L + govt contract), speech-to-speech category | Live speech-to-speech translation inside video conferencing, for government | https://www.techgentsia.com/case-studies/bhashini/ | Not documented | Win verified; UI **UNVERIFIED** |
| 12 | **Bhasha Bandhu** (Bhashini Sprint 1.0) winners: Team CodeSage, Team The Boys 002 (₹5L each) | Judiciary-language hackathon, Feb 2025 | Legal translation/literacy prototypes | https://www.tribuneindia.com/news/business/bhasha-bandhu-hackathon-a-revolutionary-step-toward-bridging-language-barriers-in-indias-judiciary/ | Unknown | Names verified; details **UNVERIFIED** |
| 13 | **MumbaiHacks 2025**: Padhai Check (Misinformation track, communicates in Hinglish), MoneyMitra (Fintech, multilingual literacy modules) | Track winners | Students / personal finance | https://www.business-standard.com/content/press-releases-ani/mumbaihacks-2025-crowns-india-s-next-gen-ai-innovators-with-inr-1-crore-cash-and-rewards-marking-the-world-s-largest-agentic-ai-hackathon-125120500292_1.html | Unknown | Win verified; UI **UNVERIFIED** |
| 14 | **BhashaSetu** (solo, 6 hours) | Sarvam **Epoch Buildathon** 2026 entry. **Placement UNVERIFIED** (results never published). | Kannada↔Hindi live voice bridge that ends in one "verified bilingual receipt"; self-corrections shown with strike-through | https://github.com/thorOdinson16/BhashaSetu | **FastAPI + vanilla HTML/CSS/JS** (same stack as ours); system-ui font; dark theme | Repo verified, placement not |
| 15 | **Indic Copilot** (Akshay M Puttallavar) | Build India 2026 entry using Sarvam voice credits. **Placement UNVERIFIED.** | Voice app-builder in Indian languages | https://www.linkedin.com/in/akshaymp/ | React/TS + Express | Unverified |

Partner context: Sarvam × Lightspeed Warpspeed (24h, theme "voice-led and multilingual AI agents") https://x.com/SarvamAI/status/1937385814956159108 ; Sarvam × HackCulture Great Bengaluru Hackathon (50 projects in the Sarvam track, which was a multilingual loan advisor) https://x.com/SarvamAI/status/1905165495042535889

## 2. Per-project UI findings (from reading the code)

### 2.1 Chat2Cash / Snapdo (Build India Grand Prize)
Source: `src/pages/public/Landing.tsx`, `src/index.css`, `DESIGN.md` in https://github.com/swayam-mishra/Chat2Cash
- **First screen = before/after.** On the left, a **WhatsApp-styled chat mockup**: dark header `#1F2C34`, avatar "R", "Ramesh Kirana · online", customer bubble with the raw Hinglish *"bhai 5kg aata, 2kg daal, 1 bottle sarso tel bhejo aaj"* and "10:42 AM", and a reply bubble in WhatsApp green `#005C4B` reading "✓ Order received & extracting…". On the right, an **"Extracted order" card** with item / qty / ₹ rows, a **"✓ 98% match" confidence pill**, and the total in WhatsApp green `#25D366`.
- Hero headline: "WhatsApp orders, structured instantly." CTA: **"Try demo — no sign up"**. Live demo uses a pre-filled Hinglish sample ("Ramesh: bhai 5kg aata chahiye … Vendor: theek hai kal tak bhej deta hoon").
- Palette tokens include the **WhatsApp brand set**: `--wa-green #25D366`, `--wa-light #E6FFDA`, `--wa-linen #FCF5EB`, `--wa-dark #111B21`. The social-proof bar sits on `#E6FFDA` and lists "Kirana stores · FMCG distributors · Tiffin services…".
- Problems are named in the user's own pain language: "WhatsApp chaos", "Manual entry hell", "No GST record". Steps: 01 Paste the chat, 02 AI extracts, 03 Download the invoice ("Review, confirm, and generate").
- **Anti-pattern:** the post-win redesign copies Shopify's look (DESIGN.md is literally "Shopifi-design-analysis": 96px thin display type, black canvas, cream-mint pastels). The UI copy is **English-only** even though the input is Hinglish. Testimonials look invented.

### 2.2 BimaSathi (AWS AI for Bharat, Student winner)
Source: `README.md`, `src/shared/languages.js`, `src/shared/s3.js`, `dashboard/src/index.css` in https://github.com/ammarsksk/BimaSathi
- **The end user never installs anything. WhatsApp is the UI.** Separately, a **CSC operator dashboard** handles the assisted flow. This maps directly to our split between the mechanic page and the customer link.
- WhatsApp copy for Hindi is **Romanized Hinglish that keeps English loanwords**: "Aapke phone par OTP bheja gaya hai…", "Main Menu: 1. Nayi claim file karein 2. Claim status dekhein 3. Adhuri claim (draft) resume karein 4. Madad chahiye". The welcome is in Devanagari ("नमस्ते! BimaSathi में आपका स्वागत है। मैं आपकी फसल बीमा claim में मदद करूँगा।"). The language menu lists **endonyms** (हिन्दी / मराठी / తెలుగు / தமிழ் / ગુજરાતી / ಕನ್ನಡ / English). Crop choices are bilingual: "Gehun (Wheat)", "Dhan (Rice)".
- **Numbered replies** keep each step to one decision.
- **Per-photo feedback is like a receipt**: "Photo #{n} accept ho gayi! Labels… Quality: {score}/100. {remaining} aur photos chahiye."
- **Trust:** every piece of evidence gets a **SHA-256 hash for tamper detection**, plus GPS validation, an audit trail, digital consent, and a **"claim summary for user verification before final submission"**. Output is an insurer-ready **PDF claim pack**.
- **Anti-pattern:** the dashboard is generic SaaS (`--primary #2563EB`, purple gradient CTA `#2563EB→#7C3AED`, slate text), and its language switcher labels languages in English ("Hindi", "Marathi").

### 2.3 MindBridge / मनसेतु (Gemma 4 Good, Unsloth Prize)
Source: `README.md`, `app/theme.ts`, `app/components/primitives/VoiceInputButton.tsx`, `BilingualLabel.tsx`, `app/screens/ScreeningItem.tsx` in https://github.com/HP-00/MindBridge-Gemma-4. This is the most design-mature Indic-voice winner I found.
- **Hindi-first, not translated:** "Devanagari is the primary script, not a translation layer over English". The design rule is "Devanagari at equal-or-greater hierarchy than Latin in every bilingual block". The `BilingualLabel` component stacks Devanagari 17pt semibold `#1c1a16` above Latin 13pt medium `#6b665d`.
- **Fonts:** Noto Sans Devanagari (variable), Inter, JetBrains Mono. **Line-height is set per script: Devanagari 1.55, Latin 1.45** ("Devanagari needs more vertical room for matras and headstroke").
- **Palette: warm paper, not dark slate.** Background `#f7f3ec`, cards `#fbf8f2`, hairlines `#d9d2c4`, text is warm charcoal `#1c1a16` ("never pure black"), primary teal `#0f4c5c`. **Alarm-red `#b3261e` is reserved for the single safety blocker** ("Anywhere else is a bug").
- **Voice UI:** a **96pt central mic button**. While recording it shows a calm **3-ring pulse** (2.4s, staggered 0.8s), the icon switches to a stop square, and a **"listening" pill counts up**. The screen has three states: IDLE → RECORDING → DRAWER.
- **Human has the final tap:** **Likert buttons are always present as a fallback** to voice. The model's score, a one-line rationale and its confidence appear in a **"Why" drawer**. The worker commits the answer, never the model. Low confidence triggers a follow-up banner.
- Type floors: 17pt body, 20pt button labels, 13pt minimum footer, **36pt+ for the emergency tap-to-call** buttons (Tele MANAS 14416).
- Output is a **bilingual referral PDF plus the native share sheet**. The README story opens on a concrete person ("In Barabanki, UP, an ASHA worker visits Priya…").
- An on-screen status telemetry strip ("E2B · TTFT 1.9S · … · ON-DEVICE") turns a technical property into a visible trust signal.

### 2.4 MediAudit-X (Forge the Future, Sarvam-partnered)
Source: https://github.com/devanshupathak9/mediaudit-x (`README.md`, `frontend/app/audit-trail/page.tsx`, `ClaimAuditTrail.tsx`)
- Tagline: **"Claims you can cite, not just trust."** The verdict comes from a deterministic function, never from the LLM.
- **The tamper-evident ledger is shown in the UI**: `record_hash = SHA256(canonical_json(payload) + prev_hash)`, a one-click **"Verify Chain"** button, and the plain-language explanation "If any past entry were altered, the chain would break and show it."
- Visual style is navy/slate developer dashboard, which is the wrong look for our audience. The **trust copy pattern** is still worth borrowing.

### 2.5 PragyanAI (Warpspeed, Sarvam track, 1st runner-up)
Source: https://github.com/Pranay50x/Warp_hack (`src/app/globals.css`, `translation/page.tsx`)
- Dark teal gradient body (`#0f2027 → #2c5364`), neon cyan glow text, teal→purple→blue gradients, Geist font. The language dropdown shows **English names** ("Hindi", "Tamil") rather than native script. This is the classic "AI hackathon" look, and it still placed. Evidence that judges weren't scoring UI, not evidence that the look is good.

### 2.6 ArtisanGully (Gen AI Exchange 2025 winner; repo ownership unverified)
Source: https://github.com/navyajain7105/ArtisanGully (`docs/blueprint.md`, `tailwind.config.ts`, `src/ai/community_flow/voice-navigation.ts`)
- Firebase Studio Next.js + shadcn starter. The blueprint specifies **forest green `#38761D`, light green bg `#E0F2E9`, golden-yellow accent `#D4AC0D`** ("nature, growth"), PT Sans, a progress bar for application stages, a checklist, and "AI form fill pending user review and OTP confirmation".
- **Voice navigation**: speak and the app routes to a page. The domain-tinted palette (green/gold for agriculture and artisans) is the recurring idea here.

### 2.7 Suno Sutra (BHASHINI VYOMA reference device)
Source: https://github.com/currentai-org/suno-sutra-sw
- The interaction is **hold the trigger, speak, release**. The answer appears on screen **and** is read aloud. A status bar shows "ready". Language is chosen in settings. **Push-to-talk on a physical button** is the government-backed pattern for offline, noisy, low-literacy field use.

### 2.8 BhashaSetu (Sarvam Epoch entry, placement unverified)
Source: https://github.com/thorOdinson16/BhashaSetu
- Same stack as Kaam ka Parcha (FastAPI + vanilla JS). The useful pattern is **self-correction propagation**: "Thursday… no, Friday" updates both sides and **strikes through** the old value. The session ends in **one shared, verified bilingual receipt at a shareable URL**. The UI itself is minimal (system-ui, dark).

## 3. Recurring patterns among winners (Bharat-facing)

1. **WhatsApp is the end user's surface** (Chat2Cash, BimaSathi, and many Sarvam-track entries). Winners either live inside WhatsApp or copy its visual grammar: bubbles, ticks, timestamps, `#25D366` / `#005C4B` / `#E6FFDA` / `#FCF5EB`.
2. **Show the raw Hinglish next to the structured result.** The strongest first-10-seconds hook (Chat2Cash hero) is a messy real utterance turning into a clean itemised ₹ card.
3. **Two surfaces: an assisted operator view and a citizen view** (BimaSathi's CSC dashboard vs WhatsApp; MindBridge's ASHA worker vs patient). The citizen view is radically simpler.
4. **Bilingual with native script first.** Endonyms in the language picker. Romanized Hinglish with English loanwords ("claim", "OTP", "draft") for chat copy, because that is how users actually write.
5. **Big central mic with a calm pulse, a "listening" state and a timer, plus a tap fallback** (MindBridge). Push-to-talk for field devices (Suno Sutra).
6. **Human confirms. AI proposes with visible confidence** ("98% match" pill; Why-drawer with rationale and confidence; "review, confirm, generate").
7. **Trust is made visible in plain words**: SHA-256 per evidence item, hash-chain with "Verify" button, "claim summary before final submission", bilingual PDF and share sheet.
8. **Warm, domain-coloured palettes** win on design maturity (MindBridge paper + teal; ArtisanGully green + gold). They beat dark developer dashboards.
9. **Story-first demos**: open on a named person in a named place (Barabanki ASHA worker; "Ramesh Kirana").

## 4. Anti-patterns seen (even among winners)

- Generic SaaS styling: blue-purple gradients (BimaSathi dashboard), neon glow on dark gradient (PragyanAI), navy dev dashboards (MediAudit-X), Shopify clone (Snapdo post-win). These won on substance despite the UI.
- **English-only chrome over a Hinglish product** (Snapdo). Language names in English instead of native script (PragyanAI, BimaSathi dashboard).
- Fake-looking testimonials (Snapdo).
- Heavy auth (Clerk/Cognito/OTP) before value. Chat2Cash's mitigation: "Try demo — no sign up".

## 5. Sources not reachable / gaps
- X/Twitter posts (HTTP 402), YourStory Gen AI Exchange "10 innovations" (403), Kaggle writeup body (JS-only), the Replit Chat2Cash demo (404), gnani.ai/internship (socket hang-up).
- The WebSearch budget was exhausted before I could search for repos of Vigil, Kisan Mitra AI, the BuildIn' Hours winners and the VYOMA winners.
