LINE_CLASSES = (
    "input_tokens",
    "output_tokens",
    "cached_tokens",
    "reasoning_tokens",
    "per_call",
    "per_seat",
    "fine_tuning",
    "hosted_capacity",
    "embeddings",
    "retrieval",
    "evaluation",
    "observability",
    "support",
    "mixed_unsplit",
    "unknown",
)


def classify_line(description: str, unit: str) -> str:
    text = f"{description} {unit}".lower()
    if unit == "mixed" or " and gpt" in text or "mixed" in text:
        return "mixed_unsplit"
    if "embed" in text:
        return "embeddings"
    if "endpoint" in text or "provisioned" in text or unit == "hours":
        return "hosted_capacity"
    if "reason" in text or "thinking" in text:
        return "reasoning_tokens"
    if "cache" in text:
        return "cached_tokens"
    if "output" in text or "completion" in text:
        return "output_tokens"
    if "input" in text or "prompt" in text:
        return "input_tokens"
    if "embed" in text:
        return "embeddings"
    if "eval" in text or "judge" in text:
        return "evaluation"
    if "seat" in text:
        return "per_seat"
    if "request" in text or "call" in text:
        return "per_call"
    if "vector" in text or "retriev" in text:
        return "retrieval"
    if "log" in text or "trace" in text:
        return "observability"
    return "unknown"
