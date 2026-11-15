import json, pytest
from pathlib import Path
from costlab.serving import batch_cost, effective_self_host_per_mtok, breakeven_utilisation, units_needed, committed_capacity_cost
RUN = Path(__file__).resolve().parents[1] / "runs" / "batch-lab-2026-11-10.json"
def test_batch_cost_blend():
    assert batch_cost(40000, 0.3) == pytest.approx(34000)
    assert batch_cost(100, 0) == 100 and batch_cost(100, 1) == 50
def test_underutilisation_penalty_is_one_over_u():
    full = effective_self_host_per_mtok(3.49, 1000, 1.0)
    assert effective_self_host_per_mtok(3.49, 1000, 0.25) == pytest.approx(4 * full)
def test_breakeven_matches_price():
    u = breakeven_utilisation(3.49, 1000, 3.5)
    assert effective_self_host_per_mtok(3.49, 1000, u) == pytest.approx(3.5)
def test_units_needed():
    assert units_needed(3500, 1000, 0.7) == 5
    assert committed_capacity_cost(5, 3.49) == pytest.approx(5 * 3.49 * 730)
@pytest.mark.skipif(not RUN.exists(), reason="recorded batch run absent")
def test_recorded_batch_shape():
    d = json.load(open(RUN))
    assert d["batches"]["billing"]["request_counts"]["succeeded"] == 30
    h = [r for r in d["batches"]["handbook"]["rows"] if "in" in r]
    assert all(r["cr"] + r["cw"] == 7545 for r in h)
