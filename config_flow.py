"""Config flow for MotionEye."""
import logging

import voluptuous as vol
from homeassistant import config_entries, core, exceptions
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_USERNAME,
)
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client, config_validation as cv

from .motion_eye import MotionEye
from .const import DOMAIN, MOTION_EYE_SCHEMA, MOTION_EYE_PLACEHOLDERS
from homeassistant.const import (CONF_ID, CONF_HOSTS, CONF_URL, CONF_AUTHENTICATION, CONF_USERNAME, CONF_PASSWORD)

_LOGGER = logging.getLogger(__name__)

@config_entries.HANDLERS.register(DOMAIN)
class MotionEyeConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for MotionEye."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, config):
        """Allow a user to configure MotionEye via the UI."""
        _LOGGER.info(f"motion step user {config}")
        if config is None:
            return self.async_show_form(
                step_id="user",
                data_schema=MOTION_EYE_SCHEMA,
                description_placeholders=MOTION_EYE_PLACEHOLDERS
            )
        return await self.async_step_import(config)

    async def async_step_import(self, config):
        """Centralized entry-creation step; used by both import & user creation."""
        if not config: return
        config = dict(config)
        data = {}
        _LOGGER.info(f"motion step import: {config}")
        meye = MotionEye(config)

        # Check for an update of existing data.
        existing = configured_instances(self.hass)
        _LOGGER.info(f"motion step update check? {list(existing)}")
        if meye.title in existing:
            _LOGGER.info(f"motion step update {meye.title}: {config}")
            return self.async_update_entry(existing[meye.title], data=config)

        _LOGGER.info(f"motion step unique: {meye.unique_id}")
        await self.async_set_unique_id(meye.unique_id)
        self._abort_if_unique_id_configured()

        _LOGGER.info(f"motion step create: {config}")
        return self.async_create_entry(title=meye.title, data=config)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for MotionEye."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_URL, default=self.config_entry.options.get(CONF_URL, "")): str,
            vol.Optional(CONF_AUTHENTICATION, default=self.config_entry.options.get(CONF_AUTHENTICATION, "basic")): str,
            vol.Required(CONF_USERNAME, default=self.config_entry.options.get(CONF_USERNAME, "admin")): str,
            vol.Required(CONF_PASSWORD, default=self.config_entry.options.get(CONF_PASSWORD, "")): str,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            description_placeholders=MOTION_EYE_PLACEHOLDERS
        )
