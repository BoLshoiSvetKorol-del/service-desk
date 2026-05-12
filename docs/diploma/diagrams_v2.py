# -*- coding: utf-8 -*-
"""
diagrams_v2.py
Генерирует все диаграммы дипломной работы через Kroki API.
PlantUML — UML-диаграммы (авто-расстановка, нет перекрытий).
Graphviz — ER и DFD (авто-layout dot/neato).
Matplotlib — только IDEF0 (нестандартная нотация).
Файлы сохраняются в docs/diploma/diagrams/.
"""

import os
import time
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches

OUT    = r'Z:\ProjectX\docs\diploma\diagrams'
KROKI  = 'http://localhost:8080'   # локальный Docker-контейнер yuzutech/kroki
FONT   = 'DejaVu Sans'
os.makedirs(OUT, exist_ok=True)


# ─── helpers ──────────────────────────────────────────────────────────────────

def render(kind: str, src: str, fname: str, retries: int = 3) -> None:
    """POST diagram source to local Kroki, save PNG."""
    url = f'{KROKI}/{kind}/png'
    for attempt in range(retries):
        try:
            r = requests.post(url, data=src.encode('utf-8'),
                              headers={'Content-Type': 'text/plain'},
                              timeout=60)
            if r.status_code != 200:
                raise RuntimeError(f'HTTP {r.status_code}: {r.text[:300]}')
            with open(os.path.join(OUT, fname), 'wb') as f:
                f.write(r.content)
            print(f'  + {fname}')
            time.sleep(0.3)
            return
        except Exception as exc:
            if attempt == retries - 1:
                print(f'  FAIL {fname}: {exc}')
                raise
            time.sleep(3)


def save_mpl(fig, name: str) -> None:
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f'  + {name}')


# ══════════════════════════════════════════════════════════════════════════════
# 01 — ER-диаграмма концептуального уровня (Graphviz)
# ══════════════════════════════════════════════════════════════════════════════
def gen_01():
    src = r"""
digraph ER_Conceptual {
    graph [
        rankdir=TB
        splines=polyline
        nodesep=1.0
        ranksep=1.4
        fontname="DejaVu Sans"
        label="ER-диаграмма концептуального уровня"
        labelloc=t
        fontsize=20
        bgcolor=white
        pad=0.6
    ]
    node [
        shape=box style="filled,rounded"
        fillcolor="#2E5FA3" fontcolor=white
        fontname="DejaVu Sans" fontsize=13
        margin="0.3,0.12" penwidth=2
    ]
    edge [
        fontname="DejaVu Sans" fontsize=10
        color="#1a3a6b" penwidth=1.6
        arrowhead=vee
    ]

    { rank=same; Departments; Users }
    { rank=same; Priorities; Tickets; TicketTypes }
    { rank=same; Comments; Attachments; TicketHistory }
    { rank=same; Tags; Notifications; SavedFilters }

    Departments  [label="Departments"]
    Users        [label="Users"]
    Priorities   [label="Priorities"]
    Tickets      [label="Tickets"]
    TicketTypes  [label="TicketTypes"]
    Comments     [label="Comments"]
    Attachments  [label="Attachments"]
    TicketHistory[label="TicketHistory"]
    Tags         [label="Tags"]
    Notifications[label="Notifications"]
    SavedFilters [label="SavedFilters"]

    Departments -> Users
        [label="  1:M\n  содержит  "]
    Users -> Tickets
        [label="  1:M\n  создаёт  "]
    Users -> Tickets
        [label="  0..1:M\n  исполнитель  "
         style=dashed color="#888888" fontcolor="#888888"]
    Departments -> Tickets
        [label="  0..1:M\n  ответ. отдел  "
         style=dashed color="#888888" fontcolor="#888888"]
    Priorities -> Tickets
        [label="  1:M\n  определяет  "]
    TicketTypes -> Tickets
        [label="  1:M\n  классифицирует  "]
    Tickets -> Comments
        [label="  1:M\n  имеет  "]
    Tickets -> Attachments
        [label="  1:M\n  имеет  "]
    Tickets -> TicketHistory
        [label="  1:M\n  фиксирует  "]
    Tickets -> Tags
        [label="  M:M\n  тегирует  "
         dir=both color="#C00000" fontcolor="#C00000" penwidth=2.2]
    Users -> Notifications
        [label="  1:M\n  получает  "]
    Users -> SavedFilters
        [label="  1:M\n  сохраняет  "]
}
"""
    render('graphviz', src, '01_er_conceptual.png')


