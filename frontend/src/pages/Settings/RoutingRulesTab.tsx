import { useEffect, useState } from 'react'
import {
  Alert, Button, Card, Form, Input, InputNumber, Modal, Popconfirm,
  Select, Space, Switch, Table, Tag, Tooltip, Typography, message,
} from 'antd'
import { BranchesOutlined, PlusOutlined, QuestionCircleOutlined } from '@ant-design/icons'
import {
  getRoutingRules, createRoutingRule, updateRoutingRule, deleteRoutingRule,
  testRouting, type RoutingRule, type RoutingTestResult,
} from '../../api/routingRules'
import { getDepartments } from '../../api/departments'
import { getUsers } from '../../api/users'
import { getTicketTypes } from '../../api/ticketTypes'
import type { Department, TicketType, User } from '../../types/user'
import { getErrorMessage } from '../../types/common'

const { TextArea } = Input
const { Text } = Typography

export default function RoutingRulesTab() {
  const [rules, setRules] = useState<RoutingRule[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [agents, setAgents] = useState<User[]>([])
  const [ticketTypes, setTicketTypes] = useState<TicketType[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<RoutingRule | null>(null)
  const [form] = Form.useForm()

  // Test panel state
  const [testForm] = Form.useForm()
  const [testResult, setTestResult] = useState<RoutingTestResult | null>(null)
  const [testLoading, setTestLoading] = useState(false)

  async function load() {
    setLoading(true)
    try {
      setRules(await getRoutingRules())
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    getDepartments().then(setDepartments)
    getUsers({ page_size: 200 }).then(r => setAgents(r.items.filter((u: User) => u.role !== 'user')))
    getTicketTypes().then(setTicketTypes)
  }, [])

  function openCreate() {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ priority: 0, is_active: true })
    setModalOpen(true)
  }

  function openEdit(r: RoutingRule) {
    setEditing(r)
    form.setFieldsValue({
      name: r.name,
      keywords: r.keywords ?? '',
      ticket_type_id: r.ticket_type_id ?? undefined,
      department_id: r.department_id,
      assignee_id: r.assignee_id ?? undefined,
      priority: r.priority,
      is_active: r.is_active,
    })
    setModalOpen(true)
  }

  async function handleSubmit() {
    const values = await form.validateFields()
    const payload = {
      name: values.name,
      keywords: values.keywords || null,
      ticket_type_id: values.ticket_type_id ?? null,
      department_id: values.department_id,
      assignee_id: values.assignee_id ?? null,
      priority: values.priority ?? 0,
      is_active: values.is_active ?? true,
    }
    try {
      if (editing) {
        await updateRoutingRule(editing.id, payload)
        message.success('Правило обновлено')
      } else {
        await createRoutingRule(payload)
        message.success('Правило создано')
      }
      setModalOpen(false)
      load()
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteRoutingRule(id)
      message.success('Правило удалено')
      load()
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  async function handleTest() {
    const values = await testForm.validateFields()
    setTestLoading(true)
    try {
      const result = await testRouting({
        title: values.title,
        description: values.description || undefined,
        type_id: values.type_id ?? undefined,
      })
      setTestResult(result)
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setTestLoading(false)
    }
  }

  const columns = [
    {
      title: <Tooltip title="Порядок проверки (меньше = раньше)">Приор.<QuestionCircleOutlined style={{ marginLeft: 4, color: '#aaa' }} /></Tooltip>,
      dataIndex: 'priority', key: 'priority', width: 80,
      render: (v: number) => <Tag>{v}</Tag>,
    },
    { title: 'Название', dataIndex: 'name', key: 'name' },
    {
      title: 'Ключевые слова',
      dataIndex: 'keywords',
      key: 'keywords',
      render: (v: string | null) => {
        if (!v) return <Text type="secondary">—</Text>
        return v.split(',').map(k => k.trim()).filter(Boolean).map(k => (
          <Tag key={k} style={{ marginBottom: 2 }}>{k}</Tag>
        ))
      },
    },
    {
      title: 'Тип заявки',
      key: 'ticket_type',
      render: (_: unknown, r: RoutingRule) => r.ticket_type?.name ?? <Text type="secondary">Любой</Text>,
    },
    {
      title: '→ Отдел',
      key: 'department',
      render: (_: unknown, r: RoutingRule) => <Tag color="blue">{r.department.name}</Tag>,
    },
    {
      title: '→ Исполнитель',
      key: 'assignee',
      render: (_: unknown, r: RoutingRule) => r.assignee?.full_name ?? <Text type="secondary">—</Text>,
    },
    {
      title: 'Активно',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 90,
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? 'Да' : 'Нет'}</Tag>,
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: unknown, r: RoutingRule) => (
        <Space>
          <Button size="small" onClick={() => openEdit(r)}>Изменить</Button>
          <Popconfirm title="Удалить правило?" onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger>Удалить</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="Как работает авто-маршрутизация"
        description={
          <ul style={{ margin: '4px 0 0', paddingLeft: 20 }}>
            <li>Правила проверяются по порядку (поле «Приор.»). Первое совпавшее применяется.</li>
            <li>Правило совпадает, если <b>все</b> его условия выполнены одновременно.</li>
            <li>Условие «Ключевые слова» — хотя бы одно слово есть в теме или описании заявки.</li>
            <li>Условие «Тип заявки» — заявка должна быть именно этого типа.</li>
            <li>Если ни одно правило не совпало, используется настройка «Отдел по умолч.» из типа заявки.</li>
          </ul>
        }
      />

      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Добавить правило</Button>
      </div>

      <Table
        rowKey="id"
        dataSource={rules}
        columns={columns}
        loading={loading}
        pagination={false}
        style={{ marginBottom: 32 }}
      />

      {/* Test panel */}
      <Card
        title={<Space><BranchesOutlined />Проверить маршрутизацию</Space>}
        style={{ maxWidth: 600 }}
      >
        <Form form={testForm} layout="vertical">
          <Form.Item name="title" label="Тема заявки" rules={[{ required: true, message: 'Введите тему' }]}>
            <Input placeholder="Например: не работает принтер" />
          </Form.Item>
          <Form.Item name="description" label="Описание (опционально)">
            <TextArea rows={3} placeholder="Подробное описание проблемы..." />
          </Form.Item>
          <Form.Item name="type_id" label="Тип заявки (опционально)">
            <Select
              allowClear
              placeholder="Выберите тип"
              options={ticketTypes.map(t => ({ value: t.id, label: t.name }))}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" loading={testLoading} onClick={handleTest}>
              Проверить
            </Button>
          </Form.Item>
        </Form>

        {testResult && (
          testResult.matched ? (
            <Alert
              type="success"
              showIcon
              message={`Сработало правило: «${testResult.rule_name}»`}
              description={
                <div>
                  <div>Отдел: <b>{testResult.department_name}</b></div>
                  {testResult.assignee_name && <div>Исполнитель: <b>{testResult.assignee_name}</b></div>}
                </div>
              }
            />
          ) : (
            <Alert
              type="warning"
              showIcon
              message="Ни одно правило не совпало"
              description="Будет использован отдел по умолчанию из типа заявки (или не назначен)."
            />
          )
        )}
      </Card>

      <Modal
        title={editing ? 'Редактировать правило' : 'Новое правило маршрутизации'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText="Сохранить"
        cancelText="Отмена"
        destroyOnClose
        width={560}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Название" rules={[{ required: true, message: 'Введите название' }]}>
            <Input placeholder="Например: Проблемы с принтерами → IT" />
          </Form.Item>

          <Form.Item
            name="keywords"
            label={<span>Ключевые слова <Text type="secondary" style={{ fontSize: 12 }}>(через запятую)</Text></span>}
            tooltip="Правило сработает, если хотя бы одно ключевое слово найдено в теме или описании заявки"
          >
            <Input placeholder="принтер, сканер, копир, картридж" />
          </Form.Item>

          <Form.Item
            name="ticket_type_id"
            label="Тип заявки"
            tooltip="Оставьте пустым, чтобы правило применялось к любому типу"
          >
            <Select
              allowClear
              placeholder="Любой тип"
              options={ticketTypes.map(t => ({ value: t.id, label: t.name }))}
            />
          </Form.Item>

          <Form.Item name="department_id" label="Отдел" rules={[{ required: true, message: 'Выберите отдел' }]}>
            <Select
              placeholder="Выберите отдел"
              options={departments.map(d => ({ value: d.id, label: d.name }))}
            />
          </Form.Item>

          <Form.Item
            name="assignee_id"
            label="Исполнитель"
            tooltip="Оставьте пустым, если нужно только определить отдел"
          >
            <Select
              allowClear
              placeholder="Не назначать автоматически"
              options={agents.map(u => ({ value: u.id, label: u.full_name || u.username }))}
            />
          </Form.Item>

          <Form.Item
            name="priority"
            label={<span>Приоритет <Text type="secondary" style={{ fontSize: 12 }}>(меньше = проверяется раньше)</Text></span>}
          >
            <InputNumber min={-100} max={1000} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="is_active" label="Активно" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
