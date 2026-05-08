import { Layout } from 'antd'
import { Outlet } from 'react-router-dom'
import AppHeader from './Header'
import AppSidebar from './Sidebar'
import { useSSE } from '../../../hooks/useSSE'

const { Content } = Layout

export default function AppLayout() {
  useSSE()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppSidebar />
      <Layout>
        <AppHeader />
        <Content style={{ margin: '24px', padding: '24px', background: '#fff', borderRadius: 8, minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
