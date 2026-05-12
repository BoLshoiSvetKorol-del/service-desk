# Миссии разработки Service Desk

Проект разбит на миссии: сначала весь Backend (MVP), затем Frontend (MVP), затем расширенный функционал по ТЗ (SD.docx).  
Каждая миссия — завершённая, тестируемая часть системы.

---

## Обзор миссий

| # | Миссия | Слой | Статус |
|---|--------|------|--------|
| 01 | Project Foundation | Backend | ✅ Готово |
| 02 | Authentication | Backend | ✅ Готово |
| 03 | Users & Departments | Backend | ✅ Готово |
| 04 | Reference Data | Backend | ✅ Готово |
| 05 | Tickets Core | Backend | ✅ Готово |
| 06 | SLA Engine | Backend | ✅ Готово |
| 07 | Comments & Attachments | Backend | ✅ Готово |
| 08 | Celery Tasks (Email + SLA) | Backend | ✅ Готово |
| 09 | Reports & Saved Filters | Backend | ✅ Готово |
| 10 | SSE & Notifications | Backend | ✅ Готово |
| 11 | Frontend Foundation + Auth UI | Frontend | ✅ Готово |
| 12 | Tickets UI | Frontend | ✅ Готово |
| 13 | Comments, Attachments & Timeline UI | Frontend | ✅ Готово |
| 14 | Real-time, Notifications & Reports UI | Frontend | ✅ Готово |
| 15 | Merge Tickets (Мердж заявок) | Full-stack | ✅ Готово |
| 16 | Tags & Notes (Теги и заметки) | Full-stack | ✅ Готово |
| 17 | Client Portal (Клиентский портал) | Full-stack | 🔜 Следующая |
| 18 | Enhanced SLA Reports (Детальные отчёты) | Full-stack | ⬜ Запланировано |
| 19 | Email Channel (Email-канал) | Full-stack | ⬜ Запланировано |
| 20 | VK Bot | Backend | ⬜ Если останется время |

---

## Миссия 01 — Project Foundation

**Цель:** Поднять рабочее окружение: все контейнеры, базовый скелет FastAPI, подключение к БД, первая миграция.

**Что входит:**
- `docker-compose.yml` — сервисы: `nginx`, `backend`, `frontend`, `postgres`, `redis`, `celery_worker`, `celery_beat`
- `nginx/nginx.conf` — reverse proxy: `/api` → backend, `/` → frontend, `/uploads` → static
- `backend/Dockerfile`, `frontend/Dockerfile`
- FastAPI приложение: `app/main.py`, `app/config.py` (pydantic-settings), `app/database.py` (asyncpg + SQLAlchemy async)
- Alembic: `alembic.ini`, `alembic/env.py`, начальная пустая миграция
- `backend/.env.example` с описанием всех переменных
- `backend/requirements.txt`

**Ключевые файлы:**
```
backend/app/main.py
backend/app/config.py
backend/app/database.py
backend/alembic/env.py
docker-compose.yml
nginx/nginx.conf
backend/.env.example
```

**Результат:** `docker compose up` поднимает все контейнеры, FastAPI отвечает на `GET /health` → `{"status": "ok"}`, Alembic подключается к PostgreSQL.

**Зависимости:** нет.

---

## Миссия 02 — Authentication

**Цель:** Реализовать полный цикл аутентификации: вход, JWT-токены, обновление, выход.

**Что входит:**
- Модель `User` (SQLAlchemy): поля id, email, username, password_hash, full_name, role (enum), department_id, is_active, created_at
- Миграция для таблицы `users`
- Сид-скрипт: создание первого администратора из env (`ADMIN_USERNAME`, `ADMIN_PASSWORD`)
- Утилиты: `app/utils/security.py` — `hash_password`, `verify_password`, `create_access_token`, `create_refresh_token`, `decode_token`
- Хранение refresh-токенов в Redis (блок-лист при logout, TTL = 7 дней)
- Схемы Pydantic: `LoginRequest`, `TokenResponse`, `UserResponse`
- Эндпоинты `app/api/v1/auth.py`:
  - `POST /api/v1/auth/login` — вернуть `access_token` + `refresh_token`
  - `POST /api/v1/auth/refresh` — обновить access по refresh
  - `POST /api/v1/auth/logout` — добавить refresh в Redis блок-лист
- Dependency `get_current_user` — декодирует JWT, загружает пользователя из БД
- Декораторы `require_role(*roles)` в `app/utils/permissions.py`

**Ключевые файлы:**
```
backend/app/models/user.py
backend/app/schemas/auth.py
backend/app/schemas/user.py
backend/app/api/v1/auth.py
backend/app/utils/security.py
backend/app/utils/permissions.py
backend/alembic/versions/002_users.py
```

