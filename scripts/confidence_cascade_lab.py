#!/usr/bin/env python3
"""Ch17 lab (37th run). REAL calls. Does a model's self-reported confidence separate its right answers from its wrong ones, so that a cascade could escalate only the doubtful calls? 12 tickets (6 plain, 6 that need a stated routing policy), 1 model, 3 repeats = 36 calls. Full replies stored. Key from env only."""
import os, sys, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
MODEL = "claude-haiku-4-5-20251001"
POLICY = ("Routing policy: BILLING = money, invoices, charges, refunds, plan prices. OUTAGE = the service is down or erroring for many users. ACCESS = login, permissions, SSO, API keys. "
 "If a ticket mentions two areas, route by the FIRST problem the customer says must be fixed before anything else. OTHER = anything else.")
T = [
 ("We were charged twice for March and the invoice does not match the dashboard.", "BILLING"),
 ("Nobody on my team can log in since the SSO change this morning.", "ACCESS"),
 ("Every call to the batch endpoint has returned 503 since 09:10 UTC.", "OUTAGE"),
 ("Can you send me the slide deck from last week's webinar?", "OTHER"),
 ("Our API key was rotated and the new one is rejected; also the March invoice looks high.", "ACCESS"),
 ("Please fix the double charge first. Separately, two of our users cannot sign in.", "BILLING"),
 ("The dashboard shows an outage for us but the status page is green; we need our refund for the downtime, and that is the main thing.", "BILLING"),
 ("Login works for admins but contractors get a permission error; they also say the service is slow today.", "ACCESS"),
 ("Is the Pro plan price going up in January? Also we saw timeouts yesterday.", "BILLING"),
 ("Timeouts across the EU region for all customers since noon; we also want a quote for more seats.", "OUTAGE"),
 ("Our auditor asks for a statement of how you store invoices. Nothing is broken.", "OTHER"),
 ("We cannot see the usage export, and the refund you promised last week has not arrived. The export matters most.", "ACCESS"),
]
OUT = Path(__file__).resolve().parents[1] / "runs" / "confidence-cascade-lab-2026-11-13.jsonl"
def one(a):
    cl, ti, rep = a
    p = POLICY + "\n\nTicket: " + T[ti][0] + "\n\nReply on one line in the form LABEL | CONFIDENCE where LABEL is BILLING, OUTAGE, ACCESS or OTHER and CONFIDENCE is an integer from 0 to 100 giving the chance you are right."
    x = cl.messages.create(model=MODEL, max_tokens=300, messages=[{"role": "user", "content": p}])
    r = "".join(b.text for b in x.content if b.type == "text")
    lab, conf = None, None
    try:
        a_, b_ = r.split("|"); lab = a_.strip().upper(); conf = int("".join(c for c in b_ if c.isdigit()))
    except Exception: pass
    return {"task": ti, "rep": rep, "input": x.usage.input_tokens, "out": x.usage.output_tokens, "label": lab, "conf": conf, "ok": lab == T[ti][1], "plain": ti < 4, "reply": r}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(cl, t, r) for t in range(len(T)) for r in range(3)]
    def safe(j):
        try: return one(j)
        except Exception as e: return {"task": j[1], "rep": j[2], "error": type(e).__name__ + ": " + str(e)[:160]}
    with ThreadPoolExecutor(6) as ex: rows = list(ex.map(safe, jobs))
    OUT.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
def summary():
    rows = [json.loads(l) for l in OUT.read_text().splitlines()]; good = [r for r in rows if "error" not in r]
    print("calls", len(rows), "errors", len(rows) - len(good), "unparsed", sum(r["conf"] is None for r in good))
    for nm, sel in (("plain", True), ("policy", False)):
        rs = [r for r in good if r["plain"] == sel]
        print(nm, "n", len(rs), "correct", sum(r["ok"] for r in rs), "mean_conf", sum(r["conf"] or 0 for r in rs) / max(len(rs), 1))
    ws = [r for r in good if not r["ok"]]; rt = [r for r in good if r["ok"]]
    print("wrong confs", sorted(r["conf"] for r in ws)); print("right conf min/mean", min(r["conf"] for r in rt), sum(r["conf"] for r in rt) / len(rt))
    for th in (50, 70, 80, 85, 90, 95):
        esc = [r for r in good if r["conf"] < th]; kept = [r for r in good if r["conf"] >= th]
        print(f"threshold {th}: escalate {len(esc)}/{len(good)}; wrong kept {sum(not r['ok'] for r in kept)}; wrong escalated {sum(not r['ok'] for r in esc)}")
    print("mean in/out", sum(r["input"] for r in good) / len(good), sum(r["out"] for r in good) / len(good))
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
