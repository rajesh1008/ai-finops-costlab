#!/usr/bin/env python3
"""Arithmetic for the 42nd-run sections (Ch13, 14, 17, 18, 19, 24, 25, 26). Invented inputs; seeds fixed."""
import random, statistics as st, json
from pathlib import Path
print("== ch22 truncation lab totals")
rows=[json.loads(l) for l in (Path(__file__).resolve().parents[1]/"runs"/"truncation-retry-lab-2026-11-13.jsonl").read_text().splitlines()]
print("calls",len(rows),"cut",sum(r["stop"]=="max_tokens" for r in rows),"out tokens",sum(r["out"] for r in rows),"in tokens",sum(r["input"] for r in rows))
print("== ch13 percentile budgeting")
rng=random.Random(42); N=20000; base=100_000; res=[]
for _ in range(N):
    s=base
    for m in range(6): s*=1+rng.gauss(0.06,0.04)
    res.append(s)
res.sort(); q=lambda p: res[int(p*N)]
print("month-6 spend p10 %.0f p50 %.0f p80 %.0f p90 %.0f"%(q(.1),q(.5),q(.8),q(.9)))
print("== ch14 simpson")
A={"easy":(8000,0.02),"hard":(2000,0.20)}; B={"easy":(2000,0.025),"hard":(8000,0.24)}
for n,d in (("A",A),("B",B)):
    tot=sum(v[0] for v in d.values()); c=sum(v[0]*v[1] for v in d.values()); print(n,"blended per outcome",round(c/tot,4))
print("== ch17 router")
c1,c2,a1,a2,F=0.002,0.02,0.82,0.95,0.15
print("cheap",c1+(1-a1)*F,"strong",c2+(1-a2)*F, "breakF", (c2-c1)/(a2-a1))
print("== ch18 cache breakeven")
for w in (1.25,2.0):
    print(w, "n reads to beat uncached", (w-1)/(1-0.1))
print("1h vs 5m: 5m with 3 reads/hr after expiry")
print("== ch19 history growth")
t=40; u=400; tot=sum(i*u for i in range(1,t+1)); print("full history total input",tot)
k=10; s=800; tot2=0; hist=0
for i in range(1,t+1):
    if (i-1)%k==0 and i>1: hist=s
    hist_i=hist+((i-1)%k+1)*u; tot2+=hist_i
print("summarise every 10 turns",tot2, round(1-tot2/tot,3))
print("== ch24 agent run")
steps=20; sysp=3000; per=1200
inp=[sysp+i*per for i in range(steps)]; print("input tokens total",sum(inp),"last",inp[-1])
cost=sum(inp)*3/1e6+steps*400*15/1e6; print("uncached $",cost)
cc=0
for i,x in enumerate(inp):
    prev=inp[i-1] if i else 0
    cc+=(prev*0.3+(x-prev)*3.75)/1e6
cc+=steps*400*15/1e6; print("cached $",round(cc,4), "ratio",round(cc/cost,3))
print("== ch25 fanout")
shared=20000; k=6; task=1500
no=k*(shared+task); print("tokens no cache",no)
price=3/1e6
unc=no*price; cac=(shared*3.75/1e6)+(k-1)*shared*0.3/1e6+k*task*price+shared*0*0
print("uncached",unc,"cached",round(cac,4))
print("== ch26 kill-switch latency")
r=40; print("60 min",r*60,"5min",r*5,"15min",r*15)