**Результат:** `POST /auth/login` возвращает токены; защищённые маршруты отклоняют запросы без валидного JWT; сид-скрипт создаёт admin-пользователя.

**Зависимости:** 01.

---

## Миссия 03 — Users & Departments

**Цель:** CRUD для управления пользователями и отделами (только администратор).

**Что входит:**
- Модель `Department`: id, name, description, created_at + миграция
- Дополнение модели `User`: внешний ключ `department_id → departments.id`
- Схемы: `DepartmentCreate`, `DepartmentResponse`, `UserCreate`, `UserUpdate`, `UserListResponse`
- Эндпоинты `app/api/v1/departments.py`:
  - `GET /departments` — список (доступно всем авторизованным)
  - `POST /departments` — создать (admin)
  - `GET /departments/{id}` — отдел + список его агентов
  - `PUT /departments/{id}` — редактировать (admin)
  - `DELETE /departments/{id}` — удалить, если нет связанных заявок (admin)
- Эндпоинты `app/api/v1/users.py`:
  - `GET /users` — список с фильтрами `?role=&department_id=&is_active=&search=` (admin)
  - `POST /users` — создать пользователя (admin)
  - `GET /users/me` — свой профиль
  - `PUT /users/me` — изменить свой профиль (full_name, email, пароль)
  - `GET /users/{id}` — профиль пользователя (admin, agent)
  - `PUT /users/{id}` — редактировать (admin)
  - `PATCH /users/{id}/activate` — активировать/деактивировать (admin)
- Пагинация: хелпер `app/utils/pagination.py` — `PagedResponse[T]`

**Ключевые файлы:**
```
backend/app/models/department.py
backend/app/api/v1/users.py
backend/app/api/v1/departments.py
backend/app/schemas/user.py
backend/app/schemas/department.py
backend/app/utils/pagination.py
backend/alembic/versions/003_departments.py
```

**Результат:** администратор может создавать пользователей/отделы через API; пользователь видит только свой профиль; пагинация работает корректно.

**Зависимости:** 02.

---

## Миссия 04 — Reference Data

**Цель:** Справочники типов заявок и приоритетов с SLA-часами. Маршрутизация заявок по типу.

**Что входит:**
- Модель `Priority`: id, name (enum: low/normal/high/critical), sla_hours (24/8/4/1), color_hex + миграция
- Сид данных приоритетов (4 фиксированные записи, создаются автоматически при старте)
- Модель `TicketType`: id, name, service_type, work_direction, default_department_id (FK), is_active + миграция
- Схемы: `PriorityResponse`, `TicketTypeCreate`, `TicketTypeUpdate`, `TicketTypeResponse`
- Эндпоинты `app/api/v1/priorities.py`:
  - `GET /priorities` — список всех приоритетов (все авторизованные)
- Эндпоинты `app/api/v1/ticket_types.py`:
  - `GET /ticket-types` — список (все авторизованные)
  - `POST /ticket-types` — создать (admin)
  - `GET /ticket-types/{id}` — детали
  - `PUT /ticket-types/{id}` — редактировать (admin)
  - `DELETE /ticket-types/{id}` — удалить, если нет заявок (admin)

**Ключевые файлы:**
```
backend/app/models/priority.py
backend/app/models/ticket_type.py
backend/app/api/v1/priorities.py
backend/app/api/v1/ticket_types.py
backend/app/schemas/ticket_type.py
backend/alembic/versions/004_reference_data.py
```

**Результат:** 4 приоритета засеяны при старте; администратор управляет типами заявок; при выборе типа клиент знает, в какой отдел пойдёт заявка.

**Зависимости:** 03.

---

## Миссия 05 — Tickets Core

**Цель:** Полный жизненный цикл заявки: создание, просмотр, переходы статусов, назначение, история.

**Что входит:**
- Модель `Ticket`: все поля из ERD (см. architecture.md §2) + миграция
- Модель `TicketHistory`: id, ticket_id, user_id, event_type, payload (JSONB), created_at + миграция
- Генератор номеров `app/utils/ticket_number.py` — атомарный счётчик в БД, формат `SD-YYYY-XXXXX`
- Сервис `app/services/ticket_service.py`:
  - `create_ticket` — присвоить номер, автовыбор отдела по типу, запись в историю
  - `change_status` — валидация перехода по матрице (см. architecture.md §5.2), запись в историю
  - `assign_ticket` — назначить исполнителя/отдел, запись в историю
  - `get_tickets` — фильтрация с учётом роли: user видит только свои, agent — отдела+назначенные, admin — все
