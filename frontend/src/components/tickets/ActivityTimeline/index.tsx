import { Timeline, Typography } from 'antd'
import {
  FileAddOutlined, SwapOutlined, UserOutlined, ExclamationCircleOutlined,
  CommentOutlined, PaperClipOutlined, InfoCircleOutlined, CheckCircleOutlined,
  CloseCircleOutlined, MergeCellsOutlined,
} from '@ant-design/icons'
import type { TicketHistory, TicketStatus, PriorityName } from '../../../types/ticket'
import { STATUS_LABELS, PRIORITY_LABELS } from '../../../types/ticket'

function formatDate(d: string) {
  return new Date(d).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function describeEvent(event: TicketHistory): string {
  const p = event.payload ?? {}
  switch (event.event_type) {
    case 'created':
      return 'Заявка создана'
    case 'status_changed': {
      const from = STATUS_LABELS[p.old_status as TicketStatus] ?? p.old_status ?? '?'
      const to = STATUS_LABELS[p.new_status as TicketStatus] ?? p.new_status ?? '?'
      return `Статус изменён: ${from} → ${to}`
    }
    case 'assigned': {
      const parts: string[] = []
      if (p.new_assignee_name) parts.push(`Исполнитель: ${p.new_assignee_name}`)
      else if ('new_assignee_id' in p && p.new_assignee_id === null) parts.push('Исполнитель снят')
      if (p.new_department_name) parts.push(`Отдел: ${p.new_department_name}`)
      return parts.join(', ') || 'Назначение обновлено'
    }
    case 'priority_changed': {
      const from = PRIORITY_LABELS[p.old_priority_name as PriorityName] ?? p.old_priority_name ?? '?'
      const to = PRIORITY_LABELS[p.new_priority_name as PriorityName] ?? p.new_priority_name ?? '?'
      return `Приоритет изменён: ${from} → ${to}`
    }
    case 'updated':
      return 'Заявка обновлена'
    case 'merged':
      return `Объединена с заявкой ${p.target_number ?? ''}`
    case 'comment_added':
      return 'Добавлен комментарий'
    case 'attachment_added':
      return `Файл прикреплён${p.filename ? `: ${p.filename}` : ''}`
    case 'attachment_deleted':
      return 'Файл удалён'
    default:
      return event.event_type.replace(/_/g, ' ')
  }
}

function getEventIcon(event: TicketHistory) {
  const p = event.payload ?? {}
  switch (event.event_type) {
    case 'created':
      return <FileAddOutlined style={{ color: '#52c41a' }} />
    case 'status_changed':
      if (p.new_status === 'resolved') return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      if (p.new_status === 'cancelled') return <CloseCircleOutlined style={{ color: '#f5222d' }} />
      return <SwapOutlined style={{ color: '#1677ff' }} />
    case 'assigned':
      return <UserOutlined style={{ color: '#722ed1' }} />
    case 'priority_changed':
      return <ExclamationCircleOutlined style={{ color: '#fa8c16' }} />
    case 'merged':
      return <MergeCellsOutlined style={{ color: '#722ed1' }} />
    case 'comment_added':
      return <CommentOutlined style={{ color: '#8c8c8c' }} />
    case 'attachment_added':
    case 'attachment_deleted':
      return <PaperClipOutlined style={{ color: '#8c8c8c' }} />
    default:
      return <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
  }
}

function getEventColor(event: TicketHistory): string {
  const p = event.payload ?? {}
  switch (event.event_type) {
    case 'created': return 'green'
    case 'status_changed':
      if (p.new_status === 'resolved') return 'green'
      if (p.new_status === 'cancelled') return 'red'
      return 'blue'
    case 'assigned': return 'purple'
    case 'priority_changed': return 'orange'
    case 'merged': return 'purple'
    default: return 'gray'
  }
}

interface Props {
  history: TicketHistory[]
}

export default function ActivityTimeline({ history }: Props) {
  if (history.length === 0) {
    return <Typography.Text type="secondary">История пуста</Typography.Text>
  }

  const sorted = [...history].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )

  return (
    <Timeline
      mode="left"
      items={sorted.map(event => ({
        key: event.id,
        dot: getEventIcon(event),
        color: getEventColor(event),
        label: (
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            {formatDate(event.created_at)}
          </Typography.Text>
        ),
        children: (
          <div>
            <div>{describeEvent(event)}</div>
            {event.user_name && (
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                {event.user_name}
              </Typography.Text>
            )}
          </div>
        ),
      }))}
    />
  )
}
