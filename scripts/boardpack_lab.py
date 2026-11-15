#!/usr/bin/env python3
"""Chapter 40 lab, REAL calls (Anthropic API, key from the environment, never printed). 200 SYNTHETIC handbook questions (templates A, B, C; seed 401) answered in ONE call each with the BM25 top 3 clauses pasted in,
by claude-haiku-4-5 (M1) and by claude-haiku-5-5 with thinking disabled (M2): 400 calls. Outcome classes are scored by string match: correct, decline (the reply says it cannot answer), wrong (a confident wrong answer).
Records the usage fields the bill is made from. Output runs/boardpack-lab-2026-11-11.json."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.retrieval import BM25
from costlab.ladder import clauses, make_questions, score
OUT = Path(__file__).resolve().parents[1] / "runs" / "boardpack-lab-2026-11-11.json"
MODELS = {"M1": ("claude-haiku-4-5-20251001", {}), "M2": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}})}
SYS = "You answer questions about the Fieldstone support handbook using only the clauses supplied. Reply in one short sentence. If the supplied clauses do not contain what is needed, say you cannot answer."
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); C = clauses(); bm = BM25([c["text"] for c in C]); Q = make_questions(200, 401)
    jobs = [(i, q, m) for i, q in enumerate(Q) for m in MODELS]
    def one(j):
        i, q, m = j; model, kw = MODELS[m]; top = bm.search(q["q"], 3)
        ctx = "\n".join(C[t]["text"] for t in top)
        err = None
        for att in range(4):
            try:
                r = cl.messages.create(model=model, max_tokens=200, system=SYS, messages=[{"role": "user", "content": f"Clauses:\n{ctx}\n\nQuestion: {q['q']}"}], **kw)
                txt = "".join(b.text for b in r.content if b.type == "text")
                return {"i": i, "t": q["t"], "m": m, "in": r.usage.input_tokens, "out": r.usage.output_tokens, "text": txt[:200], "ok": score(txt, q["gold"]), "error": None}
            except (APIStatusError, APIConnectionError) as e:
                err = f"{type(e).__name__}:{getattr(e, 'status_code', None)}"; time.sleep(2 * (att + 1))
        return {"i": i, "t": q["t"], "m": m, "in": 0, "out": 0, "text": "", "ok": False, "error": err}
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps({"results": res})); print("saved", OUT.name, len(res), "errors", sum(1 for r in res if r["error"]))
if __name__ == "__main__": main()
