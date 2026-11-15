#!/usr/bin/env python3
"""Ch18 lab (47th run). REAL calls. A 10-turn conversation whose history grows by about 700 tokens a turn on a ~5k-token system document.
Three arms: none (no cache_control), static (breakpoint on the system block only), moving (breakpoint on the system block and on the last user message each turn).
Each (arm, repeat) uses its own nonce so arms cannot read each other's cache. 3 arms x 4 repeats x 10 turns = 120 calls on claude-haiku-4-5.
Cost is computed from the usage fields the API returned. Key from env only, never printed."""
import os, sys, json, random
from pathlib import Path
M = "claude-haiku-4-5-20251001"; P = dict(inp=1.00, out=5.00, cr=0.10, cw=1.25)
OUT = Path(__file__).resolve().parents[1] / "runs" / "history-cache-lab-2026-11-13.jsonl"
WORDS = "ledger invoice meter quota budget tenant gateway tag token batch cache prefix route retry ticket owner forecast variance alert policy region rate window credit refund account review tier limit usage report".split()
def prose(rng, n):
    out = []
    while len(out) < n:
        s = [rng.choice(WORDS) for _ in range(rng.randint(8, 16))]
        out.append(" ".join(s).capitalize() + ".")
        out.extend([])
        n2 = len(" ".join(out).split())
        if n2 >= n: break
    return " ".join(out)
def system_doc(nonce):
    rng = random.Random(nonce)
    return f"Session {nonce}. You are a terse assistant. Reply with one short sentence acknowledging the note.\n\n" + "\n".join(f"Section {i}. " + prose(rng, 120) for i in range(1, 36))
def user_note(nonce, t):
    rng = random.Random(f"{nonce}-{t}")
    return f"Note {t}. " + prose(rng, 380)
def cost(u):
    return (u["in"] * P["inp"] + u["out"] * P["out"] + u["cr"] * P["cr"] + u["cw"] * P["cw"]) / 1e6
def run(cl, arm, rep, turns=10):
    nonce = f"{arm}{rep}-{random.Random(arm + str(rep)).randint(10**6, 10**7)}"
    sysblock = {"type": "text", "text": system_doc(nonce)}
    if arm != "none": sysblock["cache_control"] = {"type": "ephemeral"}
    msgs, rows = [], []
    for t in range(1, turns + 1):
        content = [{"type": "text", "text": user_note(nonce, t)}]
        if arm == "moving": content[0]["cache_control"] = {"type": "ephemeral"}
        # strip older breakpoints from earlier user turns (only the last stays marked)
        for m in msgs:
            if m["role"] == "user":
                for b in m["content"]: b.pop("cache_control", None)
        msgs.append({"role": "user", "content": content})
        r = cl.messages.create(model=M, max_tokens=40, system=[sysblock], messages=msgs)
        a = "".join(b.text for b in r.content if b.type == "text")
        us = r.usage
        u = {"turn": t, "in": us.input_tokens, "out": us.output_tokens, "cr": us.cache_read_input_tokens or 0, "cw": us.cache_creation_input_tokens or 0}
        u["cost"] = cost(u); rows.append(u)
        msgs.append({"role": "assistant", "content": [{"type": "text", "text": a or "Noted."}]})
    return {"arm": arm, "rep": rep, "rows": rows}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); out = []
    for rep in range(4):
        for arm in ("none", "static", "moving"):
            try: out.append(run(cl, arm, rep))
            except Exception as e: out.append({"arm": arm, "rep": rep, "error": type(e).__name__ + ": " + str(e)[:160]})
    OUT.write_text("\n".join(json.dumps(x) for x in out) + "\n")
def summary(path=OUT):
    rows = [json.loads(l) for l in Path(path).read_text().splitlines()]; ok = [r for r in rows if "error" not in r]
    print("sessions", len(rows), "errors", len(rows) - len(ok), "calls", sum(len(r["rows"]) for r in ok))
    for arm in ("none", "static", "moving"):
        g = [r for r in ok if r["arm"] == arm]
        if not g: continue
        tot = [sum(x["cost"] for x in r["rows"]) for r in g]
        n = len(g)
        print(arm, "n", n, "cost/session $", round(sum(tot) / n, 5), "min", round(min(tot), 5), "max", round(max(tot), 5),
              "| mean per session: uncached in", round(sum(x["in"] for r in g for x in r["rows"]) / n),
              "cache read", round(sum(x["cr"] for r in g for x in r["rows"]) / n), "cache write", round(sum(x["cw"] for r in g for x in r["rows"]) / n))
        print("  mean cost by turn $:", [round(sum(r["rows"][t]["cost"] for r in g) / n, 5) for t in range(10)])
    print("turn-1 total prompt tokens (in+cr+cw), by arm:", {a: [sum(r["rows"][0][k] for k in ("in", "cr", "cw")) for r in ok if r["arm"] == a] for a in ("none", "static", "moving")})
    print("turn-10 total prompt tokens, by arm:", {a: [sum(r["rows"][9][k] for k in ("in", "cr", "cw")) for r in ok if r["arm"] == a][:2] for a in ("none", "static", "moving")})
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
