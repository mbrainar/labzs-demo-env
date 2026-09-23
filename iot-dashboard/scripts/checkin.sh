#!/usr/bin/env bash
# Sends a status check-in (hostname, IP address, local time) to the IoT
# Device Status Dashboard API.
#
# Usage:
#   checkin.sh <api-url> [api-key]
#
# Example:
#   ./checkin.sh http://iot-dashboard.labzs.com/api/checkin
#   ./checkin.sh http://iot-dashboard.labzs.com/api/checkin s3cr3t
#
# The API key can also be supplied via the IOT_API_KEY environment variable.

set -euo pipefail

API_URL="${1:-}"
API_KEY="${2:-${IOT_API_KEY:-}}"

if [[ -z "$API_URL" ]]; then
    echo "Usage: $0 <api-url> [api-key]" >&2
    exit 2
fi

get_primary_ipv4() {
    local ip=""
    # Source address the kernel would use to reach the internet (follows the default route).
    if command -v ip >/dev/null 2>&1; then
        ip=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i=1;i<=NF;i++) if ($i=="src") {print $(i+1); exit}}')
    fi
    # Fallback: first non-loopback address reported by hostname -I.
    if [[ -z "$ip" ]] && command -v hostname >/dev/null 2>&1; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    echo "${ip:-unknown}"
}

HOSTNAME_VALUE=$(hostname)
IP_ADDRESS=$(get_primary_ipv4)
DEVICE_TIME=$(date --iso-8601=seconds)   # e.g. 2026-09-19T14:32:10-04:00

BODY=$(printf '{"hostname":"%s","ip_address":"%s","device_time":"%s"}' \
    "$HOSTNAME_VALUE" "$IP_ADDRESS" "$DEVICE_TIME")

CURL_ARGS=(-fsS --max-time 15 -X POST "$API_URL" -H "Content-Type: application/json" -d "$BODY")
if [[ -n "$API_KEY" ]]; then
    CURL_ARGS+=(-H "X-API-Key: $API_KEY")
fi

if curl "${CURL_ARGS[@]}" >/dev/null; then
    echo "Check-in OK: $HOSTNAME_VALUE / $IP_ADDRESS / $DEVICE_TIME"
else
    echo "Check-in FAILED: $HOSTNAME_VALUE / $IP_ADDRESS / $DEVICE_TIME" >&2
    exit 1
fi