- Схемы: `TicketCreate`, `TicketUpdate`, `TicketResponse`, `TicketListItem`, `StatusChangeRequest`, `AssignRequest`
- Эндпоинты `app/api/v1/tickets.py`:
  - `GET /tickets` — список с фильтрами (status, priority_id, type_id, department_id, assignee_id, sla_violated, search, date_from, date_to, sort_by, page)
  - `POST /tickets` — создать
  - `GET /tickets/{id}` — карточка
  - `PUT /tickets/{id}` — редактировать title/description (admin, agent)
  - `PATCH /tickets/{id}/status` — изменить статус
  - `PATCH /tickets/{id}/assign` — назначить
  - `PATCH /tickets/{id}/priority` — изменить приоритет
  - `GET /tickets/{id}/history` — лента событий

**Ключевые файлы:**
```
backend/app/models/ticket.py
backend/app/models/ticket_history.py
backend/app/services/ticket_service.py
backend/app/api/v1/tickets.py
backend/app/schemas/ticket.py
backend/app/utils/ticket_number.py
backend/alembic/versions/005_tickets.py
```

**Результат:** полный CRUD заявок работает; матрица переходов статусов соблюдается (403 при недопустимом переходе); история событий записывается на каждое действие.

**Зависимости:** 04.

---

## Миссия 06 — SLA Engine

**Цель:** Автоматический расчёт SLA дедлайнов в рабочих часах, пауза при ожидании информации.

**Что входит:**
- Сервис `app/services/sla_service.py`:
  - `calculate_deadline(start_dt, sla_hours)` — прибавить N рабочих часов (пн-пт 09:00–18:00), вернуть `datetime`
  - `pause_sla(ticket)` — записать `sla_paused_at = now()`
  - `resume_sla(ticket)` — вычислить `pause_duration`, добавить к `sla_extra_minutes`, пересчитать `sla_deadline`, обнулить `sla_paused_at`
  - `check_sla_violated(ticket)` — вернуть `True`, если `now() > sla_deadline` и статус активный
- Интеграция в `ticket_service.py`:
  - При создании заявки → `calculate_deadline`
  - При переходе `in_progress → waiting_info` → `pause_sla`
  - При переходе `waiting_info → in_progress` → `resume_sla`
- Поле `sla_violated` обновляется в реальном времени через Celery (миссия 08)
- Unit-тесты `tests/test_sla.py` — граничные случаи: старт в пятницу вечером, праздники (базово), паузы

**Ключевые файлы:**
```
backend/app/services/sla_service.py
backend/tests/test_sla.py
```

**Результат:** `calculate_deadline(friday_17:30, 4)` → следующий понедельник 10:30; пауза SLA корректно добавляется к дедлайну; тесты покрывают граничные случаи.

**Зависимости:** 05.

---

## Миссия 07 — Comments & Attachments

**Цель:** Комментарии к заявкам (в т.ч. внутренние) и загрузка файлов с абстракцией хранилища.

**Что входит:**
- Модель `Comment`: id, ticket_id, author_id, body, is_internal, created_at, updated_at + миграция
- Модель `Attachment`: id, ticket_id, comment_id (nullable), original_filename, stored_path, size_bytes, mimetype, uploaded_by, created_at + миграция
- Абстракция хранилища `app/services/storage/`:
  - `base.py` — абстрактный класс `StorageBackend` с методами `save(file) → path`, `delete(path)`, `get_url(path)`
  - `local.py` — сохранение в `uploads/tickets/{ticket_id}/{uuid}_{filename}`, отдача через Nginx `X-Accel-Redirect`
  - `minio.py` — заглушка с интерфейсом (не реализована, только структура)
  - Фабрика: выбор бэкенда через `STORAGE_BACKEND` env
- Эндпоинты `app/api/v1/comments.py`:
  - `GET /tickets/{id}/comments` — список (is_internal скрыты от user-роли)
  - `POST /tickets/{id}/comments` — добавить (is_internal доступно только agent/admin)
  - `PUT /tickets/{id}/comments/{cid}` — редактировать свой комментарий (окно 5 минут)
  - `DELETE /tickets/{id}/comments/{cid}` — удалить (admin или автор в первые 5 мин)
- Эндпоинты `app/api/v1/attachments.py`:
  - `POST /tickets/{id}/attachments` — загрузить файл (multipart, макс 10 МБ, проверка MIME)
  - `POST /tickets/{id}/comments/{cid}/attachments` — загрузить к комментарию
  - `GET /attachments/{id}` — скачать (проверка доступа к заявке)
  - `DELETE /attachments/{id}` — удалить файл + запись в БД

