from datetime import date, datetime

import pytest

from parcha.artefact import audit_manifest
from parcha.gnani import GnaniError
from parcha.money import decide_amounts
from parcha.schema import Delivery, Evidence, JobCard, LineItem, review_fields
from parcha.session import Conflict, SessionStore
from parcha.workflow import RepeatRequest, Workflow
from tests.fakes import ScriptedPrisma

T_EN = "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
V_EN = "front brake pad saade chaar sau labour do sau Somvaar shaam tak"
T_W2 = "फ्रंट ब्रेक पैड 04:30 100 लेबर 200 मंगलवार शाम तक"          # effort 005, real transcribe output
V_W2 = "फ्रंट ब्रेक पैड साढ़े चार सौ लेबर दो सौ मंगलवार शाम तक"


def card(labels=("front brake pad", "labour"), amounts=(99900, 99900)) -> JobCard:
    """Extractor output with deliberately wrong amounts: the money path must replace them."""
    return JobCard(
        items=[LineItem(id="part-1", label="front brake pad", kind="part", amount_paise=amounts[0]),
               LineItem(id="labour-1", label="labour", kind="labour", amount_paise=amounts[1])],
        delivery=Delivery(date=date(2026, 10, 6), window="evening", spoken="shaam tak"),
        evidence=[Evidence(field="items.part-1.label", quote=labels[0], review_score=0.95),
                  Evidence(field="items.part-1.amount_paise", quote="₹999", review_score=0.95),
                  Evidence(field="items.labour-1.label", quote=labels[1], review_score=0.95),
                  Evidence(field="items.labour-1.amount_paise", quote="₹999", review_score=0.95),
                  Evidence(field="delivery", quote="shaam tak", review_score=0.95)],
    )


class CardExtractor:
    def __init__(self, result):
        self.result = result

    def extract_card(self, normalized, verbatim, recorded_at_utc):
        return self.result

    def extract_field(self, *args, **kwargs):
        raise AssertionError("amount re-ask must not call the extractor")


def service(prisma, extractor):
    store = SessionStore()
    session = store.create()
    return Workflow(store=store, prisma=prisma, extractor=extractor,
                    normalize_audio=lambda b, m: b"RIFFpcm"), store, session.id


def abstentions(session):
    return {log.mode.removeprefix("abstain:"): log.text for log in session.logs if log.mode.startswith("abstain:")}


def test_intake_requires_independent_confirmation_even_when_both_modes_agree():
    wf, _, sid = service(ScriptedPrisma([T_EN, V_EN]), CardExtractor(card()))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert [decision.paise for decision in decide_amounts(V_EN, T_EN, expected_count=2)] == [45000, 20000]
    assert [it.amount_paise for it in s.card.items] == [None, None]
    assert abstentions(s) == {
        "items.part-1.amount_paise": "independent_confirmation_required",
        "items.labour-1.amount_paise": "independent_confirmation_required",
    }
    assert set(review_fields(s.card)) == set(abstentions(s))
    # The mechanic sees what was heard, but zero-score evidence never counts as confirmation.
    heard = {ev.field: ev for ev in s.card.evidence if ev.field.endswith(".amount_paise")}
    assert set(heard) == set(abstentions(s))
    assert all(ev.quote.strip() and ev.review_score == 0.0 for ev in heard.values())


def test_w2_clock_formatted_fraction_now_agrees_and_awaits_independent_confirmation():
    # Real transcribe output "04:30 100" is how the formatter writes साढ़े चार सौ; it agrees with the verbatim reading.
    wf, _, sid = service(ScriptedPrisma([T_W2, V_W2]), CardExtractor(card(labels=("फ्रंट ब्रेक पैड", "लेबर"))))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert [it.amount_paise for it in s.card.items] == [None, None]
    assert abstentions(s) == {
        "items.part-1.amount_paise": "independent_confirmation_required",
        "items.labour-1.amount_paise": "independent_confirmation_required",
    }
    assert decide_amounts(V_W2, T_W2, expected_count=2)[0].paise == 45000


def test_incomplete_number_abstains():
    wf, _, sid = service(ScriptedPrisma([T_EN, "front brake pad saade labour do sau shaam tak"]), CardExtractor(card()))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert [it.amount_paise for it in s.card.items] == [None, None]
    assert abstentions(s) == {
        "items.part-1.amount_paise": "incomplete_number",
        "items.labour-1.amount_paise": "independent_confirmation_required",
    }


def test_amount_count_mismatch_abstains_every_amount():
    wf, _, sid = service(ScriptedPrisma([T_EN, "front brake pad saade chaar sau"]), CardExtractor(card()))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert [it.amount_paise for it in s.card.items] == [None, None]
    assert set(abstentions(s).values()) == {"ambiguous_attachment"}


