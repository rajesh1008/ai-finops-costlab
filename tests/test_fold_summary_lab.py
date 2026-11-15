import json, pathlib
RUN = pathlib.Path(__file__).resolve().parents[1] / "runs" / "fold-summary-lab-2026-11-13.jsonl"
def rows(): return [json.loads(l) for l in RUN.read_text().splitlines()]
def test_shape():
    r = rows(); assert len(r) == 10 and all("error" not in x for x in r)
    assert sum(len(x["rows"]) for x in r) == 125
def test_folded_turn12_input_smaller():
    for s in range(5):
        p = next(x for x in rows() if x["session"] == s and x["mode"] == "plain"); f = next(x for x in rows() if x["session"] == s and x["mode"] == "folded")
        assert [t for t in f["rows"] if t["turn"] == 12][0]["in"] < [t for t in p["rows"] if t["turn"] == 12][0]["in"]
def test_cost_means():
    g = lambda m: [x for x in rows() if x["mode"] == m]
    c = lambda m: sum((t["in"] * 1.0 + t["out"] * 5.0) / 1e6 for x in g(m) for t in x["rows"]) / 5
    assert round(c("plain"), 5) == 0.01178 and round(c("folded"), 5) == 0.01048
    assert 1 - c("folded") / c("plain") > 0.10
