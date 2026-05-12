import { Button, Layout, Space, Typography } from 'antd'
import { LogoutOutlined, CustomerServiceOutlined, UserOutlined, QuestionCircleOutlined } from '@ant-design/icons'
import { Outlet, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../../store/authStore'
import { logout as apiLogout } from '../../../api/auth'
import { useSSE } from '../../../hooks/useSSE'

const { Header, Content } = Layout

export default function PortalLayout() {
  const user = useAuthStore(s => s.user)
  const storeLogout = useAuthStore(s => s.logout)
  const navigate = useNavigate()
  useSSE()

  async function handleLogout() {
    try {
      const refresh = localStorage.getItem('refresh_token') ?? ''
      await apiLogout(refresh)
    } catch {
      // ignore
    }
    storeLogout()
    navigate('/portal/login')
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f7fa' }}>
      <Header
        style={{
          background: '#fff',
          borderBottom: '1px solid #e8e8e8',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          position: 'sticky',
          top: 0,
          zIndex: 100,
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
        }}
      >
        <Space
          style={{ cursor: 'pointer' }}
          onClick={() => navigate('/portal/tickets')}
        >
          <CustomerServiceOutlined style={{ fontSize: 22, color: '#1677ff' }} />
          <span>
            <Typography.Text strong style={{ fontSize: 16 }}>Служба поддержки</Typography.Text>
            <Typography.Text type="secondary" style={{ fontSize: 12, marginLeft: 6 }}>Экспресс Технологии</Typography.Text>
          </span>
        </Space>

        {user && (
          <Space>
            <Typography.Text type="secondary" style={{ fontSize: 13 }}>
              {user.full_name || user.username}
            </Typography.Text>
            <Button
              type="text"
              icon={<QuestionCircleOutlined />}
              onClick={() => navigate('/portal/faq')}
              size="small"
            >
              FAQ
            </Button>
            <Button
              type="text"
              icon={<UserOutlined />}
              onClick={() => navigate('/portal/profile')}
              size="small"
            >
              Профиль
            </Button>
            <Button
              type="text"
              icon={<LogoutOutlined />}
              onClick={handleLogout}
              size="small"
            >
              Выйти
            </Button>
          </Space>
        )}
      </Header>

      <Content style={{ maxWidth: 900, margin: '0 auto', width: '100%', padding: '24px 16px' }}>
        <Outlet />
      </Content>
    </Layout>
  )
}
