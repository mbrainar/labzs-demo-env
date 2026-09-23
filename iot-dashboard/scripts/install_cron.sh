#!/usr/bin/env bash
# Installs (or replaces) a cron job that runs checkin.sh on a recurring interval.
#
# Usage:
#   ./install_cron.sh <api-url> [interval-minutes] [api-key]
#
# Example:
#   ./install_cron.sh http://iot-dashboard.labzs.com/api/checkin 5
#
# Installs into the current user's crontab. Re-running replaces the previous
# entry rather than adding a duplicate. Output is sent to syslog under the
# tag "iot-checkin" (view with: journalctl -t iot-checkin  or  grep iot-checkin /var/log/syslog).
# Remove the job with: ./install_cron.sh --remove

set -euo pipefail

MARKER="# iot-dashboard-checkin"

current_crontab() {
    crontab -l 2>/dev/null | grep -vF "$MARKER" || true
}

if [[ "${1:-}" == "--remove" ]]; then
    current_crontab | crontab -
    echo "Removed iot-dashboard check-in cron job."
    exit 0
fi

API_URL="${1:-}"
INTERVAL="${2:-5}"
API_KEY="${3:-}"

if [[ -z "$API_URL" ]]; then
    echo "Usage: $0 <api-url> [interval-minutes] [api-key]" >&2
    echo "       $0 --remove" >&2
    exit 2
fi

if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]] || (( INTERVAL < 1 || INTERVAL > 59 )); then
    echo "Interval must be a whole number of minutes between 1 and 59." >&2
    exit 2
fi

if ! command -v curl >/dev/null 2>&1; then
    echo "curl is required but not installed (sudo apt-get install -y curl)." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECKIN="$SCRIPT_DIR/checkin.sh"

if [[ ! -f "$CHECKIN" ]]; then
    echo "Could not find checkin.sh next to this script at: $CHECKIN" >&2
    exit 1
fi

# Invoked via `bash` so the entry works even if the exec bit was lost.
CMD="/bin/bash \"$CHECKIN\" \"$API_URL\""
[[ -n "$API_KEY" ]] && CMD+=" \"$API_KEY\""

ENTRY="*/$INTERVAL * * * * $CMD 2>&1 | logger -t iot-checkin $MARKER"

{ current_crontab; echo "$ENTRY"; } | crontab -

echo "Cron job installed: checking in every $INTERVAL minute(s) to $API_URL"
echo "Run one check-in now to test:  bash \"$CHECKIN\" \"$API_URL\""
echo "View logs with:                journalctl -t iot-checkin -n 20   (or grep iot-checkin /var/log/syslog)"
