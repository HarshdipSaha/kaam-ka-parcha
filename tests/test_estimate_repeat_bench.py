from parcha.lab.estimate_repeat_bench import (build_cases, paired_estimates, replay_pair, summarize_pairs)


def rows_for(case, *, first_v, first_t, second_v, second_t, condition="control"):
    base = {"case_id": case.case_id, "condition": condition, "utterance": case.utterance,
            "expected_paise": case.expected}
    return [{**base, "voice": "Roopesh", "verbatim": first_v, "transcribe": first_t},
            {**base, "voice": "Vikrant", "verbatim": second_v, "transcribe": second_t}]


def test_cases_cover_two_to_four_items_with_unique_labels_and_valid_amounts():
    cases = build_cases(30)
    assert {len(c.items) for c in cases} == {2, 3, 4}
    for c in cases:
        assert len({label for label, _, _ in c.items}) == len(c.items)
        assert all(p > 0 and p % 100 == 0 for p in c.expected)
        assert c.utterance.count(",") == len(c.items) - 1


def test_held_out_cases_differ_from_the_main_run():
    assert [c.utterance for c in build_cases(20)] != [c.utterance for c in build_cases(20, held_out=True)]


def test_two_agreeing_recordings_settle_every_item():
    good_v, good_t = "ब्रेक पैड साढ़े चार सौ, लेबर दो सौ", "ब्रेक पैड ₹450, लेबर ₹200"
    # build a synthetic 2-item case matching the transcripts
    from parcha.lab.estimate_repeat_bench import EstimateCase
    case = EstimateCase("e900", (("ब्रेक पैड", "part", 45000), ("लेबर", "labour", 20000)), good_v)
    result = replay_pair(case, {"verbatim": good_v, "transcribe": good_t}, {"verbatim": good_v, "transcribe": good_t})
    assert result["all_settled"] and result["settled_wrong"] == 0 and result["recordings"] == 2


def test_a_misheard_amount_stays_unsettled_not_wrong():
    from parcha.lab.estimate_repeat_bench import EstimateCase
    case = EstimateCase("e901", (("ब्रेक पैड", "part", 45000), ("लेबर", "labour", 20000)), "x")
    first = {"verbatim": "ब्रेक पैड साढ़े चार सौ, लेबर दो सौ", "transcribe": "ब्रेक पैड ₹450, लेबर ₹200"}
    second = {"verbatim": "ब्रेक पैड साढ़े चार सौ, लेबर तीन सौ", "transcribe": "ब्रेक पैड ₹450, लेबर ₹300"}
    result = replay_pair(case, first, second)
    assert result["settled_right"] == 1 and result["settled_wrong"] == 0 and not result["all_settled"]


def test_summary_reports_rates_wilson_bound_and_two_recordings():
    from parcha.lab.estimate_repeat_bench import EstimateCase
    v, t = "ब्रेक पैड साढ़े चार सौ, लेबर दो सौ", "ब्रेक पैड ₹450, लेबर ₹200"
    case = EstimateCase("e902", (("ब्रेक पैड", "part", 45000), ("लेबर", "labour", 20000)), v)
    rows = rows_for(case, first_v=v, first_t=t, second_v=v, second_t=t)
    summary = summarize_pairs(paired_estimates(rows, {case.case_id: case}))
    assert summary["ALL"]["estimates"] == 2           # both voice directions
    assert summary["ALL"]["items_wrong_settled"] == 0
    assert summary["ALL"]["recordings_per_estimate"] == 2
    assert summary["control"]["estimates_fully_settled_rate"] == 1.0
