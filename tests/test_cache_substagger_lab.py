import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import cache_substagger_lab as L
def test_committed_run_shape():
    rows = [json.loads(l) for l in L.OUT.read_text().splitlines()]
    assert len(rows) == 20 and all("error" not in u for r in rows for u in r["rows"])
    s = L.summarise(rows)
    assert s[0]["reads"] == 0 and s[0.4]["reads"] == 12 and s[0.8]["reads"] == 12
    assert s[0.1]["reads"] < s[0.2]["reads"] < s[0.4]["reads"]
