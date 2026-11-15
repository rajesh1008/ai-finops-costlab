import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import fold_rules_lab as f
RUN = pathlib.Path(__file__).resolve().parents[1] / "runs" / "fold-rules-lab-2026-11-13.jsonl"
def rows(): return [json.loads(l) for l in RUN.read_text().splitlines()]
def test_shape():
    r = rows(); assert len(r) == 16 and all("error" not in x for x in r)
    assert sum(len(x["rows"]) for x in r) == 216
def test_grade_parses_formats():
    gold = [g for _, g in f.questions(0)]
    assert all(f.grade("1: Yes\n2: no.\n3. yes\n4: No\n5: $850\n6: 24 hours\n7: $40\n8: USD", gold))
    assert not any(f.grade("nothing useful", gold))
    assert f.grade("5: 8500", gold)[4] is False
def test_gold_answers():
    assert [g for _, g in f.questions(0)] == ["yes", "no", "yes", "no", "850", "24", "40", "usd"]
    assert f.questions(7)[4][1] == "780"
def test_costs_and_accuracy():
    g = lambda m: [x for x in rows() if x["mode"] == m]
    c = lambda m: sum((t["in"] * 1.0 + t["out"] * 5.0) / 1e6 for x in g(m) for t in x["rows"]) / 8
    assert round(c("plain"), 5) == 0.00981 and round(c("folded"), 5) == 0.0105
    assert c("folded") > c("plain")
    assert sum(x["correct"] for x in g("plain")) == 55 and sum(x["correct"] for x in g("folded")) == 45
    assert all(t["stop"] != "max_tokens" for x in g("folded") for t in x["rows"] if t["turn"] == "summary")
