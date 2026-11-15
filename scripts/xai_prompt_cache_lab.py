"""Real-API lab (mode: xai-api). xAI's automatic prompt caching across calls that share a long prefix.

Measured on xAI's Grok API (default model grok-4.20-0309-non-reasoning) and priced at xAI's list prices
(costlab.backends.xai, read 16 Nov 2026). Not a Claude call and not an Anthropic invoice figure; the
"as-if Anthropic" column re-prices the same token counts at claude-haiku-4-5 list prices, for comparison only.

Three arms, each with its own run id at the very start of the prefix so its first call is a true cold start:
  A  same ~5,000-token policy prefix, x-grok-conv-id set, calls separated by growing gaps (0 s to 10 min)
  B  same layout, no x-grok-conv-id, six calls back to back (does routing matter?)
  C  the varying question placed BEFORE the policy text, conv id set, four calls (prefix layout)
19 calls, max_tokens 16. Wall time about 20 minutes (the gaps).

16 Nov 2026 run (4:18 to 4:38 AM IST), prompt about 3,695 tokens: every cold call still showed 128 cached tokens
(xAI's own server-side preamble). Warm calls cached 3,584 tokens (97%) and cost $0.00089 against $0.00450 cold,
about 5x cheaper. Arm A hit at gaps of 0 s, 5 s, 15 s, 60 s, 120 s, 300 s and 600 s but MISSED at 30 s, so
eviction/routing, not a fixed TTL, decides a miss. Arm B (no conv id) missed on calls 1-2 and hit from call 3
(call 4 on a partial first attempt). Arm C (question first) never hit beyond the 128-token preamble. Lab total
$0.046 at xAI list prices, equal to the cost xAI reported in cost_in_usd_ticks.
Needs XAI_API_KEY in the environment. Output: runs/xai/prompt-cache-gaps-<date>.json and .txt
"""
import argparse, datetime, json, pathlib, sys, time, uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from costlab.backends.xai import XaiBackend, XaiError

RULES = [("tagging", "every request to a hosted model must carry a team tag, a feature tag and a budget owner"),
         ("caps", "requests above the daily cap for a feature are queued for batch processing overnight"),
         ("routing", "classification and extraction go to the smallest model that passes the feature's eval set"),
         ("caching", "system prompts and reference documents are placed first so the provider can reuse them"),
         ("review", "any feature whose cost per successful task rises 20% week on week is reviewed by its owner")]
POLICY = "Fieldstone Analytics model-usage policy, version 7.\n" + "\n".join(
    f"Section {i}.{j} ({name}): {text}; exceptions need written approval from the FinOps lead, and approvals "
    f"expire after ninety days unless renewed in the monthly cost review."
    for i in range(1, 15) for j, (name, text) in enumerate(RULES, 1)) + "\nAnswer in one short sentence.\n"
QUESTIONS = ["Who owns a request's cost?", "What happens above the daily cap?", "Which tags are required?",
             "Where should system prompts go?", "When is a feature reviewed?", "How long do approvals last?",
             "Who approves exceptions?", "What model handles extraction?"]
GAPS_A = [0, 0, 5, 15, 30, 60, 120, 300, 600]   # seconds to wait BEFORE each arm-A call


def run(args):
    b = XaiBackend(args.model, as_if_anthropic_model=args.as_if, timeout=90)
    rows, t_prev = [], {}

    def call(arm, idx, prefix_first, conv, q, gap_planned):
        pid = run_ids[arm]
        policy = f"Run {pid}.\n{POLICY}"
        content = f"{policy}\nQ: {q}\nA:" if prefix_first else f"Q: {q}\n\n{policy}\nA:"
        now = time.time()
        actual_gap = round(now - t_prev[arm], 1) if arm in t_prev else None
        try:
            r = b.chat([{"role": "user", "content": content}], max_tokens=16, conv_id=conv)
            d = r.as_dict()
        except XaiError as e:
            d = {"error": str(e)}
        t_prev[arm] = time.time()
        row = {"arm": arm, "call": idx, "conv_id_set": bool(conv), "prefix_first": prefix_first,
               "planned_gap_s": gap_planned, "actual_gap_s": actual_gap,
               "at": datetime.datetime.now().isoformat(timespec="seconds"), **d}
        rows.append(row)
        if "error" in row:
            print(arm, idx, "ERROR", row["error"][:200], flush=True)
        else:
            print(arm, idx, f"gap={actual_gap} prompt={row['prompt_tokens']} cached={row['cached_tokens']} "
                  f"ms={row['wall_ms']:.0f} usd={row['cost_xai']['total']:.6f}", flush=True)

    run_ids = {a: f"{a}-{uuid.uuid4().hex[:12]}" for a in "ABC"}
    for i in range(6):
        call("B", i + 1, True, None, QUESTIONS[i], 0)
    conv_c = f"costlab-{run_ids['C']}"
    for i in range(4):
        call("C", i + 1, False, conv_c, QUESTIONS[i], 0)
    conv_a = f"costlab-{run_ids['A']}"
    for i, g in enumerate(GAPS_A if not args.quick else GAPS_A[:4]):
        time.sleep(g)
        call("A", i + 1, True, conv_a, QUESTIONS[i % len(QUESTIONS)], g)
    return b, rows


