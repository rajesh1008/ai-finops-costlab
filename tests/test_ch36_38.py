import math
from costlab.showback import caller_pays, amortised, uncached_list, misallocation, headcount_split, call_usd
from costlab.review import build, decompose, review_total, review_driver, EVENTS
from costlab.explainer import scenario, table, DRIVERS

ROWS = [
    {"team": "a", "billed": 0.0095, "prefix_usd": 0.0094, "own_usd": 0.0001, "uncached": 0.0076},
    {"team": "b", "billed": 0.0008, "prefix_usd": 0.0007, "own_usd": 0.0001, "uncached": 0.0076},
    {"team": "b", "billed": 0.0008, "prefix_usd": 0.0007, "own_usd": 0.0001, "uncached": 0.0076},
]

def test_caller_pays_and_amortised_sum_equal():
    assert math.isclose(sum(caller_pays(ROWS).values()), sum(amortised(ROWS).values()), rel_tol=1e-9)

def test_amortised_equalises_per_call_prefix_share():
    a = amortised(ROWS)
    assert math.isclose(a["a"], 0.0001 + 0.0108 / 3) and math.isclose(a["b"], 2 * (0.0001 + 0.0108 / 3))

def test_uncached_total():
    assert math.isclose(sum(uncached_list(ROWS).values()), 0.0228)

def test_misallocation_zero_and_range():
    t = {"a": 10, "b": 30}
    assert misallocation(t, t) == 0
    assert 0 < misallocation(headcount_split(40, {"a": 3, "b": 1}), t) < 1

def test_call_usd_cache_read_is_tenth():
    m = "claude-haiku-4-5-20251001"
    assert math.isclose(call_usd(m, 0, 0, 1000, 0) * 10, call_usd(m, 1000, 0))

def test_decompose_sums_to_change():
    rows = build()
    a = next(r for r in rows if r["product"] == "support-agent" and r["week"] == 4); b = next(r for r in rows if r["product"] == "support-agent" and r["week"] == 5)
    assert math.isclose(sum(decompose(a, b).values()), b["spend"] - a["spend"], rel_tol=1e-9)

def test_driver_review_catches_all_planted_events():
    rows = build(); flagged = {(w) for w in range(2, 14) if review_driver(rows, w)}
    assert set(EVENTS) <= flagged

def test_total_review_misses_small_event():
    rows = build(); assert review_total(rows, 5) == []

def test_scenarios_have_known_driver_and_detail_table_names_it():
    for d in DRIVERS:
        a, b = scenario("support-agent", d, 1); assert "price_index" in table("support-agent", a, b, True) and "price_index" not in table("support-agent", a, b, False)


from costlab.prestimate import est_list, est_cache_aware, flag, error_pct

def test_est_list_matches_hand_arithmetic():
    # 1,000 input and 100 output tokens on haiku-4-5 at $1 and $5 per million
    assert math.isclose(est_list(1000, 100, "claude-haiku-4-5-20251001"), (1000 * 1.0 + 100 * 5.0) / 1e6)

def test_cache_aware_one_call_is_write_priced_and_many_calls_approach_read():
    m = "claude-haiku-4-5-20251001"
    one = est_cache_aware(7500, 15, 0, m, 1); many = est_cache_aware(7500, 15, 0, m, 100000)
    assert math.isclose(one, (7500 * 1.25 + 15 * 1.0) / 1e6) and many < one / 5

def test_cache_off_equals_list():
    m = "claude-haiku-4-5-20251001"
    assert math.isclose(est_cache_aware(7500, 15, 8, m, 15, cache=False), est_list(7515, 8, m))

def test_discount_scales_estimate():
    m = "claude-haiku-5-5"
    assert math.isclose(est_list(5000, 10, m, 0.15), est_list(5000, 10, m) * 0.85)

def test_flag_and_error():
    assert flag(1.21, 1.0) and not flag(1.19, 1.0)
    assert math.isclose(error_pct(110, 100), 10.0)
