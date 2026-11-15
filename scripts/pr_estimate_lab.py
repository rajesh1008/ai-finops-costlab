#!/usr/bin/env python3
"""Chapter 39 lab, REAL calls. How good is a pull-request cost estimate? Ten configurations of one handbook assistant, 15 questions each (150 calls plus 150 token counts):
  model: claude-haiku-4-5-20251001 (M1), claude-haiku-5-5 thinking disabled (M2), claude-haiku-5-5 default thinking with max_tokens 800 (M3, 160-clause prefix only)
  prefix: 80 or 160 clauses of the synthetic handbook as the system prompt; cache: on (cache_control) or off.
A unique run line at the top of each prefix makes the first cached call write and the rest read. The key is read from the environment by the SDK and never printed."""
import os, sys, json, time, random
from pathlib import Path
from anthropic import Anthropic
OUT = Path(__file__).resolve().parents[1] / "runs" / "pr-estimate-lab-2026-11-11.json"
M1, M2 = "claude-haiku-4-5-20251001", "claude-haiku-5-5"
def prefix(n, salt):
    cl = [f"Clause {i}. For workspace tier {i % 7 + 1}, a support agent must verify the account owner, record reference FS-{1000 + i * 13}, and confirm the retention window of {30 + (i % 12) * 15} days before describing any export or deletion procedure." for i in range(1, n + 1)]
    return f"Fieldstone Analytics support handbook (synthetic). Run line {salt}.\n" + "\n".join(cl)
CONF = []
for model, kw, tag in ((M1, {}, "M1"), (M2, {"thinking": {"type": "disabled"}}, "M2")):
    for n in (80, 160):
        for cache in (True, False): CONF.append((f"{tag}-{n}-{'on' if cache else 'off'}", model, kw, n, cache, 200))
for cache in (True, False): CONF.append((f"M3-160-{'on' if cache else 'off'}", M2, {}, 160, cache, 800))
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); rnd = random.Random(390); qs = [f"What reference does clause {rnd.randint(1, 80)} use? Answer with the reference only." for _ in range(15)]
    res = []
    for name, model, kw, n, cache, mx in CONF:
        salt = f"{name}-{int(time.time())}"; sysb = [{"type": "text", "text": prefix(n, salt)}]
        if cache: sysb[0]["cache_control"] = {"type": "ephemeral"}
        for i, q in enumerate(qs):
            rec = {"conf": name, "i": i, "model": model, "n": n, "cache": cache, "error": None}
            for att in range(4):
                try:
                    rec["count"] = cl.messages.count_tokens(model=model, system=sysb, messages=[{"role": "user", "content": q}]).input_tokens
                    m = cl.messages.create(model=model, max_tokens=mx, system=sysb, messages=[{"role": "user", "content": q}], **kw)
                    u = m.usage; rec.update({"in": u.input_tokens, "out": u.output_tokens, "cr": getattr(u, "cache_read_input_tokens", 0) or 0, "cw": getattr(u, "cache_creation_input_tokens", 0) or 0, "stop": m.stop_reason,
                                             "text": "".join(b.text for b in m.content if b.type == "text")[:60]}); break
                except Exception as e:
                    rec["error"] = type(e).__name__; time.sleep(2 * (att + 1))
                    if att == 3: break
                    rec["error"] = None
            res.append(rec)
    OUT.write_text(json.dumps({"results": res})); print("saved", OUT.name, "calls", len(res), "errors", sum(1 for r in res if r["error"]))
if __name__ == "__main__": main()
