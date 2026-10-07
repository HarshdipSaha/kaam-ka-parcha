# 01: Curated Automotive Domain Vocabulary Biasing Registry

**What to build:** An expanded domain dictionary of 60+ two-wheeler and four-wheeler mechanical parts and colloquial automotive terminology integrated into the verbatim speech recognition pass (`bias_list`). Ensures technical terms (such as caliper pin, shocker, clutch plate, mobil oil, timing belt, and brake shoe) are accurately transcribed over workshop ambient noise without acoustic phonetic drift.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] Define comprehensive dictionary of 60+ automotive mechanical components and colloquial service terms in domain registry.
- [ ] Update STT client configuration to inject domain terms into `bias_list` during `format=verbatim` intake requests.
- [ ] Add offline unit tests validating domain dictionary completeness and payload serialization.
