import { useEffect } from 'react'
import { Badge, Button, Dropdown, Empty, List, Typography, message } from 'antd'
import { BellOutlined, CheckOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useNotificationStore } from '../../../store/notificationStore'
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '../../../api/notifications'
import type { AppNotification } from '../../../store/notificationStore'

function formatDate(d: string) {
  return new Date(d).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function NotificationBell() {
  const navigate = useNavigate()
  const { notifications, unreadCount, setNotifications, setUnreadCount, markRead, markAllRead } =
    useNotificationStore()

  useEffect(() => {
    getNotifications({ page_size: 20 })
      .then(res => {
        setNotifications(res.items)
        setUnreadCount(res.items.filter(n => !n.is_read).length)
      })
      .catch(() => {})
  }, [setNotifications, setUnreadCount])

  async function handleClick(n: AppNotification) {
    if (!n.is_read) {
      try {
        await markNotificationRead(n.id)
        markRead(n.id)
      } catch {}
    }
    if (n.ticket_id) navigate(`/tickets/${n.ticket_id}`)
  }

  async function handleMarkAll() {
    try {
      await markAllNotificationsRead()
      markAllRead()
    } catch {
      message.error('Ошибка при обновлении уведомлений')
    }
  }

  const recent = notifications.slice(0, 10)

  const dropdownContent = (
    <div style={{ width: 340 }}>
      <div
        style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '8px 12px', borderBottom: '1px solid #f0f0f0',
        }}
      >
        <Typography.Text strong>Уведомления</Typography.Text>
        {unreadCount > 0 && (
          <Button
            type="link"
            size="small"
            icon={<CheckOutlined />}
            onClick={handleMarkAll}
            style={{ padding: 0 }}
          >
            Прочитать все
          </Button>
        )}
      </div>

      {recent.length === 0 ? (
        <Empty description="Нет уведомлений" style={{ padding: '24px 0' }} />
      ) : (
        <List<AppNotification>
          dataSource={recent}
          style={{ maxHeight: 400, overflow: 'auto' }}
          renderItem={n => (
            <List.Item
              onClick={() => handleClick(n)}
              style={{
                padding: '8px 12px',
                cursor: n.ticket_id ? 'pointer' : 'default',
                backgroundColor: n.is_read ? undefined : '#e6f4ff',
                transition: 'background 0.2s',
              }}
            >
              <div style={{ width: '100%' }}>
                <Typography.Text
                  style={{ fontSize: 13, display: 'block' }}
                  strong={!n.is_read}
                >
                  {n.message}
                </Typography.Text>
                <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                  {formatDate(n.created_at)}
                </Typography.Text>
              </div>
            </List.Item>
          )}
        />
      )}
    </div>
  )

  return (
    <Dropdown
      dropdownRender={() => dropdownContent}
      trigger={['click']}
      placement="bottomRight"
    >
      <Badge count={unreadCount} size="small" offset={[-2, 2]}>
        <Button
          type="text"
          icon={<BellOutlined style={{ fontSize: 18 }} />}
          style={{ display: 'flex', alignItems: 'center' }}
        />
      </Badge>
    </Dropdown>
  )
}
