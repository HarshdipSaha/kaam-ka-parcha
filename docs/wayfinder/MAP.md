# Wayfinder map: Gnani Great Indian AI Internship Challenge idea

Label: `wayfinder:map` · Tracker: local markdown (`docs/wayfinder/tickets/*.md`) · Driver: Harshdip Saha · Charted 2026-10-04

## Destination

A **locked project idea with a one-page spec** for the Great Indian AI Internship Challenge (deadline Nov 10 2026):
problem, user, Gnani models used (Prisma v2.5 STT, Timbre v2.5 TTS, Evon v3.3), demo storyline for a ≤60 s video,
award targets, and measurable go/no-go gates. Hand-off is to `/writing-plans` in a fresh session. Building is out of scope here.

## Notes

- Domain: Indian-language voice AI on Gnani's stack. Reference notes: `docs/notes/01`–`06`. Raw docs dump: `docs/raw/llms-full.txt`.
- Standing decisions from the charting grill (2026-10-04, user said "go with your recommendation" on all):
  - **Solo** entry (Solo Ninja eligible; Two-Person Army not).
  - Optimise for the **internship shortlist** (engagement + defensible depth); secondary target **one** award, favourites **Noise Canceller** or **Real Deal**.
  - Top-2 priority, ~15 h/week; **first public post by ~Oct 25**, iterate, nominate the best post later.
  - Compute: Gnani speech APIs + external LLM for development; **Evon self-hosted on rented GPU for the final demo**, budget cap ~₹3–5k.
  - **No real PSTN line**: faithful 8 kHz telephony simulation + WhatsApp voice notes; real call is a stretch goal.
  - Exclude plain BFSI collections bots unless the angle is genuinely new.
  - Idea selection = research fan-out → ranked shortlist → `/llm-council` (up to 7 seats) → user decides in one grilling session.
- **Override of "one ticket per session"**: the user explicitly asked this session to carry through research, shortlist, council and decision.
- Skills to consult: `research`, `llm-council`, `grilling`, `domain-modeling`, `writing-plans` (hand-off).
- Hard constraints from the terms: synthetic data only (no real phone numbers / Aadhaar / PAN / recorded calls); genuine use of Gnani tech; post on LinkedIn **and** X, tag Gnani, both hashtags; no engagement exchanges.

## Decisions so far

- [R1 Enterprise pain](tickets/R1.md): the dominant failure is "the bot can't hear numbers on 8 kHz Hinglish"; regulators (RBI recovery-call recording Jan 2027, IRDAI mis-selling, DPDP spoken consent) manufacture demand. → `docs/research/R1-enterprise-pain.md`
- [R2 Grassroots](tickets/R2.md): ASHA incentive-claim data entry is the strongest money-linked voice pain; grassroots voice survives as phone calls, not apps; SHG-ledger ideas die on the 2-speaker diarization cap. → `R2-grassroots.md`
- [R3 Field](tickets/R3.md): field is tiny (entrant posts 5–26 reactions); dead rows: Hinglish bots, generic form-filling, audio-notes, farmer IVR, kirana khata, dubbing; open: noisy vertical with a validation loop, accessibility, auto/workshop. → `R3-hackathons-and-field.md`
- [R4 Technical](tickets/R4.md): Gramvaani is the only real Indic telephone corpus; telephony simulation recipe (ffmpeg/phonesim/audiomentations); Evon via Modal free credit or RunPod; measurement templates T1–T7; EULA guard = own deltas only. → `R4-technical-angles.md`
- [R5 Virality](tickets/R5.md): Gnani is LinkedIn-native; comments > likes; elder-reacting clips are the genre that travels; 60-s blueprint; shareability rubric; realistic target 60–150 reactions for this account. → `R5-virality.md`
- [R6 Dev/creator](tickets/R6.md): developers want script policy and entity accuracy; Gnani's SDK ecosystem is tiny; creator dubbing is a dead row. → `R6-dev-creator.md`
- [T1 Shortlist](tickets/T1.md): six ideas scored /40; Kaam ka Parcha 35, Sun-Saathi 33 (Award column later re-scored by the council to 34 / 31). → `docs/ideas/shortlist.md`
- [C1 Council](tickets/C1.md): 7 seats + 7 peer reviews; verdict = build Kaam ka Parcha **phone-sealed** (the system calls the customer over a simulated 8 kHz line; Prisma captures the haan/nahi correction; artefact = confirmed parcha), Line Noise Lab as spine, Noise Canceller + Mixed Vibes, deltas-only numbers in public. → `docs/ideas/council-verdict.md`
- [D1 Decision](tickets/D1.md): adopted the council verdict unchanged; one-page spec with 8 dated gates and 3 fallbacks. → `docs/ideas/spec.md`

## Not yet specified

- Nothing in scope remains unspecified at map level. Planning-level choices (customer-leg implementation: simulated line vs WhatsApp voice note; WS vs REST for the reply; Evon hosting route) are listed in `spec.md` for `/writing-plans`.

## Open HITL items carried into the plan (not decisions)

- [G1](tickets/G1.md): the driver's languages and the customer-hero casting (now gate "Oct 12" in the spec).
- [T2](tickets/T2.md): dashboard credit-burn reading (now gate "Oct 6" in the spec).

## Out of scope

- Building the project, the plan itself, and the social posts (hand-off to `/writing-plans`).
- Team recruitment.
- Real telephony integration (Twilio/Exotel numbers, KYC) beyond a stretch-goal note in the spec.
