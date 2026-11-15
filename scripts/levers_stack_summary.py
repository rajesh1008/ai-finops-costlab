#!/usr/bin/env python3
"""Chapter 43 summary of runs/levers-stack-lab-2026-11-11.json."""
import json
from pathlib import Path
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P
from costlab.stackmath import arm_cost, per_1000, saving, naive_stack, additive_stack
d = json.loads((Path(__file__).resolve().parents[1] / "runs" / "levers-stack-lab-2026-11-11.json").read_text())["results"]
PR = {"A0": P["anthropic:claude-haiku-4-5-20251001"], "A0c": P["anthropic:claude-haiku-4-5-20251001"], "A1": P["anthropic:claude-haiku-4-5-20251001"], "A2": P["anthropic:claude-haiku-5-5"]}
out = {}
for a in ("A0", "A0c", "A1", "A2"):
    rs = [r for r in d if r["arm"] == a]; n = len(rs); ok = sum(1 for r in rs if r["ok"]); c = arm_cost(rs, PR[a])
    out[a] = (c, n, ok)
    tin = sum(r["in"] for r in rs) / n; cr = sum(r["cr"] for r in rs) / n; cw = sum(r["cw"] for r in rs)
    print(f"{a}: n={n} correct={ok} cost/1000=${per_1000(c, n):.3f} cost per correct=${c / max(ok, 1):.5f} mean_in={tin:.0f} mean_cache_read={cr:.0f} cache_write_total={cw} errors={sum(1 for r in rs if r['error'])}")
b = out["A0"][0] / out["A0"][1]
s_cache = saving(b, out["A0c"][0] / out["A0c"][1]); s_diet = saving(b, out["A1"][0] / out["A1"][1]); s_model_on_diet = saving(out["A1"][0] / out["A1"][1], out["A2"][0] / out["A2"][1])
s_stack = saving(b, out["A2"][0] / out["A2"][1])
print(f"saving vs A0: cache {s_cache:.3f}, context diet {s_diet:.3f}, model switch on top of diet {s_model_on_diet:.3f}, measured diet+model {s_stack:.3f}")
print(f"claimed if cache and diet both added: additive {additive_stack([s_cache, s_diet]):.3f}, multiplicative {naive_stack([s_cache, s_diet]):.3f}; measured best single {max(s_cache, s_diet):.3f}")
print(f"claimed three-lever (cache, diet, model-on-diet) additive {additive_stack([s_cache, s_diet, s_model_on_diet]):.3f} multiplicative {naive_stack([s_cache, s_diet, s_model_on_diet]):.3f} vs measured diet+model {s_stack:.3f}")
for a in ("A0", "A1", "A2"):
    cl = {"correct": 0, "other": 0}
    rs = [r for r in d if r["arm"] == a]
    for t in "ABC":
        x = [r for r in rs if r["t"] == t]; print(f"   {a} template {t}: {sum(1 for r in x if r['ok'])}/{len(x)}")
