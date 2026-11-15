import math
from costlab.commitments import *
from costlab.policy import *

def test_commit_full_period_floor():
    r = spend_commit([100, 100], 0.2, 200)
    assert math.isclose(r["paid"], 200) and math.isclose(r["shortfall"], 40) and math.isclose(r["used"], 160)
def test_commit_met():
    r = spend_commit([100, 100], 0.2, 100)
    assert math.isclose(r["paid"], 160) and r["shortfall"] == 0
def test_monthly_floor_vs_period():
    u = [100, 10]
    assert monthly_floor_commit(u, 0.0, 50)["paid"] == 150
    assert spend_commit(u, 0.0, 100)["paid"] == 110
def test_price_cut_path():
    assert price_cut_path([10, 10, 10], 2, 0.5) == [10, 5, 5]
def test_breakeven():
    assert math.isclose(breakeven_utilisation(1.67, 1.0), 1.67)
def test_provisioned_cost_spill_and_drop():
    d = [10, 30]
    r = provisioned_cost(d, 20, 1.0, 2.0)
    assert r["capacity_cost"] == 40 and r["spill_cost"] == 20 and r["total"] == 60 and r["dropped"] == 0
    r2 = provisioned_cost(d, 20, 1.0, 2.0, spillover=False)
    assert r2["dropped"] == 10 and r2["total"] == 40
def test_diurnal_peak_and_night():
    d = diurnal_demand(hours=48, seed=1, noise=0.0)
    assert d[13] > 5 * d[2]
def test_policy_allowlist_and_tags():
    rules = [Rule("m", "model_allowlist", {"allowed": ["claude-haiku-5-5"]}), Rule("t", "required_tags", {"tags": ["team", "purpose"]})]
    ok = Request("claude-haiku-5-5", 100, 50, team="a", purpose="p")
    assert decide(ok, rules).allowed
    bad = Request("claude-haiku-4-5-20251001", 100, 50, team="a", purpose="")
    d = decide(bad, rules); assert not d.allowed and set(d.denied_by) == {"m", "t"}
def test_policy_shadow_does_not_block():
    rules = [Rule("c", "price_ceiling", {"usd": 0.0001}, mode="shadow")]
    d = decide(Request("claude-haiku-5-5", 10000, 1000, team="a", purpose="p"), rules)
    assert d.allowed and d.would_deny == ["c"] and d.denied_by == []
def test_policy_unknown_model_price_ceiling_fires():
    d = decide(Request("mystery-model", 10, 10, team="a", purpose="p"), [Rule("c", "price_ceiling", {"usd": 1.0})])
    assert not d.allowed
def test_policy_legacy_exemption():
    rules = [Rule("l", "legacy_model", {"models": ["claude-haiku-4-5-20251001"], "exempt_purposes": ["calibration"]})]
    assert not decide(Request("claude-haiku-4-5-20251001", 1, 1, team="a", purpose="x"), rules).allowed
    assert decide(Request("claude-haiku-4-5-20251001", 1, 1, team="a", purpose="calibration"), rules).allowed
def test_policy_team_cap_and_replay():
    rules = [Rule("cap", "team_month_cap", {"usd": 0.001})]
    reqs = [Request("claude-haiku-5-5", 1000, 1000, team="a", purpose="p", month_spend_team=s) for s in (0.0, 0.00095, 0.002)]
    out = replay(reqs, rules)
    assert out["blocked"] == 2 and out["per_rule"]["cap"]["fires"] == 2

from costlab.fairuse import *
def test_fairuse_caps():
    c = {"runs": [1.0, 1.0, 1.0, 1.0], "plan": 3.0, "type": "normal"}
    assert apply_cap(c, "runs", 2) == (2, 2.0)
    assert apply_cap(c, "cost", 2.5) == (2, 2.0)
    assert apply_cap(c, "none", 0) == (4, 4.0)
def test_fairuse_population_types():
    cs = make_customers(300, [0.001], [0.05], seed=1)
    assert {c["type"] for c in cs} >= {"normal", "heavy_task"}
    ev = evaluate(cs, "runs", 200)
    assert ev["normal"]["n"] + ev["heavy_task"]["n"] + ev.get("automated", {"n": 0})["n"] == 300

def test_eligible_only_old_model_and_protection():
    r = eligible_only_old_model([100, 0], [0, 50], 0.1, 150)
    assert math.isclose(r["paid"], 200) and math.isclose(r["shortfall"], 60)
    p = commit_with_protection([100, 100], 0.0, 200, 2, 0.5)
    assert math.isclose(p["paid"], 150) and p["shortfall"] == 0

def test_policy_exemption_and_message():
    rules = [Rule("c", "price_ceiling", {"usd": 0.0001})]
    r = Request("claude-haiku-5-5", 10000, 1000, team="a", purpose="p")
    assert not decide(r, rules).allowed
    ex = [Exemption("c", "a", "p", "2026-12-31", "marcus")]
    assert decide(r, rules, ex, today="2026-11-11").allowed
    assert not decide(r, rules, ex, today="2027-01-01").allowed
    assert not decide(Request("claude-haiku-5-5", 10000, 1000, team="b", purpose="p"), rules, ex, today="2026-11-11").allowed
    assert "[rule c]" in refusal_message(rules[0], r) and "$" in refusal_message(rules[0], r)

def test_policy_max_tokens_ceiling():
    rules = [Rule("t", "max_tokens_ceiling", {"max_tokens": 300})]
    assert decide(Request("claude-haiku-5-5", 10, 300, team="a", purpose="p"), rules).allowed
    assert not decide(Request("claude-haiku-5-5", 10, 301, team="a", purpose="p"), rules).allowed
