import { create } from 'zustand'

export interface AppNotification {
  id: number
  ticket_id: number | null
  event_type: string
  message: string
  is_read: boolean
  created_at: string
  actor_name?: string
}

interface NotificationState {
  notifications: AppNotification[]
  unreadCount: number
  setNotifications: (items: AppNotification[]) => void
  setUnreadCount: (count: number) => void
  addNotification: (n: AppNotification) => void
  markRead: (id: number) => void
  markAllRead: () => void
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  unreadCount: 0,

  setNotifications(items) {
    set({ notifications: items })
  },

  setUnreadCount(count) {
    set({ unreadCount: count })
  },

  addNotification(n) {
    set(state => ({
      notifications: [n, ...state.notifications].slice(0, 50),
      unreadCount: state.unreadCount + (n.is_read ? 0 : 1),
    }))
  },

  markRead(id) {
    set(state => ({
      notifications: state.notifications.map(n =>
        n.id === id ? { ...n, is_read: true } : n,
      ),
      unreadCount: Math.max(0, state.unreadCount - 1),
    }))
  },

  markAllRead() {
    set(state => ({
      notifications: state.notifications.map(n => ({ ...n, is_read: true })),
      unreadCount: 0,
    }))
  },
}))
