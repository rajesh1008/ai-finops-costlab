#!/usr/bin/env python3
"""Chapter 38 summary of the explainer lab."""
import json, re
from collections import Counter, defaultdict
from pathlib import Path
from costlab.showback import call_usd
R = Path(__file__).resolve().parents[1] / "runs"
def parse(t):
    m = re.search(r'"driver"\s*:\s*"([a-z_]+)"', t); return m.group(1) if m else "unparsed"
d = json.load(open(R / "explainer-lab-2026-11-11.json"))["results"]; ok = [r for r in d if not r["error"]]
print("calls", len(d), "errors", len(d) - len(ok))
cost = {"h45": "claude-haiku-4-5-20251001", "h55": "claude-haiku-5-5"}
for m in ("h45", "h55"):
    for form in ("T", "D"):
        rs = [r for r in ok if r["m"] == m and r["form"] == form]; c = Counter(); outs = Counter()
        for r in rs:
            g = parse(r["text"]); c["right" if g == r["true"] else ("unknown" if g == "unknown" else ("unparsed" if g == "unparsed" else "wrong"))] += 1
        usd = sum(call_usd(cost[m], r["in"], r["out"]) for r in rs)
        print(f"{m} form {form}: n {len(rs)}  right {c['right']}  wrong {c['wrong']}  unknown {c['unknown']}  unparsed {c['unparsed']}  usd {usd:.4f} per call {usd/len(rs):.6f}")
print("\nBy true driver, form D, both models (right of 16)")
for dr in ("volume", "price", "cache", "tokens_per_call", "mix", "untagged"):
    rs = [r for r in ok if r["form"] == "D" and r["true"] == dr]; print(f"  {dr:<16} right {sum(parse(r['text'])==dr for r in rs)} of {len(rs)}   by model " + ", ".join(f"{m} {sum(parse(r['text'])==dr for r in rs if r['m']==m)}/{sum(1 for r in rs if r['m']==m)}" for m in ('h45','h55')))
print("\nBy true driver, form T (spend and calls only), both models")
for dr in ("volume", "price", "cache", "tokens_per_call", "mix", "untagged"):
    rs = [r for r in ok if r["form"] == "T" and r["true"] == dr]; c = Counter(parse(r["text"]) for r in rs); print(f"  {dr:<16} answers {dict(c)}")
print("\nConfusions in form D (true -> said), wrong only")
conf = Counter((r["true"], parse(r["text"])) for r in ok if r["form"] == "D" and parse(r["text"]) != r["true"]); [print(f"  {a} -> {b}: {n}") for (a, b), n in conf.most_common(12)]
