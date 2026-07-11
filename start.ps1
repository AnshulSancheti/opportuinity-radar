# Opportunity Radar — Windows start (see README for Linux: ./start.sh)
# Usage: .\start.ps1   |   .\start.ps1 -Stop   |   .\start.ps1 -Help

param([switch]$Stop, [switch]$Help)

$Root = $PSScriptRoot
Set-Location $Root

function Show-Help {
  @"
Opportunity Radar — start script (Windows)

  .\start.ps1         Start Postgres + backend (Docker) and frontend (local dev)
  .\start.ps1 -Stop   Stop all services
  .\start.ps1 -Help   Show this help

Scraper controls: http://localhost:3000/admin
"@
}

if ($Help) { Show-Help; exit 0 }

$StateDir = Join-Path $Root ".radar"
$FrontendDir = Join-Path $Root "frontend"
$FrontendEnv = Join-Path $FrontendDir ".env.local"

function Write-Step($m) { Write-Host "`n>> $m" -ForegroundColor Cyan }
function Write-Ok($m)   { Write-Host "   OK: $m" -ForegroundColor Green }
function Write-Err($m)  { Write-Host "   ERROR: $m" -ForegroundColor Red; exit 1 }

if ($Stop) {
  Write-Step "Stopping services"
  $pidFile = Join-Path $StateDir "frontend.pid"
  if (Test-Path $pidFile) {
    $fpid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($fpid) { Stop-Process -Id $fpid -Force -ErrorAction SilentlyContinue }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
  }
  docker compose --profile full down 2>$null
  docker compose down
  Write-Ok "Stopped"
  exit 0
}

Write-Host "`n  OPPORTUNITY RADAR`n" -ForegroundColor Red

if (-not (Test-Path "$Root\.env")) {
  Copy-Item "$Root\.env.example" "$Root\.env"
  Write-Ok "Created .env from .env.example"
}
if (Select-String -Path "$Root\.env" -Pattern '^NEXT_PUBLIC_API_URL=' -Quiet) {
  Select-String -Path "$Root\.env" -Pattern '^NEXT_PUBLIC_API_URL=' | ForEach-Object { $_.Line } | Set-Content $FrontendEnv
} elseif (-not (Test-Path $FrontendEnv)) {
  Set-Content $FrontendEnv 'NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1'
}

docker info 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Err "Docker daemon not running" }

Write-Step "Starting Postgres + backend"
docker compose up -d --build postgres backend
if ($LASTEXITCODE -ne 0) { Write-Err "docker compose failed" }
Write-Ok "Docker services up"

$url = "http://localhost:8000/api/v1/health"
Write-Step "Waiting for backend"
$ready = $false
for ($i = 0; $i -lt 45; $i++) {
  try {
    Invoke-RestMethod $url -TimeoutSec 3 | Out-Null
    $ready = $true
    break
  } catch { Start-Sleep -Seconds 2 }
}
if (-not $ready) { Write-Err "Backend not healthy — check: docker compose logs backend" }
Write-Ok "Backend healthy"

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  Write-Err "Node.js/npm not found"
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
  Write-Step "Installing frontend dependencies"
  Push-Location $FrontendDir; npm install; Pop-Location
}

$port = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port) {
  try {
    Invoke-WebRequest "http://localhost:3000" -TimeoutSec 3 | Out-Null
    Write-Ok "Frontend already on http://localhost:3000"
  } catch {
    Write-Err "Port 3000 in use but not responding"
  }
} else {
  Write-Step "Starting frontend in new window"
  New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
  $cmd = "Set-Location '$FrontendDir'; npm run dev"
  Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd
  Write-Ok "Frontend starting → http://localhost:3000"
}

Write-Host "`n  Dashboard : http://localhost:3000"
Write-Host "  API docs  : http://localhost:8000/docs"
Write-Host "  Control   : http://localhost:3000/admin"
Write-Host "  Stop      : .\start.ps1 -Stop`n"
