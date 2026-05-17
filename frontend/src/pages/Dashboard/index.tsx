import { useEffect, useRef, useState } from 'react'
import { Alert, Card, Col, Row, Statistic, Table, Typography } from 'antd'
import {
  FileTextOutlined, ClockCircleOutlined,
  ExclamationCircleOutlined, SyncOutlined,
} from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import type { ColumnsType } from 'antd/es/table'
import client from '../../api/client'
import { getTickets } from '../../api/tickets'
import type { TicketListItem, TicketStatus, PriorityName } from '../../types/ticket'
import { useAuthStore } from '../../store/authStore'
import PriorityBadge from '../../components/common/PriorityBadge'
import StatusBadge from '../../components/common/StatusBadge'
import SLACountdown from '../../components/common/SLACountdown'

interface Stats {
  total: number
  newCount: number
  overdue: number
  waiting: number
}

interface DashboardCache {
  stats: Stats
  recentTickets: TicketListItem[]
  violations: TicketListItem[]
  ts: number
}

const CACHE_TTL_MS = 30_000
const CACHE_KEY = 'dashboard_cache'

function readCache(): DashboardCache | null {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY)
    if (!raw) return null
    const data: DashboardCache = JSON.parse(raw)
    if (Date.now() - data.ts > CACHE_TTL_MS) return null
    return data
  } catch {
    return null
  }
}

function writeCache(data: Omit<DashboardCache, 'ts'>) {
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({ ...data, ts: Date.now() }))
  } catch {}
}

const recentColumns: ColumnsType<TicketListItem> = [
  {
    title: 'Номер',
    dataIndex: 'number',
    width: 140,
    render: (num: string, r) => <Link to={`/tickets/${r.id}`}>{num}</Link>,
  },
  {
    title: 'Заголовок',
    dataIndex: 'title',
    render: (t: string) => (
      <Typography.Text ellipsis={{ tooltip: t }} style={{ maxWidth: 240, display: 'block' }}>
        {t}
      </Typography.Text>
    ),
  },
  {
    title: 'Приоритет',
    dataIndex: ['priority', 'name'],
    width: 120,
    render: (n: PriorityName) => <PriorityBadge name={n} />,
  },
  {
    title: 'Статус',
    dataIndex: 'status',
    width: 150,
    render: (s: TicketStatus) => <StatusBadge status={s} />,
  },
  {
    title: 'SLA',
    width: 100,
    render: (_, r) => (
      <SLACountdown
        slaDeadline={r.sla_deadline}
        slaViolated={r.sla_violated}
        createdAt={r.created_at}
      />
    ),
  },
]

export default function DashboardPage() {
  const user = useAuthStore(s => s.user)
  const navigate = useNavigate()
  const canEdit = user?.role === 'admin' || user?.role === 'agent' || user?.role === 'department_head'

  const [stats, setStats] = useState<Stats>({ total: 0, newCount: 0, overdue: 0, waiting: 0 })
  const [recentTickets, setRecentTickets] = useState<TicketListItem[]>([])
  const [violations, setViolations] = useState<TicketListItem[]>([])
  const [loading, setLoading] = useState(true)
  const loadedRef = useRef(false)

  useEffect(() => {
    const cached = readCache()
    if (cached) {
      setStats(cached.stats)
      setRecentTickets(cached.recentTickets)
      setViolations(cached.violations)
      setLoading(false)
      loadedRef.current = true
      return
    }

    setLoading(true)
    Promise.all([
      client.get<{ total: number; new_count: number; overdue: number; waiting: number }>('/dashboard/stats'),
      getTickets({ page_size: 5 }),
      canEdit ? getTickets({ sla_violated: true, page_size: 5 }) : Promise.resolve(null),
    ])
      .then(([statsRes, recent, violRes]) => {
        const s: Stats = {
          total: statsRes.data.total,
          newCount: statsRes.data.new_count,
          overdue: statsRes.data.overdue,
          waiting: statsRes.data.waiting,
        }
        const viols = violRes ? violRes.items : []
        setStats(s)
        setRecentTickets(recent.items)
        setViolations(viols)
        writeCache({ stats: s, recentTickets: recent.items, violations: viols })
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [canEdit])

  return (
    <div>
      <Typography.Title level={4} style={{ marginBottom: 20 }}>
        Добро пожаловать, {user?.full_name}!
      </Typography.Title>

      {/* Stats cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
        <Col xs={12} sm={6}>
          <Card loading={loading}>
            <Statistic
              title="Мои заявки"
              value={stats.total}
              prefix={<FileTextOutlined style={{ color: '#1677ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card loading={loading}>
            <Statistic
              title="Новые"
              value={stats.newCount}
              prefix={<ClockCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={stats.newCount > 0 ? { color: '#52c41a' } : undefined}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card loading={loading}>
            <Statistic
              title="Просрочено"
              value={stats.overdue}
              prefix={<ExclamationCircleOutlined style={{ color: '#f5222d' }} />}
              valueStyle={stats.overdue > 0 ? { color: '#f5222d' } : undefined}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card loading={loading}>
            <Statistic
              title="Ожидают ответа"
              value={stats.waiting}
              prefix={<SyncOutlined style={{ color: '#fa8c16' }} />}
              valueStyle={stats.waiting > 0 ? { color: '#fa8c16' } : undefined}
            />
          </Card>
        </Col>
      </Row>

      {/* SLA violations alert (admin/agent) */}
      {canEdit && violations.length > 0 && (
        <Alert
          type="error"
          style={{ marginBottom: 20 }}
          message={`Просроченные заявки (${stats.overdue})`}
          description={
            <div style={{ marginTop: 8 }}>
              {violations.map(t => (
                <div key={t.id} style={{ marginBottom: 4 }}>
                  <Link to={`/tickets/${t.id}`}>
                    <strong>{t.number}</strong>
                  </Link>
                  {' — '}
                  <Typography.Text ellipsis style={{ maxWidth: 300, display: 'inline-block', verticalAlign: 'middle' }}>
                    {t.title}
                  </Typography.Text>
                  {' '}
                  <PriorityBadge name={t.priority.name} />
                </div>
              ))}
              {stats.overdue > 5 && (
                <Link to="/tickets?sla_violated=true">Показать все →</Link>
              )}
            </div>
          }
          showIcon
        />
      )}

      {/* Recent tickets */}
      <Card title="Последние заявки">
        <Table<TicketListItem>
          dataSource={recentTickets}
          columns={recentColumns}
          rowKey="id"
          loading={loading}
          pagination={false}
          size="small"
          onRow={r => ({ onClick: () => navigate(`/tickets/${r.id}`), style: { cursor: 'pointer' } })}
          footer={() => (
            <Link to="/tickets" style={{ fontSize: 13 }}>
              Все заявки →
            </Link>
          )}
        />
      </Card>
    </div>
  )
}
