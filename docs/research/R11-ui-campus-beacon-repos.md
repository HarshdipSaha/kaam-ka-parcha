# Research B: CampusEvac and Beacon Night Shift, UI/UX lessons for Kaam ka Parcha

Researched 5 Oct 2026. Both repos were cloned with `git clone --depth 1` into this scratchpad:

- `campus/`: https://github.com/AfreenInnovates/campus, `main` @ `568a585` (28 Sep 2026, "phone")
- `Beacon/`: https://github.com/Prashant-thakur77/Beacon, `main` @ `03247db` (29 Sep 2026). This is the First Commit entry, tagged `first-commit-submission`.
- `Beacon-assemblyai/`: the same repo, branch `assemblyai` @ `6981d9e` (29 Sep 2026). This is the later AssemblyAI Voice Agent hackathon entry. It adds the phone channel, the consent certificate and the audit page.

**Caveat:** both repos were committed to after First Commit judging (17 to 20 Sep 2026). What I read here is close to the judged build but may not match it exactly. Beacon's own docs say the light theme shipped on 20 Sep, judging day (`docs/STATUS.md`).

Paths below are relative to the clone roots unless they are full URLs.

---

## 0. The hackathon (verified)

Both projects won prizes at the same event: **WeMakeDevs x AWS "First Commit"**, Event 01 of the **Bharat Builds Tour**. It ran 17 to 20 Sep 2026, online, with an optional in-person day in Bangalore on 19 Sep. Entrants were university students in teams of 1 to 4.

- Winners page: https://www.wemakedevs.org/aws/first-commit/projects
- Event page: https://www.wemakedevs.org/aws/first-commit

| Place | Category | Project | Team | Prize |
|---|---|---|---|---|
| 1st | Ship It | Suraksha (agentic companion for an ageing parent) | StarBugs | INR 2,00,000 + $3,000 AWS credits |
| **2nd** | **Build It** | **Beacon Night Shift** | CoffeAndCode (@prashantthakur77, solo) | INR 1,50,000 + $2,000 credits |
| **3rd** | **Best UI** | **CampusEvac** | 3 BUILDS (@abhishekshiv, @afreen007, @imakii) | INR 1,00,000 + $1,000 credits |

The event page lists these judging criteria: real-world problem-solving impact, AWS integration (mandatory), **"clean and obvious" design over complexity**, functional execution, and a **three-minute demo video**. The Best UI prize was "for exceptional design and usability across either track".

**Beacon also entered the lablab.ai AssemblyAI Voice Agent Hackathon** (1 to 30 Sep 2026; five flat winners, each $1k cash + $1k credits). That entry is the `assemblyai` branch. I could not verify whether it won: the lablab recap page (https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon) did not load and searches found no results announcement. Treat it as **entered, result unknown**.

Demo media:

- CampusEvac film: https://youtu.be/FhgTfCz0ou8 (YouTube metadata could not be fetched). Live app: https://main.d3skpx6qxc85hh.amplifyapp.com/
- Beacon First Commit film: https://youtu.be/a3SxZHvIkCo ("Beacon Night Shift — the on-call agent that fixes the 3 AM page with your voice")
- Beacon AssemblyAI cut (4:48), deck PDF and SRT: https://github.com/Prashant-thakur77/Beacon/releases/tag/v0.6.0
- Beacon blog: https://builder.aws.com/post/3Jb5v7ouXDReILJ7WMuHrlB1leL_p/why-transcript-is-the-safety-artifactvoice-approved-aws-remediation-with-strands-and-step-functions
- Beacon live console: https://6die6lduac6ipxkeg73nxsuvpu0yzkim.lambda-url.us-east-1.on.aws/ (passcode-gated for voice)

---

## 1. CampusEvac, the Best UI winner

### 1.1 What it is

CampusEvac is a two-player, real-time fire-evacuation drill in the browser.

- The **evacuee** walks a smoky 3D campus in first person and works through 6 objectives plus the exit.
- The **warden** watches from overhead. They observe and verify sensor evidence, send one route message, and get one ventilation override.

Neither player can finish alone. The narrator uses Amazon Polly. At the end, the evacuee can ask for an emailed report (Amazon SES), and a server-side check verifies the run against the drill record. Source: `README.md`. Footer credit: "CampusEvac / Bharat Builds Tour / AWS × WeMakeDevs" (`app/page.tsx:464`).

### 1.2 Target audience and how the UI is tailored

The README names the audience: "Schools, colleges, universities, and offices", and specifically the **warden / safety-officer role**. In practice the UI is aimed at **students playing on a phone or laptop**:

- **Game-poster look.** The language is neo-brutalist and game-like: sticker labels rotated -2deg/+1deg, huge uppercase headlines, a mascot. A student would read it as a game, not as compliance training.
- **Approachable illustration.** A chibi student mascot runs with an access card (`public/mascot.webp`). The hero is an isometric cut-away of the building at sunset, with smoke, a red blocked door, a green exit beacon and a warden at a console (`public/facility.webp`). Both look AI-generated; the facility image has what looks like a Gemini sparkle watermark in its bottom-right corner.
- **Safety-grade honesty.** The footer and ticker repeat "A training simulation, not live emergency guidance". Debrief language mirrors a real fire-drill debrief: "Did we get out safely? / Where did coordination slip? / What do we practise next?" (`app/simulation/DrillShell.tsx:999-1015`).
- **Phone-first in practice.** It detects coarse pointers everywhere (`useCoarsePointer.ts`) and blocks portrait with a "Turn your phone" overlay that animates a rotating phone. Edges are padded for safe areas and notches, and the HUD panels drop backdrop blur on phones to save GPU.

### 1.3 Stack and file layout

