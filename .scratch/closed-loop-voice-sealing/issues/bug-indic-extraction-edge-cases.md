# [BUG] Hinglish Dictation Extraction Edge Cases: Relative Weekday Resolution, Colloquial Currency Parsing, and Evidence Path Hierarchy

## Description

During end-to-end testing with authentic spoken Hinglish workshop recordings, three distinct extraction edge cases were observed in the intake processing pipeline (`POST /sessions/{id}/intake`):

### 1. Relative Weekday Resolution Ambiguity
- **Observed Behavior**: When dictation specifies relative spoken delivery commitments (e.g., *"Somvaar shaam tak"* / Monday evening), the extracted `promised_delivery` ISO timestamp intermittently resolves to an arbitrary upcoming day (e.g., Friday `2026-10-09`) rather than the immediate next Monday (`2026-10-12`).
- **Failure Mode**: Downstream job card records an inaccurate promised completion date, creating scheduling discrepancies between mechanic commitment and customer expectations.

### 2. Colloquial Numeral Magnitude Formatting
- **Observed Behavior**: In audio samples containing colloquial Indic monetary expressions such as *"saade chaar sau"* (four hundred fifty rupees), the parsed amount in line items can intermittently format as decimal values (e.g., `4.50` instead of `450`), resulting in a 100x magnitude error.
- **Failure Mode**: Total calculation yields malformed paise totals (e.g., ₹4.50 instead of ₹450), corrupting invoice math and WhatsApp summary strings.

### 3. Evidence Field Path Hierarchy Drift
- **Observed Behavior**: In the extracted `review_fields` list, field references occasionally emit un-scoped identifiers (e.g., `field="label"` or `field="amount"`) instead of fully qualified nested JSON paths (e.g., `field="items.part-1.label"`).
- **Failure Mode**: Field-level confidence scores decouple from specific items, causing review validation to fail or misattribute confidence to the parent container.

## Reproduction Steps

1. Send an intake audio request to `/sessions/{id}/intake` with an utterance containing:
   `"Front brake pad badla, part saade chaar sau, labour do sau, Somvaar shaam tak."`
2. Inspect the resulting `JobCard` JSON structure:
   - Check `promised_delivery` date calculation against current calendar.
   - Check `items[0].amount` for magnitude scaling.
   - Check `review_fields[0].field` for dotted path nesting.

## Expected Behavior

1. Relative weekdays like *"Somvaar"* must strictly resolve to the next upcoming calendar Monday based on the session creation timestamp.
2. Colloquial phrases like *"saade chaar sau"* must strictly evaluate to integer 450 (or 45000 paise) with zero decimal ambiguity.
3. Every entry in `review_fields` must strictly match the exact schema path format `items.<item-id>.<property>`.

## Impact

- High: Directly impacts bill accuracy, pickup scheduling, and cryptographic audit integrity on sealed parcha artefacts.
