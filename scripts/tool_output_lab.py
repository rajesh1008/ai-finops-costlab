#!/usr/bin/env python3
"""Chapter 19 lab. REAL calls. Does shrinking a tool result (compact JSON, field projection, truncation) change the billed input tokens, and does it change whether the model still answers correctly? A synthetic table of 120 invoices is returned by a fake tool. Four variants of the same tool result, three lookup questions, three repeats, two models. max_tokens 400 and tool_choice none (run 1 used max_tokens 40 and no tool_choice; many replies were cut off or were a second tool request, so its accuracy column is not usable, only its token counts; its files are kept as tool-output-run1-maxtok40-*). Answers are checked by exact match against values computed from the table, never judged by a model."""
import os, sys, json, random, time
from pathlib import Path
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
VARIANTS = ["pretty_full", "compact_full", "projected", "top20_projected"]
REPEATS = 3
MAX_TOKENS = 400
OUT = Path(__file__).resolve().parents[1] / "runs" / "tool-output-run2-2026-11-12.jsonl"
NAMES = ["Alder", "Birch", "Cedar", "Dunmore", "Elmstead", "Fairlie", "Garrow", "Hollin", "Ivel", "Juniper"]
def make_table(n=120, seed=7):
    r = random.Random(seed); rows = []
    for i in range(1, n + 1):
        rows.append({"invoice_id": f"INV-{i:04d}", "customer": f"{r.choice(NAMES)} {r.choice(['Ltd','GmbH','Inc','BV'])}",
                     "status": r.choice(["paid", "paid", "open", "overdue", "void"]), "amount": round(r.uniform(120, 9800), 2),
                     "currency": "USD", "created_at": f"2026-{r.randint(1,10):02d}-{r.randint(1,28):02d}T09:15:00Z",
                     "updated_at": f"2026-11-{r.randint(1,11):02d}T16:40:00Z",
                     "billing": {"line1": f"{r.randint(1,200)} {r.choice(NAMES)} Street", "city": r.choice(["Leeds", "Pune", "Oslo", "Lyon"]), "postcode": f"{r.randint(10000,99999)}"},
                     "notes": r.choice(["", "", "net 30", "po required", "disputed line 2", "reminder sent twice"]),
                     "line_items": [{"sku": f"SKU-{r.randint(100,999)}", "qty": r.randint(1, 20), "unit_price": round(r.uniform(5, 400), 2)} for _ in range(r.randint(1, 3))]})
    return rows
def render(rows, variant):
    if variant == "pretty_full": return json.dumps(rows, indent=2)
    if variant == "compact_full": return json.dumps(rows, separators=(",", ":"))
    keep = lambda x: {k: x[k] for k in ("invoice_id", "customer", "status", "amount")}
    if variant == "projected": return json.dumps([keep(x) for x in rows], separators=(",", ":"))
    if variant == "top20_projected":
        latest = sorted(rows, key=lambda x: x["updated_at"], reverse=True)[:20]
        return json.dumps([keep(x) for x in latest], separators=(",", ":"))
    raise ValueError(variant)
def questions(rows):
    big = max(rows, key=lambda x: x["amount"]); target = rows[86]
    od = sum(1 for x in rows if x["status"] == "overdue")
    return [("Which invoice has the largest amount? Reply with the invoice id only.", big["invoice_id"]),
            (f"What is the status of {target['invoice_id']}? Reply with one word.", target["status"]),
            ("How many invoices have status overdue? Reply with the number only.", str(od))]
def correct(reply, expected):
    """Whole-token match after stripping markdown emphasis and trailing punctuation; a number inside a longer number does not count."""
    t = reply.lower().replace("*", " ").replace(",", "")
    toks = [w.strip(".:;()\"'") for w in t.split()]
    return expected.lower() in toks
def rescore(rows, qs):
    """Run 1 of the checker missed an answer wrapped in bold marks. Re-check every stored reply (the last 80 characters) with the current checker and keep a row correct if either check passed."""
    out = []
    for r in rows:
        r = dict(r); r["ok"] = bool(r["ok"] or correct(r["reply"], qs[r["q"]][1])); out.append(r)
    return out
def build_messages(q, payload):
    return [{"role": "user", "content": q},
            {"role": "assistant", "content": [{"type": "tool_use", "id": "toolu_01lab", "name": "list_invoices", "input": {}}]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_01lab", "content": payload}]}]
TOOLS = [{"name": "list_invoices", "description": "Return the invoices for the account.", "input_schema": {"type": "object", "properties": {}}}]
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); rows = make_table(); qs = questions(rows); out = []
    for m in MODELS:
        for v in VARIANTS:
            payload = render(rows, v)
            for qi, (q, exp) in enumerate(qs):
                for rep in range(REPEATS):
                    x = cl.messages.create(model=m, max_tokens=MAX_TOKENS, tools=TOOLS, tool_choice={"type": "none"}, messages=build_messages(q, payload))
                    reply = "".join(b.text for b in x.content if b.type == "text")
                    u = x.usage
                    out.append({"model": m, "variant": v, "q": qi, "rep": rep, "input": u.input_tokens, "output": u.output_tokens,
                                "cache_write": u.cache_creation_input_tokens or 0, "cache_read": u.cache_read_input_tokens or 0,
                                "stop": x.stop_reason, "chars": len(payload), "ok": correct(reply, exp), "reply": reply[-80:]})
                    time.sleep(0.3)
    OUT.write_text("\n".join(json.dumps(r) for r in out) + "\n")
def summarise(rows):
    res = {}
    for m in sorted({r["model"] for r in rows}):
        res[m] = {}
        for v in VARIANTS:
            rs = [r for r in rows if r["model"] == m and r["variant"] == v]
            if not rs: continue
            res[m][v] = {"n": len(rs), "mean_input": sum(r["input"] for r in rs) / len(rs), "correct": sum(r["ok"] for r in rs),
                         "correct_by_q": [sum(r["ok"] for r in rs if r["q"] == q) for q in sorted({r["q"] for r in rs})]}
    return res
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        rows = rescore([json.loads(l) for l in OUT.read_text().splitlines()], questions(make_table()))
        for m, d in summarise(rows).items():
            for v, s in d.items(): print(m, v, "n", s["n"], "mean_input %.0f" % s["mean_input"], "correct", s["correct"], "/", s["n"], "by_q", s["correct_by_q"])
    else: main()
