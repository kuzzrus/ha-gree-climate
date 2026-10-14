"""Tests for the external thermostat control rules."""

import pytest
from thermostat import should_run


@pytest.mark.parametrize(
    ("current", "was_running", "expected"),
    [
        (21.4, False, True),
        (21.5, False, True),
        (22.0, False, False),
        (22.0, True, True),
        (22.5, True, False),
        (22.6, True, False),
    ],
)
def test_heat_hysteresis(current: float, was_running: bool, expected: bool) -> None:
    """Heat starts and stops at the two edges of the dead band."""
    assert should_run("heat", current, 22.0, 0.5, was_running) is expected


@pytest.mark.parametrize(
    ("current", "was_running", "expected"),
    [
        (21.4, True, False),
        (21.5, True, False),
        (22.0, False, False),
        (22.0, True, True),
        (22.5, False, True),
        (22.6, False, True),
    ],
)
def test_cool_hysteresis(current: float, was_running: bool, expected: bool) -> None:
    """Cooling starts and stops at the two edges of the dead band."""
    assert should_run("cool", current, 22.0, 0.5, was_running) is expected
