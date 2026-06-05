$PrinterName = "Senior Campus"

if (Get-Printer -Name $PrinterName -ErrorAction SilentlyContinue) {
    exit 0
}

exit 1
