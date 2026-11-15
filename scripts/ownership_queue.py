#!/usr/bin/env python3
"""Chapter 3 lab: the ownership queue for Fieldstone's October fixture. No API calls."""
import json
from pathlib import Path
from costlab.records import InvoiceLine
from costlab.ownership import build_queue

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "fieldstone_invoices.json"
lines = [InvoiceLine(**x) for x in json.loads(FIX.read_text())["lines"]]
total = sum(l.amount_usd for l in lines)
tagged = [l for l in lines if l.product_tag]
print(f"lines {len(lines)}  tagged lines {len(tagged)} ({len(tagged)/len(lines):.0%} of lines)")
print(f"total ${total:,.0f}  tagged ${sum(l.amount_usd for l in tagged):,.0f} ({sum(l.amount_usd for l in tagged)/total:.0%} of dollars)")
print()
print(f"{'#':>2} {'vendor':22s} {'class':16s} {'usd':>8s} {'cum%':>6s}  reason")
for i, r in enumerate(build_queue(lines), 1):
    print(f"{i:>2} {r['vendor']:22s} {r['class']:16s} {r['amount_usd']:>8,.0f} {r['cumulative_share']*100:>5.1f}%  {r['reason']}")
