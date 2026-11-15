import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import cpo_repeats_summary as s
def test_cpc_counts_only_correct():
    rows = [{"model": "claude-haiku-4-5-20251001", "in": 1_000_000, "out": 0, "correct": True}, {"model": "claude-haiku-4-5-20251001", "in": 1_000_000, "out": 0, "correct": False}]
    assert abs(s.cpc(rows) - 2.0) < 1e-9
def test_cpc_no_correct_is_inf():
    rows = [{"model": "claude-haiku-4-5-20251001", "in": 10, "out": 10, "correct": False}]
    assert s.cpc(rows) == float("inf")
def test_interval_ordered():
    by = {k: [{"model": "claude-haiku-4-5-20251001", "in": 100, "out": 100, "correct": k % 2 == 0}] for k in range(10)}
    lo, md, hi = s.interval(by, 10, reps=200)
    assert lo <= md <= hi
