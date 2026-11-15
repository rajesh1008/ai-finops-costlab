import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from ch45_run_sims import *

def test_split_range():
    a, b, c, d = split_range(180000, 43400, 0.2, 0.6, 30750, 33600)
    assert round(a, 4) == 0.2191 and round(b, 4) == 0.3155 and round(c, 4) == 0.2831 and round(d, 4) == 0.3796

def test_compounding():
    last, tot = compounding(180000, 0.20, 12)
    assert round(last) == 1604898 and round(tot) == 8549388
    assert round(compounding(180000, 0.05, 12)[1]) == 3008337

def test_sample_sizes():
    assert (sample_size(0.5, 0.05), sample_size(0.5, 0.05, pop=400), sample_size(0.2, 0.05), sample_size(0.5, 0.03)) == (385, 197, 246, 1068)

def test_queue():
    L = queue_population()
    assert len(L) == 400 and abs(sum(L) - 108000) < 1e-6
    assert [round(top_k_share(L, k), 3) for k in (5, 10, 20, 40, 100)] == [0.141, 0.231, 0.366, 0.511, 0.766]
    assert round(L[0]) == 3319
    m, lo, hi = sample_estimate(L, 40)
    assert round(lo, 3) == -0.378 and round(hi, 3) == 0.458

def test_price_rise():
    assert round(breakeven_loss(40, .10, 22), 4) == 0.1818
    assert price_rise(40, .10, [(20, 60, .30), (80, 12.5, .05)]) == (1800.0, 2170.0, 100, 90.0)
    assert price_rise(40, .10, [(20, 60, .10), (80, 12.5, .10)])[1] == 1980.0
    assert price_rise(40, .10, [(20, 60, 0.0), (80, 12.5, .20)])[1] == 1696.0
    assert round(breakeven_loss(40, .10, 12.5), 3) == 0.127 and breakeven_loss(40, .10, 60) < 0

def test_series():
    assert series_count([7, 12, 2400, 6, 3]) == 3628800 and series_count([7, 12, 6, 3]) == 1512
    assert occupied_series(2400, 2.5, 1.8, 1.6, 2) == 34560
    assert round(monthly_series_cost(3628800), 2) == 7257.6 and round(monthly_series_cost(34560), 2) == 69.12 and round(monthly_series_cost(1512), 2) == 3.02
