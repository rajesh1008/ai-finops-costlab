#!/usr/bin/env python3
"""Chapter 9: the double-count if OTel-style input (includes cache) is read as cr-2 input (uncached only). SYNTHETIC rows."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from costlab.views import otel_to_cr2, priced_both_ways
rows = [("first call, writes prefix", 21500, 0, 20000, 400), ("later call, reads prefix", 21800, 20000, 0, 300),
        ("late call, reads bigger prefix", 60000, 58000, 0, 500), ("no cache in use", 3000, 0, 0, 200)]
print("SYNTHETIC rows. Columns: OTel-style input (incl cache), cache read, cache write, output -> cr-2 uncached input; correct USD; naive USD")
tc = tn = 0
for name, i, r, w, o in rows:
    c, n = priced_both_ways(i, r, w, o); tc += c; tn += n
    print(f"  {name:32s} {i:6d} {r:6d} {w:6d} {o:4d} -> {otel_to_cr2(i, r, w):6d}  ${c:.5f}  ${n:.5f}  naive/correct {n/c:.2f}")
print(f"  total correct ${tc:.5f}, naive ${tn:.5f}, naive overstates by {tn/tc-1:.1%}")
try:
    otel_to_cr2(1000, 900, 300)
except ValueError as e:
    print("  impossible row refused:", e)