# ══════════════════════════════════════════════════════════════════════════════
# 02 — Логическая модель БД (Graphviz HTML-таблицы)
# ══════════════════════════════════════════════════════════════════════════════
def gen_02():
    src = r"""
digraph ER_Logical {
    graph [
        rankdir=LR splines=polyline
        nodesep=0.6 ranksep=2.2
        fontname="DejaVu Sans"
        label="Логическая модель базы данных"
        labelloc=t fontsize=18 bgcolor=white pad=0.5
    ]
    node [shape=none margin=0 fontname="DejaVu Sans" fontsize=10]
    edge [fontname="DejaVu Sans" fontsize=9 color="#6B6B6B" penwidth=1.5 arrowhead=vee]

    /* ── Tables ─────────────────────────────────────────────────────── */

    users [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
<TR><TD BGCOLOR="#2E5FA3"><FONT COLOR="white"><B>users</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="id"><FONT COLOR="#003070"><B>PK id : SERIAL</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT">   email : VARCHAR(255)</TD></TR>
<TR><TD ALIGN="LEFT">   username : VARCHAR(100)</TD></TR>
<TR><TD ALIGN="LEFT">   password_hash : VARCHAR</TD></TR>
<TR><TD ALIGN="LEFT">   full_name : VARCHAR</TD></TR>
<TR><TD ALIGN="LEFT">   role : ENUM</TD></TR>
<TR><TD ALIGN="LEFT" PORT="dept_id">FK department_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT">   is_active : BOOLEAN</TD></TR>
<TR><TD ALIGN="LEFT">   is_email_verified : BOOLEAN</TD></TR>
<TR><TD ALIGN="LEFT">   created_at : TIMESTAMPTZ</TD></TR>
</TABLE>>]

    departments [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
<TR><TD BGCOLOR="#2E5FA3"><FONT COLOR="white"><B>departments</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="id"><FONT COLOR="#003070"><B>PK id : SERIAL</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT">   name : VARCHAR(200)</TD></TR>
<TR><TD ALIGN="LEFT">   description : TEXT</TD></TR>
<TR><TD ALIGN="LEFT">   is_active : BOOLEAN</TD></TR>
</TABLE>>]

    priorities [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
<TR><TD BGCOLOR="#2E5FA3"><FONT COLOR="white"><B>priorities</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="id"><FONT COLOR="#003070"><B>PK id : SERIAL</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT">   name : VARCHAR(50)</TD></TR>
<TR><TD ALIGN="LEFT">   sla_hours : FLOAT</TD></TR>
<TR><TD ALIGN="LEFT">   color : VARCHAR(20)</TD></TR>
<TR><TD ALIGN="LEFT">   sort_order : INTEGER</TD></TR>
</TABLE>>]

    ticket_types [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
<TR><TD BGCOLOR="#2E5FA3"><FONT COLOR="white"><B>ticket_types</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="id"><FONT COLOR="#003070"><B>PK id : SERIAL</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT">   name : VARCHAR(200)</TD></TR>
<TR><TD ALIGN="LEFT" PORT="def_dept">FK default_department_id : INT</TD></TR>
<TR><TD ALIGN="LEFT">   is_active : BOOLEAN</TD></TR>
</TABLE>>]

    tickets [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
<TR><TD BGCOLOR="#2E5FA3"><FONT COLOR="white"><B>tickets</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="id"><FONT COLOR="#003070"><B>PK id : SERIAL</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT">   number : VARCHAR(20)</TD></TR>
<TR><TD ALIGN="LEFT">   title : VARCHAR(500)</TD></TR>
<TR><TD ALIGN="LEFT">   description : TEXT</TD></TR>
<TR><TD ALIGN="LEFT">   status : ENUM</TD></TR>
<TR><TD ALIGN="LEFT" PORT="priority_id">FK priority_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT" PORT="type_id">FK type_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT" PORT="requester_id">FK requester_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT" PORT="assignee_id">FK assignee_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT" PORT="dept_id">FK department_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT" PORT="merged_id">FK merged_into_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT">   sla_deadline : TIMESTAMPTZ</TD></TR>
<TR><TD ALIGN="LEFT">   sla_violated : BOOLEAN</TD></TR>
<TR><TD ALIGN="LEFT">   created_at : TIMESTAMPTZ</TD></TR>
<TR><TD ALIGN="LEFT">   closed_at : TIMESTAMPTZ</TD></TR>
</TABLE>>]

    comments [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
<TR><TD BGCOLOR="#2E5FA3"><FONT COLOR="white"><B>comments</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="id"><FONT COLOR="#003070"><B>PK id : SERIAL</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="ticket_id">FK ticket_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT" PORT="author_id">FK author_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT">   body : TEXT</TD></TR>
<TR><TD ALIGN="LEFT">   is_internal : BOOLEAN</TD></TR>
<TR><TD ALIGN="LEFT">   created_at : TIMESTAMPTZ</TD></TR>
</TABLE>>]

    attachments [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
<TR><TD BGCOLOR="#2E5FA3"><FONT COLOR="white"><B>attachments</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="id"><FONT COLOR="#003070"><B>PK id : SERIAL</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="ticket_id">FK ticket_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT" PORT="comment_id">FK comment_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT">   original_filename : VARCHAR</TD></TR>
<TR><TD ALIGN="LEFT">   stored_path : VARCHAR</TD></TR>
<TR><TD ALIGN="LEFT">   size_bytes : BIGINT</TD></TR>
<TR><TD ALIGN="LEFT">   mimetype : VARCHAR</TD></TR>
<TR><TD ALIGN="LEFT" PORT="uploaded_by">FK uploaded_by : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT">   created_at : TIMESTAMPTZ</TD></TR>
</TABLE>>]

    ticket_history [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
<TR><TD BGCOLOR="#2E5FA3"><FONT COLOR="white"><B>ticket_history</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="id"><FONT COLOR="#003070"><B>PK id : SERIAL</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="ticket_id">FK ticket_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT" PORT="user_id">FK user_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT">   event_type : VARCHAR(50)</TD></TR>
<TR><TD ALIGN="LEFT">   payload : JSONB</TD></TR>
<TR><TD ALIGN="LEFT">   created_at : TIMESTAMPTZ</TD></TR>
</TABLE>>]

    tags [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
<TR><TD BGCOLOR="#2E5FA3"><FONT COLOR="white"><B>tags</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="id"><FONT COLOR="#003070"><B>PK id : SERIAL</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT">   name : VARCHAR(50)</TD></TR>
<TR><TD ALIGN="LEFT">   color : VARCHAR(20)</TD></TR>
</TABLE>>]

    ticket_tags [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
<TR><TD BGCOLOR="#2E5FA3"><FONT COLOR="white"><B>ticket_tags</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="ticket_id">FK ticket_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT" PORT="tag_id">FK tag_id : INTEGER</TD></TR>
</TABLE>>]

    notifications [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
<TR><TD BGCOLOR="#2E5FA3"><FONT COLOR="white"><B>notifications</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="id"><FONT COLOR="#003070"><B>PK id : SERIAL</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="user_id">FK user_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT">   event_type : VARCHAR(50)</TD></TR>
<TR><TD ALIGN="LEFT">   payload : JSONB</TD></TR>
<TR><TD ALIGN="LEFT">   is_read : BOOLEAN</TD></TR>
<TR><TD ALIGN="LEFT">   created_at : TIMESTAMPTZ</TD></TR>
</TABLE>>]

    ticket_notes [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
<TR><TD BGCOLOR="#2E5FA3"><FONT COLOR="white"><B>ticket_notes</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="id"><FONT COLOR="#003070"><B>PK id : SERIAL</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT" PORT="ticket_id">FK ticket_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT" PORT="author_id">FK author_id : INTEGER</TD></TR>
<TR><TD ALIGN="LEFT">   body : TEXT</TD></TR>
<TR><TD ALIGN="LEFT">   created_at : TIMESTAMPTZ</TD></TR>
</TABLE>>]

    /* ── FK edges ──────────────────────────────────────────────────── */
    { rank=same; departments; priorities; ticket_types }
    { rank=same; users }
    { rank=same; tickets }
    { rank=same; comments; attachments; ticket_history; ticket_notes }
    { rank=same; tags; ticket_tags; notifications }

    users:dept_id          -> departments:id
    ticket_types:def_dept  -> departments:id
    tickets:priority_id    -> priorities:id
    tickets:type_id        -> ticket_types:id
    tickets:requester_id   -> users:id
    tickets:assignee_id    -> users:id
    tickets:dept_id        -> departments:id
    tickets:merged_id      -> tickets:id    [style=dashed color="#aaaaaa"]
    comments:ticket_id     -> tickets:id
    comments:author_id     -> users:id
    attachments:ticket_id  -> tickets:id
    attachments:comment_id -> comments:id  [style=dashed color="#aaaaaa"]
    attachments:uploaded_by-> users:id
    ticket_history:ticket_id -> tickets:id
    ticket_history:user_id   -> users:id
    ticket_tags:ticket_id  -> tickets:id
    ticket_tags:tag_id     -> tags:id
    notifications:user_id  -> users:id
    ticket_notes:ticket_id -> tickets:id
    ticket_notes:author_id -> users:id
}
"""
    render('graphviz', src, '02_er_logical.png')


