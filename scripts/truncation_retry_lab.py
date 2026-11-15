#!/usr/bin/env python3
"""Ch22 lab (42nd run). REAL calls. A reply cut off by max_tokens is billed in full and is not an error. Does a blind retry at the same cap repeat the cut?
8 prompts x caps (50,100,200,400) x 2 models, plus a second identical pass at caps 100 and 200 (the blind retry) = 96 calls. Key from env only."""
import os, sys, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
TOPICS = ["a refund policy for a software subscription", "a runbook step list for a database failover", "a checklist for onboarding a new engineer",
          "an explanation of exponential backoff", "a summary of how prompt caching saves money", "a plan for a quarterly cost review",
          "a description of a circuit breaker", "a list of risks in a model upgrade"]
OUT = Path(__file__).resolve().parents[1] / "runs" / "truncation-retry-lab-2026-11-13.jsonl"
def one(a):
    cl, ti, cap, mi, rep = a
    x = cl.messages.create(model=MODELS[mi], max_tokens=cap, messages=[{"role": "user", "content": "Write " + TOPICS[ti] + " for an internal wiki page. Be thorough."}])
    t = "".join(b.text for b in x.content if b.type == "text")
    return {"topic": ti, "cap": cap, "model": MODELS[mi], "rep": rep, "input": x.usage.input_tokens, "out": x.usage.output_tokens, "stop": x.stop_reason, "tail": t[-40:]}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic()
    jobs = [(cl, ti, cap, mi, 0) for ti in range(8) for cap in (50, 100, 200, 400) for mi in (0, 1)]
    jobs += [(cl, ti, cap, mi, 1) for ti in range(8) for cap in (100, 200) for mi in (0, 1)]
    def safe(j):
        try: return one(j)
        except Exception as e: return {"topic": j[1], "cap": j[2], "model": MODELS[j[3]], "rep": j[4], "error": type(e).__name__ + ": " + str(e)[:160]}
    with ThreadPoolExecutor(6) as ex: rows = list(ex.map(safe, jobs))
    OUT.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
def summary():
    rows = [json.loads(l) for l in OUT.read_text().splitlines()]; good = [r for r in rows if "error" not in r]
    print("calls", len(rows), "errors", len(rows) - len(good))
    for m in MODELS:
        for cap in (50, 100, 200, 400):
            rs = [r for r in good if r["model"] == m and r["cap"] == cap and r["rep"] == 0]
            if rs: print(m, "cap", cap, "n", len(rs), "cut", sum(r["stop"] == "max_tokens" for r in rs), "mean_out", round(sum(r["out"] for r in rs) / len(rs), 1))
    for m in MODELS:
        for cap in (100, 200):
            a = {r["topic"]: r for r in good if r["model"] == m and r["cap"] == cap and r["rep"] == 0}
            b = {r["topic"]: r for r in good if r["model"] == m and r["cap"] == cap and r["rep"] == 1}
            both = [t for t in a if t in b]
            print(m, "cap", cap, "first cut", sum(a[t]["stop"] == "max_tokens" for t in both), "of", len(both), "retry cut among first-cut", sum(b[t]["stop"] == "max_tokens" for t in both if a[t]["stop"] == "max_tokens"))
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
