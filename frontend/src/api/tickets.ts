import client from './client'
import type {
  Ticket, TicketListItem, TicketCreateRequest, TicketUpdateRequest,
  StatusChangeRequest, AssignRequest, TicketHistory, TicketFilters, Attachment,
} from '../types/ticket'
import type { PagedResponse } from '../types/common'

export async function getTickets(params?: TicketFilters): Promise<PagedResponse<TicketListItem>> {
  const res = await client.get<PagedResponse<TicketListItem>>('/tickets', { params })
  return res.data
}

export async function getTicket(id: number): Promise<Ticket> {
  const res = await client.get<Ticket>(`/tickets/${id}`)
  return res.data
}

export async function createTicket(data: TicketCreateRequest): Promise<Ticket> {
  const res = await client.post<Ticket>('/tickets', data)
  return res.data
}

export async function updateTicket(id: number, data: TicketUpdateRequest): Promise<Ticket> {
  const res = await client.put<Ticket>(`/tickets/${id}`, data)
  return res.data
}

export async function changeTicketStatus(id: number, data: StatusChangeRequest): Promise<Ticket> {
  const res = await client.patch<Ticket>(`/tickets/${id}/status`, data)
  return res.data
}

export async function assignTicket(id: number, data: AssignRequest): Promise<Ticket> {
  const res = await client.patch<Ticket>(`/tickets/${id}/assign`, data)
  return res.data
}

export async function changeTicketPriority(id: number, priority_id: number): Promise<Ticket> {
  const res = await client.patch<Ticket>(`/tickets/${id}/priority`, { priority_id })
  return res.data
}

export async function getTicketHistory(id: number): Promise<TicketHistory[]> {
  const res = await client.get<TicketHistory[]>(`/tickets/${id}/history`)
  return res.data
}

export async function uploadTicketAttachment(ticketId: number, file: File): Promise<Attachment> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await client.post<Attachment>(`/tickets/${ticketId}/attachments`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function deleteAttachment(id: number): Promise<void> {
  await client.delete(`/attachments/${id}`)
}

export async function downloadAttachment(id: number, filename: string): Promise<void> {
  const res = await client.get(`/attachments/${id}`, { responseType: 'blob' })
  const url = URL.createObjectURL(res.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
