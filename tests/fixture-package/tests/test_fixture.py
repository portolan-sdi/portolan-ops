from fixture_pkg import greet


def test_greet() -> None:
    assert greet("ops") == "Hello, ops!"
