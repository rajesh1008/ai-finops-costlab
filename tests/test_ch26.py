import json, pytest
from pathlib import Path
from costlab.budgets import Authority, Blocked, Breaker, worst_case_cost
RUN = Path(__file__).resolve().parents[1] / "runs" / "budget-policy-lab-2026-11-10.json"
def test_worst_case_bound():
    assert worst_case_cost(1000, 500, 1.0, 5.0) == pytest.approx(0.0035)
def test_reserve_commit_refund_frees_headroom():
    a = Authority({"run": 0.01, "user": 0.05}); r = a.reserve(["run", "user"], 0.006); assert a.left("run") == pytest.approx(0.004)
    a.commit(r, 0.002); assert a.left("run") == pytest.approx(0.008) and a.spent["user"] == pytest.approx(0.002)
def test_blocks_before_spending_and_reports_scope():
    a = Authority({"run": 0.01, "user": 0.05}); a.reserve(["run", "user"], 0.006)
    with pytest.raises(Blocked) as e: a.reserve(["run", "user"], 0.006)
    assert e.value.scope == "run" and a.reserved["user"] == pytest.approx(0.006)
def test_all_scopes_or_none():
    a = Authority({"run": 1.0, "user": 0.001})
    with pytest.raises(Blocked): a.reserve(["run", "user"], 0.01)
    assert a.reserved["run"] == 0.0
def test_release_on_provider_failure():
    a = Authority({"run": 0.01}); r = a.reserve(["run"], 0.009); a.release(r); assert a.left("run") == pytest.approx(0.01)
def test_actuals_only_overshoots_by_one_call():
    a = Authority({"run": 0.01}, mode="actuals_only"); r = a.reserve(["run"], 0.5); a.commit(r, 0.0105)
    with pytest.raises(Blocked): a.reserve(["run"], 0.0)
    assert a.spent["run"] > a.limit["run"]
def test_advisory_never_blocks():
    a = Authority({"run": 0.001}, mode="advisory_estimate"); r = a.reserve(["run"], 5.0); a.commit(r, 5.0); a.reserve(["run"], 5.0)
def test_bad_mode():
    with pytest.raises(ValueError): Authority({"x": 1}, mode="nope")
def test_breaker_repeat_and_errors():
    b = Breaker(limit=3, errors=3); assert not b.observe("search", {"query": "a"}); assert not b.observe("search", {"query": "a"}); assert b.observe("search", {"query": "a"})
    c = Breaker(); assert not c.observe("t", {"i": 1}, True) and not c.observe("t", {"i": 2}, True) and c.observe("t", {"i": 3}, True)
    d = Breaker(); d.observe("t", {"i": 1}, True); d.observe("t", {"i": 2}, False); assert d.consec == 0
@pytest.mark.skipif(not RUN.exists(), reason="no recorded run")
def test_recorded_policy_run():
    d = json.load(open(RUN))["results"]; assert len(d) == 240 and {r["policy"] for r in d} == {"none", "hard", "aware"}
    assert all(len(r["steps"]) <= 16 for r in d)
