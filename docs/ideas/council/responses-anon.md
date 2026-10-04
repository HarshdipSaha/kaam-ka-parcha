# Council round 1: anonymised responses (A–G)

## Response A

**Build #2 Kaam ka Parcha, with a "phone-in" mode so the same clip also runs through the 8 kHz chain. #6 is a 150-line script inside it, not a product.** #1 stacks three unmitigated dependencies (WS proxy + 1024-byte paced frames, far-field speakerphone capture, an elderly relative you don't have) and its first filmable moment is week 3 at best. #2's first filmable moment is Monday.

**Monday morning (W1, Oct 6–12): kill experiments, all REST, no UI.**
1. Record 10 scripted Hinglish garage lines with ₹ amounts, part names, a date, on your phone next to a running scooter. `POST /stt/v3`, `hi-IN`, `format=transcribe`. Kill if amount exact-match <70% at street noise. (API risk: ITN is hi/en-only, which is fine here; `multi_lang_codes` is undocumented, so probe its format once and fall back to `hi-IN`.)
2. `bias_list` with 30 part/brand names at `bias_score` 1.0 vs off. Letters-only constraint: "brake pad" becomes two words.
3. Timbre `hi-IN` explicit, "₹650, Somvaar shaam tak" → check native numbers, `container: mulaw` for the phone-in variant.
4. Confirm your ffmpeg has `libopencore_amrnb`; build §3.1 chain (G.711, AMR 4.75) × SNR {clean, 10, 5, 0} on the same 10 clips; jiwer CER + entity exact-match. That is Line Noise Lab v0.
5. **Credit burn is undocumented.** Make one 6-s STT call and one TTS call, read the dashboard decrement, then size everything. Budget the grid at ≤40% of 5,000 credits. If 1 credit ≈ 1 audio-second, 1,200 clips × 6 s = 7,200 s already busts it; cut to 100 utts × 3 codecs × 3 SNRs.

**W2 (Oct 13–19):** FastAPI + one HTML page, schema-validated extractor on an external LLM (Evon later, flag-switched), PDF bill, WhatsApp-text output. Visit a garage; record 20 scripted lines with a mechanic (scripted = synthetic data, rules-safe). **W3 (Oct 20–26):** SynthCall-IN 100–200 utts via Timbre (two voices, 8 kHz), run T1/T2, make the proof card, film, **post Oct 25**. **W4:** iterate on comments, one RunPod afternoon for Evon extraction (₹3k cap, stop the pod). **W5:** 60-s cut, README, buffer.

**Oct 25 post realistically shows:** 30–40 s, engine running, mechanic speaks, job card fills line by line, Timbre reads the total, customer nods, one number ("₹-amount exact-match 9x% at 5 dB on our pipeline, N=…"). Not partial captions, not Evon.

**(b)** #1 floor = no demo by Nov 10; #2 floor = working demo with a flat hook. **(c)** Speakerphone relay is a hack for Noise Canceller; the honest telephony story is the phone-in mode where audio has actually passed through G.711/AMR. **(d)** #2 escapes Bolo only if the bill, the read-back confirm loop, and the noisy-₹ numbers are the headline; a form on screen is Bolo. **(e)** #6 public as a repo folder plus one curve image; the manifest is the interview. **(f)** Toy = a page that transcribes a clip; treading = any BFSI voice agent. **(g)** Nothing missing; S3 Echo Test is T6 inside the harness, fold it in.

## Response B

**Pick #1 Sun-Saathi, with #6 as its public spine and the garage scene demoted to an "angle post".** The other seats will tell you #2 is safer. Safe is not what this contest pays for: the shortlist is decided by engagement, and the field's current bar is 5 and 26 reactions.

**(a/b) Ceiling.** Every Indian AI clip in R5 that cleared five figures had an elder or a child reacting in Hindi: nani-and-ChatGPT 78K likes/2M views and lifted by HT, Mint, Times Now; dadi 228K likes. Nothing else on the list can touch that genre. A grandmother reading Bengali captions of her grandchild's call, then tapping a reply Timbre speaks, is the one clip Ganesh Gopalan (27K followers, documented resharer of community content, 726-reaction posts) would reshare and press would lift. #2's ceiling is a few hundred LinkedIn reactions from the auto/B2B crowd; a mechanic nodding at a bill is a good clip, not a shared one. Floor for #1 is still a working caption app with a 1-s delay, which already beats every entrant. Use the garage reel as one of the Oct 22–Nov 10 angle posts (R5 §6.3: 3 posts/week, each pointing back to the nominated post); the ceiling is the cumulative campaign, not one upload.

