from datetime import date, datetime, timedelta, timezone
import json
import re
from typing import Any
import unicodedata
import httpx
from .schema import Delivery, Evidence, JobCard, LineItem

CARD_SYSTEM_PROMPT = """Extract only explicitly spoken workshop facts from the two transcripts. Return JSON with
items [{id,label,kind,amount_paise}], delivery {date,window,spoken} or null, evidence
[{field,quote,review_score}]. Use item ids part-1, part-2, labour-1, etc. A missing
item label or amount is null, not a guess. Provide separate evidence for every label,
amount and delivery; each quote must be contiguous in either transcript. Use the
provided Asia/Kolkata recording date to resolve a weekday. Do not guess a missing
number/date, vehicle registration, customer name, or total. Score each field 0..1
for human review, not statistical confidence. Return JSON only."""

CORRECTION_SYSTEM_PROMPT = """You are extracting a single corrected field for a workshop job card.
Target field: {field}
Return JSON with {field, value, evidence_quote, review_score}.
Value must be paise integer for an amount, text string for label, or delivery object {date, window, spoken} for delivery.
Do not extract any other field. Score 0..1. Return JSON only."""

KOLKATA_TZ = timezone(timedelta(hours=5, minutes=30))

WEEKDAY_WORDS: dict[str, int] = {
    # Monday (0)
    "somvaar": 0,
    "somwar": 0,
    "somvar": 0,
    "somwaar": 0,
    "som": 0,
    "सोमवार": 0,
    "सोम": 0,
    "monday": 0,
    "mon": 0,
    # Tuesday (1)
    "mangalvaar": 1,
    "mangalwar": 1,
    "mangalvar": 1,
    "mangalwaar": 1,
    "mangal": 1,
    "मंगलवार": 1,
    "मंगल": 1,
    "tuesday": 1,
    "tue": 1,
    # Wednesday (2)
    "budhvaar": 2,
    "budhwar": 2,
    "budhvar": 2,
    "budhwaar": 2,
    "budh": 2,
    "बुधवार": 2,
    "बुध": 2,
    "wednesday": 2,
    "wed": 2,
    # Thursday (3)
    "guruvaar": 3,
    "guruwar": 3,
    "guruvar": 3,
    "guruwaar": 3,
    "guru": 3,
    "veervaar": 3,
    "veerwar": 3,
    "brihaspativaar": 3,
    "brihaspatiwar": 3,
    "गुरुवार": 3,
    "गुरु": 3,
    "वीरवार": 3,
    "बृहस्पतिवार": 3,
    "बृहस्पत": 3,
    "thursday": 3,
    "thu": 3,
    # Friday (4)
    "shukravaar": 4,
    "shukrawar": 4,
    "shukravar": 4,
    "shukrawaar": 4,
    "shukra": 4,
    "jumma": 4,
    "juma": 4,
    "शुक्रवार": 4,
    "शुक्र": 4,
    "जुम्मा": 4,
    "जुमा": 4,
    "friday": 4,
    "fri": 4,
    # Saturday (5)
    "shanivaar": 5,
    "shaniwar": 5,
    "shanivar": 5,
    "shaniwaar": 5,
    "shani": 5,
    "sanivaar": 5,
    "saniwar": 5,
    "शनिवार": 5,
    "शनि": 5,
    "सनीवार": 5,
    "saturday": 5,
    "sat": 5,
    # Sunday (6)
    "ravivaar": 6,
    "raviwar": 6,
    "ravivar": 6,
    "raviwaar": 6,
    "ravi": 6,
    "itvaar": 6,
    "itwar": 6,
    "itwaar": 6,
    "रविवार": 6,
    "रवि": 6,
    "इतवार": 6,
    "sunday": 6,
}


class ExtractionError(RuntimeError):
    pass


def find_weekdays(text: str) -> set[int]:
    norm_text = unicodedata.normalize("NFKC", text).casefold()
    tokens = re.findall(r"[\w]+", norm_text, re.UNICODE)
    return {WEEKDAY_WORDS[t] for t in tokens if t in WEEKDAY_WORDS}


def is_delivery_ambiguous_or_mismatched(
    delivery: Delivery,
    delivery_quote: str,
    when: datetime | None,
) -> bool:
    if delivery is None:
        return False
    text = f"{delivery.spoken} {delivery_quote}"
    norm_text = unicodedata.normalize("NFKC", text).casefold()

    # 1. Multiple weekdays mentioned
    weekdays = find_weekdays(norm_text)
    if len(weekdays) > 1:
        return True

    # 2. kal / कल mentioned without unambiguous date
    has_kal = bool(re.search(r"(?i)\b(kal|कल)\b", norm_text))
    if has_kal:
        has_explicit_date = bool(
            re.search(
                r"\b([0-3]?\d)(?:st|nd|rd|th)?\s*(?:tarikh|taarikh|तारीख|तारीक|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|[/\.-])",
                norm_text,
            )
        )
        if not has_explicit_date and not weekdays:
            return True

    # 3. Check against recording date when provided
    if when is not None:
        local_when = when.astimezone(KOLKATA_TZ) if when.tzinfo else when.replace(tzinfo=KOLKATA_TZ)
        local_date = local_when.date()
        local_weekday = local_when.weekday()

        if weekdays:
            target_weekday = next(iter(weekdays))
            # Same day weekday
            if target_weekday == local_weekday:
                return True
            # Expected next weekday
            days_ahead = (target_weekday - local_weekday) % 7
            expected_date = local_date + timedelta(days=days_ahead)
            if delivery.date != expected_date:
                return True
        else:
            if delivery.date < local_date:
                return True

    return False


