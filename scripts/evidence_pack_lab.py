#!/usr/bin/env python3
"""Chapter 34 lab. Build an evidence pack from REAL usage records (token counts from the Chapter 31 portability run and, if present, the Chapter 35 model-change run), with SYNTHETIC tags, days and invoice.
Steps: ledger with hash chain; recomputation; coverage; synthetic invoice with planted defects; line-level reconciliation against a total-level check; tamper tests; sampling arithmetic and simulation; manifest.
Tags: team and feature follow the run (format or arm) and are blanked at random (4 percent team, 2 percent env, seed 340); days are assigned at random over 28 days. The invoice is built from the same tokens by my own rule plus planted defects, not a real invoice."""
import json, random, statistics
from pathlib import Path
from costlab.evidence import *
SCALE = 2000  # ASSUMED: each recorded call stands for 2,000 calls, so a month is about $600 and a line is about $10
R = Path(__file__).resolve().parents[1] / "runs"
def load():
    rnd = random.Random(340); recs = []
    d = json.load(open(R / "portability-lab-2026-11-11.json"))
    for r in d["results"]:
        if r["error"]: continue
        recs.append({"id": f"p-{r['q']}-{r['model'][-6:]}-{r['fmt']}", "model": r["model"], "in": r["in"], "out": r["out"], "team": "support-agent" if r["fmt"] == "plain" else "extraction", "feature": r["fmt"], "env": "prod"})
    f = R / "model-change-lab-2026-11-11.json"
    if f.exists():
        m = json.load(open(f)); mod = {a: v[0] for a, v in m["arms"].items()}
        for r in m["results"]:
            if r["error"]: continue
            recs.append({"id": f"m-{r['q']}-{r['arm']}-{r['k']}", "model": mod[r["arm"]], "in": r["in"], "out": r["out"], "team": "handbook-assistant", "feature": "arm-" + r["arm"], "env": "prod"})
    for r in recs:
        r["day"] = rnd.randint(1, 28)
        if rnd.random() < 0.04: r["team"] = ""
        if rnd.random() < 0.02: r["env"] = ""
    return recs
def summarise(name, meter, inv, tol=0.02):
    rows = reconcile_lines(meter, inv, tol); bad = [x for x in rows if not x["ok"]]
    mt, it = sum(meter.values()), sum(inv.values()); tot_ok = abs(it - mt) <= tol * it
    print(f"{name:<34} lines {len(rows):3d} out of tolerance {len(bad):3d}  gap ${it-mt:8.2f} ({(it-mt)/it*100:5.2f}% of invoice)  total-level check at {tol*100:.0f}%: {'PASS' if tot_ok else 'FAIL'}")
    return bad
def main():
    recs = load(); print(f"records {len(recs)} models {sorted(set(r['model'] for r in recs))}")
    led, head = chain(recs); print(f"chain head {head[:16]}...  verify {verify_chain(led, head)}")
    cv = coverage(recs); print(f"recomputed spend (unscaled) ${cv['total_usd']:.4f}, scaled x{SCALE} ${cv['total_usd']*SCALE:,.2f}; attributed ${cv['attributed_usd']:.4f} = {cv['coverage']*100:.1f}%; untagged by key " + ", ".join(f"{k} ${v:.4f}" for k, v in cv["missing_by_key_usd"].items()))
    meter = meter_lines(recs, scale=SCALE)
    print("\nReconciliation, tolerance 2% of the invoice line (floor one cent)")
    summarise("S0 clean invoice", meter, make_invoice(recs, scale=SCALE))
    nd = max(5, len(recs) // 150); b1 = summarise(f"S1 {nd} records billed twice", meter, make_invoice(recs, seed=1, dup_n=nd, scale=SCALE))
    b2 = summarise("S2 input rate +25% from day 15 (all)", meter, make_invoice(recs, early_price_day=15, early_price_factor=1.25, scale=SCALE))
    b3 = summarise("S3 goodwill credit $5.00", meter, make_invoice(recs, credit_usd=5.0, scale=SCALE))
    rnd = random.Random(7); keep = [r for r in recs if rnd.random() > 0.05]
    b4 = summarise("S4 5% of usage never on the meter", meter_lines(keep, scale=SCALE), make_invoice(recs, scale=SCALE))
    print("   S2 lines flagged:", sorted({k[0][-8:] for k in (x['key'] for x in b2)}), "days", sorted(x['key'][1] for x in b2)[:3], "...")
    print("   S3 flagged keys:", [x["key"] for x in b3])
    print("\nTamper tests on the ledger (head hash from the manifest vs none)")
    t = [dict(r) for r in led]; t[len(t)//2]["in"] += 1; print("edit one token count mid-ledger      ", verify_chain(t, head))
    t = [dict(r) for r in led]; del t[len(t)//2]; print("delete one record mid-ledger         ", verify_chain(t, head))
    t = [dict(r) for r in led][:-5]; print("truncate last 5, no head             ", verify_chain(t)); print("truncate last 5, with head           ", verify_chain(t, head))
    t = [dict(r) for r in led]; r0 = t[3]; r0["in"] += 7; body = {k: v for k, v in r0.items() if k not in ("prev", "h")}; r0["h"] = sha(r0["prev"] + canon(body))
    print("edit and re-hash one record only     ", verify_chain(t, head))
    print("\nSampling arithmetic (attribute sampling, zero errors found)")
    for p in (0.05, 0.02, 0.01): print(f"  to show error rate below {p*100:.0f}% at 95%: n = {zero_failure_sample(p)}")
    rnd = random.Random(99); trials = 4000
    for p in (0.01, 0.02, 0.05):
        for n in (59, 149, 300):
            hit = 0
            for _ in range(trials):
                bad = {i for i in range(len(recs)) if rnd.random() < p}
                if bad.intersection(rnd.sample(range(len(recs)), n)): hit += 1
            print(f"  planted error rate {p*100:.0f}%  sample {n:3d}: found at least one in {hit/trials*100:5.1f}% of trials (formula {detect_prob(p, n)*100:5.1f}%)")
    print("  full recomputation of all", len(recs), "records finds every deterministic mismatch by construction")
    files = {"ledger.jsonl": "\n".join(canon(r) for r in led).encode(), "price-table.json": json.dumps(PLACEHOLDER_USD_PER_MTIOK, sort_keys=True).encode(),
             "reconciliation.json": json.dumps([{**x, "key": list(x["key"])} for x in reconcile_lines(meter, make_invoice(recs, scale=SCALE))], sort_keys=True).encode(), "coverage.json": json.dumps(cv, sort_keys=True).encode()}
    man = manifest(files, head, "2026-11-11", "costlab.prices PLACEHOLDER_USD_PER_MTIOK as of 2026-11-09", "usage real, tags/days/invoice synthetic")
    print("\nmanifest files:", {n: (m["bytes"], m["sha256"][:12]) for n, m in man["files"].items()})
    print("verify unchanged:", verify_manifest(man, files))
    files2 = dict(files); files2["price-table.json"] = files["price-table.json"].replace(b"1.0", b"1.1", 1); print("verify after editing one price:", verify_manifest(man, files2))
    (R / "evidence-pack-manifest-2026-11-11.json").write_text(json.dumps(man, indent=1, sort_keys=True))
    (R / "evidence-pack-ledger-2026-11-11.jsonl").write_bytes(files["ledger.jsonl"])
if __name__ == "__main__": main()
