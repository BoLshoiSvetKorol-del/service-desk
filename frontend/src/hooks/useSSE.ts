import { useEffect } from 'react'
import { notification } from 'antd'
import { getAccessToken } from '../api/client'
import { useNotificationStore } from '../store/notificationStore'
import { useTicketEventStore } from '../store/ticketEventStore'
import type { AppNotification } from '../store/notificationStore'

interface SSEMessage {
  id?: string
  event?: string
  data: string
}

function parseSSEMessages(raw: string): SSEMessage[] {
  const blocks = raw.split('\n\n').filter(b => b.trim())
  return blocks.map(block => {
    const lines = block.split('\n')
    let id: string | undefined
    let event: string | undefined
    const dataLines: string[] = []

    for (const line of lines) {
      if (line.startsWith('id: ')) id = line.slice(4)
      else if (line.startsWith('event: ')) event = line.slice(7)
      else if (line.startsWith('data: ')) dataLines.push(line.slice(6))
    }

    return { id, event, data: dataLines.join('\n') }
  }).filter(m => m.data)
}

export function useSSE() {
  const addNotification = useNotificationStore(s => s.addNotification)
  const publishEvent = useTicketEventStore(s => s.publishEvent)

  useEffect(() => {
    let aborted = false
    const abortController = new AbortController()
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let lastEventId = ''

    async function connect() {
      const token = getAccessToken()
      if (!token || aborted) return

      try {
        const headers: Record<string, string> = {
          Accept: 'text/event-stream',
          Authorization: `Bearer ${token}`,
        }
        if (lastEventId) headers['Last-Event-ID'] = lastEventId

        const response = await fetch('/api/v1/events', {
          headers,
          signal: abortController.signal,
        })

        if (!response.ok || !response.body) throw new Error('SSE failed')

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const parts = buffer.split('\n\n')
          buffer = parts.pop() ?? ''

          const raw = parts.join('\n\n') + '\n\n'
          for (const msg of parseSSEMessages(raw)) {
            if (msg.id) lastEventId = msg.id
            handleEvent(msg.event ?? 'message', msg.data)
          }
        }
      } catch (err) {
        if (aborted) return
        reconnectTimer = setTimeout(connect, 3000)
      }
    }

    function handleEvent(eventType: string, rawData: string) {
      if (rawData.trim() === '' || rawData.trim() === ': ping') return

      let data: Record<string, unknown> = {}
      try {
        data = JSON.parse(rawData)
      } catch {
        return
      }

      switch (eventType) {
        case 'notification': {
          addNotification(data as unknown as AppNotification)
          break
        }
        case 'ticket_status_changed':
          publishEvent({
            type: 'status_changed',
            ticketId: data.ticket_id as number,
            ticketNumber: String(data.ticket_number ?? ''),
            payload: data,
          })
          notification.info({
            message: 'Статус заявки изменён',
            description: `${data.ticket_number ?? ''}: ${data.new_status ?? ''}`,
            placement: 'topRight',
          })
          break
        case 'ticket_assigned':
          publishEvent({
            type: 'assigned',
            ticketId: data.ticket_id as number,
            ticketNumber: String(data.ticket_number ?? ''),
            payload: data,
          })
          notification.info({
            message: 'Назначение обновлено',
            description: String(data.ticket_number ?? ''),
            placement: 'topRight',
          })
          break
        case 'new_comment':
          publishEvent({
            type: 'new_comment',
            ticketId: data.ticket_id as number,
            ticketNumber: String(data.ticket_number ?? ''),
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            comment: data.comment as any,
          })
          notification.info({
            message: `Новый комментарий — ${data.actor_name ?? ''}`,
            description: String(data.ticket_number ?? ''),
            placement: 'topRight',
          })
          break
        case 'new_attachment':
          publishEvent({
            type: 'new_attachment',
            ticketId: data.ticket_id as number,
            ticketNumber: String(data.ticket_number ?? ''),
            payload: data,
          })
          notification.info({
            message: `Новое вложение — ${data.actor_name ?? ''}`,
            description: `${data.ticket_number ?? ''}: ${data.filename ?? ''}`,
            placement: 'topRight',
          })
          break
        case 'sla_warning':
          notification.warning({
            message: 'Предупреждение SLA',
            description: `${data.ticket_number ?? ''}: приближается дедлайн`,
            placement: 'topRight',
            duration: 10,
          })
          break
        case 'sla_violated':
          notification.error({
            message: 'Нарушение SLA',
            description: `${data.ticket_number ?? ''}: дедлайн истёк`,
            placement: 'topRight',
            duration: 0,
          })
          break
      }
    }

    connect()

    return () => {
      aborted = true
      abortController.abort()
      if (reconnectTimer) clearTimeout(reconnectTimer)
    }
  }, [addNotification, publishEvent])
}
