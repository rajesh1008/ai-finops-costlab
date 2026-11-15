import math
from costlab.stackmath import arm_cost, per_1000, saving, naive_stack, additive_stack, reprice, plan_revenue, gross_margin
P = {"input": 1.0, "output": 5.0, "cache_read": 0.1, "cache_write": 1.25}

def test_arm_cost_uses_every_usage_field():
    rows = [{"in": 1000, "out": 100, "cr": 8000, "cw": 2000}]
    assert math.isclose(arm_cost(rows, P), (1000 * 1 + 100 * 5 + 8000 * 0.1 + 2000 * 1.25) / 1e6)

def test_per_1000_and_saving():
    assert math.isclose(per_1000(0.5, 100), 5.0) and per_1000(1, 0) == 0.0
    assert math.isclose(saving(10, 4), 0.6) and saving(0, 1) == 0.0

def test_naive_stack_never_exceeds_one_and_additive_can():
    assert naive_stack([0.87, 0.958]) < 1.0 and additive_stack([0.87, 0.958]) > 1.0
    assert math.isclose(naive_stack([0.5, 0.5]), 0.75)

def test_reprice():
    assert math.isclose(reprice(3.0, 0.5), 6.0)
    try: reprice(3.0, 1.0); assert False
    except ValueError: pass

def test_plan_revenue_composed_numbers():
    p = plan_revenue(2000, 26.0, 10, 3.0, 0.85, 5.1, 24.8)
    assert round(p["outcomes"]) == 16110 and math.isclose(p["overage_outcomes"], 4440.0)
    assert math.isclose(p["revenue"], 52000 + 4440 * 3.0)

def test_gross_margin():
    assert math.isclose(gross_margin(100, 40), 0.6) and gross_margin(0, 1) == 0.0