**Ключевые файлы:**
```
backend/app/models/comment.py
backend/app/models/attachment.py
backend/app/services/storage/base.py
backend/app/services/storage/local.py
backend/app/services/storage/minio.py
backend/app/api/v1/comments.py
backend/app/api/v1/attachments.py
backend/alembic/versions/007_comments_attachments.py
```

**Результат:** агент может оставлять внутренние комментарии, невидимые пользователям; файлы сохраняются локально и отдаются через Nginx без участия Python в стриминге; смена `STORAGE_BACKEND=minio` не требует правок бизнес-кода.

**Зависимости:** 05.

---

## Миссия 08 — Celery Tasks (Email + SLA мониторинг)

**Цель:** Фоновые задачи: email-уведомления через SendGrid и периодический мониторинг SLA.

**Что входит:**
- `app/tasks/celery_app.py` — Celery с Redis брокером + Celery Beat расписание
- Сервис `app/services/email_service.py`:
  - Jinja2 для рендера HTML-шаблонов
  - Отправка через SendGrid HTTP API
- HTML-шаблоны `backend/templates/`:
  - `base_email.html` — базовый layout (шапка, подпись)
  - `ticket_created.html` — подтверждение для создателя
  - `ticket_assigned.html` — уведомление исполнителю
  - `ticket_status_changed.html` — изменение статуса
  - `new_comment.html` — новый комментарий
  - `sla_warning.html` — предупреждение о дедлайне
  - `sla_violated.html` — нарушение SLA (эскалация)
- `app/tasks/email_tasks.py`:
  - `send_email_task(to, template, context)` — асинхронная отправка
  - Вызывается из `ticket_service`, `comment` эндпоинтов через `.delay()`
- `app/tasks/sla_tasks.py` + Beat расписание:
  - `check_sla_warnings` (каждые 15 мин) — найти заявки, где осталось <1ч до дедлайна → SSE-событие `sla_warning` + email исполнителю
  - `check_sla_violations` (каждые 10 мин) — найти просроченные, установить `sla_violated=True`, SSE-событие `sla_violated`
  - `escalate_overdue` (каждые 30 мин) — заявки просрочены >2ч → email руководителю отдела

**Ключевые файлы:**
```
backend/app/tasks/celery_app.py
backend/app/tasks/email_tasks.py
backend/app/tasks/sla_tasks.py
backend/app/services/email_service.py
backend/templates/*.html
```

**Результат:** при создании заявки создатель получает email; исполнитель получает email при назначении; Celery Beat отслеживает SLA и рассылает предупреждения; очередь задач видна в Redis.

**Зависимости:** 06, 07.

---

## Миссия 09 — Reports & Saved Filters

**Цель:** Аналитические отчёты по заявкам и персональные сохранённые фильтры.

**Что входит:**
- Модель `SavedFilter`: id, user_id, name, filter_params (JSONB), created_at + миграция
- Эндпоинты `app/api/v1/filters.py`:
  - `GET /filters` — мои фильтры
  - `POST /filters` — сохранить `{"name": "...", "filter_params": {...}}`
  - `DELETE /filters/{id}` — удалить свой фильтр
- Эндпоинты `app/api/v1/reports.py` (доступны admin + agent):
  - `GET /reports/tickets-count` — кол-во заявок за период, группировка по дням/неделям/месяцам
  - `GET /reports/by-status` — распределение заявок по статусам (count на каждый статус)
  - `GET /reports/avg-resolution-time` — среднее время от создания до закрытия, разбивка по приоритетам
  - `GET /reports/sla-compliance` — % заявок без нарушения SLA за период
  - `GET /reports/export` — выгрузка всех заявок в CSV или Excel (`?format=csv|xlsx&date_from=&date_to=`)
- Для Excel используется `openpyxl`, для CSV — `csv` из стандартной библиотеки
- Query params всех отчётов: `?date_from=&date_to=&department_id=&type_id=&priority_id=`

**Ключевые файлы:**
```
backend/app/models/saved_filter.py
backend/app/api/v1/reports.py
backend/app/api/v1/filters.py
backend/app/schemas/report.py
backend/alembic/versions/009_saved_filters.py
```

**Результат:** отчёты возвращают корректные агрегации; экспорт в Excel скачивается с правильными заголовками и данными; пользователь может сохранить набор фильтров и применить его одним кликом.

**Зависимости:** 05.

---

## Миссия 10 — SSE & Notifications

**Цель:** Система реального времени: уведомления в БД + push через Server-Sent Events.

**Что входит:**
- Модель `Notification`: id, user_id, ticket_id, event_type, message, is_read, created_at + миграция
- Сервис `app/services/notification_service.py`:
  - `create_notification(user_id, ticket_id, event_type, message)` — записать в БД
  - `publish_sse(channel, event_data)` — опубликовать в Redis канал `sse:user:{id}` или `sse:department:{id}`
  - `notify_ticket_event(ticket, event_type, actor)` — определить получателей + создать уведомления + publish
