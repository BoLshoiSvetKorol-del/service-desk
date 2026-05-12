import client from './client'

export interface TicketNote {
  id: number
  ticket_id: number
  author_id: number
  body: string
  created_at: string
  updated_at: string
}

export async function getNotes(ticketId: number): Promise<TicketNote[]> {
  const res = await client.get<TicketNote[]>(`/tickets/${ticketId}/notes`)
  return res.data
}

export async function createNote(ticketId: number, body: string): Promise<TicketNote> {
  const res = await client.post<TicketNote>(`/tickets/${ticketId}/notes`, { body })
  return res.data
}

export async function updateNote(ticketId: number, noteId: number, body: string): Promise<TicketNote> {
  const res = await client.put<TicketNote>(`/tickets/${ticketId}/notes/${noteId}`, { body })
  return res.data
}

export async function deleteNote(ticketId: number, noteId: number): Promise<void> {
  await client.delete(`/tickets/${ticketId}/notes/${noteId}`)
}
