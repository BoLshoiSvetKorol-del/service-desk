# Service Desk — Быстрый старт

## Требования

- **Docker Desktop** (Windows/Mac) или Docker Engine (Linux) — версия 24+
- **Git** (опционально — если клонируете репозиторий)
- Свободный порт **80** на компьютере

---

## Запуск за 3 шага

### Шаг 1 — Получите проект

**Вариант А: скопируйте папку с USB/диска** (рекомендуется для ВУЗа)
```
Просто скопируйте папку ProjectX целиком, перейдите в неё
```

**Вариант Б: клонируйте git-репозиторий**
```bash
git clone <url-репозитория>
cd ProjectX
```

### Шаг 2 — Подготовьте конфигурацию

Скопируйте файл настроек (если `.env` ещё нет):

**Windows (PowerShell):**
```powershell
Copy-Item backend\.env.example backend\.env
```

**Linux / Mac:**
```bash
cp backend/.env.example backend/.env
```

> Файл `.env` содержит готовые настройки для локального запуска.
> Менять ничего не нужно — просто скопируйте.

### Шаг 3 — Запустите

```bash
docker compose up -d --build
```

Первый запуск занимает **3–5 минут** (загрузка образов, сборка).

После этого откройте в браузере: **http://localhost**

---

## Данные для входа

| Роль | Логин | Пароль |
|------|-------|--------|
| Администратор | `admin` | `changeme` |

Дополнительные тестовые пользователи (агенты, клиенты):
```bash
docker compose exec backend python scripts/seed_demo.py
```
После seed — пароль всех demo-пользователей: `demo1234`

---

## Что входит в систему

| Адрес | Назначение |
|-------|-----------|
| http://localhost | Интерфейс сотрудников (логин admin/changeme) |
| http://localhost/portal | Клиентский портал (после seed — demo клиент) |
| http://localhost/api/docs | Swagger API документация |
| http://localhost/health | Проверка состояния |

---

## Если что-то пошло не так

**Проблема: порт 80 занят**
```bash
# Проверить что занимает порт 80 (Windows)
netstat -ano | findstr :80

# Временно остановить IIS (если Windows)
net stop w3svc
```

**Проблема: ошибки при миграции БД (DuplicateObject)**
```bash
docker compose down
docker volume rm projectx_postgres_data projectx_redis_data
docker compose up -d --build
```

**Посмотреть логи:**
```bash
docker compose logs backend       # логи API
docker compose logs frontend      # логи фронтенда
docker compose logs -f            # все логи в реальном времени
```

**Перезапустить всё с нуля (удалить все данные):**
```bash
docker compose down -v
docker compose up -d --build
```

---

## Остановка

```bash
docker compose down
```

---

## Структура сервисов

```
http://localhost (порт 80)
    ├── Nginx (прокси)
    │   ├── /api/*      → Backend FastAPI (порт 8000)
    │   └── /*          → Frontend React (порт 3000)
    ├── PostgreSQL (порт 5432, внутренний)
    ├── Redis (порт 6379, внутренний)
    ├── Celery Worker (фоновые задачи)
    └── Celery Beat (планировщик SLA)
```
