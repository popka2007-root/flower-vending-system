param(
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Continue"

function New-DirectoryIfMissing {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Write-Text {
    param(
        [string]$Path,
        [string[]]$Lines
    )
    $Lines | Out-File -FilePath $Path -Encoding UTF8
}

function Export-WmiCsv {
    param(
        [string]$ClassName,
        [string]$Path,
        [string[]]$Properties
    )
    try {
        Get-WmiObject -Class $ClassName |
            Select-Object -Property $Properties |
            Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    } catch {
        Write-Text -Path ($Path + ".error.txt") -Lines @($_.Exception.Message)
    }
}

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    $OutputDir = Join-Path (Join-Path $scriptRoot "..") "artifacts\hardware-inventory-windows"
}

New-DirectoryIfMissing -Path $OutputDir

$summary = @()
$summary += "CollectedAt=$((Get-Date).ToString('s'))"
$summary += "ComputerName=$env:COMPUTERNAME"
$summary += "UserName=$env:USERNAME"
$summary += "OS=$((Get-WmiObject Win32_OperatingSystem | Select-Object -ExpandProperty Caption))"
$summary += "OSVersion=$((Get-WmiObject Win32_OperatingSystem | Select-Object -ExpandProperty Version))"
$summary += "Architecture=$((Get-WmiObject Win32_OperatingSystem | Select-Object -ExpandProperty OSArchitecture))"
$summary += "Manufacturer=$((Get-WmiObject Win32_ComputerSystem | Select-Object -ExpandProperty Manufacturer))"
$summary += "Model=$((Get-WmiObject Win32_ComputerSystem | Select-Object -ExpandProperty Model))"
$summary += "TotalPhysicalMemory=$((Get-WmiObject Win32_ComputerSystem | Select-Object -ExpandProperty TotalPhysicalMemory))"
$summary += "Processor=$((Get-WmiObject Win32_Processor | Select-Object -First 1 -ExpandProperty Name))"
Write-Text -Path (Join-Path $OutputDir "system-summary.txt") -Lines $summary

Export-WmiCsv -ClassName Win32_OperatingSystem -Path (Join-Path $OutputDir "operating-system.csv") -Properties @(
    "Caption", "Version", "BuildNumber", "OSArchitecture", "InstallDate", "LastBootUpTime"
)
Export-WmiCsv -ClassName Win32_ComputerSystem -Path (Join-Path $OutputDir "computer-system.csv") -Properties @(
    "Manufacturer", "Model", "SystemType", "TotalPhysicalMemory", "NumberOfProcessors"
)
Export-WmiCsv -ClassName Win32_Processor -Path (Join-Path $OutputDir "processor.csv") -Properties @(
    "Name", "Manufacturer", "NumberOfCores", "NumberOfLogicalProcessors", "MaxClockSpeed", "AddressWidth"
)
Export-WmiCsv -ClassName Win32_BIOS -Path (Join-Path $OutputDir "bios.csv") -Properties @(
    "Manufacturer", "Name", "SMBIOSBIOSVersion", "SerialNumber", "ReleaseDate"
)
Export-WmiCsv -ClassName Win32_SerialPort -Path (Join-Path $OutputDir "serial-ports.csv") -Properties @(
    "DeviceID", "Name", "Description", "PNPDeviceID", "ProviderType", "MaxBaudRate", "Status"
)
Export-WmiCsv -ClassName Win32_PnPEntity -Path (Join-Path $OutputDir "pnp-devices.csv") -Properties @(
    "Name", "DeviceID", "Manufacturer", "Service", "PNPClass", "ConfigManagerErrorCode", "Status"
)
Export-WmiCsv -ClassName Win32_PointingDevice -Path (Join-Path $OutputDir "pointing-devices.csv") -Properties @(
    "Name", "DeviceID", "Manufacturer", "PNPDeviceID", "Status"
)
Export-WmiCsv -ClassName Win32_DesktopMonitor -Path (Join-Path $OutputDir "monitors.csv") -Properties @(
    "Name", "DeviceID", "PNPDeviceID", "ScreenWidth", "ScreenHeight", "Status"
)
Export-WmiCsv -ClassName Win32_POTSModem -Path (Join-Path $OutputDir "modems.csv") -Properties @(
    "Name", "AttachedTo", "DeviceID", "PNPDeviceID", "Status"
)
Export-WmiCsv -ClassName Win32_Printer -Path (Join-Path $OutputDir "printers.csv") -Properties @(
    "Name", "DriverName", "PortName", "DeviceID", "Default", "WorkOffline", "Status"
)
Export-WmiCsv -ClassName Win32_NetworkAdapterConfiguration -Path (Join-Path $OutputDir "network.csv") -Properties @(
    "Description", "MACAddress", "IPAddress", "DefaultIPGateway", "DNSServerSearchOrder", "DHCPEnabled"
)

cmd.exe /c "reg query HKLM\HARDWARE\DEVICEMAP\SERIALCOMM" > (Join-Path $OutputDir "registry-serialcomm.txt") 2>&1
cmd.exe /c "mode" > (Join-Path $OutputDir "mode.txt") 2>&1
cmd.exe /c "driverquery /v /fo csv" > (Join-Path $OutputDir "driverquery.csv") 2>&1

$setupApi = Join-Path $env:WINDIR "inf\setupapi.dev.log"
if (Test-Path -LiteralPath $setupApi) {
    Select-String -Path $setupApi -Pattern "JCM", "DBV", "ID-003", "COM[0-9]", "PortName", "MosChip", "MCS", "WCH", "CH38", "GeneralTouch", "SAW", "VID_0DFC", "VID_0DF9", "VID_12D1", "Custom Engineering" |
        Select-Object LineNumber, Line |
        Format-List |
        Out-File -FilePath (Join-Path $OutputDir "setupapi-relevant-lines.txt") -Encoding UTF8
}

Write-Host "Hardware inventory written to $OutputDir"
