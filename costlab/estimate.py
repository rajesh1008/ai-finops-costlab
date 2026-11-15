from .prices import PLACEHOLDER_USD_PER_MTIOK


def estimate_usd(vendor_model: str, input_tokens: int, output_tokens: int,
                 cache_read_tokens: int = 0, cache_write_tokens: int = 0) -> float:
    table = PLACEHOLDER_USD_PER_MTIOK.get(vendor_model)
    if table is None:
        raise KeyError(f"No dated placeholder price for {vendor_model}")
    m = 1_000_000
    return (
        input_tokens / m * table["input"]
        + output_tokens / m * table["output"]
        + cache_read_tokens / m * table["cache_read"]
        + cache_write_tokens / m * table["cache_write"]
    )
