"""Keyless lab (mode: local-model). Prefix-cache reuse and eviction on a small open model run locally with llama.cpp.

Six calls share a ~350-token policy prefix with different questions. Call 4 sends an unrelated prompt through the
single server slot to test whether the prefix survives. On the 16 Nov 2026 run it did: llama.cpp's host-memory
prompt cache restored the 458-token prefix on call 5, so a different prompt in between is not an eviction here. Token counts,
latency and cache hits are measured locally; dollars are calculated at Anthropic list prices (costlab.price_table)
for the model named in --priced-as. Not an Anthropic invoice measurement. Needs llama-server on COSTLAB_LOCAL_URL.
Output: runs/local-model/prefix-cache-local-<date>.json and .txt
"""
import argparse, datetime, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from costlab.backends.local import LocalBackend

POLICY = ("Fieldstone Analytics model-usage policy. " +
          " ".join(f"Rule {i}: every request to a hosted model must carry a team tag, a feature tag and a budget owner; "
                   f"requests above the daily cap for the feature are queued for batch processing." for i in range(1, 12)) +
          "\nAnswer in one short sentence.\n")
QUESTIONS = ["Q: Who owns a request's cost?\nA:", "Q: What happens above the daily cap?\nA:",
             "Q: Which tags are required?\nA:", None, "Q: Is batch processing used?\nA:", "Q: What is rule 3?\nA:"]
UNRELATED = "Write a haiku about autumn rain over a quiet harbour town, with fishing boats.\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--priced-as", default="claude-haiku-4-5")
    a = ap.parse_args()
    b = LocalBackend(priced_as=a.priced_as)
    # a run id at the very start makes call 1 a true cold start even if the server cached an earlier run
    policy = f"Run {datetime.datetime.now().isoformat(timespec='seconds')}. " + POLICY
    if not b.health():
        sys.exit("local model server is not running (see README: Keyless lab modes)")
    rows = []
    for i, q in enumerate(QUESTIONS, 1):
        if q is None:
            r = b.complete("", UNRELATED, max_tokens=8, cache_prefix=None)
            label = "unrelated prompt (slot test)"
        else:
            r = b.complete(policy, q, max_tokens=8, cache_prefix="5m")
            label = "policy prefix + question"
        rows.append({"call": i, "what": label, **r.as_dict()})
    today = datetime.date.today().isoformat()
    out = {**b.provenance(), "lab": "prefix-cache reuse and eviction", "run_date": today,
           "mapping": "local cached tokens -> cache read; uncached prefix -> 5m cache write; rest -> input; generated -> output",
           "calls": rows}
    d = pathlib.Path(__file__).resolve().parents[1] / "runs" / "local-model"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"prefix-cache-local-{today}.json").write_text(json.dumps(out, indent=2))
    lines = [f"mode: local-model | local model: {out['local_model']} | priced as: {a.priced_as} list prices "
             f"dated {out['pricing_date']} ({out['pricing_source']})", out["note"], "",
             f"{'call':>4} {'what':32} {'prompt':>6} {'cached':>6} {'new':>5} {'out':>4} {'prompt_ms':>9} {'gen_ms':>8} {'USD':>11}"]
    for r in rows:
        lines.append(f"{r['call']:>4} {r['what']:32} {r['prompt_tokens']:>6} {r['cached_tokens']:>6} {r['evaluated_tokens']:>5} "
                     f"{r['output_tokens']:>4} {r['prompt_ms']:>9.0f} {r['gen_ms']:>8.0f} {r['priced']['total']:>11.7f}")
    (d / f"prefix-cache-local-{today}.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
