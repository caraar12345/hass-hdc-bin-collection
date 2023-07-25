"""Config flow for hdc_bin_collection integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from hdc_bin_collection import verify_uprn

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_UPRN_SCHEMA = vol.Schema(
    {
        vol.Required("uprn"): int,
    }
)


class HdcBinCollection:
    def __init__(self, uprn: int, session) -> None:
        self.uprn = uprn
        self.session = session

    async def hdc_verify_uprn(self) -> dict:
        return await verify_uprn(session=self.session, uprn=self.uprn)


async def validate_input(session, data: dict[str, int]) -> dict[str, int]:
    hdc = HdcBinCollection(session=session, uprn=data["uprn"])
    uprn_verification = await hdc.hdc_verify_uprn()

    if uprn_verification[1] == "invalid_uprn":
        raise InvalidAuth

    if uprn_verification[1].startswith("connection_error"):
        raise CannotConnect

    if uprn_verification[0]:
        return {"title": "Bin collections at UPRN " + str(data["uprn"])}


class HdcConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for hdc_bin_collection."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, int] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        session = async_get_clientsession(hass=self.hass)

        if user_input is not None:
            await self.async_set_unique_id("hdc_bins_" + str(user_input["uprn"]))
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(session, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                _LOGGER.error(
                    f"UPRN {user_input['uprn']} is either invalid or not within the Harborough district"
                )
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_UPRN_SCHEMA, errors=errors
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
