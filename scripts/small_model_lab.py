#!/usr/bin/env python3
"""Chapter 21 lab. REAL calls. 600 SYNTHETIC tickets (seed 21): 400 train pool, 200 test. Teacher labels all 600 with claude-haiku-4-5, zero-shot with label list.
Small API model (claude-haiku-5-5) labels the 200 test tickets. Teacher self-agreement: 100 test tickets labelled again. Saves runs/small-model-lab-2026-11-10.json. Never prints the key."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
from costlab.smallmodels import make_tickets, make_tickets_hard, INTENTS, PRECEDENCE
HARD = os.environ.get('HARD') == '1'
RUNS = Path(__file__).resolve().parents[1] / "runs"; OUT = RUNS / ("small-model-lab-hard-2026-11-10.json" if os.environ.get("HARD") == "1" else "small-model-lab-2026-11-10.json")
SYSTEM = ("Classify the support ticket into exactly one intent: " + ", ".join(INTENTS) + ". The intent is what the customer is asking for now; "
          "ignore topics mentioned only as background. Reply with the intent word only.")
if HARD: SYSTEM = ("Classify the support ticket into exactly one intent: " + ", ".join(INTENTS) + ". A ticket may contain two requests. Pick the one that ranks higher in this precedence order, highest first: " + ", ".join(PRECEDENCE) + ". Reply with the intent word only.")
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    c = Anthropic(); T = make_tickets_hard() if HARD else make_tickets()
    def call(job):
        model, t = job
        for a in range(4):
            try:
                m = c.messages.create(model=model, max_tokens=12, system=SYSTEM, messages=[{"role": "user", "content": t["text"]}])
                txt = "".join(x.text for x in m.content if x.type == "text").strip().lower().split()[0].strip(".,")
                return {"id": t["id"], "model": model, "pred": txt, "in": m.usage.input_tokens, "out": m.usage.output_tokens}
            except Exception as e:
                err = type(e).__name__; time.sleep(2 + 3 * a); last = str(e)[:80]
        return {"id": t["id"], "model": model, "pred": None, "error": err}
    H45, H55 = "claude-haiku-4-5-20251001", "claude-haiku-5-5"
    jobs = [(H45, t) for t in T] + [(H55, t) for t in T[400:]] + [("again:" + H45, t) for t in T[400:500]]
    def run(j):
        r = call((j[0].replace("again:", ""), j[1])); r["arm"] = "teacher_again" if j[0].startswith("again:") else ("teacher" if j[0] == H45 else "small"); return r
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(run, jobs))
    OUT.write_text(json.dumps({"tickets": T, "results": res})); print("saved", OUT.name, "errors:", sum(1 for r in res if r["pred"] is None))
if __name__ == "__main__": main()
