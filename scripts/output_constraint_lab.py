#!/usr/bin/env python3
"""Chapter 19 lab. REAL calls to claude-haiku-5-5 on 30 SYNTHETIC billing problems (seed 17, from Chapter 17).
Three answer-format instructions. Loose correctness check as in Chapter 17. Never prints the key."""
import os, sys, json, time
from pathlib import Path
from anthropic import Anthropic
from costlab.gateway import Meter
from costlab.cascade import make_problems, correct
MODEL = "claude-haiku-5-5"
RUNS = Path(__file__).resolve().parents[1] / "runs"
LOG = RUNS / "output-constraint-2026-11-10.jsonl"; ANS = RUNS / "output-constraint-answers-2026-11-10.json"
BASE = "Give the number and one sentence."
VARIANTS = {"sentence": BASE, "steps": "Show your reasoning step by step, then give the final number.", "number": "Reply with the number only."}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    if LOG.exists(): LOG.unlink()
    meter = Meter(Anthropic(), LOG, product="output-constraint-lab")
    res = []
    for p in make_problems():
        for v, instr in VARIANTS.items():
            q = p["q"].replace(" Give the number and one sentence.", "") + " " + instr
            for attempt in range(3):
                try:
                    m = meter.call(model=MODEL, session_id=f"{v}-{p['id']}", step=1, feature=f"oc-{v}", max_tokens=900,
                                   messages=[{"role": "user", "content": q}]); break
                except Exception as e:
                    print("retry", v, p["id"], str(e)[:80], flush=True); time.sleep(4)
            else: raise SystemExit("call kept failing")
            text = "".join(b.text for b in m.content if b.type == "text")
            res.append({"id": p["id"], "v": v, "text": text, "ok": correct(text, p["answer"]), "out": m.usage.output_tokens})
    ANS.write_text(json.dumps(res)); print("calls", len(res))
if __name__ == "__main__": main()
