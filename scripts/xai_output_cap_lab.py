"""Real-API lab (mode: xai-api). What does an output cap save, and what does it break?

Measured on xAI's Grok API (grok-4.20-0309-non-reasoning) and priced at xAI's list prices (costlab.backends.xai).
Not a Claude call and not an Anthropic invoice figure. 10 open questions asking for a plain-English explanation,
each sent with four max_tokens caps (60, 150, 400, 1200), temperature 0. A reply is 'complete' when finish_reason
is 'stop'; a reply cut by the cap has finish_reason 'length' and is still billed. Needs XAI_API_KEY.
Output: runs/xai/output-caps-<date>.json and .txt.
"""
import datetime, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from costlab.backends.xai import XaiBackend, XaiError

QUESTIONS = [
    "Explain what a prompt cache is and when it saves money.",
    "Explain why output tokens cost more than input tokens.",
    "Explain what a retry storm is and how to stop one.",
    "Explain the difference between showback and chargeback.",
    "Explain what a batch API is and what you give up to use it.",
    "Explain what a cost per outcome is and why it beats cost per call.",
    "Explain what a model router does and how it can go wrong.",
    "Explain why a longer context window can raise the bill even if the question is short.",
    "Explain what a spend anomaly alert should contain.",
    "Explain what a commitment discount is and the risk of buying one.",
]
CAPS = [60, 150, 400, 1200]


def summarise(rows):
    out = {}
    for cap in CAPS:
        rs = [r for r in rows if r["cap"] == cap and "error" not in r]
        done = [r for r in rs if r["finish_reason"] == "stop"]
        cut = [r for r in rs if r["finish_reason"] == "length"]
        out[str(cap)] = {"calls": len(rs), "complete": len(done), "cut": len(cut),
                         "completion_tokens": sum(r["completion_tokens"] for r in rs),
                         "usd_xai_total": round(sum(r["cost_xai"]["total"] for r in rs), 6),
                         "usd_spent_on_cut_replies": round(sum(r["cost_xai"]["total"] for r in cut), 6),
                         "median_ms": sorted(r["wall_ms"] for r in rs)[len(rs) // 2] if rs else None}
    return out


def main():
    b = XaiBackend("grok-4.20-0309-non-reasoning", as_if_anthropic_model=None, timeout=90)
    rows = []
    for cap in CAPS:
        for i, q in enumerate(QUESTIONS, 1):
            try:
                d = b.chat([{"role": "user", "content": q}], max_tokens=cap).as_dict()
            except XaiError as e:
                d = {"error": str(e)[:200]}
            rows.append({"cap": cap, "question": i, **d})
            print(cap, i, d.get("finish_reason"), d.get("completion_tokens"), d.get("error", ""), flush=True)
    today = datetime.date.today().isoformat()
    prov = b.provenance()
    out = {**prov, "lab": "output-length caps", "run_date": today, "summary": summarise(rows), "calls": rows}
    d = pathlib.Path(__file__).resolve().parents[1] / "runs" / "xai"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"output-caps-{today}.json").write_text(json.dumps(out, indent=2))
    lines = [f"mode: xai-api | priced at xAI list prices dated {prov['pricing_date']} ({prov['pricing_source']})", prov["note"], ""]
    lines += [f"cap {k}: {json.dumps(v)}" for k, v in out["summary"].items()]
    (d / f"output-caps-{today}.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
