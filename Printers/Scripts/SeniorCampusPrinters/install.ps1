$ErrorActionPreference = "Stop"

$ConnectionName = "\\sc-printserver\SCPQ"
$PrinterName    = "Senior Campus"

Add-Printer -ConnectionName $ConnectionName -ErrorAction SilentlyContinue

if (Get-Printer -Name $PrinterName -ErrorAction SilentlyContinue) {
    exit 0
}

$printer = Get-Printer -Name $ConnectionName -ErrorAction SilentlyContinue

if ($printer) {
    Rename-Printer -Name $ConnectionName -NewName $PrinterName
}

exit 0