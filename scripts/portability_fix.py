#!/usr/bin/env python3
"""Chapter 31 follow-up, REAL calls: the 22 empty strict-format replies of claude-haiku-5-5 hit max_tokens 200. Same 60 questions and prompts as portability_lab.py, json and xml contracts, with thinking explicitly disabled (as in the Chapter 29 judge lab), and with max_tokens 600 and default thinking."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
from costlab.retrieval import BM25
from costlab.ladder import clauses, make_questions
sys.path.insert(0, str(Path(__file__).parent)); from portability_lab import SYS, TAIL, parse, B
OUT = Path(__file__).resolve().parents[1] / "runs" / "portability-fix-2026-11-11.json"
def main():
    C = clauses(); bm = BM25([c["text"] for c in C]); Q = make_questions(60, 311); cl = Anthropic()
    def one(job):
        qi, fmt, mode = job; q = Q[qi]; ctx = "\n".join(C[i]["text"] for i in bm.search(q["q"], 3))
        kw = {"max_tokens": 200, "thinking": {"type": "disabled"}} if mode == "nothink" else {"max_tokens": 600}
        for att in range(4):
            try:
                m = cl.messages.create(model=B, system=SYS, messages=[{"role": "user", "content": f"Clauses:\n{ctx}\n\nQuestion: {q['q']}\n{TAIL[fmt]}"}], **kw)
                t = "".join(b.text for b in m.content if b.type == "text"); p, ok = parse(fmt, t, q["gold"])
                return {"q": qi, "fmt": fmt, "mode": mode, "in": m.usage.input_tokens, "out": m.usage.output_tokens, "parsed": p, "ok": ok, "stop": m.stop_reason, "error": None}
            except Exception as e: time.sleep(2 * (att + 1)); err = f"{type(e).__name__}: {str(e)[:120]}"
        return {"q": qi, "fmt": fmt, "mode": mode, "error": err}
    jobs = [(qi, f, m) for qi in range(60) for f in ("json", "xml") for m in ("nothink", "think600")]
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps(res)); print("saved", OUT.name, "errors", sum(r["error"] is not None for r in res))
    from costlab.estimate import estimate_usd
    for f in ("json", "xml"):
        for mo in ("nothink", "think600"):
            rr = [r for r in res if r["error"] is None and r["fmt"] == f and r["mode"] == mo]
            c = sum(estimate_usd("anthropic:" + B, r["in"], r["out"]) for r in rr) / len(rr) * 1000
            print(f"{f:<5}{mo:<10} n={len(rr)} parsed {sum(r['parsed'] for r in rr)} correct {sum(r['ok'] for r in rr)} mean out {sum(r['out'] for r in rr)/len(rr):.1f} max_tokens stops {sum(r['stop']=='max_tokens' for r in rr)} $/1000 {c:.4f}")
if __name__ == "__main__": main()
