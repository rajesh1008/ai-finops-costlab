import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from self_predict_summary import summarise

def rows():
    return [
        {"model": "m", "pred": 50, "actual": 100, "pred_call_out": 5},
        {"model": "m", "pred": 400, "actual": 200, "pred_call_out": 5},
        {"model": "m", "pred": 30, "actual": 300, "pred_call_out": 5},
        {"model": "m", "pred": None, "actual": 10, "pred_call_out": 5},
    ]

def test_counts_and_direction():
    s = summarise(rows())["m"]
    assert s["n"] == 3 and s["unparsed"] == 1
    assert s["under"] == 2 and s["within_2x"] == 2
    assert s["median_ratio"] == 0.5
