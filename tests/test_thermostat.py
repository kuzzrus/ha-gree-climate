"""Tests for the external thermostat control rules."""

import pytest
from thermostat import ifeel_temperature, should_run


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (15.49, None),
        (15.5, 16),
        (21.4, 21),
        (21.5, 22),
        (35.49, 35),
        (35.5, None),
        (float("inf"), None),
        (float("nan"), None),
    ],
)
def test_ifeel_temperature(value: float, expected: int | None) -> None:
    """I Feel uses safe whole-degree room temperatures."""
    assert ifeel_temperature(value) == expected


@pytest.mark.parametrize(
    ("current", "was_running", "expected"),
    [
        (21.4, False, True),
        (21.5, False, True),
        (22.0, False, False),
        (22.0, True, True),
        (22.7, True, True),
        (22.8, True, False),
        (22.9, True, False),
    ],
)
def test_heat_hysteresis(current: float, was_running: bool, expected: bool) -> None:
    """Heat uses separate activation and deactivation offsets."""
    assert should_run("heat", current, 22.0, 0.5, 0.8, was_running) is expected


@pytest.mark.parametrize(
    ("current", "was_running", "expected"),
    [
        (21.6, True, False),
        (21.7, True, False),
        (21.8, True, True),
        (22.0, False, False),
        (22.0, True, True),
        (22.6, False, False),
        (22.7, False, True),
        (22.8, False, True),
    ],
)
def test_cool_hysteresis(current: float, was_running: bool, expected: bool) -> None:
    """Cooling uses separate activation and deactivation offsets."""
    assert should_run("cool", current, 22.0, 0.7, 0.3, was_running) is expected
