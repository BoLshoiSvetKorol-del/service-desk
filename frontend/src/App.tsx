import { ConfigProvider } from 'antd'
import ruRU from 'antd/locale/ru_RU'
import { RouterProvider } from 'react-router-dom'
import { router } from './router'
import ErrorBoundary from './components/common/ErrorBoundary'

export default function App() {
  return (
    <ErrorBoundary>
      <ConfigProvider locale={ruRU} theme={{ token: { colorPrimary: '#1677ff' } }}>
        <RouterProvider router={router} />
      </ConfigProvider>
    </ErrorBoundary>
  )
}
