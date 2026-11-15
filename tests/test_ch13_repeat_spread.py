import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from repeat_spread_summary import summarise

def test_cv_and_ratio():
    rows = [{"model": "m", "kind": "a", "p": 0, "out": o} for o in (100, 100, 200, 200)] + [{"model": "m", "kind": "a", "p": 1, "out": 50}] * 3 + [{"model": "m", "error": "x"}]
    s = summarise(rows)["m"]
    assert s["cells"] == 2
    assert abs(s["max_cv"] - 1 / 3) < 1e-9 and s["max_ratio"] == 2.0 and s["median_cv"] == (1 / 3) / 2
