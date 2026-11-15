#!/usr/bin/env python3
"""Chapter 16 lab. REAL calls. Rule first, model as fallback, on date normalisation. 60 synthetic date strings (seed 16) in 10 formats; the house convention is day first. A small rule parser handles five formats (one of them with a deliberate day/month slip, the kind of bug a real rule path carries). Compares model-only against rule-first-with-fallback on accuracy and token use. Strings and rules are mine; this says nothing about any real product."""
import os, sys, json, random, re
from datetime import date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
OUT = Path(__file__).resolve().parents[1] / "runs" / "rule-first-lab-2026-11-12.jsonl"
MON = ["January","February","March","April","May","June","July","August","September","October","November","December"]
ORD = {1:"first",2:"second",3:"third",4:"fourth",5:"fifth",6:"sixth",7:"seventh",8:"eighth",9:"ninth",10:"tenth",11:"eleventh",12:"twelfth",13:"thirteenth",14:"fourteenth",15:"fifteenth",16:"sixteenth",17:"seventeenth",18:"eighteenth",19:"nineteenth",20:"twentieth",21:"twenty-first",22:"twenty-second",23:"twenty-third",24:"twenty-fourth",25:"twenty-fifth",26:"twenty-sixth",27:"twenty-seventh",28:"twenty-eighth"}
FORMATS = [  # (name, renderer, handled_by_rule)
 ("iso", lambda d: d.isoformat(), True),
 ("d_month_y", lambda d: f"{d.day} {MON[d.month-1]} {d.year}", True),
 ("month_d_y", lambda d: f"{MON[d.month-1]} {d.day}, {d.year}", True),
 ("d_mon_y", lambda d: f"{d.day:02d}-{MON[d.month-1][:3]}-{d.year}", True),
 ("slash_dmy", lambda d: f"{d.day:02d}/{d.month:02d}/{d.year}", True),
 ("compact", lambda d: d.strftime("%Y%m%d"), False),
 ("ord_words", lambda d: f"the {ORD[d.day]} of {MON[d.month-1]}, {d.year}", False),
 ("short_year", lambda d: f"{d.day}th {MON[d.month-1][:3]} '{d.year%100:02d}", False),
 ("dots_dmy", lambda d: f"{d.day}.{d.month}.{d.year}", False),
 ("y_slash", lambda d: f"{d.year}/{d.month}/{d.day}", False),
]
def make(seed=16, n=60):
    r = random.Random(seed); out = []
    for i in range(n):
        f = FORMATS[i % len(FORMATS)]
        d = date(r.choice([2025, 2026]), r.randint(1, 12), r.randint(1, 12) if f[0] in ("slash_dmy","dots_dmy") else r.randint(1, 28))
        out.append({"id": i, "fmt": f[0], "text": f[1](d), "truth": d.isoformat(), "rule_format": f[2]})
    return out
def rule(s):
    """Returns ISO date string or None. The slash rule has a deliberate slip: it reads month first when both parts are 12 or less."""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m: return s
    m = re.fullmatch(r"(\d{1,2}) ([A-Za-z]+) (\d{4})", s)
    if m and m.group(2) in MON: return f"{m.group(3)}-{MON.index(m.group(2))+1:02d}-{int(m.group(1)):02d}"
    m = re.fullmatch(r"([A-Za-z]+) (\d{1,2}), (\d{4})", s)
    if m and m.group(1) in MON: return f"{m.group(3)}-{MON.index(m.group(1))+1:02d}-{int(m.group(2)):02d}"
    m = re.fullmatch(r"(\d{2})-([A-Za-z]{3})-(\d{4})", s)
    if m:
        ab = [x[:3] for x in MON]
        if m.group(2) in ab: return f"{m.group(3)}-{ab.index(m.group(2))+1:02d}-{m.group(1)}"
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), m.group(3)
        if a <= 12 and b <= 12: a, b = b, a   # the slip: month first
        return f"{y}-{b:02d}-{a:02d}"
    return None
ASK = "Convert the date below to ISO format YYYY-MM-DD. The house convention is day first, so 03/04/2026 means 3 April 2026. Reply with the ISO date only.\n\nDate: "
def one(a):
    cl, m, row = a
    x = cl.messages.create(model=m, max_tokens=600, messages=[{"role": "user", "content": ASK + row["text"]}])
    t = "".join(b.text for b in x.content if b.type == "text")
    mm = re.search(r"\d{4}-\d{2}-\d{2}", t)
    return {"model": m, **row, "answer": mm.group(0) if mm else None, "in": x.usage.input_tokens, "out": x.usage.output_tokens}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); rows = make()
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(one, [(cl, m, r) for m in MODELS for r in rows]))
    OUT.write_text("\n".join(json.dumps(x) for x in res) + "\n")
if __name__ == "__main__": main()