def test_spoken_total_that_matches_the_items_is_not_an_extra_item():
    wf, _, sid = service(ScriptedPrisma(["front brake pad ₹450, labour ₹200, kul ₹650, shaam tak",
                                         "front brake pad saade chaar sau labour do sau kul saade chhe sau shaam tak"]),
                         CardExtractor(card()))
    session = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert [it.amount_paise for it in session.card.items] == [None, None]
    assert set(abstentions(session).values()) == {"independent_confirmation_required"}


def test_spoken_total_that_disagrees_with_the_items_abstains_every_amount():
    wf, _, sid = service(ScriptedPrisma(["front brake pad ₹450, labour ₹200, kul ₹700, shaam tak",
                                         "front brake pad saade chaar sau labour do sau kul saat sau shaam tak"]),
                         CardExtractor(card()))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert [it.amount_paise for it in s.card.items] == [None, None]
    assert set(abstentions(s).values()) == {"crosscheck_disagreement"}


def test_mid_sentence_self_correction_abstains_instead_of_guessing():
    wf, _, sid = service(ScriptedPrisma([T_EN, "front brake pad saade chaar sau nahi paanch sau labour do sau"]),
                         CardExtractor(card()))
    assert [it.amount_paise for it in wf.intake(sid, b"a", "audio/webm", expected_revision=0).card.items] == [None, None]


def test_english_label_quotes_absent_from_devanagari_transcripts_abstain():
    wf, _, sid = service(ScriptedPrisma([T_W2, V_W2]), CardExtractor(card()))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert set(abstentions(s).values()) == {"ambiguous_attachment"}


def test_empty_transcripts_request_a_repeat_without_touching_the_session():
    wf, store, sid = service(ScriptedPrisma(["", "  "]), CardExtractor(card()))
    with pytest.raises(RepeatRequest) as info:
        wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert info.value.reason == "empty_transcript" and store.get(sid).revision == 0


@pytest.mark.parametrize("status,reason", [(504, "provider_504"), (429, "provider_429")])
def test_provider_errors_request_a_repeat(status, reason):
    wf, store, sid = service(ScriptedPrisma([GnaniError(f"HTTP {status}", status=status)]), CardExtractor(card()))
    with pytest.raises(RepeatRequest) as info:
        wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert info.value.reason == reason and store.get(sid).revision == 0


def test_other_provider_errors_still_raise_gnani_error():
    wf, _, sid = service(ScriptedPrisma([GnaniError("boom", status=500)]), CardExtractor(card()))
    with pytest.raises(GnaniError):
        wf.intake(sid, b"a", "audio/webm", expected_revision=0)


def test_abstained_card_cannot_be_read_back_and_reason_is_in_audit_manifest():
    wf, store, sid = service(ScriptedPrisma([T_W2, V_W2]), CardExtractor(card(labels=("फ्रंट ब्रेक पैड", "लेबर"))))
    s = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    with pytest.raises(Conflict, match="card needs review"):
        store.start_readback(sid, expected_revision=s.revision)
    assert "abstain:items.part-1.amount_paise" in [e["mode"] for e in audit_manifest(store.get(sid))["logs"]]


def test_amount_reask_uses_grammar_and_keeps_other_fields():
    prisma = ScriptedPrisma([T_W2, V_W2, "₹450", "साढ़े चार सौ"])
    wf, _, sid = service(prisma, CardExtractor(card(labels=("फ्रंट ब्रेक पैड", "लेबर"))))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    s2 = wf.reask(sid, "items.part-1.amount_paise", b"r", "audio/webm", expected_revision=s1.revision)
    assert [it.amount_paise for it in s1.card.items] == [None, None]
    assert [it.amount_paise for it in s2.card.items] == [45000, None]
    assert s2.card.delivery == s1.card.delivery
    assert review_fields(s2.card) == ["items.labour-1.amount_paise"]
    assert s2.logs[-1].mode == "reask:items.part-1.amount_paise"
    assert [c[1] for c in prisma.calls[2:]] == ["transcribe", "verbatim"]


def test_amount_reask_with_provider_429_leaves_field_unset_and_logs_reason():
    wf, _, sid = service(ScriptedPrisma([T_EN, V_EN, GnaniError("HTTP 429", status=429)]), CardExtractor(card()))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    s2 = wf.reask(sid, "items.part-1.amount_paise", b"r", "audio/webm", expected_revision=s1.revision)
    assert [it.amount_paise for it in s2.card.items] == [None, None]
    assert abstentions(s2)["items.part-1.amount_paise"] == "provider_429"


def test_correction_with_two_numbers_abstains():
    wf, _, sid = service(ScriptedPrisma([T_EN, V_EN, "₹300 ₹350", "teen sau nahi saade teen sau"]), CardExtractor(card()))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    s2 = wf.reask(sid, "items.part-1.amount_paise", b"r", "audio/webm", expected_revision=s1.revision)
    assert s2.card.items[0].amount_paise is None
    assert abstentions(s2)["items.part-1.amount_paise"] == "ambiguous_attachment"



