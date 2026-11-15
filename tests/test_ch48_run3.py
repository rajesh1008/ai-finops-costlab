import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import ch48_run_sims3 as S
def test_all():
    assert abs(S.task_cost(2000, 300, 0, 3, 15) - 0.0105) < 1e-12 and abs(S.task_cost(2000, 300, 4000, 3, 15) - 0.0705) < 1e-12
    assert S.unmetered(240000, 0.07) == 16800.000000000004 or abs(S.unmetered(240000, 0.07) - 16800) < 1e-6
    a = S.alloc({"a": 1, "b": 3}, 100); assert a == {"a": 25.0, "b": 75.0}
    assert abs(S.cost_per_verified(9800, 4000, 0.82) - 2.9878) < 1e-3
    assert S.tier_margin(30, (10,), (4,)) == [(10, 26, 260)]
    assert S.per_thousand(180000, 600000) == 300.0
