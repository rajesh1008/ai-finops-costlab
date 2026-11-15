import json
from pathlib import Path
def test_run_file():
    rows = [json.loads(l) for l in (Path(__file__).resolve().parents[1] / "runs" / "brevity-extract-lab-2026-11-12.jsonl").read_text().splitlines()]
    assert len(rows) == 96 and not any("error" in r for r in rows)
    assert all("reply" in r for r in rows)
