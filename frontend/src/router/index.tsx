import { createBrowserRouter, Navigate, Outlet, useLocation } from 'react-router-dom'
import { Result } from 'antd'
import { useAuthStore } from '../store/authStore'
import { UserRole } from '../types/user'
import AppLayout from '../components/common/Layout/AppLayout'
import PortalLayout from '../components/Portal/PortalLayout'
import LoginPage from '../pages/Login'
import DashboardPage from '../pages/Dashboard'
import SettingsPage from '../pages/Settings'
import TicketsListPage from '../pages/Tickets/TicketsList'
import CreateTicketPage from '../pages/Tickets/CreateTicket'
import TicketDetailPage from '../pages/Tickets/TicketDetail'
import ReportsPage from '../pages/Reports'
import PortalLoginPage from '../pages/Portal/PortalLoginPage'
import PortalRegisterPage from '../pages/Portal/PortalRegisterPage'
import PortalVerifyPage from '../pages/Portal/PortalVerifyPage'
import PortalTicketsPage from '../pages/Portal/PortalTicketsPage'
import PortalCreateTicketPage from '../pages/Portal/PortalCreateTicketPage'
import PortalTicketDetailPage from '../pages/Portal/PortalTicketDetailPage'
import PortalProfilePage from '../pages/Portal/PortalProfilePage'
import PortalFaqPage from '../pages/Portal/PortalFaqPage'

/** Redirect unauthenticated users to login */
function PrivateRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const user = useAuthStore((s) => s.user)
  const location = useLocation()

  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />

  // Users (clients) belong in the portal
  if (user?.role === 'user' && !location.pathname.startsWith('/portal')) {
    return <Navigate to="/portal/tickets" replace />
  }

  return <Outlet />
}

/** Portal-specific guard: must be authenticated as role=user */
function PortalRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const user = useAuthStore((s) => s.user)
  const location = useLocation()

  if (!isAuthenticated) return <Navigate to="/portal/login" state={{ from: location }} replace />

  if (user?.role !== 'user') {
    return <Result
      status="403"
      title="Недоступно"
      subTitle="Этот раздел предназначен только для клиентов."
      extra={<a href="/dashboard">Перейти в основной интерфейс</a>}
    />
  }

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
  // Public routes
  { path: '/login', element: <LoginPage /> },
  { path: '/portal/login', element: <PortalLoginPage /> },
  { path: '/portal/register', element: <PortalRegisterPage /> },
  { path: '/portal/verify', element: <PortalVerifyPage /> },

  // Agent / Admin routes (PrivateRoute blocks clients and redirects them to portal)
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

  // Client portal routes
  {
    element: <PortalRoute />,
    children: [
      {
        element: <PortalLayout />,
        children: [
          { path: '/portal/tickets', element: <PortalTicketsPage /> },
          { path: '/portal/tickets/new', element: <PortalCreateTicketPage /> },
          { path: '/portal/tickets/:id', element: <PortalTicketDetailPage /> },
          { path: '/portal/profile', element: <PortalProfilePage /> },
          { path: '/portal/faq', element: <PortalFaqPage /> },
          { path: '/portal', element: <Navigate to="/portal/tickets" replace /> },
        ],
      },
    ],
  },

  { path: '*', element: <Navigate to="/" replace /> },
])
