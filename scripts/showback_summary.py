#!/usr/bin/env python3
"""Chapter 36 summary: allocation of the REAL shared-cache run under four rules, the selfish-choice check, a scaled day, and a MODELLED quarter (all inputs below ASSUMED)."""
import json, random, statistics
from pathlib import Path
from costlab.showback import *
R = Path(__file__).resolve().parents[1] / "runs"
MODEL = "claude-haiku-4-5-20251001"
def load():
    d = json.load(open(R / "showback-cache-lab-2026-11-11.json"))
    C = [r for r in d["results"] if r["arm"] == "C" and not r["error"]]
    U = {r["i"]: r for r in d["results"] if r["arm"] == "U" and not r["error"]}
    return C, U
def rows_from(C, U):
    rows = []
    for r in C:
        u = U[r["i"]]
        billed = call_usd(MODEL, r["in"], r["out"], r["cr"], r["cw"])
        prefix_usd = call_usd(MODEL, 0, 0, r["cr"], r["cw"])
        own = billed - prefix_usd
        rows.append({"team": r["team"], "billed": billed, "prefix_usd": prefix_usd, "own_usd": own, "uncached": call_usd(MODEL, u["in"] + u["cr"] + u["cw"], u["out"]), "cw": r["cw"], "cr": r["cr"]})
    return rows
def show(title, d, n):
    tot = sum(d.values()); print(f"  {title:<22}" + "".join(f"{t}: ${d[t]:.5f} (${d[t]/n[t]*1000:.3f}/k) " for t in sorted(d)) + f" total ${tot:.5f}")
