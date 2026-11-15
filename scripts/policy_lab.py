#!/usr/bin/env python3
"""Chapter 32 lab. Replays the cost policy in costlab.policy over 2,850 REAL recorded calls: the 600 calls of the Chapter 28 shadow run and the 2,250 calls of the Chapter 29 judge run (model, input tokens, output tokens, max_tokens as set in those scripts).
Team and purpose tags are ASSIGNED by me (SYNTHETIC): shadow calls team=support purpose=answer; judge calls team=quality purpose=judge, ref_h5 purpose=judge_ref; 3 percent of calls (seeded) lose their purpose tag to model a missed tagging step.
Pre-flight check: count_tokens counts (tokenizer-lab, REAL) against the billed input tokens of the same prompts. Prices are the dated placeholders; spend here is arithmetic over recorded tokens."""
import json, random, statistics
from pathlib import Path
from costlab.policy import Request, Rule, Exemption, decide, replay, worst_case_usd, refusal_message
from costlab.estimate import estimate_usd
R = Path(__file__).resolve().parents[1] / "runs"
A, B = "claude-haiku-4-5-20251001", "claude-haiku-5-5"
JMAX = {"ctx_h5": 24, "ctx_h4": 24, "ref_h5": 24, "cot_h5": 300, "think_h5": 700}
def pct(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))]
def load():
    rnd = random.Random(321); reqs = []; meta = []
    sh = json.load(open(R / "shadow-lab-2026-11-10.json"))["results"]
    for r in sh:
        if r["error"] is None: reqs.append(Request(r["model"], r["in"], 120, team="support", purpose="answer")); meta.append((r["in"], r["out"]))
    jd = json.load(open(R / "judge-lab-2026-11-10.json")); models = {k: v[0] for k, v in jd["judges"].items()}
    for r in jd["results"]:
        if r["error"] is None: reqs.append(Request(models[r["judge"]], r["in"], JMAX[r["judge"]], team="quality", purpose="judge_ref" if r["judge"] == "ref_h5" else "judge")); meta.append((r["in"], r["out"]))
    for q in reqs:
        if rnd.random() < 0.03: q.purpose = ""
    return reqs, meta
def actual(q, m): return estimate_usd("anthropic:" + q.model, m[0], m[1])
def replay_with(reqs, rules, ex):
    return sum(1 for q in reqs if not decide(q, rules, ex, today='2026-11-11').allowed)
