$ErrorActionPreference = "Stop"

$QueueName = "senior_campus"
$DisplayName = "Senior Campus"
$Location = "Senior Campus"

$PrintServer = "sc-printserver.woodleighschool.net"
$PrintQueue = "SCPQ"

$PortName = "LPR_${PrintServer}_${PrintQueue}"
$DriverName = "EPSON AM-C6000 Series PCL6"

$LogDir = "C:\ProgramData\Woodleigh\Logs"
$LogPath = Join-Path $LogDir "printer-$QueueName.log"

New-Item -Path $LogDir -ItemType Directory -Force | Out-Null
Start-Transcript -Path $LogPath -Append

try {
    if (-not (Get-PrinterDriver -Name $DriverName -ErrorAction SilentlyContinue)) {
        throw "Required printer driver is missing: $DriverName"
    }

    Enable-WindowsOptionalFeature `
        -Online `
        -FeatureName "Printing-Foundation-LPRPortMonitor" `
        -NoRestart `
        -All | Out-Null

    if (-not (Get-PrinterPort -Name $PortName -ErrorAction SilentlyContinue)) {
        Add-PrinterPort `
            -Name $PortName `
            -LprHostAddress $PrintServer `
            -LprQueueName $PrintQueue
    }

    if (-not (Get-Printer -Name $DisplayName -ErrorAction SilentlyContinue)) {
        Add-Printer `
            -Name $DisplayName `
            -DriverName $DriverName `
            -PortName $PortName
    }

    Set-Printer `
        -Name $DisplayName `
        -Location $Location `
        -Comment $Location
}
finally {
    Stop-Transcript
}