def quote_in_transcripts(quote: str, transcripts: list[str]) -> bool:
    if not quote or not quote.strip():
        return False
    q = unicodedata.normalize("NFKC", quote).strip().casefold()
    q_collapsed = " ".join(q.split())
    for t in transcripts:
        t_norm = unicodedata.normalize("NFKC", t).casefold()
        if q in t_norm:
            return True
        t_collapsed = " ".join(t_norm.split())
        if q_collapsed in t_collapsed:
            return True
    return False


def mentions_item(transcript: str, item: LineItem) -> bool:
    t = unicodedata.normalize("NFKC", transcript).casefold()
    if item.id.casefold() in t:
        return True
    if item.label:
        norm_label = unicodedata.normalize("NFKC", item.label).casefold()
        if norm_label in t:
            return True
        words = [w for w in re.split(r"\W+", norm_label) if len(w) >= 3]
        if any(w in t for w in words):
            return True
    return False


class Extractor:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        http: httpx.Client | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_keys = [k.strip() for k in api_key.split(",") if k.strip()]
        if not self.api_keys:
            self.api_keys = [""]
        self.model = model
        self.http = http or httpx.Client(timeout=30.0)
        self._key_index = 0

    def _post_chat(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        num_keys = len(self.api_keys)
        last_error: Exception | None = None

        for _ in range(num_keys):
            current_key = self.api_keys[self._key_index]
            headers = {"Content-Type": "application/json"}
            if current_key:
                headers["Authorization"] = f"Bearer {current_key}"

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.0,
            }
            url = f"{self.base_url}/chat/completions"

            try:
                resp = self.http.post(url, json=payload, headers=headers)
            except Exception as e:
                raise ExtractionError(f"HTTP request failed: {e}") from e

            if resp.status_code == 429:
                if num_keys > 1:
                    self._key_index = (self._key_index + 1) % num_keys
                    last_error = ExtractionError(f"HTTP 429 rate limit with key {current_key}")
                    continue
                raise ExtractionError(f"HTTP 429 rate limit: {resp.text}")

            if resp.status_code >= 400:
                raise ExtractionError(f"HTTP {resp.status_code}: {resp.text}")

            try:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
            except Exception as e:
                raise ExtractionError(f"Invalid response format: {e}") from e

            return self._parse_json(content)

        raise ExtractionError(f"All API keys rate limited (429): {last_error}")

    def _parse_json(self, content: str) -> dict[str, Any]:
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except Exception as e:
                    raise ExtractionError(f"Failed to parse JSON response: {e}") from e
            raise ExtractionError(f"No JSON object found in response: {content}")

    def _validate_card_evidence(
        self,
        card: JobCard,
        transcripts: list[str],
        when: datetime | None,
    ) -> JobCard:
        delivery_quote = ""
        for ev in card.evidence:
            if ev.field == "delivery":
                delivery_quote = ev.quote
                break

        delivery_invalid = False
        if card.delivery is not None:
            delivery_invalid = is_delivery_ambiguous_or_mismatched(
                card.delivery, delivery_quote, when
            )

        updated_evidence: list[Evidence] = []
        has_delivery_ev = False
        for ev in card.evidence:
            score = ev.review_score
            if not quote_in_transcripts(ev.quote, transcripts):
                score = 0.0

            if ev.field == "delivery":
                has_delivery_ev = True
                if delivery_invalid:
                    score = 0.0

            updated_evidence.append(
                Evidence(field=ev.field, quote=ev.quote, review_score=score)
            )

        if card.delivery is not None and not has_delivery_ev:
            updated_evidence.append(
                Evidence(field="delivery", quote=card.delivery.spoken, review_score=0.0)
            )

        return JobCard(
            items=card.items,
            delivery=card.delivery,
            evidence=tuple(updated_evidence),
        )

    def extract_card(
        self,
        transcript_1: str,
        transcript_2: str,
        when: datetime,
    ) -> JobCard:
        messages = [
            {"role": "system", "content": CARD_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Recording date (Asia/Kolkata): {when.isoformat()}\n\n"
                    f"Transcript 1:\n{transcript_1}\n\n"
                    f"Transcript 2:\n{transcript_2}\n"
                ),
            },
        ]
        data = self._post_chat(messages)

        items_raw = data.get("items", [])
        if not items_raw:
            raise ExtractionError("Extractor returned no items")

        try:
            items = tuple(LineItem.model_validate(it) for it in items_raw)
            delivery = (
                Delivery.model_validate(data["delivery"])
                if data.get("delivery")
                else None
            )
            evidence = tuple(
                Evidence.model_validate(ev) for ev in data.get("evidence", [])
            )
            raw_card = JobCard(items=items, delivery=delivery, evidence=evidence)
        except Exception as e:
            raise ExtractionError(f"Invalid card schema from extractor: {e}") from e

        return self._validate_card_evidence(raw_card, [transcript_1, transcript_2], when)

    def extract_field(
        self,
        field_path: str,
        correction_transcript: str,
        old_card: JobCard,
        when: datetime | None = None,
    ) -> JobCard:
        is_amount = (
            field_path == "amount_paise"
            or field_path.endswith(".amount_paise")
            or "amount" in field_path
        )

        target_item_id: str | None = None
        target_attr: str | None = None

        if field_path == "delivery" or field_path.startswith("delivery"):
            pass
        elif field_path.startswith("items."):
            parts = field_path.split(".", 2)
            target_item_id = parts[1]
            target_attr = parts[2]
            target_item = next((it for it in old_card.items if it.id == target_item_id), None)
            if target_item is None:
                raise ExtractionError(f"Item {target_item_id} not found on card")
            if is_amount and len(old_card.items) > 1:
                if not mentions_item(correction_transcript, target_item):
                    raise ExtractionError("which item?")
        elif len(old_card.items) == 1:
            target_item_id = old_card.items[0].id
            target_attr = "amount_paise" if is_amount else "label"
            field_path = f"items.{target_item_id}.{target_attr}"
        else:
            # Multiple items and unqualified field
            if is_amount:
                mentioned = [it for it in old_card.items if mentions_item(correction_transcript, it)]
                if len(mentioned) == 1:
                    target_item_id = mentioned[0].id
                    target_attr = "amount_paise"
                    field_path = f"items.{target_item_id}.{target_attr}"
                else:
                    raise ExtractionError("which item?")
            else:
                raise ExtractionError("which item?")

        system_prompt = CORRECTION_SYSTEM_PROMPT.replace(
            "Target field: {field}", f"Target field: {field_path}"
        )
        user_message = f"Correction transcript:\n{correction_transcript}\n"
        if when is not None:
            user_message += f"Recording date (Asia/Kolkata): {when.isoformat()}\n"

        resp_data = self._post_chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ])

        quote = str(resp_data.get("evidence_quote") or resp_data.get("quote") or "")
        review_score = float(resp_data.get("review_score", 0.0))
        review_score = max(0.0, min(1.0, review_score))
        value = resp_data.get("value")

        # Validate quote in correction_transcript
        if not quote_in_transcripts(quote, [correction_transcript]):
            review_score = 0.0

        if field_path == "delivery" or field_path.startswith("delivery"):
            try:
                if isinstance(value, dict):
                    new_delivery = Delivery.model_validate(value)
                elif isinstance(value, Delivery):
                    new_delivery = value
                elif value is None:
                    new_delivery = None
                else:
                    raise ExtractionError(f"Unexpected delivery value: {value}")
            except Exception as e:
                raise ExtractionError(f"Invalid delivery format: {e}") from e

            if new_delivery is not None and is_delivery_ambiguous_or_mismatched(new_delivery, quote, when):
                review_score = 0.0

            new_ev = Evidence(field="delivery", quote=quote, review_score=review_score)
            updated_evidence: list[Evidence] = []
            replaced = False
            for ev in old_card.evidence:
                if ev.field == "delivery":
                    updated_evidence.append(new_ev)
                    replaced = True
                else:
                    updated_evidence.append(ev)
            if not replaced:
                updated_evidence.append(new_ev)

            return JobCard(
                items=old_card.items,
                delivery=new_delivery,
                evidence=tuple(updated_evidence),
            )

        # Handling line item field update
        target_item = next(it for it in old_card.items if it.id == target_item_id)
        if target_attr == "amount_paise":
            if isinstance(value, str):
                digits = re.sub(r"[^\d]", "", value)
                amount = int(digits) if digits else None
            elif value is not None:
                amount = int(value)
            else:
                amount = None
            new_item = LineItem(
                id=target_item.id,
                label=target_item.label,
                kind=target_item.kind,
                amount_paise=amount,
            )
        elif target_attr == "label":
            new_item = LineItem(
                id=target_item.id,
                label=str(value) if value is not None else None,
                kind=target_item.kind,
                amount_paise=target_item.amount_paise,
            )
        else:
            raise ExtractionError(f"Unsupported item attribute: {target_attr}")

        new_items = tuple(
            new_item if it.id == target_item_id else it
            for it in old_card.items
        )

        new_ev = Evidence(field=field_path, quote=quote, review_score=review_score)
        updated_evidence = []
        replaced = False
        for ev in old_card.evidence:
            if ev.field == field_path:
                updated_evidence.append(new_ev)
                replaced = True
            else:
                updated_evidence.append(ev)
        if not replaced:
            updated_evidence.append(new_ev)

        return JobCard(
            items=new_items,
            delivery=old_card.delivery,
            evidence=tuple(updated_evidence),
        )
