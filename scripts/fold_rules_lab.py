#!/usr/bin/env python3
"""Ch7 / Ch19 lab (46th run). REAL calls. 13-turn session. Turns 1-6 each state one invented policy rule WITH an exception.
Turns 7-12 are unrelated filler. Turn 13 asks eight scenario questions that need the rules and their exceptions; graded by code.
Plain: full history resent each turn. Folded: after turn 6 the model writes a summary (max 400 tokens, one real counted call) and history is replaced.
8 sessions x (13 + 14) = 216 calls on claude-haiku-4-5. Key from env only, never printed."""
import os, sys, json, re
from pathlib import Path
M = "claude-haiku-4-5-20251001"; PIN, POUT = 1.0, 5.0
OUT = Path(__file__).resolve().parents[1] / "runs" / "fold-rules-lab-2026-11-13.jsonl"
SYS = "You are an operations policy assistant at an invented company. Answer in one or two sentences unless told otherwise."
def params(s):
    return dict(L1=500 + 100 * s, L2=150 + 25 * s, D=14 + 2 * s, R=100 + 20 * s, P=15 + s, FEE=2, INV=2000, FREE=24, PAID=1 + s % 3)
def rules(s):
    p = params(s)
    return [
        f"Rule one. Purchases under ${p['L1']} need no approval, except software subscriptions, where the no-approval limit is ${p['L2']}.",
        f"Rule two. Refunds up to ${p['R']} are approved automatically if requested within {p['D']} days of purchase; after {p['D']} days every refund needs a manager, whatever the amount.",
        f"Rule three. Annual prepay earns 10 percent off list. Partner customers get {p['P']} percent off list instead. The two discounts never stack; the customer gets the larger one.",
        f"Rule four. Severity 1 tickets page the on-call engineer within {p['PAID']} hours on paid plans, but within {p['FREE']} hours on the free plan.",
        f"Rule five. A late-payment fee of {p['FEE']} percent of the invoice applies, but the first late payment each year is waived and only later ones are charged.",
        "Rule six. Customers in the EU are invoiced in EUR; every other customer is invoiced in USD, including customers in the UK.",
    ]
def questions(s):
    p = params(s)
    return [
        (f"A software subscription costs ${(p['L1'] + p['L2']) // 2}. Does it need approval? Answer yes or no.", "yes"),
        (f"A hardware purchase costs ${p['L1'] - 50}. Does it need approval? Answer yes or no.", "no"),
        (f"A refund of ${p['R'] - 10} is requested {p['D'] - 3} days after purchase. Is it approved automatically? Answer yes or no.", "yes"),
        (f"A refund of ${p['R'] - 10} is requested {p['D'] + 5} days after purchase. Is it approved automatically? Answer yes or no.", "no"),
        (f"A partner customer pays annually in advance for a list price of $1000. What is the price in dollars? Answer with a number only.", str(1000 - 10 * p['P'])),
        ("A free-plan customer opens a severity 1 ticket. Within how many hours is on-call paged? Answer with a number only.", str(p['FREE'])),
        (f"A customer pays late twice this year on ${p['INV']} invoices. What is the total fee charged, in dollars? Answer with a number only.", str(p['INV'] * p['FEE'] // 100)),
        ("A customer in the UK. Which currency is the invoice in? Answer with the three-letter code.", "usd"),
    ]
FILL = ["travel expense policies", "how office badges are issued", "what a purchase order is", "how a data retention schedule works", "what a service-level agreement is", "how a budget variance is explained"]
def txt(x): return "".join(b.text for b in x.content if b.type == "text").strip()
def call(cl, msgs, mt, system=SYS):
    r = cl.messages.create(model=M, max_tokens=mt, system=system, messages=msgs)
    return txt(r), {"in": r.usage.input_tokens, "out": r.usage.output_tokens, "stop": r.stop_reason}
def grade(answer, gold):
    """Parse lines of the form 'N: value'; return list of booleans, one per gold item."""
    got = {}
    for line in answer.splitlines():
        m = re.match(r"\W*(\d+)\s*[:.)-]\s*(.+)", line)
        if m: got[int(m.group(1))] = m.group(2).strip().lower()
    res = []
    for i, g in enumerate(gold, 1):
        v = got.get(i, "")
        v = v.replace("$", "").replace(",", "").strip(" .*")
        if g.isdigit(): res.append(bool(re.match(rf"^{g}(\.0+)?\b", v)))
        else: res.append(v.startswith(g))
    return res
def run(cl, s, fold):
    hist, rows, summ = [], [], None
    qs = questions(s)
    for i in range(13):
        if i < 6: q = rules(s)[i] + " Acknowledge in one sentence."
        elif i < 12: q = f"Unrelated: explain {FILL[i - 6]}, in brief."
        else: q = "Answer these using the rules I gave you, one line each in the form 'N: answer', nothing else.\n" + "\n".join(f"{n}. {t}" for n, (t, _) in enumerate(qs, 1))
        msgs = hist + [{"role": "user", "content": q}]
        a, u = call(cl, msgs, 120 if i == 12 else 90); u["turn"] = i + 1; rows.append(u)
        hist = msgs + [{"role": "assistant", "content": a}]
        if fold and i == 5:
            sm, su = call(cl, hist + [{"role": "user", "content": "Write a summary of this session for a colleague who will answer questions from it. Keep every rule, number and exception exactly."}], 400)
            su["turn"] = "summary"; rows.append(su); summ = sm
            hist = [{"role": "user", "content": "Summary of the session so far: " + sm}, {"role": "assistant", "content": "Understood."}]
    ok = grade(a, [g for _, g in qs])
    return {"session": s, "mode": "folded" if fold else "plain", "rows": rows, "correct": sum(ok), "per_question": ok, "summary": summ, "final": a}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); out = []
    for s in range(8):
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
              "correct of 8 per session", [r["correct"] for r in g], "mean", round(sum(r["correct"] for r in g) / len(g), 2))
        print("  per-question correct counts:", [sum(r["per_question"][q] for r in g) for q in range(8)])
        if mode == "folded":
            print("  summary output tokens:", [next(x["out"] for x in r["rows"] if x["turn"] == "summary") for r in g], "truncated:", sum(x["stop"] == "max_tokens" for r in g for x in r["rows"] if x["turn"] == "summary"))
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
