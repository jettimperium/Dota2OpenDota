$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$candidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe")
)
$iscc = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    $command = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($command) { $iscc = $command.Source }
}
if (-not $iscc) {
    throw "Inno Setup 6 не найден. Установите его с https://jrsoftware.org/isdl.php и повторите запуск."
}

if (-not (Test-Path "dist\Dota2Pulse.exe")) {
    & (Join-Path $PSScriptRoot "build.ps1")
}

New-Item -ItemType Directory -Force -Path "dist\installer" | Out-Null
& $iscc "installer.iss"
Write-Host ""
Write-Host "Готово: $PSScriptRoot\dist\installer\Dota2Pulse-Setup-1.2.1.exe"