**The bigger prize nobody is pricing in.** Gnani is hiring a whole B2C Products department: mobile app engineer, growth marketing, reels editor, UI/UX (notes/06 §1.4). Sun-Saathi is the only idea that is itself a consumer app with a growth story. It makes Harshdip a candidate for *two* teams, speech and B2C, and gives the interviewer a product they might actually want. Interview line: RPwD Act 2016 obliges Gnani's own bank and telco customers to be accessible; relay is the consumer mirror of Assist365, not a toy. Google demoed Live Relay in 2019 and never shipped; India has no relay service. That is a 63-million-person hole.

**(c) Speakerphone is a feature, not a hack.** Far-field speakerphone into an 8 kHz telephony preset is a *harsher* Noise Canceller case than a clean SIP leg. Name it "second-device relay" like hearing-aid companion apps, measure it in the harness, and add a VoIP leg only if week 3 allows.

**(d)** #2 escapes form-filling only on the noisy-vertical axis; it does not escape the B2B ceiling.

**(e) Publish #6.** Gnani's own paper says the AMR-NB 5.9 kbps + rural-noise WER benchmark does not exist; comparative-number threads are what Indian AI X rewards (Sarvam redemption thread, 1,630 likes). Ship it as its own repo plus a LinkedIn carousel (1.45× reach, 55-s dwell) that publishes only our system's deltas. It doubles as the speech-data-engineer interview artefact.

**(f) Toy/treading.** Sun-Saathi and the garage card tread on nothing Gnani sells; Dhokha Desk and Sahi Bikri sit next to Aura365/Collect365 and read as "we already do this".

**(g) Missed:** dual-submit the same open-source build to Code for a Billion (₹18 lakh, "frontline workers" track, closes Nov 15, judged on real deployment data; three elderly testers *is* deployment data), and post the 20-s cut as an Instagram Reel and YouTube Short, where the elder clips actually went viral, screenshotting the numbers back into the nominated post.

## Response C

**The shortlist's top two both rest on a mis-scored "Award" column, and the real bottleneck isn't the idea at all.**

**(a)/(d) #2 is a form-filler wearing overalls.** R3 §2 lists voice form-filling as crowded *because of* Bolo, whose demo forms include a "motor claim" (R3 line 55). Kaam ka Parcha's artefact is a filled form plus a bill; Voice Khata's artefact is a filled ledger line. A judge who has seen both will file #2 beside them. Worse, its Award score of 5 is wrong: Real Deal names farmers, kirana, health workers; a mechanic is none of these, and Noise Canceller says *telephonic* audio, not compressor noise. Honest score: 3, total ~33, tied with #1. If #2 is built, the "mechanic phones the job in" 8 kHz variant must be the *primary* demo, not the hedge in risk (b), or it has no award at all.

**(c) Second-device relay is a hack, and a detectable one.** The audio path is phone speaker → air → tablet mic → *our* resample to 8 kHz. No AMR-NB, no G.711 round trip, no packet loss: none of what Gnani's own channel description specifies (R4 line 60). Plus the Timbre reply is a tablet speaker shouting into a phone mic, so the caller hears room echo. A Gnani engineer who has spent years on real telephony will see a 44.1 kHz far-field recording dressed up. Add the latency fact: WS emits finals only, end-of-turn ≈ `x-min-silence-ms` 500 + ~300–500 ms (02-speech-apis lines 24, 116, 121). A caller who talks in long runs produces captions 1–2 s after each pause, which on camera looks like the thing is broken. And Live Relay died at Google for a reason that applies here too: no OS gives an app the call audio. This product cannot exist as described; the demo is the product.

**(b) Floors.** #1's floor is zero: G1 (elderly relative on camera) is open, and without her R5 says the reel is nothing. #2's floor is a mediocre form-filler with a mechanic who grunts. #1's ceiling borrows from the Nani-ChatGPT reel, which was humour from a creator's account, not engineering from a ~700-follower student (R5 line 125: normal post 5–15 reactions).

