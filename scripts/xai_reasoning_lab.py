"""Real-API lab (mode: xai-api). Same 12 tasks, three ways to get an answer: what does thinking cost?

Measured on xAI's Grok API (grok-4.20-0309-non-reasoning and grok-4.20-0309-reasoning, same list price per token)
and priced at xAI's list prices (costlab.backends.xai). Not a Claude call and not an Anthropic invoice figure.
Tasks have one checkable answer (arithmetic word problems, a unit conversion, a date calculation, a short
classification). Three arms (non-reasoning model answering directly, same model writing short working, reasoning model answering directly); each arm sees each task once, max_tokens 3000, temperature 0, answer on the last line as
'ANSWER: <value>'. Output: runs/xai/thinking-three-ways-<date>.json and .txt. Needs XAI_API_KEY.
"""
import argparse, datetime, json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from costlab.backends.xai import XaiBackend, XaiError

TASKS = [
    ("A team makes 14,500 calls a day. Each call uses 1,900 input tokens and 420 output tokens. Input costs $1.25 per million tokens and output $2.50 per million. What is the cost of one day in dollars, to the nearest cent?", "49.66"),
    ("A bill is $48,000. 70 percent is input tokens and a vendor cuts the input rate by 30 percent. What is the new bill in dollars?", "37920"),
    ("A cache write costs 1.25 times the base input price and a cache read costs 0.1 times. A 20,000-token prefix is written once and read 9 more times. At a base price of $1 per million, what is the total input cost in dollars of the 10 calls, to five decimals?", "0.043"),
    ("Spend was $82,000 in March (31 days) and $79,500 in April (30 days). By what percent did the daily rate change from March to April, to one decimal place? Give a signed number.", "0.2"),
    ("A router sends 80 percent of 50,000 requests to a model costing $0.002 per request and the rest to a model costing $0.012 per request. What is the average cost per request in dollars?", "0.004"),
    ("A feature has 12,000 sessions. 9,000 succeed. Total cost is $5,400. What is the cost per successful session in dollars?", "0.6"),
    ("Convert 3.6 million tokens per hour to tokens per second.", "1000"),
    ("A retry policy makes up to 3 attempts. Each attempt fails independently with probability 0.2. What is the expected number of attempts per request? Give the answer to three decimals.", "1.24"),
    ("Today is Monday 16 November 2026. A commitment ends 90 days from today (today is day 0). What is the weekday of that date?", "Sunday"),
    ("Classify the support ticket as BILLING, BUG or OTHER. Ticket: 'The export button throws a 500 error every time I click it.'", "BUG"),
    ("Classify the support ticket as BILLING, BUG or OTHER. Ticket: 'I was charged twice for the same seat in October.'", "BILLING"),
    ("A prepaid commitment of $600,000 is drawn down at $45,000 in month 1, growing 6 percent each month after. In which month number does the cumulative draw first exceed $600,000?", "11"),
]
SUFFIX = {"direct": "\nGive only the final answer, alone on one line, as 'ANSWER: <value>'.",
          "cot": "\nWork it out step by step in a few short lines, then put the final answer alone on the last line as 'ANSWER: <value>'."}
# arms: (label, model, prompt style). xAI bills reasoning tokens at the output rate, so completion + reasoning is billed output.
ARMS = [("plain-direct", "grok-4.20-0309-non-reasoning", "direct"),
        ("plain-written-working", "grok-4.20-0309-non-reasoning", "cot"),
        ("reasoning-direct", "grok-4.20-0309-reasoning", "direct")]


def extract(text):
    m = re.findall(r"ANSWER:\s*(.+)", text or "")
    return m[-1].strip().strip("*$ .") if m else None


def correct(got, want):
    if got is None:
        return False
    g = got.replace(",", "").replace("%", "").replace("$", "").replace("+", "").strip()
    try:
        return abs(float(g) - float(want)) <= max(1e-9, 0.005 * abs(float(want))) if float(want) != 0.2 else abs(float(g) - 0.2) <= 0.06
    except ValueError:
        return g.lower().startswith(want.lower())


def summarise(rows):
    out = {}
    for model in sorted({r["arm"] for r in rows}):
        rs = [r for r in rows if r["arm"] == model and "error" not in r]
        n = len(rs)
        out[model] = {"tasks": n, "correct": sum(r["correct"] for r in rs),
                      "completion_tokens": sum(r["completion_tokens"] for r in rs),
                      "reasoning_tokens": sum(r["reasoning_tokens"] for r in rs),
                      "median_completion_tokens": sorted(r["completion_tokens"] for r in rs)[n // 2] if n else None,
                      "max_completion_tokens": max((r["completion_tokens"] for r in rs), default=None),
                      "usd_xai_total": round(sum(r["cost_xai"]["total"] for r in rs), 6),
                      "median_ms": sorted(r["wall_ms"] for r in rs)[n // 2] if n else None}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-tokens", type=int, default=3000)
    args = ap.parse_args()
    rows, backends = [], {}
    for label, m, style in ARMS:
        b = backends[label] = XaiBackend(m, as_if_anthropic_model=None, timeout=120)
        for i, (q, want) in enumerate(TASKS, 1):
            try:
                d = b.chat([{"role": "user", "content": q + SUFFIX[style]}], max_tokens=args.max_tokens).as_dict()
            except XaiError as e:
                d = {"error": str(e)[:200]}
            row = {"arm": label, "model": m, "prompt_style": style, "task": i, "expected": want, **d}
            if "error" not in d:
                row["extracted"] = extract(d["text"])
                row["correct"] = correct(row["extracted"], want)
            rows.append(row)
            print(label, i, row.get("extracted"), row.get("correct"), d.get("completion_tokens"), d.get("reasoning_tokens"),
                  d.get("error", ""), flush=True)
    today = datetime.date.today().isoformat()
    prov = backends[ARMS[0][0]].provenance()
    out = {**prov, "lab": "direct answer, written working and hidden reasoning on the same 12 tasks", "run_date": today,
           "summary": summarise(rows), "calls": rows}
    d = pathlib.Path(__file__).resolve().parents[1] / "runs" / "xai"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"thinking-three-ways-{today}.json").write_text(json.dumps(out, indent=2))
    lines = [f"mode: xai-api | priced at xAI list prices dated {prov['pricing_date']} ({prov['pricing_source']})", prov["note"], "",
             f"{'model':<32} {'task':>4} {'ok':>3} {'got':>10} {'want':>8} {'compl':>6} {'reason':>6} {'ms':>6} {'USD':>9}"]
    for r in rows:
        if "error" in r:
            lines.append(f"{r['arm']:<32} {r['task']:>4} ERROR {r['error']}")
            continue
        lines.append(f"{r['arm']:<32} {r['task']:>4} {'y' if r['correct'] else 'N':>3} {str(r['extracted'])[:10]:>10} "
                     f"{r['expected']:>8} {r['completion_tokens']:>6} {r['reasoning_tokens']:>6} {r['wall_ms']:>6.0f} "
                     f"{r['cost_xai']['total']:>9.6f}")
    lines += ["", "summary:"] + [f"  {k}: {json.dumps(v)}" for k, v in out["summary"].items()]
    (d / f"thinking-three-ways-{today}.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
