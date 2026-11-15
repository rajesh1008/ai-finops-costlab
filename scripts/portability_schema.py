#!/usr/bin/env python3
"""Chapter 31 follow-up, REAL calls. The strict JSON contract of portability_lab.py has no way to say 'the clauses do not contain this'. Same 60 questions and prompts, JSON contract extended with an "answerable" boolean,
both models, haiku-5-5 with thinking disabled and max_tokens 200 (haiku-4-5 as before). Counts: confident wrong (answerable true and wrong), honest decline (answerable false), unparsed."""
import os, sys, json, time, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
from costlab.retrieval import BM25
from costlab.ladder import clauses, make_questions
sys.path.insert(0, str(Path(__file__).parent)); from portability_lab import SYS, A, B
OUT = Path(__file__).resolve().parents[1] / "runs" / "portability-schema-2026-11-11.json"
TAIL = 'Reply with a single JSON object only, no other text, no code fences, with keys "answerable" (true if the supplied clauses contain what is needed, otherwise false), "ref" (the FS reference code, or null) and "days" (the retention window as an integer, or null).'
def main():
    C = clauses(); bm = BM25([c["text"] for c in C]); Q = make_questions(60, 311); cl = Anthropic()
    def one(job):
        qi, model = job; q = Q[qi]; ctx = "\n".join(C[i]["text"] for i in bm.search(q["q"], 3)); kw = {"thinking": {"type": "disabled"}} if model == B else {}
        for att in range(4):
            try:
                m = cl.messages.create(model=model, max_tokens=200, system=SYS, messages=[{"role": "user", "content": f"Clauses:\n{ctx}\n\nQuestion: {q['q']}\n{TAIL}"}], **kw)
                t = "".join(b.text for b in m.content if b.type == "text").strip()
                try: o = json.loads(t); parsed = True
                except Exception: o = {}; parsed = False
                vals = [str(o.get("ref")), str(o.get("days"))]
                ok = parsed and o.get("answerable") is True and all(g in vals for g in q["gold"])
                return {"q": qi, "model": model, "in": m.usage.input_tokens, "out": m.usage.output_tokens, "parsed": parsed, "answerable": o.get("answerable"), "ok": ok, "text": t[:160], "stop": m.stop_reason, "error": None}
            except Exception as e: time.sleep(2 * (att + 1)); err = f"{type(e).__name__}: {str(e)[:120]}"
        return {"q": qi, "model": model, "error": err}
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, [(qi, m) for qi in range(60) for m in (A, B)]))
    OUT.write_text(json.dumps({"questions": Q, "results": res})); print("saved", OUT.name, "errors", sum(r["error"] is not None for r in res))
    for m in (A, B):
        rr = [r for r in res if r["error"] is None and r["model"] == m]
        wrong = [r for r in rr if r["parsed"] and r["answerable"] is True and not r["ok"]]; dec = [r for r in rr if r["parsed"] and r["answerable"] is False]
        c = [r for r in rr if Q[r["q"]]["t"] == "C"]
        print(f"{m[:16]:<17} n={len(rr)} parsed {sum(r['parsed'] for r in rr)} correct {sum(r['ok'] for r in rr)} confident-wrong {len(wrong)} declines {len(dec)} unparsed {sum(not r['parsed'] for r in rr)}; on type C (n={len(c)}): confident-wrong {sum(1 for r in c if r in wrong)} declines {sum(1 for r in c if r in dec)}; also declined on answerable A or B: {sum(1 for r in dec if Q[r['q']]['t'] != 'C')}")
if __name__ == "__main__": main()
