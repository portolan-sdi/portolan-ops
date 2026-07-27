import pytest

from fixture_pkg import clamp, greet


def test_greet() -> None:
    assert greet("ops") == "Hello, ops!"


def test_clamp_returns_value_inside_the_range() -> None:
    assert clamp(42) == 42


def test_clamp_raises_the_floor() -> None:
    assert clamp(-5) == 0


def test_clamp_caps_at_the_ceiling() -> None:
    assert clamp(150) == 100


def test_clamp_keeps_the_lower_bound() -> None:
    assert clamp(0) == 0


def test_clamp_keeps_the_upper_bound() -> None:
    assert clamp(100) == 100


def test_clamp_honours_a_custom_range() -> None:
    assert clamp(5, low=1, high=3) == 3
    assert clamp(0, low=1, high=3) == 1


def test_clamp_accepts_a_single_point_range() -> None:
    # Distinguishes `low > high` from `low >= high`, which would reject a
    # range of one valid value.
    assert clamp(5, low=3, high=3) == 3


def test_clamp_rejects_an_inverted_range() -> None:
    with pytest.raises(ValueError, match="exceeds"):
        clamp(5, low=10, high=1)