- Интеграция `notify_ticket_event` в `ticket_service` (статус, назначение) и в эндпоинты комментариев
- Эндпоинт SSE `app/api/v1/events.py`:
  - `GET /api/v1/events` — держит соединение, подписывается на `sse:user:{current_user.id}`, стримит `text/event-stream`
  - Поддержка `Last-Event-ID` для переподключения
  - Heartbeat каждые 30 сек (пустой комментарий `: ping\n\n`)
- Эндпоинты `app/api/v1/notifications.py`:
  - `GET /notifications` — список `?is_read=false&page=&page_size=`
  - `PATCH /notifications/{id}/read` — пометить прочитанным
  - `PATCH /notifications/read-all` — все прочитаны

**Ключевые файлы:**
```
backend/app/models/notification.py
backend/app/services/notification_service.py
backend/app/api/v1/events.py
backend/app/api/v1/notifications.py
backend/alembic/versions/010_notifications.py
```

**Результат:** при смене статуса заявки клиент немедленно получает SSE-событие без перезагрузки страницы; уведомления хранятся в БД; переподключение после разрыва не теряет события.

**Зависимости:** 05.

---

## Миссия 11 — Frontend Foundation + Auth UI

**Цель:** Создать React-приложение с роутингом, HTTP-клиентом, стором и страницей входа.

**Что входит:**
- Vite + React 18 + TypeScript + Ant Design (antd) + React Router v6
- `src/api/client.ts` — Axios instance: `baseURL=/api/v1`, интерцептор запросов (добавить `Authorization`), интерцептор ответов (401 → автоматический refresh токена → повтор запроса)
- `src/api/auth.ts` — `login`, `refresh`, `logout`
- `src/store/authStore.ts` — Zustand: `user`, `accessToken`, `isAuthenticated`, `login()`, `logout()`
- Типы `src/types/user.ts`, `src/types/common.ts` (`PagedResponse<T>`, `ApiError`)
- `src/router/index.tsx` — `PrivateRoute` (редирект на /login если не авторизован), `RoleRoute` (403 при недостаточной роли)
- `src/components/common/Layout/` — `AppLayout` с `Sidebar` (навигация, роль-зависимая) и `Header` (имя пользователя, кнопка выхода)
- Страница `src/pages/Login/` — форма (username + password), валидация antd Form, обработка ошибок (неверный пароль → alert)
- Страница `src/pages/Settings/` (только admin):
  - Вкладка Users — таблица пользователей + модал создания/редактирования
  - Вкладка Departments — аналогично
  - Вкладка TicketTypes — аналогично

**Ключевые файлы:**
```
frontend/src/api/client.ts
frontend/src/api/auth.ts
frontend/src/store/authStore.ts
frontend/src/router/index.tsx
frontend/src/components/common/Layout/
frontend/src/pages/Login/
frontend/src/pages/Settings/
frontend/src/types/
```

**Результат:** вход → редирект на Dashboard; выход → редирект на /login; токен автоматически обновляется; администратор может создавать пользователей через UI.

**Зависимости:** 02 (backend auth API).

---

## Миссия 12 — Tickets UI

**Цель:** Список заявок с фильтрами, форма создания, карточка заявки с управлением статусом и назначением.

**Что входит:**
- `src/api/tickets.ts` — все CRUD методы, фильтрация, смена статуса, назначение
- Компоненты:
  - `PriorityBadge` — цветной тег (low=серый, normal=синий, high=оранжевый, critical=красный)
  - `StatusBadge` — тег статуса с цветом
  - `SLACountdown` — таймер: зелёный >50% времени, жёлтый 25–50%, оранжевый <25%, красный "просрочено"
- Страница `TicketsListPage`:
  - `FilterPanel` — фильтры: статус (chips), приоритет (chips), отдел, исполнитель, диапазон дат, поиск (debounce 300мс)
  - `SavedFiltersMenu` — сохранить текущий фильтр / применить сохранённый
  - `TicketsTable` — antd Table: номер (ссылка), заголовок, приоритет, статус, SLA-таймер, исполнитель, дата создания
  - Пагинация с `page_size` 20
- Страница `CreateTicketPage`:
  - `TicketForm` — поля: заголовок, описание (textarea), тип (Select → автозаполнение отдела), приоритет (Select → показать расчётный дедлайн SLA), загрузка файлов
