import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from peer_rank_sim import rank_range

def test_width_shrinks_with_peers():
    lo5, _, hi5 = rank_range(0.5, 5, trials=3000); lo50, _, hi50 = rank_range(0.5, 50, trials=3000)
    assert (hi5 - lo5) > (hi50 - lo50)

def test_median_near_truth():
    _, md, _ = rank_range(0.25, 50, trials=3000)
    assert 18 <= md <= 32
