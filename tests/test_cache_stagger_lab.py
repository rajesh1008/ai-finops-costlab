import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import cache_stagger_lab as L
def test_summarise_counts():
    rows = [{"gap": 1, "rep": 0, "rows": [{"cost": 0.01, "cr": 0, "cw": 5000, "start_s": 0, "end_s": 1}, {"cost": 0.001, "cr": 5000, "cw": 0, "start_s": 1, "end_s": 2}]}]
    s = L.summarise(rows)[1]
    assert s["calls"] == 2 and s["reads"] == 1 and s["writes"] == 1
def test_committed_run_shape():
    rows = [json.loads(l) for l in L.OUT.read_text().splitlines()]
    assert len(rows) == 15 and all("error" not in u for r in rows for u in r["rows"])
    s = L.summarise(rows)
    assert s[0]["reads"] == 0 and all(s[g]["reads"] == 9 for g in (1, 2, 3, 5))
