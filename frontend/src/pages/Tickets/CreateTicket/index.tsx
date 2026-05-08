import { useState } from 'react'
import { Typography, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import { createTicket, uploadTicketAttachment } from '../../../api/tickets'
import type { TicketCreateRequest } from '../../../types/ticket'
import TicketForm from '../../../components/tickets/TicketForm'
import { getErrorMessage } from '../../../types/common'

export default function CreateTicketPage() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(data: TicketCreateRequest, files: File[]) {
    setLoading(true)
    try {
      const ticket = await createTicket(data)
      for (const file of files) {
        try {
          await uploadTicketAttachment(ticket.id, file)
        } catch {
          message.warning(`Не удалось загрузить файл: ${file.name}`)
        }
      }
      message.success(`Заявка ${ticket.number} создана`)
      navigate(`/tickets/${ticket.id}`)
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Typography.Title level={4} style={{ marginBottom: 24 }}>Новая заявка</Typography.Title>
      <TicketForm onSubmit={handleSubmit} loading={loading} />
    </div>
  )
}
