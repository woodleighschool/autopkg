$DriverName = "EPSON AM-C6000 Series PCL6"

if (-not [Environment]::Is64BitProcess) {
    $PowerShell64 = Join-Path $env:WINDIR "SysNative\WindowsPowerShell\v1.0\powershell.exe"
    if (Test-Path -LiteralPath $PowerShell64) {
        & $PowerShell64 -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath
        exit $LASTEXITCODE
    }
}

if (Get-PrinterDriver -Name $DriverName -ErrorAction SilentlyContinue) {
    Write-Output "Detected: $DriverName"
    exit 0
}

exit 1
