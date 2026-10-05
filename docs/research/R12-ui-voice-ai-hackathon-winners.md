# Research C: What winning voice-AI hackathon UIs and demo videos look like

For: **Kaam ka Parcha** (Gnani AI Great Indian AI Internship Challenge, targeting Demo Day Drop, Crowd Favourite, Real Deal, Mixed Vibes and Noise Canceller)
Date: 2026-10-05. Research was cut short on coordinator request, and the session's WebSearch budget ran out partway through. Anything marked **[UNVERIFIED]** is from memory, a search-result summary I did not open, or a project whose prize status I could not confirm.

Method: I read the official winner announcements (ElevenLabs, Google Cloud, Anthropic/Cerebral Valley, AssemblyAI, lablab.ai), opened the Devpost pages, and cloned these repos into `scratchpad/repos/` to read the UI code: gibberlink, Dealwise (11-hackathon), Call My Parts (C2B-Concierge), DockVoice, FieldPilot, Ira, Dukaan, elevenlabs/ui.

---

## 0. Challenge rules that affect the UI (from gnani.ai blog, fetched with curl)

Source: https://www.gnani.ai/resources/blogs/great-indian-ai-internship-challenge-2026

- There are 10 awards of ₹50,000 each, and a team can win **at most one**. Pick the award to aim for. *Demo Day Drop* = "Best 60-second demo video". *Crowd Favourite* = "Public votes on LinkedIn and X" on posts with **#GreatIndianAIInternshipChallenge #GnaniAI**. *Noise Canceller* = "Best performance on messy, noisy telephonic audio". *Mixed Vibes* = best code-mixed voice build. *Real Deal* = most useful real-world problem (farmers, kirana stores and similar users).
- Quote: **"A demo that fakes a result will cost you more than one that shows an honest limitation."** Do not script fake UI output. If you use a scripted demo runner, it must still go through the real STT, extractor and TTS.
- **Synthetic data only**: no real phone numbers, Aadhaar or recorded calls. The call-screen mockup should show an obviously fake number such as `+91 98XXX XX210`.
- Timbre v2.5 "follows lakh and crore cadence, so '₹2,50,000' sounds the way an Indian listener expects". The **visual** format should match: `Intl.NumberFormat('en-IN')` gives ₹2,50,000, not ₹250,000.
- Prisma v2.5 is "trained on 14M+ hours of telephonic audio" and handles Hinglish. Name every model used (Prisma, Timbre, Evon) in the video's end card.

---

## 1. Winning and reference projects (2024–2026)

### Verified winners

