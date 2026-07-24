"""Fixture package exercised by the reusable Python CI self-test."""


def greet(name: str) -> str:
    """Return a greeting for the given name."""
    return f"Hello, {name}!"
