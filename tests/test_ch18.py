import json
from pathlib import Path
from costlab.cachelab import (breakeven_reads, call_cost, session_cost, keepalive_i_max, make_pairs, sweep,
                              expected_cost_per_query, cache_health, cosine, trigrams, W5, W1H)

def test_breakeven_matches_vendor_statement():
    assert breakeven_reads(W5) == 1 and breakeven_reads(W1H) == 2

def test_write_costs_more_than_uncached_read_costs_less():
    assert call_cost(20000, 300, 1.0, "write5") > call_cost(20000, 300, 1.0, "none") > call_cost(20000, 300, 1.0, "read")

def test_gap_over_ttl_evicts():
    ok, w1, r1 = session_cost([4.9] * 9, 20000, 300, 1.0, 5)
    bad, w2, r2 = session_cost([5.1] * 9, 20000, 300, 1.0, 5)
    assert (w1, r1) == (1, 9) and (w2, r2) == (10, 0) and bad > ok

def test_keepalive_horizon_for_five_minute_tier():
    assert round(keepalive_i_max(4, 1.25)) == 46

def test_semantic_cache_false_hits_exist_at_high_similarity():
    rows = sweep(make_pairs(), [0.8, 0.9])
    assert rows[0]["false_hits"] > 0 and rows[0]["hit_rate"] > rows[1]["hit_rate"]

def test_large_penalty_prefers_no_cache():
    rows = sweep(make_pairs(), [0.5, 0.8, 0.95])
    costs = [expected_cost_per_query(r, 0.0006, 5.0) for r in rows]
    assert costs[-1] == min(costs) and costs[0] > 0.0006

def test_cache_health_flags_write_without_read():
    recs = [{"cache_read_tokens": 0, "cache_write_tokens": 5000, "input_tokens": 10}] * 5
    assert cache_health(recs)["write_without_read"]
    recs2 = recs[:1] + [{"cache_read_tokens": 5000, "cache_write_tokens": 0, "input_tokens": 10}] * 4
    assert not cache_health(recs2)["write_without_read"]

def test_recorded_layout_run_shows_timestamp_breaks_cache():
    p = Path(__file__).resolve().parents[1] / "runs" / "cache-layout-2026-11-10.jsonl"
    by = {}
    for l in p.read_text().splitlines():
        r = json.loads(l); by.setdefault(r["feature"], []).append(r)
    assert sum(r["cache_read_tokens"] for r in by["layout-B"]) > 30000
    assert sum(r["cache_read_tokens"] for r in by["layout-C"]) == 0
    assert sum(r["estimated_cost_usd"] for r in by["layout-C"]) > sum(r["estimated_cost_usd"] for r in by["layout-A"])
