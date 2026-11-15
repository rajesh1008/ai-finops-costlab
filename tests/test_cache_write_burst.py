import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import cache_write_burst as B
RUN = pathlib.Path(__file__).resolve().parents[1] / "runs" / "cache-substagger-lab-2026-11-15.jsonl"
def rows(): return [json.loads(l) for l in RUN.read_text().splitlines()]
def test_gap_zero_always_burst():
    b = B.bursts(rows())
    assert sum(1 for x in b if x["gap"] == 0) == 4
    assert not any(x["gap"] in (0.4, 0.8) for x in b)
def test_synthetic():
    r = [{"gap": 0, "rep": 0, "rows": [{"start_s": 0, "cw": 5000, "cr": 0}, {"start_s": 0.1, "cw": 5000, "cr": 0}]}]
    assert B.bursts(r)[0]["close_pairs"] == 1
    assert abs(B.wasted_premium(r) - 5000 * 1.15 / 1e6) < 1e-9