- Next.js 16 App Router, React 19, TypeScript, **Tailwind v4** (`@import "tailwindcss"` with `@theme inline` tokens in `app/globals.css`), and Hugeicons (`@hugeicons/react`, `@hugeicons/core-free-icons`).
- 3D uses React Three Fiber, drei, Rapier and postprocessing. State is Zustand.
- AWS pieces: AppSync Events for realtime, DynamoDB, Polly (narration pre-rendered by `scripts/synth-voice.mts`, plus a live route in `app/api/narration/route.ts`), SES for the report, and Amplify hosting.
- Key UI files:
  - `app/globals.css` (535 lines): every token and component class
  - `app/page.tsx`: landing page
  - `app/components/Depth.tsx`: parallax, tilt and reveal
  - `app/simulation/rooms/page.tsx`: lobby
  - `app/simulation/room/[code]/RoomClient.tsx`
  - `app/simulation/DrillShell.tsx` (1,882 lines): every HUD, overlay, briefing, end card and mailer
  - `app/api/report/email.ts`: HTML email
  - `app/simulation/components/BriefingArtwork.tsx`: inline SVG slides

### 1.4 Design tokens

From `app/globals.css:3-19`, under the comment "neo-brutalism: warm paper, plum ink, hard shadows, sunset accents":

| Token | Hex | Use |
|---|---|---|
| `--ink` | `#1d1626` | text, all borders, all hard shadows |
| `--ink-soft` | `#5c5066` | secondary text |
| `--paper` | `#f8f2ea` | page background |
| `--paper-deep` | `#eee3d5` | |
| `--paper-light` | `#fffaf3` | cards and inputs |
| `--sun` | `#ffc44d` | primary button, selection, highlight block (hover `#ffd57a`) |
| `--coral` | `#ff6a3d` | accent word, dark-panel shadow |
| `--violet` | `#7b5cff` | focus ring, role 1 |
| `--mint` | `#2fd18f` | success, live, verified |
| `--danger` | `#ef3b4b` | errors, hazard |
| `--night` | `#16111e` | dark panels and HUD; also `themeColor` |

Other colours:

- The email uses its own inline constants: INK `#16111e`, PAPER `#fdf7ed`, SUN `#f5a524`, MINT `#10b981`, CORAL `#ff6a3d`, outer background `#efe7db` (`app/api/report/email.ts:5-9`).
- The warden command deck hard-codes `#facc15` (observe), `#10b981` (verify), `#38bdf8` (send route), `#a78bfa` (clear smoke) and `#9a8fa3` (waiting) (`DrillShell.tsx:640-645`).
- The briefing SVGs use `#10151d`, `#55c7ff`, `#71f0c0`, `#ffd45c` and `#ff6b72`.

**Fonts.** Geist and Geist Mono via `next/font/google`, **latin subset only** (`app/layout.tsx:5-13`). Type is dominated by `font-black` (900) uppercase, letter-spacing 0.12 to 0.2em on labels and -0.05 to -0.07em on headlines. The hero is `text-[clamp(3.2rem,9vw,7.5rem)] leading-[0.82] tracking-[-0.06em]`. Step numbers are outlined: `.brutal-num` uses `-webkit-text-stroke: 2px var(--ink); color: transparent` with tabular numerals.

**Borders, radii and shadows.**

- Borders are 2 to 3px ink everywhere. Radii are **0**; the only rounded things are keycaps (0.35rem) and status dots.
- Shadows are hard offsets: `4px 4px 0 var(--ink)` on buttons, 7 to 8px on panels and cards, 10 to 12px on slabs. Dark panels cast a coral shadow (`7px 7px 0 var(--coral)`).
- The in-game HUD uses a softer three-layer shadow plus blur (`.hud-panel`, lines 170-180).

**Background.** `.brutal-grid` draws a 24px graph-paper grid of 6% ink lines on paper (lines 67-73).

**Icons.** Hugeicons, stroke width 2.2 to 2.8, sizes 13 to 44 px, usually inside 44px ink-bordered squares filled with a token colour (`app/page.tsx:300, 386`).

**Motion** (all in `globals.css`, all off under `prefers-reduced-motion`):

- Buttons lift on hover (`translate(-1px,-1px)` with a 6px shadow) and press down on `:active` (`translate(3px,3px)` with a 1px shadow), 140ms.
- `.signal-pulse` loops 1.8s for live dots. `.hud-rise` brings toasts in over 320ms with `cubic-bezier(0.22,0.8,0.24,1)`.
- `.room-title` animates letter-spacing over 2.8s. `.air-vignette.gasping` reddens the screen edges when air runs low.
- `.brutal-ticker` is a 34s marquee.
- `Depth.tsx` drives pointer parallax, a card tilt whose shadow swings opposite the tilt (`.tilt-shadow`), and an IntersectionObserver reveal with stagger. The reveal "fails open" after 2.5s so content can never stay invisible.

**Theme.** A light paper landing page and lobby; a dark night HUD in-game and for dark panels. Each surface keeps one mode; there is no toggle.

### 1.5 Screen-by-screen

**1. Landing** (`app/page.tsx`)

- Sticky nav with an ink square logo (an SVG exit arrow) and "Campus**Evac**" with "Evac" in coral.
- A black ticker strip: "Two players ◆ One building ◆ Smoke reaches the east route at 52 seconds ◆ The warden sees what you can't ◆ No game server…".
- Hero: two rotated stickers ("Co-op evacuation drill", "3D in the browser"). Headline **"Two views. / One *safe* / [exit.]"**, with "exit." on a sun-yellow slab with an 8px shadow. One-paragraph lede.
- CTAs in priority order: a sun-filled **Start a drill →**, a paper **Practice solo**, and an underlined text link **Join with a code**.
- The right side shows the illustration in a "CCTV screen" frame. Its title bar reads "Science Block / Level 1" with a pulsing mint "drill live" dot. A sticker reads "Talk them out".
- Below the hero:
  - A three-cell stat slab ("2 roles", "7 steps", "8 min"), each cell a different colour.
  - Four numbered "How a drill works" cards.
  - Role cards: light/violet for the evacuee, night/coral for the warden.
  - Seven objective tiles with icons.
  - A dark "No game server." AWS slab with a sun shadow.
  - The final CTA "Grab a partner. Find the exit."

