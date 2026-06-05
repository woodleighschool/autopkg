$ErrorActionPreference = "SilentlyContinue"

$PrinterName = "Senior Campus"
$PortName = "LPR_sc-printserver.woodleighschool.net_SCPQ"
$LogDir = "C:\ProgramData\Woodleigh\Logs"
$LogPath = Join-Path $LogDir "printer-senior_campus-uninstall.log"

New-Item -Path $LogDir -ItemType Directory -Force | Out-Null
Start-Transcript -Path $LogPath -Append

Remove-Printer -Name $PrinterName

$StillUsed = Get-Printer | Where-Object { $_.PortName -eq $PortName }
if (-not $StillUsed) {
    Remove-PrinterPort -Name $PortName
}

Stop-Transcript
