# build_win.ps1 - Professional Build Script for InfiChat
# This script handles the "Symbolic Link" and Permission errors during Windows build

$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Refining Build Environment: Requesting Administrator Privileges..." -ForegroundColor Cyan
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host "----------------------------------------------------" -ForegroundColor Green
Write-Host "   InfiChat Windows Build - Professional Mode" -ForegroundColor Green
Write-Host "----------------------------------------------------" -ForegroundColor Green

# 1. Clear Cache to resolve "Symbolic Link" issues
Write-Host "`n[1/4] Clearing Electron Builder Cache..." -ForegroundColor Yellow
$cachePath = "$env:LOCALAPPDATA\electron-builder-cache"
if (Test-Path $cachePath) {
    Remove-Item -Path $cachePath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Cache cleared successfully." -ForegroundColor Gray
}

# 2. Clear dist and dist_electron
Write-Host "[2/4] Cleaning previous build artifacts..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Path "dist" -Recurse -Force }
if (Test-Path "dist_electron") { Remove-Item -Path "dist_electron" -Recurse -Force }

# 3. Install Dependencies (ensures everything is correct)
Write-Host "[3/4] Verifying dependencies..." -ForegroundColor Yellow
npm install

# 4. Run Build
Write-Host "[4/4] Starting Production Build..." -ForegroundColor Green
npm run build:win

Write-Host "`nBuild Process Completed!" -ForegroundColor Green
Write-Host "You can find your .exe in: frontend\dist_electron" -ForegroundColor Gray
Pause