**2. Lobby** (`app/simulation/rooms/page.tsx`)

- Headline "Set the / crew loose."
- Two panels side by side: a light **New drill room** panel (labelled `CREATE_01`) and a dark **Join with a code** panel (`JOIN_02`). The code input uses a wide-tracked mono font, `tracking-[0.3em]`.
- A three-step strip explains the flow. The error state is a red left-border line: "That does not look like a room code."

**3. Onboarding modal** (`DrillShell.tsx:1112`)

- A "How to play" tag and a role-specific headline: "Six steps. Then get out." or "You see the danger. Talk them out."
- Numbered steps, a keycap legend that switches to touch labels on phones, and one full-width primary button.

**4. Briefing modal** (`DrillShell.tsx:1216`)

- "Listen first. Then move." with an `n/4` counter and a "controls locked" label.
- SVG slide artwork, then a **Narrator** caption box with a sun left border and `aria-live`. A Bedrock badge appears when the line came from Bedrock.
- A sun progress bar, a **Voice: on/off** toggle and **Skip briefing**.

**5. In-game HUD** (`image1.png`, `image3.png`, `image8.png`)

- Top left: brand and location, then an objectives checklist. Only the current objective is expanded, with directions in sun-yellow.
- Top right: minimap and a "Live / Connecting / Offline practice" badge.
- Bottom left: Health and Air bars. Bottom centre: the caption bar ("NARRATOR Central corridor. The west door leads to…") and a key strip that hides after 25s.
- Top centre: a hazard banner, e.g. "SMOKE IN THIS AREA / Keep moving and watch for warden messages".

**6. Warden command deck** (`DrillShell.tsx:608-706`)

- A "Next action" header with a three-step track ("✓ Observe — 2 Verify — 3 Send route").
- **One big button carries the single action that is ready now, with a one-line "why"** underneath. Locked actions are not drawn; the track already shows what comes next.
- After use, the button flashes "Sent" for 900ms and plays an audio blip.

**7. End card** (`image4.png`)

- A tag ("Drill complete" in mint, or "Drill ended" in coral) and the headline "You got out safely." or "Not this time.".
- A three-cell mono stat table (Time 1:04, Steps 6/6, Health 76).
- Three debrief Q&As with coloured left borders (mint, sun, violet).
- The **VerificationBadge** ("Verified against the drill record", mint, or "Unverified" plus reasons, coral) and the **ReportMailer**.
- Buttons: "Play again" and "Exit to home".

**8. Email report** (`image5.png`, `image6.png`)

- The same brutalist look rebuilt with inline styles and tables: a "Drill report" tag, the headline, "Score 100/100 · Exemplary", a 6-cell stat grid, objective splits with mono times (mint, or coral "missed"), a "How the score was reached" table (+50/50 …), and findings with sun left borders.
- Footer: "Every figure above was measured during your drill."

**States covered (worth copying):**

- **Loading:** "Loading the Science Block..." and "Preparing your briefing...".
- **Waiting:** "Waiting for the sector feed."
- **Disconnect:** a full-screen "Connection lost / Waiting for {name}" overlay with a 60px mono countdown, a draining bar, and "Air and smoke are frozen until they are back".
- **Mailer** stages idle → sending → verify ("One step first… Keep this page open" with a pulsing square) → sent, plus error. The error copy reads "Could not reach the server. Check your connection."
- **Verification is advisory and fails silent.** If the check cannot run, nothing is shown, "rather than accusing a player of cheating because of an infrastructure problem" (`DrillShell.tsx:736-743`).

**Mobile approach:**

- `@media (pointer: coarse)` plus a `useCoarsePointer` hook swaps layouts: compact headers, two-column modals sideways, collapsible warden panels (`PhoneCollapsible`).
- Twin-thumb controls in `TouchControls.tsx`.
- Safe-area classes (`.safe-x`, `.safe-bottom`, `.hud-left/right`) and `--touch-dock-h` measured at runtime.
- `viewportFit: "cover"` and `interactiveWidget: "resizes-content"` (`app/layout.tsx:26-32`).

### 1.6 Voice / AI interaction patterns

- **Narration is caption-first.** "Caption first: composed locally, so it lands the instant the event does and never waits on the voice" (`DrillShell.tsx:398`).
- Voice lines are authored constants pre-rendered to MP3 with Polly "Matthew" neural (`narration-script.ts:20-21`, `public/voice/manifest.json`). That means no network wait during a run, plus a server route that synthesises and caches live situational lines (`app/api/narration/route.ts`).
- **The briefing waits for a real user gesture** before talking, which is also the autoplay unlock (`DrillShell.tsx:1278-1290`; `audio.ts` `bindUnlock`).
- Alerts and command acknowledgements are synthesised WebAudio beeps (`audio.ts` `playSignal`), so critical feedback needs no network.
- **There is no speech input.** It is voice-out only.
- **i18n: none.** Everything is English, `lang="en"`, with a US English voice, even though the event was the Bharat Builds Tour.

### 1.7 Snippets worth borrowing

**Hard-shadow press button** (`app/globals.css:99-123`):

