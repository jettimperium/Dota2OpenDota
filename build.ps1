$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python -m PyInstaller --noconfirm --clean Dota2Pulse.spec

$staging = Join-Path $env:TEMP "Dota2Pulse-Portable"
if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
New-Item -ItemType Directory -Force -Path $staging | Out-Null
Copy-Item "dist\Dota2Pulse.exe" $staging
Copy-Item "README_USER.txt" (Join-Path $staging "README.txt")
Compress-Archive -Path (Join-Path $staging "*") -DestinationPath "dist\Dota2Pulse-Portable-1.2.1.zip" -CompressionLevel Optimal -Force
Remove-Item $staging -Recurse -Force

Write-Host ""
Write-Host "Готово: $PSScriptRoot\dist\Dota2Pulse.exe"
Write-Host "Portable: $PSScriptRoot\dist\Dota2Pulse-Portable-1.2.1.zip"
