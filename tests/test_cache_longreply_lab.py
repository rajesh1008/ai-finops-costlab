import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import cache_longreply_lab as L
def test_committed_run_shape():
    rows = [json.loads(l) for l in L.OUT.read_text().splitlines()]
    assert len(rows) == 12 and all("error" not in u for r in rows for u in r["rows"])
    s = L.summarise(rows)
    assert all(s[g]["reads"] == 9 and s[g]["writes"] == 3 for g in (0.4, 2, 5, 10))
    assert all(s[g]["mean_latency_s"] > 3 for g in s)