```css
.brutal-button{display:inline-flex;align-items:center;justify-content:center;border:2px solid var(--ink);
  background:var(--sun);color:var(--ink);box-shadow:4px 4px 0 var(--ink);font-size:.72rem;font-weight:800;
  letter-spacing:.12em;text-transform:uppercase;transition:transform 140ms ease,box-shadow 140ms ease,background 140ms ease}
.brutal-button:hover{background:var(--sun-hover);transform:translate(-1px,-1px);box-shadow:6px 6px 0 var(--ink)}
.brutal-button:active{transform:translate(3px,3px);box-shadow:1px 1px 0 var(--ink)}
```

**Sticker label** (lines 336-347) and **graph-paper ground** (lines 67-73):

```css
.brutal-sticker{display:inline-flex;align-items:center;gap:.45rem;border:3px solid var(--ink);box-shadow:4px 4px 0 var(--ink);
  padding:.3rem .7rem;font-size:.6rem;font-weight:900;letter-spacing:.2em;text-transform:uppercase}
.brutal-grid{background-color:var(--paper);background-image:linear-gradient(rgba(29,22,38,.06) 1px,transparent 1px),
  linear-gradient(90deg,rgba(29,22,38,.06) 1px,transparent 1px);background-size:24px 24px}
```

**Toast arrival and live-dot pulse** (lines 212-243):

```css
@keyframes hud-rise{from{opacity:0;transform:translate3d(0,12px,0) scale(.982)}to{opacity:1;transform:none}}
.hud-rise{animation:hud-rise 320ms cubic-bezier(.22,.8,.24,1) both}
.signal-pulse{animation:signal-pulse 1.8s ease-in-out infinite}
@keyframes signal-pulse{0%,100%{opacity:.55;transform:scale(.92)}50%{opacity:1;transform:scale(1)}}
```

**Patterns that port to vanilla JS:**

- The **next-action deck** (`DrillShell.tsx:632-706`): a three-step track plus one primary button with a "why" sub-line.
- **Reveal that fails open** (`Depth.tsx:158-205`): an IntersectionObserver plus a 2.5s `setTimeout(show)` safety net.
- The **email report** (`app/api/report/email.ts`): inline-styled table HTML. The same technique would work for a printable or PDF job card.

### 1.8 What likely impressed judges, and what is weak

**Impressed:**

1. An instantly distinctive, coherent visual system: warm paper with hard ink shadows and sunset accents, carried consistently from landing to lobby to modals to the email.
2. Real craft in motion and depth that degrades properly on phones and under reduced motion.
3. A polished 3D world on top of all that.
4. Every flow has a designed state: loading, disconnect, verify, error and debrief.
5. A clear two-role story told in four words: "Two views. One safe exit."
6. An emailed report that looks like the app.

**Weak:**

- English only, with an American narrator, for an Indian student audience.
- Very small type: 9 to 11px uppercase labels everywhere, which hurts legibility.
- No voice input, despite a "talk them out" theme.
- Possibly AI-generated hero art (watermark-like mark).
- Heavy Three.js load. DrillShell is a 1,900-line file.
- Colour tokens drift: the command deck hard-codes Tailwind hexes outside the palette.
- The game is landscape-only on phones.

---

## 2. Beacon Night Shift, Build It winner (2nd overall)

### 2.1 What it is

Beacon is a voice on-call agent for AWS. When an alarm fires, it:

1. reads the logs with Bedrock Nova 2 Lite;
2. finds the CloudTrail change behind the alarm;
3. checks it against a golden security-group snapshot;
4. proposes **one allowlisted fix**, dry-run under a locked-down role.

The engineer then has to say the exact phrase **"approve fix one"**. Consent is checked against the raw transcript, never against the model's tool arguments. A Step Functions loop applies the fix and only reports recovered when CloudWatch agrees on three checks.

The engineer can then say "grant contract for seven days" to create a **Sleep Contract**: scoped and expiring, with their own quote as the record. The repeat fault is then fixed without waking anyone.

The `assemblyai` branch adds:

- full duplex on the AssemblyAI Voice Agent API, with **barge-in that withdraws the fix** being read back;
- a **phone channel** at 8 kHz µ-law with dual-channel recording;
- Telegram voice notes;
- a **consent certificate**;
- an **audit page with ▶ Listen**;
- pull requests opened by voice;
- Hinglish in and out.

Sources: `Beacon/README.md`, `Beacon-assemblyai/README.md`.

### 2.2 Target audience and how the UI is tailored

The audience is "solo engineers and small teams (in India o…)" running production for another time zone: "alone, half-asleep, phone in hand, no laptop" (`docs/submission.md:11`; film rows 1, 22 and 14 in `video/script-assemblyai.md`). The UI is tailored to that one emotional outcome, **going back to sleep**:

- **The vocabulary is the user's.** "Night Board", "awaiting your word", "humans woken", "sleep protected · night IST", "☾ Resolved under Sleep Contract", "All quiet. Waiting for the next page."
- **Colour is spent only on state.** From the header comment in `web/src/theme.css:1-6`: coral means needs you, amber means warning, deep green means proven, pink means handled under a Sleep Contract, lavender means the one thing to press.
- **Phone-first incident mode** (`Talk.tsx:170`, `theme.css:706-721`). Under 760px the Talk panel moves above the feed (`order:-1`), the mic grows to 88px, a row of three big phrase chips appears, and the composer becomes sticky at the bottom: "one-thumb incident mode".
- **Built for the judge.** A "How to judge this in 90 seconds" disclosure, a **▶ Run the night** button that auto-plays the whole scenario, an archived-run replay when the deployment is empty, a "?" help FAB, and "proof" lines citing the source file and test for every claim (`Landing.tsx` FEATURES `proof`; the Safety page "enforced in / proven by").

