# Архитектура системы Service Desk

## Содержание

1. [Обзор архитектуры](#1-обзор-архитектуры)
2. [ERD-диаграмма](#2-erd-диаграмма)
3. [REST API](#3-rest-api)
4. [Компонентная структура фронтенда](#4-компонентная-структура-фронтенда)
5. [Workflow заявки](#5-workflow-заявки)
6. [SLA и эскалация](#6-sla-и-эскалация)
7. [Файловое хранилище](#7-файловое-хранилище)
8. [Real-time уведомления (SSE)](#8-real-time-уведомления-sse)
9. [Структура проекта](#9-структура-проекта)
10. [Docker Compose](#10-docker-compose)

---

## 1. Обзор архитектуры

```
┌─────────────────────────────────────────────────────────────────┐
│                        NGINX (reverse proxy)                    │
│              /api  →  backend:8000                              │
│              /     →  frontend:3000 (SPA)                       │
│              /uploads → static files                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
          ┌─────────────────┴──────────────────┐
          │                                    │
   ┌──────▼──────┐                    ┌────────▼───────┐
   │   FastAPI   │                    │  React 18 SPA  │
   │  (backend)  │                    │  (TypeScript   │
   │  port 8000  │                    │   + antd)      │
   └──────┬──────┘                    └────────────────┘
          │
   ┌──────┴──────────────────────────────┐
   │                                     │
┌──▼──────────┐   ┌──────────┐   ┌──────▼──────┐
│ PostgreSQL  │   │  Redis   │   │   Celery    │
│  (данные)   │   │ (broker  │   │  Worker     │
│             │   │ + cache) │   │ (email, SLA)│
└─────────────┘   └──────────┘   └─────────────┘
```

**Принципы:**
- Stateless backend — аутентификация через JWT (access 15 мин + refresh 7 дней)
- Redis — брокер задач Celery + хранение refresh-токенов в блок-листе при logout
- SSE — push-уведомления от сервера к клиенту (без WebSocket)
- Файлы — локально в `uploads/`, путь в БД; абстракция StorageBackend позволяет заменить на MinIO

---

## 2. ERD-диаграмма

```mermaid
erDiagram
    User {
        int id PK
        string email UK
        string username UK
        string password_hash
        string full_name
        enum role "admin | agent | user"
        int department_id FK
        bool is_active
        datetime created_at
        datetime updated_at
    }

    Department {
        int id PK
        string name UK
        string description
        datetime created_at
    }

    TicketType {
        int id PK
        string name
        string service_type
        string work_direction
        int default_department_id FK
        bool is_active
    }

    Priority {
        int id PK
        string name "low | normal | high | critical"
        int sla_hours "24 | 8 | 4 | 1"
        string color_hex
    }

    Ticket {
        int id PK
        string number UK "SD-YYYY-XXXXX"
        string title
        text description
        enum status "new | in_progress | waiting_info | resolved | cancelled"
        int priority_id FK
        int type_id FK
        int requester_id FK
        int assignee_id FK "nullable"
        int department_id FK "nullable"
        datetime sla_deadline
        datetime sla_paused_at "nullable — когда перешёл в waiting_info"
        int sla_extra_minutes "накопленное время паузы"
        bool sla_violated
        datetime created_at
        datetime updated_at
        datetime closed_at "nullable"
    }

    Comment {
        int id PK
        int ticket_id FK
        int author_id FK
        text body
        bool is_internal "виден только агентам"
        datetime created_at
        datetime updated_at
    }

    Attachment {
        int id PK
        int ticket_id FK
        int comment_id FK "nullable"
        string original_filename
        string stored_path
        int size_bytes
        string mimetype
        int uploaded_by FK
        datetime created_at
    }

    TicketHistory {
        int id PK
        int ticket_id FK
        int user_id FK "кто совершил действие"
        string event_type "status_changed | assigned | priority_changed | commented | etc"
        jsonb payload "old/new значения"
        datetime created_at
    }

    Notification {
        int id PK
        int user_id FK
        int ticket_id FK
        string event_type
        string message
        bool is_read
        datetime created_at
    }

    SavedFilter {
        int id PK
        int user_id FK
        string name
        jsonb filter_params
        datetime created_at
    }

    Department ||--o{ User : "сотрудники"
    Department ||--o{ TicketType : "маршрутизация по умолчанию"
    Department ||--o{ Ticket : "назначен отдел"
    Priority ||--o{ Ticket : "приоритет"
    TicketType ||--o{ Ticket : "тип"
    User ||--o{ Ticket : "создал (requester)"
    User ||--o{ Ticket : "исполнитель (assignee)"
    Ticket ||--o{ Comment : "комментарии"
    Ticket ||--o{ Attachment : "вложения"
    Ticket ||--o{ TicketHistory : "история"
    Ticket ||--o{ Notification : "уведомления"
    User ||--o{ Comment : "автор"
    User ||--o{ Notification : "получатель"
    User ||--o{ SavedFilter : "сохранённые фильтры"
    User ||--o{ Attachment : "загрузил"
    User ||--o{ TicketHistory : "совершил действие"
    Comment ||--o{ Attachment : "вложения к комментарию"
```

---

## 3. REST API

**Базовый URL:** `/api/v1`  
**Аутентификация:** `Authorization: Bearer <access_token>`  
**Формат:** JSON (multipart/form-data для загрузки файлов)

---

### 3.1 Аутентификация `/auth`

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| `POST` | `/auth/login` | Вход по логину/паролю | Все |
| `POST` | `/auth/refresh` | Обновление access токена | Все |
| `POST` | `/auth/logout` | Выход (инвалидация refresh токена) | Все |

**POST /auth/login**
```json
// Request
{ "username": "john.doe", "password": "secret" }

// Response 200
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "full_name": "John Doe", "role": "agent" }
}
```

---

### 3.2 Пользователи `/users`

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| `GET` | `/users` | Список пользователей | admin |
| `POST` | `/users` | Создать пользователя | admin |
| `GET` | `/users/me` | Текущий пользователь | все |
| `PUT` | `/users/me` | Изменить свой профиль | все |
| `GET` | `/users/{id}` | Профиль пользователя | admin, agent |
| `PUT` | `/users/{id}` | Редактировать пользователя | admin |
| `PATCH` | `/users/{id}/activate` | Активировать/деактивировать | admin |

**Query params GET /users:** `?department_id=&role=&is_active=&search=&page=&page_size=`

---

### 3.3 Отделы `/departments`

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| `GET` | `/departments` | Список отделов | все |
| `POST` | `/departments` | Создать отдел | admin |
| `GET` | `/departments/{id}` | Отдел + его агенты | admin, agent |
| `PUT` | `/departments/{id}` | Редактировать | admin |
| `DELETE` | `/departments/{id}` | Удалить (если нет заявок) | admin |

---

### 3.4 Типы заявок `/ticket-types`

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| `GET` | `/ticket-types` | Список типов | все |
| `POST` | `/ticket-types` | Создать тип | admin |
| `GET` | `/ticket-types/{id}` | Тип заявки | все |
| `PUT` | `/ticket-types/{id}` | Редактировать | admin |
| `DELETE` | `/ticket-types/{id}` | Удалить | admin |

---

### 3.5 Приоритеты `/priorities`

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| `GET` | `/priorities` | Список приоритетов с SLA | все |

---

### 3.6 Заявки `/tickets`

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| `GET` | `/tickets` | Список заявок (с фильтрами) | все* |
| `POST` | `/tickets` | Создать заявку | все |
| `GET` | `/tickets/{id}` | Карточка заявки | все* |
| `PUT` | `/tickets/{id}` | Редактировать заявку | admin, agent |
| `PATCH` | `/tickets/{id}/status` | Изменить статус | по правилам workflow |
| `PATCH` | `/tickets/{id}/assign` | Назначить исполнителя/отдел | admin, agent |
| `PATCH` | `/tickets/{id}/priority` | Изменить приоритет | admin, agent |
| `GET` | `/tickets/{id}/history` | История действий | все* |

*user видит только свои заявки, agent — заявки своего отдела + назначенные на него, admin — все.

**Query params GET /tickets:**
```
?status=new,in_progress
&priority_id=1,2
&type_id=3
&department_id=1
&assignee_id=5
&requester_id=10
&sla_violated=true
&search=текст поиска
&date_from=2026-01-01
&date_to=2026-12-31
&sort_by=created_at
&sort_order=desc
&page=1
&page_size=20
```

**Response GET /tickets (paginated):**
```json
{
  "items": [ { "id": 1, "number": "SD-2026-00001", ... } ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "pages": 8
}
```

**POST /tickets:**
```json
// Request
{
  "title": "Не работает принтер",
  "description": "Принтер HP в кабинете 305 не печатает",
  "priority_id": 2,
  "type_id": 4
}

// Response 201
{
  "id": 1,
  "number": "SD-2026-00001",
  "status": "new",
  "sla_deadline": "2026-05-07T17:00:00Z",
  ...
}
```

**PATCH /tickets/{id}/status:**
```json
// Request
{ "status": "in_progress", "comment": "Беру в работу" }
```

**PATCH /tickets/{id}/assign:**
```json
// Request
{ "assignee_id": 5, "department_id": 2 }
```

---

### 3.7 Комментарии `/tickets/{id}/comments`

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| `GET` | `/tickets/{id}/comments` | Список комментариев | все* |
| `POST` | `/tickets/{id}/comments` | Добавить комментарий | все |
| `PUT` | `/tickets/{id}/comments/{cid}` | Редактировать (свой, <5 мин) | автор |
| `DELETE` | `/tickets/{id}/comments/{cid}` | Удалить | admin, автор |

*is_internal комментарии видны только агентам и администраторам.

```json
// POST Request
{
  "body": "Уточните модель принтера",
  "is_internal": false
}
```

---

### 3.8 Вложения

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| `POST` | `/tickets/{id}/attachments` | Загрузить файл к заявке | все |
| `POST` | `/tickets/{id}/comments/{cid}/attachments` | Загрузить к комментарию | все |
| `GET` | `/attachments/{id}` | Скачать файл | все* |
| `DELETE` | `/attachments/{id}` | Удалить файл | admin, загрузивший |

*Проверка доступа к заявке перед выдачей файла.

**POST /tickets/{id}/attachments** — `multipart/form-data`, поле `file`, максимум 10 МБ.

---

### 3.9 Уведомления `/notifications`

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| `GET` | `/notifications` | Список уведомлений текущего пользователя | все |
| `PATCH` | `/notifications/{id}/read` | Пометить прочитанным | владелец |
| `PATCH` | `/notifications/read-all` | Все прочитаны | все |

**Query params:** `?is_read=false&page=1&page_size=20`

---

### 3.10 SSE-поток `/events`

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/events` | SSE-поток уведомлений для текущего пользователя |

```
Accept: text/event-stream

data: {"type": "ticket_status_changed", "ticket_id": 1, "number": "SD-2026-00001", "new_status": "in_progress"}

data: {"type": "ticket_assigned", "ticket_id": 2, "assignee": "John Doe"}

data: {"type": "new_comment", "ticket_id": 1, "author": "Jane"}

data: {"type": "sla_warning", "ticket_id": 5, "minutes_left": 30}
```

---

### 3.11 Отчёты `/reports`

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| `GET` | `/reports/tickets-count` | Кол-во заявок за период | admin, agent |
| `GET` | `/reports/by-status` | Распределение по статусам | admin, agent |
| `GET` | `/reports/avg-resolution-time` | Среднее время обработки | admin, agent |
| `GET` | `/reports/sla-compliance` | % заявок без нарушения SLA | admin, agent |
| `GET` | `/reports/export` | Экспорт в CSV/Excel | admin, agent |

**Query params:** `?date_from=&date_to=&department_id=&type_id=&format=csv|xlsx`

---

### 3.12 Сохранённые фильтры `/filters`

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| `GET` | `/filters` | Мои сохранённые фильтры | все |
| `POST` | `/filters` | Сохранить фильтр | все |
| `DELETE` | `/filters/{id}` | Удалить фильтр | владелец |

```json
// POST Request
{
  "name": "Критичные просроченные",
  "filter_params": { "priority_id": [4], "sla_violated": true }
}
```

---

## 4. Компонентная структура фронтенда

```
App
├── Router
│   ├── PublicRoute
│   │   └── LoginPage
│   └── PrivateRoute
│       ├── Layout
│       │   ├── Sidebar (навигация, роль-зависимая)
│       │   ├── Header (уведомления, профиль)
│       │   │   └── NotificationBell
│       │   │       └── NotificationDropdown
│       │   └── ContentArea
│       │
│       ├── DashboardPage
│       │   ├── StatsCards (мои заявки, просроченные, ожидают)
│       │   ├── RecentTicketsTable
│       │   └── SLAViolationsAlert
│       │
│       ├── TicketsListPage
│       │   ├── FilterPanel
│       │   │   ├── StatusFilter
│       │   │   ├── PriorityFilter
│       │   │   ├── DateRangePicker
│       │   │   ├── AssigneeSelect
│       │   │   └── SavedFiltersMenu
│       │   ├── TicketsTable
│       │   │   ├── TicketNumberCell
│       │   │   ├── PriorityBadge
│       │   │   ├── StatusBadge
│       │   │   └── SLACountdown
│       │   └── Pagination
│       │
│       ├── CreateTicketPage
│       │   └── TicketForm
│       │       ├── TitleInput
│       │       ├── DescriptionEditor
│       │       ├── TypeSelect (→ автовыбор отдела)
│       │       ├── PrioritySelect (→ показ SLA дедлайна)
│       │       └── AttachmentUpload
│       │
│       ├── TicketDetailPage
│       │   ├── TicketHeader
│       │   │   ├── TicketNumber + Title
│       │   │   ├── StatusBadge + StatusChangeDropdown
│       │   │   ├── PriorityBadge
│       │   │   └── SLACountdown (с подсветкой при нарушении)
│       │   ├── TicketMeta
│       │   │   ├── Requester info
│       │   │   ├── Department + AssigneeSelect
│       │   │   └── Dates (создана, дедлайн, закрыта)
│       │   ├── TicketDescription
│       │   ├── AttachmentList
│       │   │   └── AttachmentItem (скачать / удалить)
│       │   ├── ActivityTimeline
│       │   │   └── HistoryItem (статус / назначение / комментарий)
│       │   └── CommentSection
│       │       ├── CommentList
│       │       │   └── CommentItem (тело, автор, дата, is_internal-флаг)
│       │       └── CommentForm
│       │           ├── TextEditor
│       │           ├── InternalToggle (только для агентов)
│       │           └── AttachmentUpload
│       │
│       ├── ReportsPage
│       │   ├── DateRangeSelector
│       │   ├── DepartmentFilter
│       │   ├── TicketsCountChart (столбчатая, по дням/неделям)
│       │   ├── StatusDistributionChart (пирог)
│       │   ├── AvgResolutionTimeChart (по приоритетам)
│       │   ├── SLAComplianceMetric
│       │   └── ExportButton (CSV / Excel)
│       │
│       └── SettingsPage (только admin)
│           ├── UsersTab
│           │   ├── UsersTable
│           │   └── UserFormModal (создать / редактировать)
│           ├── DepartmentsTab
│           │   ├── DepartmentsTable
│           │   └── DepartmentFormModal
│           └── TicketTypesTab
│               ├── TicketTypesTable
│               └── TicketTypeFormModal
```

**Общие (переиспользуемые) компоненты:**

| Компонент | Назначение |
|-----------|-----------|
| `PriorityBadge` | Цветной тег приоритета |
| `StatusBadge` | Тег статуса с цветом |
| `SLACountdown` | Таймер до дедлайна (зелёный / жёлтый / красный) |
| `UserAvatar` | Аватар + имя пользователя |
| `AttachmentUpload` | Drag-and-drop загрузка файлов |
| `ConfirmModal` | Модал подтверждения действия |
| `PageHeader` | Заголовок страницы с хлебными крошками |
| `EmptyState` | Заглушка для пустых списков |

**Кастомные хуки:**

| Хук | Назначение |
|-----|-----------|
| `useSSE(url)` | Подписка на SSE-поток, переподключение при обрыве |
| `useTickets(filters)` | Загрузка и кеш списка заявок |
| `useTicket(id)` | Загрузка карточки заявки |
| `usePermissions()` | Проверка прав текущего пользователя |
| `useNotifications()` | Список уведомлений + счётчик непрочитанных |

---

## 5. Workflow заявки

### 5.1 Диаграмма состояний

```mermaid
stateDiagram-v2
    [*] --> new : Создание заявки (любой пользователь)

    new --> in_progress : Взять в работу
    new --> cancelled : Отменить

    in_progress --> waiting_info : Запросить информацию\n(SLA приостанавливается)
    in_progress --> resolved : Выполнить
    in_progress --> cancelled : Отменить

    waiting_info --> in_progress : Клиент ответил\n(SLA возобновляется)
    waiting_info --> cancelled : Отменить

    resolved --> in_progress : Переоткрыть

    resolved --> [*]
    cancelled --> [*]
```

### 5.2 Матрица переходов

| Переход | Кто может | Комментарий обязателен |
|---------|-----------|----------------------|
| `new → in_progress` | agent, admin | нет |
| `new → cancelled` | admin, requester | рекомендован |
| `in_progress → waiting_info` | agent, admin | да (что требуется) |
| `in_progress → resolved` | agent, admin | нет |
| `in_progress → cancelled` | agent, admin | рекомендован |
| `waiting_info → in_progress` | requester, agent, admin | нет |
| `waiting_info → cancelled` | agent, admin | рекомендован |
| `resolved → in_progress` | requester (≤72ч), admin | да (причина) |

### 5.3 Автоматические действия при переходах

| Событие | Действие |
|---------|----------|
| Создание заявки | Автоназначение отдела по типу заявки; расчёт SLA дедлайна; email requester'у |
| `→ in_progress` | Email requester'у о начале работ; запись в историю |
| `→ waiting_info` | Пауза SLA таймера (`sla_paused_at = now()`); email requester'у |
| `waiting_info → in_progress` | Возобновление SLA (добавить паузу в `sla_extra_minutes`); email агенту |
| `→ resolved` | `closed_at = now()`; email requester'у |
| `→ cancelled` | `closed_at = now()`; email всем участникам |
| Назначение исполнителя | Email новому исполнителю; SSE-уведомление |
| Новый комментарий | SSE + email (если `is_internal=false` — всем; если `true` — только агентам) |

---

## 6. SLA и эскалация

### 6.1 Расчёт дедлайна

**Рабочие часы:** пн–пт, 09:00–18:00 (9 рабочих часов в день).

Алгоритм:
1. `start = max(created_at, следующий_рабочий_момент)`
2. Прибавить `sla_hours` рабочих часов, пропуская нерабочее время и выходные
3. `sla_deadline = полученная_дата`

При переходе в `waiting_info`:
- Сохранить `sla_paused_at = now()`

При возврате в `in_progress`:
- `pause_duration = now() - sla_paused_at`
- `sla_extra_minutes += pause_duration.total_minutes()`
- `sla_deadline += timedelta(minutes=sla_extra_minutes)` (пересчёт)
- `sla_paused_at = null`

### 6.2 Celery Beat задачи

| Задача | Расписание | Действие |
|--------|-----------|----------|
| `check_sla_warnings` | каждые 15 мин | SSE + email за 1ч до дедлайна |
| `check_sla_violations` | каждые 10 мин | Пометить `sla_violated=true`, эскалация |
| `escalate_overdue` | каждые 30 мин | Email руководителю отдела при нарушении >2ч |

### 6.3 Визуальные индикаторы на фронтенде

| Состояние | Индикатор |
|-----------|----------|
| > 50% времени осталось | Зелёный таймер |
| 25–50% времени осталось | Жёлтый таймер |
| < 25% времени осталось | Оранжевый таймер |
| SLA нарушен | Красный счётчик "просрочено на Xч Yм" |
| Статус `waiting_info` | Серый "SLA на паузе" |

---

## 7. Файловое хранилище

**Стратегия:** абстракция `StorageBackend` позволяет переключить хранилище через переменную окружения без изменения кода бизнес-логики.

```
STORAGE_BACKEND=local   # uploads/ на сервере
STORAGE_BACKEND=minio   # S3-совместимое MinIO
```

**Структура папки `uploads/` (local backend):**
```
uploads/
└── tickets/
    └── {ticket_id}/
        ├── {uuid}_{original_filename}
        └── comments/
            └── {comment_id}/
                └── {uuid}_{original_filename}
```

**Ограничения:**
- Максимум 10 МБ на файл
- Разрешённые MIME-типы: `image/*`, `application/pdf`, `application/msword`, `application/vnd.openxmlformats-officedocument.*`, `text/plain`
- Файлы отдаются через Nginx (`X-Accel-Redirect`) — Python не участвует в стриминге

---

## 8. Real-time уведомления (SSE)

**Схема:**
```
Client                    FastAPI                   Redis
  |                          |                         |
  |── GET /api/v1/events ──→ |                         |
  |   (держит соединение)    |── SUBSCRIBE channel ──→ |
  |                          |                         |
  |   (другой запрос)        |                         |
  |── PATCH /tickets/1/status|                         |
  |                          |── PUBLISH event ──────→ |
  |                          |                         |
  |← data: {event} ─────────|←── message ─────────────|
```

**Каналы Redis:**
- `sse:user:{user_id}` — персональные уведомления пользователя
- `sse:department:{dept_id}` — уведомления для агентов отдела

**Типы событий SSE:**

| Тип | Получатели | Данные |
|-----|-----------|--------|
| `ticket_created` | агенты отдела, admin | ticket summary |
| `ticket_status_changed` | requester, assignee, admin | ticket_id, old/new status |
| `ticket_assigned` | новый исполнитель | ticket_id, assignee |
| `new_comment` | все участники заявки | ticket_id, author, is_internal |
| `sla_warning` | assignee, admin | ticket_id, minutes_left |
| `sla_violated` | assignee, admin, dept head | ticket_id |

**Переподключение:** клиент использует `EventSource` с `Last-Event-ID` для продолжения после разрыва.

---

## 9. Структура проекта

### Backend

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, подключение роутеров
│   ├── config.py                # Settings (pydantic-settings, .env)
│   ├── database.py              # SQLAlchemy engine, SessionLocal
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py        # Агрегация всех роутеров
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── departments.py
│   │       ├── ticket_types.py
│   │       ├── priorities.py
│   │       ├── tickets.py
│   │       ├── comments.py
│   │       ├── attachments.py
│   │       ├── notifications.py
│   │       ├── reports.py
│   │       ├── filters.py
│   │       └── events.py        # SSE endpoint
│   │
│   ├── models/                  # SQLAlchemy ORM модели
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── department.py
│   │   ├── ticket_type.py
│   │   ├── priority.py
│   │   ├── ticket.py
│   │   ├── comment.py
│   │   ├── attachment.py
│   │   ├── ticket_history.py
│   │   ├── notification.py
│   │   └── saved_filter.py
│   │
│   ├── schemas/                 # Pydantic схемы (request/response)
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── department.py
│   │   ├── ticket.py
│   │   ├── comment.py
│   │   ├── attachment.py
│   │   ├── notification.py
│   │   └── report.py
│   │
│   ├── services/                # Бизнес-логика
│   │   ├── auth_service.py      # JWT, hashing
│   │   ├── ticket_service.py    # CRUD + workflow переходы
│   │   ├── sla_service.py       # Расчёт дедлайна, рабочие часы
│   │   ├── notification_service.py  # Создание уведомлений + SSE publish
│   │   ├── email_service.py     # Jinja2 рендер + отправка через SendGrid
│   │   └── storage/
│   │       ├── base.py          # Абстрактный StorageBackend
│   │       ├── local.py         # Локальная файловая система
│   │       └── minio.py         # MinIO / S3 (для будущего)
│   │
│   ├── tasks/                   # Celery задачи
│   │   ├── celery_app.py        # Celery + Beat расписание
│   │   ├── email_tasks.py       # send_email_task
│   │   └── sla_tasks.py         # check_sla_warnings, check_sla_violations
│   │
│   └── utils/
│       ├── security.py          # create_token, verify_token
│       ├── permissions.py       # Декораторы проверки ролей
│       ├── pagination.py        # Paged response helper
│       └── ticket_number.py     # Генерация SD-YYYY-XXXXX
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/               # Миграции
│
├── templates/                   # Jinja2 HTML email шаблоны
│   ├── base_email.html
│   ├── ticket_created.html
│   ├── ticket_assigned.html
│   ├── ticket_status_changed.html
│   ├── new_comment.html
│   └── sla_warning.html
│
├── uploads/                     # Локальное хранилище файлов
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_tickets.py
│   └── test_sla.py
│
├── requirements.txt
├── Dockerfile
├── .env.example
└── alembic.ini
```

### Frontend

```
frontend/
├── public/
│   └── favicon.ico
│
├── src/
│   ├── api/                     # HTTP клиент
│   │   ├── client.ts            # Axios instance + interceptors (token refresh)
│   │   ├── auth.ts
│   │   ├── tickets.ts
│   │   ├── users.ts
│   │   ├── departments.ts
│   │   ├── notifications.ts
│   │   └── reports.ts
│   │
│   ├── components/
│   │   ├── common/
│   │   │   ├── Layout/
│   │   │   ├── PriorityBadge/
│   │   │   ├── StatusBadge/
│   │   │   ├── SLACountdown/
│   │   │   ├── NotificationBell/
│   │   │   ├── AttachmentUpload/
│   │   │   ├── UserAvatar/
│   │   │   └── ConfirmModal/
│   │   │
│   │   ├── tickets/
│   │   │   ├── TicketForm/
│   │   │   ├── TicketTable/
│   │   │   ├── FilterPanel/
│   │   │   ├── CommentList/
│   │   │   ├── CommentForm/
│   │   │   ├── AttachmentList/
│   │   │   └── ActivityTimeline/
│   │   │
│   │   └── reports/
│   │       ├── TicketsCountChart/
│   │       ├── StatusDistributionChart/
│   │       └── AvgResolutionChart/
│   │
│   ├── pages/
│   │   ├── Login/
│   │   ├── Dashboard/
│   │   ├── Tickets/
│   │   │   ├── TicketsList/
│   │   │   ├── TicketDetail/
│   │   │   └── CreateTicket/
│   │   ├── Reports/
│   │   └── Settings/
│   │       ├── Users/
│   │       ├── Departments/
│   │       └── TicketTypes/
│   │
│   ├── store/                   # Zustand (или Context API)
│   │   ├── authStore.ts         # user, tokens, isAuthenticated
│   │   └── notificationStore.ts # unread count, list
│   │
│   ├── hooks/
│   │   ├── useSSE.ts            # EventSource с авто-переподключением
│   │   ├── useTickets.ts
│   │   ├── useTicket.ts
│   │   ├── usePermissions.ts    # can(action, resource)
│   │   └── useNotifications.ts
│   │
│   ├── types/
│   │   ├── ticket.ts
│   │   ├── user.ts
│   │   ├── report.ts
│   │   └── common.ts            # Pagination, ApiError
│   │
│   ├── utils/
│   │   ├── sla.ts               # formatSLARemaining, getSLAColor
│   │   └── date.ts              # форматирование дат
│   │
│   ├── router/
│   │   └── index.tsx            # Routes + PrivateRoute + RoleRoute
│   │
│   ├── App.tsx
│   └── main.tsx
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── Dockerfile
└── nginx.conf                   # SPA: try_files $uri /index.html
```

---

## 10. Docker Compose

```
Контейнеры:
┌─────────────┐  ┌─────────────┐  ┌──────────────┐
│    nginx    │  │   backend   │  │   frontend   │
│   :80/:443  │  │    :8000    │  │    :3000     │
└──────┬──────┘  └──────┬──────┘  └──────────────┘
       │                │
       │         ┌──────┴───────────────────┐
       │         │                          │
       │  ┌──────▼──────┐       ┌───────────▼──┐
       │  │ PostgreSQL  │       │    Redis     │
       │  │    :5432    │       │    :6379     │
       │  └─────────────┘       └──────────────┘
       │                                │
       │                        ┌───────▼──────┐
       │                        │    Celery    │
       │                        │    Worker    │
       │                        └──────────────┘

Сервисы: nginx, backend, frontend, postgres, redis, celery_worker, celery_beat
Volumes: postgres_data, redis_data, uploads_data
Networks: app_network (internal bridge)
```

**Переменные окружения (`.env`):**

| Переменная | Назначение |
|-----------|-----------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@postgres/db` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `SECRET_KEY` | JWT подпись |
| `SENDGRID_API_KEY` | Ключ SendGrid |
| `MAIL_FROM` | Адрес отправителя |
| `STORAGE_BACKEND` | `local` или `minio` |
| `UPLOAD_PATH` | `/app/uploads` |
| `MAX_FILE_SIZE_MB` | `10` |
| `CORS_ORIGINS` | `http://localhost,http://your-domain` |