- Страница `TicketDetailPage`:
  - Шапка: номер, заголовок, `StatusBadge` + дропдаун смены статуса (кнопки только для допустимых переходов), `SLACountdown`
  - Мета-блок: заявитель, отдел, `AssigneeSelect` (для агента/admin), даты
  - Описание заявки
  - `AttachmentList` — список файлов с иконками типа и кнопкой скачать

**Ключевые файлы:**
```
frontend/src/api/tickets.ts
frontend/src/components/common/PriorityBadge/
frontend/src/components/common/StatusBadge/
frontend/src/components/common/SLACountdown/
frontend/src/components/tickets/FilterPanel/
frontend/src/components/tickets/TicketForm/
frontend/src/pages/Tickets/TicketsList/
frontend/src/pages/Tickets/TicketDetail/
frontend/src/pages/Tickets/CreateTicket/
```

**Результат:** пользователь видит свои заявки, агент — заявки отдела, admin — все; создание заявки работает со всеми полями; смена статуса через UI записывает переход; SLA-таймер обновляется в реальном времени (каждую минуту через `setInterval`).

**Зависимости:** 05, 11.

---

## Миссия 13 — Comments, Attachments & Timeline UI

**Цель:** Блок общения на карточке заявки: комментарии, файлы, лента истории событий.

**Что входит:**
- `src/api/comments.ts`, `src/api/attachments.ts`
- Компонент `CommentList`:
  - `CommentItem` — аватар автора, имя, дата, текст, badge "Внутренний" (для is_internal)
  - Кнопки редактировать/удалить (своё, в первые 5 мин)
- Компонент `CommentForm`:
  - Textarea + кнопка "Отправить"
  - `InternalToggle` — переключатель "Внутренний комментарий" (виден только агентам/admin)
  - `AttachmentUpload` — drag-and-drop (antd Upload), показ превью, ограничение 10 МБ
- Компонент `AttachmentList`:
  - Иконка по типу файла, имя, размер, кнопка скачать, кнопка удалить (для владельца/admin)
- Компонент `ActivityTimeline` (antd Timeline):
  - Каждый элемент `TicketHistory` — иконка типа события, текст ("Статус изменён: Новая → В работе"), автор, дата
  - Хронологический порядок (новые сверху)
- Интеграция в `TicketDetailPage` — вкладки или секции: "Комментарии", "Вложения", "История"

**Ключевые файлы:**
```
frontend/src/api/comments.ts
frontend/src/api/attachments.ts
frontend/src/components/tickets/CommentList/
frontend/src/components/tickets/CommentForm/
frontend/src/components/tickets/AttachmentList/
frontend/src/components/tickets/ActivityTimeline/
```

**Результат:** агент оставляет внутренний комментарий — пользователь его не видит; файл загружается drag-and-drop; лента истории показывает все действия в хронологическом порядке.

**Зависимости:** 07, 12.

---

## Миссия 14 — Real-time, Notifications & Reports UI

**Цель:** SSE-интеграция (живые обновления), колокольчик уведомлений, Dashboard и страница отчётов.

**Что входит:**
- `src/hooks/useSSE.ts` — подписка на `GET /api/v1/events`, авто-переподключение через 3 сек при разрыве, обработка `Last-Event-ID`
- `src/store/notificationStore.ts` — Zustand: список уведомлений, счётчик непрочитанных, методы `markRead`, `markAllRead`
- Компонент `NotificationBell` в Header:
  - Иконка колокольчика с badge (непрочитанных)
  - Дропдаун со списком последних 10 уведомлений
  - Клик на уведомление → переход на карточку заявки + пометить прочитанным
- SSE-обработчики в `useSSE`:
  - `ticket_status_changed` → обновить запись в кеше списка + показать antd notification
  - `ticket_assigned` → то же
  - `new_comment` → обновить счётчик комментариев
  - `sla_warning` → antd warning notification с таймером
  - `sla_violated` → antd error notification
- `src/pages/Dashboard/`:
  - `StatsCards` — 4 карточки: "Мои заявки", "Новые", "Просроченные", "Ожидают ответа"
  - `RecentTicketsTable` — последние 5 заявок пользователя
  - `SLAViolationsAlert` — список просроченных заявок (для admin/agent)
- `src/pages/Reports/` (admin + agent):
  - DateRangePicker + DepartmentFilter
  - `TicketsCountChart` — столбчатая диаграмма (recharts или antd Charts)
  - `StatusDistributionChart` — круговая диаграмма
  - `AvgResolutionTimeChart` — столбчатая по приоритетам
  - `SLAComplianceMetric` — большое число с процентом соответствия SLA
  - `ExportButton` — скачать CSV / Excel