**A design pivot worth knowing about.** `docs/PLAN.md:247` planned a **dark** "night shift" theme (`#0B1020` background, amber `#FFB020`, green `#2ED47A`, lilac `#B8A6FF`; "Dark only (light theme cut)"). On submission day it was replaced with a **light editorial theme** "inspired by Wispr Flow" (`docs/STATUS.md:11`, `CHANGELOG.md:60`). In other words, the team moved away from the generic dark developer dashboard, which is the same decision Kaam ka Parcha faces now.

### 2.3 Stack and file layout

- Vite + React 18 + TypeScript, **no component library**, all hand-written CSS in one file: `web/src/theme.css` (669 lines on main, 721 on `assemblyai`).
- Google Fonts are loaded via `<link>` in `web/index.html:19-21`.
- Motion helpers live in `web/src/motion.ts` (no animation library).
- Backend: Python Lambdas plus FastAPI for local mode.
- Components (`web/src/components/`): `Landing`, `NightBoard` (tally, incident cards, archived-run card), `Talk` (push-to-talk cascade), `TalkDuplex` (AssemblyAI full duplex), `Timeline`, `Contracts`, `Safety`, `Analytics`, `Reports` (postmortem, audit, morning report), `Chrome` (announcement strip, footer, toasts, help popover), `Marquee`, `Sparkline`.
- Voice clients are in `web/src/voice/*.ts`: Transcribe streaming, Web Speech, AssemblyAI, and a PCM worklet player.

### 2.4 Design tokens

From `web/src/theme.css:7-49`. The values are identical on `main` and `assemblyai`.

| Token | Hex | Meaning |
|---|---|---|
| `--cream` | `#ffffeb` | page ground, `theme-color` |
| `--paper` | `#fffdf9` | cards, topbar |
| `--beige` | `#e4e4d0` | nav pill track, pillars, "Proof" panel |
| `--deep` | `#034f46` | deep green: proven/verified, mic panel, announcement strip, stats band |
| `--ink` | `#1a1a1a` | text; ink-70 / ink-50 alphas for dim / faint |
| `--lavender` | `#f0d7ff` | **the one thing to press** (primary button, hover `#e9c8ff`), selection |
| `--coral` | `#ff6c4c` | needs you, active nav underline, beacon dot |
| `--warn` | `#ffa946` | warning, the "listening" state text |
| `--pink` | `#ffbcf2` | Sleep Contract / handled while you slept, evidence chips |
| `--red` | `#c9330f` | coral darkened for 12px text (contrast) |
| `--line` / `--line-strong` | `rgba(26,26,26,.15)` / `.4` | hairlines |

Fonts:

- `--font-display` is **EB Garamond** 400/500 plus italic: "one serif statement per screen", with an `<em>` italic half-line, e.g. "The 3 AM page, *fixed with your voice.*"
- `--font-ui` is **Figtree** 400 to 700. The body is `500 14px/1.3`.
- `--font-mono` is **Geist Mono**, used for ids, timestamps and numbers (tabular).

Shape and spacing:

- Radii: `--r: 8px`, `--r-card: 16px`, `--r-pill: 999px`. Big surfaces use 24 to 32px, often asymmetric: `border-radius: 32px 32px 16px 16px` on `.tally` and `.talk`, `48px 48px 0 0` on the ink band, `0 0 80px 80px` on the green band.
- One whisper shadow: `rgba(0,0,0,.1) 1px 1px 3px 0`. Structure comes from hairlines, not boxes.
- Gutter 20px, max width 1320px.

Motion: the comment at `theme.css:457-459` says "Wispr Flow timing tokens":

- `rise` 0.32s ease-out with a 60ms stagger via `--i`; `pop` 0.28s spring `cubic-bezier(.34,1.56,.64,1)` for chips and toasts.
- A 40s marquee and a sliding coral nav indicator.
- Serif tally numbers count up over 600ms (`motion.ts` `useCountUp`).
- A five-bar **waveform** while listening, and a **rotating conic-gradient ring** on the mic while thinking.
- A `beacon` ripple dot on empty states.
- A cursor glow and ring on fine pointers only.
- Everything is off under reduced motion.

Iconography is almost entirely **typographic glyphs**: 🎙 ● ◉ ▶ ☾ ✓ ✗ ↩︎ ◎ ✦ ›. There is no icon library and no illustration; product screenshots are the imagery. The theme is light only (`<meta name="color-scheme" content="light">`).

### 2.5 Screen-by-screen

**1. Landing** (`#home`, `Landing.tsx`)

- A deep-green announcement strip on top, and a floating paper topbar card containing:
  - a coral-dot brand, "**Beacon** Night Shift";
  - a pill nav on beige with a sliding coral underline;
  - a right-hand status area with "● live", version and a mono clock.
- Hero: centred eyebrow, a serif h1 at `clamp(44px,7.4vw,96px)`, a lede, then **one lavender primary** ("Open the Night Board"), an outline secondary ("▶ Run the night" / "▶ Watch the film"), and a ghost tertiary ("Code on GitHub").
- A tilted product screenshot (`perspective(1400px) rotateX(4deg) rotate(-1deg)`, which straightens on hover). An ink pill sits over it with an animated waveform and the words "approve fix one". The pitch lives in that pill.
- Further sections:
  - An ink "Built on" marquee band.
  - A deep-green stats band: "*Nobody* woken the second time." with live tally numbers and a "Human on call 12 min vs Beacon 30 s" comparison.
  - A sticky-list scrollytelling features section (Talk to it / Approve with your words / Sleep through the repeat), each with a proof line naming a source file and test.
  - Pillars on beige, and quote cards in italic serif.
  - A two-pane FAQ: a green question list on the left and a chat-bubble answer on the right.
  - A final CTA.
- Screenshot: `docs/assets/landing.png`.

**2. Night Board** (`#board`, `NightBoard.tsx`, `docs/assets/night-board.png`)

