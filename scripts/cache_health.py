#!/usr/bin/env python3
"""Chapter 18: read the layout lab's cost records and report cache health per layout."""
import json
from pathlib import Path
from collections import defaultdict
from costlab.cachelab import cache_health
runs = Path(__file__).resolve().parents[1] / "runs"
by = defaultdict(list)
for line in (runs / "cache-layout-2026-11-10.jsonl").read_text().splitlines():
    r = json.loads(line); by[r["feature"]].append(r)
print("layout  calls  in    write   read   est_usd  read_share  write_without_read")
for f in sorted(by):
    rs = by[f]; h = cache_health(rs)
    print(f"{f:9s} {h['calls']}  {sum(r['input_tokens'] for r in rs):5d} {sum(r['cache_write_tokens'] for r in rs):6d} {sum(r['cache_read_tokens'] for r in rs):6d}  "
          f"{sum(r['estimated_cost_usd'] for r in rs):.5f}  {h['read_share_of_input']:.2f}      {h['write_without_read']}")
