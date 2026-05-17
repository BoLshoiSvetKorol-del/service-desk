import { useState } from 'react'
import { Drawer, Grid, Layout } from 'antd'
import { Outlet } from 'react-router-dom'
import AppHeader from './Header'
import AppSidebar, { SidebarMenu } from './Sidebar'
import { useSSE } from '../../../hooks/useSSE'

const { Content } = Layout
const { useBreakpoint } = Grid

export default function AppLayout() {
  useSSE()
  const screens = useBreakpoint()
  const isMobile = !screens.md
  const [drawerOpen, setDrawerOpen] = useState(false)

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {isMobile ? (
        <Drawer
          placement="left"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          width={220}
          styles={{ body: { padding: 0 }, header: { display: 'none' } }}
        >
          <SidebarMenu onNavigate={() => setDrawerOpen(false)} />
        </Drawer>
      ) : (
        <AppSidebar />
      )}

      <Layout>
        <AppHeader onMenuClick={isMobile ? () => setDrawerOpen(true) : undefined} />
        <Content
          style={{
            margin: isMobile ? '12px 8px' : '24px',
            padding: isMobile ? '16px 12px' : '24px',
            background: '#fff',
            borderRadius: 8,
            minHeight: 280,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
