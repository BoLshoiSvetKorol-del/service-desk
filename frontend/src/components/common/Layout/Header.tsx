import { Layout, Avatar, Button, Dropdown, Typography, Space } from 'antd'
import { UserOutlined, LogoutOutlined, MenuOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../../store/authStore'
import { logout as apiLogout } from '../../../api/auth'
import NotificationBell from '../NotificationBell'

const { Header } = Layout
const { Text } = Typography

const ROLE_LABELS: Record<string, string> = {
  admin: 'Администратор',
  department_head: 'Руководитель отдела',
  agent: 'Агент поддержки',
  user: 'Пользователь',
}

interface AppHeaderProps {
  onMenuClick?: () => void
}

export default function AppHeader({ onMenuClick }: AppHeaderProps) {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  async function handleLogout() {
    await apiLogout()
    logout()
    navigate('/login')
  }

  const menuItems = [
    { key: 'logout', icon: <LogoutOutlined />, label: 'Выйти', danger: true, onClick: handleLogout },
  ]

  return (
    <Header
      style={{
        background: '#fff',
        padding: '0 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
        borderBottom: '1px solid #f0f0f0',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {onMenuClick && (
          <Button type="text" icon={<MenuOutlined />} onClick={onMenuClick} />
        )}
      </div>

      <Space>
        <NotificationBell />
        <Dropdown menu={{ items: menuItems }} placement="bottomRight">
          <Space style={{ cursor: 'pointer' }}>
            <Avatar icon={<UserOutlined />} style={{ background: '#1677ff' }} />
            <div style={{ lineHeight: 1.2 }}>
              <Text strong style={{ display: 'block', fontSize: 14 }}>{user?.full_name}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>{ROLE_LABELS[user?.role ?? '']}</Text>
            </div>
          </Space>
        </Dropdown>
      </Space>
    </Header>
  )
}
