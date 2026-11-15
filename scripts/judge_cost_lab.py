#!/usr/bin/env python3
"""Chapter 29 lab (twenty-first run). REAL calls. A judge grading 30 worked cost answers (15 right, 15 wrong by a stated slip), 2 repeats, both models, ceiling 4000. Records verdict accuracy and billed tokens per judged item. Items and slips are mine, built with a seeded generator. Never prints the key."""
import os, sys, json, random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
VARIANT = os.environ.get("VARIANT", "verdict_first")
OUT = Path(__file__).resolve().parents[1] / "runs" / ("judge-cost-lab-2026-11-11.jsonl" if VARIANT == "verdict_first" else f"judge-cost-lab-2026-11-11-{VARIANT}.jsonl")
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
def items():
    r = random.Random(29); out = []
    for i in range(30):
        calls, tin, tout = r.choice([1200, 3000, 4200, 8000]), r.choice([800, 1500, 1900, 2600]), r.choice([120, 310, 450, 700])
        pin, pout = r.choice([1, 2, 3]), r.choice([4, 5, 10, 15])
        true = calls * (tin * pin + tout * pout) / 1e6
        good = i % 2 == 0
        if good: ans = true
        else:
            slip = r.choice(["swap", "per_thousand", "forgot_output"])
            ans = {"swap": calls * (tin * pout + tout * pin) / 1e6, "per_thousand": true * 1000 / 1e3 * 10, "forgot_output": calls * tin * pin / 1e6}[slip]
            if abs(ans - true) < 0.005: ans = true * 1.1
        q = f"A job makes {calls:,} calls a day, each with {tin:,} input tokens and {tout} output tokens, at ${pin} per million input tokens and ${pout} per million output tokens. What does it cost per day?"
        out.append({"q": q, "proposed": round(ans, 2), "true": round(true, 2), "good": good})
    return out
def one(a):
    cl, m, it, k, rep = a
    ask = "Is the proposed answer correct to the cent? Reply with exactly one word first: CORRECT or INCORRECT, then one short line of reason." if VARIANT == "verdict_first" else "Is the proposed answer correct to the cent? Work the cost out briefly first, then end with a final line that is exactly VERDICT: CORRECT or VERDICT: INCORRECT."
    x = cl.messages.create(model=m, max_tokens=4000, messages=[{"role": "user", "content": f"Question: {it['q']}\nProposed answer: ${it['proposed']:,.2f} per day.\n{ask}"}])
    t = "".join(b.text for b in x.content if b.type == "text").strip().upper()
    if VARIANT == "verdict_first": verdict = "INCORRECT" if t.startswith("INCORRECT") else ("CORRECT" if t.startswith("CORRECT") else "OTHER")
    else:
        last = t.splitlines()[-1].replace("*", "").strip() if t else ""
        verdict = "INCORRECT" if last.endswith("VERDICT: INCORRECT") else ("CORRECT" if last.endswith("VERDICT: CORRECT") else "OTHER")
    return {"model": m, "item": k, "rep": rep, "good": it["good"], "verdict": verdict, "right": (verdict == "CORRECT") == it["good"] and verdict != "OTHER", "in": x.usage.input_tokens, "out": x.usage.output_tokens, "thinking": any(b.type == "thinking" for b in x.content)}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); its = items(); jobs = [(cl, m, it, k, r) for m in MODELS for k, it in enumerate(its) for r in range(2)]
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(one, jobs))
    OUT.write_text("\n".join(json.dumps(x) for x in res) + "\n")
    for m in MODELS:
        q = [x for x in res if x["model"] == m]
        fp = [x for x in q if not x["good"] and x["verdict"] == "CORRECT"]; fn = [x for x in q if x["good"] and x["verdict"] == "INCORRECT"]
        print(m, "n", len(q), "right", sum(x["right"] for x in q), "wrong-accepted", len(fp), "right-rejected", len(fn), "other", sum(x["verdict"] == "OTHER" for x in q), "mean in %.0f out %.0f" % (sum(x["in"] for x in q)/len(q), sum(x["out"] for x in q)/len(q)), "thinking", sum(x["thinking"] for x in q))
if __name__ == "__main__": main()
