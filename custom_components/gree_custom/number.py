"""Support for Gree number entities (e.g., target humidity control)."""

from collections.abc import Callable
import logging
import math
from typing import Any, override

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .aiogree.api import HumidityControlMode, OperationMode
from .aiogree.const import (
    MAX_HUM_COOL_P,
    MAX_HUM_DRY_P,
    MAX_TEMP_C,
    MIN_HUM_COOL_P,
    MIN_HUM_DRY_P,
    MIN_TEMP_C,
)
from .aiogree.device import GreeDevice
from .const import (
    CONF_COOL_ACTIVE_TEMPERATURE,
    CONF_COOL_IDLE_TEMPERATURE,
    CONF_DEVICE_OPTIONS,
    CONF_DEVICES,
    CONF_EXTERNAL_THERMOSTAT,
    CONF_EXTERNAL_THERMOSTAT_HYSTERESIS,
    CONF_EXTERNAL_THERMOSTAT_SENSOR,
    CONF_HEAT_ACTIVE_TEMPERATURE,
    CONF_HEAT_IDLE_TEMPERATURE,
    DEFAULT_COOL_ACTIVE_TEMPERATURE,
    DEFAULT_COOL_IDLE_TEMPERATURE,
    DEFAULT_EXTERNAL_THERMOSTAT_HYSTERESIS,
    DEFAULT_HEAT_ACTIVE_TEMPERATURE,
    DEFAULT_HEAT_IDLE_TEMPERATURE,
    DOMAIN,
    GATTR_FEAT_HUMIDITY,
    GATTR_FEAT_HUMIDITY_TARGET,
    MAX_THERMOSTAT_HYSTERESIS,
    MIN_THERMOSTAT_HYSTERESIS,
)
from .coordinator import GreeConfigEntry, GreeCoordinator
from .entity import GreeEntity, GreeEntityDescription
from .platform_helpers import supported_descriptions

_LOGGER = logging.getLogger(__name__)


class GreeNumberDescription(
    GreeEntityDescription, NumberEntityDescription, frozen_or_thawed=True
):
    """Description of a Gree number."""

    value_func: Callable[[GreeDevice], int]
    set_func: Callable[[GreeDevice, int], None]
    min_func: Callable[[GreeDevice], int] | None = None
    max_func: Callable[[GreeDevice], int] | None = None
    updates_device: bool = True


NUMBER_TYPES: list[GreeNumberDescription] = [
    GreeNumberDescription(
        feature_key_override=GATTR_FEAT_HUMIDITY,
        key=GATTR_FEAT_HUMIDITY_TARGET,
        translation_key=GATTR_FEAT_HUMIDITY_TARGET,
        device_class=NumberDeviceClass.HUMIDITY,
        mode=NumberMode.AUTO,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        value_func=lambda device: device.feature_humidity_control_target,
        set_func=lambda device, value: device.set_feature_humidity_control_target(
            value
        ),
        additional_available_func=lambda device: (
            device.operation_mode in (OperationMode.cool, OperationMode.dry)
            and device.feature_humidity_control is HumidityControlMode.target_dry
        ),
        min_func=lambda device: (
            MIN_HUM_COOL_P
            if device.operation_mode == OperationMode.cool
            else MIN_HUM_DRY_P
        ),
        max_func=lambda device: (
            MAX_HUM_COOL_P
            if device.operation_mode == OperationMode.cool
            else MAX_HUM_DRY_P
        ),
        updates_device=True,
    )
]


class GreeThermostatNumberDescription(
    GreeEntityDescription, NumberEntityDescription, frozen_or_thawed=True
):
    """Description of a stored external thermostat setting."""

    config_key: str
    default_value: float


