#!/usr/bin/env python3
"""Chapter 26: arithmetic over the recorded budget-policy-lab JSON. No API. haiku-4-5 placeholder rates. Policies: none (cap 16 steps), hard (kill at $0.012), aware (budget note in every tool result, kill at $0.012)."""
import json
from collections import Counter
from pathlib import Path
from costlab.agentrun import run_cost, quantile
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P
p = P["anthropic:claude-haiku-4-5-20251001"]; ui, uo = p["input"], p["output"]
d = [r for r in json.load(open(Path(__file__).resolve().parents[1] / "runs" / "budget-policy-lab-2026-11-10.json"))["results"] if r["status"] != "api_error"]
for r in d: r["cost"] = run_cost(r["steps"], ui, uo); r["n"] = len(r["steps"])
base = None
for pol in ("none", "hard", "aware"):
    g = [r for r in d if r["policy"] == pol]; c = [r["cost"] for r in g]; tot = sum(c); ok = sum(r["ok"] for r in g)
    if pol == "none": base = tot
    print(f"{pol:5s}: runs {len(g)} correct {ok}/{len(g)} = {ok/len(g):.3f} spend ${tot:.4f} ({tot/base:.2f}x of none) mean ${tot/len(g):.5f} p90 ${quantile(c,.9):.5f} max ${max(c):.5f} mean steps {sum(r['n'] for r in g)/len(g):.2f} cost per correct ${tot/max(ok,1):.5f}  status {dict(Counter(r['status'] for r in g))}")
    for h in (3, 5):
        gh = [r for r in g if r["n_pairs"] == h]; ch = [r["cost"] for r in gh]
        print(f"        {h} hops: correct {sum(r['ok'] for r in gh)}/{len(gh)} mean ${sum(ch)/len(ch):.5f} max ${max(ch):.5f}")
idx = {(r["q"], r["rep"], r["policy"]): r for r in d}
lost = sum(1 for (q, rep, pol), r in idx.items() if pol == "none" and r["ok"] and not idx.get((q, rep, "hard"), {"ok": True})["ok"])
lost_a = sum(1 for (q, rep, pol), r in idx.items() if pol == "none" and r["ok"] and not idx.get((q, rep, "aware"), {"ok": True})["ok"])
gain_a = sum(1 for (q, rep, pol), r in idx.items() if pol == "none" and not r["ok"] and idx.get((q, rep, "aware"), {"ok": False})["ok"])
print(f"paired (same question and repeat; sampling differs between arms): correct under none but wrong under hard {lost}; under aware {lost_a}; wrong under none but right under aware {gain_a}")
for pol in ("hard", "aware"):
    k = [r for r in d if r["policy"] == pol and r["status"] == "killed"]
    print(f"{pol}: killed {len(k)} runs, spend on killed runs ${sum(r['cost'] for r in k):.4f}")
