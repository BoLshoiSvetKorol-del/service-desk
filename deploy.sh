#!/bin/bash
set -e

# ─────────────────────────────────────────────
#  Service Desk — первичный деплой на VPS
#  Запускать ОДИН РАЗ при первоначальной настройке.
#
#  Предварительные шаги (выполнить на VPS перед этим скриптом):
#    apt-get install -y git
#    git clone https://github.com/BoLshoiSvetKorol-del/service-desk.git /opt/servicedesk
#    cd /opt/servicedesk
#    bash deploy.sh
#
#  Для обновлений — используй CI/CD (git push) или update.sh
# ─────────────────────────────────────────────

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

[ "$(id -u)" -ne 0 ] && error "Запустите скрипт от root: sudo bash deploy.sh"

PROJECT_DIR="/opt/servicedesk"
DOMAIN1="extechportal.online"
DOMAIN2="extechportal.ru"

# ─── 1. Установка Docker ───────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    info "Устанавливаю Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    info "Docker установлен: $(docker --version)"
else
    info "Docker уже установлен: $(docker --version)"
fi

if ! docker compose version &>/dev/null 2>&1; then
    info "Устанавливаю Docker Compose plugin..."
    apt-get install -y docker-compose-plugin
fi

# Утилиты
apt-get install -y -q dnsutils curl openssl 2>/dev/null || true

# ─── 2. Конфигурация ───────────────────────────────────────────────────────────
CONFIG_FILE="${PROJECT_DIR}/deploy-config.env"

if [ -f "$CONFIG_FILE" ]; then
    info "Загружаю конфигурацию из deploy-config.env (интерактивный ввод пропущен)."
    # shellcheck source=/dev/null
    source "$CONFIG_FILE"
    : "${ADMIN_EMAIL:=admin@${DOMAIN1}}"
    : "${ADMIN_FULL_NAME:=Администратор}"
    : "${SMTP_HOST:=mail.hosting.reg.ru}"
    : "${SMTP_PORT:=587}"
    : "${SMTP_USER:=company@extechservice.ru}"
