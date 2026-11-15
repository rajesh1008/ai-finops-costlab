import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from session_percentiles_demo import sessions, report

def test_shape():
    r = report(sessions())
    assert r["n"] == 1000 and r["mean"] > r["median"] and r["p99"] > r["p90"] > r["median"]
    assert 0.0 < r["top1_share"] < r["top5_share"] < 1.0
    assert report(sessions()) == r
