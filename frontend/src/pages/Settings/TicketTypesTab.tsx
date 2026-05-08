import { useEffect, useState } from 'react'
import { Table, Button, Modal, Form, Input, Select, Space, Tag, Popconfirm, message } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { getTicketTypes, createTicketType, updateTicketType, deleteTicketType } from '../../api/ticketTypes'
import { getDepartments } from '../../api/departments'
import { TicketType, Department } from '../../types/user'
import { getErrorMessage } from '../../types/common'

export default function TicketTypesTab() {
  const [types, setTypes] = useState<TicketType[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<TicketType | null>(null)
  const [form] = Form.useForm()

  async function load() {
    setLoading(true)
    try {
      setTypes(await getTicketTypes())
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    getDepartments().then(setDepartments)
  }, [])

  function openCreate() {
    setEditing(null)
    form.resetFields()
    setModalOpen(true)
  }

  function openEdit(t: TicketType) {
    setEditing(t)
    form.setFieldsValue(t)
    setModalOpen(true)
  }

  async function handleSubmit() {
    const values = await form.validateFields()
    try {
      if (editing) {
        await updateTicketType(editing.id, values)
        message.success('Тип заявки обновлён')
      } else {
        await createTicketType(values)
        message.success('Тип заявки создан')
      }
      setModalOpen(false)
      load()
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteTicketType(id)
      message.success('Тип заявки удалён')
      load()
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  const columns = [
    { title: 'Название', dataIndex: 'name', key: 'name' },
    { title: 'Вид услуги', dataIndex: 'service_type', key: 'service_type', render: (v: string | null) => v ?? '—' },
    { title: 'Направление работ', dataIndex: 'work_direction', key: 'work_direction', render: (v: string | null) => v ?? '—' },
    {
      title: 'Отдел по умолч.', dataIndex: 'default_department_id', key: 'default_department_id',
      render: (id: number | null) => departments.find(d => d.id === id)?.name ?? '—',
    },
    {
      title: 'Статус', dataIndex: 'is_active', key: 'is_active',
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? 'Активен' : 'Отключён'}</Tag>,
    },
    {
      title: 'Действия', key: 'actions',
      render: (_: unknown, record: TicketType) => (
        <Space>
          <Button size="small" onClick={() => openEdit(record)}>Изменить</Button>
          <Popconfirm title="Удалить тип заявки?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger>Удалить</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Добавить тип</Button>
      </div>
      <Table rowKey="id" dataSource={types} columns={columns} loading={loading} pagination={false} />
      <Modal
        title={editing ? 'Редактировать тип заявки' : 'Новый тип заявки'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText="Сохранить"
        cancelText="Отмена"
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Название" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="service_type" label="Вид услуги">
            <Input />
          </Form.Item>
          <Form.Item name="work_direction" label="Направление работ">
            <Input />
          </Form.Item>
          <Form.Item name="default_department_id" label="Отдел по умолчанию">
            <Select allowClear options={departments.map(d => ({ value: d.id, label: d.name }))} />
          </Form.Item>
          {editing && (
            <Form.Item name="is_active" label="Статус">
              <Select options={[{ value: true, label: 'Активен' }, { value: false, label: 'Отключён' }]} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </>
  )
}
