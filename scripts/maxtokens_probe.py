#!/usr/bin/env python3
"""Chapter 26 follow-up (twenty-first run). REAL calls. Why did haiku-5-5 hit every ceiling up to 800? Record block types, text chars and output tokens at larger ceilings, 10 tasks x 2 caps x 1 repeat."""
import os, sys, json, re
from pathlib import Path
from anthropic import Anthropic
sys.path.insert(0, str(Path(__file__).parent))
from maxtokens_lab import TASKS
OUT = Path(__file__).resolve().parents[1] / "runs" / "maxtokens-probe-2026-11-11.jsonl"
def main():
    cl = Anthropic(); res = []
    for cap in [1600, 4000]:
        for ti in range(10):
            x = cl.messages.create(model="claude-haiku-5-5", max_tokens=cap, messages=[{"role": "user", "content": f"Explain, for a finance partner, whether to investigate this: {TASKS[ti]}. Give the reasoning, then end with exactly one final line: DECISION: yes or DECISION: no."}])
            types = [b.type for b in x.content]; text = "".join(b.text for b in x.content if b.type == "text")
            res.append({"cap": cap, "task": ti, "out": x.usage.output_tokens, "stop": x.stop_reason, "types": types, "text_chars": len(text), "has_decision": bool(re.search(r"DECISION:\s*(yes|no)\s*\**\s*$", text.strip(), re.I))})
    OUT.write_text("\n".join(json.dumps(r) for r in res) + "\n")
    for cap in [1600, 4000]:
        q = [r for r in res if r["cap"] == cap]
        print(cap, "hit", sum(r["stop"] == "max_tokens" for r in q), "decision", sum(r["has_decision"] for r in q), "mean out %.0f" % (sum(r["out"] for r in q)/len(q)), "mean text chars %.0f" % (sum(r["text_chars"] for r in q)/len(q)), "types", sorted({t for r in q for t in r["types"]}))
if __name__ == "__main__": main()