**(e) Make #6 public, as a carousel.** The avoided question is distribution. R5 line 66: the only plausible resharers are Ganesh and the engineers whose model you name, earned "by naming the model and a concrete number". Carousels get 1.45× reach and the highest dwell (R5 line 96). A curve set is what an engineer reshares; a form is not. But fix the EULA trap first: every proof card on the list cites "WER at 5 dB", an absolute Prisma number, which R4 line 14 flags as unverified territory. Publish only deltas (denoise on/off, preset A/B, bias_list on/off).

**(f) Treading.** Live call transcription *is* Assist365; #4 is Aura365 plus their compliance tutorial. Both read as a student rebuilding the house product with worse audio.

**(g) Missed:** R3's S9 "Dhai-Lakh Guard" (numeric-safety middleware around ITN variants) is the one seed that treads on nobody, targets the two publicised numeric agent bugs, and produces exactly the entity-accuracy metrics Gnani asks for. Merge it into whichever product wins as the visible engineering core.

## Response D

**Verdict: build #1 Sun-Saathi, with a reacting grandparent on camera, or don't build it at all.**

**(a) Which idea.** Every Indian AI clip in R5 §4 that cleared five figures had an elder being understood in their own language (nani: 2M views, 78K likes, 1,854 comments; dadi: 228K likes; Sophie). The rubric agrees: #1 scores 19–20/21, #2 14–15, and the gap is on the two criteria that actually move reach: "Relatability" (grandmother hearing the phone = universal/emotional, 3; garage bill = common work task, 2) and "Human in frame" (mechanic dictating = user acting, 1; grandmother laughing = reacting, 3). Modifications: Bengali or another non-Hindi script (regional communities reshare their own); the grandparent is the hero and an informed participant, shown benefiting on camera (the nani clip's backlash was "you're making fun of amma ji"); the mishear → "phir se boliye" beat stays, because misunderstanding-then-recovery is the comment engine (§7.1 #6). Hard gate: if no elder relative is confirmed on camera by Oct 12, switch to #2 and add a customer laughing when Timbre reads back "chhe sau pachaas" (lifts #2 to ~17).

**(b) Ceiling vs floor.** With the §6 playbook (30-person first-hour list, Discord, NSUT societies, professor comment) both floor at roughly 60–120 LinkedIn reactions / 15–30 comments. #2 ceiling ≈ 200–300 reactions, 40–60 comments: a "that's clever" post, shared rationally. #1 ceiling ≈ 400–1,000+ and 100+ comments, because it is the only idea on the list where a Ganesh reshare or a press lift ("6 crore Indians can't hear the phone") is plausible; R5 says that reshare is the only route past 1K. #1's floor is lower (~50) if caption latency visibly lags on screen, so measure Prisma's final-only latency in week 1 and shoot around it. X: #1 100–300 likes, #2 50–150.

**(c) The single change.** End on her, not the proof card. Move the card to 0:44–0:50 and give 0:50–0:58 to the grandmother saying one line to camera in Bengali ("Now I pick up the phone myself"). Reaction is the shareable unit; a card is not.

**(d) Gnani reshare.** Rubric criterion 7 at 3/3: split-screen Prisma v2.5 vs Whisper/Google on the same 8 kHz market clip with WER on screen, model names burned in, plus one line Ganesh can lift verbatim into his sovereign-AI framing ("Indian voice AI for 6 crore Indians the phone left behind"; RPwD Act hook for his bank/telco customers). Pre-earn it: two weeks of substantive comments on Ganesh/Thoshith posts, Discord helpfulness, tag only gnani.ai + one engineer you've talked to.

**(e) Baked-in question.** Only #1 has one: "Who in your family stopped answering the phone?" generates stories, and "is speakerphone relay a hack / is a synthetic voice for dida okay?" generates argument. #2's "garage overcharged me" is complaint, not warmth. #3–#6: none.

**(f) Missed.** Not an idea, a shape: a weekly "classmate's grandparent, new language" series (Tamil/Marathi/Kannada via NSUT friends) each pointing back to the nominated post, cross-posted as Reels/Shorts where the nani clips actually travelled; and #6's WER-vs-noise curves as the X content, since Indian AI X runs on comparative numbers (Sarvam-M arc, 1,630 likes).

**(g) Platform.** 80%+ of countable engagement will come from LinkedIn (Gnani 124K, Ganesh 27K, interest graph giving 0–500-follower accounts 367% reach at p90). X is the compliance post, but a 20–30 s cut can out-reach Gnani's own 14 likes. #1 is LinkedIn- and Reel-native; #2 is platform-neutral but lower everywhere. Idea choice doesn't change where reach comes from; it changes whether the reshare happens.

