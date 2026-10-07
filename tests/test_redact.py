import json
from datetime import datetime, timezone

from parcha.extract import Extractor
from parcha.redact import mask_pii
from tests.test_extract_evon import CARD, T, V, WHEN, capture


def test_masks_phone_aadhaar_and_pan_but_leaves_amounts_alone():
    assert mask_pii("call 9876543210 now") == "call [PHONE] now"
    assert mask_pii("+91 98765 43210 aur 98765-43210") == "[PHONE] aur [PHONE]"
    assert mask_pii("aadhaar 1234 5678 9012 ya 123456789012") == "aadhaar [AADHAAR] ya [AADHAAR]"
    assert mask_pii("PAN ABCDE1234F hai") == "PAN [PAN] hai"
    for kept in ("front brake pad ₹450, labour ₹200", "Rs 9876543210 nahi", "₹9876543210", "KA-01-AB-1234", "2026-10-05"):
        assert mask_pii(kept) == kept


def test_extractor_request_carries_no_identifiers_but_keeps_the_estimate():
    seen = []
    noisy = T + ", mera number 9876543210 hai"
    Extractor("http://l/v1", "", "m", capture(json.dumps(CARD), seen)).extract_card(noisy, V, WHEN)
    sent = json.dumps(seen[0]["messages"], ensure_ascii=False)
    assert "9876543210" not in sent and "[PHONE]" in sent
    assert "front brake pad ₹450" in sent and "saade chaar sau" in sent
