"""Support for filtering events from a calendar entity."""

import logging
from datetime import datetime
from typing import Any
# from ast import literal_eval

import voluptuous as vol
from homeassistant.components.calendar import (
    CALENDAR_EVENT_SCHEMA,
    CalendarEntity,
    CalendarEvent,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_template_result, TrackTemplate, TrackTemplateResult, EventStateChangedData
from homeassistant.helpers.template import Template

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    _: Any = None,
) -> bool | None:
    """Set up the Template Calendar platform."""
    name = config.get("name")
    template = config.get("template")

    if not name or not template:
        _LOGGER.error("Missing required configuration items")
        return None

    template_calendar = TemplateCalendarEntity(hass, name, template)
    async_add_entities([template_calendar])

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> bool | None:
    """Set up the Template Calendar platform."""
    name = config_entry.options.get("name")
    template = config_entry.options.get("template")

    if not name or not template:
        _LOGGER.error("Missing required configuration items")
        return None

    template_calendar = TemplateCalendarEntity(
        hass,
        name,
        template,
        config_entry.entry_id,
    )
    async_add_entities([template_calendar])

    return True


class TemplateCalendarEntity(CalendarEntity):
    """Representation of a filtered calendar entity."""

    _attr_supported_features = 0

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        template_string: str,
        config_entry_id: str | None = None,
    ) -> None:
        """Initialize the Template Calendar entity."""
        self.hass = hass
        self._name = name
        self._template = TrackTemplate(Template(template_string, hass), None)
        self._event: CalendarEvent | None = None
        # events generated from the template (list of dict-like CalendarEvent)
        self._events: list[CalendarEvent] = []
        self._attr_unique_id = config_entry_id

    async def async_added_to_hass(self) -> None:
        """Entity added to hass — set up template dependency listeners and render initial events."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_template_result(
                self.hass,
                [self._template],
                self._parse_template_result,
            ).async_remove
        )

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        return self._event

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return events within a datetime range."""
        return [
            event
            for event in self._events
            if event.start_datetime_local and end_date > event.start_datetime_local >= start_date
        ]

    @callback
    def _parse_template_result(self, event: Event[EventStateChangedData] | None, updates: list[TrackTemplateResult]) -> None:
        """Parse the result of the template rendering."""
        result = updates[0].result

        # _LOGGER.info("Template result type: %s", type(result))
        # _LOGGER.info("Template result: %s", result)

        if isinstance(result, TemplateError):
            _LOGGER.error("Error rendering template %s: %s", self._name, result)
            return

        if not result:
            self._events = []
            self._event = None
            self.async_write_ha_state()
            return

        # try:
        #     data = literal_eval(result)
        # except Exception as e:
        #     _LOGGER.error("Template %s did not return valid JSON", self._name)
        #     _LOGGER.exception(e)
        #     self._events = []
        #     self._event = None
        #     self.async_write_ha_state()
        #     return

        data = result

        if not isinstance(data, list):
            _LOGGER.error("Template %s did not return a list of events", self._name)
            self._events = []
            self._event = None
            self.async_write_ha_state()
            return

        self._events = []
        for event_data in data:
            try:
                validated = CALENDAR_EVENT_SCHEMA(event_data)
                self._events.append(CalendarEvent(**validated))
            except (vol.Invalid, TypeError, ValueError) as err:
                _LOGGER.warning("Invalid event data from template %s: %s", self._name, err)

        self._events.sort(key=lambda x: x.start)
        self._event = self._events[0] if self._events else None
        self.async_write_ha_state()