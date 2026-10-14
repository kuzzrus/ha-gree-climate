"""Control rules for the external Gree thermostat."""

from typing import Literal

type ThermostatMode = Literal["cool", "heat"]


def should_run(
    mode: ThermostatMode,
    current_temperature: float,
    target_temperature: float,
    hysteresis: float,
    was_running: bool,
) -> bool:
    """Return whether the thermostat should use its active setpoint.

    The last state is kept while the temperature is inside the dead band.
    """
    if mode == "heat":
        if current_temperature <= target_temperature - hysteresis:
            return True
        if current_temperature >= target_temperature + hysteresis:
            return False
    else:
        if current_temperature >= target_temperature + hysteresis:
            return True
        if current_temperature <= target_temperature - hysteresis:
            return False

    return was_running
