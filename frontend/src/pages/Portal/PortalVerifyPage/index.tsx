import { useEffect, useState } from 'react'
import { Alert, Button, Card, Input, Result, Spin, Typography, message } from 'antd'
import { MailOutlined } from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { verifyEmail, resendVerification } from '../../../api/auth'
import { useAuthStore } from '../../../store/authStore'
import { getErrorMessage } from '../../../types/common'

export default function PortalVerifyPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const user = useAuthStore(s => s.user)
  const isRegistered = searchParams.get('registered') === '1'
  const tokenParam = searchParams.get('token')

  const [verifying, setVerifying] = useState(!!tokenParam)
  const [verified, setVerified] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [manualToken, setManualToken] = useState('')
  const [resending, setResending] = useState(false)

  useEffect(() => {
    if (tokenParam) {
      verifyEmail(tokenParam)
        .then(() => setVerified(true))
        .catch(e => setError(getErrorMessage(e)))
        .finally(() => setVerifying(false))
    }
  }, [tokenParam])

  async function handleManualVerify() {
    if (!manualToken.trim()) return
    setVerifying(true)
    setError(null)
    try {
      await verifyEmail(manualToken.trim())
      setVerified(true)
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setVerifying(false)
    }
  }

  async function handleResend() {
    if (!user) {
      navigate('/portal/login')
      return
    }
    setResending(true)
    try {
      await resendVerification()
      message.success('Письмо отправлено повторно')
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setResending(false)
    }
  }

  if (verifying) return (
    <div style={{ textAlign: 'center', padding: 80 }}>
      <Spin size="large" />
      <div style={{ marginTop: 16 }}>Проверка токена...</div>
    </div>
  )

  if (verified) return (
    <Result
      status="success"
      title="Email подтверждён!"
      subTitle="Теперь вы можете войти в клиентский портал и создавать заявки."
      extra={
        <Button type="primary" size="large" onClick={() => navigate('/portal/tickets')}>
          Перейти к заявкам
        </Button>
      }
    />
  )

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', background: '#f5f7fa' }}>
      <Card style={{ width: 460, textAlign: 'center', boxShadow: '0 4px 16px rgba(0,0,0,.08)' }}>
        <MailOutlined style={{ fontSize: 48, color: '#1677ff', marginBottom: 16 }} />
        <Typography.Title level={3}>
          {isRegistered ? 'Подтвердите email' : 'Email не подтверждён'}
        </Typography.Title>
        <Typography.Paragraph type="secondary">
          {isRegistered
            ? 'Мы отправили письмо с ссылкой для подтверждения. Проверьте почту и перейдите по ссылке.'
            : 'Для доступа к порталу необходимо подтвердить ваш email.'}
        </Typography.Paragraph>

        {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16, textAlign: 'left' }} />}

        <div style={{ marginBottom: 16 }}>
          <Typography.Text type="secondary" style={{ fontSize: 13 }}>
            Введите токен из письма вручную:
          </Typography.Text>
          <Input.Search
            placeholder="Токен из письма"
            value={manualToken}
            onChange={e => setManualToken(e.target.value)}
            onSearch={handleManualVerify}
            enterButton="Подтвердить"
            size="large"
            style={{ marginTop: 8 }}
          />
        </div>

        {user && (
          <Button type="link" loading={resending} onClick={handleResend}>
            Отправить письмо повторно
          </Button>
        )}

        <div style={{ marginTop: 8 }}>
          <Button type="link" onClick={() => navigate('/portal/login')}>
            Вернуться к входу
          </Button>
        </div>
      </Card>
    </div>
  )
}
