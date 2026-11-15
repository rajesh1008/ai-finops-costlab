"""Chapter 44/45: the segment-cost identity from the TokenCast paper (arXiv 2609.35760, opened in full 11 Nov 2026), implemented from its stated definitions.
A segment of n calls starts with input length L, consumes C tokens in total. Its triple is (n, g, b) with g the net change in input length across the segment and b = C - n*L.
Composition: (nA+nB, gA+gB, bA+bB+nB*gA). For a whole trace of K calls, T = K*L1 + b. Here `calls` is a list of (input_tokens, output_tokens) per call, so C_k = in_k + out_k."""
def single(calls, k):
    """Triple for call k (0-based) using L_k = input tokens of call k and L_{k+1} the next call's input (terminal call: no growth)."""
    L = calls[k][0]; nxt = calls[k + 1][0] if k + 1 < len(calls) else L
    return (1, nxt - L, (calls[k][0] + calls[k][1]) - L)
def compose(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2] + b[0] * a[1])
def trace_triple(calls):
    t = single(calls, 0)
    for k in range(1, len(calls)): t = compose(t, single(calls, k))
    return t
def total_from_triple(t, L1): return t[0] * L1 + t[2]
def total(calls): return sum(i + o for i, o in calls)
def repeated_input_share(calls):
    """Share of total tokens that is input after the first call's input (the re-read of carried context plus the new tool output)."""
    T = total(calls); return (sum(i for i, _ in calls[1:])) / T if T else 0.0
def quadratic_fit(calls):
    """Mean growth of input per call (tokens) and the implied total for K calls under linear growth: sum_{k<K}(L1 + k*g) + outputs."""
    K = len(calls); g = (calls[-1][0] - calls[0][0]) / (K - 1) if K > 1 else 0.0
    return g, sum(calls[0][0] + k * g for k in range(K)) + sum(o for _, o in calls)
