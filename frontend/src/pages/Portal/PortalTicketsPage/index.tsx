import { useEffect, useState } from 'react'
import { Badge, Button, Card, Input, Select, Space, Table, Tag, Typography, message } from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { getTickets } from '../../../api/tickets'
import type { TicketListItem } from '../../../types/ticket'
import { STATUS_LABELS, PRIORITY_LABELS } from '../../../types/ticket'
import SLACountdown from '../../../components/common/SLACountdown'

const STATUS_COLOR: Record<string, string> = {
  new: 'blue', in_progress: 'cyan', waiting_info: 'gold',
  resolved: 'green', cancelled: 'default', merged: 'purple',
}

export default function PortalTicketsPage() {
  const navigate = useNavigate()
  const [tickets, setTickets] = useState<TicketListItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>()

  useEffect(() => {
    setLoading(true)
    getTickets({
      page,
      page_size: 10,
      search: search || undefined,
      status: statusFilter,
    })
      .then(res => { setTickets(res.items); setTotal(res.total) })
      .catch(() => message.error('Ошибка загрузки заявок'))
      .finally(() => setLoading(false))
  }, [page, search, statusFilter])

  const columns = [
    {
      title: '№',
      dataIndex: 'number',
      render: (number: string, row: TicketListItem) => (
        <Button type="link" style={{ padding: 0 }} onClick={() => navigate(`/portal/tickets/${row.id}`)}>
          {number}
        </Button>
      ),
      width: 130,
    },
    {
      title: 'Тема',
      dataIndex: 'title',
      render: (title: string, row: TicketListItem) => (
        <Button type="link" style={{ padding: 0, textAlign: 'left', height: 'auto', whiteSpace: 'normal' }}
          onClick={() => navigate(`/portal/tickets/${row.id}`)}>
          {title}
        </Button>
      ),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      width: 150,
      render: (s: string) => (
        <Tag color={STATUS_COLOR[s] ?? 'default'}>{STATUS_LABELS[s as keyof typeof STATUS_LABELS] ?? s}</Tag>
      ),
    },
    {
      title: 'Приоритет',
      dataIndex: ['priority', 'name'],
      width: 120,
      render: (name: string) => PRIORITY_LABELS[name as keyof typeof PRIORITY_LABELS] ?? name,
    },
    {
      title: 'SLA',
      width: 130,
      render: (_: unknown, row: TicketListItem) => (
        <SLACountdown slaDeadline={row.sla_deadline} slaViolated={row.sla_violated} createdAt={row.created_at} />
      ),
    },
    {
      title: 'Создана',
      dataIndex: 'created_at',
      width: 120,
      render: (d: string) => new Date(d).toLocaleDateString('ru-RU'),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          Мои заявки
          {total > 0 && <Badge count={total} style={{ marginLeft: 8, backgroundColor: '#1677ff' }} />}
        </Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/portal/tickets/new')}>
          Новая заявка
        </Button>
      </div>

      <Card style={{ marginBottom: 12 }} bodyStyle={{ padding: '12px 16px' }}>
        <Space wrap>
          <Input
            placeholder="Поиск по теме или номеру"
            prefix={<SearchOutlined />}
            allowClear
            style={{ width: 260 }}
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
          />
          <Select
            placeholder="Статус"
            allowClear
            style={{ width: 180 }}
            value={statusFilter}
            onChange={v => { setStatusFilter(v); setPage(1) }}
            options={[
              { value: 'new', label: 'Новая' },
              { value: 'in_progress', label: 'В работе' },
              { value: 'waiting_info', label: 'Ожидает информации' },
              { value: 'resolved', label: 'Выполнена' },
              { value: 'cancelled', label: 'Отменена' },
            ]}
          />
        </Space>
      </Card>

      <Card>
        <Table
          dataSource={tickets}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            total,
            pageSize: 10,
            onChange: setPage,
            showTotal: t => `Всего ${t}`,
            showSizeChanger: false,
          }}
          locale={{ emptyText: 'Заявок пока нет' }}
        />
      </Card>
    </div>
  )
}
