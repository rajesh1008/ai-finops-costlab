import pytest
from costlab.retries import ccrm_success, clean_success, fit_p1, simulate, loop_signals, expected_attempts, cost_per_success
def test_iid_recovery():
    assert ccrm_success(0.6, 0.6, 3) == pytest.approx(clean_success(0.6, 3))
def test_paper_fit_roundtrip():
    p1 = fit_p1(0.761, 0.812, 3)
    assert p1 == pytest.approx(0.113, abs=0.001)
    assert ccrm_success(0.761, p1, 3) == pytest.approx(0.812)
def test_formula_matches_simulation():
    assert simulate(0.7, 0.2, 3, n=40000) == pytest.approx(ccrm_success(0.7, 0.2, 3), abs=0.01)
def test_loop_signals():
    assert loop_signals(list("AAAB"))["repeat_run"] == 3
    assert loop_signals(list("ABAB"))["abab"] and not loop_signals(list("ABCD"))["abab"]
def test_cost_per_success_monotone():
    assert cost_per_success(0.5, 0.5, 3, 1, 1) < cost_per_success(0.5, 0.2, 3, 1, 1)
