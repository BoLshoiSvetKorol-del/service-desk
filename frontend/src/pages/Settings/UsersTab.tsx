import { useEffect, useState } from 'react'
import { Table, Button, Modal, Form, Input, Select, Space, Tag, message, Popconfirm } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { getUsers, createUser, updateUser, toggleUserActive, UserCreateRequest } from '../../api/users'
import { getDepartments } from '../../api/departments'
import { User, Department } from '../../types/user'
import { getErrorMessage } from '../../types/common'

const ROLE_OPTIONS = [
  { value: 'admin', label: 'Администратор' },
  { value: 'agent', label: 'Агент поддержки' },
  { value: 'user', label: 'Пользователь' },
]

const ROLE_COLOR: Record<string, string> = { admin: 'red', agent: 'blue', user: 'default' }

export default function UsersTab() {
  const [users, setUsers] = useState<User[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<User | null>(null)
  const [form] = Form.useForm()

  async function load(p = page) {
    setLoading(true)
    try {
      const res = await getUsers({ page: p, page_size: 20 })
      setUsers(res.items)
      setTotal(res.total)
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

  function openEdit(user: User) {
    setEditing(user)
    form.setFieldsValue({ ...user, password: '' })
    setModalOpen(true)
  }

  async function handleSubmit() {
    const values = await form.validateFields()
    try {
      if (editing) {
        await updateUser(editing.id, values)
        message.success('Пользователь обновлён')
      } else {
        await createUser(values as UserCreateRequest)
        message.success('Пользователь создан')
      }
      setModalOpen(false)
      load()
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  async function handleToggle(user: User) {
    try {
      await toggleUserActive(user.id, !user.is_active)
      message.success(user.is_active ? 'Деактивирован' : 'Активирован')
      load()
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  const columns = [
    { title: 'Имя', dataIndex: 'full_name', key: 'full_name' },
    { title: 'Логин', dataIndex: 'username', key: 'username' },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    {
      title: 'Роль', dataIndex: 'role', key: 'role',
      render: (role: string) => <Tag color={ROLE_COLOR[role]}>{ROLE_OPTIONS.find(r => r.value === role)?.label}</Tag>,
    },
    {
      title: 'Отдел', dataIndex: 'department_id', key: 'department_id',
      render: (id: number | null) => departments.find(d => d.id === id)?.name ?? '—',
    },
    {
      title: 'Статус', dataIndex: 'is_active', key: 'is_active',
      render: (active: boolean) => <Tag color={active ? 'green' : 'default'}>{active ? 'Активен' : 'Отключён'}</Tag>,
    },
    {
      title: 'Действия', key: 'actions',
      render: (_: unknown, record: User) => (
        <Space>
          <Button size="small" onClick={() => openEdit(record)}>Изменить</Button>
          <Popconfirm title={record.is_active ? 'Деактивировать?' : 'Активировать?'} onConfirm={() => handleToggle(record)}>
            <Button size="small" danger={record.is_active}>{record.is_active ? 'Деактивировать' : 'Активировать'}</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Добавить пользователя</Button>
      </div>
      <Table
        rowKey="id"
        dataSource={users}
        columns={columns}
        loading={loading}
        pagination={{ total, pageSize: 20, current: page, onChange: (p) => { setPage(p); load(p) } }}
      />
      <Modal
        title={editing ? 'Редактировать пользователя' : 'Новый пользователь'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText="Сохранить"
        cancelText="Отмена"
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="full_name" label="Полное имя" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="username" label="Логин" rules={[{ required: !editing }]}>
            <Input disabled={!!editing} />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
            <Input />
          </Form.Item>
          {!editing && (
            <Form.Item name="password" label="Пароль" rules={[{ required: true, min: 6 }]}>
              <Input.Password />
            </Form.Item>
          )}
          <Form.Item name="role" label="Роль" rules={[{ required: true }]}>
            <Select options={ROLE_OPTIONS} />
          </Form.Item>
          <Form.Item name="department_id" label="Отдел">
            <Select allowClear options={departments.map(d => ({ value: d.id, label: d.name }))} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
