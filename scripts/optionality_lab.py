#!/usr/bin/env python3
"""Chapter 31: break-even spend for keeping a second vendor warm. ASSUMED standing costs and probabilities. The standing cost of the parity suite itself is measured from the portability lab (real calls): see portability_summary.py."""
import json
from pathlib import Path
from costlab.optionality import annual_value, breakeven_spend
from costlab.estimate import estimate_usd
R = Path(__file__).resolve().parents[1] / "runs"
def main():
    d = json.load(open(R / "portability-lab-2026-11-11.json")); res = [r for r in d["results"] if r["error"] is None]
    api = sum(estimate_usd("anthropic:" + r["model"], r["in"], r["out"]) for r in res)
    print(f"parity run in the portability lab: {len(res)} calls, ${api:.4f} at placeholder rates; 60 questions x 3 contracts x 2 models")
    print("scaled to a 500-case suite on 4 prompts x 2 vendors x 4 contracts, 10 refreshes a year, at 20 times the per-call cost of these small prompts:")
    per = api / len(res); n = 500 * 4 * 2 * 4 * 10; print(f"  {n:,} calls x ${per*20:.5f} = ${n*per*20:,.0f} a year of API spend for parity testing")
    print("\nbreak-even annual spend (spend at which expected value of optionality equals its standing cost):")
    print(f"{'standing cost':>14}{'p(event)':>10}{'saving':>8}{'break-even spend':>20}")
    for F in (60000, 150000, 400000):
        for p in (0.15, 0.30, 0.60):
            for sv in (0.20, 0.40):
                print(f"{F:>14,}{p:>10.2f}{sv:>8.2f}{breakeven_spend(F, p, sv):>20,.0f}")
    print("\nFieldstone assumption: annual AI spend $3.0 million, standing cost $150,000, p 0.30, saving 0.30:")
    print(f"  value ${annual_value(3.0e6, .30, .30):,.0f} against cost $150,000")
    print(f"  at $0.5 million spend, same terms: value ${annual_value(0.5e6, .30, .30):,.0f}")
if __name__ == "__main__": main()
