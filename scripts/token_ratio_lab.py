#!/usr/bin/env python3
"""Chapter 14 lab (twentieth run). REAL count_tokens calls on both models for six kinds of text I wrote or generated. Counts tokens the bill would see; no completions. Never prints the key."""
import os, sys, json, random
from pathlib import Path
from anthropic import Anthropic
OUT = Path(__file__).resolve().parents[1] / "runs" / "token-ratio-lab-2026-11-11.json"
r = random.Random(14)
T = {
 "english_prose": " ".join(["The support team reviewed the account, confirmed the owner, and described the export steps in plain language."] * 40),
 "python_code": "def total(rows):\n    s = 0\n    for r in rows:\n        if r['ok']:\n            s += r['cost']\n    return s\n\n" * 40,
 "json_records": "\n".join(json.dumps({"id": r.randint(10**6, 10**7), "model": "m-small", "in": r.randint(100, 9000), "out": r.randint(10, 900), "ok": r.random() < .9}) for _ in range(150)),
 "digits": " ".join(str(r.randint(10**8, 10**9)) for _ in range(300)),
 "german_prose": " ".join(["Das Support-Team pruefte das Konto, bestaetigte den Inhaber und erklaerte die Exportschritte in einfacher Sprache."] * 40),
 "hindi_prose": " ".join(["सहायता दल ने खाते की जाँच की, मालिक की पुष्टि की और निर्यात के चरण सरल भाषा में समझाए।"] * 40),
}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); out = {}
    for k, t in T.items():
        out[k] = {"chars": len(t)}
        for m in ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]:
            out[k][m] = cl.messages.count_tokens(model=m, messages=[{"role": "user", "content": t}]).input_tokens
    OUT.write_text(json.dumps(out, indent=1))
    for k, v in out.items():
        a, b = v["claude-haiku-4-5-20251001"], v["claude-haiku-5-5"]; print(f"{k:14s} chars {v['chars']:6d} h45 {a:6d} h55 {b:6d} ratio {b/a:.3f} chars/token h45 {v['chars']/a:.2f}")
if __name__ == "__main__": main()
