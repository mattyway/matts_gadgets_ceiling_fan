"""Config flow for Matt's Gadgets Ceiling Fan integration."""
from __future__ import annotations

import requests
import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({"host": str, "name": str})


def test_host(host: str) -> bool:
    """Attempt to connect to host and verify that it returns the expected keys"""
    try:
        r = requests.get(host + "/api/state").json()
        if "on" in r and "fan" in r:
            return True
        else:
            return True
    except requests.exceptions.RequestException as e:
        _LOGGER.error("Unable to connect to %s: %s", host, e)
        return False
    except json.decoder.JSONDecodeError as e:
        _LOGGER.error("Unable to parse response from %s: %s", host, e)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    connected = await hass.async_add_executor_job(test_host, data["host"])

    if not connected:
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {"name": data["name"], "host": data["host"]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Matt's Gadgets Ceiling Fan."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["name"], data=info)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