- A five-tile serif tally: incidents resolved, median time to recovery, humans woken, model cost per incident in ₹, sleep protected · night IST.
- Passcode plus "Unlock voice". A judge card.
- Incident cards: an alarm name in serif, a severity pill and a status pill (dot plus word). The selected card gets a coral left bar.
- An expandable vertical timeline with mono timestamps and coloured dots.
- **Empty state:** "● All quiet. Waiting for the next page. Nothing is broken right now." with **▶ Replay an archived run**.

**3. Talk panel** (`Talk.tsx`, `TalkDuplex.tsx`)

- A cream card with a **deep-green mic panel**: a 60px cream circular mic, a state label (Ready / Listening / Thinking… / "Beacon is speaking — talk to interrupt" / Error), and a mono partial transcript line ("heard: "approve fix two" [██ 96%]").
- A "noisy room" checkbox and an Interrupt button.
- A **latency strip**: "0.2 s to first audio · 412 ms propose_fix round trip · 3.1 s last turn".
- **Bubbles.** These are not chat bubbles. Each turn is a two-column row (who and time on the left, text on the right) separated by hairlines. Beacon's sentences contain `[E1]` evidence chips in pink mono that scroll to the evidence card, with "tool" pills underneath (`propose_fix fix 1: sg.restore_ingress (dry run PASSED)`).
- Interrupted replies get an amber "interrupted" pill. Console-generated notes are dashed and italic: "Fix 1 withdrawn — you spoke over the read-back, so nothing was applied." (`docs/assets/bargein-slide.png`).
- A typed composer ("type instead of speaking…").
- **Phrase chips:** "ask" phrases are solid outline pills. **Consent phrases are dashed deep-green mono pills**, with the tooltip "A consent phrase: it only counts if you say it, and it is kept on the record".

**4. Fix card** (`Talk.tsx:69-139`)

The card has a left border whose colour encodes state. It moves through four states:

- **Proposal:** "Fix 1: `sg.restore_ingress`" with a [dry run PASSED] pill, a "why" line, a key/value list (blast radius, dry run, params), and "awaiting your word: say [approve fix 1]".
- **Executing:** an amber pulsing pill, "dry run → require approval → execute → wait 30 s → verify (up to 6×)", and a sparkline.
- **Resolved:** "✓ Verified recovery [3/3 checks]" or "☾ Resolved under Sleep Contract", a sparkline of errors falling to 0, and "↩︎ Undo fix 1 — the fault will return; Beacon asks you to confirm by phrase".
- **Escalated:** "✗ Escalated to a human".

**5. Contracts** shows cards with an italic serif quote of the granting sentence, a pink left border, and a use meter made of little pill segments (`.meter span`).

**6. Safety** (`docs/assets/safety.png`): "Two roles, *one direction.*" with a kill-switch row, an allowlist table, and a **Controls (deep green) / Proof (beige)** two-pane explorer. Each control shows the file that enforces it and the test that proves it.

**7. Audit** (`assemblyai` branch, `Reports.tsx:156-345`, `docs/assets/audit-listen.png`)

- "Every consent, *in your words.*"
- Filter chips and Export CSV / JSON.
- A table: When | Kind | Alarm · action | **The words** (italic serif quote, plus "AssemblyAI live · 100% confidence") | Channel | Outcome.
- Per row: **▶ Listen** (inline `<audio>`), **✦ Summarise the session**, and **◎ How clearly was it heard?**. The last one returns a "Consent certificate · checked against the recording" block: ✓ "approve fix 1" heard at **95%** (weakest word "fix") · one voice on your channel.

**8. Postmortem and morning report** are rendered as a "letter": a paper card with a serif subject line and a body with pink-bordered items.

**States covered:**

- `.empty` with a pulsing beacon dot; chart skeletons with a shimmer; chart-empty text.
- Toasts ("Link copied", "Night complete · 2 incidents · 1 human woken").
- A 404 page and an ErrorBoundary.
- A mic-denied fallback: "No microphone, so nothing is being listened to — type below instead. The consent rules are identical…" (`TalkDuplex.tsx:259`).
- Polling backs off on errors and pauses in hidden tabs.

**Mobile approach:**

- Breakpoints at 760, 720, 560 and 420 px, plus container queries on cards (`@container (max-width: 640px)`).
- The hamburger morphs into an X, and the topbar card expands into stacked rows.
- Tally tiles reflow to 2 columns. One-thumb incident mode as described in 2.2.
- `STATUS.md` claims screenshots were checked at 1440 / 1024 / 400 px with no horizontal scroll.

### 2.6 Voice / AI interaction patterns

These are the most relevant to Kaam ka Parcha.