def main():
    C, U = load(); rows = rows_from(C, U)
    n = {}
    for r in rows: n[r["team"]] = n.get(r["team"], 0) + 1
    print(f"calls cached arm {len(C)}, uncached arm {len(U)}; calls per team {n}")
    wr = [r for r in rows if r["cw"] > 0]; print(f"cache writes {len(wr)} (tokens {sum(r['cw'] for r in wr)}), reads {sum(1 for r in rows if r['cr']>0)}")
    print(f"prefix tokens written {wr[0]['cw']}; billed write call ${wr[0]['billed']:.6f}; mean billed read call ${statistics.mean(r['billed'] for r in rows if r['cr']>0):.6f}; mean uncached call ${statistics.mean(r['uncached'] for r in rows):.6f}")
    print("\nAllocation of one measured run (cost per thousand calls in brackets)")
    a1, a2, a3 = caller_pays(rows), amortised(rows), uncached_list(rows)
    show("caller pays", a1, n); show("amortised per call", a2, n); show("uncached (requested)", a3, n)
    print(f"  company bill cached ${sum(a1.values()):.5f} vs uncached ${sum(a3.values()):.5f} (saving {(1-sum(a1.values())/sum(a3.values()))*100:.1f}%); platform keeps ${sum(a3.values())-sum(a1.values()):.5f} under the requested-price rule")
    print("\nSelfish-choice check (a team keeps the cache only if its own bill is lower with it)")
    for name, rule in (("caller pays", caller_pays), ("amortised", amortised)):
        ch, base, unc = selfish_cache_choice(rows, rule)
        print(f"  {name:<12}" + "; ".join(f"{t}: cache {'ON ' if ch[t] else 'OFF'} (${base[t]:.5f} vs ${unc[t]:.5f})" for t in sorted(ch)))
    # Scaled day, ASSUMED: calls per day per team, cache expires after 5 idle minutes; the writer opens the cache W times a day
    wcall = wr[0]["billed"]; rcall = statistics.mean(r["billed"] for r in rows if r["cr"] > 0); ucall = statistics.mean(r["uncached"] for r in rows)
    print("\nScaled day, ASSUMED volumes: support 1,000, product 30,000, data 9,000 calls; support's first call after each idle gap writes")
    for W in (1, 6, 40, 200):
        vol = {"support": 1000, "product": 30000, "data": 9000}
        tot = sum(vol.values()); writes = W
        sup = writes * wcall + (vol["support"] - writes) * rcall
        prod = vol["product"] * rcall; dat = vol["data"] * rcall
        cached = sup + prod + dat; unc = tot * ucall
        am = cached / tot
        print(f"  writes/day {W:>3}: caller-pays support ${sup:8.2f} (${sup/vol['support']*1000:7.3f}/k) vs product ${prod/vol['product']*1000:6.3f}/k; amortised all ${am*1000:6.3f}/k; company cached ${cached:8.2f} vs uncached ${unc:8.2f}")
    # Expected cost per call when the cache is warmed only by a team's own calls, Poisson arrivals, 5-minute refresh-on-read TTL (ASSUMED arrival rates)
    import math
    print("\nExpected billed cost per call by arrival rate if the team's own calls are the only ones keeping the prefix warm (5-minute lifetime, ASSUMED rates)")
    flip = None
    for lam in (1, 2, 3, 6, 12, 30, 120):
        p = math.exp(-lam / 12.0); e = p * wcall + (1 - p) * rcall
        print(f"  {lam:>4} calls an hour: P(write) {p:5.3f}  expected ${e:.6f} per call, uncached ${ucall:.6f}  ratio {e/ucall:5.2f}")
    pf = (ucall - rcall) / (wcall - rcall); print(f"  the cache stops paying for a lone team when P(write) exceeds {pf:.3f}, i.e. below about {-12*math.log(pf):.2f} calls an hour")
    # Misallocation by rule on a SYNTHETIC population
    rnd = random.Random(361)
    teams = {"support-agent": 120, "handbook": 40, "extraction": 30, "search": 25, "reports": 60, "sales-email": 90, "platform-evals": 35}
    spend = {"support-agent": 52000, "handbook": 21000, "extraction": 33000, "search": 61000, "reports": 18000, "sales-email": 6500, "platform-evals": 24000}
    total = sum(spend.values())
    keys = {"support-agent": "key-a", "handbook": "key-a", "extraction": "key-b", "search": "key-b", "reports": "key-b", "sales-email": "key-c", "platform-evals": "key-c"}
    print(f"\nMisallocation on a SYNTHETIC month (total ${total:,}); share of dollars charged to the wrong team")
    hc = headcount_split(total, teams); print(f"  headcount split            {misallocation(hc, spend)*100:5.1f}%")
    kt = {}; ks = {}
    for t, k in keys.items(): ks[k] = ks.get(k, 0) + spend[t]
    knames = {}
    for t, k in keys.items(): knames.setdefault(k, []).append(t)
    kk = {}
    for k, ts in knames.items():
        for t in ts: kk[t] = ks[k] / len(ts)
    print(f"  one key per team group     {misallocation(kk, spend)*100:5.1f}%   (shared keys split equally among their users)")
    for cov in (0.7, 0.9, 0.96):
        tagged = {t: spend[t] * cov for t in spend}; pool = total - sum(tagged.values())
        prop = {t: tagged[t] + pool * tagged[t] / sum(tagged.values()) for t in tagged}
        eq = {t: tagged[t] + pool / len(tagged) for t in tagged}
        print(f"  tags at {cov*100:.0f}% coverage: pool pro rata {misallocation(prop, spend)*100:4.1f}%, pool split equally {misallocation(eq, spend)*100:4.1f}%")
    # MODELLED quarter: 13 weeks; products with a ready lever respond to showback (ASSUMED)
    prods = {"support-agent": (52000, 0.18), "handbook": (21000, 0.12), "extraction": (33000, 0.20), "search": (61000, 0.0), "reports": (18000, 0.10), "sales-email": (6500, 0.0), "platform-evals": (24000, 0.02)}
    print("\nMODELLED quarter, ASSUMED responses: monthly spend, showback with a ready lever cuts the waste share by half over 13 weeks")
    base = sum(v[0] for v in prods.values()); after = 0
    for p, (s, waste) in prods.items():
        cut = s * waste * 0.5; after += s - cut
        print(f"  {p:<16} ${s:7,}  waste share {waste*100:4.1f}%  cut ${cut:7,.0f}")
    print(f"  total ${base:,} -> ${after:,.0f} ({(1-after/base)*100:.1f}% lower); products that moved: {sum(1 for v in prods.values() if v[1] >= 0.1)} of 7")
    for blunt in (0.0, 0.5, 1.0):
        exp_share = 0.12; cutb = base * 0.10
        print(f"  chargeback model, blunt cut 10% of bill, share of the cut falling on experiments {blunt*100:3.0f}% -> experiment spend lost ${cutb*blunt:,.0f} of a ${base*exp_share:,.0f} experiment budget ({cutb*blunt/(base*exp_share)*100:.0f}%)")
if __name__ == "__main__": main()
