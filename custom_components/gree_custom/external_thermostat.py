"""External sensor thermostat for a Gree air conditioner."""

import asyncio
import logging
import math
from typing import Any, cast, override

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,  # pyright: ignore[reportPrivateImportUsage]
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,  # pyright: ignore[reportPrivateImportUsage]
    HVACAction,  # pyright: ignore[reportPrivateImportUsage]
    HVACMode,  # pyright: ignore[reportPrivateImportUsage]
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import Event, EventStateChangedData, State, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util.unit_conversion import TemperatureConverter

from .aiogree.api import OperationMode
from .aiogree.const import MAX_TEMP_C, MIN_TEMP_C
from .const import (
    CONF_COOL_ACTIVE_TEMPERATURE,
    CONF_COOL_IDLE_TEMPERATURE,
    CONF_DEVICE_OPTIONS,
    CONF_EXTERNAL_THERMOSTAT,
    CONF_EXTERNAL_THERMOSTAT_HYSTERESIS,
    CONF_EXTERNAL_THERMOSTAT_SENSOR,
    CONF_HEAT_ACTIVE_TEMPERATURE,
    CONF_HEAT_IDLE_TEMPERATURE,
    DEFAULT_COOL_ACTIVE_TEMPERATURE,
    DEFAULT_COOL_IDLE_TEMPERATURE,
    DEFAULT_EXTERNAL_THERMOSTAT_HYSTERESIS,
    DEFAULT_EXTERNAL_THERMOSTAT_TARGET,
    DEFAULT_HEAT_ACTIVE_TEMPERATURE,
    DEFAULT_HEAT_IDLE_TEMPERATURE,
    DOMAIN,
    UNITS_GREE_TO_HA,
)
from .coordinator import GreeCoordinator
from .entity import GreeEntity, GreeEntityDescription
from .thermostat import ThermostatMode, should_run

_LOGGER = logging.getLogger(__name__)

GATTR_EXTERNAL_THERMOSTAT = "external_thermostat"


class GreeExternalThermostatDescription(
    GreeEntityDescription, ClimateEntityDescription, frozen_or_thawed=True
):
    """Description of an external Gree thermostat entity."""


