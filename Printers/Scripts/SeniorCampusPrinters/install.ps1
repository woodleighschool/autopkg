$ErrorActionPreference = "Stop"

$PrintServer = "sc-printserver"
$PrintQueue  = "SCPQ"
$PortName    = "LPR_${PrintServer}_${PrintQueue}"
$PrinterName = "Senior Campus"
$DriverName  = "EPSON AM-C6000 Series PCL6"

# Driver must already be installed by the driver package/app.
if (-not (Get-PrinterDriver -Name $DriverName -ErrorAction SilentlyContinue)) {
    throw "Driver installation prerequisite missing: $DriverName"
}

# LPR Port Monitor is required for Add-PrinterPort -LprHostAddress.
# It is a Windows Optional Feature, disabled by default on Windows 11.
$lprFeature = Get-WindowsOptionalFeature -Online -FeatureName "LPRMonitor" -ErrorAction SilentlyContinue
if ($lprFeature -and $lprFeature.State -ne "Enabled") {
    Enable-WindowsOptionalFeature -Online -FeatureName "LPRMonitor" -NoRestart | Out-Null
}

# Create the LPR TCP/IP port if missing.
if (-not (Get-PrinterPort -Name $PortName -ErrorAction SilentlyContinue)) {
    Add-PrinterPort `
        -Name $PortName `
        -LprHostAddress $PrintServer `
        -LprQueueName $PrintQueue
}

$printer = Get-Printer -Name $PrinterName -ErrorAction SilentlyContinue

if ($printer) {
    if ($printer.DriverName -ne $DriverName -or $printer.PortName -ne $PortName) {
        Remove-Printer -Name $PrinterName
        $printer = $null
    }
}

if (-not $printer) {
    Add-Printer `
        -Name $PrinterName `
        -DriverName $DriverName `
        -PortName $PortName
}
