import client from './client'
import type { Attachment } from '../types/ticket'

export async function uploadTicketAttachment(ticketId: number, file: File): Promise<Attachment> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await client.post<Attachment>(`/tickets/${ticketId}/attachments`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function uploadCommentAttachment(ticketId: number, commentId: number, file: File): Promise<Attachment> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await client.post<Attachment>(
    `/tickets/${ticketId}/comments/${commentId}/attachments`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return res.data
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

export async function deleteAttachment(id: number): Promise<void> {
  await client.delete(`/attachments/${id}`)
}
