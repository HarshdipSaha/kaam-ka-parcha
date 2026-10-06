from parcha.lab.reask_bench import ReaskCase, amount_pool, build_cases, score, summarize


def test_pool_is_deterministic_whole_rupees_and_includes_the_estimate_amounts(tmp_path):
    first, second = amount_pool(60), amount_pool(60)
    assert first == second and len(first) == 60
    assert all(p % 100 == 0 and 0 < p <= 10_000_000 for p in first)
    assert 65000 in amount_pool(60)  # an amount from the v2 estimate manifest


def test_cases_speak_one_amount_the_way_a_mechanic_would():
    cases = build_cases([45000, 25000])
    assert [c.expected_paise for c in cases] == [25000, 45000]
    assert cases[0].utterance.startswith("ढाई सौ")


def test_score_classifies_recovered_wrong_and_abstained():
    case = ReaskCase("r1", 45000, "साढ़े चार सौ")
    assert score(case, "साढ़े चार सौ", "₹450")["outcome"] == "recovered"
    assert score(case, "साढ़े पाँच सौ", "₹550")["outcome"] == "wrong_accepted"
    abstained = score(case, "साढ़े चार सौ", "₹350")
    assert abstained["outcome"] == "abstain" and abstained["reason"] == "crosscheck_disagreement"


def test_summary_counts_by_condition_and_overall():
    rows = [
        {"condition": "g711|clean", "outcome": "recovered", "reason": None},
        {"condition": "g711|clean", "outcome": "abstain", "reason": "crosscheck_disagreement"},
        {"condition": "control", "outcome": "recovered", "reason": None},
    ]
    summary = summarize(rows)
    assert summary["ALL"]["n"] == 3 and summary["ALL"]["recovered"] == 2
    assert summary["g711|clean"]["abstain_reasons"] == {"crosscheck_disagreement": 1}
    assert summary["control"]["wrong_accepted"] == 0


def test_paired_rule_settles_only_when_two_recordings_agree_and_counts_wrong_settles():
    from parcha.lab.reask_bench import paired_outcomes

    def row(voice, paise, expected=45000, case="r1", cond="control"):
        return {"case_id": case, "condition": cond, "voice": voice, "paise": paise, "expected_paise": expected}

    good = paired_outcomes([row("Roopesh", 45000), row("Vikrant", 45000)])["ALL"]
    assert good["settled"] == 2 and good["settled_wrong"] == 0
    split = paired_outcomes([row("Roopesh", 45000), row("Vikrant", 1200)])["ALL"]
    assert split["needs_another"] == 2 and split["settled"] == 0
    wrong = paired_outcomes([row("Roopesh", 43800), row("Vikrant", 43800)])["ALL"]
    assert wrong["settled_wrong"] == 2
    none = paired_outcomes([row("Roopesh", None), row("Vikrant", 45000)])["ALL"]
    assert none["needs_another"] == 2
