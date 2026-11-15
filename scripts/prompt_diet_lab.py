#!/usr/bin/env python3
"""Chapter 19 lab. REAL calls to claude-haiku-4-5 on 60 SYNTHETIC tickets (seed 16, Chapter 16 generator, hard share 0.3).
Same instruction, three system prompts: lean (about 40 tokens), +800 tokens of irrelevant house rules, +3,000 tokens. No caching.
Never prints the key."""
import os, sys, json, time
from pathlib import Path
from anthropic import Anthropic
from costlab.gateway import Meter
from costlab.triage import make_tickets, LABELS
from costlab.context import filler
MODEL = "claude-haiku-4-5-20251001"
RUNS = Path(__file__).resolve().parents[1] / "runs"
LOG = RUNS / "prompt-diet-2026-11-10.jsonl"; ANS = RUNS / "prompt-diet-answers-2026-11-10.json"
CORE = ("Classify the customer message into exactly one of: billing, password, shipping, cancel, other. "
        "Reply with the single label word only.")
SYS = {"lean": CORE, "plus800": "House rules for the support team (context only):\n" + filler(800) + "\n\n" + CORE,
       "plus3000": "House rules for the support team (context only):\n" + filler(3000) + "\n\n" + CORE}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    if LOG.exists(): LOG.unlink()
    meter = Meter(Anthropic(), LOG, product="prompt-diet-lab")
    res = []
    for t in make_tickets(60):
        for v, system in SYS.items():
            for attempt in range(3):
                try:
                    m = meter.call(model=MODEL, session_id=f"{v}-{t['id']}", step=1, feature=f"diet-{v}", max_tokens=8,
                                   system=system, messages=[{"role": "user", "content": t["text"]}]); break
                except Exception as e:
                    print("retry", v, t["id"], str(e)[:80], flush=True); time.sleep(4)
            else: raise SystemExit("call kept failing")
            w = "".join(b.text for b in m.content if b.type == "text").strip().lower().split()
            lab = w[0].strip(".,") if w else ""
            res.append({"id": t["id"], "v": v, "pred": lab if lab in LABELS else "other", "label": t["label"], "in": m.usage.input_tokens})
    ANS.write_text(json.dumps(res)); print("calls", len(res))
if __name__ == "__main__": main()
