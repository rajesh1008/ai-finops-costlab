#!/usr/bin/env python3
"""Chapter 23 lab. REAL calls, claude-haiku-4-5. The SYNTHETIC 160-clause handbook of Chapter 18 as the knowledge base, a pure-python BM25 retriever,
one clause per chunk. 40 questions of the form 'Which reference(s) apply to workspace tier T with a retention window of D days?' Gold = every clause with that
tier and window (1 to 2 clauses). k in {1, 2, 4, 8, 16} plus the whole handbook in context (no retrieval). Recall@k needs no API. Max tokens 400 (an earlier run at 80 truncated the long-context replies; see Chapter 23). A reply that gives only clause numbers is mapped to its reference (the first version of the scorer missed those and understated k=8 and the full context). Never prints the key."""
import os, sys, json, time, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
from costlab.retrieval import BM25
RUNS = Path(__file__).resolve().parents[1] / "runs"; OUT = RUNS / "retrieval-k-lab-2026-11-10.json"
MODEL = "claude-haiku-4-5-20251001"
def clauses():
    out = []
    for i in range(1, 161):
        out.append({"i": i, "tier": i % 7 + 1, "days": 30 + (i % 12) * 15, "ref": f"FS-{1000 + i * 13}",
                    "text": f"Clause {i}. For workspace tier {i % 7 + 1}, a support agent must verify the account owner, record reference FS-{1000 + i * 13}, and confirm the retention window of {30 + (i % 12) * 15} days before describing any export or deletion procedure."})
    return out
def parse(t):
    """References named in a reply. Accepts FS codes, 'Clause N', or bare clause numbers (the model sometimes answers '21, 105'), each mapped to its FS code."""
    fs = set(re.findall(r"FS-\d+", t))
    if fs: return fs
    nums = re.findall(r"[Cc]lause (\d+)", t) or re.findall(r"\b(\d{1,3})\b", t)
    return {f"FS-{1000 + int(n) * 13}" for n in nums if 1 <= int(n) <= 160}
def main():
    C = clauses(); bm = BM25([c["text"] for c in C])
    pairs = sorted({(c["tier"], c["days"]) for c in C}); import random; random.Random(23).shuffle(pairs); pairs = pairs[:40]
    Q = []
    for t, d in pairs:
        gold = [c["ref"] for c in C if c["tier"] == t and c["days"] == d]
        Q.append({"q": f"Which reference or references apply when the workspace tier is {t} and the retention window is {d} days? List every reference that applies.", "gold": gold, "tier": t, "days": d})
    rec = {}
    for k in (1, 2, 4, 8, 16):
        r = 0
        for q in Q:
            hit = {C[i]["ref"] for i in bm.search(q["q"], k)}; r += all(g in hit for g in q["gold"])
        rec[k] = r / len(Q)
    print("recall@k (all gold clauses retrieved):", rec)
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    c = Anthropic()
    def ctx(q, k):
        if k == 0: return "\n".join(x["text"] for x in C)
        return "\n".join(C[i]["text"] for i in bm.search(q["q"], k))
    jobs = [(q, k) for q in Q for k in (1, 2, 4, 8, 16, 0)]
    def run(job):
        q, k = job
        for a in range(4):
            try:
                m = c.messages.create(model=MODEL, max_tokens=400, system="Answer only from the clauses given. Reply with the reference codes only, comma separated.",
                                      messages=[{"role": "user", "content": "Clauses:\n" + ctx(q, k) + "\n\nQuestion: " + q["q"]}])
                t = "".join(x.text for x in m.content if x.type == "text"); got = parse(t)
                return {"k": k, "tier": q["tier"], "days": q["days"], "gold": q["gold"], "got": sorted(got), "ok": got == set(q["gold"]), "in": m.usage.input_tokens, "out": m.usage.output_tokens, "stop": m.stop_reason, "cut": m.stop_reason == "max_tokens", "text": t[:160]}
            except Exception: time.sleep(2 + 3 * a)
        return {"k": k, "ok": None}
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(run, jobs))
    OUT.write_text(json.dumps({"recall": rec, "results": res})); print("saved", OUT.name, "failed:", sum(1 for r in res if r["ok"] is None))
if __name__ == "__main__": main()
