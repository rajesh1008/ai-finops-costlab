#!/usr/bin/env python3
"""Chapter 27 lab, REAL calls (Anthropic API, key from the environment, never printed). 120 SYNTHETIC handbook questions (templates A, B, C; seed 271).
Rung `full`: claude-haiku-4-5 agent with a search tool (BM25 top 3), step cap 8, answers in plain text. Rung `reduced`: ONE call, claude-haiku-5-5, top 3 clauses for the question pasted into the prompt, max 120 output tokens.
Errors are recorded in the result (status 'api_error' plus the exception text); only 429 and 5xx are retried, three times, and the number of attempts is recorded. No temperature argument is passed."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.retrieval import BM25
from costlab.ladder import clauses, make_questions, score
RUNS = Path(__file__).resolve().parents[1] / "runs"; OUT = RUNS / "ladder-lab-2026-11-10.json"
FULL, RED = "claude-haiku-4-5-20251001", "claude-haiku-5-5"; CAP = 8
TOOLS = [{"name": "search", "description": "Search the support handbook. Returns the 3 best matching clauses.", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}]
SYS_FULL = "You answer questions about the Fieldstone support handbook. Use the search tool to find clauses. When you have what you need, reply in one short sentence with the answer. Only state codes and numbers you have seen in search results."
SYS_RED = "You answer questions about the Fieldstone support handbook using only the clauses supplied. Reply in one short sentence. If the supplied clauses do not contain what is needed, say you cannot answer."
cl = None
def call(**kw):
    attempts = 0
    while True:
        attempts += 1
        try: return cl.messages.create(**kw), attempts, None
        except (APIStatusError, APIConnectionError) as e:
            code = getattr(e, "status_code", None)
            if attempts < 4 and (code in (429, 500, 502, 503, 529) or code is None): time.sleep(2 * attempts); continue
            return None, attempts, f"{type(e).__name__}: {str(e)[:160]}"
def main():
    global cl
    C = clauses(); bm = BM25([c["text"] for c in C]); Q = make_questions(120, 271)
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic()
    def full(qi):
        q = Q[qi]; msgs = [{"role": "user", "content": q["q"]}]; steps = []; text = ""; status = "cap"; err = None
        for s in range(CAP):
            m, att, err = call(model=FULL, max_tokens=400, system=SYS_FULL, tools=TOOLS, messages=msgs)
            if m is None: status = "api_error"; break
            steps.append({"in": m.usage.input_tokens, "out": m.usage.output_tokens}); msgs.append({"role": "assistant", "content": m.content})
            uses = [b for b in m.content if b.type == "tool_use"]
            if not uses: text = "".join(b.text for b in m.content if b.type == "text"); status = "answered"; break
            msgs.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": u.id, "content": "\n".join(C[i]["text"] for i in bm.search(str(u.input.get("query", "")), 3))} for u in uses]})
        return {"q": qi, "rung": "full", "steps": steps, "status": status, "answer": text, "ok": score(text, q["gold"]) if status == "answered" else False, "error": err}
    def reduced(qi):
        q = Q[qi]; ctx = "\n".join(C[i]["text"] for i in bm.search(q["q"], 3))
        m, att, err = call(model=RED, max_tokens=120, system=SYS_RED, messages=[{"role": "user", "content": f"Clauses:\n{ctx}\n\nQuestion: {q['q']}"}])
        if m is None: return {"q": qi, "rung": "reduced", "steps": [], "status": "api_error", "answer": "", "ok": False, "error": err}
        text = "".join(b.text for b in m.content if b.type == "text")
        return {"q": qi, "rung": "reduced", "steps": [{"in": m.usage.input_tokens, "out": m.usage.output_tokens}], "status": "answered", "answer": text, "ok": score(text, q["gold"]), "error": None, "attempts": att}
    jobs = [(f, qi) for qi in range(len(Q)) for f in (full, reduced)]
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(lambda j: j[0](j[1]), jobs))
    OUT.write_text(json.dumps({"models": {"full": FULL, "reduced": RED}, "questions": Q, "results": res}))
    print("saved", OUT.name, "runs", len(res), "api_error", sum(r["status"] == "api_error" for r in res))
if __name__ == "__main__": main()