def main():
    reqs, meta = load(); n = len(reqs); tot = sum(actual(q, m) for q, m in zip(reqs, meta))
    print(f"requests {n}; actual spend over the log ${tot:.4f} at placeholder rates; untagged purpose {sum(1 for q in reqs if not q.purpose)}")
    tk = json.load(open(R / "tokenizer-lab-2026-11-11.json")); cnt = {(r["q"], r["model"]): r["count"] for r in tk}
    sh = [r for r in json.load(open(R / "shadow-lab-2026-11-10.json"))["results"] if r["error"] is None]
    same = sum(1 for r in sh if cnt.get((r["q"], r["model"])) == r["in"]); diff = [cnt[(r["q"], r["model"])] - r["in"] for r in sh if cnt.get((r["q"], r["model"])) != r["in"]]
    print(f"pre-flight count_tokens equals billed input tokens: {same} of {len(sh)} calls; where different, difference range {min(diff) if diff else 0} to {max(diff) if diff else 0}")
    print("\n== worst-case estimate (input + max_tokens at output rate) against actual cost ==")
    groups = {}
    for q, m in zip(reqs, meta): groups.setdefault((q.team, q.purpose or "(untagged)", q.model, q.max_tokens), []).append(worst_case_usd(q.model, q.input_tokens, q.max_tokens) / actual(q, m))
    for k, v in sorted(groups.items()): print(f"{k[0]:<8}{k[1]:<11}{k[2][:16]:<17}max {k[3]:>4}  n {len(v):>4}  worst/actual median {statistics.median(v):5.2f}x  p90 {pct(v,.9):5.2f}x  max {max(v):6.2f}x")
    print("\n== price ceiling sweep: requests the ceiling would refuse (worst-case estimate) and the share of actual spend they carried ==")
    for c in (0.0003, 0.0005, 0.0008, 0.0012, 0.002, 0.004):
        rr = replay(reqs, [Rule("c", "price_ceiling", {"usd": c})]); bl = [i for i, d in enumerate(rr["decisions"]) if not d.allowed]
        sp = sum(actual(reqs[i], meta[i]) for i in bl)
        print(f"ceiling ${c:.4f}: refuses {len(bl):>5} ({len(bl)/n*100:5.1f}%), carried ${sp:.4f} ({sp/tot*100:5.1f}% of spend)")
    print("\n== policy v1 in shadow, then enforcing ==")
    base = [Rule("R1_allowlist", "model_allowlist", {"allowed": [A, B]}),
            Rule("R2_tags", "required_tags", {"tags": ["team", "purpose"]}),
            Rule("R3_ceiling", "price_ceiling", {"usd": 0.0012}),
            Rule("R4_legacy", "legacy_model", {"models": [A], "exempt_purposes": ["judge_ref"]}),
            Rule("R5_tokens", "max_tokens_ceiling", {"max_tokens": 300})]
    for mode in ("shadow", "enforce"):
        rules = [Rule(r.id, r.kind, r.params, mode=mode) for r in base]; rr = replay(reqs, rules)
        print(f"mode {mode}: blocked {rr['blocked']} of {n}")
        for k, v in rr["per_rule"].items(): print(f"   {k:<14} fires {v['fires']:>5}  blocks {v['blocks']:>5}")
        if mode == "enforce":
            bl = [i for i, d in enumerate(rr["decisions"]) if not d.allowed]; sp = sum(actual(reqs[i], meta[i]) for i in bl)
            print(f"   blocked requests carried ${sp:.4f} of ${tot:.4f} ({sp/tot*100:.1f}%)")
            by = {}
            for i in bl:
                for rid in rr["decisions"][i].denied_by: by.setdefault(rid, []).append(i)
            for rid, ii in by.items(): print(f"   {rid}: ${sum(actual(reqs[i], meta[i]) for i in ii):.4f} over {len(ii)} requests")
            only = [i for i in bl if len(rr["decisions"][i].denied_by) == 1]
            print(f"   blocked by exactly one rule: {len(only)}; by two or more: {len(bl)-len(only)}")
    # exception queue: the distinct (team, purpose, rules) groups the enforcing policy refused, as the list a reviewer would face
    rules = [Rule(r.id, r.kind, r.params, mode="enforce") for r in base]; groups = {}
    for q, m in zip(reqs, meta):
        d = decide(q, rules)
        if not d.allowed:
            g = groups.setdefault((q.team, q.purpose or "(untagged)", q.model[:16], tuple(d.denied_by)), [0, 0.0]); g[0] += 1; g[1] += actual(q, m)
    print("\n== exception queue under the enforcing policy: groups a reviewer would see ==")
    for k, (c, sp) in sorted(groups.items(), key=lambda kv: -kv[1][1]): print(f"  {k[0]:<8}{k[1]:<11}{k[2]:<17}{', '.join(k[3]):<28} {c:>5} requests ${sp:.4f}")
    ex = [Exemption("R4_legacy", "support", "answer", "2026-12-31", "marcus.hale"), Exemption("R5_tokens", "quality", "judge", "2026-12-31", "tanya.brooks")]
    after = replay_with(reqs, rules, ex)
    print(f"with two dated exemptions (R4 for support/answer, R5 for quality/judge): blocked {after} of {n}")
    sample = next(q for q in reqs if q.model == A and q.purpose == "answer")
    print("example refusal text:", refusal_message([x for x in rules if x.id == "R4_legacy"][0], sample))
    # team month cap in order of arrival, using actual spend so far
    print("\n== team month cap, requests in recorded order, cap judged on worst-case of the incoming request plus spend so far ==")
    for cap in (0.05, 0.2, 0.5):
        sp = {}; blocked = 0; carried = 0.0
        for q, m in zip(reqs, meta):
            q.month_spend_team = sp.get(q.team, 0.0); d = decide(q, [Rule("cap", "team_month_cap", {"usd": cap})])
            if d.allowed: sp[q.team] = sp.get(q.team, 0.0) + actual(q, m)
            else: blocked += 1; carried += actual(q, m)
        print(f"cap ${cap:.2f} per team: blocked {blocked}, spend admitted ${sum(sp.values()):.4f}, spend refused ${carried:.4f}; first-block position matters: support ${sp.get('support',0):.4f} quality ${sp.get('quality',0):.4f}")
if __name__ == "__main__": main()