1. **Exact-phrase consent, never "yes".** "Yes, do it" is refused; the console teaches the exact phrase through chips and through the fix card ("awaiting your word: say approve fix 1"). Hinglish affirmatives (*haan, kar do, theek hai*) are accepted only for the **read-back** step, while English is kept for the consent phrase itself (`docs/PLAN-v2.md:47`, `docs/PLAN.md:429`).
2. **Confidence-gated approval.** Below 85%, the user is asked to repeat. The UI shows a confidence mini-bar next to "heard:" (`.conf.ok` green / `.conf.low` coral, `theme.css:196-199`). The film's best moment was unscripted: approvals heard at 75% and then 74% were both refused, so the engineer typed the phrase (`video/script-assemblyai.md` row 24).
3. **Barge-in has meaning.** Interrupting the read-back withdraws the proposal and shows a visible "interrupted" pill plus a console note.
4. **Speech-mark sync.** Polly sentence speech marks highlight each sentence in lavender as it is spoken (`web/src/voice/player.ts`, `.sentence.hot`).
5. **Honest channel labelling.** Every user line is tagged by channel (`you · assemblyai · 00:15:25`, or `typed`). The certificate says "**Typed** … not spoken, so there is no audio to score" rather than pretending (`src/beacon/certificate.py` `to_markdown`).
6. **Telephony rules** (`docs/phone.md`): "**A keypress is never consent**" (DTMF can only ack or repeat). "**The caller's channel is the only consent channel**": dual-channel recording proves the phrase came from the human and not from the agent's own read-back. A "noisy room" toggle raises the VAD threshold and the end-of-turn pause.
7. **Hinglish and Devanagari normalisation.** On narrowband lines, an English phrase spoken with an Indian accent often comes back in Devanagari (`अप्रूव फिक्स टू`). `src/beacon/consent_phrase.py` maps only the consent vocabulary and **deliberately does not map Hindi cardinals**, because `दो` means both "two" and "give" ("isko fix kar do").
8. **Tamper-evident record.** The certificate carries a `sha256:` digest of the canonical JSON, explicitly "**Not a signature and not claimed to be one**… a fake signature is worse than none" (`certificate.py:209-217`).
9. **Telegram page format:** a one-line cause plus three buttons, **Talk · Fix 1 · Ack** (`src/beacon/telegram.py:170-174`). This is a close analogue to a WhatsApp job-card message.

### 2.7 Snippets worth borrowing

**State pill** (dot plus word; the dot carries the colour, the word stays ink; `theme.css`):

```css
.pill{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;color:var(--dim);white-space:nowrap}
.pill::before{content:"";width:8px;height:8px;border-radius:50%;background:currentColor;flex:none}
.pill.green{color:var(--deep)} .pill.green::before{background:var(--deep)}
.pill.amber{color:var(--ink)}  .pill.amber::before{background:var(--coral)}
.pill.pulse::before{animation:pulse 1.4s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:.3}50%{opacity:1}}
```

**Listening waveform and thinking ring** (`theme.css:477-488`):

```css
.wave{display:flex;align-items:center;gap:3px;height:22px}
.wave i{display:block;width:3px;height:22px;border-radius:2px;background:var(--ink);transform-origin:center;animation:wave 1.2s ease-in-out infinite}
.wave i:nth-child(2){animation-delay:.15s}.wave i:nth-child(3){animation-delay:.3s}.wave i:nth-child(4){animation-delay:.45s}.wave i:nth-child(5){animation-delay:.6s}
@keyframes wave{0%,100%{transform:scaleY(.3)}50%{transform:scaleY(1)}}
@property --angle{syntax:"<angle>";initial-value:0deg;inherits:false}
@keyframes flowBorder{to{--angle:360deg}}
.mic.thinking::before{content:"";position:absolute;inset:-5px;border-radius:50%;padding:3px;
  background:conic-gradient(from var(--angle),var(--pink),var(--lavender),var(--coral),var(--pink));
  -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;
  mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);mask-composite:exclude;animation:flowBorder 1.6s linear infinite}
.mic.live{border-color:var(--coral);box-shadow:0 0 0 6px rgba(255,108,76,.35)}
```

**Consent phrase chip versus ask chip** (`theme.css:189-195`):

```css
.phrase{font-size:12.5px;padding:6px 12px;border-radius:999px;border:1px solid var(--line);background:var(--paper);color:var(--dim);transition:all 150ms}
.phrase.consent{border-style:dashed;border-color:var(--deep);color:var(--deep);font-family:var(--font-mono);font-size:11.5px}
.phrase.consent:hover:not(:disabled){background:var(--deep);color:var(--cream)}
```

**Confidence bar** (`theme.css:196-199`, markup at `TalkDuplex.tsx:358-361`): `<span class="conf ok"><i style="width:96%"></i>96%</span>`.

**Empty-state beacon ripple** (`theme.css:562-565`):

```css
.empty h3::before{content:"";display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--coral);margin-right:12px;animation:beacon 1.8s ease-out infinite}
@keyframes beacon{0%{box-shadow:0 0 0 0 rgba(255,108,76,.45)}70%{box-shadow:0 0 0 12px rgba(255,108,76,0)}100%{box-shadow:0 0 0 0 rgba(255,108,76,0)}}
```

**Count-up numbers** (`motion.ts` `useCountUp`): an rAF ease-out cubic over 600ms, about 20 lines. It ports trivially to vanilla JS.

### 2.8 What likely impressed judges, and what is weak

**Impressed:**

1. A UI story built around one emotion ("go back to sleep") with the user's own vocabulary on every screen.
2. A safety argument made visible: exact phrase, dry run, three checks and quotes on the record. Every claim links to a file and a test.
3. A judge-friendly flow: 90-second instructions, "Run the night" autoplay, replay when empty, and no passcode needed to look around.
4. A tasteful, unexpected light editorial look for a "night" product.
5. Real measured latency shown in the UI.
6. A reproducible film pipeline with no editor (`video/README.md`).
7. Hinglish handled carefully. It is the judging region's language.

**Weak:**

- Text-dense and judge-oriented. Proof lines, file paths and mono parameters sit in the product UI, so it reads as developer-for-developer.
- Glyph icons (🎙 ◉ ☾) render inconsistently across platforms.
- Some state colours collide: `--amber` is aliased to coral, and `--violet` to pink.
- 12px dim labels are small for half-asleep eyes.
- The light theme is an odd fit for 3 AM use with no dark mode, and the AssemblyAI film itself went back to near-black.
- Three overlapping submissions in one repo cause confusion; the README has to redirect lablab visitors.
- Several "round N" CSS appendices show visible design churn.

---

## 3. Lessons mapped to Kaam ka Parcha

Kaam ka Parcha is a mechanic's Hinglish voice estimate, read back to the owner over a phone line and confirmed with "haan theek hai" into a SEALED job card, PDF and WhatsApp text.

### 3.1 Visual direction ("look like the audience")

