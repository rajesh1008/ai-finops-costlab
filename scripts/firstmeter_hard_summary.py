#!/usr/bin/env python3
"""Ch42 follow-up summary of runs/firstmeter-hard-lab-2026-11-11.json (offline)."""
import json
from pathlib import Path
from costlab.firstmeter_hard import parse_hard, HARD
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P
R = Path(__file__).resolve().parents[1] / "runs"; d = json.loads((R / "firstmeter-hard-lab-2026-11-11.json").read_text()); reqs = d["requests"]
PM = {"h45": "anthropic:claude-haiku-4-5-20251001", "h55": "anthropic:claude-haiku-5-5"}; lines = []
for m in ("h45", "h55"):
    for v in "UG":
        rs = [x for x in d["results"] if x["m"] == m and x["view"] == v]
        rows = [(reqs[x["i"]]["feature"], parse_hard(x["text"])) for x in rs]; ok = sum(a == b for a, b in rows); unk = sum(b == "unknown" for _, b in rows)
        wrong = sum(a != b and b != "unknown" for a, b in rows); p = P[PM[m]]; cost = sum(x["in"] * p["input"] + x["out"] * p["output"] for x in rs) / 1e6
        lines.append(f"{m} view {v}: right {ok}/{len(rows)}, wrong {wrong}, unknown {unk}, errors {sum(1 for x in rs if x['error'])}, classifier cost ${cost:.4f}")
        c = {}
        for r in rows: c[r] = c.get(r, 0) + 1
        for f in HARD: lines.append(f"    {f}: " + str({l: c[(f, l)] for l in HARD + ['unknown', 'unparsed'] if (f, l) in c}))
(R / "firstmeter-hard-summary-2026-11-11.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
# spend-weighted view with ASSUMED per-request token weights (support 6200, report 3100, sql 900, explainer 1500; the explainer weight is a new assumption)
W = {"support_assistant": 6200, "report_summariser": 3100, "sql_helper": 900, "metric_explainer": 1500}; extra = []
for m in ("h45", "h55"):
    for v in "UG":
        rs = [x for x in d["results"] if x["m"] == m and x["view"] == v]; tot = sum(W[reqs[x["i"]]["feature"]] for x in rs)
        wrong = sum(W[reqs[x["i"]]["feature"]] for x in rs if parse_hard(x["text"]) not in (reqs[x["i"]]["feature"], "unknown"))
        unk = sum(W[reqs[x["i"]]["feature"]] for x in rs if parse_hard(x["text"]) == "unknown")
        extra.append(f"{m} view {v} ASSUMED weights: misattributed share {wrong / tot:.3f}, unknown share {unk / tot:.3f}")
(R / "firstmeter-hard-summary-2026-11-11.txt").write_text("\n".join(lines + extra) + "\n"); print("\n".join(extra))
