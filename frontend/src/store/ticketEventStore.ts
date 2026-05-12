import { create } from 'zustand'
import type { Comment } from '../types/ticket'

interface TicketEvent {
  type: 'new_comment' | 'new_attachment' | 'status_changed' | 'assigned' | 'priority_changed'
  ticketId: number
  ticketNumber: string
  comment?: Comment
  payload?: Record<string, unknown>
}

interface TicketEventStore {
  lastEvent: TicketEvent | null
  publishEvent: (event: TicketEvent) => void
}

export const useTicketEventStore = create<TicketEventStore>(set => ({
  lastEvent: null,
  publishEvent: event => set({ lastEvent: event }),
}))
