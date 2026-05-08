import { useState } from 'react'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  FileTextOutlined,
  BarChartOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../../store/authStore'

const { Sider } = Layout

export default function AppSidebar() {
  const [collapsed, setCollapsed] = useState(false)
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
    <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} theme="light">
      <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 700, fontSize: collapsed ? 14 : 18, color: '#1677ff', padding: '0 16px' }}>
        {collapsed ? 'SD' : 'Service Desk'}
      </div>
      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        items={items}
        onClick={({ key }) => navigate(key)}
      />
    </Sider>
  )
}
