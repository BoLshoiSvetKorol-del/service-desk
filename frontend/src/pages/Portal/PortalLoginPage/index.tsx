import { useState } from 'react'
import { Form, Input, Button, Card, Typography, Alert } from 'antd'
import { UserOutlined, LockOutlined, CustomerServiceOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { login } from '../../../api/auth'
import { useAuthStore } from '../../../store/authStore'
import { getErrorMessage } from '../../../types/common'

const { Title } = Typography

export default function PortalLoginPage() {
  const navigate = useNavigate()
  const { login: storeLogin } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onFinish(values: { username: string; password: string }) {
    setLoading(true)
    setError(null)
    try {
      const { tokens, user } = await login(values)

      if (user.role !== 'user') {
        setError('Неверный логин или пароль')
        setLoading(false)
        return
      }

      storeLogin(user, tokens.access_token, tokens.refresh_token)
      navigate('/portal/tickets')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', background: '#f5f7fa' }}>
      <Card style={{ width: 420, boxShadow: '0 4px 16px rgba(0,0,0,.08)' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <CustomerServiceOutlined style={{ fontSize: 40, color: '#1677ff', display: 'block', marginBottom: 12 }} />
          <Title level={3} style={{ margin: 0 }}>Клиентский портал</Title>
          <Typography.Text type="secondary">Войдите для управления заявками</Typography.Text>
        </div>

        {error && (
          <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />
        )}

        <Form layout="vertical" onFinish={onFinish} autoComplete="off">
          <Form.Item name="username" label="Email или логин" rules={[{ required: true, message: 'Введите логин' }]}>
            <Input prefix={<UserOutlined />} placeholder="Логин" size="large" />
          </Form.Item>
          <Form.Item name="password" label="Пароль" rules={[{ required: true, message: 'Введите пароль' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="Пароль" size="large" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 8 }}>
            <Button type="primary" htmlType="submit" size="large" block loading={loading}>
              Войти
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 8 }}>
          <Typography.Text type="secondary" style={{ fontSize: 13 }}>
            Нет аккаунта?{' '}
            <Typography.Link onClick={() => navigate('/portal/register')}>
              Зарегистрироваться
            </Typography.Link>
          </Typography.Text>
        </div>
      </Card>
    </div>
  )
}