def summarise(rows):
    out = {}
    for arm in "ABC":
        rs = [r for r in rows if r["arm"] == arm and "error" not in r]
        if not rs:
            continue
        p = sum(r["prompt_tokens"] for r in rs)
        c = sum(r["cached_tokens"] for r in rs)
        warm = rs[1:]
        out[arm] = {"calls": len(rs), "prompt_tokens": p, "cached_tokens": c,
                    "cache_hit_rate_all": round(c / p, 4) if p else None,
                    "cache_hit_rate_after_first": (round(sum(r["cached_tokens"] for r in warm) /
                                                         sum(r["prompt_tokens"] for r in warm), 4) if warm else None),
                    "usd_xai_total": round(sum(r["cost_xai"]["total"] for r in rs), 6),
                    "usd_xai_reported_total": round(sum(r["xai_reported_usd"] or 0 for r in rs), 6),
                    "usd_as_if_anthropic_total": round(sum((r["cost_as_if_anthropic"] or {}).get("total", 0)
                                                           for r in rs), 6),
                    "usd_first_call": round(rs[0]["cost_xai"]["total"], 6),
                    "median_ms": sorted(r["wall_ms"] for r in rs)[len(rs) // 2]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="grok-4.20-0309-non-reasoning")
    ap.add_argument("--as-if", default="claude-haiku-4-5")
    ap.add_argument("--quick", action="store_true", help="arm A stops after 4 calls (no long gaps)")
    args = ap.parse_args()
    b, rows = run(args)
    today = datetime.date.today().isoformat()
    out = {**b.provenance(), "lab": "xAI automatic prompt caching vs gap, routing and layout", "run_date": today,
           "summary": summarise(rows), "calls": rows}
    d = pathlib.Path(__file__).resolve().parents[1] / "runs" / "xai"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"prompt-cache-gaps-{today}.json").write_text(json.dumps(out, indent=2))
    lines = [f"mode: xai-api | model: {b.model} | priced at xAI list prices dated {out['pricing_date']} "
             f"({out['pricing_source']})", out["note"],
             f"as-if column: same tokens at {args.as_if} Anthropic list prices dated {out['as_if_anthropic']['pricing_date']}"
             " (a calculation, not a measurement)", "",
             f"{'arm':>3} {'call':>4} {'conv':>4} {'layout':>9} {'gap_s':>6} {'prompt':>6} {'cached':>6} {'hit%':>5} "
             f"{'ms':>6} {'xAI USD':>10} {'as-if USD':>10}"]
    for r in rows:
        if "error" in r:
            lines.append(f"{r['arm']:>3} {r['call']:>4} ERROR {r['error'][:120]}")
            continue
        hit = 100 * r["cached_tokens"] / r["prompt_tokens"] if r["prompt_tokens"] else 0
        lines.append(f"{r['arm']:>3} {r['call']:>4} {'yes' if r['conv_id_set'] else 'no':>4} "
                     f"{'prefix1st' if r['prefix_first'] else 'q-first':>9} {str(r['actual_gap_s'] or '-'):>6} "
                     f"{r['prompt_tokens']:>6} {r['cached_tokens']:>6} {hit:>5.1f} {r['wall_ms']:>6.0f} "
                     f"{r['cost_xai']['total']:>10.6f} {(r['cost_as_if_anthropic'] or {}).get('total', 0):>10.6f}")
    lines += ["", "summary:"] + [f"  {k}: {json.dumps(v)}" for k, v in out["summary"].items()]
    (d / f"prompt-cache-gaps-{today}.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
