#!/usr/bin/env python3
"""Chapter 36 lab, REAL calls. Three teams share one cached prefix (the synthetic handbook, about 7,500 tokens) on claude-haiku-4-5.
Arm C: prefix cached (cache_control). Arm U: same questions, no cache_control. 36 calls per arm, teams support (12), product (18), data (6), interleaved by seed 360.
Output: runs/showback-cache-lab-2026-11-11.json. No key is read or printed; the SDK reads ANTHROPIC_API_KEY from the environment."""
import os, sys, json, random, time
from pathlib import Path
from anthropic import Anthropic
sys.path.insert(0, str(Path(__file__).parent)); from scripts_common import handbook
MODEL = "claude-haiku-4-5-20251001"
OUT = Path(__file__).resolve().parents[1] / "runs" / "showback-cache-lab-2026-11-11.json"
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); rnd = random.Random(360)
    teams = ["support"] * 12 + ["product"] * 18 + ["data"] * 6
    rnd.shuffle(teams)
    teams[0] = "support"  # the support team's first call opens the day, as in the chapter's story
    qs = [f"What reference does clause {rnd.randint(1,160)} use? Answer with the reference only." for _ in teams]
    res = []
    for arm in ("C", "U"):
        sysb = [{"type": "text", "text": handbook()}]
        if arm == "C": sysb[0]["cache_control"] = {"type": "ephemeral"}
        for i, (t, q) in enumerate(zip(teams, qs)):
            for att in range(4):
                try:
                    m = cl.messages.create(model=MODEL, max_tokens=40, system=sysb, messages=[{"role": "user", "content": q}])
                    u = m.usage
                    res.append({"arm": arm, "i": i, "team": t, "in": u.input_tokens, "out": u.output_tokens,
                                "cr": getattr(u, "cache_read_input_tokens", 0) or 0, "cw": getattr(u, "cache_creation_input_tokens", 0) or 0, "error": None}); break
                except Exception as e:
                    if att == 3: res.append({"arm": arm, "i": i, "team": t, "error": f"{type(e).__name__}"})
                    time.sleep(2 * (att + 1))
    OUT.write_text(json.dumps({"model": MODEL, "teams": teams, "results": res}))
    print("saved", OUT.name, "calls", len(res), "errors", sum(1 for r in res if r["error"]))
if __name__ == "__main__": main()
