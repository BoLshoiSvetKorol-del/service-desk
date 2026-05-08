import client from './client'
import type { Comment, Attachment } from '../types/ticket'

export interface CommentCreateRequest {
  body: string
  is_internal?: boolean
}

export async function getComments(ticketId: number): Promise<Comment[]> {
  const res = await client.get<Comment[]>(`/tickets/${ticketId}/comments`)
  return res.data
}

export async function createComment(ticketId: number, data: CommentCreateRequest): Promise<Comment> {
  const res = await client.post<Comment>(`/tickets/${ticketId}/comments`, data)
  return res.data
}

export async function updateComment(ticketId: number, commentId: number, body: string): Promise<Comment> {
  const res = await client.put<Comment>(`/tickets/${ticketId}/comments/${commentId}`, { body })
  return res.data
}

export async function deleteComment(ticketId: number, commentId: number): Promise<void> {
  await client.delete(`/tickets/${ticketId}/comments/${commentId}`)
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
