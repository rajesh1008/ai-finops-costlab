#!/usr/bin/env python3
"""Chapter 28 lab, REAL calls. 300 SYNTHETIC handbook questions (seed 281, templates A, B, C). Incumbent: claude-haiku-4-5, ONE call with the top 3 clauses pasted in. Candidate: claude-haiku-5-5, same prompt, same clauses.
Both answers are scored by the exact scorer in costlab.ladder. Errors are recorded, not retried silently (429 and 5xx get three retries and the attempt count is stored). No temperature argument."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.retrieval import BM25
from costlab.ladder import clauses, make_questions, score
OUT = Path(__file__).resolve().parents[1] / "runs" / "shadow-lab-2026-11-10.json"
A, B = "claude-haiku-4-5-20251001", "claude-haiku-5-5"
SYS = "You answer questions about the Fieldstone support handbook using only the clauses supplied. Reply in one short sentence. If the supplied clauses do not contain what is needed, say you cannot answer."
def main():
    C = clauses(); bm = BM25([c["text"] for c in C]); Q = make_questions(300, 281)
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic()
    def one(job):
        qi, model = job; q = Q[qi]; ctx = "\n".join(C[i]["text"] for i in bm.search(q["q"], 3)); att = 0
        while True:
            att += 1
            try:
                m = cl.messages.create(model=model, max_tokens=120, system=SYS, messages=[{"role": "user", "content": f"Clauses:\n{ctx}\n\nQuestion: {q['q']}"}])
                t = "".join(b.text for b in m.content if b.type == "text")
                return {"q": qi, "model": model, "in": m.usage.input_tokens, "out": m.usage.output_tokens, "answer": t, "ok": score(t, q["gold"]), "error": None, "attempts": att}
            except (APIStatusError, APIConnectionError) as e:
                code = getattr(e, "status_code", None)
                if att < 4 and (code in (429, 500, 502, 503, 529) or code is None): time.sleep(2 * att); continue
                return {"q": qi, "model": model, "in": 0, "out": 0, "answer": "", "ok": False, "error": f"{type(e).__name__}: {str(e)[:160]}", "attempts": att}
    jobs = [(qi, m) for qi in range(len(Q)) for m in (A, B)]
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps({"models": {"incumbent": A, "candidate": B}, "questions": Q, "results": res}))
    print("saved", OUT.name, "runs", len(res), "errors", sum(r["error"] is not None for r in res))
if __name__ == "__main__": main()
