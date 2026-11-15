#!/usr/bin/env python3
"""Chapter 11: cost per successful task under three accounting choices, and the retry-cap sweep. SYNTHETIC. No API."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from costlab.cpst import simulate, report, by_kind

tasks, rate = simulate()
print("SYNTHETIC 5,000 tasks, seed 11, retry cap 2. Assumed: easy p=0.85, hard p=0.35, 25% hard, human $0.80/min, 4 min on failure.")
r_h = report(tasks, rate, True); r_m = report(tasks, rate, False)
print(f"success rate {r_h['success_rate']:.3f} ({r_h['successes']} of {r_h['tasks']})")
print(f"A  cost of successful tasks only / successes ('mean cost of a done task'): ${r_h['mean_cost_of_successes']:.4f}")
print(f"B  CPST, machine cost only (failures in numerator, human excluded):       ${r_m['cpst']:.4f}")
print(f"C  CPST, human review of failures included:                                ${r_h['cpst']:.4f}")
print(f"   per attempted task (the naive per-task number):             ${r_h['per_attempted']:.4f}")
print(f"   share of all cost spent on tasks that failed (human included):          {r_h['failed_cost_share']:.1%}")
print(f"   A understates C by {1 - r_h['mean_cost_of_successes']/r_h['cpst']:.1%}")
print("\nBy kind (human included)")
for k, v in by_kind(tasks, rate).items():
    print(f"  {k:5s} tasks {v['tasks']:5d} success {v['success_rate']:.3f} CPST ${v['cpst']:.4f} per attempted ${v['per_attempted']:.4f}")
print("\nRetry-cap sweep (human included). correlated = a retry on a hard task is half as likely to succeed")
print("cap  correlated  success  CPST_human  CPST_machine_only  failed_cost_share_machine")
for corr in (False, True):
    for cap in (1, 2, 3, 4, 6):
        t, rt = simulate(retry_cap=cap, correlated=corr)
        r = report(t, rt, True); m = report(t, rt, False)
        print(f"{cap:3d}  {str(corr):10s}  {r['success_rate']:.3f}   ${r['cpst']:.4f}     ${m['cpst']:.4f}            {m['failed_cost_share']:.1%}")
