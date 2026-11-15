#!/usr/bin/env python3
"""Chapter 11 offline simulation (no API calls). Bootstrap interval for the ratio of cost per success between two prompts. All parameters are invented. Seed 2026."""
import random, statistics as st
r=random.Random(2026)
# Two prompts; each task attempt cost lognormal median $0.040 (A) and $0.030 (B), sigma 0.5; success p
def sample(n,p,med,sig):
    return [(r.random()<p, med*r.lognormvariate(0,sig)) for _ in range(n)]
A=sample(200,0.86,0.040,0.5); B=sample(200,0.80,0.030,0.5)
def cpo(x): 
    s=sum(1 for ok,c in x if ok); return sum(c for ok,c in x)/s
print('A',cpo(A),'B',cpo(B),'ratio',cpo(B)/cpo(A), 'succ',sum(o for o,c in A),sum(o for o,c in B))
rat=[]
for _ in range(5000):
    a=[r.choice(A) for _ in A]; b=[r.choice(B) for _ in B]
    rat.append(cpo(b)/cpo(a))
rat.sort(); print(rat[125],rat[2500],rat[4875], sum(1 for x in rat if x<1)/5000)
# how n changes interval width: n=50,100,200,400 with same true params; repeated 300 experiments, width of 90% interval average
import math
def ci(n):
    A=sample(n,0.86,0.040,0.5); B=sample(n,0.80,0.030,0.5)
    rr=[]
    for _ in range(400):
        a=[r.choice(A) for _ in A]; b=[r.choice(B) for _ in B]
        sa=sum(o for o,c in a); sb=sum(o for o,c in b)
        if sa==0 or sb==0: continue
        rr.append(cpo(b)/cpo(a))
    rr.sort(); return rr[int(.05*len(rr))],rr[int(.95*len(rr))]
for n in (50,100,200,400,800):
    lo,hi=ci(n); print(n,round(lo,3),round(hi,3),round(hi-lo,3))
print('true ratio',(0.030*math.exp(.125)/.80)/(0.040*math.exp(.125)/.86))
