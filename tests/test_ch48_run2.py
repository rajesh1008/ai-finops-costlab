import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import ch48_run_sims2 as S
def test_all():
    assert S.store_gb(2_000_000, 1200, 400) == 960.0
    assert abs(S.store_cost(960, 0.023) - 22.08) < 1e-9
    assert abs(S.false_alerts_per_year(3) - 0.5 * 0.0026998 * 365 * 2 / 2) < 0.02
    assert abs(S.cascade_cost(0.002, 0.02, 0.7) - 0.008) < 1e-12 and abs(S.cascade_breakeven_accept(0.002, 0.02) - 0.1) < 1e-12
    assert abs(S.diet_saving(1800, 3.0, 400000) - 2160) < 1e-9
    assert S.blended_batch(60000, 0.3, 0.5) == 51000
    assert abs(S.expected_attempts(0.5, 4) - 1.875) < 1e-12 and S.expected_attempts(1.0, 4) == 4
    assert S.agent_input_tokens(10, 3000, 1500) == 30000 + 1500 * 45
    assert abs(S.ladder_cost((0.7, 0.2, 0.1), (0.02, 0.004, 0.0005)) - 0.01485) < 1e-9
