import math
from costlab.boardpack import classify, loaded_cost, cost_per_outcome, cost_per_correct_only, margin, decision, call_usd, list_price_per_mtok, bootstrap_ci

def test_classify():
    assert classify("FS-1013; 45 days", True) == "correct"
    assert classify("I cannot answer from the clauses supplied.", False) == "decline"
    assert classify("The window is 30 days.", False) == "wrong"

def test_loaded_cost_breakdown_adds_up():
    b = loaded_cost(["correct", "decline", "wrong", "correct"], [0.001] * 4, human=6.0, rework=4.0, platform=0.004)
    assert b["declines"] == 1 and b["wrongs"] == 1 and b["correct"] == 2
    assert math.isclose(b["total"], 0.004 + 0.016 + 12.0 + 4.0)
    assert math.isclose(cost_per_outcome(b), b["total"] / 4)

def test_wrong_costs_more_than_decline():
    d = loaded_cost(["decline"], [0.001]); w = loaded_cost(["wrong"], [0.001])
    assert w["total"] > d["total"]

def test_cost_per_correct_ignores_failures():
    b = loaded_cost(["correct", "wrong"], [0.002, 0.002])
    assert math.isclose(cost_per_correct_only(b), 0.004 / 1)

def test_no_correct_is_infinite():
    assert cost_per_correct_only(loaded_cost(["wrong"], [0.001])) == float("inf")

def test_price_per_token_is_ten_times_lower_for_newer_model():
    a = list_price_per_mtok("claude-haiku-4-5-20251001"); b = list_price_per_mtok("claude-haiku-5-5")
    assert math.isclose(a / b, 10.0)

def test_call_usd():
    assert math.isclose(call_usd("claude-haiku-4-5-20251001", 1_000_000, 0), 1.0)

def test_margin_and_decision():
    assert math.isclose(margin(0.50, 0.20), 0.6)
    assert decision(0.65, 0.64) == "scale"
    assert decision(0.65, 0.64, measured=False) == "fix"
    assert decision(0.20, 0.25) == "retire"
    assert decision(0.45, 0.50) == "fix"

def test_bootstrap_ci_brackets_mean():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0] * 10
    lo, hi = bootstrap_ci(lambda idx: sum(xs[i] for i in idx) / len(idx), len(xs), reps=500)
    assert lo < 3.0 < hi

from costlab.maturity import CAPS, ARTEFACT, STATEMENTS, level_from_evidence, score, weakest, inflation, gaming_example

def test_no_skipping_rule():
    assert level_from_evidence([True, True]) == 2
    assert level_from_evidence([True, False]) == 1
    assert level_from_evidence([False, True]) == 0

def test_score_bounds_and_arithmetic():
    assert score({c: 0 for c in CAPS}) == 0.0
    assert score({c: 2 for c in CAPS}) == 100.0
    assert score({c: 1 for c in CAPS}) == 50.0

def test_weakest_and_inflation():
    lv = {c: 1 for c in CAPS}; lv["budgets"] = 0
    assert weakest(lv) == ["budgets"]
    s = {c: 2 for c in CAPS}
    assert inflation(s, lv)["budgets"] == 2 and inflation(s, lv)["metering"] == 1

def test_statement_set_shape():
    assert len(STATEMENTS) == 48
    for c in CAPS:
        xs = [s for s in STATEMENTS if s["cap"] == c]
        assert len(xs) == 6 and {s["true"] for s in xs if s["kind"] == "plain"} == {0, 1, 2}
        assert len(ARTEFACT[c]) == 3

def test_gaming_example_raises_coverage_not_owned_share():
    g = gaming_example()
    assert g["coverage_after_dumping_into_shared"] == 1.0 and g["owned_spend_share_after"] == 0.38

from costlab.maturity import SEAT_ARTEFACT, idle_seat_cost

def test_seat_variants_have_three_levels():
    for k, v in SEAT_ARTEFACT.items():
        assert len(v) == 3 and v[0] == "" and v[1] and v[2]

def test_idle_seat_cost():
    assert math.isclose(idle_seat_cost(1000, 30, 0.38), 136800.0)
