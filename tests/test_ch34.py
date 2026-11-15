import math
from costlab.evidence import *

def recs(n=10):
    return [{"id": i, "model": "claude-haiku-4-5-20251001", "in": 1000, "out": 100, "day": i % 3, "team": "t", "feature": "f", "env": "prod"} for i in range(n)]

def test_chain_ok_and_head():
    c, head = chain(recs()); assert verify_chain(c, head) == (True, None, "ok")
def test_chain_detects_edit_and_truncation():
    c, head = chain(recs()); c[4]["in"] = 999
    assert verify_chain(c)[:2] == (False, 4)
    c2, head2 = chain(recs()); assert verify_chain(c2[:-1])[0] is True and verify_chain(c2[:-1], head2)[0] is False
def test_recompute_matches_price():
    r = recs(1); assert math.isclose(recompute(r)[0], 1000 / 1e6 * 1.0 + 100 / 1e6 * 5.0)
def test_unknown_model_is_none_not_zero():
    r = [{"model": "nope", "in": 1, "out": 1, "day": 0}]; assert recompute(r) == [None]
def test_coverage():
    r = recs(4); r[0]["team"] = ""; cv = coverage(r); assert math.isclose(cv["coverage"], 0.75)
def test_reconcile_clean_and_duplicate():
    r = recs(300); inv = make_invoice(r); assert all(x["ok"] for x in reconcile_lines(meter_lines(r), inv))
    inv2 = make_invoice(r, dup_n=60); assert not all(x["ok"] for x in reconcile_lines(meter_lines(r), inv2))
def test_credit_line_only_on_invoice():
    r = recs(30); inv = make_invoice(r, credit_usd=1.0); bad = [x for x in reconcile_lines(meter_lines(r), inv) if not x["ok"]]
    assert len(bad) == 1 and bad[0]["key"][0] == "credit"
def test_zero_failure_sample():
    assert zero_failure_sample(0.05) == 59 and zero_failure_sample(0.02) == 149
def test_manifest_verify():
    f = {"a": b"x", "b": b"y"}; m = manifest(f, "h", "2026-11-11", "p", ""); assert verify_manifest(m, f) == []
    assert verify_manifest(m, {"a": b"x", "b": b"z"}) == [("b", "changed")]
