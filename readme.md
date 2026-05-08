# Cronicle for Home Assistant

A custom Home Assistant integration for monitoring a local [Cronicle](https://github.com/jhuckaby/Cronicle) job scheduler instance.

This integration connects to the Cronicle REST API and exposes scheduler state, active jobs, schedule counts, and recent job history as Home Assistant entities.

## Features

- Configurable through the Home Assistant UI
- Supports HTTP and HTTPS
- Local polling integration
- Configurable poll interval
- Configurable number of recent jobs to keep
- Device page with direct link back to the Cronicle web UI
- Sensors for active jobs, scheduled events, and recent job history
- Binary sensors for scheduler status and last job failure state

## Requirements

- Home Assistant
- A reachable Cronicle instance
- Cronicle API key
- Network access from Home Assistant to Cronicle

Default Cronicle port is `3012`.

## Installation

Copy the integration folder into your Home Assistant `custom_components` directory:

```text
config/custom_components/cronicle/
````

Expected structure:

```text
custom_components/cronicle/
├── __init__.py
├── api.py
├── binary_sensor.py
├── config_flow.py
├── const.py
├── coordinator.py
├── manifest.json
├── sensor.py
├── strings.json
└── translations/
    └── en.json
```

Restart Home Assistant after copying the files.

## Setup

1.  Go to **Settings → Devices & services**
2.  Click **Add integration**
3.  Search for **Cronicle**
4.  Enter:
    *   **Host**
    *   **Port**
    *   **API Key**
    *   **Use HTTPS**
    *   **Poll interval**
    *   **Recent jobs count**
5.  Submit the form

The integration validates the connection during setup by calling Cronicle's `get_master_state` endpoint.

## Configuration Options

After setup, the following options can be changed from the integration options menu:

| Option            |      Default |     Range | Description                                 |
| ----------------- | -----------: | --------: | ------------------------------------------- |
| Poll interval     | `30` seconds | `10–3600` | How often Home Assistant polls Cronicle     |
| Recent jobs count |          `5` |    `1–25` | Number of completed jobs kept in attributes |

## Entities

### Sensors

| Entity                              | Description                                 |
| ----------------------------------- | ------------------------------------------- |
| `sensor.cronicle_active_jobs`       | Number of currently running jobs            |
| `sensor.cronicle_total_events`      | Total number of scheduled events            |
| `sensor.cronicle_enabled_events`    | Number of enabled scheduled events          |
| `sensor.cronicle_last_job`          | Title of the most recent completed job      |
| `sensor.cronicle_last_job_code`     | Exit code of the most recent completed job  |
| `sensor.cronicle_last_job_duration` | Runtime of the most recent completed job    |
| `sensor.cronicle_last_job_finished` | Timestamp when the most recent job finished |
| `sensor.cronicle_recent_jobs`       | Number of recent jobs returned by Cronicle  |

### Binary Sensors

| Entity                                   | Description                                  |
| ---------------------------------------- | -------------------------------------------- |
| `binary_sensor.cronicle_scheduler`       | Whether the Cronicle scheduler is enabled    |
| `binary_sensor.cronicle_last_job_failed` | Whether the most recent completed job failed |

## Attributes

Some entities include additional job details as attributes.

### Active Jobs

`sensor.cronicle_active_jobs` includes a `jobs` attribute with details such as:

*   Job ID
*   Event ID
*   Title
*   Source
*   Runtime
*   Progress
*   Hostname
*   Target
*   Category
*   Plugin
*   CPU usage
*   Memory usage

### Recent Jobs

`sensor.cronicle_recent_jobs` includes a `jobs` attribute with details such as:

*   Job ID
*   Event ID
*   Title
*   Exit code
*   Success state
*   Runtime
*   Hostname
*   Category
*   Plugin
*   Source
*   Description
*   Start time
*   End time
*   Finished timestamp

### Last Job

`sensor.cronicle_last_job` includes attributes for the most recent completed job, including job ID, event, exit code, runtime, host, category, plugin, source, description, and timestamps.

## API Endpoints Used

The integration uses the following Cronicle API endpoints:

*   `get_master_state`
*   `get_active_jobs`
*   `get_schedule`
*   `get_history`

Connection testing uses `get_master_state`.

## Troubleshooting

### Cannot connect during setup

Check that:

*   The host is reachable from Home Assistant
*   The port is correct
*   The API key is valid
*   HTTPS is only enabled if Cronicle is actually served over HTTPS
*   Firewalls or reverse proxies are not blocking Home Assistant

### Entities are unavailable

Check the Home Assistant logs for Cronicle API errors. The integration raises update failures when the API client cannot complete a refresh.

### No recent job data

Cronicle must have completed job history available. If no history rows are returned, last job sensors may be empty.

## Notes

*   This integration uses local polling.
*   No external Python requirements are needed.
*   The integration stores API data in a Home Assistant `DataUpdateCoordinator`.
*   Partial API failures are logged and the integration returns the data that could still be collected.

## License

This project is licensed under the MIT License.
