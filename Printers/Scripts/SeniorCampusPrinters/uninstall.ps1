$ErrorActionPreference = "Stop"

$PrintServer = "sc-printserver"
$PrintQueue = "SCPQ"
$PortName = "LPR_${PrintServer}_${PrintQueue}"
$PrinterName = "Senior Campus"

if (Get-Printer -Name $PrinterName -ErrorAction SilentlyContinue) {
    Remove-Printer -Name $PrinterName
}

if (Get-PrinterPort -Name $PortName -ErrorAction SilentlyContinue) {
    $stillUsed = Get-Printer | Where-Object { $_.PortName -eq $PortName }
    if (-not $stillUsed) {
        Remove-PrinterPort -Name $PortName
    }
}
