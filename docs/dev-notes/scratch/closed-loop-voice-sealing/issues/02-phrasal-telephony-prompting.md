# 02: Phrasal Telephony Prompting & VAD Stabilization Engine

**What to build:** Refactor the telephony read-back synthesis prompt generation to acoustically elicit stable 3-word phrasal confirmations (*"Agar aapko yeh manzoor hai, toh boliye: 'Haan, theek hai'. Koi badlaav chahiye toh rate batayein."*). Increases acoustic phonemic duration and signal energy over 8 kHz G.711 / AMR-NB channels, preventing Voice Activity Detector (VAD) endpointing truncation and short-reply dropouts.

**Blocked by:** 01: Curated Automotive Domain Vocabulary Biasing Registry.

**Status:** ready-for-agent

- [ ] Refactor read-back prompt synthesis in `readback.py` to structure calls with phrasal affirmation instructions.
- [ ] Preserve Indic currency numeral pre-normalization and date formatting within new phrasal templates.
- [ ] Update reply classifier to recognize both full phrasal affirmations and legacy affirmations.
- [ ] Add offline unit tests validating prompt phrasing across single-item and multi-item job cards.
