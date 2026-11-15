#!/usr/bin/env python3
"""Chapter 20 second setting, REAL Message Batches calls. Three batches submitted at once (10, 100 and 400 requests), each request one of the SYNTHETIC handbook questions (seed 201, top-3 BM25 clauses pasted in)
on claude-haiku-5-5 with thinking disabled and max_tokens 100, plus a synchronous run of the first 100 of the same requests (6 workers) for price, tokens and accuracy. Wall times use the API's own created_at and ended_at for batches.
Batch price is the placeholder table times 0.5 (vendor page opened 10 Nov 2026). Errors are recorded. Never prints the key."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
from costlab.retrieval import BM25
from costlab.ladder import clauses, make_questions, score
OUT = Path(__file__).resolve().parents[1] / "runs" / "batch-scale-lab-2026-11-11.json"
M = "claude-haiku-5-5"; SYS = "You answer questions about the Fieldstone support handbook using only the clauses supplied. Reply in one short sentence."
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    c = Anthropic(); C = clauses(); bm = BM25([x["text"] for x in C]); Q = make_questions(400, 201)
    def params(q):
        ctx = "\n".join(C[i]["text"] for i in bm.search(q["q"], 3))
        return {"model": M, "max_tokens": 100, "thinking": {"type": "disabled"}, "system": SYS, "messages": [{"role": "user", "content": f"Clauses:\n{ctx}\n\nQuestion: {q['q']}"}]}
    sizes = (10, 100, 400); bs = {}
    for n in sizes:
        bs[n] = c.messages.batches.create(requests=[{"custom_id": f"q{i}", "params": params(Q[i])} for i in range(n)])
    t0 = time.time()
    def one(i):
        m = c.messages.create(**params(Q[i])); return {"id": f"q{i}", "in": m.usage.input_tokens, "out": m.usage.output_tokens, "text": "".join(b.text for b in m.content if b.type == "text")}
    with ThreadPoolExecutor(6) as ex: sync = list(ex.map(one, range(100)))
    sync_secs = time.time() - t0
    done = {}
    while len(done) < len(sizes):
        for n in sizes:
            if n in done: continue
            cur = c.messages.batches.retrieve(bs[n].id)
            if cur.processing_status == "ended": done[n] = cur
        if len(done) < len(sizes): time.sleep(15)
        if time.time() - t0 > 3300: print("timeout waiting"); break
    out = {"model": M, "sync_secs": round(sync_secs, 1), "sync": sync, "questions": Q[:400], "batches": {}}
    for n in sizes:
        cur = c.messages.batches.retrieve(bs[n].id); rows = []
        for res in c.messages.batches.results(bs[n].id):
            if res.result.type == "succeeded":
                m = res.result.message; rows.append({"id": res.custom_id, "in": m.usage.input_tokens, "out": m.usage.output_tokens, "text": "".join(b.text for b in m.content if b.type == "text")})
            else: rows.append({"id": res.custom_id, "result": res.result.type})
        out["batches"][str(n)] = {"created_at": cur.created_at.isoformat(), "ended_at": cur.ended_at.isoformat() if cur.ended_at else None, "status": cur.processing_status, "counts": cur.request_counts.model_dump(), "rows": rows}
    OUT.write_text(json.dumps(out)); print("saved", OUT.name)
if __name__ == "__main__": main()
