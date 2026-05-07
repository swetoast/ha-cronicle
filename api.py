"""Cronicle REST API client."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

import aiohttp

_LOGGER = logging.getLogger(__name__)


@dataclass
class ActiveJob:
    """Represents a currently-running Cronicle job."""
    id: str
    event: str
    title: str
    source: str
    elapsed: float
    progress: float
    hostname: str
    nice_target: str
    category: str
    plugin: str
    time_start: float
    timeout: int
    pid: int | None
    cpu_current: float
    mem_current: int


@dataclass
class CompletedJob:
    """Represents one row in get_history."""
    id: str
    event: str
    title: str
    code: int
    elapsed: float
    hostname: str
    category: str
    plugin: str
    source: str
    description: str
    time_start: float
    time_end: float


@dataclass
class CronicleData:
    scheduler_enabled: bool = False
    active_jobs: list[ActiveJob] = field(default_factory=list)
    total_events: int = 0
    enabled_events: int = 0
    recent_jobs: list[CompletedJob] = field(default_factory=list)


class CronicleAPIError(Exception):
    """Raised when a Cronicle API call fails or returns a non-zero code."""


class CronicleClient:
    """Async wrapper for the Cronicle REST API."""

    def __init__(
        self,
        host: str,
        port: int,
        api_key: str,
        session: aiohttp.ClientSession,
        use_ssl: bool = False,
        history_limit: int = 5,
    ) -> None:
        scheme = "https" if use_ssl else "http"
        self._base = f"{scheme}://{host}:{port}/api/app"
        self._headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        self._session = session
        self._history_limit = max(1, history_limit)

    async def _get(self, endpoint: str) -> dict:
        url = f"{self._base}/{endpoint}/v1"
        try:
            async with self._session.get(
                url, headers=self._headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as r:
                r.raise_for_status()
                data = await r.json()
        except aiohttp.ClientError as e:
            raise CronicleAPIError(f"HTTP error on {endpoint}: {e}") from e
        if data.get("code") != 0:
            raise CronicleAPIError(
                f"Cronicle returned code={data.get('code')} on {endpoint}: "
                f"{data.get('description')}"
            )
        return data

    async def _post(self, endpoint: str, payload: dict) -> dict:
        url = f"{self._base}/{endpoint}/v1"
        try:
            async with self._session.post(
                url,
                headers=self._headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        except aiohttp.ClientError as e:
            raise CronicleAPIError(f"HTTP error on {endpoint}: {e}") from e
        if data.get("code") != 0:
            raise CronicleAPIError(
                f"Cronicle returned code={data.get('code')} on {endpoint}: "
                f"{data.get('description')}"
            )
        return data

    async def fetch_all(self) -> CronicleData:
        """Fetch all data in parallel; populate a CronicleData snapshot."""
        results = await asyncio.gather(
            self._get("get_master_state"),
            self._get("get_active_jobs"),
            self._post("get_schedule", {"offset": 0, "limit": 1000}),
            self._post("get_history", {"offset": 0, "limit": self._history_limit}),
            return_exceptions=True,
        )

        data = CronicleData()

        # ── Master state ─────────────────────────────────────────────────────
        if isinstance(results[0], dict):
            data.scheduler_enabled = bool(
                results[0].get("state", {}).get("enabled", 0)
            )
        elif isinstance(results[0], Exception):
            _LOGGER.warning("get_master_state failed: %s", results[0])

        # ── Active jobs ──────────────────────────────────────────────────────
        if isinstance(results[1], dict):
            jobs_raw = results[1].get("jobs", {})
            data.active_jobs = [_parse_active_job(j) for j in jobs_raw.values()]
        elif isinstance(results[1], Exception):
            _LOGGER.warning("get_active_jobs failed: %s", results[1])

        # ── Schedule ─────────────────────────────────────────────────────────
        if isinstance(results[2], dict):
            rows = results[2].get("rows", [])
            data.total_events = results[2].get("list", {}).get("length", len(rows))
            data.enabled_events = sum(1 for e in rows if e.get("enabled"))
        elif isinstance(results[2], Exception):
            _LOGGER.warning("get_schedule failed: %s", results[2])

        # ── History ──────────────────────────────────────────────────────────
        if isinstance(results[3], dict):
            rows = results[3].get("rows", [])
            data.recent_jobs = [_parse_completed_job(r) for r in rows]
            _LOGGER.debug(
                "Fetched %d history row(s); first time_end=%s, time_start=%s, elapsed=%s",
                len(rows),
                rows[0].get("time_end") if rows else None,
                rows[0].get("time_start") if rows else None,
                rows[0].get("elapsed") if rows else None,
            )
        elif isinstance(results[3], Exception):
            _LOGGER.warning("get_history failed: %s", results[3])

        return data

    async def test_connection(self) -> None:
        await self._get("get_master_state")


def _parse_active_job(raw: dict) -> ActiveJob:
    cpu_obj = raw.get("cpu") or {}
    mem_obj = raw.get("mem") or {}
    return ActiveJob(
        id=raw.get("id", ""),
        event=raw.get("event", ""),
        title=raw.get("event_title", raw.get("id", "Unknown")),
        source=raw.get("source", ""),
        elapsed=_to_float(raw.get("elapsed")),
        progress=_to_float(raw.get("progress")),
        hostname=raw.get("hostname", ""),
        nice_target=raw.get("nice_target") or raw.get("target", ""),
        category=raw.get("category_title") or raw.get("category", ""),
        plugin=raw.get("plugin_title") or raw.get("plugin", ""),
        time_start=_to_float(raw.get("time_start")),
        timeout=int(raw.get("timeout") or 0),
        pid=raw.get("pid"),
        cpu_current=_to_float(cpu_obj.get("current")),
        mem_current=int(mem_obj.get("current") or 0),
    )


def _parse_completed_job(raw: dict) -> CompletedJob:
    return CompletedJob(
        id=raw.get("id", ""),
        event=raw.get("event", ""),
        title=raw.get("event_title", raw.get("title", "Unknown")),
        code=int(raw.get("code") or 0),
        elapsed=_to_float(raw.get("elapsed")),
        hostname=raw.get("hostname", ""),
        category=raw.get("category_title") or raw.get("category", ""),
        plugin=raw.get("plugin_title") or raw.get("plugin", ""),
        source=raw.get("source", ""),
        description=raw.get("description", ""),
        time_start=_to_float(raw.get("time_start")),
        time_end=_to_float(raw.get("time_end")),
    )


def _to_float(v) -> float:
    """Defensive float conversion — Cronicle sometimes returns strings."""
    if v is None or v == "":
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0
