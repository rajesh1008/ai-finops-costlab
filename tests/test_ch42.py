import math
from costlab.firstmeter import make_requests, parse_label, score, confusion, coverage_trajectory, residual, first_honest_number, NAMES

def test_requests_balanced_and_deterministic():
    a = make_requests(); b = make_requests()
    assert a == b and len(a) == 160
    assert all(sum(r["feature"] == f for r in a) == 40 for f in NAMES)

def test_parse_label_variants():
    assert parse_label('{"feature": "sql_helper"}') == "sql_helper"
    assert parse_label("I think it is report_summariser") == "report_summariser"
    assert parse_label('{"feature": "unknown"}') == "unknown"
    assert parse_label("???") == "unparsed"
    assert parse_label('{"feature": "banana"}') == "unparsed"

def test_score_weights_by_tokens():
    rows = [{"feature": "a", "label": "a", "tokens": 100}, {"feature": "a", "label": "b", "tokens": 900}, {"feature": "b", "label": "unknown", "tokens": 1000}]
    s = score(rows, 1.0)
    assert s["right"] == 1 and math.isclose(s["misattributed"], 900) and math.isclose(s["unknown"], 1000) and math.isclose(s["wrong_share"], 0.45)

def test_confusion_counts():
    c = confusion([{"feature": "a", "label": "b", "tokens": 1}] * 3)
    assert c[("a", "b")] == 3

def test_coverage_monotone_and_capped():
    t = coverage_trajectory()
    assert len(t) == 13 and all(y > x for x, y in zip(t, t[1:])) and t[-1] < 0.93

def test_residual_and_first_number():
    r = residual(100.0, 90.0); assert math.isclose(r["residual_share"], 0.1)
    f = first_honest_number(1000.0, 600.0, 100)
    assert math.isclose(f["cost_per_outcome"], 6.0) and math.isclose(f["upper_bound_per_outcome"], 10.0) and math.isclose(f["untagged_usd"], 400.0)
    assert first_honest_number(1.0, 1.0, 0)["cost_per_outcome"] == float("inf")
