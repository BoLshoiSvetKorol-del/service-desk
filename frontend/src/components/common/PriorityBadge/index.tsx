import { Tag } from 'antd'
import type { PriorityName } from '../../../types/ticket'
import { PRIORITY_LABELS } from '../../../types/ticket'

const PRIORITY_COLORS: Record<PriorityName, string> = {
  low: 'default',
  normal: 'blue',
  high: 'orange',
  critical: 'red',
}

export default function PriorityBadge({ name }: { name: PriorityName }) {
  return <Tag color={PRIORITY_COLORS[name]}>{PRIORITY_LABELS[name]}</Tag>
}
