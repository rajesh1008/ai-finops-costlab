import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import ch43_run_sims as s

def test_ladder_reach_zero_with_terminal_rung():
    exp, reach = s.ladder_expected([0.97, 0.90, 1.0], [0.012, 0.003, 0.0])
    assert reach == 0.0 and abs(exp - (0.012 + 0.03 * 0.003)) < 1e-12

def test_shadow_cache_cheaper():
    plain, cached = s.shadow_cache(28000, 6000, 1.0)
    assert cached < plain and abs(plain - 168.0) < 1e-9

def test_commit_utilisation():
    p, _ = s.commit_breakeven(1.0, 0.2, 0.8)
    assert abs(p - 1.0) < 1e-12

def test_team_breakeven():
    assert s.team_breakeven(180000, 0.05, 3e6) == (3_600_000, 150000.0)
