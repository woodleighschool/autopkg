$DriverName = "EPSON AM-C6000 Series PCL6"

if (Get-PrinterDriver -Name $DriverName -ErrorAction SilentlyContinue) {
    exit 0
}

exit 1
