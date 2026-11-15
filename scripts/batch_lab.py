#!/usr/bin/env python3
"""Chapter 20 lab. REAL Message Batches calls. Batch 1: 30 SYNTHETIC billing problems (seed 17) on claude-haiku-5-5.
Batch 2: 20 questions over the Chapter 18 handbook on claude-haiku-4-5, 1-hour cache_control on the handbook, to see cache hits in a batch.
Cost = usage at the placeholder table times the batch factor 0.5 (vendor page). Never prints the key."""
import os, sys, json, time
from pathlib import Path
from datetime import datetime, timezone
from anthropic import Anthropic
from costlab.estimate import estimate_usd
from costlab.cascade import make_problems, correct
from scripts_common import handbook
RUNS = Path(__file__).resolve().parents[1] / "runs"
OUT = RUNS / "batch-lab-2026-11-10.json"
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    c = Anthropic()
    probs = make_problems()
    r1 = [{"custom_id": f"bill-{p['id']}", "params": {"model": "claude-haiku-5-5", "max_tokens": 300, "messages": [{"role": "user", "content": p["q"]}]}} for p in probs]
    system = [{"type": "text", "text": "Batch cache lab (salt 2026-11-10).\n" + handbook(), "cache_control": {"type": "ephemeral", "ttl": "1h"}}]
    r2 = [{"custom_id": f"hb-{i}", "params": {"model": "claude-haiku-4-5-20251001", "max_tokens": 60, "system": system,
           "messages": [{"role": "user", "content": f"What reference does clause {3 + 7 * i} use?"}]}} for i in range(20)]
    t0 = time.time()
    b1 = c.messages.batches.create(requests=r1); b2 = c.messages.batches.create(requests=r2)
    created = {b1.id: datetime.now(timezone.utc).isoformat(), b2.id: datetime.now(timezone.utc).isoformat()}
    done = {}
    while len(done) < 2:
        for b in (b1, b2):
            if b.id in done: continue
            cur = c.messages.batches.retrieve(b.id)
            if cur.processing_status == "ended": done[b.id] = time.time() - t0
        if len(done) < 2: time.sleep(20)
        if time.time() - t0 > 3000: print("timeout waiting"); break
    out = {"batches": {}}
    for name, b, model in (("billing", b1, "claude-haiku-5-5"), ("handbook", b2, "claude-haiku-4-5-20251001")):
        cur = c.messages.batches.retrieve(b.id)
        rows = []
        for res in c.messages.batches.results(b.id):
            if res.result.type == "succeeded":
                m = res.result.message; u = m.usage
                text = "".join(x.text for x in m.content if x.type == "text")
                rows.append({"id": res.custom_id, "in": u.input_tokens, "out": u.output_tokens,
                             "cr": getattr(u, "cache_read_input_tokens", 0) or 0, "cw": getattr(u, "cache_creation_input_tokens", 0) or 0, "text": text})
            else:
                rows.append({"id": res.custom_id, "result": res.result.type})
        out["batches"][name] = {"model": model, "seconds_to_end": round(done.get(b.id, -1), 1), "request_counts": cur.request_counts.model_dump(), "rows": rows}
    OUT.write_text(json.dumps(out)); print("saved", OUT.name)
if __name__ == "__main__": main()
