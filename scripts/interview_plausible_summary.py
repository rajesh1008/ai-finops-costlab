#!/usr/bin/env python3
"""Ch47 summary for both plausible-weak-answer runs (h45-written, eighteenth run; h55-written, nineteenth run). Offline. Picks of the strong answer by grader, per generator."""
import json, statistics as st
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "runs"; lines = []
for gen, fn in (("h45-written weak", "interview-plausible-lab-2026-11-11.json"), ("h55-written weak", "interview-plausible-h55gen-lab-2026-11-11.json"), ("h55-written weak, length-gated", "interview-plausible-h55match-lab-2026-11-11.json")):
    d = json.loads((R / fn).read_text()); res = d["results"]; n_items = len(d["q"]); ok_items = [i for i, w in enumerate(d["len_weak"]) if w]
    ls = [x for x in d["len_strong"]]; lw = [x for x in d["len_weak"] if x]
    lines.append(f"{gen}: items {n_items} (with a weak answer: {len(ok_items)}); median words strong (those items) {st.median([ls[i] for i in ok_items])} weak {st.median(lw)}")
    for m in ("h45", "h55"):
        rs = [r for r in res if r["m"] == m]; s = sum(r["picked"] == "strong" for r in rs)
        o0 = [r for r in rs if r["order"] == 0]; o1 = [r for r in rs if r["order"] == 1]
        a = sum(r["picked"] == "strong" for r in o0); b = sum(r["picked"] == "strong" for r in o1)
        first = sum(r["choice"] == "A" for r in rs)
        lines.append(f"  grader {m}: picked strong {s}/{len(rs)} (strong first {a}/{len(o0)}, strong second {b}/{len(o1)}); chose position A {first}/{len(rs)}")
    # longer-wins rule
    lw_rule = 0
    for i in range(n_items):
        if d["len_weak"][i]: lw_rule += d["len_strong"][i] > d["len_weak"][i]
    lines.append(f"  longer-wins picks strong in {lw_rule}/{sum(1 for x in d['len_weak'] if x)} items")
    # items where either grader picked weak in both orders
    both = 0
    for i in range(n_items):
        rs = [r for r in res if r["i"] == i and r["picked"]]
        if rs and all(r["picked"] == "weak" for r in rs): both += 1
    lines.append(f"  items where all four gradings picked the weak answer: {both}")
(R / "interview-plausible-summary-2026-11-11b.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
