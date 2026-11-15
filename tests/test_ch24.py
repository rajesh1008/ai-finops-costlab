import json, pytest
from pathlib import Path
from costlab.agentrun import step_cost, run_cost, quantile, spread, repeat_spread, input_share_of_steps, cost_if_capped
RUNS = Path(__file__).resolve().parents[1] / "runs"
def test_step_and_run_cost():
    assert step_cost(1_000_000, 1_000_000, 1.0, 5.0) == pytest.approx(6.0)
    assert run_cost([{"in": 1000, "out": 100}, {"in": 1500, "out": 50}], 1.0, 5.0) == pytest.approx(2500 / 1e6 + 150 * 5 / 1e6)
def test_quantile_and_spread():
    assert quantile([1, 2, 3, 4, 5], .5) == 3 and quantile([1, 2], .5) == 1.5
    s = spread([1, 1, 1, 10]); assert s["max_over_min"] == 10 and s["mean_over_median"] == pytest.approx(13 / 4)
    with pytest.raises(ValueError): quantile([], .5)
def test_repeat_spread_ignores_singletons():
    assert repeat_spread({"a": [1, 2], "b": [5], "c": [3, 3, 6]}) == [2, 2]
def test_reread_share_grows_with_steps():
    two = [{"in": 100, "out": 20}, {"in": 150, "out": 20}]; five = [{"in": 100 + 50 * i, "out": 20} for i in range(5)]
    assert input_share_of_steps(five) > input_share_of_steps(two) > 0 and input_share_of_steps([{"in": 5, "out": 1}]) == 0
def test_cost_if_capped():
    spent, cut = cost_if_capped([1, 2, 10], 3); assert spent == 6 and cut == 1
@pytest.mark.parametrize("name,n", [("agent-run-lab-2026-11-10.json", 120), ("agent-run-lab-multi-2026-11-10.json", 120), ("agent-run-lab-chain-2026-11-10.json", 120)])
def test_recorded_runs(name, n):
    f = RUNS / name
    if not f.exists(): pytest.skip("no recorded run")
    d = json.load(open(f)); assert len(d["results"]) == n and all(r["steps"] for r in d["results"] if r["status"] != "api_error")
def test_chain_cost_grows_with_steps():
    f = RUNS / "agent-run-lab-chain-2026-11-10.json"
    if not f.exists(): pytest.skip("no recorded run")
    res = json.load(open(f))["results"]
    c = lambda k: [run_cost(r["steps"], 1.0, 5.0) for r in res if len(r["steps"]) == k]
    assert sum(c(10)) / len(c(10)) > 3 * sum(c(3)) / len(c(3))
