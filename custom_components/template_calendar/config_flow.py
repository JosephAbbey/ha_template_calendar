"""Config flow for Template Calendar integration."""

from collections.abc import Mapping
from typing import Any, cast

import voluptuous as vol
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)

from . import DOMAIN

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(
        vol.Schema(
            {
                vol.Required("name"): selector.TextSelector(
                    selector.TextSelectorConfig()
                ),
                vol.Required("template"): selector.TemplateSelector(
                    selector.TemplateSelectorConfig()
                ),  # Template
            }
        ),
    ),
}


OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(
        vol.Schema(
            {
                vol.Required("name"): selector.TextSelector(
                    selector.TextSelectorConfig()
                ),
                vol.Required("template"): selector.TemplateSelector(
                    selector.TemplateSelectorConfig()
                ),  # Template
            }
        ),
    ),
}


class TemplateCalendarConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle config flow for template helper."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    @callback
    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""
        return cast(str, options["name"])
