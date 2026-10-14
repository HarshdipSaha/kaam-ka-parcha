# Jev reply review implementation plan

**Goal:** Add optional Jev advice for unclear customer replies and evaluate it live before pushing to main.

**Architecture:** Inject a bounded, text-only Jev client into Workflow. Only unclear replies invoke it. Advice is audit logged through SessionStore and may clarify retry instructions; it cannot confirm, edit a card or bypass fallback. Keys stay in ignored local configuration. External text is masked using the existing privacy helper.

**Validation:** Offline HTTP fakes cover response validation, masking, outages and preservation of confirmation state. A curated synthetic Hinglish benchmark compares expected labels with existing rules and Jev; private requests, responses and summary remain under var/.

- [x] Add Jev client, configuration and default service injection.
- [x] Add review audit and retry guidance to Workflow without changing consent transitions.
- [x] Add offline regressions and run focused tests.
- [x] Run a larger live benchmark with the local key and configured timeout.
- [x] Document commands and limits, run offline suite and diff checks.
- [x] Review task changes; commit and push main as the final publication step without rewriting history.
