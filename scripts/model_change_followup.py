#!/usr/bin/env python3
"""Chapter 35 follow-up, REAL calls. Same 120 questions, contract and K=3 as model_change_lab.py, claude-haiku-5-5, thinking disabled, one repair of the B1 setting:
  B3  thinking disabled, max_tokens 200, and a sentence in the prompt: the reply must start with the JSON object, with no text before or after it
Only B3 is run. Prefill and other thinking budgets are not tested. Errors are recorded."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.retrieval import BM25
from costlab.ladder import clauses, make_questions
OUT = Path(__file__).resolve().parents[1] / "runs" / "model-change-followup-2026-11-11.json"
B = "claude-haiku-5-5"
SYS = "You answer questions about the Fieldstone support handbook using only the clauses supplied."
TAIL = ('Reply with a single JSON object only, no other text and no code fences, with keys "ref" (the FS reference code) and "days" (the retention window as an integer). '
        'If the clauses do not contain what is needed, set both "ref" and "days" to null. The first character of your reply must be the opening brace and the last must be the closing brace: no reasoning, no explanation, nothing before or after the object.')
ARMS = {"B3": {"max_tokens": 200, "thinking": {"type": "disabled"}}}
def main():
    C = clauses(); bm = BM25([c["text"] for c in C]); Q = make_questions(120, 351)
    ctxs = ["\n".join(C[i]["text"] for i in bm.search(q["q"], 3)) for q in Q]
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic()
    def one(job):
        qi, arm, k = job; att = 0
        while True:
            att += 1; t0 = time.time()
            try:
                m = cl.messages.create(model=B, system=SYS, messages=[{"role": "user", "content": f"Clauses:\n{ctxs[qi]}\n\nQuestion: {Q[qi]['q']}\n{TAIL}"}], **ARMS[arm])
                return {"q": qi, "arm": arm, "k": k, "in": m.usage.input_tokens, "out": m.usage.output_tokens, "text": "".join(b.text for b in m.content if b.type == "text"), "stop": m.stop_reason, "secs": round(time.time() - t0, 3), "error": None}
            except (APIStatusError, APIConnectionError) as e:
                code = getattr(e, "status_code", None)
                if att < 4 and (code in (429, 500, 502, 503, 529) or code is None): time.sleep(2 * att); continue
                return {"q": qi, "arm": arm, "k": k, "in": 0, "out": 0, "text": "", "stop": None, "secs": None, "error": f"{type(e).__name__}: {str(e)[:160]}"}
    jobs = [(qi, a, k) for qi in range(len(Q)) for a in ARMS for k in range(3)]
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps({"arms": {a: [B, kw] for a, kw in ARMS.items()}, "questions": Q, "results": res}))
    print("saved", OUT.name, "calls", len(res), "errors", sum(r["error"] is not None for r in res))
if __name__ == "__main__": main()
