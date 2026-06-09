$ErrorActionPreference = "Stop"

$ConnectionName = "\\SC-PRINTSERVER\SCPQ"

$existing = Get-Printer | Where-Object { $_.PortName -eq $ConnectionName } | Select-Object -First 1

if ($existing) {
    Remove-Printer -Name $existing.Name
}
