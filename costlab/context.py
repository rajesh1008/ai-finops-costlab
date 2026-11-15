"""Chapter 19: filler prompts for the diet lab and a cache-aware compaction cost model. Filler is SYNTHETIC; rates are the vendor-page multipliers, volumes ASSUMED."""

RULE_BLOCKS = [
 "Tone: be courteous and brief; never blame the customer; address the customer by first name when it is known.",
 "Escalation: if the customer mentions a lawyer, a regulator or a chargeback, route to the escalations queue and do not discuss refunds.",
 "Formatting: all internal notes use sentence case, no abbreviations, and a reference in the form FS-0000 where one exists.",
 "Data handling: never repeat a full card number, a password or a government identifier in any note, even if the customer supplied it.",
 "Languages: reply in the language of the message when the team supports it, otherwise reply in English and flag for translation.",
 "Hours: weekend messages are queued until the next business day unless the customer is on the priority plan.",
 "Refunds: refunds above the agent limit need a second approver, recorded in the ticket before the customer is told.",
 "Plans: the team plan includes five seats; extra seats are billed monthly in advance; the priority plan adds weekend cover.",
]

def filler(n_tokens_approx):
    """Roughly n tokens of irrelevant but plausible house rules (about 24 tokens per block repeat, varied by index)."""
    out, i = [], 0
    while sum(len(x.split()) for x in out) * 1.35 < n_tokens_approx:
        out.append(f"Rule {i + 1}. " + RULE_BLOCKS[i % len(RULE_BLOCKS)] + f" (revision {i // len(RULE_BLOCKS) + 1}.)")
        i += 1
    return "\n".join(out)

READ, WRITE = 0.10, 1.25

def session_cost_policy(steps, policy, base=2000, add=600, out=150, price_in=1.0, price_out=5.0, k=10, keep=3):
    """Cost of an agent session. Each step appends `add` tokens of tool result to history.
    policy: 'raw' (history grows, prefix cached);
            'mask_every' (from step keep+1 on, the tool result that falls out of the last `keep` is replaced by a stub every turn,
                          so the cached prefix changes at the first masked block each turn);
            'mask_batch' (stubs are applied only every k steps, so the prefix changes once per k steps).
    Returns (usd, input tokens sent, cache write tokens, cache read tokens). Stub = 20 tokens. Cache lifetime never expires (steps are fast)."""
    STUB = 20
    results = []            # tokens each tool result currently occupies in the prompt
    cached_len = 0          # tokens of the prefix currently in the cache (prefix = base + results[:j])
    prev_blocks = None
    usd = tin = cw = cr = 0.0
    for s in range(steps):
        if policy == "mask_every" and len(results) > keep:
            for j in range(len(results) - keep): results[j] = STUB
        if policy == "mask_batch" and s % k == 0 and len(results) > keep:
            for j in range(len(results) - keep): results[j] = STUB
        blocks = [base] + list(results)
        total = sum(blocks)
        # longest common prefix with what was cached last step
        lcp = 0
        if prev_blocks is not None:
            for a, b in zip(prev_blocks, blocks):
                if a == b: lcp += a
                else: break
        read = min(lcp, total); write = total - read
        usd += (read * READ + write * WRITE) * price_in / 1e6 + out * price_out / 1e6
        tin += total; cw += write; cr += read
        prev_blocks = blocks
        results.append(add)
    return usd, tin, cw, cr
