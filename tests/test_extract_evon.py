import json
from datetime import datetime, timezone

import httpx
import pytest

from parcha.config import Settings
from parcha.extract import CARD_RESPONSE_SCHEMA, Extractor

WHEN = datetime(2026, 10, 4, 10, tzinfo=timezone.utc)
T = "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
V = "front brake pad saade chaar sau labour do sau Somvaar shaam tak"
CARD = {"items": [{"id": "part-1", "label": "front brake pad", "kind": "part", "amount_paise": None},
                  {"id": "labour-1", "label": "labour", "kind": "labour", "amount_paise": None}],
        "delivery": {"date": "2026-10-05", "window": "evening", "spoken": "Somvaar shaam tak"},
        "evidence": [{"field": "items.part-1.label", "quote": "front brake pad", "review_score": 0.95},
                     {"field": "items.labour-1.label", "quote": "labour", "review_score": 0.95},
                     {"field": "delivery", "quote": "Somvaar shaam tak", "review_score": 0.9}]}


def capture(content, seen):
    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_evon_turns_thinking_off_and_requests_the_card_schema():
    seen = []
    Extractor("http://localhost:8080/v1", "", "gnani-evon-v3.3", capture(json.dumps(CARD), seen)).extract_card(T, V, WHEN)
    assert seen[0]["chat_template_kwargs"] == {"enable_thinking": False}
    assert seen[0]["response_format"] == {"type": "json_schema",
                                          "json_schema": {"name": "job_card", "schema": CARD_RESPONSE_SCHEMA}}


def test_external_provider_sends_a_plain_openai_payload():
    seen = []
    Extractor("http://t/v1", "k", "m", capture(json.dumps(CARD), seen), provider="external").extract_card(T, V, WHEN)
    assert "chat_template_kwargs" not in seen[0] and "response_format" not in seen[0]


def test_reasoning_block_is_stripped_before_parsing():
    card = Extractor("http://l/v1", "", "m", capture("<think>maybe ₹999?</think>" + json.dumps(CARD), [])
                     ).extract_card(T, V, WHEN)
    assert [it.label for it in card.items] == ["front brake pad", "labour"]


def test_groq_key_alone_no_longer_configures_an_extractor():
    settings = Settings.from_mapping({"GROQ_API_KEY": "groq-secret"})
    assert settings.extractor_base_url == "" and settings.extractor_provider == "evon"
    with pytest.raises(ValueError, match="extractor endpoint and model are required"):
        settings.require_extractor()
