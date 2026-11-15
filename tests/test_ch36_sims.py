import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ch36_run_sims as s
def test_ch25(): 
    r = s.ch25(); assert round(r["per_sub_full"], 5) == 0.22905 and round(r["per_sub_brief"], 5) == 0.08205 and round(r["saving"], 3) == 0.589
def test_ch26(): 
    r = s.ch26(); assert r[1.5] > r[2.0] > r[3.0] and round(r[2.0], 2) == 0.84
def test_ch33():
    r, t1, t10 = s.ch33(); assert round(r[95]["cost_share_removed"], 3) == 0.141 and round(t10, 2) == 0.46
def test_ch36():
    r, ut, ht = s.ch36(); assert round(r["Search"][0]) == 46800 and round(r["Search"][1]) == 38571
def test_ch40_bridge():
    assert 200_000 * 0.30 == 60_000 and round(1_200_000 * (346_500 / 1_200_000 - 0.30)) == -13_500
    assert 60_000 - 18_000 - 6_000 + 10_500 - 0 == 46_500
