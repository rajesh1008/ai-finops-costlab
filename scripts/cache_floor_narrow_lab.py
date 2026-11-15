#!/usr/bin/env python3
"""Chapter 18 lab, narrowing the haiku 5.5 cache floor. REAL calls. Targets 210 to 290 in steps of 20, three repeats each, same method as cache_floor_repeats_lab.py."""
import os, sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import cache_floor_repeats_lab as b
M = "claude-haiku-5-5"; TARGETS = [210, 230, 250, 270, 290]
OUT = Path(__file__).resolve().parents[1] / "runs" / "cache-floor-narrow-2026-11-12.jsonl"
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); rows = []
    for rep in range(3):
        for k, t in enumerate(TARGETS):
            text = f"Salt narrow {t} {rep} {time.time()}.\n" + b.filler(int(t * 0.75), 500 + k * 10 + rep)
            try:
                u = cl.messages.create(model=M, max_tokens=5, system=[{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}],
                                       messages=[{"role": "user", "content": "Reply with the single word OK."}]).usage
                rows.append({"model": M, "target": t, "rep": rep, "input": u.input_tokens, "write": u.cache_creation_input_tokens or 0, "read": u.cache_read_input_tokens or 0})
            except Exception as e:
                rows.append({"model": M, "target": t, "rep": rep, "error": type(e).__name__ + ": " + str(e)[:200]})
            time.sleep(0.4)
    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        rows = [json.loads(l) for l in OUT.read_text().splitlines()]
        for r in rows: print(r["target"], r["rep"], ("ERROR " + r["error"]) if "error" in r else f'total {b.total(r)} write {r["write"]}')
        print(json.dumps(b.summarise(rows)))
    else: main()
