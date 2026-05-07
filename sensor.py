"""Cronicle sensor platform."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HOST, CONF_PORT, CONF_USE_SSL, DOMAIN
from .coordinator import CronicleCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class CronicleSensorDescription(SensorEntityDescription):
    """Cronicle sensor description."""


SENSOR_DESCRIPTIONS: tuple[CronicleSensorDescription, ...] = (
    CronicleSensorDescription(
        key="active_jobs",
        name="Active Jobs",
        icon="mdi:play-circle-multiple",
        native_unit_of_measurement="jobs",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    CronicleSensorDescription(
        key="total_events",
        name="Total Events",
        icon="mdi:calendar-multiple",
        native_unit_of_measurement="events",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    CronicleSensorDescription(
        key="enabled_events",
        name="Enabled Events",
        icon="mdi:calendar-check",
        native_unit_of_measurement="events",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    CronicleSensorDescription(
        key="last_job",
        name="Last Job",
        icon="mdi:history",
    ),
    CronicleSensorDescription(
        key="last_job_code",
        name="Last Job Code",
        icon="mdi:check-circle-outline",
    ),
    CronicleSensorDescription(
        key="last_job_duration",
        name="Last Job Duration",
        icon="mdi:timer-outline",
        native_unit_of_measurement="s",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    CronicleSensorDescription(
        key="last_job_finished",
        name="Last Job Finished",
        icon="mdi:clock-check-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    CronicleSensorDescription(
        key="recent_jobs",
        name="Recent Jobs",
        icon="mdi:format-list-bulleted",
        native_unit_of_measurement="jobs",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


def _device_info(entry: ConfigEntry) -> dict:
    scheme = "https" if entry.data.get(CONF_USE_SSL) else "http"
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": "Cronicle",
        "manufacturer": "Cronicle",
        "model": "Job Scheduler",
        "configuration_url": f"{scheme}://{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}",
    }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: CronicleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CronicleSensor(coordinator, entry, desc) for desc in SENSOR_DESCRIPTIONS
    )


class CronicleSensor(CoordinatorEntity[CronicleCoordinator], SensorEntity):
    entity_description: CronicleSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CronicleCoordinator,
        entry: ConfigEntry,
        description: CronicleSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = _device_info(entry)

    def _last_job(self):
        """Return the most-recent CompletedJob, or None."""
        jobs = self.coordinator.data.recent_jobs
        return jobs[0] if jobs else None

    @property
    def native_value(self):
        data = self.coordinator.data
        key = self.entity_description.key

        if key == "active_jobs":
            return len(data.active_jobs)
        if key == "total_events":
            return data.total_events
        if key == "enabled_events":
            return data.enabled_events
        if key == "recent_jobs":
            return len(data.recent_jobs)

        # All last_job_* sensors share the same source row.
        last = self._last_job()
        if last is None:
            return None

        if key == "last_job":
            return last.title
        if key == "last_job_code":
            return last.code
        if key == "last_job_duration":
            return round(last.elapsed)
        if key == "last_job_finished":
            # Prefer time_end; fall back to time_start + elapsed if needed.
            ts = last.time_end
            if ts <= 0 and last.time_start > 0:
                ts = last.time_start + last.elapsed
                _LOGGER.debug(
                    "last_job_finished: time_end missing, using time_start+elapsed=%s",
                    ts,
                )
            if ts <= 0:
                _LOGGER.debug(
                    "last_job_finished: no usable timestamp; "
                    "time_end=%s time_start=%s elapsed=%s",
                    last.time_end, last.time_start, last.elapsed,
                )
                return None
            return datetime.fromtimestamp(ts, tz=timezone.utc)

        return None

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data
        key = self.entity_description.key

        if key == "active_jobs":
            return {
                "jobs": [
                    {
                        "id": j.id,
                        "event": j.event,
                        "title": j.title,
                        "source": j.source,
                        "elapsed_s": round(j.elapsed),
                        "progress_pct": round(j.progress * 100, 1),
                        "hostname": j.hostname,
                        "target": j.nice_target,
                        "category": j.category,
                        "plugin": j.plugin,
                        "cpu_pct": round(j.cpu_current, 1),
                        "memory_mb": round(j.mem_current / 1024 / 1024, 1)
                        if j.mem_current
                        else 0,
                    }
                    for j in data.active_jobs
                ]
            }

        if key == "recent_jobs":
            return {
                "jobs": [
                    {
                        "id": j.id,
                        "event": j.event,
                        "title": j.title,
                        "exit_code": j.code,
                        "success": j.code == 0,
                        "elapsed_s": round(j.elapsed),
                        "hostname": j.hostname,
                        "category": j.category,
                        "plugin": j.plugin,
                        "source": j.source,
                        "description": j.description,
                        "time_start": j.time_start,
                        "time_end": j.time_end,
                        "finished": _fmt_ts(
                            j.time_end if j.time_end > 0
                            else (j.time_start + j.elapsed if j.time_start > 0 else 0)
                        ),
                    }
                    for j in data.recent_jobs
                ]
            }

        last = self._last_job()
        if last is not None and key == "last_job":
            return {
                "job_id": last.id,
                "event": last.event,
                "exit_code": last.code,
                "elapsed_s": round(last.elapsed),
                "hostname": last.hostname,
                "category": last.category,
                "plugin": last.plugin,
                "source": last.source,
                "description": last.description,
                "time_start": last.time_start,
                "time_end": last.time_end,
            }

        return {}


def _fmt_ts(epoch: float) -> str | None:
    """Format an epoch timestamp as ISO-8601, or None if invalid."""
    if not epoch or epoch <= 0:
        return None
    try:
        return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None