else
    info "Файл deploy-config.env не найден — запрашиваю данные вручную."
    echo ""
    echo "Подсказка: создайте ${CONFIG_FILE} по образцу deploy-config.env.example"
    echo "чтобы не вводить данные повторно."
    echo ""

    read -rp "Email администратора [admin@${DOMAIN1}]: " ADMIN_EMAIL
    ADMIN_EMAIL="${ADMIN_EMAIL:-admin@${DOMAIN1}}"

    read -rp "Полное имя администратора [Администратор]: " ADMIN_FULL_NAME
    ADMIN_FULL_NAME="${ADMIN_FULL_NAME:-Администратор}"

    while true; do
        read -rsp "Пароль администратора (мин. 8 символов): " ADMIN_PASSWORD
        echo ""
        [ ${#ADMIN_PASSWORD} -ge 8 ] && break
        warn "Пароль слишком короткий, попробуйте снова"
    done

    echo ""
    echo "Настройка Email для отправки уведомлений:"
    echo "  (уточните SMTP-хост у вашего почтового провайдера)"
    echo "  Пример reg.ru:  mail.hosting.reg.ru  port 465 (SSL) или 587 (TLS)"
    echo ""
    read -rp "SMTP хост [mail.hosting.reg.ru]: " SMTP_HOST
    SMTP_HOST="${SMTP_HOST:-mail.hosting.reg.ru}"

    read -rp "SMTP порт [587]: " SMTP_PORT
    SMTP_PORT="${SMTP_PORT:-587}"

    read -rp "Email для отправки писем [company@extechservice.ru]: " SMTP_USER
    SMTP_USER="${SMTP_USER:-company@extechservice.ru}"
    read -rsp "Пароль от почты: " SMTP_PASSWORD
    echo ""
fi

# ─── 3. Генерация ключей (или сохранение существующих) ────────────────────────
EXISTING_ENV="${PROJECT_DIR}/backend/.env"
if [ -f "$EXISTING_ENV" ] && grep -q "^SECRET_KEY=" "$EXISTING_ENV"; then
    SECRET_KEY=$(grep "^SECRET_KEY=" "$EXISTING_ENV" | cut -d= -f2-)
    DB_PASSWORD=$(grep "^DATABASE_URL=" "$EXISTING_ENV" | sed 's/.*servicedesk:\(.*\)@postgres.*/\1/')
    info "Использую существующие SECRET_KEY и DB_PASSWORD из backend/.env"
else
    SECRET_KEY=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -hex 16)
fi

# ─── 4. Создание .env ─────────────────────────────────────────────────────────
info "Создаю backend/.env..."
mkdir -p "${PROJECT_DIR}/backend"
cat > "${PROJECT_DIR}/backend/.env" <<EOF
APP_NAME=Service Desk
DEBUG=false
SECRET_KEY=${SECRET_KEY}

DATABASE_URL=postgresql+asyncpg://servicedesk:${DB_PASSWORD}@postgres:5432/servicedesk
REDIS_URL=redis://redis:6379/0

ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

SMTP_HOST=${SMTP_HOST}
SMTP_PORT=${SMTP_PORT}
SMTP_USER=${SMTP_USER}
SMTP_PASSWORD=${SMTP_PASSWORD}
SMTP_TLS=true
MAIL_FROM=${SMTP_USER}
MAIL_FROM_NAME=Service Desk

PORTAL_URL=https://${DOMAIN2}

STORAGE_BACKEND=local
UPLOAD_PATH=/app/uploads
MAX_FILE_SIZE_MB=10

CORS_ORIGINS=["https://${DOMAIN1}","https://www.${DOMAIN1}","https://${DOMAIN2}","https://www.${DOMAIN2}"]

ADMIN_USERNAME=admin
ADMIN_PASSWORD=${ADMIN_PASSWORD}
ADMIN_EMAIL=${ADMIN_EMAIL}
ADMIN_FULL_NAME=${ADMIN_FULL_NAME}
EOF

# Сохраняем пароль БД для postgres контейнера
echo "POSTGRES_PASSWORD=${DB_PASSWORD}" > "${PROJECT_DIR}/.env"

# ─── 5. Проверка DNS ──────────────────────────────────────────────────────────
VPS_IP=$(curl -s https://api.ipify.org)
info "IP этого сервера: ${VPS_IP}"
echo ""

check_dns() {
    local domain="$1"
    local resolved
    resolved=$(dig +short "$domain" A 2>/dev/null | head -1)
    if [ "$resolved" = "$VPS_IP" ]; then
        info "DNS OK: ${domain} → ${resolved}"
        return 0
    else
        warn "DNS ещё не готов: ${domain} → '${resolved}' (ожидается ${VPS_IP})"
        return 1
    fi
}

DNS_OK=true
check_dns "$DOMAIN1"        || DNS_OK=false
check_dns "www.$DOMAIN1"    || DNS_OK=false
check_dns "$DOMAIN2"        || DNS_OK=false
check_dns "www.$DOMAIN2"    || DNS_OK=false

if [ "$DNS_OK" = false ]; then
    echo ""
    warn "DNS ещё не перенаправлен на этот сервер."
    warn "Настройте A-записи в панели DNS (dnsadmin.hosting.reg.ru):"
    echo "    ${DOMAIN1}     → ${VPS_IP}"
    echo "    www.${DOMAIN1} → ${VPS_IP}"
    echo "    ${DOMAIN2}     → ${VPS_IP}"
    echo "    www.${DOMAIN2} → ${VPS_IP}"
    echo ""
    read -rp "DNS настроен? Нажмите Enter для продолжения или Ctrl+C для отмены: "
fi

# ─── 6. Получение SSL-сертификатов ────────────────────────────────────────────
info "Получаю SSL-сертификаты от Let's Encrypt..."

docker volume create certbot_conf 2>/dev/null || true

get_cert() {
    local domain="$1"
    info "Сертификат для ${domain}..."

    # Проверяем — сертификат уже существует в volume?
    local existing
    existing=$(docker run --rm \
        -v certbot_conf:/etc/letsencrypt \
        certbot/certbot certificates 2>/dev/null) || true

    if echo "$existing" | grep -q "Domains:.*${domain}"; then
        info "Сертификат для ${domain} уже существует — пропускаю."
        return 0
    fi

    docker run --rm \
        -v certbot_conf:/etc/letsencrypt \
        -p 80:80 \
        certbot/certbot certonly \
        --standalone \
        --email "${ADMIN_EMAIL}" \
        --agree-tos \
        --no-eff-email \
        --keep-until-expiring \
        -n \
        -d "${domain}" \
        -d "www.${domain}" || {
            warn "Не удалось получить сертификат для ${domain}. Проверьте DNS."
            return 1
        }
}

get_cert "$DOMAIN1"
get_cert "$DOMAIN2"

# ─── 7. Запуск системы ────────────────────────────────────────────────────────
info "Запускаю все сервисы..."
cd "${PROJECT_DIR}"
docker compose -f docker-compose.prod.yml up -d --build

info "Жду запуска базы данных..."
sleep 20

# ─── 8. Заполнение демо-данными ───────────────────────────────────────────────
info "Создаю демо-данные (admin, тестовые заявки)..."
docker compose -f docker-compose.prod.yml exec -T backend python scripts/seed_demo.py || \
    warn "seed_demo.py завершился с ошибкой — возможно данные уже есть, это нормально"

# ─── 9. Готово ────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Система запущена!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "  Для сотрудников:  https://${DOMAIN1}"
echo "  Для клиентов:     https://${DOMAIN2}"
echo ""
echo "  Логин admin:      admin"
echo "  Пароль admin:     ${ADMIN_PASSWORD}"
echo ""
echo "  Статус сервисов:"
docker compose -f docker-compose.prod.yml ps
echo ""
echo "  Логи:  docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "  Обновление кода (CI/CD): git push origin master"
echo "  Ручное обновление:       bash /opt/servicedesk/update.sh"
echo "  Перезапуск:              docker compose -f docker-compose.prod.yml restart"
