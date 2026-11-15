import json
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "runs"
def test_padding_runs_complete():
    a = json.loads((R / "padding-position-lab-2026-11-11.json").read_text()); b = json.loads((R / "padding-amend-lab-2026-11-11.json").read_text())
    assert len(a) == 240 and len(b) == 120 and not any("error" in r for r in a + b)
def test_amend_misses_are_stale_only():
    b = json.loads((R / "padding-amend-lab-2026-11-11.json").read_text())
    assert sum(r["ok"] for r in b if r["order"] == "B") == 47 and sum(r["stale"] for r in b) == 13 and not any(r["near"] for r in b)
def test_token_ratio_file():
    t = json.loads((R / "token-ratio-lab-2026-11-11.json").read_text())
    assert t["digits"]["claude-haiku-5-5"] == t["digits"]["claude-haiku-4-5-20251001"]