## Response E

**What stops my scroll: only #1.** A grandmother reading big Bengali letters while her grandchild shouts from a market is a picture. I understand it in zero seconds, I feel something, and I'd hit reshare for her, not for the tech. Nothing else on this list produces that reflex. #2 is a mechanic talking to a phone and a bill appearing: fine, useful, I nod and keep scrolling. #3 I would have to be told what an ASHA is. #4 needs two scenes and the words "pre-issuance verification" to explain itself; I'm gone. #5 is a bank complaint form. #6 is a graph. Nobody reshares a graph.

**The names are a problem.** "Sun-Saathi", "Kaam ka Parcha", "Sahi Bikri", "Dhokha Desk": to a stranger, these are four unexplained Hindi phrases. "Live captions for your parents' phone calls" is the whole product in one line; lead with that, keep the brand name small. Also drop "second-device relay", "8 kHz µ-law", "ITN", "diarization", "WER" from anything public. These impress no one outside the room and signal "student showing homework."

**What the judge who's seen 300 demos thinks:** "Captions for the hard of hearing" is Google Live Transcribe, which they know. The thing that makes yours new is the second half, tap-to-reply spoken INTO the call, and that half is buried as a clause. The reply is the demo. Grandmother taps, the delivery guy hears a voice, the door opens. Lead with that, not with the captions.

**(c) Is speakerphone honest?** As a stranger: yes, obviously, because that's exactly how my grandmother uses a phone. Nobody normal thinks "that's not real telephony." Only engineers would. Say plainly "works with any phone on speaker, no app on the other side," and it becomes a feature, not a confession. The one-second caption delay is also fine; subtitles on TV lag. Don't apologise for it in the video; put it on a proof card and move on.

**(d) Does #2 escape form-filling?** No. "Speak and a form fills" is the same demo whatever the trade. The bill readback in the customer's language is the only distinctive beat, and it's small.

**(b) Floor vs ceiling:** #2's floor is a working thing that gets 30 reactions. #1's floor, if the elderly relative won't film, is a dummy on a tablet and zero emotional pull: that's the real risk, and it's a casting risk, not a technical one. Secure the grandmother before writing code. Her face is the whole bet.

**(e) #6:** interview-only. In public it reads as a benchmark, which the EULA warns about and which bores everyone.

**(f) Toy signal:** anything whose hero shot is a transcript box. **(g) Missed:** the second-device trick works for anyone whose hearing or language fails on a call: the Tamil-speaking parent whose landlord calls in Hindi. That's a wider story than "hard of hearing" and merges Main Character into the same demo.

## Response F

**Strip the question.** You are not choosing a product. You are choosing two artefacts for two different judges: a 60-second clip that earns comments in its first 90 minutes on LinkedIn (shortlist), and a set of numbers you can defend to a speech engineer (offer). The product is only the thing that makes both honest. So the real question is: *which clip can Harshdip film with a real, reacting person within two weeks, that forces Prisma onto 8 kHz audio, and spits out his own measured deltas?* Score the list on that and it collapses fast.

**(a) Build #2, but change its artefact and import #1's hero.** As written, #2 is "mechanic speaks → fields fill", which is exactly the Bolo shape; the vertical does not rescue it (R3 §2 calls form-filling "Open" only *with a validation loop*). Make the loop the product: the mechanic's estimate becomes a **Timbre phone call to the customer** at 8 kHz ("kul chhe sau pachaas, Somvaar tak, theek hai?"), the customer answers "haan"/"nahi, saade chaar sau", Prisma captures the correction over the line, the parcha is sealed. Now the telephony leg is real by construction, the reacting human on camera is whoever picks up (a parent or grandparent, the same hero R5 §7.1 says carries 2M-view clips), and the on-screen artefact is a confirmed agreement, not a form. #6 is the spine either way.

**(b) Ceiling vs floor.** #1's ceiling comes from its hero, not its tech; the hero is portable. #1's *floor is zero*: its promise is liveness and the documented WS gives finals only (`02-speech-apis.md` line 15; `x-partials` is a single undocumented mention, line 121). If that header is dead and no elderly relative consents, there is no clip. #2's floor is a filmed Delhi garage with a real mechanic, which already clears the field's bar (5 and 26 reactions).

