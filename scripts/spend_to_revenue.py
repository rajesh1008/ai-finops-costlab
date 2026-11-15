#!/usr/bin/env python3
"""Chapter 3: the only revenue ratio the baseline supports. ASSUMED: Fieldstone ARR $140,000,000 (Chapter 1);
monthly AI spend $180,000 (fixture); month growth scenarios are assumptions, not forecasts."""
ARR = 140_000_000
SPEND = 180_000
UNOWNED = 108_000
print(f"annualised spend ${SPEND*12:,} = {SPEND*12/ARR:.2%} of ARR")
print(f"unowned part annualised ${UNOWNED*12:,} = {UNOWNED*12/ARR:.2%} of ARR")
print("\nsame ratio if spend grows by a fixed rate each month for 12 months (ARR flat; ASSUMED rates):")
for g in (0.0, 0.05, 0.10, 0.20):
    s = SPEND; tot = 0.0
    for m in range(12):
        tot += s; s *= 1 + g
    print(f"  growth {g:>4.0%} a month: year total ${tot:>12,.0f} = {tot/ARR:6.2%} of ARR; month 12 run-rate ${s/(1+g):>10,.0f}")
