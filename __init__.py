"""Cronicle integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CronicleClient
from .const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_POLL_INTERVAL,
    CONF_PORT,
    CONF_RECENT_JOBS_COUNT,
    CONF_USE_SSL,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_RECENT_JOBS_COUNT,
    DOMAIN,
)
from .coordinator import CronicleCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


def _opt(entry: ConfigEntry, key: str, default):
    """Get option value with fallback to data, then default."""
    return entry.options.get(key, entry.data.get(key, default))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    poll_interval = _opt(entry, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
    history_limit = _opt(entry, CONF_RECENT_JOBS_COUNT, DEFAULT_RECENT_JOBS_COUNT)

    session = async_get_clientsession(hass)

    client = CronicleClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        api_key=entry.data[CONF_API_KEY],
        session=session,
        use_ssl=entry.data.get(CONF_USE_SSL, False),
        history_limit=history_limit,
    )

    coordinator = CronicleCoordinator(hass, client, poll_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