# ══════════════════════════════════════════════════════════════════════════════
# 03 — Диаграмма вариантов использования (PlantUML)
# ══════════════════════════════════════════════════════════════════════════════
def gen_03():
    src = r"""
@startuml
!theme plain
skinparam backgroundColor white
skinparam defaultFontName "DejaVu Sans"
skinparam defaultFontSize 13
skinparam ArrowColor #555555
skinparam ArrowFontSize 11
skinparam usecase {
    BackgroundColor #E2EFDA
    BorderColor #375623
    FontSize 12
}
skinparam actor {
    BackgroundColor #D9E2F3
    BorderColor #1F497D
    FontSize 13
}
skinparam rectangle {
    BackgroundColor #FAFEFF
    BorderColor #1F497D
    BorderThickness 2
    FontSize 14
    FontColor #1F497D
    FontStyle bold
}
skinparam note {
    BackgroundColor #FFFDE7
    BorderColor #F0A000
}

left to right direction
title Диаграмма вариантов использования\nСистема управления заявками ООО «Экспресс-технологии»

actor "Пользователь\n(клиент)" as User
actor "Агент\nподдержки" as Agent
actor "Администратор" as Admin

Admin -|> Agent : обобщение
Agent -|> User : обобщение

rectangle "Система управления заявками" {

    package "Общий доступ" #F0F8FF {
        usecase "UC01 Войти в систему" as UC01
        usecase "UC02 Зарегистрироваться\n(клиентский портал)" as UC02
        usecase "UC03 Создать заявку" as UC03
        usecase "UC04 Просмотреть свои заявки" as UC04
        usecase "UC05 Добавить комментарий" as UC05
        usecase "UC06 Загрузить вложение" as UC06
        usecase "UC07 Отменить свою заявку" as UC07
        usecase "UC08 Получать real-time уведомления" as UC08
    }

    package "Агент и администратор" #F0FFF0 {
        usecase "UC09 Просмотреть заявки отдела" as UC09
        usecase "UC10 Взять заявку в работу" as UC10
        usecase "UC11 Изменить статус заявки" as UC11
        usecase "UC12 Назначить исполнителя" as UC12
        usecase "UC13 Добавить внутренний\nкомментарий" as UC13
        usecase "UC14 Запросить доп. информацию" as UC14
        usecase "UC15 Выполнить / закрыть заявку" as UC15
        usecase "UC16 Просмотреть отчёты отдела" as UC16
        usecase "UC17 Объединить заявки" as UC17
    }

    package "Только администратор" #FFF8F0 {
        usecase "UC18 Управление пользователями" as UC18
        usecase "UC19 Управление справочниками" as UC19
        usecase "UC20 Настройка SLA и типов заявок" as UC20
        usecase "UC21 Просмотреть все заявки" as UC21
        usecase "UC22 Экспорт отчётов (CSV / XLSX)" as UC22
        usecase "UC23 Принудительное закрытие\nлюбой заявки" as UC23
    }
}

User  --> UC01
User  --> UC02
User  --> UC03
User  --> UC04
User  --> UC05
User  --> UC06
User  --> UC07
User  --> UC08

Agent --> UC09
Agent --> UC10
Agent --> UC11
Agent --> UC12
Agent --> UC13
Agent --> UC14
Agent --> UC15
Agent --> UC16
Agent --> UC17

Admin --> UC18
Admin --> UC19
Admin --> UC20
Admin --> UC21
Admin --> UC22
Admin --> UC23

UC03 ..> UC01 : <<include>>
UC04 ..> UC01 : <<include>>
UC11 ..> UC10 : <<include>>
UC13 ..> UC11 : <<extend>>
@enduml
"""
    render('plantuml', src, '03_usecase.png')


# ══════════════════════════════════════════════════════════════════════════════
# 04 — Диаграмма последовательности: создание заявки (PlantUML)
# ══════════════════════════════════════════════════════════════════════════════
def gen_04():
    src = r"""
@startuml
!theme plain
skinparam backgroundColor white
skinparam defaultFontName "DejaVu Sans"
skinparam defaultFontSize 12
skinparam sequenceArrowThickness 2
skinparam sequenceParticipantBorderThickness 2
skinparam sequenceParticipant {
    BackgroundColor #2E5FA3
    FontColor white
    BorderColor #1a3a6b
    FontSize 12
}
skinparam sequenceLifeLineBorderColor #AAAAAA
skinparam sequenceGroupBodyBackgroundColor #F8FBFF
skinparam note {
    BackgroundColor #FFFDE7
    BorderColor #F0A000
}

title Диаграмма последовательности — создание заявки

participant "Браузер\n(React SPA)" as Browser
participant "FastAPI\nRouter" as API
participant "Ticket\nService" as TS
participant "SLA\nService" as SLA
participant "PostgreSQL" as DB
participant "Celery\nWorker" as Celery

Browser -> API : POST /api/v1/tickets\n(JWT, TicketCreate JSON)
activate API

API -> API : Валидация JWT-токена\nПроверка прав (role check)
API -> TS  : create_ticket(data, current_user)
activate TS

TS -> DB   : SELECT priority, ticket_type
activate DB
DB --> TS  : Priority, TicketType
deactivate DB

TS -> SLA  : calculate_deadline(now, sla_hours)
activate SLA
SLA --> TS : sla_deadline: datetime
deactivate SLA

TS -> DB   : INSERT INTO tickets\n(number, title, status=new, sla_deadline, ...)
activate DB
DB --> TS  : ticket_id: int
deactivate DB

TS -> DB   : INSERT INTO ticket_history\n(ticket_id, event=created, payload)
activate DB
DB --> TS  : ok
deactivate DB

TS -> DB   : SELECT department.agents (for routing)
activate DB
DB --> TS  : agent_list
deactivate DB

TS -> Celery : send_notification.delay(\n  ticket_id, event=created)
activate Celery
Celery --> TS : task_id
deactivate Celery

TS --> API : TicketResponse (id, number, status, sla_deadline, ...)
deactivate TS

API --> Browser : HTTP 201 Created\n{ticket JSON}
deactivate API

note over Celery
  Асинхронно:
  1. Email-уведомление заявителю
  2. SSE push всем агентам отдела
  3. Запись в notifications table
end note
@enduml
"""
    render('plantuml', src, '04_sequence.png')


# ══════════════════════════════════════════════════════════════════════════════
# 05 — Диаграмма состояний: жизненный цикл заявки (PlantUML)
# ══════════════════════════════════════════════════════════════════════════════
def gen_05():
    src = r"""
@startuml
!theme plain
skinparam backgroundColor white
skinparam defaultFontName "DejaVu Sans"
skinparam defaultFontSize 13
skinparam state {
    BackgroundColor #D9E2F3
    BorderColor #1F497D
    FontSize 13
    ArrowColor #333333
}
skinparam ArrowThickness 2

title Диаграмма состояний — жизненный цикл заявки

[*] --> new : Пользователь создаёт заявку

state "Новая (new)" as new #D9E2F3
state "В работе (in_progress)" as in_progress #E2EFDA
state "Ожидает информации\n(waiting_info)" as waiting_info #FFF2CC
state "Выполнена (resolved)" as resolved #E2EFDA
state "Отменена (cancelled)" as cancelled #FCE4D6

new --> in_progress    : Взять в работу\n[агент / администратор]
new --> cancelled      : Отменить\n[пользователь / агент / администратор]

in_progress --> waiting_info : Запросить\nдоп. информацию\n[агент / администратор]
in_progress --> resolved     : Выполнить / закрыть\n[агент / администратор]
in_progress --> cancelled    : Отменить\n[агент / администратор]

waiting_info --> in_progress : Информация получена\n[пользователь / агент]
waiting_info --> cancelled   : Отменить\n[агент / администратор]

resolved --> in_progress : Переоткрыть заявку\n[пользователь / администратор]
resolved --> [*]

cancelled --> [*]

note right of new
  Генерируется номер SD-ГГГГ-НННН
  Рассчитывается SLA-дедлайн
  Отправляется email-уведомление
end note

note right of in_progress
  Фиксируется в ticket_history
  SSE push всем участникам
end note

note right of waiting_info
  SLA-таймер приостановлен
end note

note right of resolved
  Закрытое время фиксируется
  Финальный email отправлен
end note
@enduml
"""
    render('plantuml', src, '05_statechart.png')


