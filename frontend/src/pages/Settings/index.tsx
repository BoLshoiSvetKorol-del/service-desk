import { Tabs } from 'antd'
import UsersTab from './UsersTab'
import DepartmentsTab from './DepartmentsTab'
import TicketTypesTab from './TicketTypesTab'

export default function SettingsPage() {
  return (
    <Tabs
      defaultActiveKey="users"
      items={[
        { key: 'users', label: 'Пользователи', children: <UsersTab /> },
        { key: 'departments', label: 'Отделы', children: <DepartmentsTab /> },
        { key: 'ticket-types', label: 'Типы заявок', children: <TicketTypesTab /> },
      ]}
    />
  )
}
