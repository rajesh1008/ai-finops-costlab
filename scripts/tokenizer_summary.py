#!/usr/bin/env python3
"""Chapter 30: arithmetic over tokenizer-lab (count_tokens) and the recorded shadow run (billed input and output). Prints the per-task price cut against the list price cut."""
import json, statistics
from pathlib import Path
from costlab.estimate import estimate_usd
R = Path(__file__).resolve().parents[1] / "runs"
A, B = "claude-haiku-4-5-20251001", "claude-haiku-5-5"
def main():
    tk = json.load(open(R / "tokenizer-lab-2026-11-11.json")); sh = json.load(open(R / "shadow-lab-2026-11-10.json"))["results"]
    cnt = {(r["q"], r["model"]): r["count"] for r in tk if r["count"] is not None}
    both = [q for q in range(300) if (q, A) in cnt and (q, B) in cnt]
    print(f"prompts counted on both models: {len(both)} of 300")
    ra = [cnt[(q, B)] / cnt[(q, A)] for q in both]
    print(f"count_tokens ratio haiku-5-5 / haiku-4-5: mean {statistics.mean(ra):.4f} min {min(ra):.4f} max {max(ra):.4f}; total {sum(cnt[(q,B)] for q in both)} vs {sum(cnt[(q,A)] for q in both)}")
    by = {(r["q"], r["model"]): r for r in sh if r["error"] is None}
    ok = [q for q in range(300) if (q, A) in by and (q, B) in by]
    ia = [by[(q, A)]["in"] for q in ok]; ib = [by[(q, B)]["in"] for q in ok]; oa = [by[(q, A)]["out"] for q in ok]; ob = [by[(q, B)]["out"] for q in ok]
    print(f"billed (shadow run, {len(ok)} paired): input mean {statistics.mean(ia):.1f} vs {statistics.mean(ib):.1f}; output mean {statistics.mean(oa):.1f} vs {statistics.mean(ob):.1f}")
    ca = sum(estimate_usd("anthropic:" + A, by[(q, A)]["in"], by[(q, A)]["out"]) for q in ok) / len(ok)
    cb = sum(estimate_usd("anthropic:" + B, by[(q, B)]["in"], by[(q, B)]["out"]) for q in ok) / len(ok)
    print(f"cost per call at placeholder rates: haiku-4-5 ${ca:.6f}, haiku-5-5 ${cb:.6f}; ratio {ca/cb:.2f}x; list price ratio input 10.0x output 10.0x")
    print(f"share of the 90 percent list cut that reaches the task bill: {(1-cb/ca)*100:.1f} percent cut per task against 90.0 percent per token")
    # same tokens, new price: what a dollar commit on the old model buys
    print(f"tasks per dollar: haiku-4-5 {1/ca:,.0f}; haiku-5-5 {1/cb:,.0f}")
if __name__ == "__main__": main()
