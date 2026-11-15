import json
from pathlib import Path
from costlab.context import session_cost_policy, filler
R = Path(__file__).resolve().parents[1] / "runs"

def test_masking_every_turn_sends_fewer_tokens_but_can_cost_more():
    raw = session_cost_policy(20, "raw"); every = session_cost_policy(20, "mask_every")
    assert every[1] < raw[1] and every[0] > raw[0]

def test_batched_masking_beats_every_turn_masking():
    assert session_cost_policy(40, "mask_batch", k=10)[0] < session_cost_policy(40, "mask_every")[0]

def test_filler_roughly_sized():
    n = len(filler(800).split()) * 1.35
    assert 700 < n < 1000

def test_recorded_output_lab_hidden_tokens():
    recs = [json.loads(l) for l in (R / "output-constraint-2026-11-10.jsonl").read_text().splitlines()]
    ans = json.loads((R / "output-constraint-answers-2026-11-10.json").read_text())
    num = [a for a in ans if a["v"] == "number"]
    avg_chars = sum(len(a["text"].strip()) for a in num) / len(num)
    avg_out = sum(r["output_tokens"] for r in recs if r["feature"] == "oc-number") / len(num)
    assert avg_chars < 30 and avg_out > 50   # visible answer is a few tokens, billed output is far larger

def test_recorded_diet_lab_cost_scales_with_prompt():
    recs = [json.loads(l) for l in (R / "prompt-diet-2026-11-10.jsonl").read_text().splitlines()]
    c = {}
    for r in recs: c.setdefault(r["feature"], []).append(r["estimated_cost_usd"])
    assert sum(c["diet-plus3000"]) > 10 * sum(c["diet-lean"])
