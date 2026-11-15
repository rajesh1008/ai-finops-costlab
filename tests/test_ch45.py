import math
from costlab.forecastvar import cv, bootstrap_total_interval, point_total, normal_total_interval, coverage, volume_error_decomposition, call_cost

def test_cv_zero_for_constant(): assert cv([2, 2, 2]) == 0.0
def test_call_cost(): assert math.isclose(call_cost(1000, 200, 1.0, 5.0), 0.002)
def test_bootstrap_interval_brackets_point():
    h = [1, 2, 3, 4, 5.0] * 4; lo, hi = bootstrap_total_interval(h, 100)
    assert lo < point_total(h, 100) < hi
def test_constant_history_gives_zero_width():
    lo, hi = bootstrap_total_interval([1.0] * 10, 50); assert lo == hi == 50.0
    lo, hi = normal_total_interval([1.0] * 10, 50); assert lo == hi == 50.0
def test_volume_rate_sum_exact():
    v, r, t = volume_error_decomposition(100, 130, 0.5, 0.4); assert math.isclose(t, 130 * 0.4 - 100 * 0.5)
def test_coverage_in_unit_range():
    import random
    rng = random.Random(0); pop = [rng.random() for _ in range(200)]
    c, w = coverage([pop], 20, 50, bootstrap_total_interval, trials=100); assert 0 <= c <= 1 and w > 0
