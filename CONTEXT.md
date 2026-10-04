# CONTEXT: Gnani Great Indian AI Internship Challenge entry

Glossary of the terms this effort uses. Vocabulary only; no implementation detail.

## Contest terms

- **Challenge**: Gnani AI's Great Indian AI Internship Challenge, Oct 1 – Nov 10 2026. Students build on Gnani models; up to 100 paid internships and ten ₹50k awards.
- **Nominated post**: the one LinkedIn post and the one X post the participant names in the submission. Only engagement on nominated posts counts toward shortlisting.
- **Engagement**: reactions, comments and reshares on a nominated post, as verified by Gnani, recorded before the **closing cutoff** (Nov 10 2026; exact time unconfirmed).
- **Shortlist**: the set of submissions Gnani invites to interview. Driven by engagement plus submission review.
- **Offer**: the written internship offer after an individual interview. The only thing that counts.
- **Award**: one of ten ₹50,000 category prizes, judged on category criteria, independent of the shortlist. One award maximum per entrant.
- **Award target**: the single award an idea is designed to compete for, as a secondary objective after the shortlist.
- **Programme credits**: the 5,000 units granted per registration for Gnani's speech APIs. The unit's value per API is unknown until read from the dashboard.
- **Genuine use**: the terms' requirement that Gnani technology does real work in the project, as opposed to being decorative.

## Gnani stack terms

- **Prisma**: Gnani's speech-to-text model family (v2.5 in the API). Exposed as REST (short clips), realtime (WebSocket) and batch (jobs with diarization).
- **Timbre**: Gnani's text-to-speech model (v2.5, beta). Exposed as REST, SSE streaming and WebSocket.
- **Voice clone**: a speaker embedding derived from a short sample and passed to Timbre to speak in that voice.
- **Evon**: Gnani's open-weight 30B-A3B reasoning LLM (v3.3). Self-hosted only; not covered by programme credits.
- **Vachana**: the brand of the speech API host (`api.vachana.ai`) and the Python SDK. Not a separate model.
- **Agent Builder**: Gnani's separate no-code voice-agent product and its platform API. Not confirmed to be covered by programme credits.
- **Load-bearing model**: a Gnani model whose removal would break the project's core value. Contrast **decorative** use.

## Idea-selection terms

- **Destination**: the end state of the wayfinder map: a locked idea with a one-page spec and gates, ready for planning.
- **Idea seed**: a candidate project sketched from a documented real situation, with its load-bearing models, award fit, demo scene and main risk.
- **Shortlist (ideas)**: the ranked 4–6 seeds carried into the council. (Distinct from the contest's shortlist above.)
- **Council**: the `/llm-council` pressure-test of the idea shortlist, up to seven seats, producing a verdict.
- **Gate**: a measurable go/no-go condition in the spec (e.g. a WER figure on a noisy test set) that decides whether to continue or pivot.
- **Telephony simulation**: 8 kHz, codec-degraded, noise-injected audio that stands in for a real phone line in development and demos.
- **Real user**: a non-participant who appears in the demo video using the product in their own language. Synthetic data applies to them too: no real personal identifiers.
