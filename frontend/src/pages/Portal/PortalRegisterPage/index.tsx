import { useState } from 'react'
import { Form, Input, Button, Card, Typography, Alert } from 'antd'
import { CustomerServiceOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { register, login } from '../../../api/auth'
import { useAuthStore } from '../../../store/authStore'
import { getErrorMessage } from '../../../types/common'

const { Title } = Typography

export default function PortalRegisterPage() {
  const navigate = useNavigate()
  const { login: storeLogin } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onFinish(values: {
    email: string
    full_name: string
    password: string
    confirm: string
  }) {
    if (values.password !== values.confirm) {
      setError('Пароли не совпадают')
      return
    }
    setLoading(true)
    setError(null)
    try {
      await register({
        email: values.email,
        full_name: values.full_name,
        password: values.password,
      })
      // Auto-login so the verify page can resend verification
      // Username is auto-generated on backend; we login by email
      const { tokens, user } = await login({ username: values.email, password: values.password })
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
      <Card style={{ width: 460, boxShadow: '0 4px 16px rgba(0,0,0,.08)' }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <CustomerServiceOutlined style={{ fontSize: 36, color: '#1677ff', display: 'block', marginBottom: 10 }} />
          <Title level={3} style={{ margin: 0 }}>Регистрация</Title>
          <Typography.Text type="secondary">Создайте аккаунт в клиентском портале</Typography.Text>
        </div>

        {error && (
          <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />
        )}

        <Form layout="vertical" onFinish={onFinish} autoComplete="off">
          <Form.Item name="full_name" label="Ваше имя" rules={[{ required: true, message: 'Введите имя' }]}>
            <Input placeholder="Иванов Иван Иванович" size="large" />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[
            { required: true, message: 'Введите email' },
            { type: 'email', message: 'Некорректный адрес почты' },
          ]}>
            <Input placeholder="ivanov@example.com" size="large" />
          </Form.Item>
          <Form.Item name="password" label="Пароль" rules={[
            { required: true, message: 'Введите пароль' },
            { min: 6, message: 'Пароль не менее 6 символов' },
          ]}>
            <Input.Password placeholder="••••••" size="large" />
          </Form.Item>
          <Form.Item name="confirm" label="Повторите пароль" rules={[
            { required: true, message: 'Повторите пароль' },
          ]}>
            <Input.Password placeholder="••••••" size="large" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 8 }}>
            <Button type="primary" htmlType="submit" size="large" block loading={loading}>
              Зарегистрироваться
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 8 }}>
          <Typography.Text type="secondary" style={{ fontSize: 13 }}>
            Уже есть аккаунт?{' '}
            <Typography.Link onClick={() => navigate('/portal/login')}>Войти</Typography.Link>
          </Typography.Text>
        </div>
      </Card>
    </div>
  )
}
