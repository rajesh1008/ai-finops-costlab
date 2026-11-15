#!/usr/bin/env python3
"""Chapter 25 cheap single agent (eleventh run): arm S only, run on claude-haiku-5-5 with thinking disabled, the baseline for cheap_worker_lab.py. Sibling docstring: Chapter 25 cheap-worker run: arm W only. Same 30 questions (seed 250) and design as multi_agent_lab.py arm M, but the workers run claude-haiku-5-5 with thinking disabled; the supervisor stays haiku-4-5. Original docstring: Chapter 25 lab. REAL calls, claude-haiku-4-5, SYNTHETIC 160-clause handbook, BM25 search (top 3).
Paired design on the same 30 questions x 2 repeats (60 runs per arm): 15 questions with 2 tier/window combinations, 15 with 6.
Arm S: one agent with search + submit (as in agent_run_lab_multi.py).
Arm M: supervisor + workers. Supervisor call 1 (no tools) splits the question into sub-questions of at most 2 combinations (JSON list). Each sub-question goes to a worker (search+submit loop, cap 6),
which returns its references. Supervisor call 2 receives the question and worker answers, then calls submit with the combined list. Costs recorded per role. Never prints the key."""
import os, sys, json, time, re, random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
from costlab.retrieval import BM25
RUNS = Path(__file__).resolve().parents[1] / "runs"; OUT = RUNS / "cheap-single-lab-2026-11-10.json"
MODEL = "claude-haiku-4-5-20251001"; WMODEL = "claude-haiku-5-5"; REPEATS = 2
def clauses():
    return [{"i": i, "tier": i % 7 + 1, "days": 30 + (i % 12) * 15, "ref": f"FS-{1000 + i * 13}",
             "text": f"Clause {i}. For workspace tier {i % 7 + 1}, a support agent must verify the account owner, record reference FS-{1000 + i * 13}, and confirm the retention window of {30 + (i % 12) * 15} days before describing any export or deletion procedure."} for i in range(1, 161)]
TOOLS = [{"name": "search", "description": "Search the support handbook. Returns the 3 best matching clauses.", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
         {"name": "submit", "description": "Submit the final answer: the list of FS reference codes that apply.", "input_schema": {"type": "object", "properties": {"references": {"type": "array", "items": {"type": "string"}}}, "required": ["references"]}}]
SYSTEM = "You answer questions about the Fieldstone support handbook. Use search to find clauses, then call submit with every reference code that applies. Only submit codes you have seen in search results."
SUP1 = "You are a supervisor. Split the user's question into independent sub-questions of at most 2 tier/window combinations each. Reply with a JSON list of strings and nothing else. Each string must be a complete question."
SUP2 = "You are a supervisor. Worker answers are given. Call submit once with the union of all reference codes the workers reported."
def main():
    C = clauses(); bm = BM25([c["text"] for c in C]); allp = sorted({(c["tier"], c["days"]) for c in C}); rnd = random.Random(250)
    Q = []
    for n in [2] * 15 + [6] * 15:
        ps = rnd.sample(allp, n); lst = "; ".join(f"tier {t} with a {d}-day window" for t, d in ps)
        Q.append({"n": n, "q": f"List every reference that applies to each of these combinations: {lst}. Give one combined list of reference codes.",
                  "gold": sorted({c["ref"] for c in C for t, d in ps if c["tier"] == t and c["days"] == d})})
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic()
    def call(worker=False, **kw):
        for a in range(4):
            try: return cl.messages.create(model=WMODEL if worker else MODEL, max_tokens=600, **({'thinking': {'type': 'disabled'}} if worker else {}), **kw)
            except Exception: time.sleep(2 + 3 * a)
        return None
    def agent(question, system, cap=8):
        msgs = [{"role": "user", "content": question}]; steps = []; answer = None
        for _ in range(cap):
            m = call(worker=True, system=system, tools=TOOLS, messages=msgs)
            if m is None: return steps, answer, "api_error"
            steps.append({"in": m.usage.input_tokens, "out": m.usage.output_tokens}); msgs.append({"role": "assistant", "content": m.content})
            uses = [b for b in m.content if b.type == "tool_use"]
            if not uses: return steps, answer, "no_tool"
            res = []
            for u in uses:
                if u.name == "submit": answer = sorted(set(u.input.get("references", []))); res.append({"type": "tool_result", "tool_use_id": u.id, "content": "received"})
                else: res.append({"type": "tool_result", "tool_use_id": u.id, "content": "\n".join(C[i]["text"] for i in bm.search(str(u.input.get("query", "")), 3))})
            msgs.append({"role": "user", "content": res})
            if answer is not None: return steps, answer, "submitted"
        return steps, answer, "cap"
    def run(job):
        qi, rep, arm = job; q = Q[qi]
        if arm == "S":
            steps, ans, st = agent(q["q"], SYSTEM); roles = {"single": steps}
        else:
            roles = {}; m1 = call(system=SUP1, messages=[{"role": "user", "content": q["q"]}])
            if m1 is None: return {"q": qi, "rep": rep, "arm": arm, "status": "api_error", "roles": {}, "ok": False, "n": q["n"], "workers": 0}
            roles["supervisor_plan"] = [{"in": m1.usage.input_tokens, "out": m1.usage.output_tokens}]
            txt = "".join(b.text for b in m1.content if b.type == "text")
            try: subs = json.loads(re.search(r"\[.*\]", txt, re.S).group(0)); subs = [str(s) for s in subs][:8]
            except Exception: subs = [q["q"]]
            outs = []
            for w, sq in enumerate(subs):
                steps, ans, st = agent(sq, SYSTEM, cap=6); roles[f"worker{w}"] = steps; outs.append(f"Worker {w + 1} question: {sq}\nWorker {w + 1} references: {ans}")
            msgs = [{"role": "user", "content": q["q"] + "\n\n" + "\n\n".join(outs)}]
            m2 = call(system=SUP2, tools=TOOLS[1:], messages=msgs); ans = None; st = "no_submit"
            if m2 is not None:
                roles["supervisor_final"] = [{"in": m2.usage.input_tokens, "out": m2.usage.output_tokens}]
                for b in m2.content:
                    if b.type == "tool_use" and b.name == "submit": ans = sorted(set(b.input.get("references", []))); st = "submitted"
        ok = ans is not None and set(ans) == set(q["gold"])
        return {"q": qi, "rep": rep, "arm": arm, "status": st, "roles": roles, "ok": ok, "n": q["n"], "workers": sum(1 for k in roles if k.startswith("worker")), "answer": ans, "gold": q["gold"]}
    jobs = [(qi, r, a) for qi in range(len(Q)) for r in range(REPEATS) for a in ("S",)]
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(run, jobs))
    OUT.write_text(json.dumps({"model": MODEL, "results": res})); print("saved", OUT.name, "runs", len(res), "api_error", sum(r["status"] == "api_error" for r in res))
if __name__ == "__main__": main()