THERMOSTAT_NUMBER_TYPES: tuple[GreeThermostatNumberDescription, ...] = (
    GreeThermostatNumberDescription(
        key="external_thermostat_hysteresis",
        translation_key="external_thermostat_hysteresis",
        config_key=CONF_EXTERNAL_THERMOSTAT_HYSTERESIS,
        default_value=DEFAULT_EXTERNAL_THERMOSTAT_HYSTERESIS,
        device_class=NumberDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.BOX,
        native_min_value=MIN_THERMOSTAT_HYSTERESIS,
        native_max_value=MAX_THERMOSTAT_HYSTERESIS,
        native_step=0.1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    GreeThermostatNumberDescription(
        key="external_thermostat_heat_active_temperature",
        translation_key="external_thermostat_heat_active_temperature",
        config_key=CONF_HEAT_ACTIVE_TEMPERATURE,
        default_value=DEFAULT_HEAT_ACTIVE_TEMPERATURE,
        device_class=NumberDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.BOX,
        native_min_value=MIN_TEMP_C,
        native_max_value=MAX_TEMP_C,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    GreeThermostatNumberDescription(
        key="external_thermostat_heat_idle_temperature",
        translation_key="external_thermostat_heat_idle_temperature",
        config_key=CONF_HEAT_IDLE_TEMPERATURE,
        default_value=DEFAULT_HEAT_IDLE_TEMPERATURE,
        device_class=NumberDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.BOX,
        native_min_value=MIN_TEMP_C,
        native_max_value=MAX_TEMP_C,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    GreeThermostatNumberDescription(
        key="external_thermostat_cool_active_temperature",
        translation_key="external_thermostat_cool_active_temperature",
        config_key=CONF_COOL_ACTIVE_TEMPERATURE,
        default_value=DEFAULT_COOL_ACTIVE_TEMPERATURE,
        device_class=NumberDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.BOX,
        native_min_value=MIN_TEMP_C,
        native_max_value=MAX_TEMP_C,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    GreeThermostatNumberDescription(
        key="external_thermostat_cool_idle_temperature",
        translation_key="external_thermostat_cool_idle_temperature",
        config_key=CONF_COOL_IDLE_TEMPERATURE,
        default_value=DEFAULT_COOL_IDLE_TEMPERATURE,
        device_class=NumberDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.BOX,
        native_min_value=MIN_TEMP_C,
        native_max_value=MAX_TEMP_C,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
)

THERMOSTAT_DEFAULTS = {
    description.config_key: description.default_value
    for description in THERMOSTAT_NUMBER_TYPES
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches from a config entry."""

    _LOGGER.debug("Setting up Number Entities")

    entities: list[GreeNumber | GreeThermostatSettingNumber] = []

    for coordinator in entry.runtime_data.values():
        descriptions = supported_descriptions(
            NUMBER_TYPES,
            coordinator.device,
            coordinator.device_config,
        )

        _LOGGER.debug(
            "Adding Number Entities for device '%s': %s",
            coordinator.device.mac_address,
            [d.key for d in descriptions],
        )

        entities.extend(
            GreeNumber(
                description,
                coordinator,
                coordinator.restore_states,
                coordinator.check_availability,
            )
            for description in descriptions
        )

        options = coordinator.device_config.get(CONF_DEVICE_OPTIONS, {})
        thermostat_config = options.get(CONF_EXTERNAL_THERMOSTAT, {})
        if thermostat_config.get(CONF_EXTERNAL_THERMOSTAT_SENSOR):
            entities.extend(
                GreeThermostatSettingNumber(description, coordinator, entry)
                for description in THERMOSTAT_NUMBER_TYPES
            )

    async_add_entities(entities)


class GreeNumber(GreeEntity, NumberEntity):  # pyright: ignore[reportIncompatibleVariableOverride]
    """Defines a Gree Number entity."""

    entity_description: GreeNumberDescription

    def __init__(
        self,
        description: GreeNumberDescription,
        coordinator: GreeCoordinator,
        restore_state: bool = True,
        check_availability: bool = True,
    ) -> None:
        """Initialize switch."""
        super().__init__(description, coordinator, restore_state, check_availability)

        self.entity_description = description  # pyright: ignore[reportIncompatibleVariableOverride]
        _LOGGER.debug(
            "Initialized number: %s (check_availability=%s)",
            self.unique_id,
            self.check_availability,
        )

    @property
    @override
    def native_min_value(self) -> float:
        """Return the minimum allowed value."""
        if self.entity_description.min_func is not None:
            return self.entity_description.min_func(self.device)

        return super().native_min_value

    @property
    @override
    def native_max_value(self) -> float:
        """Return the maximum allowed value."""
        if self.entity_description.max_func is not None:
            return self.entity_description.max_func(self.device)

        return super().native_max_value

    @property
    @override
    def native_value(self) -> float:
        """Return the state of the sensor."""
        return self.entity_description.value_func(self.device)

    @override
    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        if not self.available:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="entity_unavailable"
            )

        try:
            self.entity_description.set_func(self.device, int(value))

            if self.entity_description.updates_device:
                await self.coordinator.push_device_status()

            # notify coordinator listeners of state change so that dependent entities are updated immediately
            self.coordinator.async_update_listeners()

        except Exception as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="generic"
            ) from err

        self.async_write_ha_state()


class GreeThermostatSettingNumber(  # pyright: ignore[reportIncompatibleVariableOverride]
    GreeEntity, NumberEntity
):
    """Store one live external thermostat setting."""

    entity_description: GreeThermostatNumberDescription

    def __init__(
        self,
        description: GreeThermostatNumberDescription,
        coordinator: GreeCoordinator,
        entry: GreeConfigEntry,
    ) -> None:
        """Initialize the external thermostat setting."""
        super().__init__(
            description,
            coordinator,
            restore_state=False,
            check_availability=False,
        )
        self.entity_description = description  # pyright: ignore[reportIncompatibleVariableOverride]
        self._entry = entry

    def _thermostat_config(self) -> dict[str, Any]:
        """Return the current external thermostat configuration."""
        options = self.coordinator.device_config.get(CONF_DEVICE_OPTIONS, {})
        return options.get(CONF_EXTERNAL_THERMOSTAT, {})

    def _config_value(self, key: str) -> float:
        """Return one setting with its default."""
        default = THERMOSTAT_DEFAULTS[key]
        return float(self._thermostat_config().get(key, default))

    @property
    @override
    def native_value(self) -> float:
        """Return the saved setting."""
        return self._config_value(self.entity_description.config_key)

    @property
    @override
    def native_min_value(self) -> float:
        """Keep paired active and idle setpoints in a valid order."""
        key = self.entity_description.config_key
        if key == CONF_HEAT_ACTIVE_TEMPERATURE:
            return self._config_value(CONF_HEAT_IDLE_TEMPERATURE) + 0.5
        if key == CONF_COOL_IDLE_TEMPERATURE:
            return self._config_value(CONF_COOL_ACTIVE_TEMPERATURE) + 0.5
        return super().native_min_value

    @property
    @override
    def native_max_value(self) -> float:
        """Keep paired active and idle setpoints in a valid order."""
        key = self.entity_description.config_key
        if key == CONF_HEAT_IDLE_TEMPERATURE:
            return self._config_value(CONF_HEAT_ACTIVE_TEMPERATURE) - 0.5
        if key == CONF_COOL_ACTIVE_TEMPERATURE:
            return self._config_value(CONF_COOL_IDLE_TEMPERATURE) - 0.5
        return super().native_max_value

    @override
    async def async_set_native_value(self, value: float) -> None:
        """Save and apply the setting without reloading the integration."""
        step = float(self.entity_description.native_step or 1)
        if (
            value < self.native_min_value
            or value > self.native_max_value
            or not math.isclose(value / step, round(value / step), abs_tol=1e-6)
        ):
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="invalid_thermostat_setting",
            )

        try:
            data = dict(self._entry.data)
            devices = dict(data[CONF_DEVICES])
            device_config = dict(devices[self.device.mac_address])
            options = dict(device_config[CONF_DEVICE_OPTIONS])
            thermostat_config = dict(options[CONF_EXTERNAL_THERMOSTAT])

            thermostat_config[self.entity_description.config_key] = value
            options[CONF_EXTERNAL_THERMOSTAT] = thermostat_config
            device_config[CONF_DEVICE_OPTIONS] = options
            devices[self.device.mac_address] = device_config
            data[CONF_DEVICES] = devices

            self.coordinator.device_config = device_config
            self.hass.config_entries.async_update_entry(self._entry, data=data)
            self.coordinator.async_update_listeners()
        except Exception as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="generic"
            ) from err

        self.async_write_ha_state()
