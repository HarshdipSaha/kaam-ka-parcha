from datetime import datetime, timezone
import pytest
from parcha.session import Conflict, SessionStore
from tests.test_schema import sample_card

NOW = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)


def test_stale_readback_cannot_confirm_new_revision():
    store = SessionStore()
    session = store.create()
    session = store.set_card(session.id, expected_revision=0, card=sample_card())
    session = store.start_readback(session.id, expected_revision=1)
    store.set_card(session.id, expected_revision=1, card=sample_card())
    with pytest.raises(Conflict, match="stale read-back"):
        store.confirm(session.id, expected_revision=2, when=NOW)


def test_review_needed_card_cannot_be_read_back():
    store = SessionStore()
    session = store.create()
    card = sample_card().model_copy(update={"evidence": []})
    store.set_card(session.id, expected_revision=0, card=card)
    with pytest.raises(Conflict, match="review"):
        store.start_readback(session.id, expected_revision=1)


def test_confirmed_session_rejects_mutation():
    store = SessionStore()
    session = store.create()
    store.set_card(session.id, expected_revision=0, card=sample_card())
    store.start_readback(session.id, expected_revision=1)
    store.confirm(session.id, expected_revision=1, when=NOW)
    with pytest.raises(Conflict, match="confirmed"):
        store.set_card(session.id, expected_revision=1, card=sample_card())


def test_concurrent_updates_same_expected_revision_fails_one():
    store = SessionStore()
    session = store.create()
    # update once
    store.set_card(session.id, expected_revision=0, card=sample_card())
    # another update with expected_revision=0 must raise Conflict
    with pytest.raises(Conflict, match="stale revision"):
        store.set_card(session.id, expected_revision=0, card=sample_card())
