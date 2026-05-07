"""Cronicle DataUpdateCoordinator."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CronicleAPIError, CronicleClient, CronicleData

_LOGGER = logging.getLogger(__name__)


class CronicleCoordinator(DataUpdateCoordinator[CronicleData]):
    def __init__(
        self,
        hass: HomeAssistant,
        client: CronicleClient,
        poll_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Cronicle",
            update_interval=timedelta(seconds=poll_interval),
        )
        self.client = client

    async def _async_update_data(self) -> CronicleData:
        try:
            return await self.client.fetch_all()
        except CronicleAPIError as e:
            raise UpdateFailed(f"Cronicle API error: {e}") from e
