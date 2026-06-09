$ErrorActionPreference = "Stop"

$DriverName = "EPSON AM-C6000 Series PCL6"
$InfPath = Join-Path $PSScriptRoot "Driver\E_JFP6FSE.INF"

# Force 64-bit PowerShell if Intune launches us from a 32-bit process.
if (-not [Environment]::Is64BitProcess) {
    $PowerShell64 = Join-Path $env:WINDIR "SysNative\WindowsPowerShell\v1.0\powershell.exe"
    if (Test-Path -LiteralPath $PowerShell64) {
        & $PowerShell64 -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath
        exit $LASTEXITCODE
    }
}

$LogPath = Join-Path $env:ProgramData "Microsoft\IntuneManagementExtension\Logs\EpsonAM-C6000Driver-install.log"

$ExitCode = 0
Start-Transcript -Path $LogPath -Append | Out-Null

try {
    if (-not (Test-Path -LiteralPath $InfPath)) {
        throw "Missing driver INF: $InfPath"
    }

    if (Get-PrinterDriver -Name $DriverName -ErrorAction SilentlyContinue) {
        Write-Output "Printer driver already installed: $DriverName"
        exit 0
    }

    $PnPUtil = Join-Path $env:WINDIR "System32\pnputil.exe"

    & $PnPUtil /add-driver "$InfPath"
    if ($LASTEXITCODE -ne 0) {
        throw "pnputil failed with exit code $LASTEXITCODE"
    }

    Add-PrinterDriver -Name $DriverName

    if (-not (Get-PrinterDriver -Name $DriverName -ErrorAction SilentlyContinue)) {
        throw "Printer driver was staged but not registered: $DriverName"
    }

    Write-Output "Printer driver installed: $DriverName"
}
catch {
    Write-Error $_
    $ExitCode = 1
}
finally {
    Stop-Transcript | Out-Null
}

exit $ExitCode
