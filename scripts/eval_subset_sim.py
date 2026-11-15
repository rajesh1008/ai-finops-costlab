#!/usr/bin/env python3
"""Chapter 43 follow-up (nineteenth run), OFFLINE, no API calls. Re-uses the real graded outputs of runs/levers-stack-lab-2026-11-11.json (arms A0, A0c, A1, A2 over the same 120 items, each item graded ok or not).
Question: if the team had graded only a random fraction f of the items, how far would each arm's accuracy move, how often would the ordering of the four arms change, and how often would the
A1-versus-A0 gap (the cheap arm's loss) change sign? 2,000 random subsets per fraction, seed 5. Stratified variant: equal share from each template. Output runs/eval-subset-sim-2026-11-11.txt."""
import json, random, statistics as st
from pathlib import Path
d = json.loads((Path(__file__).resolve().parents[1] / "runs" / "levers-stack-lab-2026-11-11.json").read_text())["results"]
ARMS = ["A0", "A0c", "A1", "A2"]; acc = {a: {} for a in ARMS}; tmpl = {}
for r in d:
    if r["arm"] in acc and not r["error"]: acc[r["arm"]][r["i"]] = 1 if r["ok"] else 0; tmpl[r["i"]] = r["t"]
items = sorted(set.intersection(*[set(acc[a]) for a in ARMS]))
full = {a: sum(acc[a][i] for i in items) / len(items) for a in ARMS}
rank = lambda m: tuple(sorted(ARMS, key=lambda a: (-m[a], a)))
lines = [f"items graded in all four arms: {len(items)}", "full-set accuracy: " + ", ".join(f"{a} {full[a]:.3f}" for a in ARMS), f"full-set ordering: {' > '.join(rank(full))}"]
gap_full = full["A1"] - full["A0"]; lines.append(f"A1 minus A0 on the full set: {gap_full:+.3f}")
rng = random.Random(5); by_t = {}
for i in items: by_t.setdefault(tmpl[i], []).append(i)
def draw(f, strat):
    if not strat: return rng.sample(items, max(2, round(f * len(items))))
    out = []
    for t, v in by_t.items(): out += rng.sample(v, max(1, round(f * len(v))))
    return out
for strat in (False, True):
    lines.append("stratified by template" if strat else "simple random subset")
    for f in (0.1, 0.2, 0.3, 0.4, 0.5):
        maes, same_order, same_sign, gaps = [], 0, 0, []
        for _ in range(2000):
            s = draw(f, strat); m = {a: sum(acc[a][i] for i in s) / len(s) for a in ARMS}
            maes.append(st.mean(abs(m[a] - full[a]) for a in ARMS)); same_order += rank(m) == rank(full)
            g = m["A1"] - m["A0"]; gaps.append(g); same_sign += (g < 0) == (gap_full < 0)
        gaps.sort()
        lines.append(f"  f={f:.1f} n={len(draw(f, strat))}: mean abs error of arm accuracy {st.mean(maes):.3f}; same ordering {same_order/20:.1f}%; A1-A0 gap same sign {same_sign/20:.1f}%; gap 5th to 95th pct {gaps[100]:+.3f} to {gaps[1900]:+.3f}")
Path(__file__).resolve().parents[1].joinpath("runs", "eval-subset-sim-2026-11-11.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
