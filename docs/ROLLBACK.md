# Откат и восстановление — Service Desk

## Быстрый чеклист при поломке

```
# 1. Посмотреть что упало
docker compose ps
docker compose logs backend --tail=50
docker compose logs nginx --tail=20

# 2. Перезапустить всё
docker compose restart

# 3. Если не помогло — полный рестарт
docker compose down && docker compose up -d
```

---

## Откат на предыдущий коммит (локально)

```bash
# Посмотреть историю коммитов
git log --oneline -10

# Откатить рабочие файлы до конкретного коммита (БЕЗ удаления истории)
git checkout <hash> -- backend/app/api/v1/events.py
git checkout <hash> -- backend/app/redis.py
# и т.д. для нужных файлов

# Или полный откат всего проекта (ОСТОРОЖНО — потеряешь незакоммиченные изменения)
git reset --hard <hash>

# После отката перезапустить backend
docker compose restart backend
```

### Ключевые коммиты

| Hash | Описание | Статус |
|------|----------|--------|
| `a41241d` | dept_head роль + мобилка + SLA + портал | Стабильный |
| `9004948` | GitHub Actions CI/CD | Стабильный |
| `5b6b1ee` | Авто-маршрутизация M18 + FAQ + баг-фиксы | Стабильный |
| `d41fa13` | deploy-config.env.example | Стабильный |
| `77f504e` | certbot non-interactive | Стабильный |

---

## Откат миграции БД

```bash
# Посмотреть текущую версию Alembic
docker compose exec backend alembic current

# Посмотреть историю миграций
docker compose exec backend alembic history --verbose

# Откатить на одну миграцию назад
docker compose exec backend alembic downgrade -1

# Откатить до конкретной ревизии
docker compose exec backend alembic downgrade 015

# Применить все миграции заново
docker compose exec backend alembic upgrade head
```

### Список миграций

| Ревизия | Описание |
|---------|----------|
| `001` | Начальная схема (users, tickets, priorities) |
| `002–009` | Статусы, комментарии, вложения, история, уведомления |
| `010–014` | Теги, заметки, портал, типы заявок |
| `015` | Правила маршрутизации (routing_rules) |
| `016` | Индексы производительности (IF NOT EXISTS) |
| `017` | Роль department_head + cancellation_reason |

---

## Откат на сервере (продакшн)

```bash
# Подключиться к серверу
ssh root@195.24.71.84

# Перейти в папку проекта
cd /opt/servicedesk

# Посмотреть текущий коммит на сервере
git log --oneline -5

# Откатить до стабильного коммита
git reset --hard a41241d

# Пересобрать и перезапустить (без интернета — только restart)
docker compose restart backend

# Если нужна пересборка (с интернетом)
docker compose build backend && docker compose up -d backend
```

---

## Бэкап и восстановление БД

```bash
# Создать дамп БД (на сервере)
docker compose exec postgres pg_dump -U servicedesk servicedesk > backup_$(date +%Y%m%d).sql

# Восстановить из дампа
docker compose exec -T postgres psql -U servicedesk servicedesk < backup_20260515.sql
```

---

## Откат SSE/Redis/DB-pool фиксов (18.05.2026)

Если фиксы из 18.05 вызвали проблемы, откатить эти 4 файла:

```bash
# Откат к коммиту a41241d (до фиксов 18.05)
git checkout a41241d -- backend/app/api/v1/events.py
git checkout a41241d -- backend/app/redis.py
git checkout a41241d -- backend/app/database.py
git checkout a41241d -- backend/alembic/versions/016_performance_indexes.py
docker compose restart backend
```

**Что делали фиксы 18.05:**
- `events.py` — SSE больше не держит DB-соединение всё время онлайн
- `redis.py` — таймаут 5с на публикацию в Redis
- `database.py` — `pool_pre_ping=True` для автопереподключения
- `016_performance_indexes.py` — `CREATE INDEX IF NOT EXISTS` вместо падения при дубле

---

## Деплой на прод (нормальный флоу)

```bash
# Локально
git push origin master
# GitHub Actions сам задеплоит (~2-3 минуты)

# Если Actions не работает — вручную на сервере
ssh root@195.24.71.84
cd /opt/servicedesk
git pull origin master
docker compose build backend frontend
docker compose up -d
docker compose exec backend alembic upgrade head
```

## Полезные команды на сервере

```bash
# Статус контейнеров
docker compose ps

# Логи в реальном времени
docker compose logs -f backend

# Войти в контейнер backend
docker compose exec backend bash

# Проверить SSL
certbot certificates

# Перевыпустить SSL вручную
certbot renew --force-renewal
```