# ══════════════════════════════════════════════════════════════════════════════
# 06 — Диаграмма развёртывания (PlantUML)
# ══════════════════════════════════════════════════════════════════════════════
def gen_06():
    src = r"""
@startuml
!theme plain
skinparam backgroundColor white
skinparam defaultFontName "DejaVu Sans"
skinparam defaultFontSize 12
skinparam node {
    BackgroundColor #EBF3FB
    BorderColor #1F497D
    FontSize 13
    FontColor #1F497D
}
skinparam artifact {
    BackgroundColor #DEEAF1
    BorderColor #2E5FA3
}
skinparam database {
    BackgroundColor #FFF2CC
    BorderColor #7F6000
}
skinparam cloud {
    BackgroundColor #F5F5F5
    BorderColor #777777
}
skinparam ArrowColor #444444
skinparam ArrowThickness 1.8

title Диаграмма развёртывания — Система управления заявками

cloud "Интернет" {
    node "Браузер сотрудника" as EmpBrowser {
        artifact "React SPA\n(extechportal.online)" as ReactEmp
    }
    node "Браузер клиента" as ClientBrowser {
        artifact "React Portal\n(extechportal.ru)" as ReactClient
    }
}

node "VPS сервер (Ubuntu 26.04)\nreg.ru · 195.24.71.84" as VPS {
    node "Docker Compose" as Docker {
        artifact "Nginx 1.25\n:80 / :443\nReverse Proxy + SSL" as Nginx
        artifact "FastAPI (uvicorn)\n:8000\nREST API + SSE" as FastAPI
        artifact "Celery Worker\nEmail · SLA-monitor" as Worker
        artifact "Celery Beat\nScheduler" as Beat
        database "PostgreSQL 15\n:5432" as PG
        database "Redis 7\n:6379\nBroker + Cache" as Redis
    }
}

cloud "Внешние сервисы" {
    artifact "SMTP-сервер\nmail.hosting.reg.ru:587" as SMTP
}

EmpBrowser    --> Nginx   : HTTPS :443
ClientBrowser --> Nginx   : HTTPS :443
Nginx         --> FastAPI : HTTP :8000\n(proxy_pass)
FastAPI       --> PG      : asyncpg\n(SQLAlchemy)
FastAPI       --> Redis   : aioredis
Worker        --> PG      : SQLAlchemy
Worker        --> Redis   : broker
Worker        --> SMTP    : SMTP/TLS
Beat          --> Redis   : schedule → Worker
@enduml
"""
    render('plantuml', src, '06_deployment.png')


# ══════════════════════════════════════════════════════════════════════════════
# 07 — Диаграмма деятельности: обработка заявки (PlantUML)
# ══════════════════════════════════════════════════════════════════════════════
def gen_07():
    src = r"""
@startuml
!theme plain
skinparam backgroundColor white
skinparam defaultFontName "DejaVu Sans"
skinparam defaultFontSize 12
skinparam activity {
    BackgroundColor #D9E2F3
    BorderColor #1F497D
    DiamondBackgroundColor #FFF2CC
    DiamondBorderColor #7F6000
    ArrowColor #333333
    FontSize 12
}
skinparam swimlane {
    BorderColor #AAAAAA
    TitleFontSize 13
    TitleFontStyle bold
}
skinparam ArrowThickness 1.8

title Диаграмма деятельности — обработка заявки агентом

|#EBF3FB| Пользователь |
start
:Заполнить форму создания заявки;
:Выбрать тип, приоритет, описание;

|#E2EFDA| Система (FastAPI) |
:Валидировать данные;
:Сгенерировать номер SD-ГГГГ-НННН;
:Рассчитать SLA-дедлайн;
:Записать в БД (статус: Новая);
:SSE push агентам отдела;

|#D9E2F3| Агент поддержки |
:Просмотреть список новых заявок;
if (Берёт заявку в работу?) then (да)
    :Назначить себя исполнителем\n(статус: В работе);
    if (Нужна доп. информация?) then (да)
        :Запросить информацию у\nзаявителя (статус: Ожидает);

        |#EBF3FB| Пользователь |
        :Получить email-уведомление;
        :Ответить в комментарии;

        |#D9E2F3| Агент поддержки |
        :Получить уведомление\no новом комментарии;
        :Продолжить работу\n(статус: В работе);
    else (нет)
    endif
    :Выполнить задачу;
    :Добавить комментарий с решением;
    :Изменить статус на «Выполнена»;

    |#E2EFDA| Система (FastAPI) |
    :Записать событие в ticket_history;
    :Зафиксировать closed_at;

    |#F5F5F5| Celery Worker |
    :Отправить email-уведомление\nзаявителю о выполнении;
    stop
else (нет)
    |#D9E2F3| Агент поддержки |
    :Заявка остаётся в очереди;
    stop
endif
@enduml
"""
    render('plantuml', src, '07_activity.png')


# ══════════════════════════════════════════════════════════════════════════════
# 08 — Контекстная диаграмма DFD Level 0 (Graphviz)
# ══════════════════════════════════════════════════════════════════════════════
def gen_08():
    src = r"""
digraph DFD_Context {
    graph [
        rankdir=LR
        splines=polyline
        nodesep=1.2
        ranksep=3.0
        fontname="DejaVu Sans"
        label="Контекстная диаграмма потоков данных (DFD Level 0)"
        labelloc=t fontsize=18
        bgcolor=white pad=0.7
    ]
    edge [fontname="DejaVu Sans" fontsize=10 penwidth=1.8 arrowhead=vee]

    /* Central process */
    System [
        label="0\nАвтоматизация\nуправления\nзаявками"
        shape=ellipse
        style="filled"
        fillcolor="#2E5FA3"
        fontcolor=white
        fontname="DejaVu Sans"
        fontsize=14
        width=3.2 height=2.2
        penwidth=2.5
    ]

    /* External entities — left */
    User [
        label="Пользователь\n(заявитель)"
        shape=box style="filled,rounded"
        fillcolor="#F2F2F2" fontcolor="#222"
        fontname="DejaVu Sans" fontsize=12
        margin="0.3,0.15" penwidth=2
    ]
    Agent [
        label="Агент\nподдержки"
        shape=box style="filled,rounded"
        fillcolor="#F2F2F2" fontcolor="#222"
        fontname="DejaVu Sans" fontsize=12
        margin="0.3,0.15" penwidth=2
    ]
    Admin [
        label="Администратор"
        shape=box style="filled,rounded"
        fillcolor="#F2F2F2" fontcolor="#222"
        fontname="DejaVu Sans" fontsize=12
        margin="0.3,0.15" penwidth=2
    ]

    /* External entities — right */
    SMTP [
        label="SMTP-сервер\n(Email)"
        shape=box style="filled,rounded"
        fillcolor="#FFF2CC" fontcolor="#444"
        fontname="DejaVu Sans" fontsize=12
        margin="0.3,0.15" penwidth=2
    ]
    FS [
        label="Файловая\nсистема\n(вложения)"
        shape=box style="filled,rounded"
        fillcolor="#FFF2CC" fontcolor="#444"
        fontname="DejaVu Sans" fontsize=12
        margin="0.3,0.15" penwidth=2
    ]
    DB [
        label="PostgreSQL\n+ Redis"
        shape=cylinder
        style="filled"
        fillcolor="#FFF2CC" fontcolor="#444"
        fontname="DejaVu Sans" fontsize=12
        penwidth=2
    ]

    { rank=same; User; Agent; Admin }
    { rank=same; SMTP; FS; DB }

    /* ── Flows ─────────────────────────────────────────── */
    User  -> System [label="  Новая заявка\n  Комментарии / файлы  "]
    System -> User  [label="  Статус заявки\n  Email-уведомление  " color="#375623" fontcolor="#375623"]

    Agent -> System [label="  Смена статуса\n  Назначение\n  Ответы  "]
    System -> Agent [label="  Очередь заявок\n  SLA-таймер\n  История  " color="#375623" fontcolor="#375623"]

    Admin -> System [label="  Управление\n  пользователями\n  Справочники  "]
    System -> Admin [label="  Аналитика\n  Экспорт  " color="#843C0C" fontcolor="#843C0C"]

    System -> SMTP  [label="  Email-уведомления\n  (MIME / TLS)  "]
    System -> FS    [label="  Загрузка / скачивание\n  файлов вложений  " dir=both]
    System -> DB    [label="  SQL-запросы\n  Кэш Redis  " dir=both]
}
"""
    render('graphviz', src, '08_context_dfd.png')


