#!/usr/bin/env python3
"""Chapter 38 lab, offline. (1) Rounding: REAL token counts from the Chapter 34 ledger, priced exactly and then with a spreadsheet's habit of rounding each row. (2) Three meter sources over one SYNTHETIC month with known truth."""
import json, random, statistics
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from costlab.showback import call_usd, misallocation
R = Path(__file__).resolve().parents[1] / "runs"
def main():
    recs = [json.loads(l) for l in open(R / "evidence-pack-ledger-2026-11-11.jsonl")]
    exact = [call_usd(r["model"], r["in"], r["out"]) for r in recs]; tot = sum(exact)
    print(f"REAL token records {len(recs)}; exact total ${tot:.6f}; mean per call ${tot/len(recs):.6f}; smallest ${min(exact):.7f}; largest ${max(exact):.6f}")
    for scale in (1, 2000):
        print(f"\nPer-row rounding, each recorded call standing for {scale} calls (row cost = exact x {scale}):")
        for dp in (0, 2, 3, 4):
            rr = [float(Decimal(str(x * scale)).quantize(Decimal(1).scaleb(-dp), rounding=ROUND_HALF_UP)) for x in exact]
            print(f"  round each row to {dp} decimals: total ${sum(rr):,.4f} vs exact ${tot*scale:,.4f}  error {(sum(rr)-tot*scale)/(tot*scale)*100:+7.2f}%   rows rounded to zero: {sum(1 for x in rr if x == 0)}")
    # by team: the error is not spread evenly
    for dp in (2, 4):
        err = {}
        for r, x in zip(recs, exact):
            t = r.get("team") or "(untagged)"; rr = float(Decimal(str(x)).quantize(Decimal(1).scaleb(-dp), rounding=ROUND_HALF_UP)); a = err.setdefault(t, [0, 0]); a[0] += x; a[1] += rr
        print(f"\nUnscaled, rows rounded to {dp} decimals, by team: " + "; ".join(f"{t} {v[1]/v[0]*100-100:+.1f}%" for t, v in sorted(err.items())))
    # (2) three meter sources on the Chapter 36 synthetic month
    teams = ["support-agent", "handbook", "extraction", "search", "reports", "sales-email", "platform-evals"]
    spend = dict(zip(teams, [52000, 21000, 33000, 61000, 18000, 6500, 24000])); total = sum(spend.values())
    keys = {"support-agent": "key-a", "handbook": "key-a", "extraction": "key-b", "search": "key-b", "reports": "key-b", "sales-email": "key-c", "platform-evals": "key-c"}
    ks = {}; kn = {}
    for t, k in keys.items(): ks[k] = ks.get(k, 0) + spend[t]; kn[k] = kn.get(k, 0) + 1
    inv = {t: ks[keys[t]] / kn[keys[t]] for t in teams}
    rnd = random.Random(381); bypass = {"support-agent": 0.02, "handbook": 0.0, "extraction": 0.05, "search": 0.03, "reports": 0.10, "sales-email": 0.35, "platform-evals": 0.0}
    trace = {t: spend[t] * (1 - bypass[t]) for t in teams}; miss = total - sum(trace.values())
    gw = {t: spend[t] * 0.97 for t in teams}; gw_un = total - sum(gw.values())
    print(f"\nThree meter sources, SYNTHETIC month, total ${total:,}")
    print(f"  invoice only (keys)          wrong-team share {misallocation(inv, spend)*100:5.1f}%   unexplained $0, but per-team error up to ${max(abs(inv[t]-spend[t]) for t in teams):,.0f} ({max(abs(inv[t]-spend[t])/spend[t] for t in teams)*100:.0f}%)")
    print(f"  traces only (SDK), bypass 0 to 35%  covers ${sum(trace.values()):,.0f} = {sum(trace.values())/total*100:.1f}% of the invoice; ${miss:,.0f} unseen; sales-email understated {bypass['sales-email']*100:.0f}%")
    print(f"  gateway meter, 3% untagged   covers ${sum(gw.values()):,.0f} tagged + ${gw_un:,.0f} untagged pool = 100.0% of the invoice; untagged is a named line")
    # (3) build versus buy, SignalCost's formula. FEES are the list prices that post reports (Langfuse Core $69, $451, $3,931 at 100k, 1M, 10M runs); everything else is ASSUMED
    from costlab.showback import monthly_tco, allocation_cost_per_mtok
    fee = {100_000: 69, 1_000_000: 451, 10_000_000: 3931}
    RATE = 90.0  # ASSUMED fully loaded dollars per engineer hour
    print("\nBuild versus buy per month (fees as reported by a third-party post; infra, hours and rate ASSUMED, R=$90/h, build amortised over 24 months)")
    print(f"  {'runs a month':>13} {'SaaS':>9} {'self-host':>10} {'build':>9}")
    for runs, f in fee.items():
        infra_sh = 250 + 0.00035 * runs          # ASSUMED: databases, storage, compute
        infra_b = 100 + 0.00015 * runs           # ASSUMED: marginal on an existing warehouse
        saas = monthly_tco(fee=f, h_build=40, rate=RATE)
        sh = monthly_tco(infra=infra_sh, h_run=14, h_build=80, rate=RATE)
        bd = monthly_tco(infra=infra_b, h_run=24, h_build=520, rate=RATE)
        print(f"  {runs:>13,} {saas:>9,.0f} {sh:>10,.0f} {bd:>9,.0f}")
    print("  sensitivity: at 40 h a month of self-host operation the 1M-run self-host cost is $" + f"{monthly_tco(infra=250+0.00035*1_000_000, h_run=40, h_build=80, rate=RATE):,.0f}")
    print("\nSelf-hosted inference, usage cost $1.00 per million tokens against an API at $2.00 (the arithmetic an infrastructure post states):")
    for u in (0.9, 0.5, 0.25, 0.1):
        c = allocation_cost_per_mtok(1.0, u); print(f"  utilisation {u*100:3.0f}%: allocation-based ${c:5.2f} per million -> {'self-host cheaper' if c < 2.0 else 'API cheaper'}")
    print("  can it answer cost per resolved ticket? invoice only: no (no tickets); traces only: yes for traced calls; gateway: yes if the outcome id is on the record")
if __name__ == "__main__": main()
