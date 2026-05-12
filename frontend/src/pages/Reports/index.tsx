import { useEffect, useState } from 'react'
import {
  Button, Card, Col, DatePicker, Empty, Progress, Row,
  Select, Space, Statistic, Tooltip, Typography, message,
} from 'antd'
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  getTicketsCount, getTicketsByStatus, getAvgResolutionTime,
  getSLACompliance, exportTickets,
} from '../../api/reports'
import { getDepartments } from '../../api/departments'
import type {
  CountDataPoint, StatusDataPoint, AvgResolutionDataPoint, SLAComplianceData, ReportParams,
} from '../../api/reports'
import type { Department } from '../../types/user'
import type { TicketStatus, PriorityName } from '../../types/ticket'
import { STATUS_LABELS, PRIORITY_LABELS } from '../../types/ticket'

const { RangePicker } = DatePicker

const STATUS_COLORS: Record<string, string> = {
  new: '#1677ff',
  in_progress: '#13c2c2',
  waiting_info: '#d48806',
  resolved: '#52c41a',
  cancelled: '#8c8c8c',
}

const PRIORITY_COLORS: Record<string, string> = {
  low: '#8c8c8c',
  normal: '#1677ff',
  high: '#fa8c16',
  critical: '#f5222d',
}

function BarChart({ data }: { data: CountDataPoint[] }) {
  if (data.length === 0) return <Empty description="Нет данных" style={{ padding: '32px 0' }} />
  const max = Math.max(...data.map(d => d.count), 1)
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', height: 200, gap: 6, padding: '0 8px', overflowX: 'auto' }}>
      {data.map(item => (
        <Tooltip key={item.period} title={`${item.period}: ${item.count} заявок`}>
          <div style={{ minWidth: 28, flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            {item.count > 0 && (
              <Typography.Text style={{ fontSize: 10, color: '#666' }}>{item.count}</Typography.Text>
            )}
            <div
              style={{
                width: '100%',
                height: `${Math.max((item.count / max) * 160, item.count > 0 ? 4 : 0)}px`,
                backgroundColor: '#1677ff',
                borderRadius: '3px 3px 0 0',
              }}
            />
            <Typography.Text style={{ fontSize: 10, color: '#888', writingMode: 'vertical-rl', transform: 'rotate(180deg)', maxHeight: 60 }}>
              {item.period.slice(5)}
            </Typography.Text>
          </div>
        </Tooltip>
      ))}
    </div>
  )
}

function StatusDistributionChart({ data }: { data: StatusDataPoint[] }) {
  if (data.length === 0) return <Empty description="Нет данных" style={{ padding: '32px 0' }} />
  const total = data.reduce((s, d) => s + d.count, 0)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {data.map(item => {
        const pct = total > 0 ? Math.round((item.count / total) * 100) : 0
        const label = STATUS_LABELS[item.status as TicketStatus] ?? item.status
        const color = STATUS_COLORS[item.status] ?? '#8c8c8c'
        return (
          <div key={item.status}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <Typography.Text style={{ fontSize: 13 }}>{label}</Typography.Text>
              <Typography.Text style={{ fontSize: 13, color: '#666' }}>
                {item.count} ({pct}%)
              </Typography.Text>
            </div>
            <Progress
              percent={pct}
              strokeColor={color}
              showInfo={false}
              size="small"
            />
          </div>
        )
      })}
    </div>
  )
}

function AvgResolutionChart({ data }: { data: AvgResolutionDataPoint[] }) {
  if (data.length === 0) return <Empty description="Нет данных" style={{ padding: '32px 0' }} />
  return (
    <Row gutter={[16, 16]}>
      {data.map(item => {
        const label = PRIORITY_LABELS[item.priority as PriorityName] ?? item.priority
        const color = PRIORITY_COLORS[item.priority] ?? '#666'
        return (
          <Col key={item.priority} xs={12} sm={6}>
            <Statistic
              title={label}
              value={item.avg_hours != null ? item.avg_hours.toFixed(1) : '—'}
              suffix={item.avg_hours != null ? 'ч' : ''}
              valueStyle={{ color }}
            />
          </Col>
        )
      })}
    </Row>
  )
}

