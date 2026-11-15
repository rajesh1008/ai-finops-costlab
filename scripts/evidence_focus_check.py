#!/usr/bin/env python3
"""Chapter 34: map the 1,800-record evidence ledger to FOCUS-shaped rows with costlab.focus (the Chapter 8 mapping, FOCUS 1.5 working-draft names, provisional until ratification on 3 December 2026).
Days are the lab's SYNTHETIC days (October 2026); the credential id is derived from the team label. Reports row counts, the token double-count check, and which pack fields have no FOCUS column and travel as x_ extensions."""
import json
from datetime import datetime
from costlab.focus import StrictCostRecord, to_focus_rows, credential_id, token_total, check_no_double_count
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence_pack_lab import load
def main():
    recs = load(); rows = []; tot = 0
    for r in recs:
        rec = StrictCostRecord(schema_version="cr-2", record_id=r["id"], occurred_at=datetime(2026, 10, r["day"]), vendor="anthropic", model=r["model"], credential_id=credential_id(r["team"] or "unknown"),
                               product=r["team"] or None, feature=r["feature"] or None, tenant=None, input_tokens=r["in"], output_tokens=r["out"], cache_read_tokens=0, cache_write_tokens=0)
        fr = to_focus_rows(rec); rows += fr; tot += token_total(rec); assert check_no_double_count(fr, token_total(rec))
    print(f"ledger records {len(recs)} -> FOCUS-shaped rows {len(rows)} ({len(rows)/len(recs):.2f} per record); tokens in rows {sum(x['ConsumedQuantity'] for x in rows)} against ledger tokens {tot}")
    cols = sorted({k for x in rows for k in x}); print("columns used:", ", ".join(cols))
    pack = ["prev", "h", "price_table_version", "price_effective_date", "recomputed_cost_usd", "attribution_complete", "invoice_line_id", "exception_id", "env", "day"]
    print("pack fields without a FOCUS column in this mapping (carried as x_ extensions):", ", ".join(p for p in pack if p not in ("day",)))
    size_ledger = sum(len(json.dumps(r, sort_keys=True, separators=(",", ":"))) + 1 for r in recs); size_rows = sum(len(json.dumps(x, sort_keys=True, separators=(",", ":"))) + 1 for x in rows)
    print(f"bytes: plain records {size_ledger:,}; FOCUS-shaped rows {size_rows:,} ({size_rows/size_ledger:.2f}x)")
if __name__ == "__main__": main()