# ══════════════════════════════════════════════════════════════════════════════
# 09 — IDEF0 Контекстная диаграмма A-0 (Matplotlib)
# ══════════════════════════════════════════════════════════════════════════════
def gen_09():
    fig, ax = plt.subplots(figsize=(22, 14))
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 14)
    ax.axis('off')
    fig.suptitle(
        'Контекстная диаграмма IDEF0 (уровень A-0)\n'
        'Система автоматизации управления заявками ООО «Экспресс-технологии»',
        fontsize=13, fontweight='bold', y=0.99
    )

    # ── Central box ──────────────────────────────────────────────────────────
    BX, BY, BW, BH = 6.0, 3.5, 10.0, 7.0
    box = FancyBboxPatch((BX, BY), BW, BH, boxstyle='square,pad=0',
                         facecolor='#EBF3FB', edgecolor='#1F497D', lw=3)
    ax.add_patch(box)
    ax.text(BX + BW - 0.15, BY + 0.15, 'A0', ha='right', va='bottom',
            fontsize=11, fontweight='bold', color='#1F497D', fontfamily=FONT)
    for dy, text, fs, bold in [
        (1.2,  'АВТОМАТИЗАЦИЯ УПРАВЛЕНИЯ ЗАЯВКАМИ',        13, True),
        (0.3,  'ООО «Экспресс-технологии»',                11, False),
        (-0.8, 'Приём, регистрация, распределение,',        10, False),
        (-1.5, 'контроль исполнения и закрытие заявок',     10, False),
    ]:
        ax.text(BX + BW/2, BY + BH/2 + dy, text, ha='center', va='center',
                fontsize=fs, fontweight='bold' if bold else 'normal',
                color='#1F497D' if bold else '#444', fontfamily=FONT)

    AKW = dict(lw=2.0, length_includes_head=True, head_width=0.18, head_length=0.18)

    # ── Inputs (left) ────────────────────────────────────────────────────────
    inputs = [
        (9.5,  'И1', 'Обращения пользователей', '(данные заявки, комментарии, файлы)'),
        (7.0,  'И2', 'Учётные данные',          '(логин / email, пароль)'),
        (4.8,  'И3', 'Параметры фильтрации',    '(статус, период, приоритет, отдел)'),
    ]
    for y, code, title, detail in inputs:
        ax.annotate('', xy=(BX, y), xytext=(0.5, y),
                    arrowprops=dict(arrowstyle='-|>', color='#1F497D', lw=2.0))
        ax.text(0.6, y + 0.28, f'{code}: {title}', ha='left', va='bottom',
                fontsize=9, fontweight='bold', color='#1F497D', fontfamily=FONT)
        ax.text(0.6, y - 0.25, detail, ha='left', va='top',
                fontsize=8, color='#555', fontfamily=FONT)

    # ── Outputs (right) ──────────────────────────────────────────────────────
    outputs = [
        (9.5,  'В1', 'Зарегистрированные заявки', '(номер SD-ГГГГ-НННН, статус, SLA-дедлайн)'),
        (7.0,  'В2', 'Уведомления',               '(Email + SSE real-time)'),
        (4.8,  'В3', 'Отчёты и аналитика',         '(CSV / XLSX, статистика SLA, KPI)'),
    ]
    for y, code, title, detail in outputs:
        ax.annotate('', xy=(21.5, y), xytext=(BX + BW, y),
                    arrowprops=dict(arrowstyle='-|>', color='#375623', lw=2.0))
        ax.text(BX + BW + 0.2, y + 0.28, f'{code}: {title}', ha='left', va='bottom',
                fontsize=9, fontweight='bold', color='#375623', fontfamily=FONT)
        ax.text(BX + BW + 0.2, y - 0.25, detail, ha='left', va='top',
                fontsize=8, color='#555', fontfamily=FONT)

    # ── Controls (top) ───────────────────────────────────────────────────────
    controls = [
        (8.0,  'У1', 'SLA-регламент',    'нормативы по приоритетам'),
        (11.0, 'У2', 'Политика RBAC',    'роли: admin / agent / user'),
        (14.0, 'У3', 'Бизнес-правила',   'маршрутизация, переходы статусов'),
    ]
    for x, code, title, detail in controls:
        ax.annotate('', xy=(x, BY + BH), xytext=(x, 13.5),
                    arrowprops=dict(arrowstyle='-|>', color='#843C0C', lw=2.0))
        ax.text(x, 13.6, f'{code}: {title}', ha='center', va='bottom',
                fontsize=9, fontweight='bold', color='#843C0C', fontfamily=FONT)
        ax.text(x, 13.1, detail, ha='center', va='bottom',
                fontsize=8, color='#843C0C', fontfamily=FONT)

    # ── Mechanisms (bottom) ──────────────────────────────────────────────────
    mechs = [
        (7.5,  'М1', 'FastAPI + Python 3.12',    'backend-фреймворк'),
        (9.5,  'М2', 'React 18 + TypeScript',    'frontend SPA'),
        (11.5, 'М3', 'PostgreSQL + SQLAlchemy',  'хранение данных'),
        (13.5, 'М4', 'Celery 5 + Redis 7',       'фоновые задачи'),
    ]
    for x, code, title, detail in mechs:
        ax.annotate('', xy=(x, BY), xytext=(x, 0.8),
                    arrowprops=dict(arrowstyle='-|>', color='#7F6000', lw=2.0))
        ax.text(x, 0.68, f'{code}: {title}', ha='center', va='top',
                fontsize=8.5, fontweight='bold', color='#7F6000', fontfamily=FONT)
        ax.text(x, 0.22, detail, ha='center', va='top',
                fontsize=7.5, color='#7F6000', fontfamily=FONT)

    # ── Legend ───────────────────────────────────────────────────────────────
    ax.text(11.0, 1.7,
            'И — Вход (Input)    В — Выход (Output)'
            '    У — Управление (Control)    М — Механизм (Mechanism)',
            ha='center', va='center', fontsize=9, color='#333', fontfamily=FONT,
            bbox=dict(facecolor='#FFFDE7', edgecolor='#888', pad=5, boxstyle='round'))

    save_mpl(fig, '09_idef0_context.png')


