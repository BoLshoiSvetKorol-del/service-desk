import { useEffect, useState } from 'react'
import { Button, Card, Form, Input, Select, Space, Typography, Upload, message } from 'antd'
import { ArrowLeftOutlined, InboxOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import type { UploadFile } from 'antd'
import { createTicket, uploadTicketAttachment } from '../../../api/tickets'
import { getTicketTypes } from '../../../api/ticketTypes'
import type { TicketType } from '../../../types/user'
import { getErrorMessage } from '../../../types/common'

const { TextArea } = Input
const { Dragger } = Upload

export default function PortalCreateTicketPage() {
  const [form] = Form.useForm()
  const navigate = useNavigate()
  const [ticketTypes, setTicketTypes] = useState<TicketType[]>([])
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getTicketTypes().then(types => setTicketTypes(types.filter(t => t.is_active))).catch(() => {})
  }, [])

  async function handleFinish(values: {
    title: string
    description: string
    type_id: number
  }) {
    setLoading(true)
    try {
      const ticket = await createTicket({
        title: values.title,
        description: values.description,
        type_id: values.type_id,
      })

      for (const f of fileList) {
        if (f.originFileObj) {
          try {
            await uploadTicketAttachment(ticket.id, f.originFileObj)
          } catch {
            message.warning(`Не удалось загрузить файл: ${f.name}`)
          }
        }
      }

      message.success(`Инцидент ${ticket.number} зарегистрирован`)
      navigate(`/portal/tickets/${ticket.id}`)
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        type="link"
        style={{ paddingLeft: 0, marginBottom: 16 }}
        onClick={() => navigate('/portal/tickets')}
      >
        К списку инцидентов
      </Button>

      <Typography.Title level={4} style={{ marginBottom: 20 }}>Новый инцидент</Typography.Title>

      <Card>
        <Form form={form} layout="vertical" onFinish={handleFinish} style={{ maxWidth: 620 }}>
          <Form.Item name="title" label="Тема обращения"
            rules={[{ required: true, message: 'Введите тему обращения' }]}>
            <Input placeholder="Кратко опишите проблему" size="large" />
          </Form.Item>

          <Form.Item name="description" label="Описание"
            rules={[{ required: true, message: 'Опишите проблему подробнее' }]}>
            <TextArea
              rows={6}
              placeholder="Опишите проблему: что произошло, когда, каков ожидаемый результат..."
              size="large"
            />
          </Form.Item>

          <Form.Item name="type_id" label="Тип обращения"
            rules={[{ required: true, message: 'Выберите тип обращения' }]}>
            <Select
              size="large"
              placeholder="Выберите тип"
              options={ticketTypes.map(t => ({ value: t.id, label: t.name }))}
            />
          </Form.Item>

          <Form.Item label="Прикрепить файлы">
            <Dragger
              multiple
              beforeUpload={() => false}
              fileList={fileList}
              onChange={({ fileList: fl }) => setFileList(fl)}
              accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.zip"
            >
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">Перетащите файлы или нажмите для выбора</p>
              <p className="ant-upload-hint">Скриншоты, документы, архивы — до 10 МБ</p>
            </Dragger>
          </Form.Item>

          <Form.Item style={{ marginTop: 8 }}>
            <Space>
              <Button type="primary" htmlType="submit" size="large" loading={loading}>
                Отправить инцидент
              </Button>
              <Button size="large" onClick={() => navigate('/portal/tickets')}>
                Отмена
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
