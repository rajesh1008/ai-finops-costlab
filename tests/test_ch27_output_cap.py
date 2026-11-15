import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from output_cap_summary import summarise

def test_shares():
    rows = [{"model": "m", "cap": 50, "out": 50, "stop": "max_tokens", "visible_chars": 0},
            {"model": "m", "cap": 50, "out": 30, "stop": "end_turn", "visible_chars": 90},
            {"model": "m", "cap": 50, "error": "x"}]
    s = summarise(rows)[("m", 50)]
    assert s["n"] == 2 and s["mean_out"] == 40 and s["truncated"] == 0.5 and s["no_visible"] == 0.5
