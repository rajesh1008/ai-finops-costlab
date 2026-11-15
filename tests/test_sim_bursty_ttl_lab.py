import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import sim_bursty_ttl_lab as B

def test_all_burst_traffic_favours_five_minute_ttl():
    r = [x for x in B.run() if x["idle_share"] == 0.0][0]
    assert r["cheapest"] == "5m" and r["5m"] < r["1h"] < r["none"]

def test_deterministic():
    assert B.run() == B.run()

def test_no_cache_never_cheapest_at_low_idle_share():
    assert all(x["cheapest"] != "none" for x in B.run() if x["idle_share"] <= 0.1)
