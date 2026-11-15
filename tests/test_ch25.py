import json, pytest
from pathlib import Path
from costlab.multiagent import break_even_fraction, feasible, pipeline_cost_ratio, role_costs, overhead_share, parallel_latency_gain
RUN = Path(__file__).resolve().parents[1] / "runs" / "multi-agent-lab-2026-11-10.json"
@pytest.mark.parametrize("alpha,r,exp", [(1.5, .5, .67), (2.0, .5, 1.0), (1.5, .33, .50), (2.0, .2, .63), (3.0, .2, .83), (4.0, .025, .77), (2.0, .025, .51)])
def test_matches_paper_table_1(alpha, r, exp):
    got = break_even_fraction(alpha, r)
    assert got == pytest.approx(exp, abs=0.011)
def test_infeasible_when_alpha_over_one_over_r():
    assert break_even_fraction(2.5, .5) is None and not feasible(2.5, .5) and feasible(1.9, .5)
def test_cost_ratio_is_one_at_threshold():
    a, r = 3.0, .2; f = break_even_fraction(a, r); assert pipeline_cost_ratio(a, f, r) == pytest.approx(1.0)
def test_role_costs_and_overhead():
    rc = role_costs({"supervisor_plan": [{"in": 1000, "out": 100}], "worker0": [{"in": 3000, "out": 100}]}, 1.0, 5.0)
    assert rc["worker0"] == pytest.approx(0.0035) and overhead_share(rc) == pytest.approx(0.0015 / 0.005)
def test_parallel_gain():
    assert parallel_latency_gain([2, 2, 2]) == 3 and parallel_latency_gain([5]) == 1
def test_input_validation():
    with pytest.raises(ValueError): break_even_fraction(2, 1.5)
@pytest.mark.skipif(not RUN.exists(), reason="no recorded run")
def test_recorded_run_pairs():
    d = json.load(open(RUN))["results"]; assert len(d) == 120 and {r["arm"] for r in d} == {"S", "M"}
    S = sum(len(v) for r in d if r["arm"] == "S" for v in r["roles"].values()); M = sum(len(v) for r in d if r["arm"] == "M" for v in r["roles"].values()); assert M > 2.5 * S