# ══════════════════════════════════════════════════════════════════════════════
# 10 — IDEF0 Функциональная декомпозиция A0 (Matplotlib)
# ══════════════════════════════════════════════════════════════════════════════
def gen_10():
    fig, ax = plt.subplots(figsize=(28, 20))
    ax.set_xlim(0, 28)
    ax.set_ylim(0, 20)
    ax.axis('off')
    fig.suptitle(
        'Функциональная диаграмма IDEF0 (уровень A0) — декомпозиция процесса управления заявками',
        fontsize=13, fontweight='bold', y=0.99
    )

    BW, BH = 4.2, 2.2

    def func_box(cx, cy, code, name, sub=''):
        """Draw an IDEF0 function box centered at (cx, cy)."""
        x, y = cx - BW/2, cy - BH/2
        box = FancyBboxPatch((x, y), BW, BH, boxstyle='square,pad=0',
                             facecolor='#EBF3FB', edgecolor='#1F497D', lw=2)
        ax.add_patch(box)
        ax.text(x + BW - 0.1, y + 0.1, code, ha='right', va='bottom',
                fontsize=9, fontweight='bold', color='#1F497D', fontfamily=FONT)
        dy_name = 0.2 if sub else 0
        ax.text(cx, cy + dy_name, name, ha='center', va='center',
                fontsize=10, fontweight='bold', color='#1F497D',
                fontfamily=FONT, multialignment='center')
        if sub:
            ax.text(cx, cy - 0.5, sub, ha='center', va='center',
                    fontsize=8.5, color='#444', fontfamily=FONT, multialignment='center')

    # Staircase positions (cx, cy)
    boxes = [
        (3.0,  17.0, 'A01', 'Аутентификация\nи регистрация', 'пользователей'),
        (8.0,  14.0, 'A02', 'Приём и регистрация\nзаявок', '(валидация, нумерация, SLA)'),
        (13.0, 11.0, 'A03', 'Маршрутизация\nи назначение', '(отдел, исполнитель)'),
        (18.0,  8.0, 'A04', 'SLA-мониторинг\nи эскалация', '(расчёт, Celery Beat)'),
        (23.0,  5.0, 'A05', 'Коммуникация\nи уведомления', '(SSE, email, история)'),
        (13.0,  2.0, 'A06', 'Аналитика\nи отчётность', '(статистика, экспорт CSV/XLSX)'),
    ]
    for cx, cy, code, name, sub in boxes:
        func_box(cx, cy, code, name, sub)

    def flow(x1, y1, x2, y2, lbl, color='#333333', rad=0):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=1.8,
                                    connectionstyle=f'arc3,rad={rad}'))
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2 + 0.22
        ax.text(mx, my, lbl, ha='center', va='bottom', fontsize=8, color=color,
                fontfamily=FONT,
                bbox=dict(facecolor='white', edgecolor='#ccc', pad=2, boxstyle='round'))

    # Boundary inputs (left)
    for y, lbl in [(17.3, 'Учётные данные'), (16.6, 'Запрос регистрации')]:
        ax.annotate('', xy=(3.0 - BW/2, y), xytext=(0.3, y),
                    arrowprops=dict(arrowstyle='-|>', color='#1F497D', lw=1.8))
        ax.text(0.4, y + 0.15, lbl, ha='left', va='bottom',
                fontsize=8.5, color='#1F497D', fontfamily=FONT)

    # A01 → A02
    flow(3.0 + BW/2, 17.0,  8.0 - BW/2, 14.0,
         'Сессия (JWT-токен, роль)', color='#1F497D', rad=-0.15)

    # Input to A02
    ax.annotate('', xy=(8.0 - BW/2, 14.3), xytext=(5.0, 14.3),
                arrowprops=dict(arrowstyle='-|>', color='#375623', lw=1.8))
    ax.text(5.1, 14.5, 'Данные заявки\n(тема, описание, тип)', ha='left', va='bottom',
            fontsize=8, color='#375623', fontfamily=FONT)

    # A02 → A03
    flow(8.0 + BW/2, 14.0,  13.0 - BW/2, 11.0,
         'Зарегистрированная заявка\n(SD-номер, SLA-дедлайн)', color='#375623', rad=-0.1)

    # A02 → A06 (событие создания для аналитики)
    flow(8.0, 14.0 - BH/2,  13.0, 2.0 + BH/2,
         'Событие: ticket_created', color='#888', rad=0.2)

    # A03 → A04
    flow(13.0 + BW/2, 11.0,  18.0 - BW/2, 8.0,
         'Назначенная заявка\n(исполнитель, отдел)', color='#843C0C', rad=-0.08)

    # A04 → A05
    flow(18.0 + BW/2, 8.0,  23.0 - BW/2, 5.0,
         'SLA-событие (нарушение,\nэскалация)', color='#C00000', rad=-0.08)

    # A03 → A05 (смена статуса)
    flow(13.0 + BW/2, 10.5,  23.0 - BW/2, 5.5,
         'Изменение статуса / назначения', color='#555', rad=0.08)

    # A05 → A06 (история для отчётности)
    flow(23.0, 5.0 - BH/2,  13.0 + BW/2, 2.0,
         'История событий (для агрегации)', color='#555', rad=0.2)

    # A04 → A06 (SLA-статистика)
    flow(18.0, 8.0 - BH/2,  13.0 + BW/2, 2.2,
         'SLA-статистика', color='#7F6000', rad=-0.15)

    # Boundary outputs (right)
    for y, lbl in [(5.5, 'Обработанная заявка'), (4.8, 'Email-уведомление')]:
        ax.annotate('', xy=(27.7, y), xytext=(23.0 + BW/2, y),
                    arrowprops=dict(arrowstyle='-|>', color='#375623', lw=1.8))
        ax.text(27.8, y + 0.15, lbl, ha='left', va='bottom',
                fontsize=8.5, color='#375623', fontfamily=FONT)

    ax.annotate('', xy=(27.7, 2.3), xytext=(13.0 + BW/2, 2.3),
                arrowprops=dict(arrowstyle='-|>', color='#375623', lw=1.8))
    ax.text(27.8, 2.45, 'Отчёт (CSV / XLSX)', ha='left', va='bottom',
            fontsize=8.5, color='#375623', fontfamily=FONT)

    # Controls (top)
    for x, lbl in [(4.0, 'SLA-регламент'), (11.0, 'Политика RBAC'), (18.0, 'Бизнес-правила')]:
        ax.annotate('', xy=(x, 19.2), xytext=(x, 19.6),
                    arrowprops=dict(arrowstyle='-|>', color='#843C0C', lw=1.6))
        ax.text(x, 19.7, lbl, ha='center', va='bottom',
                fontsize=9, color='#843C0C', fontfamily=FONT)

    # Legend
    ax.text(1.0, 0.5,
            'Нотация: IDEF0 A0  |  → Поток данных  |  ↑ Управление  |  Блоки: A01–A06',
            ha='left', va='bottom', fontsize=9, color='#333', fontfamily=FONT,
            bbox=dict(facecolor='#F5F5F5', edgecolor='#888', pad=5, boxstyle='round'))

    save_mpl(fig, '10_idef0_functional.png')


