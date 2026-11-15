#!/usr/bin/env python3
"""Chapter 19 arithmetic (no API). 40-step session, ASSUMED: 2,000-token base, 600-token tool result a step, 150 output tokens, Haiku 4.5 rates.
Policies change what is in the prompt; the cache only reads an unchanged prefix. No quality is modelled."""
from costlab.context import session_cost_policy
print("policy        steps  usd    tokens_sent  cache_write  cache_read  (vs raw)")
for steps in (20, 40, 80):
    raw = session_cost_policy(steps, "raw")[0]
    for pol, kw in (("raw", {}), ("mask_every", {}), ("mask_batch", {"k": 5}), ("mask_batch", {"k": 10}), ("mask_batch", {"k": 20})):
        u, t, w, r = session_cost_policy(steps, pol, **kw)
        name = pol + (f"/{kw['k']}" if kw else "")
        print(f"{name:12s} {steps:5d}  {u:.4f}  {t:10.0f}  {w:10.0f}  {r:10.0f}   {u/raw:.2f}x")
    print()
