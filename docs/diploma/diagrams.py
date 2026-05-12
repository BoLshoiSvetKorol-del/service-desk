# -*- coding: utf-8 -*-
"""Генератор всех диаграмм для дипломной работы Дегтярева М.Д."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
import os

OUT = r'Z:\ProjectX\docs\diploma\diagrams'
os.makedirs(OUT, exist_ok=True)

# ─── Цвета ────────────────────────────────────────────────────────────────────
C_ENT   = '#2E5FA3'    # синий — сущность
C_ENT_T = 'white'
C_LBL   = '#D9E2F3'    # светло-голубой — подпись связи
C_LINE  = '#1a3a6b'
C_UC    = '#E2EFDA'    # светло-зелёный — прецедент
C_UC_B  = '#375623'
C_ST    = '#FFF2CC'    # жёлтый — состояние
C_ST_B  = '#7F6000'
C_DEP   = '#EBF3FB'    # голубой — узел развёртывания
C_DEP_B = '#1F4E79'
C_SVC   = '#DEEAF1'    # сервис внутри узла
C_PH    = '#F0F0F0'    # серый — заглушка

FONT = 'DejaVu Sans'

def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f'  + {name}')


def entity_box(ax, x, y, w, h, text, color=C_ENT, tc=C_ENT_T, fs=10):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.05",
                         facecolor=color, edgecolor=C_LINE, linewidth=1.5)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=fs,
            fontweight='bold', color=tc, fontfamily=FONT, wrap=True)


def arrow(ax, x1, y1, x2, y2, lbl='', color=C_LINE, lw=1.5, style='-|>'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                connectionstyle='arc3,rad=0'))
    if lbl:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my, lbl, ha='center', va='center', fontsize=7,
                color='#333333', fontfamily=FONT,
                bbox=dict(facecolor='white', edgecolor='none', pad=1))


def dbl_arrow(ax, x1, y1, x2, y2, lbl=''):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='<|-|>', color=C_LINE, lw=1.5,
                                connectionstyle='arc3,rad=0'))
    if lbl:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my, lbl, ha='center', va='center', fontsize=7,
                color='#333333', fontfamily=FONT,
                bbox=dict(facecolor='white', edgecolor='none', pad=1))


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ER-ДИАГРАММА КОНЦЕПТУАЛЬНАЯ
# ═══════════════════════════════════════════════════════════════════════════════
def gen_er_conceptual():
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.set_xlim(0, 18); ax.set_ylim(0, 12)
    ax.axis('off')
    fig.suptitle('ER-диаграмма концептуального уровня', fontsize=14, fontweight='bold', y=0.98)

    EW, EH = 3.0, 0.85

    # positions (x, y)
    pos = {
        'Departments':     (2.2,  10.5),
        'Users':           (7.0,  10.5),
        'Notifications':   (12.5, 10.5),
        'SavedFilters':    (16.0, 10.5),
        'Priorities':      (2.2,   7.5),
        'Tickets':         (7.0,   7.5),
        'Comments':        (12.5,  7.5),
        'Attachments':     (16.0,  7.5),
        'TicketTypes':     (2.2,   4.5),
        'TicketHistory':   (7.0,   4.5),
        'Tags':            (12.5,  4.5),
    }

    for name, (x, y) in pos.items():
        entity_box(ax, x, y, EW, EH, name, fs=11)

    def line(a, b, lbl='', rad=0):
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=C_LINE, lw=1.5,
                                    connectionstyle=f'arc3,rad={rad}'))
        if lbl:
            mx, my = (x1+x2)/2, (y1+y2)/2 + 0.15
            ax.text(mx, my, lbl, ha='center', va='bottom', fontsize=8,
                    color='#222', fontfamily=FONT,
                    bbox=dict(facecolor='white', edgecolor='#aaa', pad=1.5, boxstyle='round'))

    # Relations with cardinality labels
    line('Departments', 'Users',         '1 : M\nимеет')
    line('Users',       'Notifications', '1 : M\nполучает')
    line('Users',       'SavedFilters',  '1 : M\nсохраняет', rad=0.15)

    line('Priorities',  'Tickets',       '1 : M\nустанавл.')
    line('Users',       'Tickets',       '1 : M\nсоздаёт')
    line('Tickets',     'Comments',      '1 : M\nимеет')
    line('Tickets',     'Attachments',   '1 : M\nимеет')
    line('TicketTypes', 'Tickets',       '1 : M\nклассиф.')
    line('Tickets',     'TicketHistory', '1 : M\nфиксирует')

    # Many-to-many Tickets ↔ Tags
    ax.annotate('', xy=(pos['Tags'][0], pos['Tags'][1]),
                xytext=(pos['Tickets'][0], pos['Tickets'][1]),
                arrowprops=dict(arrowstyle='<|-|>', color='#C00000', lw=1.8,
                                connectionstyle='arc3,rad=0'))
    ax.text(9.75, 5.95, 'M : M\nтегирование', ha='center', fontsize=8, color='#C00000',
            bbox=dict(facecolor='white', edgecolor='#C00000', pad=1.5, boxstyle='round'))

    # Departments → Tickets (nullable FK)
    ax.annotate('', xy=(pos['Tickets'][0]-EW/2, pos['Tickets'][1]),
                xytext=(pos['Departments'][0]+EW/2, pos['Departments'][1]),
                arrowprops=dict(arrowstyle='-|>', color='#7F7F7F', lw=1.2,
                                linestyle='dashed', connectionstyle='arc3,rad=0.3'))
    ax.text(4.0, 9.4, '0..1 : M\nответ. отдел', ha='center', fontsize=8, color='#555',
            bbox=dict(facecolor='white', edgecolor='#aaa', pad=1.0, boxstyle='round'))

    # User → Tickets as assignee
    ax.annotate('', xy=(pos['Tickets'][0]+0.2, pos['Tickets'][1]+EH/2),
                xytext=(pos['Users'][0]+0.2, pos['Users'][1]-EH/2),
                arrowprops=dict(arrowstyle='-|>', color='#555', lw=1.2,
                                linestyle='dotted', connectionstyle='arc3,rad=0.3'))
    ax.text(8.2, 9.1, '0..1 : M\nназначен', ha='center', fontsize=8, color='#555',
            bbox=dict(facecolor='white', edgecolor='#aaa', pad=1.0, boxstyle='round'))

    # Legend
    ax.plot([0.3, 1.0], [0.7, 0.7], color=C_LINE, lw=1.5)
    ax.annotate('', xy=(1.0, 0.7), xytext=(0.3, 0.7),
                arrowprops=dict(arrowstyle='-|>', color=C_LINE, lw=1.5))
    ax.text(1.15, 0.7, '— обязательная связь', fontsize=9, va='center', color='#333')
    ax.plot([0.3, 1.0], [0.35, 0.35], color='#7F7F7F', lw=1.2, linestyle='dashed')
    ax.annotate('', xy=(1.0, 0.35), xytext=(0.3, 0.35),
                arrowprops=dict(arrowstyle='-|>', color='#7F7F7F', lw=1.2))
    ax.text(1.15, 0.35, '- - необязательная связь', fontsize=9, va='center', color='#555')

    save(fig, '01_er_conceptual.png')


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ЛОГИЧЕСКАЯ МОДЕЛЬ БД (таблицы с полями)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_er_logical():
    fig, ax = plt.subplots(figsize=(22, 16))
    ax.set_xlim(0, 22); ax.set_ylim(0, 16)
    ax.axis('off')
    fig.suptitle('Логическая модель базы данных', fontsize=14, fontweight='bold', y=0.99)

    def table_box(ax, x, y, name, fields):
        col_w, row_h = 4.0, 0.45
        total_h = row_h * (len(fields) + 1)
        # header
        hdr = FancyBboxPatch((x, y - row_h), col_w, row_h,
                             boxstyle="square,pad=0", facecolor=C_ENT, edgecolor=C_LINE, lw=1.5)
        ax.add_patch(hdr)
        ax.text(x + col_w/2, y - row_h/2, name, ha='center', va='center',
                fontsize=9, fontweight='bold', color='white', fontfamily=FONT)
        # fields
        for i, (fname, ftype, pk) in enumerate(fields):
            fy = y - row_h * (i + 2)
            bg = '#EAF1FB' if pk else 'white'
            cell = FancyBboxPatch((x, fy), col_w, row_h,
                                  boxstyle="square,pad=0", facecolor=bg,
                                  edgecolor='#AAAAAA', lw=0.8)
            ax.add_patch(cell)
            prefix = '🔑 ' if pk == 'PK' else ('🔗 ' if pk == 'FK' else '   ')
            ax.text(x + 0.15, fy + row_h/2, f'{prefix}{fname}',
                    ha='left', va='center', fontsize=7.5, fontfamily=FONT,
                    color='#003070' if pk else '#222222')
            ax.text(x + col_w - 0.1, fy + row_h/2, ftype,
                    ha='right', va='center', fontsize=7, color='#666666', fontfamily=FONT)

    tables = [
        ('users', 3.5, 15.5, [
            ('id',           'SERIAL',      'PK'),
            ('email',        'VARCHAR(255)', ''),
            ('username',     'VARCHAR(100)', ''),
            ('password_hash','VARCHAR(255)', ''),
            ('full_name',    'VARCHAR(255)', ''),
            ('role',         'ENUM',         ''),
            ('department_id','INTEGER',      'FK'),
            ('is_active',    'BOOLEAN',      ''),
            ('created_at',   'TIMESTAMPTZ',  ''),
        ]),
        ('departments', 8.5, 15.5, [
            ('id',          'SERIAL',      'PK'),
            ('name',        'VARCHAR(200)', ''),
            ('description', 'TEXT',         ''),
            ('is_active',   'BOOLEAN',      ''),
        ]),
        ('priorities', 13.5, 15.5, [
            ('id',        'SERIAL',      'PK'),
            ('name',      'VARCHAR(50)', ''),
            ('sla_hours', 'FLOAT',       ''),
            ('color',     'VARCHAR(20)', ''),
            ('sort_order','INTEGER',     ''),
        ]),
        ('ticket_types', 18.0, 15.5, [
            ('id',                  'SERIAL',      'PK'),
            ('name',                'VARCHAR(200)', ''),
            ('default_department_id','INTEGER',     'FK'),
            ('is_active',           'BOOLEAN',      ''),
        ]),
        ('tickets', 3.5, 9.5, [
            ('id',               'SERIAL',      'PK'),
            ('number',           'VARCHAR(20)', ''),
            ('title',            'VARCHAR(500)', ''),
            ('description',      'TEXT',         ''),
            ('status',           'ENUM',         ''),
            ('priority_id',      'INTEGER',      'FK'),
            ('type_id',          'INTEGER',      'FK'),
            ('requester_id',     'INTEGER',      'FK'),
            ('assignee_id',      'INTEGER',      'FK'),
            ('department_id',    'INTEGER',      'FK'),
            ('sla_deadline',     'TIMESTAMPTZ',  ''),
            ('sla_violated',     'BOOLEAN',      ''),
            ('created_at',       'TIMESTAMPTZ',  ''),
            ('closed_at',        'TIMESTAMPTZ',  ''),
        ]),
        ('comments', 8.5, 9.5, [
            ('id',         'SERIAL',     'PK'),
            ('ticket_id',  'INTEGER',    'FK'),
            ('author_id',  'INTEGER',    'FK'),
            ('body',       'TEXT',       ''),
            ('is_internal','BOOLEAN',    ''),
            ('created_at', 'TIMESTAMPTZ',''),
        ]),
        ('attachments', 13.5, 9.5, [
            ('id',               'SERIAL',       'PK'),
            ('ticket_id',        'INTEGER',       'FK'),
            ('comment_id',       'INTEGER',       'FK'),
            ('original_filename','VARCHAR(500)',  ''),
            ('stored_path',      'VARCHAR(1000)', ''),
            ('size_bytes',       'BIGINT',        ''),
            ('mimetype',         'VARCHAR(200)',  ''),
            ('uploaded_by',      'INTEGER',       'FK'),
            ('created_at',       'TIMESTAMPTZ',   ''),
        ]),
        ('ticket_history', 18.0, 9.5, [
            ('id',         'SERIAL',     'PK'),
            ('ticket_id',  'INTEGER',    'FK'),
            ('user_id',    'INTEGER',    'FK'),
            ('event_type', 'VARCHAR(50)',''),
            ('payload',    'JSONB',      ''),
            ('created_at', 'TIMESTAMPTZ',''),
        ]),
        ('tags', 3.5, 3.5, [
            ('id',   'SERIAL',     'PK'),
            ('name', 'VARCHAR(50)',''),
            ('color','VARCHAR(20)',''),
        ]),
        ('ticket_tags', 8.5, 3.5, [
            ('ticket_id', 'INTEGER', 'FK'),
            ('tag_id',    'INTEGER', 'FK'),
        ]),
        ('notifications', 13.5, 3.5, [
            ('id',         'SERIAL',      'PK'),
            ('user_id',    'INTEGER',     'FK'),
            ('event_type', 'VARCHAR(50)', ''),
            ('payload',    'JSONB',       ''),
            ('is_read',    'BOOLEAN',     ''),
            ('created_at', 'TIMESTAMPTZ', ''),
        ]),
    ]

    for name, x, y, fields in tables:
        table_box(ax, x, y, name.upper(), fields)

    # FK arrows (simplified, key ones only)
    def fk(ax, x1, y1, x2, y2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color='#888', lw=1.0,
                                    connectionstyle='arc3,rad=0.15'))

    # users → departments
    fk(ax, 7.5, 12.7, 8.5, 14.8)
    # tickets → priorities
    fk(ax, 7.5, 8.8, 13.5, 14.8)
    # tickets → ticket_types
    fk(ax, 7.5, 8.5, 18.0, 14.8)
    # tickets → users (req)
    fk(ax, 3.5, 9.5, 3.5, 9.0)
    # comments → tickets
    fk(ax, 8.5, 8.8, 7.5, 8.8)
    # attachments → tickets
    fk(ax, 13.5, 8.5, 7.5, 8.5)
    # ticket_history → tickets
    fk(ax, 18.0, 8.8, 7.5, 8.3)
    # ticket_tags → tickets / tags
    fk(ax, 8.5, 3.0, 3.5, 9.0)
    fk(ax, 8.5, 3.0, 3.5, 3.0)
    # notifications → users
    fk(ax, 13.5, 3.0, 3.5, 9.0)

    save(fig, '02_er_logical.png')


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ДИАГРАММА ВАРИАНТОВ ИСПОЛЬЗОВАНИЯ (Use Case)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_usecase():
    fig, ax = plt.subplots(figsize=(18, 13))
    ax.set_xlim(0, 18); ax.set_ylim(0, 13)
    ax.axis('off')
    fig.suptitle('Диаграмма вариантов использования', fontsize=14, fontweight='bold')

    # System boundary
    sys_box = FancyBboxPatch((2.5, 0.5), 13, 12,
                             boxstyle="round,pad=0.15",
                             facecolor='#F8FBFF', edgecolor=C_ENT, lw=2)
    ax.add_patch(sys_box)
    ax.text(9.0, 12.2, 'Система управления заявками', ha='center', fontsize=11,
            fontweight='bold', color=C_ENT, fontfamily=FONT)

    def actor(ax, x, y, name, color='#1F497D'):
        # stick figure
        ax.plot(x, y + 0.9, 'o', markersize=14, color=color, zorder=5)
        ax.plot([x, x], [y + 0.3, y - 0.3], color=color, lw=2)
        ax.plot([x - 0.4, x, x + 0.4], [y + 0.1, y + 0.3, y + 0.1], color=color, lw=2)
        ax.plot([x - 0.35, x, x + 0.35], [y - 0.3, y - 0.3, y - 0.3], color=color, lw=2)
        ax.text(x, y - 0.7, name, ha='center', va='top', fontsize=9.5,
                fontweight='bold', color=color, fontfamily=FONT)

    def uc(ax, x, y, text, w=2.8, h=0.55):
        ell = mpatches.Ellipse((x, y), w, h, facecolor=C_UC, edgecolor=C_UC_B, lw=1.5)
        ax.add_patch(ell)
        ax.text(x, y, text, ha='center', va='center', fontsize=8.5,
                fontfamily=FONT, color='#1a1a1a', wrap=True)

    def assoc(ax, actor_x, actor_y, uc_x, uc_y):
        ax.plot([actor_x, uc_x], [actor_y + 0.3, uc_y], '-', color='#555', lw=1.0)

    # Actors
    actor(ax, 0.9, 6.5, 'Пользователь', '#1F497D')
    actor(ax, 9.0, 0.2, 'Агент\nподдержки',  '#375623')
    actor(ax, 17.1, 6.5, 'Администратор', '#843C0C')

    # Use cases — Пользователь
    uc_user = [
        (4.5, 11.5, 'Войти в систему'),
        (4.5,  9.8, 'Создать заявку'),
        (4.5,  8.3, 'Просмотреть\nсвои заявки'),
        (4.5,  6.8, 'Добавить\nкомментарий'),
        (4.5,  5.3, 'Загрузить\nвложение'),
        (4.5,  3.8, 'Отменить заявку'),
    ]
    for x, y, t in uc_user:
        uc(ax, x, y, t)
        ax.plot([0.9 + 0.15, x - 1.4], [6.5 + (y - 6.5)*0.05, y],
                '-', color='#555', lw=1.0)

    # Use cases — Агент
    uc_agent = [
        (9.0, 11.5, 'Взять заявку\nв работу'),
        (9.0,  9.8, 'Изменить статус'),
        (9.0,  8.3, 'Назначить\nисполнителя'),
        (9.0,  6.8, 'Внутренний\nкомментарий'),
        (9.0,  5.3, 'Запросить\nинформацию'),
        (9.0,  3.8, 'Просмотреть\nотчёты (отдел)'),
    ]
    for x, y, t in uc_agent:
        uc(ax, x, y, t)
        ax.plot([9.0, x], [0.2 + 0.9, y - 0.28], '-', color='#375623', lw=1.0)

    # Use cases — Администратор
    uc_admin = [
        (13.5, 11.5, 'Управление\nпользователями'),
        (13.5,  9.8, 'Управление\nсправочниками'),
        (13.5,  8.3, 'Просмотр\nвсех заявок'),
        (13.5,  6.8, 'Экспорт\nотчётов'),
        (13.5,  5.3, 'Принудительное\nзакрытие'),
        (13.5,  3.8, 'Настройка\nSLA/типов'),
    ]
    for x, y, t in uc_admin:
        uc(ax, x, y, t)
        ax.plot([17.1 - 0.15, x + 1.4], [6.5 + (y - 6.5)*0.05, y],
                '-', color='#843C0C', lw=1.0)

    # Include: агент включает всё что пользователь + своё
    ax.annotate('', xy=(4.5 + 1.4, 8.3), xytext=(9.0 - 1.4, 8.3),
                arrowprops=dict(arrowstyle='-|>', color='#888', lw=1.0, linestyle='dashed'))
    ax.text(6.75, 8.5, '«include»', ha='center', fontsize=7.5, color='#888', style='italic')

    ax.annotate('', xy=(9.0 + 1.4, 8.3), xytext=(13.5 - 1.4, 8.3),
                arrowprops=dict(arrowstyle='-|>', color='#888', lw=1.0, linestyle='dashed'))
    ax.text(11.25, 8.5, '«include»', ha='center', fontsize=7.5, color='#888', style='italic')

    save(fig, '03_usecase.png')


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ДИАГРАММА ПОСЛЕДОВАТЕЛЬНОСТИ — создание заявки
# ═══════════════════════════════════════════════════════════════════════════════
def gen_sequence():
    fig, ax = plt.subplots(figsize=(18, 13))
    ax.set_xlim(0, 18); ax.set_ylim(0, 13)
    ax.axis('off')
    fig.suptitle('Диаграмма последовательности — создание заявки', fontsize=14, fontweight='bold')

    # Lifelines
    lifelines = [
        (1.5,  'Браузер\n(React)'),
        (4.5,  'FastAPI\n(Router)'),
        (7.5,  'TicketService'),
        (10.5, 'SLA Service'),
        (13.5, 'База данных\n(PostgreSQL)'),
        (16.5, 'Celery\n(Worker)'),
    ]

    for x, name in lifelines:
        # header box
        hb = FancyBboxPatch((x - 1.0, 12.0), 2.0, 0.7,
                            boxstyle="round,pad=0.05",
                            facecolor=C_ENT, edgecolor=C_LINE, lw=1.5)
        ax.add_patch(hb)
        ax.text(x, 12.35, name, ha='center', va='center', fontsize=8.5,
                color='white', fontweight='bold', fontfamily=FONT)
        # lifeline
        ax.plot([x, x], [0.3, 12.0], '--', color='#AAAAAA', lw=1.0, zorder=0)
        # activation box (narrow tall rectangle for active periods)

    def msg(y, x1, x2, text, ret=False, note=''):
        style = '<|-' if ret else '-|>'
        color = '#888' if ret else '#1F497D'
        ls = '--' if ret else '-'
        ax.annotate('', xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle=style, color=color, lw=1.5,
                                    connectionstyle='arc3,rad=0',
                                    linestyle=ls))
        lbl_x = (x1 + x2) / 2
        lbl_y = y + 0.15
        ax.text(lbl_x, lbl_y, text, ha='center', va='bottom', fontsize=8,
                color=color, fontfamily=FONT,
                bbox=dict(facecolor='white', edgecolor='none', pad=1))
        if note:
            ax.text(x2 + 0.15, y, note, ha='left', va='center', fontsize=7,
                    color='#666', style='italic', fontfamily=FONT)

    def activate(x, y_top, y_bot):
        act = FancyBboxPatch((x - 0.15, y_bot), 0.3, y_top - y_bot,
                             boxstyle="square,pad=0", facecolor='#BDD7EE', edgecolor='#4472C4', lw=1)
        ax.add_patch(act)

    # Messages top to bottom
    steps = [
        (11.5, 1.5, 4.5, 'POST /api/v1/tickets\n(JWT token, TicketCreate JSON)', False),
        (10.8, 4.5, 7.5, 'validate(data, user)',                False),
        (10.1, 7.5, 10.5, 'calculate_deadline(now, sla_hours)', False),
        ( 9.7, 10.5, 7.5, 'sla_deadline: datetime',            True),
        ( 9.0, 7.5, 13.5, 'GET priority, ticket_type',         False),
        ( 8.5, 13.5, 7.5, 'Priority, TicketType objects',      True),
        ( 7.8, 7.5, 13.5, 'INSERT INTO tickets ...',            False),
        ( 7.3, 13.5, 7.5, 'ticket_id: int',                    True),
        ( 6.6, 7.5, 13.5, 'INSERT INTO ticket_history ...',     False),
        ( 5.9, 7.5, 16.5, 'send_email.delay(ticket_id)',        False),
        ( 5.2, 16.5, 7.5, 'task_id: str',                      True),
        ( 4.5, 7.5,  4.5, 'Ticket object',                     True),
        ( 3.8, 4.5,  1.5, 'HTTP 201 Created\n{ticket JSON}',   True),
    ]
    for y, x1, x2, text, ret in steps:
        msg(y, x1, x2, text, ret)

    # Activation boxes
    activate(4.5,  12.0, 3.5)
    activate(7.5,  11.0, 4.2)
    activate(13.5,  9.1,  7.5)

    save(fig, '04_sequence.png')


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ДИАГРАММА СОСТОЯНИЙ — жизненный цикл заявки
# ═══════════════════════════════════════════════════════════════════════════════
def gen_statechart():
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 16); ax.set_ylim(0, 10)
    ax.axis('off')
    fig.suptitle('Диаграмма состояний — жизненный цикл заявки', fontsize=14, fontweight='bold')

    SW, SH = 3.2, 0.9

    # States
    states = {
        'new':          (3.0,  8.5, 'Новая',             '#D9E2F3', '#1F497D'),
        'in_progress':  (8.0,  8.5, 'В работе',          '#E2EFDA', '#375623'),
        'waiting_info': (8.0,  5.5, 'Ожидает\nинформации','#FFF2CC', '#7F6000'),
        'resolved':     (13.0, 8.5, 'Выполнена',         '#E2EFDA', '#375623'),
        'cancelled':    (3.0,  3.0, 'Отменена',          '#FCE4D6', '#843C0C'),
    }

    for key, (x, y, name, fc, ec) in states.items():
        box = FancyBboxPatch((x - SW/2, y - SH/2), SW, SH,
                             boxstyle="round,pad=0.12",
                             facecolor=fc, edgecolor=ec, lw=2.0)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center', fontsize=12,
                fontweight='bold', color=ec, fontfamily=FONT)

    # Start marker
    ax.plot(3.0, 10.0, 'o', markersize=16, color='black', zorder=5)
    ax.plot(3.0, 10.0, 'o', markersize=10, color='black', zorder=6)

    # End marker
    ax.plot(13.0, 3.0, 'o', markersize=16, color='black', zorder=5)
    ax.plot(13.0, 3.0, 'o', markersize=8, color='white', zorder=6)
    ax.plot(13.0, 3.0, 'o', markersize=10, color='black', zorder=7)

    def trans(ax, x1, y1, x2, y2, lbl, rad=0, color='#333'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=1.8,
                                    connectionstyle=f'arc3,rad={rad}'))
        mx = (x1 + x2) / 2 + (0.3 if rad > 0 else (-0.3 if rad < 0 else 0))
        my = (y1 + y2) / 2
        ax.text(mx, my, lbl, ha='center', va='center', fontsize=8.5,
                color=color, fontfamily=FONT,
                bbox=dict(facecolor='white', edgecolor='#aaa', pad=1.5, boxstyle='round'))

    # Transitions
    # Start → new
    ax.annotate('', xy=(3.0, 8.95), xytext=(3.0, 10.0 - 0.1),
                arrowprops=dict(arrowstyle='-|>', color='black', lw=2.0))

    # new → in_progress
    trans(ax, 3.0+SW/2, 8.5, 8.0-SW/2, 8.5, 'Взять в работу\n[агент/адм.]')
    # new → cancelled
    trans(ax, 3.0, 8.5-SH/2, 3.0, 3.0+SH/2, 'Отменить\n[пользов./агент/адм.]',
          color='#843C0C')
    # in_progress → waiting_info
    trans(ax, 8.0-SW/2+0.3, 8.5-SH/2, 8.0-SW/2+0.3, 5.5+SH/2,
          'Запросить\nинформацию\n[агент/адм.]', rad=0.3, color='#7F6000')
    # waiting_info → in_progress
    trans(ax, 8.0+SW/2-0.3, 5.5+SH/2, 8.0+SW/2-0.3, 8.5-SH/2,
          'Информация\nполучена\n[пользов./агент/адм.]', rad=0.3, color='#375623')
    # in_progress → resolved
    trans(ax, 8.0+SW/2, 8.5, 13.0-SW/2, 8.5, 'Завершить\n[агент/адм.]',
          color='#375623')
    # in_progress → cancelled
    trans(ax, 8.0, 8.5-SH/2, 3.0+SW/2, 3.0+SH/2, 'Отменить\n[агент/адм.]',
          rad=-0.2, color='#843C0C')
    # waiting_info → cancelled
    trans(ax, 8.0-SW/2, 5.5, 3.0+SW/2, 3.0+SH/2-0.1, 'Отменить\n[агент/адм.]',
          rad=0.15, color='#843C0C')
    # resolved → in_progress (reopen)
    trans(ax, 13.0, 8.5-SH/2, 8.0+SW/2-0.3, 8.5-SH/2+0.2,
          'Переоткрыть\n[пользов./адм.]', rad=0.4, color='#1F497D')

    # resolved/cancelled → End marker
    ax.annotate('', xy=(13.0, 3.0 + 0.1), xytext=(13.0, 8.5 - SH/2),
                arrowprops=dict(arrowstyle='-|>', color='black', lw=1.5, linestyle='dashed'))
    ax.annotate('', xy=(13.0 - 0.1, 3.0 + 0.1), xytext=(3.0 + SW/2, 3.0),
                arrowprops=dict(arrowstyle='-|>', color='black', lw=1.5, linestyle='dashed'))

    ax.text(10.5, 3.0, '«terminal»', fontsize=8, color='#666', style='italic', va='center')

    save(fig, '05_statechart.png')


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ДИАГРАММА РАЗВЁРТЫВАНИЯ
# ═══════════════════════════════════════════════════════════════════════════════
def gen_deployment():
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 16); ax.set_ylim(0, 10)
    ax.axis('off')
    fig.suptitle('Диаграмма развёртывания (Docker Compose)', fontsize=14, fontweight='bold')

    def node(ax, x, y, w, h, name, color=C_DEP, border=C_DEP_B):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                             facecolor=color, edgecolor=border, lw=2)
        ax.add_patch(box)
        # node "stereotype" double border at top
        top_bar = FancyBboxPatch((x, y + h - 0.5), w, 0.5,
                                 boxstyle="round,pad=0.05",
                                 facecolor=border, edgecolor=border, lw=1)
        ax.add_patch(top_bar)
        ax.text(x + w/2, y + h - 0.25, f'«node» {name}', ha='center', va='center',
                fontsize=9.5, fontweight='bold', color='white', fontfamily=FONT)

    def svc(ax, x, y, w, h, name, details=''):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                             facecolor=C_SVC, edgecolor='#4472C4', lw=1.5)
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2 + (0.15 if details else 0), name,
                ha='center', va='center', fontsize=10, fontweight='bold',
                color='#1F497D', fontfamily=FONT)
        if details:
            ax.text(x + w/2, y + h/2 - 0.25, details, ha='center', va='center',
                    fontsize=8, color='#444', fontfamily=FONT)

    def conn(ax, x1, y1, x2, y2, lbl='', ls='-'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='<|-|>', color='#555', lw=1.5,
                                    linestyle=ls, connectionstyle='arc3,rad=0'))
        if lbl:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx, my + 0.15, lbl, ha='center', va='bottom', fontsize=8,
                    color='#333', fontfamily=FONT,
                    bbox=dict(facecolor='white', edgecolor='#aaa', pad=1.0))

    # Browser
    node(ax, 0.3, 7.5, 3.5, 2.0, 'Client Browser')
    svc(ax, 0.6, 7.7, 2.9, 1.0, 'React SPA', 'React 18 + TypeScript')

    # Docker Host
    node(ax, 4.5, 0.5, 11.0, 9.0, 'Docker Host (сервер компании)')
    # Nginx
    svc(ax, 4.8, 7.8, 2.4, 1.0, 'Nginx', 'Reverse Proxy :80/443')
    # Backend
    svc(ax, 7.8, 7.8, 2.4, 1.0, 'FastAPI', 'uvicorn :8000')
    # Celery Worker
    svc(ax, 7.8, 5.8, 2.4, 1.0, 'Celery Worker', 'email + SLA tasks')
    # Celery Beat
    svc(ax, 7.8, 3.8, 2.4, 1.0, 'Celery Beat', 'scheduler')
    # PostgreSQL
    svc(ax, 11.2, 7.8, 2.4, 1.0, 'PostgreSQL 15', 'port: 5432')
    # Redis
    svc(ax, 11.2, 5.8, 2.4, 1.0, 'Redis 7', 'port: 6379')

    # Connections
    # Browser ↔ Nginx
    conn(ax, 3.8, 8.3, 4.8, 8.3, 'HTTPS :443')
    # Nginx → FastAPI
    conn(ax, 7.2, 8.3, 7.8, 8.3, 'HTTP :8000')
    # FastAPI → PostgreSQL
    conn(ax, 10.2, 8.3, 11.2, 8.3, 'asyncpg')
    # FastAPI → Redis
    conn(ax, 9.0, 7.8, 9.0, 6.8, 'aioredis')
    # Celery Worker → Redis
    conn(ax, 10.2, 6.3, 11.2, 6.3, 'broker')
    # Celery Worker → PostgreSQL
    conn(ax, 10.2, 6.1, 11.2, 7.8, '')
    # Celery Beat → Redis
    conn(ax, 9.0, 5.8, 9.0, 6.8, 'schedule')
    # Beat → Worker
    conn(ax, 9.0, 4.8, 9.0, 5.8, 'tasks')

    save(fig, '06_deployment.png')


# ═══════════════════════════════════════════════════════════════════════════════
# 7. ДИАГРАММА ДЕЯТЕЛЬНОСТИ — обработка заявки агентом
# ═══════════════════════════════════════════════════════════════════════════════
def gen_activity():
    fig, ax = plt.subplots(figsize=(10, 16))
    ax.set_xlim(0, 10); ax.set_ylim(0, 16)
    ax.axis('off')
    fig.suptitle('Диаграмма деятельности — обработка заявки агентом', fontsize=12, fontweight='bold')

    def act_box(x, y, text, w=4.5, h=0.7, color='#D9E2F3', ec='#2E5FA3'):
        box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                             boxstyle="round,pad=0.1",
                             facecolor=color, edgecolor=ec, lw=1.5)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=9, fontfamily=FONT)

    def diamond(x, y, text):
        pts = [[x, y+0.5], [x+1.0, y], [x, y-0.5], [x-1.0, y]]
        diam = plt.Polygon(pts, facecolor='#FFF2CC', edgecolor='#7F6000', lw=1.5)
        ax.add_patch(diam)
        ax.text(x, y, text, ha='center', va='center', fontsize=8, fontfamily=FONT)

    def down_arrow(x, y1, y2, lbl=''):
        ax.annotate('', xy=(x, y2), xytext=(x, y1),
                    arrowprops=dict(arrowstyle='-|>', color='#333', lw=1.5))
        if lbl:
            ax.text(x + 0.15, (y1+y2)/2, lbl, fontsize=8, color='#555', va='center', fontfamily=FONT)

    def side_arrow(x1, y, x2, lbl=''):
        ax.annotate('', xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle='-|>', color='#333', lw=1.5))
        if lbl:
            ax.text((x1+x2)/2, y+0.15, lbl, ha='center', fontsize=8, color='#555', fontfamily=FONT)

    # Start
    ax.plot(5, 15.5, 'o', markersize=16, color='black', zorder=5)
    down_arrow(5, 15.5-0.08, 15.05)

    act_box(5, 14.7, 'Пользователь создаёт заявку')
    down_arrow(5, 14.35, 13.85)
    act_box(5, 13.5, 'Система генерирует номер SD-XXXX,\nрассчитывает SLA дедлайн', h=0.8)
    down_arrow(5, 13.1, 12.6)
    act_box(5, 12.3, 'Заявка попадает в очередь\n(статус: Новая)', h=0.7)
    down_arrow(5, 11.95, 11.45)
    act_box(5, 11.1, 'Агент просматривает\nненазначенные заявки', h=0.7)
    down_arrow(5, 10.75, 10.25)
    diamond(5, 10.0, 'Берёт в\nработу?')
    # No path
    side_arrow(6.0, 10.0, 8.0, 'Нет')
    act_box(8.5, 10.0, 'Заявка остаётся\nв очереди', w=2.8, ec='#888', color='#F0F0F0')
    ax.annotate('', xy=(8.5, 11.1), xytext=(8.5, 10.35),
                arrowprops=dict(arrowstyle='->', color='#888', lw=1.0, linestyle='dashed'))
    ax.text(8.8, 10.7, 'Ждёт\nдругого\nагента', fontsize=7.5, color='#888', va='center', fontfamily=FONT)

    # Yes path
    down_arrow(5, 9.5, 9.0, 'Да')
    act_box(5, 8.65, 'Назначает себя исполнителем\n(статус: В работе)', h=0.7)
    down_arrow(5, 8.3, 7.8)
    diamond(5, 7.55, 'Нужна\nинфо?')
    side_arrow(4.0, 7.55, 2.0, 'Да')
    act_box(1.5, 7.55, 'Запросить\nинформацию', w=2.5, color='#FFF2CC', ec='#7F6000')
    ax.annotate('', xy=(1.5, 6.5), xytext=(1.5, 7.2),
                arrowprops=dict(arrowstyle='-|>', color='#7F6000', lw=1.2))
    act_box(1.5, 6.2, 'Пользователь\nотвечает', w=2.5, color='#FFF2CC', ec='#7F6000')
    ax.annotate('', xy=(4.0, 7.0), xytext=(1.5, 5.85),
                arrowprops=dict(arrowstyle='-|>', color='#7F6000', lw=1.2,
                                connectionstyle='arc3,rad=-0.4'))

    down_arrow(5, 7.05, 6.55, 'Нет')
    act_box(5, 6.2, 'Решить задачу,\nдобавить комментарий', h=0.7)
    down_arrow(5, 5.85, 5.35)
    act_box(5, 5.0, 'Изменить статус на\n«Выполнена»', h=0.7)
    down_arrow(5, 4.65, 4.15)
    act_box(5, 3.8, 'Система фиксирует событие\nв ticket_history', h=0.7)
    down_arrow(5, 3.45, 2.95)
    act_box(5, 2.6, 'Celery отправляет\nemail-уведомление пользователю', h=0.7)
    down_arrow(5, 2.25, 1.8)
    act_box(5, 1.5, 'Заявка закрыта', color='#E2EFDA', ec='#375623')
    down_arrow(5, 1.15, 0.75)
    # End
    ax.plot(5, 0.5, 'o', markersize=16, color='black', zorder=5)
    ax.plot(5, 0.5, 'o', markersize=8, color='white', zorder=6)
    ax.plot(5, 0.5, 'o', markersize=10, color='black', zorder=7)

    save(fig, '07_activity.png')


# ═══════════════════════════════════════════════════════════════════════════════
# 8. КОНТЕКСТНАЯ ДИАГРАММА (DFD Level 0)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_context_dfd():
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 16); ax.set_ylim(0, 10)
    ax.axis('off')
    fig.suptitle('Контекстная диаграмма (DFD Level 0)', fontsize=14, fontweight='bold')

    # Central system box
    sys_box = FancyBboxPatch((5.5, 3.5), 5.0, 3.0, boxstyle="round,pad=0.15",
                             facecolor='#EBF3FB', edgecolor=C_ENT, lw=2.5)
    ax.add_patch(sys_box)
    ax.text(8.0, 5.0, 'Система управления\nзаявками\nООО «Экспресс-технологии»',
            ha='center', va='center', fontsize=11, fontweight='bold', color=C_ENT, fontfamily=FONT)

    def ext_box(x, y, w, h, text):
        box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                             boxstyle="round,pad=0.1",
                             facecolor='#F2F2F2', edgecolor='#404040', lw=2)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=10,
                fontweight='bold', color='#333', fontfamily=FONT)

    def flow(ax, x1, y1, x2, y2, lbl, both=False, color='#1F497D'):
        style = '<|-|>' if both else '-|>'
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=style, color=color, lw=1.8,
                                    connectionstyle='arc3,rad=0'))
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my + 0.2, lbl, ha='center', va='bottom', fontsize=8.5,
                color=color, fontfamily=FONT,
                bbox=dict(facecolor='white', edgecolor='#aaa', pad=2, boxstyle='round'))

    # External entities
    ext_box(2.0, 8.0, 2.8, 1.0, 'Пользователь\n(клиент)')
    ext_box(2.0, 5.0, 2.8, 1.0, 'Агент\nподдержки')
    ext_box(2.0, 2.0, 2.8, 1.0, 'Администратор')
    ext_box(14.0, 7.5, 2.8, 1.0, 'SMTP-сервер\n(Email)')
    ext_box(14.0, 5.0, 2.8, 1.0, 'Файловая\nсистема')
    ext_box(14.0, 2.5, 2.8, 1.0, 'PostgreSQL\n+ Redis')

    # Flows from users to system
    flow(ax, 2.8+0.15, 8.0, 5.5, 6.0, 'Новая заявка,\nкомментарии, файлы')
    flow(ax, 5.5, 5.5, 2.8+0.15, 5.0, 'Статус заявки,\nуведомления', color='#375623')

    flow(ax, 2.8+0.15, 5.0, 5.5, 5.5, 'Смена статуса,\nназначение, ответы')
    flow(ax, 5.5, 5.0, 2.8+0.15, 4.8, 'Очередь заявок,\nистория, SLA-таймер', color='#375623')

    flow(ax, 2.8+0.15, 2.0, 5.5, 4.0, 'Управление польз.,\nсправочниками, отчёты')
    flow(ax, 5.5, 4.0, 2.8+0.15, 1.8, 'Аналитика,\nэкспорт данных', color='#843C0C')

    # Flows to external services
    flow(ax, 10.5, 6.0, 13.6, 7.5, 'Email-уведомления\n(MIME)')
    flow(ax, 10.5, 5.0, 13.6, 5.0, 'Загрузка/скачивание\nфайлов вложений', both=True)
    flow(ax, 10.5, 4.0, 13.6, 2.5, 'SQL-запросы /\nкэш Redis', both=True)

    save(fig, '08_context_dfd.png')


# ═══════════════════════════════════════════════════════════════════════════════
# 9–14. ЗАГЛУШКИ ДЛЯ СКРИНШОТОВ
# ═══════════════════════════════════════════════════════════════════════════════
def gen_placeholder(fname, title, description, color='#E8E8E8'):
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_xlim(0, 16); ax.set_ylim(0, 9)
    ax.axis('off')
    fig.patch.set_facecolor(color)

    border = FancyBboxPatch((0.3, 0.3), 15.4, 8.4,
                            boxstyle="round,pad=0.2",
                            facecolor='white', edgecolor='#AAAAAA', lw=3, linestyle='--')
    ax.add_patch(border)
    ax.text(8.0, 7.5, title, ha='center', va='center', fontsize=18,
            fontweight='bold', color='#444444', fontfamily=FONT)
    ax.text(8.0, 6.5, '[ СКРИНШОТ ]', ha='center', va='center', fontsize=24,
            color='#BBBBBB', fontfamily=FONT, style='italic')
    ax.text(8.0, 4.5, description, ha='center', va='center', fontsize=12,
            color='#555555', fontfamily=FONT,
            multialignment='center', wrap=True)
    ax.text(8.0, 1.5, '⚠  Замените этот блок реальным скриншотом', ha='center',
            va='center', fontsize=10, color='#AA4400', fontfamily=FONT,
            bbox=dict(facecolor='#FFF2CC', edgecolor='#FFC000', pad=6, boxstyle='round'))
    save(fig, fname)



# ═══════════════════════════════════════════════════════════════════════════════
# 9. КОНТЕКСТНАЯ ДИАГРАММА (IDEF0 A-0)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_idef0_context():
    fig, ax = plt.subplots(figsize=(22, 16))
    ax.set_xlim(0, 22); ax.set_ylim(0, 16)
    ax.axis('off')
    fig.suptitle('Контекстная диаграмма IDEF0 (уровень A-0)\n'
                 'Система автоматизации управления заявками ООО «Экспресс-технологии»',
                 fontsize=13, fontweight='bold', y=0.99)

    BX, BY, BW, BH = 5.5, 4.5, 11.0, 7.5
    box = FancyBboxPatch((BX, BY), BW, BH, boxstyle="square,pad=0",
                         facecolor='#EBF3FB', edgecolor='#1F497D', lw=3)
    ax.add_patch(box)
    ax.text(BX + BW - 0.2, BY + 0.2, 'A0', ha='right', va='bottom',
            fontsize=12, fontweight='bold', color='#1F497D', fontfamily=FONT)
    for txt, dy, fs, bold in [
        ('АВТОМАТИЗАЦИЯ УПРАВЛЕНИЯ', 1.2, 14, True),
        ('ЗАЯВКАМИ', 0.4, 14, True),
        ('ООО «Экспресс-технологии»', -0.5, 11, False),
        ('Приём, регистрация, распределение,', -1.3, 10, False),
        ('контроль исполнения и закрытие заявок', -2.0, 10, False),
    ]:
        ax.text(BX + BW/2, BY + BH/2 + dy, txt, ha='center', va='center',
                fontsize=fs, fontweight='bold' if bold else 'normal',
                color='#1F497D' if bold else '#444', fontfamily=FONT)

    ARROW_KW_L = dict(arrowstyle='-|>', color='#1F497D', lw=2.0)
    ARROW_KW_R = dict(arrowstyle='-|>', color='#375623', lw=2.0)
    ARROW_KW_T = dict(arrowstyle='-|>', color='#843C0C', lw=2.0)
    ARROW_KW_B = dict(arrowstyle='-|>', color='#7F6000', lw=2.0)

    def lbl_box(ax, x, y, text, ha='left', color='#222'):
        ax.text(x, y, text, ha=ha, va='center', fontsize=8.5,
                color=color, fontfamily=FONT,
                bbox=dict(facecolor='white', edgecolor='#aaa', pad=2.5, boxstyle='round'))

    # ── Входы (слева) ──
    for y, code, title, detail in [
        (10.8, 'И1', 'Обращения пользователей', '(данные заявки, комментарии, файлы)'),
        (8.4,  'И2', 'Учётные данные',          '(логин / email, пароль)'),
        (6.0,  'И3', 'Параметры фильтрации',     '(статус, период, приоритет, отдел)'),
    ]:
        ax.annotate('', xy=(BX, y), xytext=(0.4, y), arrowprops=ARROW_KW_L)
        ax.text(0.5, y + 0.28, f'{code}: {title}', ha='left', va='bottom',
                fontsize=9, fontweight='bold', color='#1F497D', fontfamily=FONT)
        ax.text(0.5, y - 0.28, detail, ha='left', va='top',
                fontsize=8, color='#555', fontfamily=FONT)

    # ── Выходы (справа) ──
    for y, code, title, detail in [
        (10.8, 'В1', 'Зарегистрированные заявки', '(номер SD-ГГГГ-НННН, статус, SLA-дедлайн)'),
        (8.4,  'В2', 'Уведомления',               '(Email + SSE real-time)'),
        (6.0,  'В3', 'Отчёты и аналитика',         '(CSV / XLSX, статистика SLA, KPI)'),
    ]:
        ax.annotate('', xy=(21.6, y), xytext=(BX + BW, y), arrowprops=ARROW_KW_R)
        ax.text(BX + BW + 0.2, y + 0.28, f'{code}: {title}', ha='left', va='bottom',
                fontsize=9, fontweight='bold', color='#375623', fontfamily=FONT)
        ax.text(BX + BW + 0.2, y - 0.28, detail, ha='left', va='top',
                fontsize=8, color='#555', fontfamily=FONT)

    # ── Управление (сверху) ──
    for x, code, title, detail in [
        (7.8,  'У1', 'SLA-регламент', 'нормативы по приоритетам'),
        (11.0, 'У2', 'Политика RBAC', 'роли: admin / agent / user'),
        (14.2, 'У3', 'Бизнес-правила', 'маршрутизация, переходы статусов'),
    ]:
        ax.annotate('', xy=(x, BY + BH), xytext=(x, 15.4), arrowprops=ARROW_KW_T)
        ax.text(x, 15.5, f'{code}: {title}', ha='center', va='bottom',
                fontsize=9, fontweight='bold', color='#843C0C', fontfamily=FONT)
        ax.text(x, 14.8, detail, ha='center', va='bottom',
                fontsize=8, color='#843C0C', fontfamily=FONT)

    # ── Механизмы (снизу) ──
    for x, code, title, detail in [
        (7.0,  'М1', 'FastAPI + Python 3.12', 'backend-фреймворк'),
        (9.2,  'М2', 'React 18 + TypeScript', 'frontend SPA'),
        (11.5, 'М3', 'PostgreSQL + SQLAlchemy', 'хранение данных'),
        (13.8, 'М4', 'Celery 5 + Redis 7', 'фоновые задачи'),
    ]:
        ax.annotate('', xy=(x, BY), xytext=(x, 0.7), arrowprops=ARROW_KW_B)
        ax.text(x, 0.6, f'{code}: {title}', ha='center', va='top',
                fontsize=8.5, fontweight='bold', color='#7F6000', fontfamily=FONT)
        ax.text(x, 0.15, detail, ha='center', va='top',
                fontsize=7.5, color='#7F6000', fontfamily=FONT)

    # Легенда
    ax.text(11.0, 2.2, 'И — Вход (Input)    В — Выход (Output)    У — Управление (Control)    М — Механизм (Mechanism)',
            ha='center', va='center', fontsize=9, color='#333', fontfamily=FONT,
            bbox=dict(facecolor='#FFFDE7', edgecolor='#888', pad=4, boxstyle='round'))

    save(fig, '09_idef0_context.png')


# ═══════════════════════════════════════════════════════════════════════════════
# 10. ФУНКЦИОНАЛЬНАЯ ДИАГРАММА (IDEF0 A0 — декомпозиция)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_idef0_functional():
    fig, ax = plt.subplots(figsize=(26, 20))
    ax.set_xlim(0, 26); ax.set_ylim(0, 20)
    ax.axis('off')
    fig.suptitle('Функциональная диаграмма IDEF0 (уровень A0) — декомпозиция процесса управления заявками',
                 fontsize=13, fontweight='bold', y=0.99)

    BW, BH = 4.5, 2.5

    def func_box(x, y, code, name, sub=''):
        box = FancyBboxPatch((x, y), BW, BH, boxstyle="square,pad=0",
                             facecolor='#EBF3FB', edgecolor='#1F497D', lw=2)
        ax.add_patch(box)
        ax.text(x + BW - 0.12, y + 0.12, code, ha='right', va='bottom',
                fontsize=9, fontweight='bold', color='#1F497D', fontfamily=FONT)
        ax.text(x + BW/2, y + BH/2 + (0.2 if sub else 0), name,
                ha='center', va='center', fontsize=10, fontweight='bold',
                color='#1F497D', fontfamily=FONT, multialignment='center')
        if sub:
            ax.text(x + BW/2, y + BH/2 - 0.4, sub, ha='center', va='center',
                    fontsize=8.5, color='#444', fontfamily=FONT, multialignment='center')

    # Позиции блоков (стaircase-паттерн IDEF0)
    boxes = [
        (0.8,  16.5, 'A01', 'Регистрация\nи аутентификация', 'пользователей'),
        (5.5,  13.5, 'A02', 'Приём и регистрация\nзаявок', '(валидация, нумерация)'),
        (10.2, 10.5, 'A03', 'Маршрутизация\nи назначение', '(отдел, исполнитель)'),
        (14.9, 7.5,  'A04', 'SLA-мониторинг\nи эскалация', '(расчёт, контроль)'),
        (19.6, 4.5,  'A05', 'Коммуникация\nи уведомления', '(SSE, email, история)'),
        (10.2, 1.2,  'A06', 'Аналитика\nи отчётность', '(статистика, экспорт)'),
    ]
    for x, y, code, name, sub in boxes:
        func_box(x, y, code, name, sub)

    def flow(x1, y1, x2, y2, lbl, color='#333', rad=0):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=1.6,
                                    connectionstyle=f'arc3,rad={rad}'))
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my + 0.18, lbl, ha='center', va='bottom', fontsize=7.5,
                color=color, fontfamily=FONT,
                bbox=dict(facecolor='white', edgecolor='#ccc', pad=1.5, boxstyle='round'))

    # Входы (левая граница → A01)
    for dy, lbl in [(0.7, 'Учётные данные'), (1.5, 'Запрос регистрации')]:
        ax.annotate('', xy=(0.8, 16.5 + dy), xytext=(0.1, 16.5 + dy),
                    arrowprops=dict(arrowstyle='-|>', color='#1F497D', lw=1.6))
        ax.text(0.15, 16.5 + dy + 0.1, lbl, ha='left', va='bottom',
                fontsize=8, color='#1F497D', fontfamily=FONT)

    # A01 → A02 (аутентифицированный пользователь)
    flow(0.8 + BW, 16.5 + BH/2, 5.5, 13.5 + BH/2,
         'Сессия пользователя\n(JWT-токен, роль)', color='#1F497D', rad=-0.2)

    # Входы для A02
    ax.annotate('', xy=(5.5, 13.5 + 1.8), xytext=(4.0, 13.5 + 1.8),
                arrowprops=dict(arrowstyle='-|>', color='#375623', lw=1.5))
    ax.text(4.1, 13.5 + 2.0, 'Данные заявки\n(тема, описание, тип)', ha='left',
            va='bottom', fontsize=8, color='#375623', fontfamily=FONT)

    # A02 → A03 (новая заявка)
    flow(5.5 + BW, 13.5 + BH/2, 10.2, 10.5 + BH/2,
         'Зарегистрированная заявка\n(SD-номер, SLA рассчитан)', color='#375623', rad=-0.15)

    # A02 → A05 (событие создания)
    flow(5.5 + BW/2, 13.5, 10.2 + BW/2, 1.2 + BH,
         'Событие: ticket_created', color='#555', rad=0.25)

    # A03 → A04 (назначенная заявка)
    flow(10.2 + BW, 10.5 + BH/2, 14.9, 7.5 + BH/2,
         'Назначенная заявка\n(исполнитель, отдел)', color='#843C0C', rad=-0.1)

    # A04 → A05 (SLA-нарушение → уведомление)
    flow(14.9 + BW, 7.5 + BH/2, 19.6, 4.5 + BH/2,
         'SLA-событие\n(нарушение, эскалация)', color='#C00000', rad=-0.1)

    # A03 → A05 (изменение статуса)
    flow(10.2 + BW, 10.5 + 0.6, 19.6, 4.5 + 1.8,
         'Изменение статуса\n(webhook event)', color='#555', rad=0.1)

    # A05 → A06 (данные для отчётности)
    flow(19.6 + BW/2, 4.5, 10.2 + BW + 0.5, 1.2 + BH/2,
         'История событий\n(для агрегации)', color='#555', rad=0.2)

    # A04 → A06 (данные SLA для отчётности)
    flow(14.9 + BW/2, 7.5, 10.2 + BW - 0.5, 1.2 + BH,
         'SLA-статистика', color='#7F6000', rad=-0.2)

    # Выходы (правая граница)
    for dy, lbl in [(1.8, 'Обработанная заявка\n(статус updated)'), (0.6, 'Email-уведомление')]:
        ax.annotate('', xy=(25.9, 4.5 + dy), xytext=(19.6 + BW, 4.5 + dy),
                    arrowprops=dict(arrowstyle='-|>', color='#375623', lw=1.5))
        ax.text(25.95, 4.5 + dy + 0.1, lbl, ha='left', va='bottom',
                fontsize=8, color='#375623', fontfamily=FONT)

    ax.annotate('', xy=(25.9, 1.2 + 1.3), xytext=(10.2 + BW, 1.2 + 1.3),
                arrowprops=dict(arrowstyle='-|>', color='#375623', lw=1.5))
    ax.text(25.95, 1.2 + 1.5, 'Отчёт (CSV/XLSX)', ha='left', va='bottom',
            fontsize=8, color='#375623', fontfamily=FONT)

    # Управляющие стрелки (сверху)
    for x, lbl in [(2.0, 'SLA-регламент'), (6.7, 'Политика RBAC'), (11.4, 'Бизнес-правила')]:
        ax.annotate('', xy=(x, 19.0), xytext=(x, 19.5),
                    arrowprops=dict(arrowstyle='-|>', color='#843C0C', lw=1.4))
        ax.text(x, 19.55, lbl, ha='center', va='bottom', fontsize=8,
                color='#843C0C', fontfamily=FONT)

    # Заголовок-нотация
    ax.text(1.0, 0.5, 'Нотация: IDEF0 A0  |  → Поток данных  |  ↑ Управление  |  Блоки: A01–A06',
            ha='left', va='bottom', fontsize=9, color='#333', fontfamily=FONT,
            bbox=dict(facecolor='#F5F5F5', edgecolor='#888', pad=4, boxstyle='round'))

    save(fig, '10_idef0_functional.png')


# ═══════════════════════════════════════════════════════════════════════════════
# 11. DFD УРОВЕНЬ 1 — декомпозиция (Data Flow Diagram)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_dfd_level1():
    fig, ax = plt.subplots(figsize=(26, 20))
    ax.set_xlim(0, 26); ax.set_ylim(0, 20)
    ax.axis('off')
    fig.suptitle('DFD-диаграмма потоков данных (Level 1) — Система управления заявками',
                 fontsize=13, fontweight='bold', y=0.99)

    def ext_entity(x, y, w, h, text):
        r = FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="square,pad=0",
                           facecolor='#F2F2F2', edgecolor='#404040', lw=2.5)
        ax.add_patch(r)
        r2 = FancyBboxPatch((x - w/2 + 0.12, y - h/2 + 0.12), w, h, boxstyle="square,pad=0",
                            facecolor='none', edgecolor='#404040', lw=1.5)
        ax.add_patch(r2)
        ax.text(x, y, text, ha='center', va='center', fontsize=9.5,
                fontweight='bold', color='#222', fontfamily=FONT, multialignment='center')

    def process(x, y, num, text):
        circle = plt.Circle((x, y), 1.4, facecolor='#D9E2F3', edgecolor='#2E5FA3', lw=2)
        ax.add_patch(circle)
        ax.text(x, y + 0.35, num, ha='center', va='center', fontsize=9,
                fontweight='bold', color='#1F497D', fontfamily=FONT)
        ax.text(x, y - 0.2, text, ha='center', va='center', fontsize=8.5,
                color='#1a1a1a', fontfamily=FONT, multialignment='center')

    def data_store(x, y, num, text, w=4.5):
        h = 0.65
        ax.plot([x, x + w], [y + h, y + h], color='#333', lw=2)
        ax.plot([x, x + w], [y, y], color='#333', lw=2)
        ax.plot([x, x], [y, y + h], color='#333', lw=2)
        box = FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0",
                             facecolor='#FFF2CC', edgecolor='none', lw=0)
        ax.add_patch(box)
        ax.text(x + 0.55, y + h/2, f'Д{num}', ha='center', va='center',
                fontsize=9, fontweight='bold', color='#7F6000', fontfamily=FONT)
        ax.plot([x + 1.0, x + 1.0], [y, y + h], color='#333', lw=1.5)
        ax.text(x + 1.2, y + h/2, text, ha='left', va='center',
                fontsize=9, color='#222', fontfamily=FONT)

    def flow(x1, y1, x2, y2, lbl, color='#1F497D', rad=0, lw=1.5):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=lw,
                                    connectionstyle=f'arc3,rad={rad}'))
        mx = (x1 + x2) / 2 + (-0.3 if rad < 0 else (0.3 if rad > 0 else 0))
        my = (y1 + y2) / 2 + 0.18
        ax.text(mx, my, lbl, ha='center', va='bottom', fontsize=7.5,
                color=color, fontfamily=FONT,
                bbox=dict(facecolor='white', edgecolor='#ddd', pad=1.5, boxstyle='round'))

    # Внешние сущности
    ext_entity(2.2, 17.5, 3.8, 1.6, 'Пользователь\n(заявитель)')
    ext_entity(2.2, 10.5, 3.8, 1.6, 'Агент\nподдержки')
    ext_entity(2.2, 3.5,  3.8, 1.6, 'Администратор')
    ext_entity(23.8, 14.0, 3.8, 1.6, 'SMTP-сервер\n(Email)')
    ext_entity(23.8, 7.0,  3.8, 1.6, 'Файловое\nхранилище')

    # Процессы
    process(8.5,  17.0, '1.1', 'Аутен-\nтификация')
    process(8.5,  12.5, '1.2', 'Создание\nзаявки')
    process(13.5, 15.5, '1.3', 'Обработка\nзаявки')
    process(13.5, 9.5,  '1.4', 'SLA-\nмониторинг')
    process(18.5, 13.0, '1.5', 'Уведом-\nления')
    process(18.5, 6.0,  '1.6', 'Отчёты\nи экспорт')

    # Хранилища данных
    data_store(10.5, 10.2, '1', 'Пользователи (users)')
    data_store(10.5, 7.5,  '2', 'Заявки (tickets)')
    data_store(10.5, 5.0,  '3', 'Комментарии (comments)')
    data_store(10.5, 2.5,  '4', 'История (ticket_history)')
    data_store(10.5, 0.3,  '5', 'Уведомления (notifications)')

    # Потоки данных
    # Пользователь
    flow(4.1, 17.5, 7.1, 17.2, 'Учётные данные', color='#1F497D')
    flow(7.1, 17.0, 4.1, 17.0, 'JWT-токен', color='#375623', rad=0.15)
    flow(4.1, 11.5, 7.1, 12.5, 'Данные заявки', color='#1F497D')
    flow(7.1, 12.2, 4.1, 10.8, 'Статус заявки', color='#375623', rad=0.1)

    # Агент
    flow(4.1, 10.5, 7.1, 10.8, 'Смена статуса,\nназначение', color='#375623', rad=-0.1)
    flow(4.1, 9.8,  7.1, 9.5,  'Комментарий', color='#375623', rad=0.1)

    # Администратор
    flow(4.1, 3.5, 17.1, 6.0, 'Запрос отчёта', color='#843C0C', rad=-0.1)
    flow(17.1, 5.5, 4.1, 2.8, 'Отчёт (CSV/XLSX)', color='#375623', rad=0.15)

    # 1.1 ↔ Д1
    flow(8.5, 15.6, 12.5, 10.8, 'Проверка\nпользователя', color='#555', rad=0.1)
    flow(12.5, 10.4, 8.5, 15.6, 'Данные\nпользователя', color='#555', rad=0.2)

    # 1.2 → Д2
    flow(8.5, 11.1, 12.5, 7.8, 'Сохранить заявку', color='#1F497D')
    flow(8.5, 11.1, 12.5, 5.3, 'Сохранить\nкомментарий', color='#375623', rad=0.15)

    # 1.3 ↔ Д2
    flow(13.5, 14.1, 12.5, 8.2, 'Обновить заявку', color='#843C0C', rad=-0.1)
    flow(12.5, 7.2,  13.5, 14.1, 'Данные заявки', color='#555', rad=-0.2)

    # 1.3 → Д4
    flow(13.5, 14.1, 14.5, 2.8, 'Запись в историю', color='#555', rad=-0.15)

    # 1.4 ↔ Д2
    flow(13.5, 8.1, 14.5, 7.8, 'Читать SLA-дедлайны', color='#7F6000', rad=0.1)
    flow(14.5, 7.2, 13.5, 8.1, 'Список заявок', color='#555', rad=0.2)

    # 1.4 → 1.5
    flow(14.9, 9.5, 17.1, 12.5, 'SLA-нарушение', color='#C00000')

    # 1.3 → 1.5
    flow(14.9, 15.5, 17.1, 13.2, 'Событие изменения', color='#555', rad=0.1)

    # 1.5 → SMTP
    flow(19.9, 13.0, 21.9, 14.0, 'Email-сообщение', color='#1F497D')

    # 1.5 → Д5
    flow(18.5, 11.6, 14.5, 0.6, 'Сохранить уведомление', color='#555', rad=0.2)

    # Вложения ↔ Файловое хранилище
    flow(14.9, 9.2, 21.9, 7.0, 'Путь к файлу', color='#555', rad=-0.1)
    flow(21.9, 6.5, 14.5, 5.3, 'Файл вложения', color='#555', rad=0.1)

    # 1.6 ↔ Д2, Д4
    flow(18.5, 4.6, 14.5, 7.7, 'SQL-запрос\n(агрегация)', color='#843C0C', rad=0.1)
    flow(18.5, 4.6, 14.5, 2.8, 'История событий', color='#843C0C', rad=-0.1)

    # Легенда
    legend_items = [
        ('Внешняя сущность', '#F2F2F2', '#404040'),
        ('Процесс', '#D9E2F3', '#2E5FA3'),
        ('Хранилище данных', '#FFF2CC', '#B8860B'),
    ]
    lx, ly = 0.5, 0.4
    for i, (lbl, fc, ec) in enumerate(legend_items):
        r = FancyBboxPatch((lx + i * 4.5, ly - 0.2), 1.2, 0.55,
                           boxstyle="round,pad=0.05", facecolor=fc, edgecolor=ec, lw=1.5)
        ax.add_patch(r)
        ax.text(lx + i * 4.5 + 1.35, ly + 0.07, lbl, ha='left', va='center',
                fontsize=8, color='#333', fontfamily=FONT)

    save(fig, '11_dfd_level1.png')


# ═══════════════════════════════════════════════════════════════════════════════
# 12. ДИАГРАММА КОММУНИКАЦИЙ (UML Communication Diagram)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_communication():
    fig, ax = plt.subplots(figsize=(24, 16))
    ax.set_xlim(0, 24); ax.set_ylim(0, 16)
    ax.axis('off')
    fig.suptitle('Диаграмма коммуникаций — сценарий создания заявки',
                 fontsize=13, fontweight='bold', y=0.99)

    OBJ_W, OBJ_H = 3.6, 0.8

    def obj_box(x, y, name, stereotype=''):
        box = FancyBboxPatch((x - OBJ_W/2, y - OBJ_H/2), OBJ_W, OBJ_H,
                             boxstyle="round,pad=0.07",
                             facecolor='#D9E2F3', edgecolor='#2E5FA3', lw=2)
        ax.add_patch(box)
        if stereotype:
            ax.text(x, y + 0.16, f'«{stereotype}»', ha='center', va='center',
                    fontsize=7.5, color='#555', fontfamily=FONT, style='italic')
            ax.text(x, y - 0.12, f':{name}', ha='center', va='center',
                    fontsize=9, fontweight='bold', color='#1F497D', fontfamily=FONT)
        else:
            ax.text(x, y, f':{name}', ha='center', va='center',
                    fontsize=9.5, fontweight='bold', color='#1F497D', fontfamily=FONT)

    # Объекты (координаты центров)
    objects = {
        'Браузер':          (2.5,  14.5),
        'Nginx':            (7.5,  14.5),
        'FastAPI Router':   (13.5, 14.5),
        'AuthMiddleware':   (19.5, 14.5),
        'TicketService':    (12.0, 9.5),
        'SLAService':       (4.5,  9.5),
        'NotificationSvc':  (20.0, 9.5),
        'PostgreSQL':       (8.0,  4.5),
        'Redis':            (16.0, 4.5),
        'CeleryWorker':     (21.5, 4.5),
    }
    for name, (x, y) in objects.items():
        st = ''
        if name in ('PostgreSQL', 'Redis'):
            st = 'database'
        elif name in ('Nginx',):
            st = 'component'
        elif name in ('CeleryWorker',):
            st = 'process'
        obj_box(x, y, name, st)

    def msg(x1, y1, x2, y2, num, text, ret=False, rad=0, offset=0.2):
        color = '#888' if ret else '#1F497D'
        ls = '--' if ret else '-'
        style = '<|-' if ret else '-|>'
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=style, color=color, lw=1.6,
                                    connectionstyle=f'arc3,rad={rad}',
                                    linestyle=ls))
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2 + offset
        ax.text(mx, my, f'{num}: {text}', ha='center', va='bottom',
                fontsize=8, color=color, fontfamily=FONT,
                bbox=dict(facecolor='white', edgecolor='none', pad=1))

    # Линия-связь между объектами
    def link(x1, y1, x2, y2):
        ax.plot([x1, x2], [y1, y2], '-', color='#AAAAAA', lw=1.2, zorder=0)

    # Связи
    link(2.5, 14.5, 7.5, 14.5)
    link(7.5, 14.5, 13.5, 14.5)
    link(13.5, 14.5, 19.5, 14.5)
    link(13.5, 14.5, 12.0, 10.3)
    link(19.5, 14.5, 12.0, 10.3)
    link(12.0, 10.3, 4.5, 10.3)
    link(12.0, 9.1, 8.0, 4.9)
    link(12.0, 9.1, 16.0, 4.9)
    link(12.0, 9.5, 20.0, 9.5)
    link(20.0, 9.1, 21.5, 4.9)

    # Сообщения
    msg(2.5,  14.9,  7.5,  14.9,  '1', 'HTTP POST /api/v1/tickets', rad=0.15, offset=0.3)
    msg(7.5,  14.9,  13.5, 14.9,  '2', 'proxy_pass :8000/api/v1/tickets', rad=0.15, offset=0.3)
    msg(13.5, 14.1, 19.5, 14.1,  '3', 'verify_token(JWT)', rad=-0.15, offset=-0.4)
    msg(19.5, 14.1, 13.5, 14.1,  '4', 'UserContext(id, role)', ret=True, rad=0.15, offset=-0.4)
    msg(13.5, 14.1, 12.0, 10.3,  '5', 'create_ticket(data, user)', offset=0.25)
    msg(12.0, 10.3,  4.5, 10.3,  '6', 'calc_deadline(sla_hours)', offset=0.25)
    msg(4.5,  10.3, 12.0, 10.3,  '7', 'sla_deadline: datetime', ret=True, rad=0.2, offset=-0.4)
    msg(12.0,  9.1,  8.0,  4.9,  '8', 'INSERT INTO tickets ...', offset=0.2)
    msg(8.0,   4.9, 12.0,  9.1,  '9', 'ticket_id: int', ret=True, rad=0.2, offset=-0.35)
    msg(12.0,  9.1,  8.0,  4.5, '10', 'INSERT INTO ticket_history ...', rad=-0.1, offset=0.2)
    msg(12.0,  9.5, 20.0,  9.5, '11', 'notify(ticket_id, event)', offset=0.25)
    msg(20.0,  9.1, 16.0,  4.9, '12', 'PUBLISH ticket_channel', offset=0.2)
    msg(20.0,  9.1, 21.5,  4.9, '13', 'send_email.delay()', offset=0.2)
    msg(12.0, 14.1, 13.5, 14.1, '14', 'TicketResponse (201 Created)', ret=True, rad=-0.15, offset=-0.4)
    msg(7.5,  14.1,  2.5, 14.1, '15', 'HTTP 201 {ticket JSON}', ret=True, rad=-0.15, offset=-0.4)

    # Нотация
    ax.text(0.5, 0.5, 'Нотация: UML 2.5 Communication Diagram  |  → прямой вызов  |  - - → возврат  '
            '|  Числа — порядок сообщений',
            ha='left', va='bottom', fontsize=9, color='#333', fontfamily=FONT,
            bbox=dict(facecolor='#F5F5F5', edgecolor='#888', pad=4, boxstyle='round'))

    save(fig, '12_communication.png')


# ═══════════════════════════════════════════════════════════════════════════════
# 13. ДИАГРАММА КЛАССОВ (UML Class Diagram)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_class_diagram():
    fig, ax = plt.subplots(figsize=(28, 22))
    ax.set_xlim(0, 28); ax.set_ylim(0, 22)
    ax.axis('off')
    fig.suptitle('Диаграмма классов — ключевые классы системы управления заявками',
                 fontsize=13, fontweight='bold', y=0.99)

    CW = 5.5

    def uml_class(x, y, name, attrs, methods, stereotype=None, color='#D9E2F3', border='#2E5FA3'):
        row_h = 0.38
        name_h = 0.65 if not stereotype else 0.85
        attrs_h = max(len(attrs), 1) * row_h + 0.15
        meth_h  = max(len(methods), 1) * row_h + 0.15
        total_h = name_h + attrs_h + meth_h

        # Header
        hdr = FancyBboxPatch((x, y - name_h), CW, name_h,
                             boxstyle="square,pad=0", facecolor=color, edgecolor=border, lw=2)
        ax.add_patch(hdr)
        if stereotype:
            ax.text(x + CW/2, y - 0.22, f'«{stereotype}»', ha='center', va='center',
                    fontsize=8, color='#555', fontfamily=FONT, style='italic')
            ax.text(x + CW/2, y - 0.58, name, ha='center', va='center',
                    fontsize=10, fontweight='bold', color='#1a3a6b', fontfamily=FONT)
        else:
            ax.text(x + CW/2, y - name_h/2, name, ha='center', va='center',
                    fontsize=10.5, fontweight='bold', color='#1a3a6b', fontfamily=FONT)

        # Атрибуты
        abg = FancyBboxPatch((x, y - name_h - attrs_h), CW, attrs_h,
                             boxstyle="square,pad=0", facecolor='#F0F4FB', edgecolor=border, lw=1.2)
        ax.add_patch(abg)
        ax.plot([x, x + CW], [y - name_h, y - name_h], '-', color=border, lw=1.2)
        for i, attr in enumerate(attrs):
            ay = y - name_h - 0.12 - (i + 0.5) * row_h
            ax.text(x + 0.18, ay, attr, ha='left', va='center', fontsize=7.5,
                    color='#222', fontfamily=FONT)

        # Методы
        mbg = FancyBboxPatch((x, y - total_h), CW, meth_h,
                             boxstyle="square,pad=0", facecolor='white', edgecolor=border, lw=1.2)
        ax.add_patch(mbg)
        ax.plot([x, x + CW], [y - name_h - attrs_h, y - name_h - attrs_h],
                '-', color=border, lw=1.2)
        for i, m in enumerate(methods):
            my = y - name_h - attrs_h - 0.12 - (i + 0.5) * row_h
            ax.text(x + 0.18, my, m, ha='left', va='center', fontsize=7.5,
                    color='#333', fontfamily=FONT, style='italic')

        return y - total_h  # bottom coordinate

    # ── Модели ────────────────────────────────────────────────────────────────

    # User
    user_bot = uml_class(0.5, 21.5, 'User', [
        '+ id: int  [PK]',
        '+ email: str  [UNIQUE]',
        '+ username: str  [UNIQUE]',
        '+ password_hash: str',
        '+ full_name: str',
        '+ role: UserRole  {admin|agent|user}',
        '+ department_id: int | None  [FK]',
        '+ is_active: bool = True',
        '+ is_email_verified: bool = False',
        '+ created_at: datetime',
    ], [
        '+ verify_password(plain: str): bool',
        '+ set_password(plain: str): None',
    ], stereotype='entity', color='#D9E2F3', border='#2E5FA3')

    # Department
    dept_bot = uml_class(0.5, user_bot - 0.5, 'Department', [
        '+ id: int  [PK]',
        '+ name: str  [UNIQUE]',
        '+ description: str | None',
        '+ is_active: bool = True',
    ], [
        '+ __repr__(): str',
    ], stereotype='entity', color='#D9E2F3', border='#2E5FA3')

    # Priority
    uml_class(0.5, dept_bot - 0.5, 'Priority', [
        '+ id: int  [PK]',
        '+ name: str  [UNIQUE]',
        '+ level: PriorityLevel  {low|normal|high|critical}',
        '+ sla_hours: float',
        '+ color_hex: str',
        '+ sort_order: int',
    ], [
        '+ __repr__(): str',
    ], stereotype='entity', color='#D9E2F3', border='#2E5FA3')

    # Ticket
    ticket_bot = uml_class(7.0, 21.5, 'Ticket', [
        '+ id: int  [PK]',
        '+ number: str  [UNIQUE]  e.g. SD-2026-00001',
        '+ title: str',
        '+ description: str',
        '+ status: TicketStatus',
        '+ priority_id: int  [FK → priorities]',
        '+ type_id: int  [FK → ticket_types]',
        '+ requester_id: int  [FK → users]',
        '+ assignee_id: int | None  [FK → users]',
        '+ department_id: int | None  [FK → departments]',
        '+ sla_deadline: datetime | None',
        '+ sla_violated: bool = False',
        '+ merged_into_id: int | None  [FK → tickets]',
        '+ created_at: datetime',
        '+ updated_at: datetime',
        '+ closed_at: datetime | None',
    ], [
        '+ is_overdue(): bool',
        '+ can_transition_to(status): bool',
        '+ get_sla_remaining(): timedelta',
    ], stereotype='entity', color='#E2EFDA', border='#375623')

    # Comment
    uml_class(7.0, ticket_bot - 0.5, 'Comment', [
        '+ id: int  [PK]',
        '+ ticket_id: int  [FK → tickets]',
        '+ author_id: int | None  [FK → users]',
        '+ body: str',
        '+ is_internal: bool = False',
        '+ created_at: datetime',
        '+ updated_at: datetime',
    ], [
        '+ __repr__(): str',
    ], stereotype='entity', color='#D9E2F3', border='#2E5FA3')

    # TicketHistory
    uml_class(13.5, 21.5, 'TicketHistory', [
        '+ id: int  [PK]',
        '+ ticket_id: int  [FK → tickets]',
        '+ user_id: int | None  [FK → users]',
        '+ event_type: str',
        '+ payload: dict  [JSONB]',
        '+ created_at: datetime',
    ], [
        '+ get_display_text(): str',
    ], stereotype='entity', color='#D9E2F3', border='#2E5FA3')

    # TicketService
    ts_bot = uml_class(13.5, 16.0, 'TicketService', [
        '- db: AsyncSession',
        '- redis: Redis',
        '- notification_svc: NotificationService',
    ], [
        '+ create_ticket(data, user): Ticket',
        '+ get_ticket(id, user): Ticket',
        '+ list_tickets(filters, user): list[Ticket]',
        '+ change_status(id, status, user): Ticket',
        '+ assign_ticket(id, assignee_id, user): Ticket',
        '+ add_comment(id, body, user): Comment',
        '+ upload_attachment(id, file, user): Attachment',
        '+ merge_tickets(src_id, dst_id, user): Ticket',
        '+ generate_number(year): str',
        '+ _record_history(ticket, event, user): None',
    ], stereotype='service', color='#FFF2CC', border='#7F6000')

    # AuthService
    uml_class(13.5, ts_bot - 0.5, 'AuthService', [
        '- db: AsyncSession',
        '- redis: Redis',
        '- pwd_ctx: CryptContext',
    ], [
        '+ login(username, password): tuple[str, str]',
        '+ logout(token: str): None',
        '+ refresh(refresh_token): str',
        '+ register(data): User',
        '+ verify_email(token): bool',
        '+ _create_token(user_id, type): str',
        '+ _hash_password(plain): str',
    ], stereotype='service', color='#FFF2CC', border='#7F6000')

    # NotificationService
    uml_class(20.5, 21.5, 'NotificationService', [
        '- redis: Redis',
        '- db: AsyncSession',
    ], [
        '+ publish(event_type, ticket, user): None',
        '+ stream(user_id): AsyncGenerator',
        '+ get_unread(user_id): list[Notification]',
        '+ mark_read(ids, user): None',
    ], stereotype='service', color='#FFF2CC', border='#7F6000')

    # TicketCreate (Pydantic)
    uml_class(20.5, 14.0, 'TicketCreate', [
        '+ title: str  [max=500]',
        '+ description: str',
        '+ type_id: int',
        '+ priority_id: int',
        '+ department_id: int | None',
        '+ assignee_id: int | None',
    ], [
        '+ model_validate(data): TicketCreate',
    ], stereotype='schema', color='#FCE4D6', border='#843C0C')

    # TicketResponse (Pydantic)
    uml_class(20.5, 9.0, 'TicketResponse', [
        '+ id: int',
        '+ number: str',
        '+ title: str',
        '+ status: str',
        '+ priority: PriorityInfo',
        '+ creator_name: str',
        '+ assignee_name: str | None',
        '+ sla_deadline: datetime | None',
        '+ sla_violated: bool',
        '+ tags: list[TagResponse]',
        '+ created_at: datetime',
    ], [
        '+ model_validate(orm_obj): TicketResponse',
        '+ from_orm(ticket): TicketResponse',
    ], stereotype='schema', color='#FCE4D6', border='#843C0C')

    # ── Связи ─────────────────────────────────────────────────────────────────
    def assoc(x1, y1, x2, y2, lbl='', mult1='', mult2='', rad=0, color='#555', dashed=False):
        ls = '--' if dashed else '-'
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=1.5,
                                    connectionstyle=f'arc3,rad={rad}',
                                    linestyle=ls))
        if lbl:
            mx = (x1+x2)/2 + 0.2
            my = (y1+y2)/2 + 0.15
            ax.text(mx, my, lbl, ha='center', va='bottom', fontsize=7.5,
                    color=color, fontfamily=FONT,
                    bbox=dict(facecolor='white', edgecolor='none', pad=1))
        if mult1:
            ax.text(x1 + 0.2, y1, mult1, ha='left', va='center',
                    fontsize=8, color='#888', fontfamily=FONT)
        if mult2:
            ax.text(x2 + 0.2, y2, mult2, ha='left', va='center',
                    fontsize=8, color='#888', fontfamily=FONT)

    # Ticket → User (requester)
    assoc(7.0, 19.0, 6.0, 19.0, 'создаёт', mult1='1', mult2='*', color='#2E5FA3', rad=-0.3)
    # Ticket → Department
    assoc(7.0, 17.5, 6.0, 14.0, 'принадлежит', color='#2E5FA3', rad=0.15)
    # Ticket → Comment (1:N)
    assoc(7.0 + CW/2, ticket_bot, 7.0 + CW/2, ticket_bot - 0.3, '1 : N', color='#375623')
    # Ticket → TicketHistory (1:N)
    assoc(7.0 + CW, 20.0, 13.5, 20.0, '1 : N', color='#2E5FA3')
    # TicketService → Ticket (creates/manages)
    assoc(13.5, 14.5, 12.5, 14.5, '<<creates>>', color='#7F6000', dashed=True, rad=0.1)
    # TicketService → NotificationService (uses)
    assoc(13.5 + CW, 14.0, 20.5, 20.0, '<<uses>>', color='#7F6000', dashed=True, rad=-0.15)
    # TicketCreate → Ticket (maps to)
    assoc(20.5, 12.5, 12.5, 12.5, '<<instantiates>>', color='#843C0C', dashed=True)
    # TicketResponse ← Ticket (derived from)
    assoc(20.5, 8.0, 12.5, 10.0, '<<serializes>>', color='#843C0C', dashed=True, rad=0.15)
    # User → Department (FK)
    assoc(0.5 + CW/2, user_bot, 0.5 + CW/2, user_bot - 0.05, 'FK', color='#555')

    # Легенда
    leg_items = [
        ('─►  Ассоциация', '#2E5FA3', False),
        ('- -► Зависимость (use/create)', '#7F6000', True),
        ('──   Связь 1:N', '#375623', False),
    ]
    for i, (txt, col, dash) in enumerate(leg_items):
        ax.text(0.5 + i * 8.5, 0.5, txt, ha='left', va='center',
                fontsize=9, color=col, fontfamily=FONT,
                bbox=dict(facecolor='white', edgecolor='#ccc', pad=3, boxstyle='round'))

    save(fig, '13_class_diagram.png')


# ═══════════════════════════════════════════════════════════════════════════════
# 14. СХЕМА ИНТЕГРАЦИИ ПРОГРАММНЫХ МОДУЛЕЙ
# ═══════════════════════════════════════════════════════════════════════════════
def gen_integration_schema():
    fig, ax = plt.subplots(figsize=(26, 20))
    ax.set_xlim(0, 26); ax.set_ylim(0, 20)
    ax.axis('off')
    fig.suptitle('Схема интеграции программных модулей\nСистема управления заявками ООО «Экспресс-технологии»',
                 fontsize=13, fontweight='bold', y=0.99)

    def layer_bg(y_bot, y_top, label, color, lcolor):
        r = FancyBboxPatch((0.3, y_bot), 25.4, y_top - y_bot,
                           boxstyle="round,pad=0.2", facecolor=color, edgecolor=lcolor, lw=2)
        ax.add_patch(r)
        ax.text(0.65, (y_bot + y_top) / 2, label, ha='left', va='center',
                fontsize=11, fontweight='bold', color=lcolor, fontfamily=FONT, rotation=90)

    def mod_box(x, y, w, h, text, facecolor='#EBF3FB', edgecolor='#2E5FA3', fs=8.5):
        r = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                           facecolor=facecolor, edgecolor=edgecolor, lw=1.8)
        ax.add_patch(r)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center',
                fontsize=fs, fontweight='bold', color='#1a3a6b', fontfamily=FONT,
                multialignment='center')

    def conn_arrow(x1, y1, x2, y2, lbl='', color='#555', rad=0, dashed=False):
        ls = '--' if dashed else '-'
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=1.5,
                                    connectionstyle=f'arc3,rad={rad}', linestyle=ls))
        if lbl:
            mx = (x1+x2)/2 + 0.1
            my = (y1+y2)/2 + 0.15
            ax.text(mx, my, lbl, ha='center', va='bottom', fontsize=7.5,
                    color=color, fontfamily=FONT,
                    bbox=dict(facecolor='white', edgecolor='#ddd', pad=1.5, boxstyle='round'))

    # ── Слои ──────────────────────────────────────────────────────────────────
    layer_bg(14.0, 19.5, 'Frontend\n(React)', '#F0F7FF', '#2E5FA3')
    layer_bg(6.5,  13.5, 'Backend\n(FastAPI)', '#F0FFF0', '#375623')
    layer_bg(0.3,  6.0,  'Инфра-\nструктура', '#FFFDE7', '#7F6000')

    # ── Frontend модули ───────────────────────────────────────────────────────
    # Страницы
    pages = [
        (1.3, 17.3, 3.0, 1.5, 'LoginPage\n/portal/login'),
        (4.8, 17.3, 3.0, 1.5, 'TicketsListPage\n/tickets'),
        (8.3, 17.3, 3.0, 1.5, 'TicketDetailPage\n/tickets/:id'),
        (11.8, 17.3, 3.0, 1.5, 'ReportsPage\n/reports'),
        (15.3, 17.3, 3.0, 1.5, 'AdminPage\n/admin'),
        (18.8, 17.3, 3.0, 1.5, 'PortalPage\n/portal/*'),
    ]
    for x, y, w, h, t in pages:
        mod_box(x, y, w, h, t, '#D9E2F3', '#2E5FA3')

    # Компоненты
    comps = [
        (1.3,  14.8, 2.8, 1.2, 'TicketForm'),
        (4.5,  14.8, 2.8, 1.2, 'FilterPanel'),
        (7.7,  14.8, 2.8, 1.2, 'SLACountdown'),
        (10.9, 14.8, 3.2, 1.2, 'ActivityTimeline'),
        (14.5, 14.8, 2.8, 1.2, 'TagSelector'),
        (17.7, 14.8, 2.8, 1.2, 'NotesTab'),
        (20.9, 14.8, 3.3, 1.2, 'useSSE (hook)'),
    ]
    for x, y, w, h, t in comps:
        mod_box(x, y, w, h, t, '#BDD7EE', '#2E5FA3', fs=8)

    # API-слой (frontend)
    api_fe = [
        (1.5, 14.1, 3.0, 0.5, 'api/auth.ts'),
        (5.0, 14.1, 3.0, 0.5, 'api/tickets.ts'),
        (8.5, 14.1, 3.0, 0.5, 'api/attachments.ts'),
        (12.0, 14.1, 2.5, 0.5, 'api/tags.ts'),
        (15.0, 14.1, 2.5, 0.5, 'api/reports.ts'),
        (18.0, 14.1, 2.5, 0.5, 'api/users.ts'),
    ]
    for x, y, w, h, t in api_fe:
        mod_box(x, y, w, h, t, '#DEEBF7', '#2E5FA3', fs=8)

    # ── Backend модули ────────────────────────────────────────────────────────
    # Роутеры
    routers = [
        (1.3, 11.5, 2.5, 1.0, 'auth\nrouter'),
        (4.3, 11.5, 2.5, 1.0, 'tickets\nrouter'),
        (7.3, 11.5, 2.5, 1.0, 'users\nrouter'),
        (10.3, 11.5, 2.5, 1.0, 'comments\nrouter'),
        (13.3, 11.5, 2.5, 1.0, 'attachments\nrouter'),
        (16.3, 11.5, 2.5, 1.0, 'tags\nrouter'),
        (19.3, 11.5, 2.5, 1.0, 'notes\nrouter'),
    ]
    for x, y, w, h, t in routers:
        mod_box(x, y, w, h, t, '#C6EFCE', '#375623', fs=8)

    # Сервисы
    services = [
        (1.5, 9.5, 3.5, 1.0, 'AuthService'),
        (5.5, 9.5, 3.5, 1.0, 'TicketService'),
        (9.5, 9.5, 3.5, 1.0, 'NotificationService'),
        (13.5, 9.5, 3.5, 1.0, 'EmailService'),
        (17.5, 9.5, 3.5, 1.0, 'SLAService'),
    ]
    for x, y, w, h, t in services:
        mod_box(x, y, w, h, t, '#E2EFDA', '#375623')

    # Модели
    models = [
        (1.5, 7.5, 2.8, 1.0, 'User'),
        (4.8, 7.5, 2.8, 1.0, 'Ticket'),
        (8.1, 7.5, 2.8, 1.0, 'Comment'),
        (11.4, 7.5, 2.8, 1.0, 'Attachment'),
        (14.7, 7.5, 2.8, 1.0, 'TicketHistory'),
        (18.0, 7.5, 2.8, 1.0, 'Tag / Note'),
    ]
    for x, y, w, h, t in models:
        mod_box(x, y, w, h, t, '#D9E2F3', '#2E5FA3')

    # Схемы Pydantic
    schemas = [
        (1.5, 6.7, 2.8, 0.65, 'UserSchema'),
        (4.8, 6.7, 2.8, 0.65, 'TicketSchema'),
        (8.1, 6.7, 2.8, 0.65, 'CommentSchema'),
        (11.4, 6.7, 3.5, 0.65, 'AttachmentSchema'),
        (15.4, 6.7, 3.5, 0.65, 'HistorySchema'),
    ]
    for x, y, w, h, t in schemas:
        mod_box(x, y, w, h, t, '#FCE4D6', '#843C0C', fs=7.5)

    # ── Инфраструктура ────────────────────────────────────────────────────────
    infra = [
        (1.5, 3.5, 3.5, 1.8, 'Nginx 1.25\n:80 / :443\nReverse Proxy\n+ Static Files'),
        (5.5, 3.5, 3.5, 1.8, 'FastAPI\nUvicorn :8000\nasync workers'),
        (9.5, 3.5, 3.5, 1.8, 'PostgreSQL 15\n:5432\nAsyncpg driver\nAlembic migrations'),
        (13.5, 3.5, 3.5, 1.8, 'Redis 7\n:6379\nBroker + Cache\n+ JWT blocklist'),
        (17.5, 3.5, 3.5, 1.8, 'Celery Worker\nQueues: default,sla\nEmail + SLA tasks'),
        (21.5, 3.5, 3.5, 1.8, 'Celery Beat\nScheduler\nSLA check\nevery 5 min'),
    ]
    for x, y, w, h, t in infra:
        mod_box(x, y, w, h, t, '#FFF2CC', '#7F6000')

    # ── Стрелки соединений ────────────────────────────────────────────────────
    # Browser → Nginx
    conn_arrow(0.5, 16.0, 1.5, 5.3, 'HTTPS', '#1F497D', rad=0.3)
    # API-слой → Backend routers
    for x_fe, x_be in [(3.0, 2.55), (6.5, 5.55), (10.0, 14.55)]:
        conn_arrow(x_fe, 14.1, x_be, 12.5, '', '#1F497D')
    # Routers → Services
    for x in [2.55, 5.55, 8.55, 11.55, 14.55]:
        conn_arrow(x, 11.5, x, 10.5, '', '#375623')
    # Services → Models
    for x_s, x_m in [(3.25, 2.9), (7.25, 6.2), (11.25, 9.5), (15.25, 16.1)]:
        conn_arrow(x_s, 9.5, x_m, 8.5, '', '#2E5FA3')
    # Models → DB
    conn_arrow(9.5, 7.5, 11.25, 5.3, 'SQLAlchemy\nORM', '#2E5FA3', rad=0.2)
    # Redis ← Services
    conn_arrow(11.25, 9.5, 15.25, 5.3, 'aioredis', '#7F6000', rad=-0.15, dashed=True)
    # Celery ← Services
    conn_arrow(15.25, 9.5, 19.25, 5.3, 'task.delay()', '#7F6000', rad=-0.1, dashed=True)
    # Nginx → FastAPI
    conn_arrow(5.0, 4.4, 7.0, 4.4, 'proxy_pass', '#555')

    # Легенда
    ax.text(0.6, 0.25, '─►  HTTP/REST вызов    - -►  Асинхронная задача    SQLAlchemy → ORM-запрос    Все контейнеры под Docker Compose',
            ha='left', va='bottom', fontsize=9, color='#333', fontfamily=FONT,
            bbox=dict(facecolor='white', edgecolor='#888', pad=4, boxstyle='round'))

    save(fig, '14_integration_schema.png')


# ─── RUN ALL ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('Генерация диаграмм...')
    gen_er_conceptual()
    gen_er_logical()
    gen_usecase()
    gen_sequence()
    gen_statechart()
    gen_deployment()
    gen_activity()
    gen_context_dfd()

    print('Генерация новых диаграмм...')
    gen_idef0_context()
    gen_idef0_functional()
    gen_dfd_level1()
    gen_communication()
    gen_class_diagram()
    gen_integration_schema()

    print('Генерация заглушек для скриншотов...')
    placeholders = [
        ('ph_01_login.png',
         'Рисунок X – Страница входа в систему',
         'Экран авторизации: поля «Логин» и «Пароль»,\n'
         'кнопка «Войти», логотип системы.\n'
         'Адрес: http://localhost:3000/login'),
        ('ph_02_tickets_list.png',
         'Рисунок X – Список заявок',
         'Главная страница агента/администратора:\n'
         'таблица заявок с колонками Номер, Тема, Статус, Приоритет, Исполнитель, Дедлайн SLA.\n'
         'Панель фильтров слева. Несколько заявок в таблице.'),
        ('ph_03_ticket_create.png',
         'Рисунок X – Форма создания заявки',
         'Форма создания заявки: поля Тема, Описание,\n'
         'Тип заявки (выпадающий список), Приоритет (выпадающий список),\n'
         'кнопка «Создать заявку».'),
        ('ph_04_ticket_detail.png',
         'Рисунок X – Карточка заявки',
         'Страница просмотра заявки: номер SD-XXXX, статус, SLA-таймер,\n'
         'блок информации (тема, описание, заявитель, исполнитель),\n'
         'лента истории действий, блок комментариев.'),
        ('ph_05_reports.png',
         'Рисунок X – Страница отчётов',
         'Страница аналитики: карточки со статистикой (всего заявок, закрыто, нарушено SLA),\n'
         'график распределения по статусам, таблица среднего времени обработки.'),
        ('ph_06_admin_users.png',
         'Рисунок X – Управление пользователями',
         'Административная страница: таблица пользователей\n'
         'с колонками ФИО, Email, Роль, Отдел, Статус.\n'
         'Кнопки «Добавить», «Редактировать», «Деактивировать».'),
    ]
    for fname, title, desc in placeholders:
        gen_placeholder(fname, title, desc)

    print(f'\nВсе файлы сохранены в: {OUT}')
