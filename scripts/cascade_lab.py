#!/usr/bin/env python3
"""Chapter 17 lab. REAL calls. 30 SYNTHETIC billing word problems (seed 17), three models, no thinking, default temperature.
Haiku 4.5 x2 samples, Haiku 5.5 x2, Sonnet 4.6 x1. Policies are then evaluated over the recorded answers at the vendor page rates
(opened 10 Nov 2026). Never prints the key."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
from costlab.gateway import Meter
from costlab.cascade import make_problems, correct, agree

RUNS = Path(__file__).resolve().parents[1] / "runs"
LOG = RUNS / "cascade-2026-11-10.jsonl"
ANS = RUNS / "cascade-answers-2026-11-10.json"
MODELS = {"H45": "claude-haiku-4-5-20251001", "H55": "claude-haiku-5-5", "S46": "claude-sonnet-4-6"}
PLAN = [("H45", 2), ("H55", 2), ("S46", 1)]

def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    if LOG.exists(): LOG.unlink()
    meter = Meter(Anthropic(), LOG, product="cascade-lab")
    probs = make_problems()
    jobs = [(p, k, j) for p in probs for k, n in PLAN for j in range(n)]
    def run(job):
        p, k, j = job
        for attempt in range(4):
            try:
                msg = meter.call(model=MODELS[k], session_id=f"{k}-{p['id']}-{j}", step=1, feature=f"cascade-{k}",
                                 max_tokens=300, messages=[{"role": "user", "content": p["q"]}])
                break
            except Exception as e:  # the same call is retried, never a different model or key
                print("retry", k, p["id"], str(e)[:80], flush=True)
                time.sleep(3 * (attempt + 1))
        else:
            raise SystemExit("call kept failing")
        return p["id"], k, j, "".join(b.text for b in msg.content if b.type == "text"), msg.usage.input_tokens, msg.usage.output_tokens
    with ThreadPoolExecutor(2) as ex:
        res = list(ex.map(run, jobs))
    ANS.write_text(json.dumps([{"id": a, "m": b, "j": c, "text": d, "in": e, "out": f} for a, b, c, d, e, f in res]))
    print("calls", len(res))

if __name__ == "__main__":
    main()
