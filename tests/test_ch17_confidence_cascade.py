import json
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "runs" / "confidence-cascade-lab-2026-11-13.jsonl"
def test_table():
    rows = [json.loads(l) for l in R.read_text().splitlines()]
    assert len(rows) == 36 and not any("error" in r for r in rows)
    for th, esc, kept in ((80, 4, 3), (90, 10, 2), (95, 17, 0)):
        assert sum(r["conf"] < th for r in rows) == esc
        assert sum((not r["ok"]) for r in rows if r["conf"] >= th) == kept
    assert round(0.0008 + 4 / 36 * 0.006, 5) == 0.00147
