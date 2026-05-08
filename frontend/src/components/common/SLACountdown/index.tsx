import { useEffect, useState } from 'react'
import { Tag, Tooltip } from 'antd'

interface Props {
  slaDeadline: string | null
  slaViolated: boolean
  createdAt: string
}

function formatRemaining(ms: number): string {
  const h = Math.floor(ms / 3_600_000)
  const m = Math.floor((ms % 3_600_000) / 60_000)
  if (h > 0) return `${h}ч ${m}м`
  return `${m}м`
}

function getColor(pct: number): string {
  if (pct > 0.5) return 'green'
  if (pct > 0.25) return 'gold'
  return 'orange'
}

export default function SLACountdown({ slaDeadline, slaViolated, createdAt }: Props) {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 60_000)
    return () => clearInterval(id)
  }, [])

  if (!slaDeadline) return null

  const deadline = new Date(slaDeadline).getTime()
  const created = new Date(createdAt).getTime()
  const total = deadline - created
  const remaining = deadline - now

  if (slaViolated || remaining <= 0) {
    return <Tag color="red">Просрочено</Tag>
  }

  const pct = remaining / total
  const deadlineStr = new Date(slaDeadline).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })

  return (
    <Tooltip title={`Дедлайн: ${deadlineStr}`}>
      <Tag color={getColor(pct)}>{formatRemaining(remaining)}</Tag>
    </Tooltip>
  )
}
