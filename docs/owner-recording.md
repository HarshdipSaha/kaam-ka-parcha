# Recording your own voice (80 owner takes)

These takes are the first **real workshop speech** in the benchmark. They stay private under ignored `var/`.

1. `.\.venv\Scripts\python.exe scripts/make_owner_recorder.py` → writes `var/owner_recorder.html`.
2. Open it in Chrome (double-click works; no server needed). Click **Choose folder** and pick
   `var/benchmark_audio/owner/takes` (create it first). Without a folder it downloads each file instead.
3. For each card, speak the estimate in your own words — dedh, dhai, saade, sava, barah sau — near a running
   scooter or fan. Don't read the digits aloud like a script. **Record → Stop → Play → Save & next.**
4. Register the takes: `.\.venv\Scripts\python.exe scripts/register_owner_takes.py` (writes
   `var/benchmark_audio/owner/manifest.jsonl`, 8 kHz mono).
5. Score them with the plan's Task 14 Step 2/5 commands (`docs/superpowers/plans/2026-10-05-money-path-safety.md`):
   run the amount runner on the owner manifest, then `parcha.lab.money_eval` with `--results var/lab/v2_owner.jsonl`.

Use `--max-credits` and the dry-run forecast first. Takes are one speaker: report them as such, and never
commit the audio.
