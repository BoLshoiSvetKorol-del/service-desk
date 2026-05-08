import { useEffect, useState } from 'react'
import { Button, Table, Typography, message } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import type { ColumnsType } from 'antd/es/table'
import { getTickets } from '../../../api/tickets'
import type { TicketListItem, TicketFilters, TicketStatus, PriorityName } from '../../../types/ticket'
import type { PagedResponse } from '../../../types/common'
import FilterPanel from '../../../components/tickets/FilterPanel'
import PriorityBadge from '../../../components/common/PriorityBadge'
import StatusBadge from '../../../components/common/StatusBadge'
import SLACountdown from '../../../components/common/SLACountdown'

export default function TicketsListPage() {
  const [filters, setFilters] = useState<TicketFilters>({ page: 1, page_size: 20 })
  const [data, setData] = useState<PagedResponse<TicketListItem> | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    setLoading(true)
    getTickets(filters)
      .then(setData)
      .catch(() => message.error('Ошибка загрузки заявок'))
      .finally(() => setLoading(false))
  }, [filters])

  const columns: ColumnsType<TicketListItem> = [
    {
      title: 'Номер',
      dataIndex: 'number',
      width: 140,
      render: (num: string, record) => (
        <Link to={`/tickets/${record.id}`} onClick={e => e.stopPropagation()}>
          {num}
        </Link>
      ),
    },
    {
      title: 'Заголовок',
      dataIndex: 'title',
      render: (title: string) => (
        <Typography.Text ellipsis={{ tooltip: title }} style={{ maxWidth: 300, display: 'block' }}>
          {title}
        </Typography.Text>
      ),
    },
    {
      title: 'Приоритет',
      dataIndex: ['priority', 'name'],
      width: 130,
      render: (name: PriorityName) => <PriorityBadge name={name} />,
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      width: 170,
      render: (status: TicketStatus) => <StatusBadge status={status} />,
    },
    {
      title: 'SLA',
      width: 110,
      render: (_, record) => (
        <SLACountdown
          slaDeadline={record.sla_deadline}
          slaViolated={record.sla_violated}
          createdAt={record.created_at}
        />
      ),
    },
    {
      title: 'Исполнитель',
      dataIndex: 'assignee_name',
      width: 160,
      render: (name: string | null) =>
        name ?? <Typography.Text type="secondary">Не назначен</Typography.Text>,
    },
    {
      title: 'Создана',
      dataIndex: 'created_at',
      width: 110,
      render: (d: string) => new Date(d).toLocaleDateString('ru-RU'),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Заявки</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/tickets/new')}>
          Создать заявку
        </Button>
      </div>

      <FilterPanel filters={filters} onChange={setFilters} />

      <Table<TicketListItem>
        dataSource={data?.items ?? []}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          current: filters.page ?? 1,
          pageSize: filters.page_size ?? 20,
          total: data?.total ?? 0,
          onChange: (page, pageSize) => setFilters(prev => ({ ...prev, page, page_size: pageSize })),
          showSizeChanger: true,
          pageSizeOptions: ['20', '50', '100'],
          showTotal: total => `Всего: ${total}`,
        }}
        onRow={record => ({
          onClick: () => navigate(`/tickets/${record.id}`),
          style: { cursor: 'pointer' },
        })}
      />
    </div>
  )
}
