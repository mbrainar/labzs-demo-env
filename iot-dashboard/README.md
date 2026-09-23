# IoT Device Status Dashboard

Flask + SQLite app that receives status check-ins from Windows machines and
displays them on a web dashboard.

## What's included

- `app/` — Flask application (API + dashboard UI)
- `Dockerfile`, `docker-compose.yml` — containerized deployment
- `scripts/checkin.ps1` — run on each Windows "device", POSTs hostname/IP/time to the API
- `scripts/register_task.ps1` — registers a Windows Scheduled Task that runs `checkin.ps1` on a timer
- `scripts/checkin.sh`, `scripts/install_cron.sh` — Linux equivalents: check-in script and a cron installer

## 1. Run the server

This stack expects an existing external Docker network that your Traefik
instance is also attached to, named `proxy`. Create it once if it doesn't
already exist:

```bash
docker network create proxy
```

Then:

```bash
docker compose up -d --build
```

No host ports are published directly — Traefik routes to the container over
the `proxy` network and terminates TLS on port 443 (entrypoint `websecure`)
for `iot-dashboard.labzs.com`, both the dashboard and the `/api/checkin` /
`/api/devices` endpoints. Data persists in the `iot-data` Docker volume
(SQLite file), so it survives container restarts.

Configuration (edit `docker-compose.yml`):

- `API_KEY` — if set, devices must send this value in an `X-API-Key` header on check-in. Leave blank to allow unauthenticated check-ins (fine for a trusted LAN).
- `STALE_AFTER_MINUTES` — a device shows as offline (red dot) if it hasn't checked in within this many minutes. Default 10.
- `MAX_CHECKINS_PER_DEVICE` — only the newest N check-ins are kept for each device (default 300). Older rows are deleted whenever that device checks in, so an existing database is trimmed the next time each device reports.
- Traefik `labels` — update the `Host()` rule, `entrypoints`, and `traefik.docker.network` if your Traefik setup uses different values than `iot-dashboard.labzs.com` / `web` / `proxy`.

## 2. Point Windows devices at it

Copy the `scripts/` folder to each Windows machine (or a shared location),
then from an **elevated** PowerShell prompt:

```powershell
.\register_task.ps1 -ApiUrl "https://iot-dashboard.labzs.com/api/checkin" -IntervalMinutes 5
```

Add `-ApiKey "yourkey"` if you set `API_KEY` on the server. This registers a
Scheduled Task (running as SYSTEM) that checks in every 5 minutes, starting
immediately and continuing across reboots.

Run a one-off check-in manually to test it first:

```powershell
.\checkin.ps1 -ApiUrl "https://iot-dashboard.labzs.com/api/checkin"
```

### Linux (Ubuntu) devices

Requires `curl` (`sudo apt-get install -y curl`). From the `scripts/` folder:

```bash
./install_cron.sh https://iot-dashboard.labzs.com/api/checkin 5
```

Add a third argument for the API key if you set `API_KEY` on the server
(`./install_cron.sh <url> 5 yourkey`). This adds a cron entry to the current
user's crontab that runs `checkin.sh` every 5 minutes. Re-running it replaces
the existing entry, and `./install_cron.sh --remove` uninstalls it. Output goes
to syslog: `journalctl -t iot-checkin -n 20`.

Test a single check-in first:

```bash
./checkin.sh https://iot-dashboard.labzs.com/api/checkin
```

### Plain curl.exe equivalent

If you'd rather not use the PowerShell script, `curl.exe` ships with Windows 10/11:

```bat
curl.exe -s -X POST "https://iot-dashboard.labzs.com/api/checkin" ^
  -H "Content-Type: application/json" ^
  -d "{\"hostname\":\"%COMPUTERNAME%\",\"ip_address\":\"<fill-in>\",\"device_time\":\"%date% %time%\"}"
```

You still need something to fill in the current IP address and format the
timestamp reliably, which is why `checkin.ps1` is the recommended path — it
handles both and parses cleanly on the server (ISO 8601 timestamps).

## API

`POST /api/checkin`

```json
{
  "hostname": "DESKTOP-ABC123",
  "ip_address": "192.168.1.42",
  "device_time": "2026-09-18T14:32:10-04:00"
}
```

Optional header: `X-API-Key: <key>` (required only if `API_KEY` is set on the server).

Response: `201 Created` with the stored record, or `400`/`401` on error.

`GET /api/devices` — JSON list of each device's latest status (used by the dashboard for live updates).

## Dashboard

- `/` — one row per device: hostname, IP, last check-in (device-reported time), and time since last check-in (computed from server receive time, refreshes live). Click a hostname to see full history.
- `/device/<hostname>` — paginated history of the device's retained check-ins, with an **Actions** menu that uses the device's latest IPv4 address:
  - **RDP** downloads a `.rdp` file (opens in mstsc / Microsoft Remote Desktop).
  - **SSH** opens an `ssh://` link if your OS has a handler registered for it, and also copies `ssh <ip>` to the clipboard as a fallback. Browsers can't launch SSH directly, so on many machines you'll just paste the command into a terminal.
  - **Copy IP address** and **Export history (CSV)** of the retained check-ins.
  - **Clear check-in history** deletes every check-in except the most recent one (so the device stays on the dashboard). Asks for confirmation first.
  - **Delete device** removes the device and all its check-ins. Asks for confirmation first. A device that is still running its check-in job will reappear on its next check-in, so stop the scheduled task/cron job on the device to remove it permanently.

  Note that the dashboard has no login. Anyone who can reach it can use these destructive actions, and `API_KEY` only protects check-ins. The destructive endpoints reject cross-site form posts, but consider restricting access at Traefik (e.g. basic-auth or an IP allowlist middleware) if that matters.

## Local development (without Docker)

```bash
cd app
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set DB_PATH=.\iot-dev.db
python app.py
```

Serves on `http://localhost:5000`.
