#!/usr/bin/env python3
"""Chapter 16 lab. Real calls, Haiku 4.5, on 100 SYNTHETIC tickets with known labels (seed 16).
Designs: A rules only; B model for every ticket; C rules first, model only when no rule fires.
Never prints the key."""
import os, sys, json
from pathlib import Path
from anthropic import Anthropic
from costlab.gateway import Meter
from costlab.triage import make_tickets, rule_label, LABELS

MODEL = "claude-haiku-4-5-20251001"
LOG = Path(__file__).resolve().parents[1] / "runs" / "triage-2026-11-10.jsonl"
SYSTEM = ("Classify the customer message into exactly one of: billing, password, shipping, cancel, other. "
          "Reply with the single label word only.")

def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    if LOG.exists(): LOG.unlink()
    meter = Meter(Anthropic(), LOG, product="triage-lab")
    tickets = make_tickets()
    llm = {}
    for t in tickets:
        msg = meter.call(model=MODEL, session_id=f"t{t['id']}", step=1, feature="triage", max_tokens=8,
                         system=SYSTEM, messages=[{"role": "user", "content": t["text"]}])
        w = "".join(b.text for b in msg.content if b.type == "text").strip().lower().split()
        lab = w[0].strip(".,") if w else ""
        llm[t["id"]] = lab if lab in LABELS else "other"
    recs = [json.loads(l) for l in open(LOG)]
    per_call = sum(r["estimated_cost_usd"] for r in recs) / len(recs)
    avg_in = sum(r["input_tokens"] for r in recs) / len(recs); avg_out = sum(r["output_tokens"] for r in recs) / len(recs)
    n = len(tickets)
    def acc(f): return sum(f(t) == t["label"] for t in tickets) / n
    A = lambda t: rule_label(t["text"]) or "unrouted"
    B = lambda t: llm[t["id"]]
    C = lambda t: rule_label(t["text"]) or llm[t["id"]]
    fired = sum(rule_label(t["text"]) is not None for t in tickets)
    hard = [t for t in tickets if rule_label(t["text"]) is None or True]
    wrong_rules = sum(1 for t in tickets if rule_label(t["text"]) not in (None, t["label"]))
    print(f"tickets={n} avg_input_tokens={avg_in:.0f} avg_output_tokens={avg_out:.1f} measured_cost_per_call=${per_call:.6f}")
    print(f"rules fired on {fired}/{n}; fired and wrong {wrong_rules}")
    print(f"A rules only      accuracy {acc(A):.1%}  (unrouted count {n - fired})  cost per ticket $0")
    print(f"B model always    accuracy {acc(B):.1%}  cost per ticket ${per_call:.6f}  calls {n}")
    print(f"C rules then model accuracy {acc(C):.1%}  cost per ticket ${per_call * (n - fired) / n:.6f}  calls {n - fired}")
    for name, f in (("A", A), ("B", B), ("C", C)):
        errs = [(t["text"][:60], t["label"], f(t)) for t in tickets if f(t) != t["label"]]
        print(f"errors {name}: {len(errs)}")
        for e in errs[:6]: print("   ", e)
    for vol in (100_000, 1_000_000):
        print(f"at {vol:,} tickets/month (ASSUMED volume): B ${per_call*vol:,.0f}  C ${per_call*vol*(n-fired)/n:,.0f}")

if __name__ == "__main__":
    main()
