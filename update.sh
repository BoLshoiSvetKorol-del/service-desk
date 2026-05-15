#!/bin/bash
# Manual update script — run directly on VPS when CI/CD is not available
# Usage: bash update.sh
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

[ "$(id -u)" -ne 0 ] && { warn "Запустите от root: sudo bash update.sh"; exit 1; }

PROJECT_DIR="/opt/servicedesk"
cd "$PROJECT_DIR"

info "Обновляю сервисы..."
docker compose -f docker-compose.prod.yml up -d --build backend frontend celery_worker celery_beat

info "Очищаю старые образы..."
docker image prune -f

echo ""
info "Обновление завершено в $(date)"
echo "Статус сервисов:"
docker compose -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}"
