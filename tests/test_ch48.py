from costlab.canary import count_matches_usage, counts_deterministic, cost_identity, cache_expected, summarise
def test_count_and_determinism(): assert count_matches_usage(100, 100) and not count_matches_usage(100, 103) and count_matches_usage(100, 103, 3) and counts_deterministic(5, 5)
def test_cost_identity(): assert cost_identity(1000, 100, 1.0, 5.0, 0.0015) and not cost_identity(1000, 100, 1.0, 5.0, 0.002)
def test_cache_expected():
    assert cache_expected(3000, 4096, 0) and not cache_expected(3000, 4096, 2900) and cache_expected(5000, 4096, 4900) and not cache_expected(5000, 4096, 0)
def test_summarise(): assert summarise([{"check": "a", "ok": True}, {"check": "a", "ok": False}]) == {"a": (1, 2)}