def test_disputed_reask_keeps_what_was_heard_without_confirming_it():
    wf, _, sid = service(ScriptedPrisma([T_EN, V_EN, "₹300", "चार सौ"]), CardExtractor(card()))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    s2 = wf.reask(sid, "items.part-1.amount_paise", b"r", "audio/webm", expected_revision=s1.revision)
    field = "items.part-1.amount_paise"
    assert s2.card.items[0].amount_paise is None
    assert abstentions(s2)[field] == "crosscheck_disagreement"
    heard = next(ev for ev in s2.card.evidence if ev.field == field)
    assert heard.quote.strip() and heard.review_score == 0.0
    assert field in review_fields(s2.card)


@pytest.mark.parametrize("verbatim, transcribe, paise", [
    ("साढ़े चार सौ रुपये", "04:30 ₹100", 45000),
    ("साढ़े तीन सौ रुपये।", "03:30 100 रुपये।", 35000),
    ("डेढ़ सौ", "डेढ़ 100", 15000),
    ("ढाई सौ रुपए", "ढाई ₹100", 25000),
    ("पौने दो सौ रुपये", "पौने ₹200", 17500),
    ("पौने दो हज़ार रुपए", "पौने ₹2,000", 175000),
    ("साढ़े सात सौ रुपये", "07:30 ₹100", 75000),
    ("साढ़े तीन हज़ार रुपये", "03:30 ₹1,000", 350000),
    ("साढ़े तीन हज़ार।", "03:30 हज़ार।", 350000),
    ("साढ़े दस हजार", "10:30 हजार।", 1050000),
    ("साढ़े चार हज़ार", "साढ़े 4,000", 450000),
    ("साढ़े उनतीस हज़ार", "साढ़े 29,000", 2950000),
    ("साढ़े तेईस हज़ार।", "साढ़े 23 हज़ार।", 2350000),
    ("साढ़े सैंतीस हज़ार रुपये।", "साढ़े 37,000 रुपये।", 3750000),
])
def test_transcribe_pass_fraction_formatting_still_cross_checks_the_spoken_amount(verbatim, transcribe, paise):
    [decision] = decide_amounts(verbatim, transcribe, expected_count=1)
    assert (decision.paise, decision.reason) == (paise, None)


@pytest.mark.parametrize("verbatim, transcribe", [
    ("साढ़े चार सौ रुपये", "04:30 ₹200"),   # formatting says 900, speech says 450
    ("साढ़े चार सौ रुपये", "05:30 ₹100"),
    ("डेढ़ सौ", "डेढ़ ₹1,000"),
])
def test_fraction_normalisation_never_hides_a_real_disagreement(verbatim, transcribe):
    [decision] = decide_amounts(verbatim, transcribe, expected_count=1)
    assert decision.paise is None and decision.reason == "crosscheck_disagreement"


def _reask(wf, sid, revision, transcribe, verbatim):
    wf.prisma.script.extend([transcribe, verbatim])
    return wf.reask(sid, "items.part-1.amount_paise", b"r", "audio/webm", expected_revision=revision)


def test_reask_matching_the_intake_candidate_is_two_agreeing_recordings():
    wf, _, sid = service(ScriptedPrisma([T_EN, V_EN]), CardExtractor(card()))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    s2 = _reask(wf, sid, s1.revision, "₹450", "साढ़े चार सौ")
    assert s2.card.items[0].amount_paise == 45000
    assert "items.part-1.amount_paise" not in review_fields(s2.card)


def test_reask_that_differs_from_the_candidate_needs_one_more_agreeing_recording():
    wf, _, sid = service(ScriptedPrisma([T_EN, V_EN]), CardExtractor(card()))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    s2 = _reask(wf, sid, s1.revision, "₹12", "बारह")          # truncated tail: "बारह सौ" heard as "बारह"
    assert s2.card.items[0].amount_paise is None
    assert abstentions(s2)["items.part-1.amount_paise"] == "recordings_disagree"
    s3 = _reask(wf, sid, s2.revision, "₹1,200", "बारह सौ")      # still differs from the last candidate
    assert s3.card.items[0].amount_paise is None
    s4 = _reask(wf, sid, s3.revision, "₹1,200", "बारह सौ")      # two consecutive recordings agree
    assert s4.card.items[0].amount_paise == 120000


def test_first_agreeing_reask_without_a_candidate_is_only_a_candidate():
    incomplete = "front brake pad saade labour do sau Somvaar shaam tak"
    wf, _, sid = service(ScriptedPrisma([T_EN, incomplete]), CardExtractor(card()))
    s1 = wf.intake(sid, b"a", "audio/webm", expected_revision=0)
    assert abstentions(s1)["items.part-1.amount_paise"] == "incomplete_number"
    s2 = _reask(wf, sid, s1.revision, "₹500", "पाँच सौ")
    assert s2.card.items[0].amount_paise is None
    assert abstentions(s2)["items.part-1.amount_paise"] == "independent_confirmation_required"
    s3 = _reask(wf, sid, s2.revision, "₹500", "पाँच सौ")
    assert s3.card.items[0].amount_paise == 50000