- **Use CampusEvac's warm-paper, ink and hard-shadow system as the base.** It already reads as a printed **bill-book / parchi**: graph-paper ground, ink rules, sticker tags, stamp-like slabs. Map it onto a garage job slip:
  - paper `#f8f2ea` / `#fffaf3`, ink `#1d1626`;
  - sun or marigold `#ffc44d` for the primary action;
  - coral `#ff6a3d` for "needs the customer";
  - mint `#2fd18f` (or Beacon's deep green `#034f46` for better contrast on paper) for SEALED/verified;
  - danger `#ef3b4b`.
- Add a carbon-copy feel: pale pink or yellow duplicate-slip tints, perforation dashes, and a rotated **rubber-stamp "SEALED / मुहर"** using `.brutal-sticker` with a `rotate(-6deg)` and a coral or deep-green border. These additions are my suggestion; neither repo has them.
- **Use Beacon's rule: colour only on state.** Give each job-card state one colour and one word. For example: *bol rahe hain / listening* (warn `#ffa946`), *customer ko sunaya / read back* (pink `#ffbcf2`), *correction* (coral), *sealed* (deep green), *needs you* (coral). Use the dot-plus-word `.pill`.
- **Fonts: neither repo's fonts render Devanagari.** Geist (latin subset), Figtree and EB Garamond are Latin only. If Kaam ka Parcha shows Hindi or Devanagari (it should for Hinglish), pair a Devanagari-capable family. Google Fonts candidates (my suggestion, not from the repos):
  - **Mukta** or **Hind** for UI;
  - **Baloo 2** or **Yatra One** for signboard-style display;
  - **Tiro Devanagari Hindi** as the serif "statement" font, playing EB Garamond's role;
  - **Noto Sans Devanagari** as a fallback.

  Keep a mono with `font-variant-numeric: tabular-nums` for rupee columns. **Verify the ₹ glyph renders** in whichever families you pick.
- **Do not copy the 9 to 11px uppercase labels** from either repo. A mechanic in a noisy, bright workshop needs at least 16px body text and 44 to 88px touch targets. Beacon's phone mode uses an 88px mic.

### 3.2 Flow and interaction

1. **Next-action deck** (CampusEvac `CommandDeck`). Show a three-to-four-step track: *Bolo → Card bana → Customer ko sunao → Haan / Correct → Sealed*. Put the single ready action in one big button with a one-line "why". Do not draw locked actions.
2. **Caption first, voice second** (CampusEvac `NarrationCaption`). Render the read-back text immediately and let TTS follow. Highlight the item currently being spoken, like Beacon's speech-mark `.sentence.hot`. This works directly for the TTS read-back of each line item.
3. **The consent phrase is a visibly different chip** (Beacon's dashed deep-green mono `.phrase.consent`). Show "haan theek hai" as the consent chip and "isko badlo / X ka rate galat hai" as ask chips. Keep Beacon's principle that loose agreement alone is not consent if the stakes call for it, and make the rule visible on screen.
4. **Show "heard: "…" [██ 92%]"** with a confidence bar, and ask to repeat below a threshold. This directly targets the *noisy telephony* and *Hinglish* awards. Add Beacon's **"noisy room" toggle** (higher VAD threshold, longer pause) as a visible "Garage mein shor hai" switch.
5. **Barge-in withdraws.** If the customer speaks over the read-back, mark the bubble "interrupted" and require the read-back again before sealing. That is turn-taking with a safety meaning, which judges loved.
6. **Typed vs heard honesty.** Tag every line with its channel (*phone · mechanic mic · typed*), and never imply a typed confirmation was spoken.
7. **Tamper-evident seal, worded honestly.** Use Beacon's `sha256:` digest of canonical JSON with "detects edits, not a signature". Print it on the PDF footer and the WhatsApp text with the customer's quoted words, channel, confidence and timestamp, like Beacon's consent certificate.
8. **Audit row with ▶ Listen.** Play back the customer's "haan theek hai" next to the sealed card. Use a dual-channel idea: the customer's line on its own channel, so the system's own read-back is never counted as the customer's consent.
9. **Empty, loading, error and success states.** Copy CampusEvac's mailer stages (idle → sending → verify → sent, plus error) for WhatsApp sending. Copy Beacon's "All quiet" empty state with a pulsing dot and a **"▶ Demo chalao / Replay a sample job"** button, so judges never see an empty screen.
10. **Built for judges and the 60-second film.** Add a "How to judge this in 60 seconds" disclosure, a one-click scripted run (Beacon's `?night=1`), and a hero pill showing the key phrase with an animated waveform (Beacon's `.ribbon-tag` "approve fix one" becomes **"haan theek hai"**). Both films open with the user's real moment: a phone lighting up at 03:12. Kaam ka Parcha could open on a revving engine and a mechanic talking.
11. **Report that looks like the app.** CampusEvac's inline-styled table email transfers directly to the PDF and HTML job card: stat cells, a line-items table with right-aligned mono ₹, "How the total was reached", and a footer saying "every figure was said aloud and confirmed".
12. **Mobile.** Use CampusEvac's `(pointer: coarse)` adaptations and safe-area padding, and Beacon's 760px "one-thumb mode": mic first, phrase chips, sticky composer, and the feed below.

### 3.3 No-build feasibility

Everything above is plain CSS plus small vanilla JS:

- the custom properties;
- the `.brutal-*` classes (CampusEvac uses Tailwind, but the classes in `globals.css` are plain CSS);
- the `.pill`, `.wave`, `.mic.thinking`, `.phrase`, `.conf` and `.empty` classes;
- an IntersectionObserver reveal with fail-open;
- rAF count-up numbers.

None of it needs React. The only extra assets would be Google Fonts `<link>` tags and one static CSS file.
