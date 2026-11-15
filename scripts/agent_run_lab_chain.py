#!/usr/bin/env python3
"""Chapter 24 lab, part three (dependent lookups). REAL calls, claude-haiku-4-5. Each SYNTHETIC clause ends with 'If unresolved, escalate per clause J' (J = (i*37+11) % 160 + 1).
Question: start at clause S, follow the escalation H times, and report the FS reference of the clause you land on. H in {1, 3, 5, 8}. The agent cannot batch searches because each
query depends on the previous result. Tools: search(query) top 3 by BM25, submit(references). Step cap 16. 10 questions per H x 3 repeats = 120 runs. Never prints the key."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
from costlab.retrieval import BM25
RUNS = Path(__file__).resolve().parents[1] / "runs"; OUT = RUNS / "agent-run-lab-chain-2026-11-10.json"
MODEL = "claude-haiku-4-5-20251001"; CAP = 16; REPEATS = 3
nxt = lambda i: (i * 37 + 11) % 160 + 1
def clauses():
    return [{"i": i, "ref": f"FS-{1000 + i * 13}",
             "text": f"Clause {i}. For workspace tier {i % 7 + 1}, a support agent must verify the account owner, record reference FS-{1000 + i * 13}, and confirm the retention window of {30 + (i % 12) * 15} days before describing any export or deletion procedure. If unresolved, escalate per clause {nxt(i)}."} for i in range(1, 161)]
TOOLS = [{"name": "search", "description": "Search the support handbook. Returns the 3 best matching clauses.", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
         {"name": "submit", "description": "Submit the final answer: the list of FS reference codes that answer the question.", "input_schema": {"type": "object", "properties": {"references": {"type": "array", "items": {"type": "string"}}}, "required": ["references"]}}]
SYSTEM = "You answer questions about the Fieldstone support handbook. Use search to find clauses, then call submit. Only submit codes you have seen in search results."
def main():
    C = clauses(); bm = BM25([c["text"] for c in C]); import random; rnd = random.Random(241)
    Q = []
    for h in (1, 3, 5, 8):
        for _ in range(10):
            s = rnd.randint(1, 160); cur = s
            for _ in range(h): cur = nxt(cur)
            Q.append({"h": h, "q": f"Start at clause {s} of the handbook. Follow its escalation instruction {h} time{'s' if h > 1 else ''} in a row (each time go to the clause it names). Report the reference code of the clause you end on.", "gold": [C[cur - 1]["ref"]]})
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic()
    def call(msgs):
        for a in range(4):
            try: return cl.messages.create(model=MODEL, max_tokens=500, system=SYSTEM, tools=TOOLS, messages=msgs)
            except Exception: time.sleep(2 + 3 * a)
        return None
    def run(job):
        qi, rep = job; q = Q[qi]; msgs = [{"role": "user", "content": q["q"]}]; steps = []; answer = None; status = "cap"
        for s in range(CAP):
            m = call(msgs)
            if m is None: status = "api_error"; break
            steps.append({"in": m.usage.input_tokens, "out": m.usage.output_tokens}); msgs.append({"role": "assistant", "content": m.content})
            uses = [b for b in m.content if b.type == "tool_use"]
            if not uses: status = "no_tool"; break
            results = []
            for u in uses:
                if u.name == "submit":
                    answer = sorted(set(u.input.get("references", []))); status = "submitted"; results.append({"type": "tool_result", "tool_use_id": u.id, "content": "received"})
                else:
                    results.append({"type": "tool_result", "tool_use_id": u.id, "content": "\n".join(C[i]["text"] for i in bm.search(str(u.input.get("query", "")), 3))})
            msgs.append({"role": "user", "content": results})
            if status == "submitted": break
        return {"q": qi, "rep": rep, "steps": steps, "status": status, "ok": answer is not None and set(answer) == set(q["gold"]), "answer": answer, "gold": q["gold"], "n_pairs": q["h"]}
    jobs = [(qi, r) for qi in range(len(Q)) for r in range(REPEATS)]
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(run, jobs))
    OUT.write_text(json.dumps({"model": MODEL, "cap": CAP, "results": res})); print("saved", OUT.name, "runs", len(res), "api_error", sum(r["status"] == "api_error" for r in res))
if __name__ == "__main__": main()
