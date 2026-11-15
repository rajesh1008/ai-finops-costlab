import json, math, pytest
from pathlib import Path
from costlab.smallmodels import make_tickets, make_tickets_hard, NB, accuracy, breakeven_requests, breakeven_months, utilisation_cost_per_1k, PRECEDENCE
RUNS = Path(__file__).resolve().parents[1] / "runs"
def test_tickets_balanced_and_seeded():
    a, b = make_tickets(), make_tickets()
    assert a == b and len(a) == 600
    assert {t["label"] for t in a} == set(PRECEDENCE)
def test_hard_gold_follows_precedence():
    T = make_tickets_hard()
    assert any(", and also" in t["text"] for t in T)
def test_nb_learns_easy_task():
    T = make_tickets(); nb = NB().fit([t["text"] for t in T[:400]], [t["label"] for t in T[:400]])
    assert accuracy([nb.predict(t["text"]) for t in T[400:]], [t["label"] for t in T[400:]]) > 0.95
def test_breakeven_forms():
    assert breakeven_requests(6000, 0.0002, 0.0001) == pytest.approx(60_000_000)
    assert breakeven_requests(6000, 0.0001, 0.0002) == math.inf
    assert breakeven_months(5000, 0, 4, 400) == pytest.approx(12.5)
def test_utilisation_penalty():
    assert utilisation_cost_per_1k(2.5, 50, 0.1) == pytest.approx(10 * utilisation_cost_per_1k(2.5, 50, 1.0))
@pytest.mark.skipif(not (RUNS / "small-model-lab-hard-2026-11-10.json").exists(), reason="no recorded run")
def test_recorded_hard_run():
    d = json.load(open(RUNS / "small-model-lab-hard-2026-11-10.json"))
    teach = [r for r in d["results"] if r["arm"] == "teacher"]
    assert len(teach) == 600
