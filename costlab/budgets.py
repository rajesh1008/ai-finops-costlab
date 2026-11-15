"""Chapter 26: a small in-process budget authority. Hierarchical scopes (run, user, org), reserve -> commit -> refund, enforcement modes, and a repeated-call circuit breaker.
Single-process and not thread-safe by design: a production version would put the reserve step in one atomic store transaction (the source RFC says all scopes reserve or none do).
The design follows the decision flow described in the Agent Budget Protocol RFC excerpt (reserve against all scopes, commit actual, release the unused reserve), reimplemented from that description."""
from collections import Counter

class Blocked(Exception):
    def __init__(self, scope, need, left): super().__init__(f"blocked by {scope}: need {need:.6f}, left {left:.6f}"); self.scope, self.need, self.left = scope, need, left

class Authority:
    def __init__(self, limits, mode="hard_gate"):
        """limits: {scope_name: dollars}. mode: advisory_estimate | hard_gate | actuals_only."""
        if mode not in ("advisory_estimate", "hard_gate", "actuals_only"): raise ValueError(mode)
        self.limit = dict(limits); self.spent = {k: 0.0 for k in limits}; self.reserved = {k: 0.0 for k in limits}; self.mode = mode; self.log = []
    def left(self, scope): return self.limit[scope] - self.spent[scope] - self.reserved[scope]
    def reserve(self, scopes, estimate):
        """Reserve the worst-case estimate against every scope or none. Returns a reservation id."""
        if self.mode == "hard_gate":
            for s in scopes:
                if self.left(s) < estimate - 1e-12: self.log.append(("blocked", s, estimate)); raise Blocked(s, estimate, self.left(s))
            for s in scopes: self.reserved[s] += estimate
            return (tuple(scopes), estimate)
        if self.mode == "actuals_only":
            for s in scopes:
                if self.spent[s] >= self.limit[s] - 1e-12: self.log.append(("blocked", s, 0.0)); raise Blocked(s, 0.0, self.limit[s] - self.spent[s])
        return (tuple(scopes), 0.0)
    def commit(self, reservation, actual):
        scopes, est = reservation
        for s in scopes: self.reserved[s] -= est; self.spent[s] += actual
    def release(self, reservation):
        scopes, est = reservation
        for s in scopes: self.reserved[s] -= est

def worst_case_cost(prompt_tokens, max_output_tokens, usd_in, usd_out):
    """Upper bound for one call: the whole prompt as fresh input plus the full output cap."""
    return prompt_tokens / 1e6 * usd_in + max_output_tokens / 1e6 * usd_out

class Breaker:
    """Trips when the same tool call (name plus arguments) repeats `limit` times in one run, or when `errors` consecutive tool errors occur."""
    def __init__(self, limit=3, errors=3): self.limit, self.errors, self.seen, self.consec = limit, errors, Counter(), 0
    def observe(self, name, args, error=False):
        self.seen[(name, str(sorted(args.items())) if isinstance(args, dict) else str(args))] += 1; self.consec = self.consec + 1 if error else 0
        return self.seen[(name, str(sorted(args.items())) if isinstance(args, dict) else str(args))] >= self.limit or self.consec >= self.errors
