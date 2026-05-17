import { useState } from 'react'
import { Form, Input, Button, Card, Typography, Alert, Divider } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { login } from '../../api/auth'
import { useAuthStore } from '../../store/authStore'
import { getErrorMessage } from '../../types/common'

const { Title } = Typography

export default function LoginPage() {
  const navigate = useNavigate()
  const { login: storeLogin } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onFinish(values: { username: string; password: string }) {
    setLoading(true)
    setError(null)
    try {
      const { tokens, user } = await login(values)
      storeLogin(user, tokens.access_token, tokens.refresh_token)
      // Clients should use the portal
      if (user.role === 'user') {
        navigate('/portal/tickets', { replace: true })
      } else {
        navigate('/dashboard', { replace: true })
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', background: '#f0f2f5' }}>
      <Card style={{ width: 400, boxShadow: '0 4px 16px rgba(0,0,0,.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ color: '#1677ff', margin: 0 }}>Service Desk</Title>
          <Typography.Text type="secondary">Вход для сотрудников</Typography.Text>
        </div>

        {error && (
          <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />
        )}

        <Form layout="vertical" onFinish={onFinish} autoComplete="off">
          <Form.Item name="username" rules={[{ required: true, message: 'Введите логин' }]}>
            <Input prefix={<UserOutlined />} placeholder="Логин" size="large" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: 'Введите пароль' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="Пароль" size="large" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" size="large" block loading={loading}>
              Войти
            </Button>
          </Form.Item>
        </Form>

        <Divider style={{ margin: '20px 0 12px' }} />
        <div style={{ textAlign: 'center' }}>
          <Typography.Text type="secondary" style={{ fontSize: 13 }}>
            Клиент?{' '}
            <Typography.Link href="https://extechportal.ru/portal/login">Войти в клиентский портал</Typography.Link>
          </Typography.Text>
        </div>
      </Card>
    </div>
  )
}
