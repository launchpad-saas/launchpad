Set-Location (Join-Path $PSScriptRoot "..")

# Bootstrap .env from .env.example if missing
$envMap = @(
    @{ Src = ".env.example";                        Dst = ".env" },
    @{ Src = "backend/admin_api/.env.example";      Dst = "backend/admin_api/.env" },
    @{ Src = "backend/auth_api/.env.example";       Dst = "backend/auth_api/.env" },
    @{ Src = "backend/catalog_api/.env.example";    Dst = "backend/catalog_api/.env" },
    @{ Src = "backend/orders_api/.env.example";     Dst = "backend/orders_api/.env" }
)

foreach ($m in $envMap) {
    if (-not (Test-Path $m.Dst) -and (Test-Path $m.Src)) {
        Copy-Item $m.Src $m.Dst
        Write-Host "  [OK] $($m.Dst) (from $($m.Src))" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Starting stack..." -ForegroundColor Cyan
docker compose up -d --build

Write-Host ""
Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

docker compose ps

Write-Host ""
Write-Host "Health endpoints:" -ForegroundColor Cyan
Write-Host "  http://localhost:8000/api/v1/health  (admin_api)"
Write-Host "  http://localhost:8001/api/v1/health  (auth_api)"
Write-Host "  http://localhost:8002/api/v1/health  (catalog_api)"
Write-Host "  http://localhost:8003/api/v1/health  (orders_api)"