**Ключевые файлы:**
```
frontend/src/hooks/useSSE.ts
frontend/src/store/notificationStore.ts
frontend/src/components/common/NotificationBell/
frontend/src/pages/Dashboard/
frontend/src/pages/Reports/
```

**Результат:** смена статуса заявки одним агентом — другой агент видит обновление без перезагрузки страницы; колокольчик показывает количество непрочитанных; отчёты строятся по выбранному периоду; экспорт в Excel скачивается.

**Зависимости:** 08, 09, 10, 13.

---

## Итог: порядок выполнения

```
01 → 02 → 03 → 04 → 05 ──┬── 06 ──┐
                           │        ├── 08 ──┐
                           └── 07 ──┘        │
                           │                 │
                           ├── 09 ────────────────────────┐
                           │                 │            │
                           └── 10 ──┐        │            │
                                    │        │            │
                           11 → 12 → 13 → 14 ←────────────┘
```

**Минимальный рабочий контур (demo-ready):** миссии 01–05, 11–12  
**Полный MVP:** миссии 01–14  
**Расширенный функционал (SD.docx):** миссии 15–19

---

## Миссия 15 — Merge Tickets (Мердж заявок)

**Цель:** Позволить агентам объединять дублирующие заявки от одного клиента или по одной проблеме в одну главную.

**Что входит:**

Backend:
- Поле `merged_into_id` в таблице `tickets` (FK на себя) + миграция `011`
- Статус `merged` в enum `TicketStatus`
- Эндпоинт `POST /api/v1/tickets/{id}/merge` — принимает `target_id`, переводит исходную заявку в статус `merged`, записывает `merged_into_id`, переносит все комментарии и вложения в целевую заявку, создаёт запись в истории
- Эндпоинт `GET /api/v1/tickets/{id}/merged` — список заявок, смерженных в данную
- Поиск дублей: `GET /api/v1/tickets/{id}/duplicates?q=...` — поиск заявок для предложения мерджа
- Тесты: `test_merge.py`

Frontend:
- Кнопка "Объединить" в `TicketDetail` (только для admin/agent)
- Модальное окно с поиском заявок (input + список результатов с номером, заголовком, статусом)
- После мерджа — редирект на целевую заявку
- Значок "поглощена заявкой SD-XXXX" в заголовке смерженной заявки

**Ключевые файлы:**
```
backend/alembic/versions/011_merge_tickets.py
backend/app/api/v1/tickets.py  (новые эндпоинты merge)
backend/app/services/ticket_service.py  (merge логика)
backend/tests/test_merge.py
frontend/src/api/tickets.ts  (mergeTicket, getMerged, getDuplicates)
frontend/src/components/tickets/MergeModal/
```

**Результат:** агент видит две заявки с одинаковой проблемой, объединяет их — одна становится главной со всеми комментариями, вторая переходит в статус "объединена" и показывает ссылку на главную.

**Зависимости:** 05, 12.

---

## Миссия 16 — Tags & Notes (Теги и заметки)

**Цель:** Добавить теги к заявкам (из SD.docx) и личные заметки агента по заявке.

**Что входит:**

Backend:
- Таблица `tags` + таблица `ticket_tags` (M2M) + миграция `012`
- CRUD для тегов: `GET/POST /api/v1/tags`, `DELETE /api/v1/tags/{id}`
- `POST /api/v1/tickets/{id}/tags` — добавить тег к заявке
- `DELETE /api/v1/tickets/{id}/tags/{tag_id}` — убрать тег
- Таблица `ticket_notes` — личные заметки агента (не видны клиенту, не видны другим агентам) + миграция `012`
- CRUD для заметок: `GET/POST/PUT/DELETE /api/v1/tickets/{id}/notes`
- Тесты: `test_tags_notes.py`

Frontend:
- Компонент `TagSelector` — мультиселект с автодополнением, создание нового тега на лету
- Теги отображаются в карточке заявки и в списке
- Вкладка "Заметки" в `TicketDetail` — личные заметки с markdown-редактором

**Зависимости:** 05, 12, 13.

---

## Миссия 17 — Client Portal (Клиентский портал + Безопасность)

**Цель:** Разделить интерфейсы клиентов и сотрудников, добавить самостоятельную регистрацию через email.

**Проблема:** Сейчас клиент и агент используют один и тот же login. Клиент может случайно попасть на агентский интерфейс. Нужна чёткая граница.

**Что входит:**

Backend:
- `POST /api/v1/auth/register` — публичная регистрация (только роль `user`, без доступа к агентскому UI)
- Email-подтверждение регистрации (Celery task, токен с TTL 24 ч)
- `POST /api/v1/auth/verify-email?token=` — подтвердить email
- `POST /api/v1/auth/resend-verification` — повторная отправка

