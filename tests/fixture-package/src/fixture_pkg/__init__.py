"""Fixture package exercised by the reusable Python CI self-test.

The functions here exist to be mutated. `greet` alone was not enough: an
f-string holding one interpolation gives mutmut nothing to change, so the
mutation job generated zero mutants and stopped early. `clamp` adds
comparisons, boundaries, and default arguments, which mutmut does mutate.
"""


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
