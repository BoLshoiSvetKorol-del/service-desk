import { useState } from 'react'
import { Layout, Menu, Typography } from 'antd'
import {
  DashboardOutlined,
  FileTextOutlined,
  BarChartOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../../store/authStore'

const { Sider } = Layout

interface SidebarMenuProps {
  onNavigate?: () => void
}

export function SidebarMenu({ onNavigate }: SidebarMenuProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const user = useAuthStore((s) => s.user)

  const items = [
    { key: '/dashboard', icon: <DashboardOutlined />, label: 'Дашборд' },
    { key: '/tickets', icon: <FileTextOutlined />, label: 'Заявки' },
    ...(user?.role !== 'user'
      ? [{ key: '/reports', icon: <BarChartOutlined />, label: 'Отчёты' }]
      : []),
    ...(user?.role === 'admin'
      ? [{ key: '/settings', icon: <SettingOutlined />, label: 'Настройки' }]
      : []),
  ]

  const selectedKey = '/' + location.pathname.split('/')[1]

  return (
    <>
      <div
        style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 700,
          color: '#1677ff',
          padding: '0 16px',
          flexDirection: 'column',
          lineHeight: 1.2,
          gap: 2,
        }}
      >
        <Typography.Text strong style={{ fontSize: 16, color: '#1677ff' }}>Service Desk</Typography.Text>
        <Typography.Text type="secondary" style={{ fontSize: 10 }}>Экспресс Технологии</Typography.Text>
      </div>
      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        items={items}
        onClick={({ key }) => { navigate(key); onNavigate?.() }}
      />
    </>
  )
}

export default function AppSidebar() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} theme="light">
      {collapsed ? (
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontWeight: 700, fontSize: 14, color: '#1677ff' }}>ЭТ</div>
      ) : (
        <SidebarMenu />
      )}
    </Sider>
  )
}
