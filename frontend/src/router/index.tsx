import { createBrowserRouter, Navigate, Outlet, useLocation } from 'react-router-dom'
import { Result } from 'antd'
import { useAuthStore } from '../store/authStore'
import { UserRole } from '../types/user'
import AppLayout from '../components/common/Layout/AppLayout'
import LoginPage from '../pages/Login'
import DashboardPage from '../pages/Dashboard'
import SettingsPage from '../pages/Settings'
import TicketsListPage from '../pages/Tickets/TicketsList'
import CreateTicketPage from '../pages/Tickets/CreateTicket'
import TicketDetailPage from '../pages/Tickets/TicketDetail'
import ReportsPage from '../pages/Reports'

function PrivateRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const location = useLocation()
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />
  return <Outlet />
}

function RoleRoute({ roles }: { roles: UserRole[] }) {
  const user = useAuthStore((s) => s.user)
  if (!user || !roles.includes(user.role)) {
    return <Result status="403" title="403" subTitle="Недостаточно прав" />
  }
  return <Outlet />
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    element: <PrivateRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/', element: <Navigate to="/dashboard" replace /> },
          { path: '/dashboard', element: <DashboardPage /> },
          { path: '/tickets', element: <TicketsListPage /> },
          { path: '/tickets/new', element: <CreateTicketPage /> },
          { path: '/tickets/:id', element: <TicketDetailPage /> },
          {
            element: <RoleRoute roles={['admin', 'agent']} />,
            children: [
              { path: '/reports', element: <ReportsPage /> },
            ],
          },
          {
            element: <RoleRoute roles={['admin']} />,
            children: [
              { path: '/settings', element: <SettingsPage /> },
            ],
          },
        ],
      },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])