| # | Project | Award | Links | Why it matters to us |
|---|---|---|---|---|
| 1 | **GibberLink** | ElevenLabs x a16z Worldwide Hackathon, global top prize (Feb 2025) | Devpost https://devpost.com/software/gibber-link · GitHub https://github.com/PennyroyalTea/gibberlink · YouTube https://www.youtube.com/watch?v=EtNagNezo8w (70 s, ~14.1M views when fetched) | Most viral voice-hackathon demo ever, and it is about **a phone call between two parties**, filmed as two physical devices side by side |
| 2 | **Dealwise** | ElevenLabs SF 1st place | https://devpost.com/software/john-ai · https://github.com/jasonwcfan/11-hackathon | Calls local businesses for **price quotes** over Twilio and compiles a quote table. "Vendors had no clue they were talking to AI" |
| 3 | **Procuro** | ElevenLabs NYC 2nd place | https://devpost.com/software/procuro · https://github.com/RiptideStar/vendorwhisperer | Calls suppliers and **auto-generates a purchase-order receipt document**. Small-business procurement |
| 4 | **ECHO AI** | ElevenLabs Bengaluru 2nd place | https://devpost.com/software/echo-ai-zqgmbv | Voice to structured data (mood score, events, memory) |
| 5 | **AMUSH (AI Multilingual Shopping Host)** | ElevenLabs Seoul 2nd place | https://devpost.com/software/ai-multilingual-shopping-host | Multilingual commerce voice host |
| 6 | **Call My Parts** | Gemini Live Agent Challenge, Honorable Mention (2026) | https://devpost.com/software/call-my-parts · https://github.com/Top-Notch-X/C2B-Concierge | **Auto parts** for dealerships. Phones up to 3 vendors in parallel over Twilio and Gemini Live. "Live pipeline tracker and real-time vendor call status" |
| 7 | **Ekaette** | Gemini Live Agent Challenge, Honorable Mention | https://devpost.com/software/ekaette · (repo github.com/ogabasseyy/ekaette would not clone, probably private) | **Real phone calls** over an Africa's Talking SIP number. Hands off to WhatsApp mid-call. 2G-accessible. Bridges G.711 audio to PCM 16 kHz with echo suppression and noise reduction. Closest to our telephony story |
| 8 | **NagarDrishti** (Pune) | Gemini Live Agent Challenge, Honorable Mention | https://devpost.com/software/nagardrishti | Indian civic voice app in **English, Hindi and Marathi**. Hands-free voice reporting while driving. Severity-coloured heatmap |
| 9 | ORION (grand prize), drone-copilot, Sankofa, Wand, etc. | Gemini Live Agent Challenge | https://cloud.google.com/blog/topics/developers-practitioners/winners-and-highlights-of-the-gemini-live-agent-challenge | Rubric: **40% Innovation & multimodal UX, 30% tech, 30% demo**. Video under 4 min, "working in real-time (no mockups)" (https://geminiliveagentchallenge.devpost.com/) |
| 10 | **MaestrIA** | Built with Opus 4.7 Claude Code hackathon, "Keep Thinking" prize | Gallery https://cerebralvalley.ai/e/built-with-4-7-hackathon/hackathon/gallery/194 · Video https://youtu.be/rkH4AjoTL5Q (182 s) · Winners https://claude.com/blog/meet-the-winners-of-built-with-opus-4-7-claude-code-hackathon | **Trades and home-repair estimates in local currency (CLP)**, voice input in Chilean Spanish, a local trade-dialect glossary, and a WhatsApp message drafted to the tradesperson. Visually the closest match to "UI that resembles its audience". (The GitHub repo returned 404 when I fetched it.) |
| 11 | **Wrench Board** | Same hackathon, 2nd place | https://github.com/Junkz3/wrench-board (not inspected) | Diagnostic tool for independent repair technicians |
| 12 | **Soba** (#1), **Goose! Goose! Cook!** (#3) | AssemblyAI Voice Agent Hackathon on lablab, Sept 2026, community-vote leaderboard | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/live · Goose: https://github.com/Ziqing110/goose-goose-cook | Goose is a hands-busy voice app with a **local keyword grammar fallback** so commands still work when the LLM is slow |
| 13 | **Voxy** (Best Overall) and others | SF Voice Agent Hackathon (AssemblyAI, LiveKit, Rime, Accel) | https://www.assemblyai.com/blog/voice-agent-hackathon-sept-19 | Judge on Voxy: "The platform just works" |
| 14 | **Automated OneService** (#1) | OpenAI x GovTech Singapore hackathon (Realtime API) | https://community.openai.com/t/openai-s-first-hackathon-in-asia-in-conjunction-with-govtechsg/1028468 | Seniors file municipal cases **in any language** by voice. Low-literacy and non-English pattern |
| 15 | **Vite Vere** | Gemini API Developer Competition 2024: Most Impactful **and People's Choice** | https://developers.googleblog.com/en/announcing-the-winners-of-the-gemini-api-developer-competition/ | A public-vote winner with a human-impact story (cognitive disability). Relevant to Crowd Favourite |

### Strong references with unconfirmed prize status

| Project | Event | Links | Notes |
|---|---|---|---|
| **DockVoice** (warehouse receiving) | AssemblyAI Voice Agent Hackathon, **#6** on the community-vote leaderboard. **[UNVERIFIED whether it won a prize]** | https://github.com/mohamedahil/assemblyai-voice-agent-dockvoice · demo https://assemblyai-voice-agent-dockvoice.vercel.app | **Nearly the same flow as ours**: worker speaks counts in noise, self-corrects ("eighty… eight zero"), agent reads back, worker says "yes", POSTED stamp drops in. Best code reference found |
| **Ira** (Hinglish receptionist) | AssemblyAI Voice Agent Hackathon **[UNVERIFIED prize]** | https://github.com/h55n/ira · https://ira.h55n.deno.net | Single vanilla `public/index.html`, no build step. Pure-CSS morphing orb. Hinglish copy. WhatsApp confirmation card appears in the feed |
| **Dukaan** (kirana shopkeeper, Hinglish) | Amazon Developer Hackathon, Alexa+ track **[UNVERIFIED prize]** | https://github.com/vivekvermaji/dukaan · https://dukaan-voice.pages.dev | Example lines "2 doodh aur 1 bread becho", "Ramesh ka 500 udhaar likh do". Every action becomes an **undoable card**. Fonts: Plus Jakarta Sans + **Noto Sans Devanagari** + Instrument Serif. Saffron accent `#ff9f1c` |
| **Munim AI** | Paytm Build for India AI Hackathon **[UNVERIFIED prize]** | https://github.com/Virenbhalgamiya/munim-ai | FastAPI + vanilla HTML/JS, like our stack. The whole UI switches between Hindi, English and Marathi, including names (Suresh / सुरेश) |
| **FieldPilot** (trade invoices, GST) | AssemblyAI Voice Agent Hackathon **[UNVERIFIED prize]** | https://github.com/ethicks-x/assemblyai-voice-agent | Has a **"Job-Site Noise" toggle** that plays HVAC noise to show STT robustness, plus a latency telemetry bar. Good idea for Noise Canceller. Visually it is a generic slate dashboard, which is the style to move away from |

---

## 2. How these UIs look, project by project

### GibberLink (verified in code: `hackathon_demo/src/components/ConvAI.tsx`, `globals.css`; thumbnail viewed)
- **Layout:** black full screen, one centred 180 px orb, one rounded "Start/End conversation" button at the bottom. Nothing else.
- **Two parties, two colours:** the receptionist orb is a blue radial gradient (`#7ab8ff → #4a90e2 → #2171cc`) and the caller is red (`#ff7a7a → #e24a4a → #cc2121`). Inactive is the same gradient at about 0.3 alpha.
- **Voice state:** while speaking, `transform: scale(1)→scale(1.05)` loops every **0.4 s**. While connected but idle, the same animation runs every **2 s**. Once in data mode, the orb is replaced by an oscilloscope (audiomotion-analyzer, mode 6, `steelblue` or `orangered` gradient).
- **Live captions:** the latest line is drawn **text-3xl, rising to text-5xl on desktop**, centred above the orb, in white with a 1 px black text-stroke shadow. It is readable on a phone screen filmed by a camera.
- **Demo video (thumbnail viewed):** filmed with a camera, not screen-recorded. A **laptop and a phone sit side by side on a table**, one device per party. A burned-in, huge, orange, outlined subtitle reads **"Oh, you are also AI?"**. The phone shows "is it better now?" with a red level bar. Length is 70 s.
- **First 5 seconds [UNVERIFIED, from memory]:** no title card. It opens straight into the call: "Thanks for calling Leonardo Hotel…".
- **Lesson:** for mechanic and customer, use **two devices (laptop = workshop, phone = vehicle owner)** or a split-screen, with one colour per party and giant captions.

### Dealwise (verified in code)
- The UI code is minimal: a white glass card with a full-width green "Start Negotiation" button and an `animate-ping` dot labelled "Negotiating...". The Devpost screens are business list, search form, live call view, and a **price comparison table of up to 10 quotes**.
- **Lesson:** the payoff artefact (the quote table) is the hero, and the call UI is secondary.

### Call My Parts (verified in code: `voice/AudioWaveform.tsx`, `AIStateIndicator.tsx`, `pipeline/VendorCallQueue.tsx`)
- **Light theme with iOS system colours** per state: idle `#C7C7CC` ("Ready"), listening green `#28B640`, thinking or processing purple and blue, speaking `#5E5CE6` or `#0A84FF`, clarifying amber `#E8870A` ("Input needed"), done green.
- **Orb:** a canvas core with radial gradient, glow, and **3 expanding rings** whose period depends on state: listening 1.8 s, speaking 0.9 s, thinking 2.6 s, clarifying 2.2 s, idle none. The core "breathes" at 5 Hz while speaking and 1.6 Hz otherwise.
- **State label:** small uppercase, wide letter-spacing, coloured, with a pulsing dot.
- **Call queue rows:** a 3 px left border coloured by status (amber pulsing while calling, green when done, orange for no answer or busy, red for failed). Labels read **"Calling…", "Answered", "Not picked up", "Line busy", "Left voicemail"**, with a mono **call-duration timer**, and the **price appears in the row when the call completes**.

### DockVoice (verified in code; screenshot `docs/pitch/assets/cockpit-live.png` viewed)
- A dark slate dashboard (the style our user wants to leave), but the **interaction design maps almost one-to-one onto ours**:
  - **Phase stepper** across the top: Identify PO → Count → **Confirm** → Posted. Completed steps get green checks.
  - **Draft table** with a pill reading "**Awaiting your confirmation**". Rows slide in with a stagger (`delay 0.08 * index`). On every change the row background flashes in its status colour for 1.4 s.
  - **Correction moment:** the old number exits upward with line-through while the new number rolls in from below at scale 1.3 with a spring (`stiffness 380, damping 24`).
  - **Transcript:** worker bubbles on the right (hard-hat icon, cyan), agent bubbles on the left (bot icon, violet). **Numbers and PO ids are highlighted** in the accent colour by regex. Interim text shows at 75% opacity with a caret, and an "interrupted" tag appears on barge-in.
  - **Voice orb** driven by real RMS levels: **worker voice drives cyan, agent voice drives violet**. States: idle, connecting, listening, "Hearing you", "Thinking", "Updating ERP", "Speaking", error. Orbiting particles appear while thinking or working.
  - **Stamp:** after the GRN card lands, a bordered mono "POSTED" label drops in: `scale 2.4→1, rotate -24°→-12°, delay 0.35 s, spring stiffness 520 damping 18`. Then an envelope icon flies from the card to the Outbox nav item.
  - **State machine:** `DRAFT → AWAITING_CONFIRMATION → POSTED`. Posting requires the exact draft version that was read back, and any correction invalidates it. Our card-sealing logic should work the same way.
  - The landing page has a **looping scripted demo** of chat bubbles (one every 2.1 s) so the product is shown moving before anyone clicks.

### MaestrIA (video thumbnail viewed)
- **Warm cream or paper background with a faint dot grid.** Very heavy black geometric display headline, "A master's diagnosis, **in two minutes.**", with the second line in orange and a soft highlighter underline.
- The logo has a local-identity subline, **"CHILOÉ · CHILE"**. There is an ES/EN toggle, small rounded chips ("CLP budget", "Fair prices by zone", "8 trades"), and case-ID badges ("DIA-1042") on photo cards.
- Streaming: "thinks live on screen, draws boxes over the damage", and a "committee of trades argue on screen". The output gives a structured cost in local currency and work time in human units ("half a day, two days"). Then a WhatsApp message is drafted.
- **Lesson:** this is the reference for "looks like it belongs to its users": local place name, local currency, local trade words, a warm paper palette, and a document-like output.

### Ira (verified, single vanilla HTML)
- Light, airy design with Inter. The **orb is pure CSS**: two pseudo-elements with radial and conic gradients, `filter: blur(5px)`, and a `@keyframes morph` that animates `border-radius` (50/50 → 56/44 → 46/54…) together with rotation. A `.think` class swaps the gradient layer and adds a 1.1 s scale pulse.
- Messages enter with `@keyframes rise { from {opacity:0; transform:translateY(12px); filter:blur(4px)} }`. Suggestion chips show Hinglish example phrases.

### Dukaan (verified CSS)
- Dark background with a **saffron/orange accent** (`--acc:#ff9f1c`) and a gradient logo mark. The **Instrument Serif** italic hero is clamped at 54–120 px. The font stack includes `'Noto Sans Devanagari'`.
- The mic button pulse is `@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(255,100,60,.55)}100%{box-shadow:0 0 0 26px rgba(255,100,60,0)}}`. Every voice action becomes a card with an **Undo** link.

### ElevenLabs UI component library (verified in code: https://github.com/elevenlabs/ui, `apps/www/registry/elevenlabs-ui/ui/*`)
- Agent state type: `connecting | initializing | listening | thinking | speaking`. The orb uses `null | thinking | listening | talking`.
- **BarVisualizer timings:** connecting = a highlight sweeps across the bars over 2000 ms; listening = 500 ms step; **thinking = fast 150 ms pulse**; speaking = bars follow real volume.
- **LiveWaveform:** `fftSize 256`, `smoothingTimeConstant 0.8`, `historySize 60`, "scrolling" mode. It averages only the **5%–40% band of frequency bins** (the speech band) per frame and pushes that into a right-to-left history.

---

## 3. 60-second demo video: what judges and devrel people say

Sources: Devpost "6 tips" https://info.devpost.com/blog/6-tips-for-making-a-hackathon-demo-video · Devpost Help https://help.devpost.com/article/84-video-making-best-practices · AngelHack https://angelhack.com/blog/10-tips-to-help-you-rock-your-next-hackathon-demo/ · TechCrunch-style 60 s tips https://ellemorrill.substack.com/p/tips-for-your-60-second-techcrunch-disrupt-demo · Gemini Live rubric https://geminiliveagentchallenge.devpost.com/

- **First few seconds:** "Explain what your app does … in the first few seconds… treat the opening seconds … as you would a movie trailer" (Devpost). Judges watch many submissions back to back.
- **Screencast over marketing video:** "Snazzy marketing videos … don't help others understand and evaluate your app" (Devpost). Show it running.
- **Script it and do multiple takes:** "Edit out the messy stuff… don't be afraid to do multiple takes" (Devpost Help). Don't speed up the audio to fit (Devpost).
- **Story:** "Open with a frustration the room has felt, then build the whole demo around the moment your product resolves it." "Create **one distinctive moment** judges will remember." Narrate the invisible work while the screen shows the visible action. Keep a recorded clean run ready (AngelHack).
- **Skip the stack talk** in 60 s, and end with a handle or URL (TechCrunch 60 s tips).
- **Structure [UNVERIFIED, from a search-result summary of Product Hunt and Indie Hackers guides I did not open]:** hook 0–3 s (the aha moment), problem 3–15 s, demo 15–45 s, close or CTA 45–60 s. About **100–150 spoken words** for 60 s.
- **Gnani-specific:** honest limitations beat faked results. Tag both hashtags, and name the models.
- **GibberLink as proof:** 70 s, one idea, one surprising moment, giant burned-in captions, two physical devices. Result: about 14M views.

### UI patterns that read well on a recorded screen (my synthesis from the above; general practice, not individually sourced)
1. **One focal point per beat.** The camera or viewer should never have to search. Dim or blur everything except the active zone (mic, then card, then phone, then seal).
2. **Large type.** Key numbers and totals at 48–72 px, line items at 22–28 px, captions at 36–56 px. Assume LinkedIn and X autoplay **muted** and viewers on phones. Burned-in captions are mandatory.
3. **Split screen: mechanic (left, workshop or laptop) and customer (right, phone frame)**, each with a fixed colour that is also used in the transcript and on the orb (GibberLink, DockVoice).
4. **High contrast on a light paper background** survives video compression better than thin grey-on-slate text. Avoid 11–12 px mono labels.
5. **Motion with meaning only:** items pop in as they are spoken, a corrected value visibly swaps, the seal thuds. No ambient particle noise.
6. **Record at 1920×1080** with browser zoom at 125–150%, bookmarks bar and extensions hidden, and a "Demo mode / Reset" control. Consider a 1:1 or 4:5 crop for feed posts.

---

## 4. Implementation snippets (vanilla, no build)

All snippets are written for this report. Each is adapted from the cited source, not copied verbatim.

### 4.1 Live mic level (RMS) from a MediaStream with AnalyserNode
Sources: MDN https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Visualizations_with_Web_Audio_API and https://developer.mozilla.org/en-US/docs/Web/API/AnalyserNode/getFloatTimeDomainData. The ×3.2 scaling follows DockVoice `frontend/src/features/voice/audio/audio.ts` ("Speech RMS rarely exceeds ~0.3").
```js
// Call from a click handler (AudioContext needs a user gesture).
async function startMicMeter(onLevel) {
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: { echoCancellation: true, noiseSuppression: false } // keep raw noise visible for the Noise Canceller story
  });
  const ctx = new AudioContext();
  const src = ctx.createMediaStreamSource(stream);
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 512;
  analyser.smoothingTimeConstant = 0.6;
  src.connect(analyser);                 // no need to connect to destination (MDN)
  const buf = new Float32Array(analyser.fftSize);
  let smooth = 0, raf = 0;
  const tick = () => {
    analyser.getFloatTimeDomainData(buf);
    let sum = 0;
    for (let i = 0; i < buf.length; i++) sum += buf[i] * buf[i];
    const rms = Math.sqrt(sum / buf.length);
    const level = Math.min(1, rms * 3.2);            // 0..1
    const db = 20 * Math.log10(rms || 1e-8);         // about -60..0 dBFS for a dB readout
    smooth += (level - smooth) * 0.25;               // ease so it breathes, not jitters
    onLevel(smooth, db);
    raf = requestAnimationFrame(tick);
  };
  tick();
  return { stream, analyser, ctx, stop() { cancelAnimationFrame(raf); stream.getTracks().forEach(t => t.stop()); ctx.close(); } };
}
```

### 4.2 Mic button with pulse rings plus a level-driven halo (CSS + 1 line of JS)
Source of the pattern: Dukaan box-shadow pulse, Call My Parts expanding rings, ElevenLabs UI state timings.
```html
<button class="mic" data-state="idle" aria-label="Bolo / Speak"><svg ...mic icon.../></button>
```
```css
.mic{--level:0;--c:#e8590c;position:relative;width:104px;height:104px;border-radius:50%;border:0;
  background:var(--c);color:#fff;display:grid;place-items:center;cursor:pointer;
  box-shadow:0 0 0 calc(var(--level)*28px) color-mix(in srgb,var(--c) 30%,transparent);
  transition:box-shadow 60ms linear}
.mic::before,.mic::after{content:"";position:absolute;inset:0;border-radius:50%;border:3px solid var(--c);opacity:0;pointer-events:none}
.mic[data-state="listening"]::before{animation:ring 1.8s cubic-bezier(.2,.6,.3,1) infinite}
.mic[data-state="listening"]::after {animation:ring 1.8s .9s cubic-bezier(.2,.6,.3,1) infinite}
.mic[data-state="thinking"]{animation:breathe .9s ease-in-out infinite;--c:#5f3dc4}
.mic[data-state="speaking"]{--c:#1864ab}
@keyframes ring{from{transform:scale(1);opacity:.65}to{transform:scale(2);opacity:0}}
@keyframes breathe{50%{transform:scale(1.06)}}
@media (prefers-reduced-motion:reduce){.mic::before,.mic::after,.mic{animation:none!important}}
```
```js
startMicMeter(l => mic.style.setProperty('--level', l.toFixed(3)));
```

### 4.3 Scrolling waveform bars on canvas (speech band only)
Port of the ElevenLabs UI `live-waveform.tsx` "scrolling" mode: 5–40% of the frequency bins, history trimmed to the canvas width.
```js
function scrollingWave(canvas, analyser, { bar = 4, gap = 3, color = '#1864ab', gain = 1.6 } = {}) {
  const ctx = canvas.getContext('2d');
  const dpr = Math.min(devicePixelRatio || 1, 2);
  const freq = new Uint8Array(analyser.frequencyBinCount);
  const hist = [];
  const fit = () => { const r = canvas.getBoundingClientRect();
    canvas.width = r.width * dpr; canvas.height = r.height * dpr; ctx.setTransform(dpr,0,0,dpr,0,0); };
  fit(); addEventListener('resize', fit);
  let last = 0;
  (function draw(t) {
    requestAnimationFrame(draw);
    if (t - last < 50) return; last = t;               // about 20 bars per second
    analyser.getByteFrequencyData(freq);
    const a = Math.floor(freq.length * .05), b = Math.floor(freq.length * .4);
    let s = 0; for (let i = a; i < b; i++) s += freq[i];
    hist.push(Math.max(.05, Math.min(1, s / (b - a) / 255 * gain)));
    const w = canvas.clientWidth, h = canvas.clientHeight, step = bar + gap, n = Math.floor(w / step);
    if (hist.length > n) hist.splice(0, hist.length - n);
    ctx.clearRect(0, 0, w, h); ctx.fillStyle = color;
    for (let i = 0; i < hist.length; i++) {
      const v = hist[hist.length - 1 - i], bh = Math.max(3, v * h * .85);
      ctx.globalAlpha = .35 + v * .65;
      ctx.beginPath(); ctx.roundRect(w - (i + 1) * step, (h - bh) / 2, bar, bh, bar / 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
  })(0);
}
```
For the "Noise Canceller" story, draw two strips: **raw mic** (grey, noisy) and **"Prisma heard"** (the transcript appearing as words). That shows the model coping with noise without inventing a fake denoise visual.

### 4.4 One state attribute drives the whole stage (bilingual labels)
```js
const STATES = {
  idle:      ['तैयार', 'Ready'],
  listening: ['सुन रहे हैं…', 'Listening to mechanic'],
  thinking:  ['पर्चा बन रहा है…', 'Building job card'],
  ringing:   ['ग्राहक को कॉल…', 'Calling vehicle owner'],
  speaking:  ['पढ़कर सुना रहे हैं', 'Reading card to owner'],
  awaiting:  ['ग्राहक की हाँ?', 'Waiting for "haan theek hai"'],
  sealed:    ['पर्चा पक्का ✔', 'Card sealed'],
};
function setState(s) {
  document.body.dataset.state = s;                 // CSS: body[data-state="ringing"] .phone{...}
  const [hi, en] = STATES[s];
  statusHi.textContent = hi; statusEn.textContent = en;
}
```
Use CSS such as `body[data-state="listening"] .mechanic-pane{outline:4px solid var(--mech)}` and `body:not([data-state="listening"]) .mechanic-pane{opacity:.55}` to enforce **one focal point per state**.

### 4.5 Phone call screen mockup (CSS)
```html
<div class="phone" data-call="ringing">
  <div class="notch"></div>
  <div class="call-top"><small>Kaam ka Parcha · Workshop line</small>
    <div class="avatar">RK</div><h2>Ramesh ji</h2><p class="num">+91 98XXX XX210</p>
    <p class="call-status"><span class="ringing-txt">Calling…</span><span class="timer">00:00</span></p></div>
  <div class="caption" aria-live="polite"></div>
  <div class="call-actions"><button class="end" aria-label="End">✆</button></div>
</div>
```
```css
.phone{width:340px;aspect-ratio:9/19.5;border-radius:44px;padding:14px;background:#0b0f14;border:10px solid #1c1f24;
  box-shadow:0 30px 60px rgba(0,0,0,.35),inset 0 0 0 2px #2b2f36;color:#fff;display:flex;flex-direction:column;position:relative;
  background-image:radial-gradient(120% 70% at 50% 0%,#1b3a4b 0%,#0b0f14 70%)}
.notch{width:110px;height:26px;border-radius:0 0 16px 16px;background:#000;margin:-14px auto 8px}
.call-top{text-align:center;margin-top:28px}
.call-top small{opacity:.6;font-size:13px}
.avatar{width:96px;height:96px;margin:18px auto 12px;border-radius:50%;display:grid;place-items:center;font:700 34px/1 system-ui;background:#2f9e44;position:relative}
.phone[data-call="ringing"] .avatar::before,.phone[data-call="ringing"] .avatar::after{content:"";position:absolute;inset:0;border-radius:50%;border:2px solid #69db7c;animation:ring 1.6s infinite}
.phone[data-call="ringing"] .avatar::after{animation-delay:.8s}
.call-top h2{font:600 28px/1.1 system-ui;margin:0}
.num{opacity:.65;margin:.3em 0 0;font-variant-numeric:tabular-nums}
.call-status{font:500 17px system-ui;opacity:.85}
.phone[data-call="ringing"] .timer,.phone[data-call="live"] .ringing-txt{display:none}
.caption{margin:auto 6px 18px;padding:14px 16px;border-radius:18px;background:rgba(255,255,255,.1);font:500 20px/1.35 'Mukta',system-ui;min-height:3.2em}
.call-actions{display:flex;justify-content:center;padding-bottom:18px}
.end{width:68px;height:68px;border-radius:50%;border:0;background:#e03131;color:#fff;font-size:28px;transform:rotate(135deg)}
@keyframes ring{from{transform:scale(1);opacity:.8}to{transform:scale(1.8);opacity:0}}
```
Timer: `let t0=Date.now(); setInterval(()=>{const s=(Date.now()-t0)/1000|0; timer.textContent=String(s/60|0).padStart(2,'0')+':'+String(s%60).padStart(2,'0')},500)`. Call-status vocabulary taken from Call My Parts: "Calling…", "Answered", "Not picked up", "Line busy".

### 4.6 Job slip / receipt with perforated edges and a tear line
The technique (radial-gradient masks for bites and notches) is from Temani Afif's https://css-shape.com/ (its ticket "circle-cut" shape uses `mask:radial-gradient(30px at 30px 50%,#0000 98%,#000)-30px 50%`). See also https://css-shape.com/scalloped-box/, https://css-shape.com/zig-zag-box/ and https://css-generators.com/custom-borders/.
```css
.parcha{--paper:#fffaf0;--ink:#1d2a5b;--bite:7px;--gap:18px;
  width:min(440px,100%);position:relative;padding:34px 26px 40px;background:var(--paper);color:#222;
  font-family:'Mukta','Noto Sans Devanagari',system-ui,sans-serif;
  filter:drop-shadow(0 12px 22px rgba(0,0,0,.18));          /* drop-shadow follows the mask edge */
  /* perforated top and bottom edges: semicircle bites, two half-height layers added together */
  -webkit-mask:
    radial-gradient(circle var(--bite) at 50% 0,#0000 98%,#000) 0 0/var(--gap) 51% repeat-x,
    radial-gradient(circle var(--bite) at 50% 100%,#0000 98%,#000) 0 100%/var(--gap) 51% repeat-x;
          mask:
    radial-gradient(circle var(--bite) at 50% 0,#0000 98%,#000) 0 0/var(--gap) 51% repeat-x,
    radial-gradient(circle var(--bite) at 50% 100%,#0000 98%,#000) 0 100%/var(--gap) 51% repeat-x;
  background-image:repeating-linear-gradient(#0000 0 31px,#e9e1cc 31px 32px);   /* faint ruled-notebook lines */
}
.parcha .tear{height:0;border-top:2px dashed #cfc6ad;margin:20px -26px;position:relative}
.parcha .tear::before,.parcha .tear::after{content:"";position:absolute;top:-12px;width:22px;height:22px;border-radius:50%;background:var(--page-bg,#efe7d6)}
.parcha .tear::before{left:-11px}.parcha .tear::after{right:-11px}
.parcha .line{display:grid;grid-template-columns:1fr auto;gap:12px;font-size:22px;padding:6px 0;animation:rise .35s both;animation-delay:calc(var(--i)*80ms)}
.parcha .line .hi{display:block;font-size:15px;opacity:.65}
.parcha .amt{font-variant-numeric:tabular-nums;font-weight:700;color:var(--ink)}
.parcha .total{font-size:44px;font-weight:800;color:var(--ink)}
@keyframes rise{from{opacity:0;transform:translateY(12px);filter:blur(4px)}}   /* from Ira */
```
The `--i` stagger comes from DockVoice (`0.08 * index`) and the rise and blur from Ira. Put the drop shadow on a wrapper if your target browser clips it.

### 4.7 Rubber-stamp SEAL animation (CSS port of DockVoice's spring)
DockVoice uses `initial {opacity:0, scale:2.4, rotate:-24}`, `animate {scale:1, rotate:-12}`, `delay .35s`, `spring stiffness 520 damping 18`.
```html
<svg width="0" height="0" style="position:absolute"><filter id="ink"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="3"/></filter></svg>
<div class="seal" aria-hidden="true"><b>पक्का</b><span>SEALED · 05-10-2026 · #KP-0142</span></div>
```
```css
.seal{position:absolute;right:20px;bottom:70px;padding:8px 16px;border:5px double #c92a2a;border-radius:12px;color:#c92a2a;
  text-align:center;line-height:1.05;transform:rotate(-12deg);opacity:0;filter:url(#ink);mix-blend-mode:multiply;pointer-events:none}
.seal b{display:block;font:800 34px/1 'Mukta',sans-serif;letter-spacing:.06em}
.seal span{font:700 11px/1.4 ui-monospace,monospace;letter-spacing:.14em}
.parcha.sealed .seal{animation:stamp .5s cubic-bezier(.2,1.5,.4,1) .35s both}
.parcha.sealed{animation:thud .22s .62s ease-out}
.parcha.sealed .line{filter:saturate(.85)}               /* the card looks "locked" */
@keyframes stamp{0%{opacity:0;transform:scale(2.4) rotate(-24deg)}
                 60%{opacity:1;transform:scale(.94) rotate(-11deg)}
                 100%{opacity:.92;transform:scale(1) rotate(-12deg)}}
@keyframes thud{50%{transform:translateY(3px) scale(.995)}}
```
Pair it with a short "thump" audio sample and `navigator.vibrate?.(30)`. In the video the stamp is the **single memorable moment** AngelHack recommends.

### 4.8 Correction swap ("brake pad 1,200 nahi, 950")
Pattern from DockVoice `ReceivedValue`: the old value exits upward struck through and the new one springs in.
```css
.amt-swap{display:inline-grid;overflow:hidden;vertical-align:bottom}
.amt-swap>span{grid-area:1/1}
.amt-swap .old{animation:out .5s forwards;text-decoration:line-through 3px #e03131}
.amt-swap .new{animation:in .45s cubic-bezier(.2,1.4,.4,1) .15s both}
.line.changed{animation:flash 1.4s}
@keyframes out{to{transform:translateY(-100%);opacity:0}}
@keyframes in{from{transform:translateY(100%) scale(1.3);opacity:0}}
@keyframes flash{from{background:#fff3bf}}
```
For video, consider keeping a small struck-through `₹1,200` next to the new `₹950` for about 2 s so muted viewers can see what changed.

### 4.9 Highlight the spoken words that produced each field
Adapted from DockVoice `TranscriptFeed.tsx` (regex on numbers and ids). Ideally the extractor returns an `evidence` substring per line item.
```js
const esc = s => s.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function renderTranscript(text, items) {           // items: [{id, evidence:"brake pad ka 1200"}]
  let html = esc(text);
  items.forEach(it => { if (!it.evidence) return;
    const e = esc(it.evidence);
    html = html.replace(e, `<mark data-line="${it.id}">${e}</mark>`); });
  // fallback: highlight bare amounts and Hindi number words
  html = html.replace(/(₹\s?[\d,]+|\b\d[\d,]*\b|\b(?:sau|hazaar|hazar|dedh|dhai|saade)\b)(?![^<]*<\/mark>)/gi, '<b class="num">$1</b>');
  transcriptEl.innerHTML = html;
}
transcriptEl.addEventListener('mouseover', e => {
  const id = e.target.closest('mark')?.dataset.line;
  document.querySelectorAll('.line').forEach(l => l.classList.toggle('linked', l.dataset.id === id));
});
```
When a new item arrives, flash both its `<mark>` and its `.line` in the same colour. A line drawn between them in the split view is optional.

### 4.10 Indian number formatting and a count-up total
```js
const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
inr.format(250000);   // "₹2,50,000" (matches Timbre's lakh cadence)
function countUp(el, to, ms = 700) { const from = +el.dataset.v || 0, t0 = performance.now();
  (function f(t){ const k = Math.min(1,(t-t0)/ms), v = from + (to-from)*(1-Math.pow(1-k,3));
    el.textContent = inr.format(Math.round(v)); if (k<1) requestAnimationFrame(f); else el.dataset.v = to; })(t0); }
```

### 4.11 Fonts (Google Fonts)
`Noto Sans Devanagari` is confirmed in use (Dukaan). **[UNVERIFIED but well-known Google Fonts Devanagari families]:** Mukta, Hind, Baloo 2, Tiro Devanagari Hindi, Yatra One (display). One link example: `https://fonts.googleapis.com/css2?family=Mukta:wght@400;600;800&family=Noto+Sans+Devanagari:wght@400;700&display=swap`. Use a **bilingual label pattern**: Devanagari or Hinglish large, English small underneath (Munim AI and NagarDrishti both ship Hindi, English and Marathi UIs).

---

## 5. Suggested visual direction for Kaam ka Parcha (synthesis)

- **Page:** warm workshop paper (`#efe7d6` page, `#fffaf0` slip), dark ink-blue numbers (`#1d2a5b`), saffron or safety-orange action colour (`#e8590c`), stamp red (`#c92a2a`), WhatsApp green only for the final message. This is MaestrIA's warm paper look with Dukaan's saffron.
- **Layout for recording:** left is the **mechanic pane** (mic, scrolling raw-noise waveform, Hinglish live caption at 36 px or more). Centre is the **parcha** (job slip with lines popping in). Right is the **phone frame** for the owner, with call status, timer and TTS caption. One active pane at a time, the rest dimmed.
- **Seal moment:** the owner says "haan theek hai", the phone caption highlights it, the stamp thuds onto the slip, and the slip slides into a WhatsApp bubble mock with the PDF chip.
- **Local identity:** a workshop name and city on the slip header (e.g., "Sharma Auto Works · Karol Bagh", synthetic), a job number, vehicle number plate in the Indian plate style (synthetic), Hinglish item names with an English subline, rupee amounts in en-IN format.

---

## 6. 60-second demo checklist (UI side)

| Time | Screen | Must be readable muted |
|---|---|---|
| 0–3 s | **Cold open on the product.** Engine noise audible, mechanic speaking Hinglish, first 2 line items pop onto the slip with ₹ amounts | Burned-in Hinglish + English caption of what he said |
| 3–8 s | Problem in one line overlaid: "Mechanic bolta hai. Owner ko phone pe samajh nahi aata. Bill pe jhagda." | Max ~10 words on screen |
| 8–25 s | Extraction: lines animate in with the spoken words highlighted. Raw-noise waveform visibly loud (Noise Canceller). Total counts up | Total at 48 px or more |
| 25–40 s | Split screen: phone rings, owner hears the TTS readback (Timbre, ₹ in lakh cadence). Owner corrects one item, and the swap animation plays | Old value struck through, new value highlighted |
| 40–50 s | "Haan theek hai" → **SEAL stamp thud** → PDF + WhatsApp bubble | The one memorable moment |
| 50–60 s | End card: who it's for, "Built on Gnani Prisma v2.5 · Timbre v2.5 · Evon v3.3", one honest limitation, hashtags #GreatIndianAIInternshipChallenge #GnaniAI | Large, 3 lines max |

Pre-flight: 1080p, 125–150% zoom, Demo/Reset button, synthetic names and numbers only, real pipeline (no faked outputs), a recorded clean take as backup, script of 100–150 words **[UNVERIFIED rule of thumb]**, at least 3 takes, captions burned in, cuts tightened in editing (Devpost: "edit out the messy stuff").

---

## 7. Gaps and unverified items
- First-5-second content of most demo videos was **not verified**. YouTube blocked fetches, and there was no yt-dlp or ffmpeg to pull frames. Only the thumbnails and lengths for GibberLink and MaestrIA were checked.
- Prize status of DockVoice, Ira, Dukaan, Munim AI and FieldPilot is unconfirmed. The Cartesia x Anthropic, Hume, Retell, Vapi, Deepgram and Groq winner lists were not obtained (pages failed or no list was published), and the ElevenHacks 2026 site sat behind a Vercel checkpoint.
- The 60-second section timings (hook 0–3, problem 3–15, …) come from search-result summaries, not opened pages.
