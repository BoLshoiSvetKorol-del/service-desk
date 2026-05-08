import { useEffect, useState } from 'react'
import { Table, Button, Modal, Form, Input, Space, Popconfirm, message } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { getDepartments, createDepartment, updateDepartment, deleteDepartment } from '../../api/departments'
import { Department } from '../../types/user'
import { getErrorMessage } from '../../types/common'

export default function DepartmentsTab() {
  const [departments, setDepartments] = useState<Department[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Department | null>(null)
  const [form] = Form.useForm()

  async function load() {
    setLoading(true)
    try {
      setDepartments(await getDepartments())
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  function openCreate() {
    setEditing(null)
    form.resetFields()
    setModalOpen(true)
  }

  function openEdit(dept: Department) {
    setEditing(dept)
    form.setFieldsValue(dept)
    setModalOpen(true)
  }

  async function handleSubmit() {
    const values = await form.validateFields()
    try {
      if (editing) {
        await updateDepartment(editing.id, values)
        message.success('Отдел обновлён')
      } else {
        await createDepartment(values)
        message.success('Отдел создан')
      }
      setModalOpen(false)
      load()
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteDepartment(id)
      message.success('Отдел удалён')
      load()
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  const columns = [
    { title: 'Название', dataIndex: 'name', key: 'name' },
    { title: 'Описание', dataIndex: 'description', key: 'description', render: (v: string | null) => v ?? '—' },
    {
      title: 'Действия', key: 'actions',
      render: (_: unknown, record: Department) => (
        <Space>
          <Button size="small" onClick={() => openEdit(record)}>Изменить</Button>
          <Popconfirm title="Удалить отдел?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger>Удалить</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Добавить отдел</Button>
      </div>
      <Table rowKey="id" dataSource={departments} columns={columns} loading={loading} pagination={false} />
      <Modal
        title={editing ? 'Редактировать отдел' : 'Новый отдел'}
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
          <Form.Item name="description" label="Описание">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