# ══════════════════════════════════════════════════════════════════════════════
# 11 — DFD Уровень 1 (Graphviz)
# ══════════════════════════════════════════════════════════════════════════════
def gen_11():
    src = r"""
digraph DFD_Level1 {
    graph [
        rankdir=TB
        splines=polyline
        nodesep=1.0
        ranksep=1.8
        fontname="DejaVu Sans"
        label="Диаграмма потоков данных (DFD Level 1)\nСистема управления заявками"
        labelloc=t fontsize=18
        bgcolor=white pad=0.7
    ]
    edge [fontname="DejaVu Sans" fontsize=9 penwidth=1.6 arrowhead=vee color="#333333"]

    /* External entities */
    node [shape=box style="filled,rounded" fillcolor="#F2F2F2"
          fontcolor="#222" fontname="DejaVu Sans" fontsize=12
          margin="0.3,0.15" penwidth=2]

    EUser  [label="Пользователь\n(заявитель)"]
    EAgent [label="Агент\nподдержки"]
    EAdmin [label="Администратор"]
    EEmail [label="SMTP-сервер\n(Email)"]

    /* Processes */
    node [shape=ellipse style="filled" fillcolor="#D9E2F3"
          fontcolor="#1F497D" fontname="DejaVu Sans" fontsize=11
          margin="0.4,0.2" penwidth=2]

    P1 [label="1\nАутентификация\nи авторизация"]
    P2 [label="2\nУправление\nзаявками"]
    P3 [label="3\nКоммуникация\n(комментарии,\nвложения)"]
    P4 [label="4\nSLA-мониторинг\nи эскалация"]
    P5 [label="5\nАналитика\nи отчёты"]

    /* Data stores */
    node [shape=none margin=0 fontname="DejaVu Sans" fontsize=10]

    D1 [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3">
<TR><TD WIDTH="40" BGCOLOR="#FFF2CC"><FONT COLOR="#7F6000"><B>Д1</B></FONT></TD>
<TD BGCOLOR="white">Users / Departments</TD></TR>
</TABLE>>]

    D2 [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3">
<TR><TD WIDTH="40" BGCOLOR="#FFF2CC"><FONT COLOR="#7F6000"><B>Д2</B></FONT></TD>
<TD BGCOLOR="white">Tickets / Priorities / TicketTypes</TD></TR>
</TABLE>>]

    D3 [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3">
<TR><TD WIDTH="40" BGCOLOR="#FFF2CC"><FONT COLOR="#7F6000"><B>Д3</B></FONT></TD>
<TD BGCOLOR="white">Comments / Attachments / TicketNotes</TD></TR>
</TABLE>>]

    D4 [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3">
<TR><TD WIDTH="40" BGCOLOR="#FFF2CC"><FONT COLOR="#7F6000"><B>Д4</B></FONT></TD>
<TD BGCOLOR="white">Notifications / TicketHistory</TD></TR>
</TABLE>>]

    D5 [label=<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3">
<TR><TD WIDTH="40" BGCOLOR="#FFF2CC"><FONT COLOR="#7F6000"><B>Д5</B></FONT></TD>
<TD BGCOLOR="white">SavedFilters / Reports cache (Redis)</TD></TR>
</TABLE>>]

    /* ── Layout hints ────────────────────────────────────── */
    { rank=source; EUser; EAgent; EAdmin }
    { rank=same;   P1; P2 }
    { rank=same;   D1; D2; D3 }
    { rank=same;   P3; P4; P5 }
    { rank=sink;   D4; D5; EEmail }

    /* ── Edges ───────────────────────────────────────────── */
    EUser  -> P1 [label="Учётные данные"]
    EAgent -> P1 [label="Учётные данные"]
    EAdmin -> P1 [label="Учётные данные"]
    P1 -> D1     [label="Запись / обновление\nпользователя" dir=both]
    P1 -> P2     [label="JWT-токен, роль"]

    EUser  -> P2 [label="Данные заявки"]
    EAgent -> P2 [label="Смена статуса,\nназначение"]
    EAdmin -> P2 [label="Управление,\nнастройки"]
    P2 -> D2     [label="CRUD заявок,\nтипов, приоритетов" dir=both]
    P2 -> P3     [label="ticket_id, event"]
    P2 -> P4     [label="SLA-данные заявки"]
    P2 -> P5     [label="Данные для агрегации"]

    P3 -> D3     [label="Запись\nкомментариев,\nфайлов" dir=both]
    P3 -> D4     [label="Уведомления,\nhistory-записи"]
    P3 -> EEmail [label="Email-\nуведомление"]
    D4 -> EUser  [label="SSE / email"]
    D4 -> EAgent [label="SSE / email"]

    P4 -> D2     [label="SLA-нарушение\n(флаг)" dir=both]
    P4 -> D4     [label="Событие эскалации"]
    P4 -> EEmail [label="Escalation email"]

    P5 -> D5     [label="Кэш отчётов" dir=both]
    EAdmin -> P5 [label="Запрос отчёта"]
    EAgent -> P5 [label="Запрос отчёта\nотдела"]
}
"""
    render('graphviz', src, '11_dfd_level1.png')


# ══════════════════════════════════════════════════════════════════════════════
# 12 — Диаграмма коммуникации (PlantUML sequence с нумерацией)
# ══════════════════════════════════════════════════════════════════════════════
def gen_12():
    src = r"""
@startuml
!theme plain
skinparam backgroundColor white
skinparam defaultFontName "DejaVu Sans"
skinparam defaultFontSize 12
skinparam sequenceArrowThickness 2
skinparam sequenceParticipant {
    BackgroundColor #2E5FA3
    FontColor white
    BorderColor #1a3a6b
    FontSize 12
}
skinparam note {
    BackgroundColor #FFFDE7
    BorderColor #F0A000
}
skinparam sequenceGroupBodyBackgroundColor #F8FBFF

autonumber

title Диаграмма коммуникации — изменение статуса заявки агентом

participant "React SPA\n(агент)" as Browser
participant "FastAPI\nRouter" as Router
participant "Auth\nMiddleware" as Auth
participant "Ticket\nService" as TS
participant "Notification\nService" as NS
participant "PostgreSQL" as DB
participant "Redis\n(SSE broker)" as Redis
participant "Celery\nWorker" as Celery

Browser -> Router : PATCH /api/v1/tickets/{id}/status\n{status: «in_progress»}

Router -> Auth : Проверить JWT-токен
Auth -> DB     : SELECT user WHERE id=sub
DB --> Auth    : User(role=agent, dept_id=X)
Auth --> Router: current_user

Router -> TS   : change_status(ticket_id, new_status, user)
TS -> DB       : SELECT ticket WHERE id=ticket_id
DB --> TS      : Ticket(status=new, assignee=None)

TS -> TS       : Проверить допустимость перехода\n(STATUS_TRANSITIONS map)
TS -> DB       : UPDATE tickets SET status=in_progress,\nassignee_id=user.id
DB --> TS      : ok

TS -> DB       : INSERT INTO ticket_history\n(event=status_changed, payload={...})
DB --> TS      : history_id

TS -> NS       : notify(ticket_id, event, recipients)
NS -> DB       : INSERT INTO notifications (user_id=requester_id, ...)
NS -> Redis    : PUBLISH channel:ticket:{id}\n{event: status_changed, ...}
Redis --> NS   : ok
NS -> Celery   : send_email.delay(ticket_id, event)
Celery --> NS  : task_id

NS --> TS      : done
TS --> Router  : TicketResponse (обновлённая заявка)
Router --> Browser : HTTP 200 OK\n{ticket JSON}

note over Redis
  SSE-клиенты (заявитель,
  другие агенты) получают
  push в реальном времени
end note
@enduml
"""
    render('plantuml', src, '12_communication.png')


