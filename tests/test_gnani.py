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


def test_rate_limit_is_retried_then_succeeds(monkeypatch):
    import httpx
    from parcha import gnani

    monkeypatch.setattr(gnani, "RETRY_DELAYS", (0, 0))
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) < 3:
            return httpx.Response(429)
        return httpx.Response(200, json={"success": True, "transcript": "ok"})

    client = gnani.PrismaClient("k", http=httpx.Client(transport=httpx.MockTransport(handler)))
    assert client.transcribe(b"wav", mode="transcribe") == "ok"
    assert len(calls) == 3


def test_rate_limit_gives_up_after_two_retries(monkeypatch):
    import httpx
    import pytest
    from parcha import gnani

    monkeypatch.setattr(gnani, "RETRY_DELAYS", (0, 0))
    client = gnani.PrismaClient("k", http=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(429))))
    with pytest.raises(gnani.GnaniError) as err:
        client.transcribe(b"wav", mode="transcribe")
    assert err.value.status == 429


def test_long_readback_is_split_below_the_tts_limit_and_audio_joined():
    from parcha.gnani import TTS_MAX_CHARS, chunk_for_tts

    sentence = "front brake pad: चार सौ पचास रुपये, labour: दो सौ रुपये."
    text = " ".join([sentence] * 60)
    assert len(text) > TTS_MAX_CHARS * 2
    chunks = chunk_for_tts(text)
    assert len(chunks) >= 3 and all(len(c) <= TTS_MAX_CHARS for c in chunks)
    assert " ".join(chunks) == text   # nothing lost or reordered

    sent: list[str] = []

    def handler(request):
        sent.append(json.loads(request.content)["text"])
        return httpx.Response(200, content=b"\xff" * 100)

    client = TimbreClient("test-key", http=httpx.Client(transport=httpx.MockTransport(handler)))
    audio = client.synthesize(text)
    assert sent == chunks and len(audio) == 100 * len(chunks)


def test_chunking_breaks_an_unpunctuated_run_at_word_boundaries():
    from parcha.gnani import chunk_for_tts

    text = " ".join(["shabd"] * 500)
    chunks = chunk_for_tts(text, limit=100)
    assert all(len(c) <= 100 for c in chunks) and " ".join(chunks) == text
    assert chunk_for_tts("chhota sa") == ["chhota sa"]


def _client_for(statuses_by_key: dict[str, list[int]], seen: list[str], cls=PrismaClient, *keys: str):
    """Fake Gnani: each key answers with its scripted statuses (last one repeats); 200 carries a transcript/audio."""
    def handler(request):
        key = request.headers["x-api-key-id"]
        seen.append(key)
        queue = statuses_by_key[key]
        status = queue.pop(0) if len(queue) > 1 else queue[0]
        if status != 200:
            return httpx.Response(status, json={"success": False})
        return httpx.Response(200, json={"success": True, "transcript": "₹450"}, headers={}) if cls is PrismaClient \
            else httpx.Response(200, content=b"\xff" * 10)
    return cls(",".join(keys), http=httpx.Client(transport=httpx.MockTransport(handler)))


def test_spent_key_is_retired_and_the_next_key_takes_over_for_good():
    seen: list[str] = []
    client = _client_for({"k1": [403], "k2": [200]}, seen, PrismaClient, "k1", "k2")
    assert client.transcribe(b"x", mode="transcribe") == "₹450"
    assert seen == ["k1", "k2"]                       # one refused call, retried on the next key
    seen.clear()
    assert client.transcribe(b"x", mode="transcribe") == "₹450"
    assert seen == ["k2"]                              # the spent key is never tried again
    assert client.api_key == "k2" and "k1" not in repr(client)


def test_all_keys_spent_raises_a_gnani_403():
    seen: list[str] = []
    client = _client_for({"k1": [403], "k2": [403]}, seen, PrismaClient, "k1", "k2")
    with pytest.raises(GnaniError) as error:
        client.transcribe(b"x", mode="transcribe")
    assert error.value.status == 403 and seen == ["k1", "k2"]
    assert "k1" not in str(error.value) and "k2" not in str(error.value)


def test_timbre_and_prisma_share_one_pool_and_a_single_key_still_works():
    seen: list[str] = []
    prisma = _client_for({"k1": [401], "k2": [200]}, seen, PrismaClient, "k1", "k2")
    timbre = TimbreClient(prisma.pool, http=httpx.Client(transport=httpx.MockTransport(
        lambda r: (seen.append(r.headers["x-api-key-id"]), httpx.Response(200, content=b"\xff" * 5))[1])))
    prisma.transcribe(b"x", mode="transcribe")          # retires k1 (401), moves to k2
    seen.clear()
    assert timbre.synthesize("namaste") == b"\xff" * 5 and seen == ["k2"]   # TTS skips the key Prisma found spent

    single: list[str] = []
    one = _client_for({"only": [403]}, single, PrismaClient, "only")
    with pytest.raises(GnaniError):
        one.transcribe(b"x", mode="transcribe")
    assert single == ["only"]                           # no key to switch to: one attempt, no loop


def test_keys_are_trimmed_deduplicated_and_validated():
    from parcha.config import Settings
    from parcha.gnani import KeyPool
    from parcha.gnani_ws import telephony_headers

    assert KeyPool.from_value(" a , b,,a ").current() == "a" and KeyPool.from_value(" a , b,,a ").remaining == 2
    assert telephony_headers("first,second")["x-api-key-id"] == "first"
    Settings(api_key="replace_me, real").require_gnani()
    with pytest.raises(ValueError):
        Settings(api_key="replace_me, ").require_gnani()
