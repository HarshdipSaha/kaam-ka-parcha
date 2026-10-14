import httpx
import json
import pytest
from parcha.jev import JevClient, JevUnavailable


def test_review_masks_identifiers_and_returns_validated_advice():
    def handler(request):
        assert '9876543210' not in request.content.decode()
        assert '[PHONE]' in request.content.decode()
        return httpx.Response(200, json={'model': 'jev-1.13.0', 'answers': {'intent': {
            'type': 'choice', 'choice': 'correction', 'confidence': .9,
            'probabilities': {'accept': .01, 'correction': .9, 'reject': .01, 'unclear': .08}}}})
    advice = JevClient('secret', http=httpx.Client(transport=httpx.MockTransport(handler))).review('call 9876543210, price galat hai')
    assert advice['choice'] == 'correction'
    assert advice['model'] == 'jev-1.13.0'


@pytest.mark.parametrize('answer', [
    {'choice': 'accept', 'confidence': float('nan'), 'probabilities': {'accept': 1, 'correction': 0, 'reject': 0, 'unclear': 0}},
    {'choice': 'invented', 'confidence': 1, 'probabilities': {}},
    {'choice': 'accept', 'confidence': 1, 'probabilities': ['accept', 'correction', 'reject', 'unclear']},
])
def test_invalid_response_abstains(answer):
    body = json.dumps({'model': 'test', 'answers': {'intent': answer}})
    http = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, text=body)))
    with pytest.raises(JevUnavailable):
        JevClient('secret', http=http).review('hmm')


def test_http_failure_does_not_expose_key():
    http = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(503, text='secret')))
    with pytest.raises(JevUnavailable) as exc:
        JevClient('secret', http=http).review('hmm')
    assert 'secret' not in str(exc.value)


@pytest.mark.parametrize('choice', ['accept', 'correction', 'reject', 'outage'])
def test_advice_cannot_confirm_or_edit_an_unclear_reply(choice):
    from tests.conftest import FakeExtractor, make_test_card
    from tests.test_reply import MockPrisma
    from parcha.session import SessionStore
    from parcha.workflow import Workflow

    class Reviewer:
        def review(self, text):
            if choice == 'outage':
                raise JevUnavailable('unavailable')
            return {'choice': choice, 'confidence': .99, 'model': 'test'}

    store = SessionStore()
    session = store.create()
    session = store.set_card(session.id, expected_revision=0, card=make_test_card())
    store.start_readback(session.id, expected_revision=1)
    workflow = Workflow(store, MockPrisma('hmm'), FakeExtractor(),
                        normalize_audio=lambda blob, mime: blob, reply_reviewer=Reviewer())
    result = workflow.reply(session.id, b'audio', 'audio/wav', expected_revision=1, readback_revision=1)
    assert result.outcome == 'retry'
    assert result.session.status == 'awaiting_reply'
    assert result.session.card == session.card
    assert any(log.mode == 'jev_review' for log in result.session.logs)
    assert result.session.logs[-1].role == 'customer'
