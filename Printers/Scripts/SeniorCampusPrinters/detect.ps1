$PrinterName = "Senior Campus"
$DriverName  = "EPSON AM-C6000 Series PCL6"
$PortName    = "LPR_sc-printserver_SCPQ"

$printer = Get-Printer -Name $PrinterName -ErrorAction SilentlyContinue

if (
    $printer -and
    $printer.DriverName -eq $DriverName -and
    $printer.PortName -eq $PortName
) {
    Write-Output "Detected: $PrinterName"
    exit 0
}

exit 1
