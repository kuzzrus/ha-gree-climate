"""Control rules for the external Gree thermostat."""

import math
from typing import Literal

type ThermostatMode = Literal["cool", "heat"]


def ifeel_temperature(value: float, minimum: int = 16, maximum: int = 35) -> int | None:
    """Round a room temperature to a safe whole-degree I Feel value."""
    if not math.isfinite(value):
        return None

    rounded = math.floor(value + 0.5)
    if not minimum <= rounded <= maximum:
        return None
    return rounded


def should_run(
    mode: ThermostatMode,
    current_temperature: float,
    target_temperature: float,
    activation_hysteresis: float,
    deactivation_hysteresis: float,
    was_running: bool,
) -> bool:
    """Return whether the thermostat should use its active setpoint.

    The last state is kept between the activation and deactivation limits.
    """
    if mode == "heat":
        if current_temperature <= target_temperature - activation_hysteresis:
            return True
        if current_temperature >= target_temperature + deactivation_hysteresis:
            return False
    else:
        if current_temperature >= target_temperature + activation_hysteresis:
            return True
        if current_temperature <= target_temperature - deactivation_hysteresis:
            return False

    return was_running
