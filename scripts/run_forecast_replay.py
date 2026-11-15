#!/usr/bin/env python3
"""Chapter 24 follow-up (nineteenth run), OFFLINE replay of the 16 recorded 20-step runs of runs/loop-growth-lab-2026-11-11.json (real token counts). After k completed calls, forecast the total tokens of a 20-call run two ways:
(naive) tokens so far divided by k, times 20; (growth) fit input length linear in call number on the k calls seen (least squares), extrapolate the input of calls k+1..20, add the mean output per call so far.
Report mean absolute percentage error against the recorded total, and the mean signed error (negative means underestimate). Output runs/run-forecast-replay-2026-11-11.txt."""
import json, statistics as st
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "runs"; d = [r for r in json.loads((R / "loop-growth-lab-2026-11-11.json").read_text())["results"] if not r["error"] and len(r["calls"]) == 20]
def naive(c, k): return sum(i + o for i, o in c[:k]) / k * 20
def growth(c, k):
    xs = list(range(k)); ys = [c[j][0] for j in range(k)]; mx, my = st.mean(xs), st.mean(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs); a = my - b * mx
    seen = sum(i + o for i, o in c[:k]); mo = st.mean(o for _, o in c[:k])
    return seen + sum(a + b * j + mo for j in range(k, 20))
lines = [f"runs used: {len(d)} (all 20 calls); models pooled: {sorted(set(r['m'] for r in d))}", "k | naive MAPE, mean signed error | growth-fit MAPE, mean signed error"]
for k in (3, 5, 8, 12, 16):
    en, eg = [], []
    for r in d:
        c = r["calls"]; T = sum(i + o for i, o in c); en.append((naive(c, k) - T) / T); eg.append((growth(c, k) - T) / T)
    lines.append(f"k={k}: naive {st.mean(abs(x) for x in en)*100:.1f}%, {st.mean(en)*100:+.1f}% | growth {st.mean(abs(x) for x in eg)*100:.1f}%, {st.mean(eg)*100:+.1f}%")
(R / "run-forecast-replay-2026-11-11.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
