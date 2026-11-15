#!/usr/bin/env python3
"""Chapter 5: reconcile a synthetic month of gateway records to four invoice lines within 2 percent.

SYNTHETIC. There is no real Fieldstone gateway. The log is generated from the October fixture's
token lines, with seeded daily jitter. Two conditions are run:
  clean:      every call goes through the gateway
  lambda-key: a vendor key sits in a Lambda and 7 percent of one vendor's tokens bypass the gateway
Rates are the invoice's own implied unit prices, so the clean month reconciles by construction;
the exercise is the bypass, not the arithmetic.
"""
import json, random
from pathlib import Path
from costlab.reconcile import reconcile

fx = json.loads((Path(__file__).parent.parent / "fixtures" / "fieldstone_invoices.json").read_text())
token_lines = [l for l in fx["lines"] if l["unit"] in ("input_tokens", "output_tokens") and l["product_tag"] or
               (l["unit"] in ("input_tokens", "output_tokens") and l["vendor"] == "google-vertex")]
invoice = {f'{l["vendor"]}:{l["unit"]}': l["amount_usd"] for l in token_lines}


def build_meter(bypass_key=None, bypass_share=0.0, seed=5):
    rnd = random.Random(seed)
    meter, records = {}, 0
    for l in token_lines:
        key = f'{l["vendor"]}:{l["unit"]}'
        rate = l["amount_usd"] / l["quantity"]
        weights = [rnd.uniform(0.7, 1.3) * (1 + 0.2 * d / 30) for d in range(31)]
        s = sum(weights)
        total = 0.0
        for w in weights:
            q = l["quantity"] * w / s
            if key == bypass_key:
                q *= 1 - bypass_share
            total += q * rate
            records += 1
        meter[key] = total
    return meter, records


for label, key, share in (("clean", None, 0.0), ("lambda-key", "anthropic:input_tokens", 0.07)):
    meter, n = build_meter(key, share)
    print(f"--- {label}: {n} daily rollups, tolerance 2%")
    for v, ok in reconcile(meter, invoice, 0.02):
        print(f"{v.key:32s} meter ${v.meter_usd:>10,.0f}  invoice ${v.invoice_usd:>10,.0f}  gap {v.gap_pct:>6.2%}  {'ok' if ok else 'OUT OF TOLERANCE'}")
    t_m, t_i = sum(meter.values()), sum(invoice.values())
    print(f"{'total':32s} meter ${t_m:>10,.0f}  invoice ${t_i:>10,.0f}  gap {(t_i - t_m) / t_i:>6.2%}")
