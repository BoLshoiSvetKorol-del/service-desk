import client from './client'
import type { AppNotification } from '../store/notificationStore'
import type { PagedResponse } from '../types/common'

export async function getNotifications(params?: {
  is_read?: boolean
  page?: number
  page_size?: number
}): Promise<PagedResponse<AppNotification>> {
  const res = await client.get<PagedResponse<AppNotification>>('/notifications', { params })
  return res.data
}

export async function markNotificationRead(id: number): Promise<void> {
  await client.patch(`/notifications/${id}/read`)
}

export async function markAllNotificationsRead(): Promise<void> {
  await client.patch('/notifications/read-all')
}
