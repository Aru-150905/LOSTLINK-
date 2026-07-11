# One-shot local setup for LostLink on Windows (PowerShell).
# Prereqs: Docker Desktop (running), Supabase CLI, Python 3.11+, Node.js 20+.
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\setup_local.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
Write-Host "==> Project root: $Root"

function Require-Cmd($name, $hint) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: '$name' not found. $hint"; exit 1
  }
}
Require-Cmd supabase "Install the Supabase CLI."
Require-Cmd docker   "Install Docker Desktop and start it."
try { docker info | Out-Null } catch { Write-Error "Docker is not running. Start Docker Desktop and retry."; exit 1 }

if (-not (Test-Path "supabase/config.toml")) {
  Write-Host "==> Initializing Supabase project..."
  supabase init
}

# Disable email confirmations so signup logs you straight in.
$cfg = "supabase/config.toml"
if (Test-Path $cfg) {
  (Get-Content $cfg) -replace "enable_confirmations\s*=\s*true", "enable_confirmations = false" | Set-Content $cfg
}

Write-Host "==> Starting local Supabase (first run pulls Docker images)..."
supabase start

Write-Host "==> Applying migrations..."
supabase db reset

Write-Host "==> Writing env files..."
$envLines = supabase status -o env
$vars = @{}
foreach ($line in $envLines) {
  if ($line -match '^\s*([A-Z0-9_]+)\s*=\s*"?([^"]*)"?\s*$') { $vars[$matches[1]] = $matches[2] }
}

$apiUrl  = $vars["API_URL"]
$anon    = $vars["ANON_KEY"]
$service = $vars["SERVICE_ROLE_KEY"]
$jwt     = $vars["JWT_SECRET"]
$studio  = $vars["STUDIO_URL"]

@"
SUPABASE_URL=$apiUrl
SUPABASE_SERVICE_ROLE_KEY=$service
SUPABASE_JWT_SECRET=$jwt
CORS_ORIGINS=http://localhost:3000
RESEND_API_KEY=
EMAIL_FROM=LostLink <noreply@lostlink.app>
WARMUP_MODELS=false
DEBUG=true
"@ | Set-Content backend/.env

@"
NEXT_PUBLIC_SUPABASE_URL=$apiUrl
NEXT_PUBLIC_SUPABASE_ANON_KEY=$anon
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
"@ | Set-Content frontend/.env.local

Write-Host ""
Write-Host "============================================================"
Write-Host " Local Supabase is up. Env files written."
Write-Host ""
Write-Host " Terminal 1 - backend:"
Write-Host "   cd backend; python -m venv venv; venv\Scripts\Activate.ps1;"
Write-Host "   pip install -r requirements.txt; cd ..;"
Write-Host "   uvicorn backend.app.main:app --reload --port 8000"
Write-Host ""
Write-Host " Terminal 2 - frontend:"
Write-Host "   cd frontend; npm install; npm run dev"
Write-Host ""
Write-Host " Open http://localhost:3000"
Write-Host " Supabase Studio: $studio"
Write-Host "============================================================"
