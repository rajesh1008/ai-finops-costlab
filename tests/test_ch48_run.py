import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import ch48_run_sims as S
def test_all():
    assert S.breakeven_success(1.2, 4.0) == 0.3
    assert abs(S.seq_calls(0.5, 3) - 1.75) < 1e-9 and abs(S.seq_success(0.5, 3) - 0.875) < 1e-9
    assert abs(S.policy_net(420, 3.1, 35, 14) - 812) < 1e-6
    assert S.finetune_payback_months(18000, 2400, 9000, 600) == 18000 / 6000
    assert S.finetune_payback_months(18000, 9000, 9000, 600) == math.inf
    assert S.sample_size(0.85, 0.05) > S.sample_size(0.85, 0.10)
    assert abs(S.commit_effective_discount(800000, 0.2, 800000) - (1 - 800000 / 800000)) < 1e-9
    assert S.fte_payback(190000, 1e6, 0.05) == 3.8
    assert S.tco(260000, 140000, 90000, 40000) == (540000, 310000)
    assert S.delay_cost(1800, 9, 2) == 19800
