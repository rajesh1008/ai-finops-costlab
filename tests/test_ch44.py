import math
from costlab.killswitch import run_loop, time_to_stop, incident_cost

def always_call(hist): return 1000, 100, ("lookup", {"id": "x"}), ""
def finishes_on_third(hist): return (1000, 100, None, "done") if len(hist) == 2 else (1000, 100, ("lookup", {"id": "x"}), "")
def varying(hist): return 1000, 100, ("lookup", {"id": str(len(hist))}), ""

def test_no_control_runs_to_ceiling():
    r = run_loop(always_call, 1.0, 5.0, "none", ceiling=30)
    assert r["steps"] == 30 and r["reason"] == "ceiling" and math.isclose(r["cost"], 30 * (1000 + 500) / 1e6)

def test_breaker_stops_identical_calls_at_limit():
    r = run_loop(always_call, 1.0, 5.0, "breaker", ceiling=30, breaker_limit=3)
    assert r["steps"] == 3 and r["reason"] == "breaker" and r["stopped"]

def test_breaker_misses_varying_arguments():
    r = run_loop(varying, 1.0, 5.0, "breaker", ceiling=30)
    assert r["steps"] == 30 and r["reason"] == "ceiling"

def test_cap_stops_before_overspend():
    r = run_loop(always_call, 1.0, 5.0, "cap", ceiling=30, cap_usd=0.01)
    assert r["reason"] == "cap" and r["cost"] <= 0.01 and r["steps"] < 30

def test_finishing_run_is_not_stopped():
    for c in ("none", "breaker", "cap"):
        r = run_loop(finishes_on_third, 1.0, 5.0, c)
        assert r["reason"] == "finished" and r["steps"] == 3

def test_time_to_stop_and_incident_cost():
    assert time_to_stop(15, 25, 40, 10) == 90
    assert math.isclose(incident_cost(10.0, 5), 50.0)
    assert math.isclose(incident_cost(10.0, 20, 10), 10 * 10 / 2 + 10 * 10)
    assert math.isclose(incident_cost(10.0, 5, 10), 10 * 25 / 20)
