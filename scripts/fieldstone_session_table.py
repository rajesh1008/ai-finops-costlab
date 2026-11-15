#!/usr/bin/env python3
"""Chapter 7: the worked Fieldstone session table. SYNTHETIC hand-built traces, priced with costlab rates, rolled up with runs_graph."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from costlab.waste import call_cost
from costlab.runs_graph import Call, rollup, session_costs, tail_summary

def agent(sid, steps, tool_tok=1100, retries=(), sub=0, floor=1500, new=900, out=350, human_expiry=0):
    """steps model calls; each carries the tool description (tool_tok) in its new input; retries is a set of step numbers
    whose first attempt failed and was billed again; sub = number of subagent runs of 6 steps each; human_expiry =
    number of steps whose cache lapsed during a person's wait (prefix re-written)."""
    calls, ctx = [], floor
    for s in range(1, steps + 1):
        rd, wr = (ctx, 0) if s > 1 else (0, ctx)
        if s - 1 in range(1, 100) and human_expiry >= (steps - s + 1) and s > 1:
            rd, wr = 0, ctx
        c = call_cost(new + tool_tok, out, rd, wr)
        calls.append(Call(f"{sid}-{s}", sid, f"{sid}-root", None, c, "model"))
        if s in retries:
            calls.append(Call(f"{sid}-{s}r", sid, f"{sid}-root", None, c, "retry"))
        ctx += new + out
    for k in range(sub):
        cx = 2500
        for s in range(1, 7):
            rd, wr = (cx, 0) if s > 1 else (0, cx)
            calls.append(Call(f"{sid}-sub{k}-{s}", sid, f"{sid}-sub{k}", f"{sid}-root", call_cost(new, out, rd, wr), "model"))
            cx += new + out
    return calls

sessions = {
    "s01 order status": agent("s01", 2),
    "s02 refund small": agent("s02", 4),
    "s03 refund, one retry": agent("s03", 5, retries={3}),
    "s04 account question": agent("s04", 6),
    "s05 two subagents": agent("s05", 5, sub=2),
    "s06 approval, lunch": agent("s06", 6, human_expiry=3),
    "s07 loop to cap": agent("s07", 40, retries=set(range(5, 40, 2))),
    "s08 loop, big registry": agent("s08", 40, tool_tok=15856 - 496, retries=set(range(5, 40, 2))),
}
print("SYNTHETIC session table (hand-built traces; placeholder rates; not a Fieldstone measurement)")
print(f"{'session':24s} {'calls':>5s} {'retry':>5s} {'subruns':>7s} {'cost':>9s} {'vs s01':>7s}")
allc = []; base = None; tot = {}
for name, calls in sessions.items():
    sid = calls[0].session_id
    cost = session_costs(calls)[sid]; tot[name] = cost
    base = base or cost
    nret = sum(1 for c in calls if c.kind == "retry"); subs = len({c.run_id for c in calls if "sub" in c.run_id})
    rr = rollup(calls)[f"{sid}-root"]
    assert abs(rr - cost) < 1e-9
    print(f"{name:24s} {len(calls):5d} {nret:5d} {subs:7d} ${cost:8.4f} {cost/base:6.1f}x")
    allc += calls
costs = list(tot.values()); s = tail_summary(costs)
print(f"\nEight sessions: total ${s['total']:.4f}; median ${s['median']:.4f}; mean ${s['mean']:.4f}; max ${s['max']:.4f}")
print(f"s07 plus s08 = {(tot['s07 loop to cap']+tot['s08 loop, big registry'])/s['total']:.1%} of the table's spend")
rt = sum(c.cost for c in allc if c.kind == 'retry')
print(f"billed retry calls: ${rt:.4f} = {rt/s['total']:.1%} of spend; in s07 {sum(c.cost for c in allc if c.kind=='retry' and c.session_id=='s07')/tot['s07 loop to cap']:.1%} of that session")