Frontend:
- Отдельный layout `/portal/*` — упрощённый, без Sidebar агента
- `/portal/login` — вход только для клиентов (роль `user`); если агент/admin логинится здесь → редирект на `/login`
- `/login` — вход только для агентов и администраторов; если `user` логинится → редирект на `/portal`
- `/portal/register` — форма регистрации: email, имя, пароль
- `/portal/verify` — страница "проверьте почту" + ввод кода
- `/portal/tickets` — список своих заявок (упрощённый)
- `/portal/tickets/{id}` — только публичные комментарии и статус
- `/portal/tickets/new` — форма создания (тема + описание + тип)

**Ключевые файлы:**
```
backend/app/api/v1/auth.py  (register, verify-email)
frontend/src/router/index.tsx  (разделение ролей)
frontend/src/pages/Portal/  (новые страницы)
frontend/src/components/Portal/PortalLayout/
```

**Зависимости:** 02, 05, 11.

---

## Миссия 18 — Enhanced SLA Reports (Детальные отчёты SLA)

**Цель:** Добавить детальные отчёты по нарушениям SLA: кто нарушил, на сколько, рейтинг отделов и сотрудников.

**Что входит:**

Backend:
- `GET /api/v1/reports/sla-violations` — список заявок с нарушенным SLA:
  - кто исполнитель, отдел, насколько превышен дедлайн (в часах), приоритет
  - фильтры: date_from, date_to, department_id, assignee_id
- `GET /api/v1/reports/agent-performance` — рейтинг агентов:
  - всего заявок, закрыто вовремя / с нарушением SLA, среднее время решения (ч)
- `GET /api/v1/reports/department-performance` — рейтинг отделов: аналогичная статистика

Frontend:
- Новая вкладка "SLA-нарушения" на странице Reports:
  - таблица нарушений (номер, заголовок, исполнитель, дедлайн, превышение в часах)
  - сортировка по превышению
- Вкладка "Рейтинг агентов":
  - таблица с Statistic Badge (✅ % в срок, ⚠️ % нарушений)
- Вкладка "Рейтинг отделов": аналогично

**Ключевые файлы:**
```
backend/app/api/v1/reports.py  (новые эндпоинты)
backend/app/schemas/report.py  (AgentPerformance, DeptPerformance, SLAViolation)
frontend/src/pages/Reports/  (новые вкладки)
```

**Как считается статистика (справка):**
- Среднее время решения: `AVG(closed_at - created_at)` для resolved/cancelled заявок
- SLA compliance: `COUNT(sla_violated=False) / COUNT(*) * 100` за период
- Просроченные: заявки где `sla_violated=True` или (`closed_at > sla_deadline` и `status IN (resolved, cancelled)`)

**Зависимости:** 09, 14.

---

## Миссия 19 — Email Channel (Email-канал)

**Цель:** Принимать заявки по электронной почте (входящие письма → заявки) и отвечать клиентам через email (публичные комментарии → письма).

**Что входит:**

Backend:
- Интеграция с SendGrid Inbound Parse (webhook `POST /api/v1/webhooks/email/inbound`)
- Парсинг входящего письма → поиск/создание пользователя по `From:` → создание заявки или добавление комментария (по `In-Reply-To` или `References` заголовку)
- Поле `email_message_id` в таблице `tickets` для трекинга треда
- Celery task: при публичном комментарии агента → отправить email клиенту с цитированием
- Email-шаблоны: ответ на заявку, создание через email

Frontend:
- Значок "создана по email" в карточке заявки
- Настройки (вкладка Email в Settings): адрес входящей почты, тестовый send

**Зависимости:** 08, 05.

---

## Миссия 20 — VK Bot

**Цель:** Телеграм/VK-бот для клиентов — создать заявку, узнать статус, получить уведомление.

**Что входит:**

Backend:
- Webhook `POST /api/v1/webhooks/vk` — обработка событий VK API
- Команды бота: `/start`, `/new <тема>`, `/status <номер>`, `/list`
- При смене статуса заявки — уведомление в VK пользователю (Celery task)
- Таблица `vk_bindings` — связь `vk_user_id` ↔ `User`

Frontend:
- Страница настроек: QR-код для привязки VK-аккаунта
- Значок VK у заявок созданных через бот

**Зависимости:** 17, 08.

---

## Итог: порядок выполнения

```
MVP (01–14) → 15 (Merge) → 16 (Tags+Notes) → 17 (Portal) → 18 (SLA Reports) → 19 (Email) → 20 (VK)
```

**Минимальный рабочий контур (demo-ready):** миссии 01–05, 11–12  
**Полный MVP:** миссии 01–14  
**Полная система по SD.docx:** миссии 01–20
