#!/usr/bin/env python3
"""Chapter 11 lab. REAL calls. 40 worked cost questions (seeded generator, answer is a single dollar figure to the cent), 3 repeats, two models, ceiling 4000.
Records correctness and billed tokens per call. Questions are mine and synthetic; correctness is a numeric match on the last dollar figure in the reply.
Never prints the key."""
import os, sys, json, random, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
OUT = Path(__file__).resolve().parents[1] / "runs" / "cpo-repeats-lab-2026-11-11.jsonl"
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
def items():
    r = random.Random(11); out = []
    for i in range(40):
        calls = r.choice([1200, 3700, 4200, 8800, 15300]); tin = r.choice([813, 1507, 1921, 2644, 3377]); tout = r.choice([127, 313, 458, 702])
        hit = r.choice([0.0, 0.0, 0.4, 0.7])
        pin = r.choice([1, 2, 3]); pout = r.choice([4, 5, 10, 15])
        # cached share of input is billed at a tenth of the input price
        true = calls * (tin * (1 - hit) * pin + tin * hit * pin * 0.1 + tout * pout) / 1e6
        cache = f" {int(hit*100)} percent of the input tokens in each call are served from a cache and billed at one tenth of the input price." if hit else ""
        q = f"A job makes {calls:,} calls a day, each with {tin:,} input tokens and {tout} output tokens, at ${pin} per million input tokens and ${pout} per million output tokens.{cache} What does it cost per day? End your reply with a final line of the form ANSWER: $<amount to the cent>."
        out.append({"q": q, "true": round(true, 2)})
    return out
def parse(t):
    m = re.findall(r"ANSWER:\s*\$?\s*([0-9][0-9,]*\.?[0-9]*)", t)
    if not m: return None
    try: return float(m[-1].replace(",", ""))
    except ValueError: return None
def one(a):
    cl, m, it, k, rep = a
    x = cl.messages.create(model=m, max_tokens=4000, messages=[{"role": "user", "content": it["q"]}])
    t = "".join(b.text for b in x.content if b.type == "text")
    v = parse(t)
    return {"model": m, "item": k, "rep": rep, "true": it["true"], "got": v, "correct": v is not None and abs(v - it["true"]) < 0.005 + 1e-9, "in": x.usage.input_tokens, "out": x.usage.output_tokens, "stop": x.stop_reason}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); its = items(); jobs = [(cl, m, it, k, r) for m in MODELS for k, it in enumerate(its) for r in range(3)]
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(one, jobs))
    OUT.write_text("\n".join(json.dumps(x) for x in res) + "\n")
    for m in MODELS:
        q = [x for x in res if x["model"] == m]
        print(m, "n", len(q), "correct", sum(x["correct"] for x in q), "no-answer", sum(x["got"] is None for x in q), "mean in %.0f out %.0f" % (sum(x["in"] for x in q)/len(q), sum(x["out"] for x in q)/len(q)))
if __name__ == "__main__": main()
