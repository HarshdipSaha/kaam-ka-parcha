from dataclasses import replace

from fastapi.testclient import TestClient
import pytest

from parcha.app import AppServices, create_app
from parcha.config import Settings
from parcha.guard import SlidingWindow, access_ok, access_token, client_ip, is_guarded
from parcha.session import CapacityError, SessionStore


def app_with(fake_services: AppServices, **overrides) -> TestClient:
    services = AppServices(replace(fake_services.settings, **overrides), fake_services.store, fake_services.workflow, fake_services.timbre)
    return TestClient(create_app(services))


def test_sliding_window_blocks_then_recovers():
    now = [0.0]
    w = SlidingWindow(2, 60.0, clock=lambda: now[0])
    assert w.hit("a") == 0 and w.hit("a") == 0
    assert w.hit("a") > 0
    assert w.hit("b") == 0
    now[0] = 61.0
    assert w.hit("a") == 0
    assert SlidingWindow(0, 60.0).hit("a") == 0


def test_client_ip_trusts_only_the_proxy_appended_entry():
    headers = {"x-forwarded-for": "6.6.6.6, 203.0.113.9"}
    assert client_ip(headers, "10.0.0.1", trust_proxy=True) == "203.0.113.9"
    assert client_ip(headers, "10.0.0.1", trust_proxy=False) == "10.0.0.1"


def test_guarded_paths():
    assert is_guarded("POST", "/sessions") and is_guarded("POST", "/sessions/x/intake")
    assert is_guarded("POST", "/sessions/x/reask/items.a.amount_paise")
    assert is_guarded("POST", "/sessions/x/readback") and is_guarded("POST", "/sessions/x/reply")
    assert not is_guarded("GET", "/sessions/x") and not is_guarded("GET", "/health")


def test_burst_returns_429_without_calling_speech_fakes(fake_services):
    client = app_with(fake_services, rate_limit_per_minute=3)
    sid = client.post("/sessions").json()["id"]
    codes = [
        client.post(f"/sessions/{sid}/intake", data={"expected_revision": 0}, files={"audio": ("a.wav", b"x", "audio/wav")}).status_code
        for _ in range(5)
    ]
    assert 429 in codes
    before = len(fake_services.workflow.prisma.calls)
    res = client.post(f"/sessions/{sid}/intake", data={"expected_revision": 0}, files={"audio": ("a.wav", b"x", "audio/wav")})
    assert res.status_code == 429 and res.headers["retry-after"]
    assert len(fake_services.workflow.prisma.calls) == before
    assert client.get("/health").status_code == 200


def test_session_creation_cap_per_ip(fake_services):
    client = app_with(fake_services, sessions_per_ip_per_hour=2)
    assert [client.post("/sessions").status_code for _ in range(3)] == [200, 200, 429]


def test_oversized_upload_rejected_before_processing(fake_services):
    client = app_with(fake_services, max_upload_bytes=1000)
    sid = client.post("/sessions").json()["id"]
    res = client.post(f"/sessions/{sid}/intake", data={"expected_revision": 0}, files={"audio": ("a.wav", b"x" * 200_000, "audio/wav")})
    assert res.status_code == 413
    small_over = client.post(f"/sessions/{sid}/intake", data={"expected_revision": 0}, files={"audio": ("a.wav", b"x" * 1500, "audio/wav")})
    assert small_over.status_code == 413


def test_total_session_cap():
    store = SessionStore(max_total=2)
    a, b = store.create(), store.create()
    assert len(store._items) == 2
    store.create()  # evicts the oldest untouched draft rather than growing
    assert len(store._items) == 2
    assert a.id not in store._items


def test_total_session_cap_refuses_when_nothing_is_evictable(fake_services):
    store = SessionStore(max_total=1)
    first = store.create()
    store._items[first.id] = replace(first, status="review")  # real work in progress is never evicted
    with pytest.raises(CapacityError):
        store.create()


def test_access_code_gate(fake_services):
    client = app_with(fake_services, demo_access_code="open-sesame")
    assert client.get("/health").status_code == 200
    assert client.post("/sessions").status_code == 401
    page = client.get("/workshop", headers={"accept": "text/html"}, follow_redirects=False)
    assert page.status_code == 303 and page.headers["location"] == "/gate"
    assert client.post("/gate", data={"code": "wrong"}).status_code == 401
    ok = client.post("/gate", data={"code": "open-sesame"}, follow_redirects=False)
    assert ok.status_code == 303
    assert client.post("/sessions").status_code == 200
    assert access_ok("", None) and not access_ok("c", None) and access_ok("c", access_token("c"))


def test_settings_parse_guard_env():
    s = Settings.from_mapping({"RATE_LIMIT_PER_MINUTE": "10", "DEMO_ACCESS_CODE": " x ", "TRUST_PROXY": "1", "MAX_UPLOAD_BYTES": "bad"})
    assert s.rate_limit_per_minute == 10 and s.demo_access_code == "x" and s.trust_proxy
    assert s.max_upload_bytes == 8 * 1024 * 1024
    assert "demo_access_code" not in repr(s)


def test_unexpected_errors_are_generic(fake_services):
    app = create_app(fake_services)

    @app.get("/boom")
    def boom():
        raise RuntimeError("http://private-host.internal/secret")

    res = TestClient(app, raise_server_exceptions=False).get("/boom")
    assert res.status_code == 500 and "private-host" not in res.text


def test_gate_guesses_are_rate_limited(fake_services):
    client = app_with(fake_services, demo_access_code="open-sesame")
    codes = [client.post("/gate", data={"code": f"guess{i}"}).status_code for i in range(12)]
    assert codes[:10] == [401] * 10 and codes[10:] == [429, 429]
    assert client.post("/gate", data={"code": "open-sesame"}).status_code == 429  # even the right code waits


def test_daily_cap_stops_credit_spending_calls_app_wide(fake_services):
    client = app_with(fake_services, max_speech_calls_per_day=2)
    sid = client.post("/sessions").json()["id"]            # creating sessions spends nothing, so it is not counted
    assert client.post("/sessions").status_code == 200

    def intake():
        return client.post(f"/sessions/{sid}/intake", data={"expected_revision": 0}, files={"audio": ("a.wav", b"x", "audio/wav")})

    assert intake().status_code != 503 and intake().status_code != 503
    before = len(fake_services.workflow.prisma.calls)
    res = intake()
    assert res.status_code == 503 and res.headers["retry-after"]
    assert len(fake_services.workflow.prisma.calls) == before   # refused before any speech call
    assert client.get("/health").status_code == 200 and client.get(f"/sessions/{sid}").status_code == 200


def test_daily_cap_defaults_off_and_parses_env():
    assert Settings().max_speech_calls_per_day == 0
    assert Settings.from_mapping({"MAX_SPEECH_CALLS_PER_DAY": "500"}).max_speech_calls_per_day == 500
