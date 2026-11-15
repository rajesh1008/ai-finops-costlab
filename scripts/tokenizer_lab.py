#!/usr/bin/env python3
"""Chapter 30 lab, REAL calls (count_tokens endpoint, no generation). The 300 prompts of the Chapter 28 shadow lab (SYNTHETIC handbook, seed 281, top-3 BM25 clauses)
are counted on claude-haiku-4-5 and claude-haiku-5-5. Output tokens are read from the recorded shadow run (real calls). Answers: how much of a list-price cut reaches a task bill."""
import os, sys, json, statistics
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
from costlab.retrieval import BM25
from costlab.ladder import clauses, make_questions
RUNS = Path(__file__).resolve().parents[1] / "runs"; OUT = RUNS / "tokenizer-lab-2026-11-11.json"
A, B = "claude-haiku-4-5-20251001", "claude-haiku-5-5"
SYS = "You answer questions about the Fieldstone support handbook using only the clauses supplied. Reply in one short sentence. If the supplied clauses do not contain what is needed, say you cannot answer."
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    C = clauses(); bm = BM25([c["text"] for c in C]); Q = make_questions(300, 281); cl = Anthropic()
    def count(job):
        qi, model = job; ctx = "\n".join(C[i]["text"] for i in bm.search(Q[qi]["q"], 3))
        for att in range(4):
            try:
                r = cl.messages.count_tokens(model=model, system=SYS, messages=[{"role": "user", "content": f"Clauses:\n{ctx}\n\nQuestion: {Q[qi]['q']}"}])
                return {"q": qi, "model": model, "count": r.input_tokens}
            except Exception as e:
                err = f"{type(e).__name__}: {str(e)[:120]}"
        return {"q": qi, "model": model, "count": None, "error": err}
    jobs = [(qi, m) for qi in range(300) for m in (A, B)]
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(count, jobs))
    OUT.write_text(json.dumps(res)); print("saved", OUT.name, "errors", sum(r["count"] is None for r in res))
if __name__ == "__main__": main()
