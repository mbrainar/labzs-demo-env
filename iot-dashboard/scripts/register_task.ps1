<#
.SYNOPSIS
    Registers a Windows Scheduled Task that runs checkin.ps1 on a recurring
    interval to report this machine's status to the IoT dashboard.

.PARAMETER ApiUrl
    Full URL of the check-in endpoint, e.g. http://dashboard-host:8080/api/checkin

.PARAMETER ApiKey
    Optional shared secret, if the server requires one.

.PARAMETER IntervalMinutes
    How often to check in. Default: 5 minutes.

.PARAMETER TaskName
    Name of the scheduled task. Default: IoTDashboardCheckin.

.EXAMPLE
    .\register_task.ps1 -ApiUrl "http://192.168.1.50:8080/api/checkin" -IntervalMinutes 5

    Run this from an elevated (Administrator) PowerShell prompt.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$ApiUrl,

    [string]$ApiKey = "",

    [int]$IntervalMinutes = 5,

    [string]$TaskName = "IoTDashboardCheckin"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$checkinScript = Join-Path $scriptDir "checkin.ps1"

if (-not (Test-Path $checkinScript)) {
    throw "Could not find checkin.ps1 next to this script at: $checkinScript"
}

$argumentList = "-NoProfile -ExecutionPolicy Bypass -File `"$checkinScript`" -ApiUrl `"$ApiUrl`""
if ($ApiKey) { $argumentList += " -ApiKey `"$ApiKey`"" }

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argumentList
# Task Scheduler's trigger XML has no "repeat forever" option, and
# [TimeSpan]::MaxValue overflows its duration schema (fails with "task XML
# contains a value which is incorrectly formatted or out of range"). Use a
# long-but-valid duration instead -- effectively indefinite for this purpose.
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 3650)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "Sends periodic status check-ins to the IoT Device Status Dashboard" `
    -Force

Write-Output "Scheduled task '$TaskName' registered. Checking in every $IntervalMinutes minute(s) to $ApiUrl"
Write-Output "Run it once immediately with: Start-ScheduledTask -TaskName `"$TaskName`""
