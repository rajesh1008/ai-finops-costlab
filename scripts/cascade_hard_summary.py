#!/usr/bin/env python3
"""Chapter 17 follow-up summary (offline) of runs/cascade-hard-lab-2026-11-11.json: accuracy and dollars per model, the expression arm, agreement as a signal, and policies at the price table's rates."""
import json
from pathlib import Path
from costlab.cascade_hard import make_hard, correct, agree, safe_eval
from costlab.estimate import estimate_usd
R = Path(__file__).resolve().parents[1] / "runs"; rows = json.loads((R / "cascade-hard-lab-2026-11-11.json").read_text())["results"]
MODEL = {"H45": "anthropic:claude-haiku-4-5-20251001", "H55": "anthropic:claude-haiku-5-5", "S46": "anthropic:claude-sonnet-4-6", "EXPR": "anthropic:claude-haiku-5-5"}
probs = make_hard(); N = len(probs); by = {}; lines = []
for r in rows:
    r["cost"] = estimate_usd(MODEL[r["m"]], r["in"], r["out"], 0, 0); a = probs[r["id"]]["answer"]
    if r["m"] == "EXPR":
        try: r["ok"] = abs(safe_eval(r["text"]) - a) < 0.005; r["evalerr"] = False
        except Exception: r["ok"] = False; r["evalerr"] = True
    else: r["ok"] = correct(r["text"], a); r["evalerr"] = False
    by.setdefault((r["id"], r["m"]), []).append(r)
lines.append(f"errors: {sum(1 for r in rows if r['error'])}")
lines.append(f"{'model':>5} {'samples':>8} {'correct':>8} {'rate':>7} {'avg in':>7} {'avg out':>8} {'$/call':>10}")
for m in ("H45", "H55", "S46", "EXPR"):
    rs = [r for r in rows if r["m"] == m]; ok = sum(r["ok"] for r in rs)
    lines.append(f"{m:>5} {len(rs):>8} {ok:>8} {ok/len(rs):>7.1%} {sum(r['in'] for r in rs)/len(rs):>7.1f} {sum(r['out'] for r in rs)/len(rs):>8.1f} {sum(r['cost'] for r in rs)/len(rs):>10.6f}")
lines.append(f"EXPR strict reading (whole reply must be an expression): evaluator failures {sum(r['evalerr'] for r in rows if r['m']=='EXPR')} of 40")
# LENIENT extraction, written AFTER seeing that the model explained itself instead of replying with the expression only: the last line made only of digits, spaces, + - * / ( ) . and the multiplication sign
import re
def lenient(text):
    cands = [l.strip().replace("\u00d7", "*").replace("\u2212", "-") for l in text.splitlines() if l.strip()]
    ok = [l for l in cands if re.fullmatch(r"[\d\s+\-*/().]+", l) and any(c in l for c in "+-*/")]
    return ok[-1] if ok else None
len_ok = 0; len_valid = 0; len_cost = 0.0
for p in probs:
    e = by[(p["id"], "EXPR")][0]; x = lenient(e["text"])
    if x:
        try: v = safe_eval(x); len_valid += 1; len_ok += abs(v - p["answer"]) < 0.005
        except Exception: pass
lines.append(f"EXPR lenient reading (last pure-arithmetic line, written after the fact): valid {len_valid} of 40, correct {len_ok} of 40, correct among valid {len_ok}/{len_valid}")
def pol(first):
    ok = cost = esc = 0
    for p in probs:
        a, b = by[(p["id"], first)][:2]; cost += a["cost"] + b["cost"]
        if agree(a["text"], b["text"]): ok += a["ok"]
        else: s = by[(p["id"], "S46")][0]; cost += s["cost"]; ok += s["ok"]; esc += 1
    return ok / N, cost / N, esc / N
lines.append("POLICIES"); 
for m in ("H45", "H55", "S46"):
    x = by; ok = sum(by[(p["id"], m)][0]["ok"] for p in probs); c = sum(by[(p["id"], m)][0]["cost"] for p in probs); lines.append(f"always {m}: {ok/N:.1%} ${c/N:.6f}")
for first in ("H45", "H55"):
    a, c, e = pol(first); lines.append(f"2x {first} agree else S46: {a:.1%} ${c:.6f} escalated {e:.1%}")
for first in ("H45", "H55"):
    ok = cost = 0
    for p in probs:
        a = by[(p["id"], first)][0]; cost += a["cost"]
        if a["ok"]: ok += 1
        else: s = by[(p["id"], "S46")][0]; cost += s["cost"]; ok += s["ok"]
    lines.append(f"oracle {first} then S46 if wrong: {ok/N:.1%} ${cost/N:.6f} (bound)")
# expression arm as first stage, S46 when the expression does not evaluate
ok = cost = esc = 0
for p in probs:
    e = by[(p["id"], "EXPR")][0]; cost += e["cost"]
    if e["evalerr"]: s = by[(p["id"], "S46")][0]; cost += s["cost"]; ok += s["ok"]; esc += 1
    else: ok += e["ok"]
lines.append(f"EXPR, S46 only if it does not evaluate: {ok/N:.1%} ${cost/N:.6f} escalated {esc/N:.1%}")
for first in ("H45", "H55"):
    ag = [(by[(p['id'], first)][0], by[(p['id'], first)][1]) for p in probs if agree(by[(p['id'], first)][0]["text"], by[(p['id'], first)][1]["text"])]
    lines.append(f"{first}: agreed on {len(ag)}/{N}; both correct on {sum(1 for a,b in ag if a['ok'] and b['ok'])}/{len(ag)}")
(R / "cascade-hard-summary-2026-11-11.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
ok = cost = esc = 0
for p in probs:
    e = by[(p["id"], "EXPR")][0]; cost += e["cost"]; x = lenient(e["text"]); v = None
    if x:
        try: v = safe_eval(x)
        except Exception: v = None
    if v is None: s = by[(p["id"], "S46")][0]; cost += s["cost"]; ok += s["ok"]; esc += 1
    else: ok += abs(v - p["answer"]) < 0.005
lines.append(f"EXPR lenient, S46 only when no expression found: {ok/N:.1%} ${cost/N:.6f} escalated {esc/N:.1%}")
(R / "cascade-hard-summary-2026-11-11.txt").write_text("\n".join(lines) + "\n"); print(lines[-1])
