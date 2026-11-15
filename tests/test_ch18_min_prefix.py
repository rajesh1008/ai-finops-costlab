import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from cache_min_prefix_lab import filler, summarise, TARGETS

def test_filler_reproducible_and_sized():
    assert filler(100, 1) == filler(100, 1)
    assert len(filler(100, 1).split()) == 100

def test_summarise_boundary():
    rows = [{"model": "m", "target": 1, "input": 900, "write": 0, "read": 0},
            {"model": "m", "target": 2, "input": 10, "write": 1500, "read": 0},
            {"model": "m", "target": 3, "input": 5, "write": 0, "read": 2500}]
    s = summarise(rows)["m"]
    assert s == {"smallest_cached": 1510, "largest_uncached": 900}

def test_targets_sorted():
    assert TARGETS == sorted(TARGETS)
