#!/usr/bin/env python3
"""Chapter 30: three contract structures against three Fieldstone scenarios. SYNTHETIC path ($180,000 a month at month 1 of the contract, 6 percent monthly growth), ASSUMED discounts and floors.
The 5.99x per-task price move is measured (tokenizer_summary.py); everything else is an assumption of mine and no vendor has offered these terms.
S1 pay as you go at list. S2 12-month full-period commit, 15 percent discount, commit 90 percent of the forecast discounted spend, no protection, counts old-model spend only (failure injection shown separately).
S3 12-month, 12 percent discount, commit 70 percent of forecast discounted spend, commit stated in work and scaled when list price per task falls, quarterly ramp 10/20/30/40 percent."""
from costlab.commitments import *
RATIO = 1 / 5.99
RAMP = [0.10 / 3] * 3 + [0.20 / 3] * 3 + [0.30 / 3] * 3 + [0.40 / 3] * 3
def main():
    base = usage_path(12, 180000, 0.06, seed=9)
    scen = {"A base (6% growth, no price move)": (base, None),
            "B price move (work moves to the newer model in month 5, 0.167 per task)": (base, 5),
            "C growth stalls (flat from month 4, a lever removes 20% of volume in month 7)": ([u if m < 4 else base[3] * (0.8 if m >= 7 else 1.0) for m, u in enumerate(base, start=1)], None)}
    fc = sum(base)
    print(f"forecast usage at list over 12 months ${fc:,.0f}")
    c2 = 0.90 * fc * 0.85; c3 = 0.70 * fc * 0.88
    print(f"S2 commit ${c2:,.0f} (discounted dollars); S3 commit ${c3:,.0f}")
    print(f"{'scenario':<82}{'S1 PAYG':>12}{'S2':>12}{'S2 old-model-only':>20}{'S3':>12}")
    for name, (u, cut) in scen.items():
        v = price_cut_path(u, cut, RATIO) if cut else u
        s1 = sum(v); s2 = spend_commit(v, 0.15, c2)["paid"]
        if cut:
            old = [x if m < cut else 0.0 for m, x in enumerate(u, start=1)]; new = [x * RATIO if m >= cut else 0.0 for m, x in enumerate(u, start=1)]
            s2b = eligible_only_old_model(old, new, 0.15, c2)["paid"]
            s3 = commit_with_protection(u, 0.12, c3, cut, RATIO, ramp=RAMP)["paid"]
        else:
            s2b = None
            s3 = commit_with_protection(u, 0.12, c3, 99, RATIO, ramp=RAMP)["paid"]
        print(f"{name:<82}{s1:>12,.0f}{s2:>12,.0f}{(s2b if s2b is not None else float('nan')):>20,.0f}{s3:>12,.0f}   S2/S1 {s2/s1:5.2f}  S3/S1 {s3/s1:5.2f}" + (f"  S2b/S1 {s2b/s1:5.2f}" if s2b else ""))
if __name__ == "__main__": main()
