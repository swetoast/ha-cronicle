# Cronicle for Home Assistant

A custom Home Assistant integration for monitoring and controlling a local [Cronicle](https://github.com/jhuckaby/Cronicle) job scheduler instance.

The integration connects to the Cronicle REST API and exposes scheduler state, active jobs, schedule counts, recent job history, diagnostics, buttons, and services.

## Features

- UI-based setup through Home Assistant
- HTTP and HTTPS support
- Local polling
- Configurable poll interval
- Configurable recent job history limit
- Sensors for scheduler/job state
- Diagnostic entities for API health
- Buttons for refresh and scheduler control
- Services for running events, aborting jobs, updating jobs, and scheduler control
- Device page link back to the Cronicle web UI

## Requirements

- Home Assistant
- A reachable Cronicle instance
- Cronicle API key
- Network access from Home Assistant to Cronicle

Default Cronicle port is `3012`.

## Installation

Copy the integration folder into:

```text
config/custom_components/cronicle/
```

Expected structure:

```text
custom_components/cronicle/
├── __init__.py
├── api.py
├── binary_sensor.py
├── button.py
├── config_flow.py
├── const.py
├── coordinator.py
├── manifest.json
├── sensor.py
├── services.yaml
├── strings.json
└── translations/
    └── en.json
```

Restart Home Assistant after copying the files.

## Setup

1. Go to **Settings → Devices & services**
2. Click **Add integration**
3. Search for **Cronicle**
4. Enter the host, port, API key, HTTPS setting, poll interval, and recent jobs count
5. Submit the form

The integration validates the connection by calling Cronicle's master state endpoint.

## Options

| Option | Default | Range | Description |
|---|---:|---:|---|
| Poll interval | `30` seconds | `10–3600` | How often Home Assistant polls Cronicle |
| Recent jobs count | `5` | `1–25` | Number of completed jobs kept in attributes |

## Entities

### Regular sensors

- `sensor.cronicle_active_jobs`
- `sensor.cronicle_total_events`
- `sensor.cronicle_enabled_events`
- `sensor.cronicle_disabled_events`
- `sensor.cronicle_last_job`
- `sensor.cronicle_last_job_code`
- `sensor.cronicle_last_job_duration`
- `sensor.cronicle_last_job_finished`
- `sensor.cronicle_recent_jobs`
- `sensor.cronicle_failed_recent_jobs`
- `sensor.cronicle_success_rate`

### Diagnostic sensors

- `sensor.cronicle_api_status`
- `sensor.cronicle_last_update`
- `sensor.cronicle_last_successful_update`
- `sensor.cronicle_last_error`
- `sensor.cronicle_api_response_time`
- `sensor.cronicle_api_failures`
- `sensor.cronicle_history_total`
- `sensor.cronicle_recent_jobs_limit`

### Binary sensors

- `binary_sensor.cronicle_scheduler`
- `binary_sensor.cronicle_last_job_failed`
- `binary_sensor.cronicle_active_jobs_running`
- `binary_sensor.cronicle_api_connected`
- `binary_sensor.cronicle_problem`

### Buttons

- `button.cronicle_refresh`
- `button.cronicle_enable_scheduler`
- `button.cronicle_disable_scheduler`

## Services

### Run event

```yaml
service: cronicle.run_event
data:
  id: "3c182051"
```

or:

```yaml
service: cronicle.run_event
data:
  title: "Backup Logs"
```

### Abort job

```yaml
service: cronicle.abort_job
data:
  id: "jiinxhh5203"
```

### Update job

```yaml
service: cronicle.update_job
data:
  id: "jiinxhh5203"
  timeout: 300
  retries: 1
```

### Scheduler control

```yaml
service: cronicle.enable_scheduler
```

```yaml
service: cronicle.disable_scheduler
```

### Refresh

```yaml
service: cronicle.refresh
```

If multiple Cronicle instances are configured, add `config_entry_id` to target one instance.

## API Endpoints Used

- `get_master_state`
- `get_active_jobs`
- `get_schedule`
- `get_history`
- `run_event`
- `abort_job`
- `update_job`
- `update_master_state`
- `get_job_status`

## API Key Privileges

Cronicle API key permissions depend on which services you use:

- Read-only monitoring requires access to state, schedule, active jobs, and history endpoints.
- Running events requires the `run_events` privilege.
- Aborting jobs requires the `abort_events` privilege.
- Updating running jobs requires the `edit_events` privilege.
- Enabling or disabling the scheduler requires the `state_update` privilege.

## Troubleshooting

### Cannot connect during setup

Check host, port, API key, HTTPS setting, firewall rules, and reverse proxy configuration.

### Entities are unavailable

Check Home Assistant logs for Cronicle API errors.

### Services fail

Check that the API key has the required Cronicle privilege for the action.

## License

This project is licensed under the MIT License.
