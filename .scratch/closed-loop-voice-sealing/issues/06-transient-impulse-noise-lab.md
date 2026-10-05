# 06: Transient Impulse Noise & Idle Hallucination Laboratory Suite

**What to build:** Expand the `parcha.lab` evaluation harness to benchmark non-stationary transient impulse noises (pneumatic impact wrenches, dropped metal spanners, compressor air exhausts) alongside stationary engine drones. Quantify non-speech hallucination rates during engine idle segments to establish rigorous acoustic operational boundaries.

**Blocked by:** 01: Curated Automotive Domain Vocabulary Biasing Registry.

**Status:** ready-for-agent

- [ ] Implement transient impulse noise generator module simulating intermittent workshop acoustic spikes.
- [ ] Update evaluation runner to execute benchmarks across codecs (G.711, AMR-NB), SNRs, and impulse noise profiles.
- [ ] Add hallucination scoring metric measuring phantom word generation on zero-speech idle engine segments.
- [ ] Add offline unit tests validating impulse mixing, metric calculations, and safe relative delta reporting.
