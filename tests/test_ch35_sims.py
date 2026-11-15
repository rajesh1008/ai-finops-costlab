import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import ch35_run_sims as c

def test_sessions_fall_with_longer_limit():
    n, out = c.ch07()
    assert n == 1591 and out[10] > out[30] > out[60] > out[120]

def test_hybrid_break_even():
    rows = c.ch15()
    assert rows[2][0] == 7843 and abs(rows[2][1] - rows[2][2]) <= 2

def test_failover_premium_small():
    calls, base, writes, extra = c.ch31()
    assert writes == 144 and extra < 1 and base > 100

def test_month_length():
    a, b, rate, headline = c.ch43()
    assert rate > 0 and headline < 0

def test_commit_loses_when_usage_low():
    d = c.ch30()
    assert d["pool"] < d["list"] and d["used"] == 539
