import { useState } from 'react'
import { useEffect } from 'react'
import { Badge, Button, Drawer, Empty, List, Tag, Typography, message } from 'antd'
import { BellOutlined, CheckOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useNotificationStore } from '../../../store/notificationStore'
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '../../../api/notifications'
import type { AppNotification } from '../../../store/notificationStore'

const EVENT_LABELS: Record<string, { label: string; color: string }> = {
  ticket_created: { label: 'Создана', color: 'blue' },
  ticket_status_changed: { label: 'Статус', color: 'purple' },
  ticket_assigned: { label: 'Назначена', color: 'cyan' },
  new_comment: { label: 'Комментарий', color: 'green' },
  new_attachment: { label: 'Вложение', color: 'orange' },
  sla_warning: { label: 'SLA', color: 'gold' },
  sla_violated: { label: 'SLA!', color: 'red' },
}

function formatDate(d: string) {
  return new Date(d).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const { notifications, unreadCount, setNotifications, setUnreadCount, markRead, markAllRead } =
    useNotificationStore()

  useEffect(() => {
    getNotifications({ page_size: 50 })
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
    if (n.ticket_id) {
      navigate(`/tickets/${n.ticket_id}`)
      setOpen(false)
    }
  }

  async function handleMarkAll() {
    try {
      await markAllNotificationsRead()
      markAllRead()
    } catch {
      message.error('Ошибка при обновлении уведомлений')
    }
  }

  const drawerTitle = (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span>Уведомления {unreadCount > 0 && <Badge count={unreadCount} size="small" style={{ marginLeft: 6 }} />}</span>
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
  )

  return (
    <>
      <Badge count={unreadCount} size="small" offset={[-2, 2]}>
        <Button
          type="text"
          icon={<BellOutlined style={{ fontSize: 18 }} />}
          onClick={() => setOpen(true)}
          style={{ display: 'flex', alignItems: 'center' }}
        />
      </Badge>

      <Drawer
        title={drawerTitle}
        placement="right"
        onClose={() => setOpen(false)}
        open={open}
        width={400}
        styles={{ body: { padding: 0 } }}
      >
        {notifications.length === 0 ? (
          <Empty description="Нет уведомлений" style={{ padding: '48px 0' }} />
        ) : (
          <List<AppNotification>
            dataSource={notifications}
            renderItem={n => {
              const evMeta = EVENT_LABELS[n.event_type]
              return (
                <List.Item
                  onClick={() => handleClick(n)}
                  style={{
                    padding: '10px 16px',
                    cursor: n.ticket_id ? 'pointer' : 'default',
                    backgroundColor: n.is_read ? undefined : '#e6f4ff',
                    borderLeft: n.is_read ? undefined : '3px solid #1677ff',
                    transition: 'background 0.2s',
                    alignItems: 'flex-start',
                  }}
                >
                  <div style={{ width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                      {evMeta && (
                        <Tag color={evMeta.color} style={{ margin: 0, fontSize: 11 }}>
                          {evMeta.label}
                        </Tag>
                      )}
                      <Typography.Text style={{ fontSize: 13 }} strong={!n.is_read}>
                        {n.message}
                      </Typography.Text>
                    </div>
                    <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                      {formatDate(n.created_at)}
                    </Typography.Text>
                  </div>
                </List.Item>
              )
            }}
          />
        )}
      </Drawer>
    </>
  )
}
