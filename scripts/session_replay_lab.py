#!/usr/bin/env python3
"""Ch7 lab (44th run). REAL calls. A scripted 12-turn support session where every turn resends the full history (the stateless API).
Measures input tokens per turn from usage, compares with the quadratic prediction, and compares to a 'summarise at turn 6' variant.
3 sessions x (12 plain + 12 with a folded history) = 72 calls max. Cap 80 output tokens. Model claude-haiku-4-5-20251001. Key from env only."""
import os, sys, json
from pathlib import Path
M = "claude-haiku-4-5-20251001"; PIN, POUT = 1.0, 5.0
OUT = Path(__file__).resolve().parents[1] / "runs" / "session-replay-lab-2026-11-13.jsonl"
SYS = "You are a billing support assistant for an invented software company. Answer in two or three sentences."
TOPICS = ["invoice line items", "seat overage", "annual versus monthly billing", "refund window", "tax on invoices", "payment retries",
          "plan downgrade", "credit notes", "currency conversion", "purchase orders", "late fees", "account closure"]
def user_msg(i, s):
    return f"Question {i+1} of session {s+1}: explain how {TOPICS[i]} usually works for a small team, and one thing to check before contacting support."
def txt(x): return "".join(b.text for b in x.content if b.type == "text").strip()
def run_session(cl, s, fold_at=None):
    hist, rows, summary = [], [], None
    for i in range(12):
        msgs = list(hist) + [{"role": "user", "content": user_msg(i, s)}]
        r = cl.messages.create(model=M, max_tokens=80, system=SYS, messages=msgs)
        a = txt(r)
        rows.append({"turn": i + 1, "in": r.usage.input_tokens, "out": r.usage.output_tokens, "stop": r.stop_reason})
        hist = msgs + [{"role": "assistant", "content": a}]
        if fold_at and i + 1 == fold_at:
            hist = [{"role": "user", "content": "Summary of the session so far: the customer asked about " + ", ".join(TOPICS[:fold_at]) + "; each was answered briefly."},
                    {"role": "assistant", "content": "Understood."}]
    return rows
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); out = []
    for s in range(3):
        for mode, fold in (("plain", None), ("folded", 6)):
            try: out.append({"session": s, "mode": mode, "turns": run_session(cl, s, fold)})
            except Exception as e: out.append({"session": s, "mode": mode, "error": type(e).__name__ + ": " + str(e)[:160]})
    OUT.write_text("\n".join(json.dumps(x) for x in out) + "\n")
def summary(path=OUT):
    rows = [json.loads(l) for l in Path(path).read_text().splitlines()]; ok = [r for r in rows if "error" not in r]
    print("sessions", len(rows), "errors", len(rows) - len(ok))
    for mode in ("plain", "folded"):
        g = [r for r in ok if r["mode"] == mode]
        tin = [sum(t["in"] for t in r["turns"]) for r in g]; tout = [sum(t["out"] for t in r["turns"]) for r in g]
        mi, mo = sum(tin) / len(g), sum(tout) / len(g)
        print(mode, "n", len(g), "mean input tokens/session", round(mi, 1), "output", round(mo, 1), "cost $/session", round((mi * PIN + mo * POUT) / 1e6, 5))
        print("  mean input by turn:", [round(sum(r["turns"][k]["in"] for r in g) / len(g)) for k in range(12)])
        print("  truncated replies:", sum(t["stop"] == "max_tokens" for r in g for t in r["turns"]))
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