class GreeExternalThermostat(  # pyright: ignore[reportIncompatibleVariableOverride]
    GreeEntity, ClimateEntity, RestoreEntity
):
    """Control a Gree device from a Home Assistant temperature sensor."""

    _attr_should_poll = False
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = MIN_TEMP_C
    _attr_max_temp = MAX_TEMP_C
    _attr_target_temperature_step = 0.5

    entity_description: GreeExternalThermostatDescription

    def __init__(
        self,
        coordinator: GreeCoordinator,
        config: dict[str, Any],
        hvac_modes: list[HVACMode],
    ) -> None:
        """Initialize the thermostat."""
        super().__init__(
            GreeExternalThermostatDescription(
                key=GATTR_EXTERNAL_THERMOSTAT,
                translation_key=GATTR_EXTERNAL_THERMOSTAT,
            ),
            coordinator,
            restore_state=True,
            check_availability=coordinator.check_availability,
        )

        self._sensor_entity_id: str = config[CONF_EXTERNAL_THERMOSTAT_SENSOR]
        self._attr_hvac_modes = hvac_modes
        self._attr_hvac_mode = HVACMode.OFF
        self._last_hvac_mode = next(
            (mode for mode in hvac_modes if mode != HVACMode.OFF), HVACMode.HEAT
        )
        self._attr_hvac_action = HVACAction.OFF
        self._attr_current_temperature: float | None = None
        self._attr_target_temperature = DEFAULT_EXTERNAL_THERMOSTAT_TARGET
        self._running = False
        self._control_lock = asyncio.Lock()

    @property
    @override
    def available(self) -> bool:
        """Return whether both the device and external sensor are available."""
        return super().available and self._attr_current_temperature is not None

    @override
    async def async_added_to_hass(self) -> None:
        """Restore state, read the sensor and start control."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._sensor_entity_id],
                self._async_sensor_changed,
            )
        )

        self._update_sensor(self.hass.states.get(self._sensor_entity_id))
        await self._async_restore_state()
        self._running = self._infer_running()
        self._update_hvac_action()

        if self._attr_hvac_mode != HVACMode.OFF and self.available:
            try:
                await self._async_control()
            except Exception:
                _LOGGER.exception(
                    "Failed to start external thermostat for %s",
                    self.device.unique_id,
                )

    async def _async_restore_state(self) -> None:
        """Restore the virtual target temperature and mode."""
        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        target = last_state.attributes.get(ATTR_TEMPERATURE)
        if isinstance(target, int | float) and math.isfinite(target):
            last_unit = (
                UnitOfTemperature.CELSIUS
                if float(target) <= MAX_TEMP_C
                else UnitOfTemperature.FAHRENHEIT
            )
            self._attr_target_temperature = TemperatureConverter.convert(
                float(target), last_unit, UnitOfTemperature.CELSIUS
            )

        try:
            mode = HVACMode(last_state.state)
        except ValueError:
            return

        if mode in self._attr_hvac_modes:
            self._attr_hvac_mode = mode
            if mode != HVACMode.OFF:
                self._last_hvac_mode = mode

    @override
    def _handle_coordinator_update(self) -> None:
        """Reapply control after device state changes."""
        if self._attr_hvac_mode != HVACMode.OFF and self.available:
            self.hass.async_create_task(self._async_control_after_update())
        self.async_write_ha_state()

    async def _async_control_after_update(self) -> None:
        """Run control from a coordinator callback without leaking errors."""
        try:
            await self._async_control()
        except Exception:
            _LOGGER.exception(
                "Failed to update external thermostat for %s",
                self.device.unique_id,
            )

    async def _async_sensor_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle a new external sensor value."""
        self._update_sensor(event.data.get("new_state"))
        if self._attr_hvac_mode != HVACMode.OFF and self.available:
            try:
                await self._async_control()
            except Exception:
                _LOGGER.exception(
                    "Failed to control %s from external sensor %s",
                    self.device.unique_id,
                    self._sensor_entity_id,
                )
        self.async_write_ha_state()

    @callback
    def _update_sensor(self, state: State | None) -> None:
        """Store an external sensor value in Celsius."""
        self._attr_current_temperature = None
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return

        try:
            value = float(state.state)
            if not math.isfinite(value):
                _LOGGER.error(
                    "Unable to read external thermostat sensor %s: illegal state %s",
                    self._sensor_entity_id,
                    state.state,
                )
                return
            unit = state.attributes.get(
                ATTR_UNIT_OF_MEASUREMENT, UnitOfTemperature.CELSIUS
            )
            self._attr_current_temperature = TemperatureConverter.convert(
                value, unit, UnitOfTemperature.CELSIUS
            )
        except (TypeError, ValueError) as err:
            _LOGGER.error(
                "Unable to read external thermostat sensor %s: %s",
                self._sensor_entity_id,
                err,
            )

    def _infer_running(self) -> bool:
        """Infer the dead-band state from the current device setpoint."""
        if self._attr_hvac_mode not in (HVACMode.HEAT, HVACMode.COOL):
            return False
        if not self.device.power_mode:
            return False

        expected_mode = (
            OperationMode.heat
            if self._attr_hvac_mode == HVACMode.HEAT
            else OperationMode.cool
        )
        if self.device.operation_mode != expected_mode:
            return False

        current_setpoint = TemperatureConverter.convert(
            float(self.device.target_temperature),
            UNITS_GREE_TO_HA[self.device.target_temperature_unit],
            UnitOfTemperature.CELSIUS,
        )
        active_setpoint, idle_setpoint = self._control_setpoints()
        return abs(current_setpoint - active_setpoint) <= abs(
            current_setpoint - idle_setpoint
        )

    def _control_setpoints(self) -> tuple[float, float]:
        """Return active and idle device setpoints for the selected mode."""
        if self._attr_hvac_mode == HVACMode.HEAT:
            return (
                self._setting(
                    CONF_HEAT_ACTIVE_TEMPERATURE, DEFAULT_HEAT_ACTIVE_TEMPERATURE
                ),
                self._setting(
                    CONF_HEAT_IDLE_TEMPERATURE, DEFAULT_HEAT_IDLE_TEMPERATURE
                ),
            )
        return (
            self._setting(
                CONF_COOL_ACTIVE_TEMPERATURE, DEFAULT_COOL_ACTIVE_TEMPERATURE
            ),
            self._setting(CONF_COOL_IDLE_TEMPERATURE, DEFAULT_COOL_IDLE_TEMPERATURE),
        )

    def _setting(self, key: str, default: float) -> float:
        """Return the current external thermostat setting."""
        options = self.coordinator.device_config.get(CONF_DEVICE_OPTIONS, {})
        config = options.get(CONF_EXTERNAL_THERMOSTAT, {})
        return float(config.get(key, default))

    def _update_hvac_action(self) -> None:
        """Update the action shown by Home Assistant."""
        if self._attr_hvac_mode == HVACMode.OFF:
            self._attr_hvac_action = HVACAction.OFF
        elif not self._running:
            self._attr_hvac_action = HVACAction.IDLE
        elif self._attr_hvac_mode == HVACMode.HEAT:
            self._attr_hvac_action = HVACAction.HEATING
        else:
            self._attr_hvac_action = HVACAction.COOLING

    async def _async_control(self) -> None:
        """Choose and send the Gree setpoint for the current sensor value."""
        async with self._control_lock:
            if self._attr_hvac_mode not in (HVACMode.HEAT, HVACMode.COOL):
                return
            if (
                self._attr_current_temperature is None
                or self._attr_target_temperature is None
            ):
                return

            mode = cast(ThermostatMode, self._attr_hvac_mode.value)
            self._running = should_run(
                mode,
                self._attr_current_temperature,
                self._attr_target_temperature,
                self._setting(
                    CONF_EXTERNAL_THERMOSTAT_HYSTERESIS,
                    DEFAULT_EXTERNAL_THERMOSTAT_HYSTERESIS,
                ),
                self._running,
            )
            self._update_hvac_action()

            active_setpoint, idle_setpoint = self._control_setpoints()
            await self._async_apply_device_setpoint(
                active_setpoint if self._running else idle_setpoint
            )
            self.async_write_ha_state()

    async def _async_apply_device_setpoint(self, setpoint_c: float) -> None:
        """Apply mode, power and a Celsius setpoint to the Gree device."""
        operation_mode = (
            OperationMode.heat
            if self._attr_hvac_mode == HVACMode.HEAT
            else OperationMode.cool
        )
        device_unit = UNITS_GREE_TO_HA[self.device.target_temperature_unit]
        device_setpoint = TemperatureConverter.convert(
            setpoint_c, UnitOfTemperature.CELSIUS, device_unit
        )
        changed = False

        if self.device.operation_mode != operation_mode:
            self.device.set_operation_mode(operation_mode)
            if self.coordinator.feature_auto_xfan:
                self.device.set_feature_xfan(operation_mode == OperationMode.cool)
            changed = True
        if not self.device.power_mode:
            self.device.set_power_mode(True)
            if self.coordinator.feature_auto_light:
                self.device.set_feature_light(True)
            changed = True
        if not math.isclose(
            float(self.device.target_temperature), device_setpoint, abs_tol=0.1
        ):
            self.device.set_target_temperature(float(device_setpoint))
            changed = True

        if changed:
            await self.coordinator.push_device_status()
            self.coordinator.async_update_listeners()
            await self.coordinator.async_request_refresh()

    async def _async_turn_device_off(self) -> None:
        """Turn the physical device off once."""
        if not self.device.power_mode:
            return
        self.device.set_power_mode(False)
        if self.coordinator.feature_auto_light:
            self.device.set_feature_light(False)
        await self.coordinator.push_device_status()
        self.coordinator.async_update_listeners()
        await self.coordinator.async_request_refresh()

    def _ensure_available(self, require_sensor: bool = True) -> None:
        """Raise the standard service error when control is unavailable."""
        if not super().available or (
            require_sensor and self._attr_current_temperature is None
        ):
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="entity_unavailable"
            )

    @override
    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the virtual target temperature."""
        temperature: float | None = kwargs.get(ATTR_TEMPERATURE)
        hvac_mode: HVACMode | None = kwargs.get(ATTR_HVAC_MODE)
        if temperature is None and hvac_mode is None:
            return

        self._ensure_available(require_sensor=hvac_mode != HVACMode.OFF)
        if temperature is not None:
            self._attr_target_temperature = float(temperature)

        if hvac_mode is not None:
            await self.async_set_hvac_mode(hvac_mode)
            return

        if self._attr_hvac_mode != HVACMode.OFF:
            try:
                await self._async_control()
            except Exception as err:
                raise HomeAssistantError(
                    translation_domain=DOMAIN, translation_key="generic"
                ) from err
        self.async_write_ha_state()

    @override
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the virtual thermostat mode."""
        if hvac_mode not in self._attr_hvac_modes:
            return
        self._ensure_available(require_sensor=hvac_mode != HVACMode.OFF)

        try:
            if hvac_mode == HVACMode.OFF:
                self._attr_hvac_mode = HVACMode.OFF
                self._running = False
                self._update_hvac_action()
                await self._async_turn_device_off()
            else:
                self._attr_hvac_mode = hvac_mode
                self._last_hvac_mode = hvac_mode
                self._running = self._infer_running()
                await self._async_control()
        except Exception as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="generic"
            ) from err

        self.async_write_ha_state()

    @override
    async def async_turn_on(self) -> None:
        """Turn on with the last selected heat or cool mode."""
        await self.async_set_hvac_mode(self._last_hvac_mode)

    @override
    async def async_turn_off(self) -> None:
        """Turn off the thermostat and physical device."""
        await self.async_set_hvac_mode(HVACMode.OFF)
