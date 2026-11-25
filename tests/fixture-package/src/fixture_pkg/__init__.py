"""Fixture package exercised by the reusable Python CI self-test."""


def greet(name: str) -> str:
    """Return a greeting for the given name."""
    return f"Hello, {name}!"


def clamp(value: int, low: int = 0, high: int = 100) -> int:
    """Return `value` confined to the inclusive range from `low` to `high`.

    Raises:
        ValueError: `low` is greater than `high`.
    """
    if low > high:
        raise ValueError(f"low {low} exceeds high {high}")
    if value < low:
        return low
    if value > high:
        return high
    return value
