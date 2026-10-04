import json
import httpx
import pytest
from parcha.gnani import GnaniError, PrismaClient, TimbreClient

def test_prisma_dual_modes_use_documented_multipart_fields():
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"success": True, "transcript": "₹450"})
    http = httpx.Client(transport=httpx.MockTransport(handler))
    client = PrismaClient("test-key", http=http)
    assert client.transcribe(b"RIFFdemo", mode="transcribe") == "₹450"
    assert client.transcribe(b"RIFFdemo", mode="verbatim", bias=["brake"], score=1.0) == "₹450"
    assert all(r.url.path == "/stt/v3" for r in requests)
    assert all(r.headers["x-api-key-id"] == "test-key" for r in requests)
    first, second = (r.content.decode("utf-8", errors="replace") for r in requests)
    assert 'name="format"\r\n\r\ntranscribe' in first
    assert 'name="language_code"\r\n\r\nhi-IN' in first
    assert 'name="format"\r\n\r\nverbatim' in second
    assert 'name="bias_list"' in second and '["brake"]' in second

def test_invalid_bias_is_rejected_before_paid_call():
    client = PrismaClient("test-key", http=httpx.Client())
    with pytest.raises(ValueError, match="single words"):
        client.transcribe(b"RIFFdemo", mode="verbatim", bias=["brake pad"])

def test_timbre_requests_8k_mulaw_and_returns_bytes():
    def handler(request):
        body = json.loads(request.content)
        assert request.url.path == "/api/v1/tts/inference"
        assert body["model"] == "timbre-v2.5"
        assert body["language"] == "hi-IN"
        assert body["audio_config"]["container"] == "mulaw"
        assert body["audio_config"]["sample_rate"] == 8000
        return httpx.Response(200, content=b"\xff" * 8000)
    client = TimbreClient("test-key", http=httpx.Client(transport=httpx.MockTransport(handler)))
    assert len(client.synthesize("कुल ₹650")) == 8000

def test_error_redacts_key():
    http = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(403, json={"success": False})))
    with pytest.raises(GnaniError) as error:
        PrismaClient("secret-value", http=http).transcribe(b"x", mode="transcribe")
    assert "secret-value" not in str(error.value)
