<#
.SYNOPSIS
    Sends a status check-in (hostname, IP address, local time) to the IoT
    Device Status Dashboard API.

.PARAMETER ApiUrl
    Full URL of the check-in endpoint, e.g. http://dashboard-host:8080/api/checkin

.PARAMETER ApiKey
    Optional shared secret. Only needed if the server was started with API_KEY set.
    Sent as the X-API-Key header.

.EXAMPLE
    .\checkin.ps1 -ApiUrl "http://192.168.1.50:8080/api/checkin"

.EXAMPLE
    .\checkin.ps1 -ApiUrl "http://192.168.1.50:8080/api/checkin" -ApiKey "s3cr3t"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$ApiUrl,

    [string]$ApiKey = ""
)

$ErrorActionPreference = "Stop"

function Get-PrimaryIPv4Address {
    # Prefer the address on the interface that owns the default route.
    $route = Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue |
        Sort-Object -Property RouteMetric |
        Select-Object -First 1

    if ($route) {
        $ip = Get-NetIPAddress -InterfaceIndex $route.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Where-Object { $_.IPAddress -notlike "169.254.*" } |
            Select-Object -First 1
        if ($ip) { return $ip.IPAddress }
    }

    # Fallback: first non-loopback, non-link-local IPv4 address on any adapter.
    $fallback = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object {
            $_.IPAddress -notlike "127.*" -and
            $_.IPAddress -notlike "169.254.*"
        } |
        Select-Object -First 1

    if ($fallback) { return $fallback.IPAddress }
    return "unknown"
}

$hostname = $env:COMPUTERNAME
$ipAddress = Get-PrimaryIPv4Address
$deviceTime = (Get-Date).ToString("o")  # ISO 8601, includes local UTC offset

$body = @{
    hostname     = $hostname
    ip_address   = $ipAddress
    device_time  = $deviceTime
} | ConvertTo-Json

$headers = @{ "Content-Type" = "application/json" }
if ($ApiKey) { $headers["X-API-Key"] = $ApiKey }

try {
    $response = Invoke-RestMethod -Uri $ApiUrl -Method Post -Headers $headers -Body $body -TimeoutSec 15
    Write-Output "Check-in OK: $hostname / $ipAddress / $deviceTime"
} catch {
    Write-Error "Check-in FAILED: $($_.Exception.Message)"
    exit 1
}
