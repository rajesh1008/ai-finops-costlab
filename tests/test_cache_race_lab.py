import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import cache_race_lab as L
def test_cost_ttl_multipliers():
    assert abs(L.cost({"in": 0, "out": 0, "cr": 0, "cw": 1_000_000}, "5m") - 1.25) < 1e-9
    assert abs(L.cost({"in": 0, "out": 0, "cr": 0, "cw": 1_000_000}, "1h") - 2.00) < 1e-9
def test_summarise_counts():
    rows = [{"arm": "burst8", "rep": 0, "rows": [{"cost": 0.01, "cr": 0, "cw": 5000}] * 2 + [{"cost": 0.001, "cr": 5000, "cw": 0}]}]
    s = L.summarise(rows)["burst8"]
    assert s["calls"] == 3 and s["calls_with_write"] == 2 and s["calls_with_read"] == 1
def test_committed_run_shape():
    rows = [json.loads(l) for l in L.OUT.read_text().splitlines()]
    assert len(rows) == 9 and all("error" not in r for r in rows)
    s = L.summarise(rows)
    assert s["burst8"]["calls"] == 24 and s["primed8"]["calls"] == 24 and s["ttl1h_600"]["calls"] == 6
