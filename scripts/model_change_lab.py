#!/usr/bin/env python3
"""Chapter 35 lab, REAL calls. The model change that saved money: 120 SYNTHETIC handbook questions (seed 351, templates A, B, C), top-3 BM25 clauses pasted in, a strict-JSON contract
(ref and days, null for both when the clauses do not hold the answer), K=3 samples per question per arm. Arms:
  A   claude-haiku-4-5-20251001, max_tokens 200 (the incumbent and its production config)
  B0  claude-haiku-5-5, max_tokens 200, default thinking (the config left unchanged by the swap)
  B1  claude-haiku-5-5, max_tokens 200, thinking disabled
  B2  claude-haiku-5-5, max_tokens 800, default thinking
Two models of one vendor stand in for an incumbent and a cheaper candidate. No temperature argument (the SDK rejects it for these models). Errors are recorded, never hidden."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.retrieval import BM25
from costlab.ladder import clauses, make_questions
OUT = Path(__file__).resolve().parents[1] / "runs" / "model-change-lab-2026-11-11.json"
A, B = "claude-haiku-4-5-20251001", "claude-haiku-5-5"
ARMS = {"A": (A, {"max_tokens": 200}), "B0": (B, {"max_tokens": 200}), "B1": (B, {"max_tokens": 200, "thinking": {"type": "disabled"}}), "B2": (B, {"max_tokens": 800})}
SYS = "You answer questions about the Fieldstone support handbook using only the clauses supplied."
TAIL = ('Reply with a single JSON object only, no other text and no code fences, with keys "ref" (the FS reference code) and "days" (the retention window as an integer). '
        'If the clauses do not contain what is needed, set both "ref" and "days" to null.')
K = 3
def main():
    C = clauses(); bm = BM25([c["text"] for c in C]); Q = make_questions(120, 351)
    ctxs = []
    for q in Q:
        idx = bm.search(q["q"], 3); ctxs.append((idx, "\n".join(C[i]["text"] for i in idx)))
    for q, (idx, _) in zip(Q, ctxs): q["answerable"] = any(C[i]["i"] in q["needs"] for i in idx)
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic()
    def one(job):
        qi, arm, k = job; model, kw = ARMS[arm]; q = Q[qi]; att = 0
        while True:
            att += 1; t0 = time.time()
            try:
                m = cl.messages.create(model=model, system=SYS, messages=[{"role": "user", "content": f"Clauses:\n{ctxs[qi][1]}\n\nQuestion: {q['q']}\n{TAIL}"}], **kw)
                t = "".join(b.text for b in m.content if b.type == "text")
                return {"q": qi, "arm": arm, "k": k, "in": m.usage.input_tokens, "out": m.usage.output_tokens, "text": t, "stop": m.stop_reason, "secs": round(time.time() - t0, 3), "error": None, "attempts": att}
            except (APIStatusError, APIConnectionError) as e:
                code = getattr(e, "status_code", None)
                if att < 4 and (code in (429, 500, 502, 503, 529) or code is None): time.sleep(2 * att); continue
                return {"q": qi, "arm": arm, "k": k, "in": 0, "out": 0, "text": "", "stop": None, "secs": None, "error": f"{type(e).__name__}: {str(e)[:160]}", "attempts": att}
    jobs = [(qi, a, k) for qi in range(len(Q)) for a in ARMS for k in range(K)]
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps({"arms": {a: [m, kw] for a, (m, kw) in ARMS.items()}, "K": K, "questions": Q, "results": res}))
    print("saved", OUT.name, "calls", len(res), "errors", sum(r["error"] is not None for r in res))
if __name__ == "__main__": main()
