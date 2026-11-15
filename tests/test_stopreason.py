import json
from pathlib import Path
from costlab.stopreason import truncation_share, output_multiple, cost_per_correct
RUNS = Path(__file__).resolve().parents[1] / "runs"

def test_truncation_share_small():
    rs = [{"model": "a", "out": 100, "stop": "max_tokens"}, {"model": "a", "out": 50, "stop": "end_turn"}, {"model": "b", "out": 10, "stop": "end_turn"}]
    t = truncation_share(rs)
    assert t["a"]["call_share"] == 0.5 and abs(t["a"]["token_share"] - 100 / 150) < 1e-9 and t["b"]["truncated_calls"] == 0

def test_output_multiple_base_is_one():
    rs = [{"model": "a", "kind": "x", "out": 10}, {"model": "b", "kind": "x", "out": 30}]
    m = output_multiple(rs, "a")
    assert m[("a", "x")] == 1.0 and m[("b", "x")] == 3.0

def test_cost_per_correct():
    rs = [{"in": 1000000, "out": 0, "right": True}, {"in": 1000000, "out": 0, "right": False}]
    assert cost_per_correct(rs, 1, 5) == 2.0

def test_recorded_maxtokens_lab():
    f = RUNS / "maxtokens-lab-2026-11-11.jsonl"
    rs = [json.loads(l) for l in f.read_text().splitlines()]
    t = truncation_share([dict(r, model=r["model"]) for r in rs], by="model")
    assert len(rs) == 240
    assert t["claude-haiku-5-5"]["call_share"] == 0.5 or t["claude-haiku-5-5"]["call_share"] == 1.0
    # the recorded figure: haiku-5-5 hit the ceiling on all 120 calls up to 800; haiku-4-5 on 60 of 120
    assert t["claude-haiku-5-5"]["truncated_calls"] == 120 and t["claude-haiku-4-5-20251001"]["truncated_calls"] == 60

def test_recorded_billed_output_lab():
    f = RUNS / "billed-output-lab-2026-11-11.jsonl"
    rs = [json.loads(l) for l in f.read_text().splitlines()]
    m = output_multiple(rs, "claude-haiku-4-5-20251001")
    assert len(rs) == 72 and 2.5 < sum(r["out"] for r in rs if r["model"] == "claude-haiku-5-5") / sum(r["out"] for r in rs if r["model"] != "claude-haiku-5-5") < 2.7
    assert m[("claude-haiku-5-5", "judgement")] > 3
