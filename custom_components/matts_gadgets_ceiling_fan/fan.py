from homeassistant.components import matts_gadgets_ceiling_fan
import logging
import json
import requests
from typing import Any, Optional
from homeassistant.components.fan import (
    FanEntity,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_MEDIUM,
    SUPPORT_PRESET_MODE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices
) -> bool:
    """Set up Matt's Gadgets Ceiling Fan from a config entry."""
    _LOGGER.debug("Setting up entry for %s", entry.as_dict())

    async_add_devices(
        [
            MattsGadgetsCeilingFan(
                name=entry.data["name"], id=entry.entry_id, host=entry.data["host"]
            )
        ]
    )

    return True


class MattsGadgetsCeilingFan(FanEntity):
    def __init__(self, name: str, id: str, host: str) -> None:
        self._name = name
        self._id = id
        self._host = host
        self._available = True
        self._is_on = False
        self._preset_mode = SPEED_LOW

    @property
    def unique_id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        """Name of the fan."""
        return self._name

    @property
    def supported_features(self) -> int:
        """The set of features that the fan provides"""
        return SUPPORT_PRESET_MODE

    @property
    def is_on(self) -> bool:
        """If the fan is currently on or off."""
        return self._is_on

    @property
    def preset_mode(self) -> str:
        return self._preset_mode

    @property
    def preset_modes(self) -> "list[str]":
        return [SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]

    @property
    def available(self) -> bool:
        return self._available

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        self._preset_mode = preset_mode
        self.tell()

    def turn_on(
        self,
        speed: Optional[str] = None,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        self._is_on = True
        self._preset_mode = preset_mode
        self.tell()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        self._is_on = False
        self.tell()

    def tell(self):
        """Send the state to the device"""
        data = {"on": self._is_on}

        if self._preset_mode == SPEED_LOW:
            data["fan"] = 1
        elif self._preset_mode == SPEED_MEDIUM:
            data["fan"] = 2
        elif self._preset_mode == SPEED_HIGH:
            data["fan"] = 3

        _LOGGER.debug("Attempting to tell %s with %s", self._name, data)
        try:
            requests.post(self._host + "/api/state", json=data)
            _LOGGER.debug("Telling %s succeeded", self._name)
            self._available = True
        except requests.exceptions.RequestException as e:
            _LOGGER.warn("Unable to tell %s: %s", self._name, e)
            self._available = False

    def update(self):
        """Get the state from the device"""
        _LOGGER.debug("Attempting to update %s", self._name)
        try:
            r = requests.get(self._host + "/api/state").json()
            _LOGGER.debug("Updating %s with: %s", self._name, r)
            self._is_on = r["on"]
            if r["fan"] == 1:
                self._preset_mode = SPEED_LOW
            elif r["fan"] == 2:
                self._preset_mode = SPEED_MEDIUM
            elif r["fan"] == 3:
                self._preset_mode = SPEED_HIGH
            self._available = True
        except requests.exceptions.RequestException as e:
            _LOGGER.warn("Unable to update %s: %s", self._name, e)
            self._available = False
        except json.decoder.JSONDecodeError as e:
            _LOGGER.error("Unable to parse response from %s: %s", self._name, e)

    @property
    def device_info(self):
        return {
            "identifiers": {(matts_gadgets_ceiling_fan.DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Matt's Gadgets",
            "model": "eCO",
            "sw_version": "1.0",
        }
