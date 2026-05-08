import { Tag } from 'antd'
import type { TicketStatus } from '../../../types/ticket'
import { STATUS_LABELS } from '../../../types/ticket'

const STATUS_COLORS: Record<TicketStatus, string> = {
  new: 'blue',
  in_progress: 'cyan',
  waiting_info: 'gold',
  resolved: 'green',
  cancelled: 'default',
}

export default function StatusBadge({ status }: { status: TicketStatus }) {
  return <Tag color={STATUS_COLORS[status]}>{STATUS_LABELS[status]}</Tag>
}