function SLAComplianceBlock({ data }: { data: SLAComplianceData | null }) {
  if (!data) return <Empty description="Нет данных" style={{ padding: '32px 0' }} />
  const pct = Math.round(data.compliance_rate)
  const color = pct >= 90 ? '#52c41a' : pct >= 70 ? '#fa8c16' : '#f5222d'
  return (
    <Row gutter={32} align="middle">
      <Col>
        <Progress type="circle" percent={pct} strokeColor={color} size={120} />
      </Col>
      <Col>
        <Statistic
          title="Выполнено в срок"
          value={data.compliant}
          suffix={<Typography.Text type="secondary"> / {data.total}</Typography.Text>}
          valueStyle={{ color }}
        />
        <Typography.Text type="secondary" style={{ fontSize: 13 }}>заявок</Typography.Text>
      </Col>
    </Row>
  )
}

export default function ReportsPage() {
  const [params, setParams] = useState<ReportParams>({ groupby: 'day' })
  const [departments, setDepartments] = useState<Department[]>([])
  const [countData, setCountData] = useState<CountDataPoint[]>([])
  const [statusData, setStatusData] = useState<StatusDataPoint[]>([])
  const [avgData, setAvgData] = useState<AvgResolutionDataPoint[]>([])
  const [slaData, setSlaData] = useState<SLAComplianceData | null>(null)
  const [loading, setLoading] = useState(false)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    getDepartments().then(setDepartments).catch(() => {})
  }, [])

  useEffect(() => {
    loadReports()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params])

  async function loadReports() {
    setLoading(true)
    try {
      const [count, status, avg, sla] = await Promise.all([
        getTicketsCount(params),
        getTicketsByStatus(params),
        getAvgResolutionTime(params),
        getSLACompliance(params),
      ])
      setCountData(count)
      setStatusData(status)
      setAvgData(avg)
      setSlaData(sla)
    } catch {
      message.error('Ошибка загрузки отчётов')
    } finally {
      setLoading(false)
    }
  }

  async function handleExport(format: 'csv' | 'xlsx') {
    setExporting(true)
    try {
      await exportTickets(format, params)
    } catch {
      message.error('Ошибка экспорта')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Отчёты</Typography.Title>
        <Space>
          <Button
            icon={<DownloadOutlined />}
            loading={exporting}
            onClick={() => handleExport('xlsx')}
          >
            Excel
          </Button>
          <Button
            icon={<DownloadOutlined />}
            loading={exporting}
            onClick={() => handleExport('csv')}
          >
            CSV
          </Button>
          <Button icon={<ReloadOutlined />} loading={loading} onClick={loadReports} />
        </Space>
      </div>

      {/* Filters */}
      <Card style={{ marginBottom: 20 }}>
        <Space wrap>
          <RangePicker
            placeholder={['Дата от', 'Дата до']}
            onChange={(_, strings) => {
              const [from, to] = strings as [string, string]
              setParams(prev => ({ ...prev, date_from: from || undefined, date_to: to || undefined }))
            }}
            format="DD.MM.YYYY"
          />
          <Select
            placeholder="Отдел"
            allowClear
            style={{ width: 180 }}
            onChange={v => setParams(prev => ({ ...prev, department_id: v ?? undefined }))}
            options={departments.map(d => ({ value: d.id, label: d.name }))}
          />
          <Select
            value={params.groupby ?? 'day'}
            style={{ width: 140 }}
            onChange={v => setParams(prev => ({ ...prev, groupby: v }))}
            options={[
              { value: 'day', label: 'По дням' },
              { value: 'week', label: 'По неделям' },
              { value: 'month', label: 'По месяцам' },
            ]}
          />
        </Space>
      </Card>

      <Row gutter={[16, 16]}>
        {/* Tickets count chart */}
        <Col xs={24} lg={14}>
          <Card title="Количество заявок" loading={loading}>
            <BarChart data={countData} />
          </Card>
        </Col>

        {/* SLA compliance */}
        <Col xs={24} lg={10}>
          <Card title="Соответствие SLA" loading={loading}>
            <SLAComplianceBlock data={slaData} />
          </Card>
        </Col>

        {/* Status distribution */}
        <Col xs={24} md={12}>
          <Card title="Распределение по статусам" loading={loading}>
            <StatusDistributionChart data={statusData} />
          </Card>
        </Col>

        {/* Avg resolution time */}
        <Col xs={24} md={12}>
          <Card title="Среднее время выполнения" loading={loading}>
            <AvgResolutionChart data={avgData} />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
