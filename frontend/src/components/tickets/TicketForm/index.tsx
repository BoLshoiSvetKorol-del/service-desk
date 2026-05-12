import { useEffect, useState } from 'react'
import { Button, Form, Input, Select, Space, Typography, Upload, message } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd'
import type { TicketCreateRequest, Priority } from '../../../types/ticket'
import { PRIORITY_LABELS } from '../../../types/ticket'
import { getPriorities } from '../../../api/priorities'
import { getDepartments } from '../../../api/departments'
import { getTicketTypes } from '../../../api/ticketTypes'
import type { Department, TicketType } from '../../../types/user'
import { getErrorMessage } from '../../../types/common'

const { TextArea } = Input
const { Dragger } = Upload

interface Props {
  onSubmit: (data: TicketCreateRequest, files: File[]) => Promise<void>
  loading: boolean
}

export default function TicketForm({ onSubmit, loading }: Props) {
  const [form] = Form.useForm()
  const [priorities, setPriorities] = useState<Priority[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [ticketTypes, setTicketTypes] = useState<TicketType[]>([])
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [selectedPriority, setSelectedPriority] = useState<Priority | null>(null)

  useEffect(() => {
    getPriorities().then(setPriorities).catch(() => {})
    getDepartments().then(setDepartments).catch(() => {})
    getTicketTypes().then(types => setTicketTypes(types.filter(t => t.is_active))).catch(() => {})
  }, [])

  function handleTypeChange(typeId: number) {
    const type = ticketTypes.find(t => t.id === typeId)
    if (type?.default_department_id) {
      form.setFieldValue('department_id', type.default_department_id)
    }
  }



  function handlePriorityChange(priorityId: number) {
    const p = priorities.find(pr => pr.id === priorityId) ?? null
    setSelectedPriority(p)
  }

  async function handleFinish(values: {
    title: string
    description: string
    type_id: number
    priority_id: number
    department_id?: number
  }) {
    const files = fileList
      .filter(f => f.originFileObj)
      .map(f => f.originFileObj as File)

    try {
      await onSubmit(
        {
          title: values.title,
          description: values.description,
          type_id: values.type_id,
          priority_id: values.priority_id,
          department_id: values.department_id ?? null,
        },
        files,
      )
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  return (
    <Form form={form} layout="vertical" onFinish={handleFinish} style={{ maxWidth: 720 }}>
      <Form.Item name="title" label="Заголовок" rules={[{ required: true, message: 'Введите заголовок' }]}>
        <Input placeholder="Кратко опишите проблему или запрос" />
      </Form.Item>

      <Form.Item name="description" label="Описание" rules={[{ required: true, message: 'Введите описание' }]}>
        <TextArea rows={5} placeholder="Подробное описание: что произошло, что ожидалось, шаги воспроизведения..." />
      </Form.Item>

      <Form.Item name="type_id" label="Тип заявки" rules={[{ required: true, message: 'Выберите тип заявки' }]}>
        <Select
          placeholder="Выберите тип заявки"
          onChange={handleTypeChange}
          options={ticketTypes.map(t => ({ value: t.id, label: t.name }))}
        />
      </Form.Item>

      <Form.Item name="priority_id" label="Приоритет" rules={[{ required: true, message: 'Выберите приоритет' }]}>
        <Select
          placeholder="Выберите приоритет"
          onChange={handlePriorityChange}
          options={priorities.map(p => ({
            value: p.id,
            label: PRIORITY_LABELS[p.name],
          }))}
        />
      </Form.Item>

      {selectedPriority && (
        <Typography.Text type="secondary" style={{ display: 'block', marginTop: -16, marginBottom: 12 }}>
          SLA: {selectedPriority.sla_hours} рабочих {selectedPriority.sla_hours === 1 ? 'час' : 'часа(ов)'}
        </Typography.Text>
      )}

      <Form.Item name="department_id" label="Отдел">
        <Select
          placeholder="Выберите отдел (необязательно)"
          allowClear
          options={departments.map(d => ({ value: d.id, label: d.name }))}
        />
      </Form.Item>

      <Form.Item label="Файлы">
        <Dragger
          multiple
          beforeUpload={() => false}
          fileList={fileList}
          onChange={({ fileList: fl }) => setFileList(fl)}
          accept="*"
        >
          <p className="ant-upload-drag-icon"><InboxOutlined /></p>
          <p className="ant-upload-text">Перетащите файлы или нажмите для выбора</p>
          <p className="ant-upload-hint">Максимальный размер файла: 10 МБ</p>
        </Dragger>
      </Form.Item>

      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" loading={loading}>
            Создать заявку
          </Button>
          <Button onClick={() => form.resetFields()}>Сбросить</Button>
        </Space>
      </Form.Item>
    </Form>
  )
}
