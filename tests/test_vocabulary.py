import httpx

from parcha.gnani import PrismaClient
from parcha.vocabulary import AUTOMOTIVE_BIAS_WORDS


def test_automotive_bias_vocabulary_is_large_and_api_safe():
    assert len(AUTOMOTIVE_BIAS_WORDS) >= 60
    assert len(AUTOMOTIVE_BIAS_WORDS) == len(set(AUTOMOTIVE_BIAS_WORDS))

    # Validate at the public client boundary without making a paid network call.
    client = PrismaClient(
        "test-key",
        http=httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json={"success": True, "transcript": "ok"})
            )
        ),
    )
    assert client.transcribe(b"unused", mode="verbatim", bias=list(AUTOMOTIVE_BIAS_WORDS)) == "ok"
