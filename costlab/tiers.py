"""Long-context price tiers: one threshold, two sets of rates (Chapter 2).

Some vendors price a request at a higher rate when its prompt exceeds a token threshold. Whether
the higher rate applies to the whole request or only to the excess is a contract term, so both
readings are implemented and the caller must say which one the vendor's page states.
"""


def tiered_cost(prompt_tokens: int, output_tokens: int, threshold: int,
                low_in: float, low_out: float, high_in: float, high_out: float,
                whole_request: bool = True) -> float:
    """Rates are USD per million tokens."""
    if prompt_tokens <= threshold:
        return (prompt_tokens * low_in + output_tokens * low_out) / 1e6
    if whole_request:
        return (prompt_tokens * high_in + output_tokens * high_out) / 1e6
    return (threshold * low_in + (prompt_tokens - threshold) * high_in + output_tokens * high_out) / 1e6
