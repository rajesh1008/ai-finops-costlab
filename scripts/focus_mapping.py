#!/usr/bin/env python3
"""Chapter 8: upgrade the real lab records to Cost Record v2, map them to FOCUS 1.5-shaped rows,
then run two failure injections (silent rename; double-counted cache tokens). No API calls."""
import json
from pathlib import Path
from collections import Counter
from costlab.focus import (StrictCostRecord, upgrade_v1, to_focus_rows, token_total,
                           check_no_double_count, try_validate)
from costlab.records import CostRecord

runs = Path(__file__).resolve().parent.parent / "runs"
v1 = [json.loads(l) for src in ("meter-2026-11-10.jsonl", "cache-experiment-2026-11-10.jsonl")
      for l in (runs / src).read_text().splitlines()]
v2 = [StrictCostRecord(**upgrade_v1(d)) for d in v1]
rows = [r for rec in v2 for r in to_focus_rows(rec)]
print(f"v1 records {len(v1)}; v2 records {len(v2)}; FOCUS-shaped rows {len(rows)}")
c = Counter(json.loads(r['SkuPriceDetails'])['TokenDirection'] + '/' + json.loads(r['SkuPriceDetails'])['TokenCacheAction'] for r in rows)
for k, n in sorted(c.items()):
    q = sum(r['ConsumedQuantity'] for r in rows if json.loads(r['SkuPriceDetails'])['TokenDirection'] + '/' + json.loads(r['SkuPriceDetails'])['TokenCacheAction'] == k)
    print(f"  {k:16s} rows {n:3d} tokens {q:8,d}")
ok = all(check_no_double_count(to_focus_rows(r), token_total(r)) for r in v2)
print("every record's rows sum to its token total:", ok)
print("\nExample record rows (cache-lab write call):")
ex = next(r for r in v2 if r.cache_write_tokens)
for r in to_focus_rows(ex):
    print(" ", r["SkuMeter"], r["ConsumedQuantity"], r["SkuPriceDetails"])

print("\n--- Injection A: a producer renames input_tokens to prompt_tokens, no version bump ---")
d = dict(v1[0]); d["prompt_tokens"] = d.pop("input_tokens")
lenient = CostRecord(**{k: v for k, v in d.items()})   # v1 model, pydantic default ignores extras
print(f"lenient v1 model accepts it: input_tokens = {lenient.input_tokens} (true value {v1[0]['input_tokens']})")
renamed = upgrade_v1(d)
print("strict v2 model:", try_validate(renamed))
tot_in = sum(r["input_tokens"] for r in v1)
print(f"if every record arrived renamed the lenient total input would read 0 against {tot_in:,}")

print("\n--- Injection B: a producer folds cache tokens into input AND reports them separately ---")
reads = [r for r in v2 if r.cache_read_tokens]
rec = reads[0]
provider_total = token_total(rec)
bad = rec.model_copy(update={"input_tokens": rec.input_tokens + rec.cache_read_tokens + rec.cache_write_tokens})
bad_rows = to_focus_rows(bad)
print(f"provider total {provider_total:,}; rows sum {sum(r['ConsumedQuantity'] for r in bad_rows):,}; check passes: {check_no_double_count(bad_rows, provider_total)}")
over = sum(r['ConsumedQuantity'] for r in bad_rows) - provider_total
print(f"tokens counted twice {over:,}")
