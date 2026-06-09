$ConnectionName = "\\SC-PRINTSERVER\SCPQ"

$existing = Get-Printer | Where-Object { $_.PortName -eq $ConnectionName } | Select-Object -First 1

if ($existing) {
    Write-Output "Detected: $($existing.Name)"
    exit 0
}

exit 1
