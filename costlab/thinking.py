"""Thinking gap: billed output tokens minus the tokens of the visible answer.

The usage record reports one output number. When the model thinks first, the thinking is
billed as output and is not in the visible text. The gap is therefore an estimate: counting
visible text with a token-counting endpoint adds a few tokens of message framing, so the
gap is clamped at zero and should be read as 'about', never as an exact quantity.
"""


def thinking_gap(billed_output_tokens: int, visible_tokens_estimate: int) -> int:
    return max(0, billed_output_tokens - visible_tokens_estimate)


def thinking_share(billed_output_tokens: int, visible_tokens_estimate: int) -> float:
    if billed_output_tokens <= 0:
        return 0.0
    return thinking_gap(billed_output_tokens, visible_tokens_estimate) / billed_output_tokens