**(c) Speakerphone relay is a UX, not a measurement.** Loudspeaker→room→mic is a *different* degradation from 8 kHz codec audio. Claiming it as Noise Canceller evidence is a hack; stating "numbers come from the simulated 8 kHz chain, the speakerphone is how a user holds it" is honest. #1 needs that disclaimer; the merged #2 doesn't.

**(d)** Only with the change above. Noise alone does not move it out of the crowded row; the confirmed-agreement loop does.

**(e)** Public repo with seed, manifest and own-system deltas (R4 §1.6 EULA guard); never the nominated post. Dashboards are the documented unshareable floor (R5 §7.1), and the harness is the interview's spine, not the feed's.

**(f)** #4 and #5 tread on Aura365/collections/fraud (Gnani's "Large Defense Org" story) and look like a student rebuilding the customer's product. #6 standalone reads as a research artefact. The merged #2 touches an auto vertical Gnani sells into but has no product for.

**(g)** Nothing structurally missing; the miss is treating "product" and "hero" as bundled. Decide the 0:00–0:03 shot first (R5 §7.4) and let it pull the architecture.

## Response G

**Verdict: build #2 Kaam ka Parcha, re-centred on the phone leg, with #6 as its spine. Drop #1 as the product.**

**(a/b) Why not Sun-Saathi.** Two facts in the files kill it for me as an interviewer. Prisma realtime emits finals only (05-models, shortlist §1 risk a), so your "live captions" arrive 0.5–1.5 s after each pause. That is a transcript feed, not captioning, and the first commenter will hold Google Live Transcribe next to it. Second, speakerphone capture is far-field room audio at the phone's mic rate, not an 8 kHz codec path. Prisma's documented edge is Kathbath-noisy, Gramvaani and GSM/VoIP codec handling (05-models §2); far-field reverberant speech is nobody's home turf and certainly not ours. #1's ceiling is a reel; its floor is an interview where I ask "which part of our 14M telephonic hours helps you here?" and you have no answer. **(c)** So no: second-device relay is a hack dressed as telephony. It would not get a Noise Canceller vote from me.

**(d) #2 escapes "form-filling" only if you change the primary path.** Make the demo the mechanic *phoning* the job in over an AMR-NB/G.711 chain (R4 §3), with the walk-up recording as the secondary arm. Auto is a vertical we actually sell into (Tata Motors, Horsepower, 06 §1.2), every utterance is ITN-dense ("saade chaar sau", "Somvaar tak"), and the artefact is a bill a customer confirms, not a form. Bolo returns "clean English records"; you return a confirmed ₹ total via Timbre normalisation and a measured correction rate. That is a different product category to us.

**(e) #6 public, but only our pipeline's deltas.** The EULA clause bites exactly on absolute Prisma WER-vs-SNR curves: that *is* a benchmark of the Gnani Product. Publish the harness code, SynthCall-IN generator, and relative numbers: denoise gain, `bias_list` gain, entity accuracy with vs without the read-back loop, latency decomposition (R4 T1/T2/T4). Label "measured by us on N utterances, settings, date". Bring the absolute curves to the interview; ask on Discord for consent before posting them.

**(f) What I'd see as toys or trespass.** Samasya and boli-zero are toys. Dhokha Desk and Sahi Bikri tread on us: fraud intake sits beside Armour365, PIVC is something we pitch to insurers; a student version invites an unflattering comparison. Sun-Saathi brushes Assist365's real-time transcription.

Interview questions for #2: Why dataset-level WER aggregation and CER for Dravidian? What premature-endpoint rate did you see sweeping `x-min-silence-ms` at 5 dB? Short-utterance drop rate for "haan/nahi" (your confirm loop depends on it)? Hallucinated words on engine-only segments? ITN behaviour on "saade" vs "pachaas", lakh/crore? What did `bias_list` do for part names at score 1.5? #2 with #6 lets you answer every one from your own data; #1 answers none.

**(g) Missed.** The rural-ASR paper names AMR-NB 4.75, AGC and 2G jitter as the problem and offers no end-user path (06 §3.1). Sell #2 explicitly as "the 2G job card": codec-and-loss-sweep in the proof card. Also measure non-speech hallucination; the workshop demo will hit it and nobody on the shortlist budgets for it.
