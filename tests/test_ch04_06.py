from datetime import date
import pytest
from costlab.outcome import OutcomeContract, Window, three_denominators, cost_per
from costlab.reconcile import reconcile
from costlab.hierarchy import Assignment, owner_on, latest_owner, check_gaps_and_overlaps
from costlab.tiers import tiered_cost
from costlab.tags import Credential, resolve_tags


def test_contract_missing_fields():
    c = OutcomeContract(product="x", outcome_statement="s")
    assert "owner" in c.missing() and not c.is_valid()


def test_zero_denominator_refused():
    with pytest.raises(ValueError):
        cost_per(100.0, 0)


def test_denominators_order():
    r = three_denominators(Window(1000, emitted=100, accepted=80, benefited=60))
    assert r["per_emitted"] < r["per_accepted"] < r["per_benefited"]


def test_reconcile_flags_line_even_when_total_is_inside_tolerance():
    out = reconcile({"a": 97.0, "b": 100.0}, {"a": 100.0, "b": 100.0}, 0.02)
    assert [ok for _, ok in out] == [False, True]
    assert abs(sum(v.gap_usd for v, _ in out) / 200.0) < 0.02


def test_hierarchy_as_of_and_overlap():
    t = [Assignment("p", "A", date(2026, 1, 1), date(2026, 10, 16)), Assignment("p", "B", date(2026, 10, 16))]
    assert owner_on(t, "p", date(2026, 10, 15)) == "A" and owner_on(t, "p", date(2026, 10, 16)) == "B"
    assert latest_owner(t, "p") == "B"
    bad = t + [Assignment("p", "C", date(2026, 10, 10), date(2026, 10, 20))]
    assert check_gaps_and_overlaps(bad, "p", date(2026, 10, 9), date(2026, 10, 11))


def test_tier_whole_vs_excess():
    kw = dict(threshold=200_000, low_in=3.0, low_out=15.0, high_in=6.0, high_out=22.5)
    assert tiered_cost(200_500, 600, whole_request=True, **kw) > 1.9 * tiered_cost(200_000, 600, **kw)
    assert tiered_cost(200_500, 600, whole_request=False, **kw) < 1.02 * tiered_cost(200_000, 600, **kw)


def test_tags_reject_caller_product():
    reg = {"k": Credential("k", "p", "t", "production")}
    with pytest.raises(ValueError):
        resolve_tags("k", {"product": "other"}, reg)
    assert resolve_tags("zz", {}, reg)["product"] == "unregistered"
