#!/usr/bin/env python3
"""Chapter 9 offline simulation (no API calls). Error in p95 and p99 of session cost when read back from histogram buckets by linear interpolation. 100,000 lognormal session costs (median $0.011, sigma 1.1), seed 9. Invented parameters."""
import math, random
print('--- Ch9 histogram p95')
r=random.Random(9)
x=sorted(r.lognormvariate(math.log(0.011),1.1) for _ in range(100000))
true95=x[int(.95*len(x))-1]; true99=x[int(.99*len(x))-1]
def est(x,edges,q):
    n=len(x); target=q*n; cum=0; prev=0.0
    for e in edges+[float('inf')]:
        c=sum(1 for v in x if prev<v<=e)
        if cum+c>=target:
            if e==float('inf'): return prev
            return prev+(e-prev)*(target-cum)/c
        cum+=c; prev=e
for edges in ([0.01,0.05,0.10,0.50,1,5],[0.005,0.01,0.02,0.04,0.08,0.16,0.32,0.64,1.28,2.56,5.12],[0.005*1.25**i for i in range(0,40)]):
    print(len(edges), round(est(x,edges,.95),4), round(est(x,edges,.99),4), 'true',round(true95,4),round(true99,4), round(est(x,edges,.95)/true95-1,3), round(est(x,edges,.99)/true99-1,3))
print('median',x[50000], 'mean', sum(x)/len(x))
