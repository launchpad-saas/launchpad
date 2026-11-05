$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
Write-Host "=== core_api ===" -ForegroundColor Cyan
docker compose run --rm core_api alembic upgrade head
Write-Host "=== catalog_api ===" -ForegroundColor Cyan
docker compose run --rm catalog_api alembic upgrade head
Write-Host "=== orders_api ===" -ForegroundColor Cyan
docker compose run --rm orders_api alembic upgrade head
Write-Host "=== Done ===" -ForegroundColor Green