# ══════════════════════════════════════════════════════════════════════════════
# 13 — Диаграмма классов (PlantUML)
# ══════════════════════════════════════════════════════════════════════════════
def gen_13():
    src = r"""
@startuml
!theme plain
skinparam backgroundColor white
skinparam defaultFontName "DejaVu Sans"
skinparam defaultFontSize 11
skinparam classAttributeIconSize 0
skinparam class {
    BackgroundColor #EBF3FB
    BorderColor #1F497D
    HeaderBackgroundColor #2E5FA3
    FontColor #1F497D
    HeaderFontColor white
    HeaderFontSize 13
    FontSize 11
}
skinparam ArrowColor #555555
skinparam ArrowThickness 1.8

title Диаграмма классов — модели данных системы управления заявками

enum RoleEnum {
    ADMIN
    AGENT
    USER
}

enum StatusEnum {
    NEW
    IN_PROGRESS
    WAITING_INFO
    RESOLVED
    CANCELLED
}

class Department {
    +id: int
    +name: str
    +description: str
    +is_active: bool
}

class User {
    +id: int
    +email: str
    +username: str
    -password_hash: str
    +full_name: str
    +role: RoleEnum
    +department_id: int
    +is_active: bool
    +is_email_verified: bool
    +created_at: datetime
    --
    +verify_password(plain): bool
    +set_password(plain): void
}

class Priority {
    +id: int
    +name: str
    +sla_hours: float
    +color: str
    +sort_order: int
}

class TicketType {
    +id: int
    +name: str
    +default_department_id: int
    +is_active: bool
}

class Tag {
    +id: int
    +name: str
    +color: str
}

class Ticket {
    +id: int
    +number: str
    +title: str
    +description: str
    +status: StatusEnum
    +priority_id: int
    +type_id: int
    +requester_id: int
    +assignee_id: int
    +department_id: int
    +merged_into_id: int
    +sla_deadline: datetime
    +sla_violated: bool
    +created_at: datetime
    +closed_at: datetime
    --
    +is_sla_breached(): bool
    +can_transition(new_status): bool
}

class Comment {
    +id: int
    +ticket_id: int
    +author_id: int
    +body: str
    +is_internal: bool
    +created_at: datetime
}

class Attachment {
    +id: int
    +ticket_id: int
    +comment_id: int
    +original_filename: str
    +stored_path: str
    +size_bytes: int
    +mimetype: str
    +uploaded_by: int
    +created_at: datetime
}

class TicketHistory {
    +id: int
    +ticket_id: int
    +user_id: int
    +event_type: str
    +payload: dict
    +created_at: datetime
}

class TicketNote {
    +id: int
    +ticket_id: int
    +author_id: int
    +body: str
    +created_at: datetime
}

class Notification {
    +id: int
    +user_id: int
    +event_type: str
    +payload: dict
    +is_read: bool
    +created_at: datetime
}

' ── Relationships ──────────────────────────────────────────
Department   "1" o-- "0..*" User          : содержит >
User         ..>  RoleEnum                 : использует

Department   "0..1" o-- "0..*" Ticket      : ответственен за >
User         "1" o-- "0..*" Ticket         : создаёт (requester) >
User         "0..1" o-- "0..*" Ticket      : исполняет (assignee) >
Priority     "1" o-- "1..*" Ticket         : определяет >
TicketType   "1" o-- "1..*" Ticket         : классифицирует >
Ticket       "1" o-- "0..*" Ticket         : объединён в (merged_into) >

Ticket       "1" *-- "0..*" Comment        : имеет >
Ticket       "1" *-- "0..*" Attachment     : прикреплены к >
Ticket       "1" *-- "0..*" TicketHistory  : фиксирует >
Ticket       "1" *-- "0..*" TicketNote     : заметки >
Ticket       "0..*" --o "0..*" Tag         : тегирован (M:M)

User         "1" o-- "0..*" Notification   : получает >
Ticket       ..>  StatusEnum               : использует
@enduml
"""
    render('plantuml', src, '13_class_diagram.png')


# ══════════════════════════════════════════════════════════════════════════════
# 14 — Схема интеграции компонентов (PlantUML component)
# ══════════════════════════════════════════════════════════════════════════════
def gen_14():
    src = r"""
@startuml
!theme plain
skinparam backgroundColor white
skinparam defaultFontName "DejaVu Sans"
skinparam defaultFontSize 12
skinparam component {
    BackgroundColor #DEEAF1
    BorderColor #2E5FA3
    FontSize 12
}
skinparam rectangle {
    BackgroundColor #F8FBFF
    BorderColor #1F497D
    FontColor #1F497D
    FontStyle bold
    FontSize 13
    RoundCorner 12
}
skinparam database {
    BackgroundColor #FFF2CC
    BorderColor #7F6000
    FontSize 12
}
skinparam cloud {
    BackgroundColor #F5F5F5
    BorderColor #888888
    FontSize 12
}
skinparam ArrowColor #444444
skinparam ArrowThickness 1.8
skinparam interface {
    BackgroundColor #E2EFDA
    BorderColor #375623
}

title Схема интеграции компонентов — Система управления заявками

cloud "Клиенты" {
    [React SPA\n(сотрудники)\nextechportal.online] as ReactEmp
    [React Portal\n(клиенты)\nextechportal.ru] as ReactClient
}

rectangle "VPS · Ubuntu 26.04\nDocker Compose" {

    rectangle "Сетевой уровень" {
        [Nginx 1.25\nReverse Proxy + SSL\nLet's Encrypt] as Nginx
    }

    rectangle "Уровень приложения" {
        [FastAPI\n(uvicorn, async)\nREST API + SSE] as FastAPI
        [Auth Service\nJWT (access 15 мин\n+ refresh 7 дней)] as Auth
        [Ticket Service\n(CRUD, SLA, routing)] as TicketSvc
        [Notification\nService\n(SSE pub/sub)] as NotifSvc
        [Celery Worker\n(email, SLA-monitor)] as Worker
        [Celery Beat\n(scheduler)] as Beat
    }

    rectangle "Уровень данных" {
        database "PostgreSQL 15\n(основное хранилище)" as PG
        database "Redis 7\n(broker + SSE pub/sub\n+ cache)" as Redis
    }
}

cloud "Внешние сервисы" {
    [SMTP\nmail.hosting.reg.ru\n:587 TLS] as SMTP
}

' ── Interfaces ────────────────────────────────────────────
() "HTTPS :443" as HTTPS
() "REST API\n/api/v1" as REST
() "SSE\n/events" as SSE
() "asyncpg" as APGSQL
() "aioredis" as AREDIS
() "AMQP\n(Redis)" as AMQP

ReactEmp    --> HTTPS
ReactClient --> HTTPS
HTTPS       -- Nginx
Nginx       --> REST
Nginx       --> SSE
REST        -- FastAPI
SSE         -- FastAPI

FastAPI     --> Auth
FastAPI     --> TicketSvc
FastAPI     --> NotifSvc
TicketSvc   --> APGSQL
Auth        --> APGSQL
NotifSvc    --> APGSQL
APGSQL      -- PG

NotifSvc    --> AREDIS
AREDIS      -- Redis

TicketSvc   --> AMQP
AMQP        -- Redis
Worker      --> AMQP
Beat        --> AMQP

Worker      --> SMTP
Worker      --> PG
@enduml
"""
    render('plantuml', src, '14_integration_schema.png')


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    import sys
    print('=== Generating diagrams v2 ===')
    print(f'Output: {OUT}\n')

    steps = [
        ('01_er_conceptual.png',   gen_01),
        ('02_er_logical.png',      gen_02),
        ('03_usecase.png',         gen_03),
        ('04_sequence.png',        gen_04),
        ('05_statechart.png',      gen_05),
        ('06_deployment.png',      gen_06),
        ('07_activity.png',        gen_07),
        ('08_context_dfd.png',     gen_08),
        ('09_idef0_context.png',   gen_09),
        ('10_idef0_functional.png',gen_10),
        ('11_dfd_level1.png',      gen_11),
        ('12_communication.png',   gen_12),
        ('13_class_diagram.png',   gen_13),
        ('14_integration_schema.png', gen_14),
    ]

    failed = []
    for name, fn in steps:
        try:
            fn()
        except Exception as e:
            print(f'  ERROR {name}: {e}')
            failed.append(name)

    print(f'\nDone. {len(steps) - len(failed)}/{len(steps)} generated.')
    if failed:
        print('Failed:', ', '.join(failed))
        sys.exit(1)
