#!/usr/bin/env python3
"""Chapter 31 lab, REAL calls. 60 SYNTHETIC handbook questions (seed 311, templates A, B, C), top-3 BM25 clauses pasted in. Three output contracts (plain sentence, strict JSON, XML tags), each on claude-haiku-4-5 and claude-haiku-5-5.
Two models of one vendor stand in for two vendors: this tests prompt and format portability and the shape of a switch, not cross-vendor behaviour. Latency is wall time per call with 6 parallel workers (NOT a latency benchmark).
Also a failover probe: an unknown model name first, then the fallback; the added wall time is recorded. Errors are recorded. No temperature argument."""
import os, sys, json, time, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.retrieval import BM25
from costlab.ladder import clauses, make_questions, score
OUT = Path(__file__).resolve().parents[1] / "runs" / "portability-lab-2026-11-11.json"
A, B = "claude-haiku-4-5-20251001", "claude-haiku-5-5"
SYS = "You answer questions about the Fieldstone support handbook using only the clauses supplied."
TAIL = {"plain": "Reply in one short sentence.",
        "json": 'Reply with a single JSON object only, no other text, with keys "ref" (the FS reference code or null if not asked) and "days" (the retention window as an integer). Do not use code fences.',
        "xml": "Reply with exactly this and nothing else: <answer><ref>FS reference code or none</ref><days>integer</days></answer>"}
def parse(fmt, t, gold):
    """Returns (parsed_ok, correct). plain: parsed always, correct by scorer. json: strict json.loads on the whole reply. xml: strict regex on whole reply."""
    t = (t or "").strip()
    if fmt == "plain": return True, score(t, gold)
    if fmt == "json":
        try: o = json.loads(t)
        except Exception: return False, False
        vals = [str(o.get("ref")), str(o.get("days"))]
    else:
        m = re.fullmatch(r"<answer><ref>(.*?)</ref><days>(.*?)</days></answer>", t, re.S)
        if not m: return False, False
        vals = [m.group(1).strip(), m.group(2).strip()]
    ok = all(g in vals for g in gold)
    return True, ok
def main():
    C = clauses(); bm = BM25([c["text"] for c in C]); Q = make_questions(60, 311)
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic()
    def one(job):
        qi, model, fmt = job; q = Q[qi]; ctx = "\n".join(C[i]["text"] for i in bm.search(q["q"], 3)); att = 0
        while True:
            att += 1; t0 = time.time()
            try:
                m = cl.messages.create(model=model, max_tokens=200, system=SYS, messages=[{"role": "user", "content": f"Clauses:\n{ctx}\n\nQuestion: {q['q']}\n{TAIL[fmt]}"}])
                t = "".join(b.text for b in m.content if b.type == "text"); p, ok = parse(fmt, t, q["gold"])
                return {"q": qi, "model": model, "fmt": fmt, "in": m.usage.input_tokens, "out": m.usage.output_tokens, "text": t, "parsed": p, "ok": ok, "secs": round(time.time() - t0, 3), "stop": m.stop_reason, "error": None, "attempts": att}
            except (APIStatusError, APIConnectionError) as e:
                code = getattr(e, "status_code", None)
                if att < 4 and (code in (429, 500, 502, 503, 529) or code is None): time.sleep(2 * att); continue
                return {"q": qi, "model": model, "fmt": fmt, "in": 0, "out": 0, "text": "", "parsed": False, "ok": False, "secs": None, "stop": None, "error": f"{type(e).__name__}: {str(e)[:160]}", "attempts": att}
    jobs = [(qi, m, f) for qi in range(len(Q)) for m in (A, B) for f in ("plain", "json", "xml")]
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
    # failover probe, sequential
    probe = []
    for k in range(10):
        q = Q[k]; ctx = "\n".join(C[i]["text"] for i in bm.search(q["q"], 3)); msg = [{"role": "user", "content": f"Clauses:\n{ctx}\n\nQuestion: {q['q']}\nReply in one short sentence."}]
        t0 = time.time(); err = None
        try: cl.messages.create(model="claude-haiku-9-9-not-a-model", max_tokens=50, system=SYS, messages=msg)
        except Exception as e: err = f"{type(e).__name__}: {str(e)[:100]}"
        t1 = time.time(); cl.messages.create(model=B, max_tokens=60, system=SYS, messages=msg); t2 = time.time()
        probe.append({"k": k, "fail_secs": round(t1 - t0, 3), "fallback_secs": round(t2 - t1, 3), "err": err})
    OUT.write_text(json.dumps({"models": [A, B], "questions": Q, "results": res, "failover": probe}))
    print("saved", OUT.name, "runs", len(res), "errors", sum(r["error"] is not None for r in res))
if __name__ == "__main__": main()
