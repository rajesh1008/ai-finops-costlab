#!/usr/bin/env python3
"""Chapter 24 lab, part two (multi-lookup questions). REAL calls, claude-haiku-4-5. A tool-using agent answers the Chapter 23 question ('which references apply to tier T with a retention window of D days')
over the SYNTHETIC 160-clause handbook. Tools: search(query) returns the top 3 clauses by BM25 (a retriever that sometimes misses), submit(references) ends the run.
Step cap 14. 40 questions (14 with 2 combinations, 14 with 4, 12 with 6) x 3 repeats = 120 runs, default temperature. Records per-step billed tokens. Never prints the key."""
import os, sys, json, time, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
from costlab.retrieval import BM25
RUNS = Path(__file__).resolve().parents[1] / "runs"; OUT = RUNS / "agent-run-lab-multi-2026-11-10.json"
MODEL = "claude-haiku-4-5-20251001"; CAP = 14; REPEATS = 3
def clauses():
    return [{"i": i, "tier": i % 7 + 1, "days": 30 + (i % 12) * 15, "ref": f"FS-{1000 + i * 13}",
             "text": f"Clause {i}. For workspace tier {i % 7 + 1}, a support agent must verify the account owner, record reference FS-{1000 + i * 13}, and confirm the retention window of {30 + (i % 12) * 15} days before describing any export or deletion procedure."} for i in range(1, 161)]
TOOLS = [{"name": "search", "description": "Search the support handbook. Returns the 3 best matching clauses.", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
         {"name": "submit", "description": "Submit the final answer: the list of FS reference codes that apply.", "input_schema": {"type": "object", "properties": {"references": {"type": "array", "items": {"type": "string"}}}, "required": ["references"]}}]
SYSTEM = "You answer questions about the Fieldstone support handbook. Use search to find clauses, then call submit with every reference code that applies. Only submit codes you have seen in search results."
def main():
    C = clauses(); bm = BM25([c["text"] for c in C])
    allp = sorted({(c["tier"], c["days"]) for c in C}); import random; rnd = random.Random(240)
    Q = []
    for n in [2] * 14 + [4] * 14 + [6] * 12:
        ps = rnd.sample(allp, n)
        lst = "; ".join(f"tier {t} with a {d}-day window" for t, d in ps)
        Q.append({"n": n, "q": f"List every reference that applies to each of these combinations: {lst}. Give one combined list of reference codes.",
                  "gold": sorted({c["ref"] for c in C for t, d in ps if c["tier"] == t and c["days"] == d})})
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic()
    def call(msgs):
        for a in range(4):
            try: return cl.messages.create(model=MODEL, max_tokens=500, system=SYSTEM, tools=TOOLS, messages=msgs)
            except Exception as e:
                last = type(e).__name__; time.sleep(2 + 3 * a)
        return None
    def run(job):
        qi, rep = job; q = Q[qi]; msgs = [{"role": "user", "content": q["q"]}]; steps = []; answer = None; status = "cap"
        for s in range(CAP):
            m = call(msgs)
            if m is None: status = "api_error"; break
            steps.append({"in": m.usage.input_tokens, "out": m.usage.output_tokens})
            msgs.append({"role": "assistant", "content": m.content})
            uses = [b for b in m.content if b.type == "tool_use"]
            if not uses: status = "no_tool"; break
            results = []
            for u in uses:
                if u.name == "submit":
                    answer = sorted(set(u.input.get("references", []))); status = "submitted"
                    results.append({"type": "tool_result", "tool_use_id": u.id, "content": "received"})
                else:
                    hits = [C[i]["text"] for i in bm.search(str(u.input.get("query", "")), 3)]
                    results.append({"type": "tool_result", "tool_use_id": u.id, "content": "\n".join(hits)})
            msgs.append({"role": "user", "content": results})
            if status == "submitted": break
        ok = answer is not None and set(answer) == set(q["gold"])
        return {"q": qi, "rep": rep, "steps": steps, "status": status, "ok": ok, "answer": answer, "gold": q["gold"], "n_pairs": q["n"]}
    jobs = [(qi, r) for qi in range(len(Q)) for r in range(REPEATS)]
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(run, jobs))
    OUT.write_text(json.dumps({"model": MODEL, "cap": CAP, "results": res})); print("saved", OUT.name, "runs", len(res), "api_error", sum(r["status"] == "api_error" for r in res))
if __name__ == "__main__": main()
