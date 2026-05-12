import { useEffect, useState } from 'react'
import { Button, Card, Form, Input, Space, Typography, message, Divider } from 'antd'
import { ArrowLeftOutlined, UserOutlined, PhoneOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../../store/authStore'
import { updateMe } from '../../../api/users'
import { getErrorMessage } from '../../../types/common'

const { TextArea } = Input

export default function PortalProfilePage() {
  const navigate = useNavigate()
  const user = useAuthStore(s => s.user)
  const setUser = useAuthStore(s => s.setUser)
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) {
      form.setFieldsValue({
        full_name: user.full_name,
        email: user.email,
        phone: user.phone ?? '',
        contact_info: user.contact_info ?? '',
      })
    }
  }, [user, form])

  async function handleFinish(values: {
    full_name: string
    email: string
    phone: string
    contact_info: string
    password?: string
  }) {
    setLoading(true)
    try {
      const updated = await updateMe({
        full_name: values.full_name,
        email: values.email,
        phone: values.phone || null,
        contact_info: values.contact_info || null,
        ...(values.password ? { password: values.password } : {}),
      })
      setUser(updated)
      message.success('Профиль обновлён')
      form.setFieldValue('password', '')
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
        К списку заявок
      </Button>

      <Typography.Title level={4} style={{ marginBottom: 20 }}>Мой профиль</Typography.Title>

      <Card style={{ maxWidth: 560 }}>
        <Form form={form} layout="vertical" onFinish={handleFinish}>
          <Form.Item name="full_name" label="Имя"
            rules={[{ required: true, message: 'Введите имя' }]}>
            <Input prefix={<UserOutlined />} size="large" />
          </Form.Item>

          <Form.Item name="email" label="Email"
            rules={[{ required: true, type: 'email', message: 'Введите корректный email' }]}>
            <Input size="large" />
          </Form.Item>

          <Divider>Контакты для связи</Divider>

          <Typography.Paragraph type="secondary" style={{ marginBottom: 12, fontSize: 13 }}>
            Укажите, как с вами можно связаться помимо системы — например, телефон, Telegram, WhatsApp или другой мессенджер.
          </Typography.Paragraph>

          <Form.Item name="phone" label="Телефон">
            <Input
              prefix={<PhoneOutlined />}
              size="large"
              placeholder="+7 (999) 123-45-67"
            />
          </Form.Item>

          <Form.Item name="contact_info" label="Мессенджер / другой способ связи">
            <TextArea
              rows={3}
              placeholder="Например: Telegram @username, WhatsApp +7 999 123-45-67"
            />
          </Form.Item>

          <Divider>Смена пароля</Divider>

          <Form.Item name="password" label="Новый пароль (оставьте пустым, если не меняете)"
            rules={[{ min: 6, message: 'Минимум 6 символов' }]}>
            <Input.Password size="large" placeholder="Не менее 6 символов" />
          </Form.Item>

          <Form.Item style={{ marginTop: 8 }}>
            <Space>
              <Button type="primary" htmlType="submit" size="large" loading={loading}>
                Сохранить
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
