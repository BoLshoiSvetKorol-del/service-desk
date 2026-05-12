# upload_to_vps.ps1 -- kopiruet proekt na VPS
# Zapusk: .\upload_to_vps.ps1

$VPS_IP = "195.24.71.84"
$VPS_USER = "root"
$REMOTE_DIR = "/opt/servicedesk"

Write-Host "Kopirovanie proekta na VPS $VPS_IP..." -ForegroundColor Cyan

# Sozdayom direktoriu na VPS
ssh "${VPS_USER}@${VPS_IP}" "mkdir -p $REMOTE_DIR"

# Backend (bez __pycache__ i .pyc)
Write-Host "  -> backend" -ForegroundColor Gray
tar -czf - --exclude="backend\__pycache__" --exclude="backend\*.pyc" --exclude="backend\.env" -C . backend |
    ssh "${VPS_USER}@${VPS_IP}" "tar -xzf - -C ${REMOTE_DIR}"

# Frontend (bez node_modules i dist — server sam sdelaet npm install + build)
Write-Host "  -> frontend" -ForegroundColor Gray
tar -czf - --exclude="frontend\node_modules" --exclude="frontend\dist" --exclude="frontend\.next" -C . frontend |
    ssh "${VPS_USER}@${VPS_IP}" "tar -xzf - -C ${REMOTE_DIR}"

# nginx, docker-compose, deploy.sh
Write-Host "  -> nginx" -ForegroundColor Gray
scp -r ".\nginx" "${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/"

Write-Host "  -> docker-compose.prod.yml" -ForegroundColor Gray
scp ".\docker-compose.prod.yml" "${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/"

Write-Host "  -> deploy.sh" -ForegroundColor Gray
scp ".\deploy.sh" "${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/"

# Ustanavlivaem prava na skript
ssh "${VPS_USER}@${VPS_IP}" "chmod +x $REMOTE_DIR/deploy.sh"

Write-Host ""
Write-Host "Gotovo! Teper podklyuchites k serveru:" -ForegroundColor Green
Write-Host "  ssh root@$VPS_IP" -ForegroundColor Yellow
Write-Host "  cd $REMOTE_DIR" -ForegroundColor Yellow
Write-Host "  bash deploy.sh" -ForegroundColor Yellow
