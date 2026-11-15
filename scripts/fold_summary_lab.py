#!/usr/bin/env python3
"""Ch7/Ch19 lab (45th run). REAL calls. 12-turn support session; turns 1-6 each state one invented customer fact.
Plain: full history resent. Folded: after turn 6 the model itself writes a summary (one real call, counted), history is replaced by it.
Turn 12 asks the model to recall all six facts; graded by exact string match. 5 sessions x (12 + 13) = 125 calls. Key from env only."""
import os, sys, json
from pathlib import Path
M = "claude-haiku-4-5-20251001"; PIN, POUT = 1.0, 5.0
OUT = Path(__file__).resolve().parents[1] / "runs" / "fold-summary-lab-2026-11-13.jsonl"
SYS = "You are a billing support assistant for an invented software company. Answer in two or three sentences."
def facts(s):
    return [("purchase order", f"PO-{4100+s*37}"), ("seat count", f"{12+s*5} seats"), ("renewal date", f"{3+s} March"),
            ("account manager", ["Imran", "Wen", "Sofia", "Tariq", "Anneke"][s]), ("billing currency", ["CHF", "SGD", "BRL", "AED", "NOK"][s]),
            ("support ticket", f"TKT-{880+s*91}")]
FILL = ["late fees", "credit notes", "tax on invoices", "payment retries", "plan downgrade"]
def txt(x): return "".join(b.text for b in x.content if b.type == "text").strip()
def call(cl, msgs, mt, system=SYS):
    r = cl.messages.create(model=M, max_tokens=mt, system=system, messages=msgs)
    return txt(r), {"in": r.usage.input_tokens, "out": r.usage.output_tokens, "stop": r.stop_reason}
def run(cl, s, fold):
    fs = facts(s); hist, rows, summ = [], [], None
    for i in range(12):
        if i < 6: q = f"For the record, our {fs[i][0]} is {fs[i][1]}. Briefly, what is one thing to know about invoices on that basis?"
        elif i < 11: q = f"Unrelated: explain how {FILL[i-6]} usually work, in brief."
        else: q = "List our purchase order, seat count, renewal date, account manager, billing currency and support ticket exactly as I gave them, one per line."
        msgs = hist + [{"role": "user", "content": q}]
        a, u = call(cl, msgs, 160 if i == 11 else 80); u["turn"] = i + 1; rows.append(u)
        hist = msgs + [{"role": "assistant", "content": a}]
        if fold and i == 5:
            sm, su = call(cl, hist + [{"role": "user", "content": "Write a short summary of this session for a colleague taking over. Keep every customer detail they gave."}], 150)
            su["turn"] = "summary"; rows.append(su); summ = sm
            hist = [{"role": "user", "content": "Summary of the session so far: " + sm}, {"role": "assistant", "content": "Understood."}]
    got = sum(v.lower() in a.lower() for _, v in fs)
    return {"session": s, "mode": "folded" if fold else "plain", "rows": rows, "recalled": got, "summary_kept": (sum(v.lower() in summ.lower() for _, v in fs) if summ else None), "summary": summ, "final": a}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); out = []
    for s in range(5):
        for fold in (False, True):
            try: out.append(run(cl, s, fold))
            except Exception as e: out.append({"session": s, "mode": "folded" if fold else "plain", "error": type(e).__name__ + ": " + str(e)[:160]})
    OUT.write_text("\n".join(json.dumps(x) for x in out) + "\n")
def summary(path=OUT):
    rows = [json.loads(l) for l in Path(path).read_text().splitlines()]; ok = [r for r in rows if "error" not in r]
    print("sessions", len(rows), "errors", len(rows) - len(ok), "calls", sum(len(r["rows"]) for r in ok))
    for mode in ("plain", "folded"):
        g = [r for r in ok if r["mode"] == mode]
        if not g: continue
        ti = sum(x["in"] for r in g for x in r["rows"]) / len(g); to = sum(x["out"] for r in g for x in r["rows"]) / len(g)
        print(mode, "n", len(g), "input/session", round(ti, 1), "output/session", round(to, 1), "cost/session $", round((ti * PIN + to * POUT) / 1e6, 5),
              "mean recalled of 6:", round(sum(r["recalled"] for r in g) / len(g), 2), "per session", [r["recalled"] for r in g])
        if mode == "folded":
            print("  summary kept facts of 6:", [r["summary_kept"] for r in g], "summary output tokens:", [next(x["out"] for x in r["rows"] if x["turn"] == "summary") for r in g],
                  "summary truncated:", sum(x["stop"] == "max_tokens" for r in g for x in r["rows"] if x["turn"] == "summary"))
            print("  turn-12 input folded:", [next(x["in"] for x in r["rows"] if x["turn"] == 12) for r in g])
        else: print("  turn-12 input plain:", [next(x["in"] for x in r["rows"] if x["turn"] == 12) for r in g])
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
