import json
from pathlib import Path
RUNS = Path(__file__).resolve().parents[1] / "runs"
def rows(): return [json.loads(l) for l in (RUNS / "cache-hierarchy-gap-2026-11-13.jsonl").read_text().splitlines()]
def test_gap_floor_between_3924_and_4104():
    r = rows(); assert len(r) == 30
    sysblock = 3215
    read = {}
    for x in r:
        if x["cell"] == "system_changed": read.setdefault(x["size"], []).append(x["read"])
    for s in ("w1200", "w1750", "w2050"): assert all(v == 0 for v in read[s])
    for s in ("w2150", "w2300"): assert all(v > 4000 for v in read[s])
    warm = {x["size"]: x["write"] - sysblock for x in r if x["cell"] == "warm" and x["rep"] == 0}
    assert warm["w2050"] < 4096 < warm["w2150"]
