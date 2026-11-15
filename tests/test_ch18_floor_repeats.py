import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import cache_floor_repeats_lab as b

def test_summarise_mixed_cells_and_errors():
    rows = [{"model": "m", "target": 1, "rep": 0, "input": 400, "write": 0, "read": 0},
            {"model": "m", "target": 2, "rep": 0, "input": 16, "write": 520, "read": 0},
            {"model": "m", "target": 2, "rep": 1, "input": 500, "write": 0, "read": 0},
            {"model": "m", "target": 3, "rep": 0, "error": "X"}]
    s = b.summarise(rows)["m"]
    assert s["cells_none_cached"] == [1] and s["cells_mixed"] == [2] and s["errors"] == 1
    assert s["smallest_cached"] == 536 and s["largest_uncached"] == 500

def test_repeats_and_sizes():
    assert b.REPEATS == 3
    for t in b.MODELS.values(): assert t == sorted(t)

def test_recorded_runs_floor_between():
    import json
    rows = []
    for n in ("cache-floor-repeats-2026-11-12.jsonl", "cache-floor-narrow-2026-11-12.jsonl"):
        rows += [json.loads(l) for l in (Path(__file__).resolve().parents[1] / "runs" / n).read_text().splitlines()]
    s = b.summarise([r for r in rows if r["model"] == "claude-haiku-5-5"])["claude-haiku-5-5"]
    assert s["errors"] == 0 and s["largest_uncached"] < s["smallest_cached"] + 100
    assert s["largest_uncached"] == 522 and s["smallest_cached"] == 539

def test_recorded_haiku45_boundary_brackets_documented_minimum():
    import json
    p = Path(__file__).resolve().parents[1] / "runs"
    rows = []
    for n in ("cache-floor-repeats-2026-11-12.jsonl", "cache-floor-narrow45-2026-11-12.jsonl"):
        rows += [json.loads(l) for l in (p / n).read_text().splitlines()]
    s = b.summarise([r for r in rows if r["model"].startswith("claude-haiku-4-5")])[rows[0]["model"]]
    # system tokens = total - fixed overhead (write rows show 13): uncached max 4092-13 < 4096 < cached min write 4135
    assert s["errors"] == 0 and s["largest_uncached"] - 13 < 4096 < s["smallest_cached"] - 13
