#!/usr/bin/env python3
"""Chapter 33: customer-facing cap designs against a SYNTHETIC population of 5,000 customers whose run costs are the REAL per-run costs of the Chapter 24 chain lab (120 runs, haiku-4-5 placeholder rates).
Types and run counts are my own construction (90 percent normal, 8 percent heavy_task, 2 percent automated); plan price $3.00 a month is ASSUMED. This tests the shape of a cap, not any product."""
import json, statistics
from pathlib import Path
from costlab.agentrun import run_cost
from costlab.fairuse import make_customers, evaluate
R = Path(__file__).resolve().parents[1] / "runs"
def main():
    d = json.load(open(R / "agent-run-lab-chain-2026-11-10.json")); res = [r for r in d["results"] if r["status"] != "api_error"]
    costs = sorted(run_cost(r["steps"], 1.0, 5.0) for r in res); h = len(costs) // 2; easy, hard = costs[:h], costs[h:]
    print(f"real run costs n={len(costs)}: cheapest half mean ${statistics.mean(easy):.5f}, dearest half mean ${statistics.mean(hard):.5f}, overall mean ${statistics.mean(costs):.5f}, max ${max(costs):.5f}")
    cs = make_customers(5000, easy, hard, seed=331, plan=3.0)
    tot = {t: sum(sum(c['runs']) for c in cs if c['type'] == t) for t in ("normal", "heavy_task", "automated")}; cnt = {t: sum(1 for c in cs if c['type'] == t) for t in tot}
    allc = sum(tot.values()); print(f"customers {cnt}; cost share by type " + ", ".join(f"{t} {tot[t]/allc*100:.1f}%" for t in tot) + f"; total cost ${allc:,.2f} against plan revenue ${3.0*len(cs):,.0f}")
    for t in tot: print(f"   {t}: mean monthly cost per customer ${tot[t]/cnt[t]:.3f}; share over the $3.00 plan price {sum(1 for c in cs if c['type']==t and sum(c['runs'])>3.0)/cnt[t]*100:.1f}%")
    for kind, vals in (("none", (0,)), ("runs", (100, 200, 400, 1000)), ("cost", (0.5, 1.0, 2.0, 3.0))):
        for v in vals:
            ev = evaluate(cs, kind, v); line = f"{kind:<5}{v:>7}: "
            line += "  ".join(f"{t[:6]} hit {ev[t]['hit']/ev[t]['n']*100:5.1f}% lost {ev[t]['lost']/max(1,ev[t]['runs'])*100:5.1f}%" for t in ("normal", "heavy_task", "automated"))
            adm = sum(ev[t]["cost_admitted"] for t in ev); plan = sum(ev[t]["plan"] for t in ev); line += f"  | cost admitted ${adm:,.0f} margin {(plan-adm)/plan*100:5.1f}% | customers over plan price {sum(ev[t]['neg_margin'] for t in ev)}"
            print(line)
if __name__ == "__main__": main()
